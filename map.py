# starting file

import json
from pathlib import Path

import folium
# allows us to load in stuff to have interactive maps -> python database
from folium.plugins import Geocoder

# Define the geographic coordinates for San Jose, California (don't know if they are specificly correct )
san_jose_coords = [37.23, -121.82]

# Define the field and color mapping for fire hazard severity zones
FIELD = "FIREHAZARDSEVERITYZONE"

# More aggressive warning-map palette so the fire zones read as danger zones on the website.
# We made the reds/oranges much stronger and the outlines much darker so they stand out.
fire_colors = {
    "Very High": "#b10000",  # deep red for highest danger
    "High": "#ff5a1f",      # strong orange/red warning color
    "Moderate": "#ffb000",  # amber to show medium risk
    "None": "#dfe4ea",      # light neutral for areas without a recorded fire hazard
}

# New: normalize a few possible variations of the hazard label.
# Some GeoJSON layers use values like "Very High", "VERY HIGH", or blank values.
# We convert them into the exact names we use in fire_colors so the styling is stable.
def normalize_hazard_level(value):
    if value is None:
        return "None"

    cleaned = str(value).strip()
    if not cleaned:
        return "None"

    cleaned_upper = cleaned.upper()
    aliases = {
        "VERY HIGH": "Very High",
        "HIGH": "High",
        "MODERATE": "Moderate",
        "NONE": "None",
        "N/A": "None",
        "LOW": "None",
    }

    return aliases.get(cleaned_upper, cleaned)


# Function to define the style for each fire hazard zone on the map.
# We made the boundaries heavier and the fill much stronger so the zones look like a warning layer.
def map_style(feature):
    properties = feature.get("properties", {})
    raw_level = properties.get(FIELD)
    level = normalize_hazard_level(raw_level)
    color = fire_colors.get(level, "#868e96")  # dark gray fallback if something unexpected happens

    return {
        "fillColor": color,
        "color": "#111111",  # extremely dark border for sharp contrast
        "weight": 3.5,
        "opacity": 1,
        "fillOpacity": 0.88,
        "dashArray": "",
        "lineJoin": "round",
        "lineCap": "round",
        "smoothFactor": 2,
    }


# New: add a hovering state so the map feels more fluid and the danger areas get more obvious.
# When the user hovers, the zone gets a darker outline and even stronger fill to feel like a warning layer.
def highlight_style(feature):
    base = map_style(feature)
    return {
        **base,
        "weight": 6,
        "fillOpacity": 1.0,
        "color": "#000000",
    }


# New: add a legend to make the fire hazard map immediately readable on the website.
def create_legend_html():
    return """
    <div style="
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 9999;
        background: rgba(15, 23, 42, 0.92);
        border: 2px solid rgba(255, 255, 255, 0.28);
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        padding: 12px 14px;
        font-family: Arial, sans-serif;
        color: white;
    ">
        <div style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Fire Hazard Zones</div>
        <div style="display: flex; align-items: center; gap: 8px; margin: 5px 0;">
            <span style="width: 18px; height: 18px; background: #b10000; border: 2px solid #111111; display: inline-block; border-radius: 3px;"></span>
            <span>Very High</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; margin: 5px 0;">
            <span style="width: 18px; height: 18px; background: #ff5a1f; border: 2px solid #111111; display: inline-block; border-radius: 3px;"></span>
            <span>High</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; margin: 5px 0;">
            <span style="width: 18px; height: 18px; background: #ffb000; border: 2px solid #111111; display: inline-block; border-radius: 3px;"></span>
            <span>Moderate</span>
        </div>
    </div>
    """


# New: a small helper to safely load the GeoJSON file and keep the map path stable.
def load_fire_zones_geojson():
    geojson_path = Path(__file__).resolve().parent / "fire_zones_d10.geojson"

    if not geojson_path.exists():
        raise FileNotFoundError(f"Missing fire zone file: {geojson_path}")

    with geojson_path.open("r", encoding="utf-8") as geojson_file:
        return json.load(geojson_file)


# Function that holds main code (Used for error handling)
def main():
    try:
        # Create an open-source map centered on San Jose.
        # We use a brighter neutral base so the red/orange danger zones feel dramatic and obvious.
        sj_map = folium.Map(
            location=san_jose_coords,
            zoom_start=11,
            min_zoom=10,
            max_zoom=16,
            control_scale=True,
            # Bounds for the map (limits the viewable area)
            min_lat=37.05,
            max_lat=37.45,
            min_lon=-122.1,
            max_lon=-121.65,
            max_bounds=True,
            tiles="CartoDB Positron",  # light base map makes red/orange warnings pop
        )

        # Creates tiles, which are the many small square images that the map will stitch together.
        # New: we still add a base layer with explicit attribution so it looks clean.
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; OpenStreetMap contributors &copy; CARTO',
            name="Light Map",
        ).add_to(sj_map)

        # Adding the search tool (uses the Photon geocoding service)
        # Will have to check usage rights for Photon later
        Geocoder(
            provider="photon",
            provider_options={
                "geocodingQueryParams": {
                    # Limits autocomplete results to San Jose
                    "bbox": "-122.1, 37.05, -121.65, 37.45",
                    # Max amount of suggested results
                    "limit": 5,
                }
            },
            add_marker=True,
            suggestMinLength=3,
            suggestTimeout=250,
        ).add_to(sj_map)

        # Add the fire hazard zones to the map.
        # New: use the actual GeoJSON data object instead of a file path so we can
        # more easily style and inspect the data before drawing it on the map.
        fire_zones = load_fire_zones_geojson()

        fire_layer = folium.GeoJson(
            fire_zones,
            name="Map of D10 Fire Hazards (by CalFire)",
            style_function=map_style,
            highlight_function=highlight_style,
            smooth_factor=2,
            tooltip=folium.GeoJsonTooltip(
                fields=[FIELD],
                aliases=["Fire Hazard Level: "],
                sticky=True,
                labels=True,
            ),
        )
        fire_layer.add_to(sj_map)

        # After generating the map, we add our CSS file to style the map container.
        # We can't add it to html directly because map generation changes every time the script is run.
        sj_map.get_root().header.add_child(
            folium.Element('<link rel="stylesheet" href="website.css"/>')
        )

        # New: add the custom warning legend so the red/orange danger zones are obvious on the website.
        sj_map.get_root().html.add_child(folium.Element(create_legend_html()))

        # New: keep the map layer control visible so users can toggle the base map/layer.
        folium.LayerControl().add_to(sj_map)

        # The map is added to our html file.
        # New: save to the same folder as this script so it is easy to find and consistent.
        output_path = Path(__file__).resolve().parent / "map.html"
        sj_map.save(output_path)
        print("Map was generated on website")  # To inform us that python script has successfully created the map.html file

    except FileNotFoundError as e:
        print(f"Missing file: {e}")
    except ValueError as e:
        print(f"Bad data or color mapping: {e}")
    except json.JSONDecodeError as e:
        print(f"GeoJSON file is invalid: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
