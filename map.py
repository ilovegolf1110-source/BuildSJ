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

# New: make the zone colors clearer and more consistent for map readability.
# We keep the same general palette but tune the opacity and contrast so the
# hazard areas read clearly over the base map without blending too much.
fire_colors = {
    "Very High": "#d62828",
    "High": "#f77f00",
    "Moderate": "#B59A00",
    "None": "#adb5bd",
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


# Function to define the style for each fire hazard zone on the map
# New: this version is cleaner and more readable, with softer fills and stronger borders.
def map_style(feature):
    properties = feature.get("properties", {})
    raw_level = properties.get(FIELD)
    level = normalize_hazard_level(raw_level)
    color = fire_colors.get(level, "#868e96")  # Comes out as dark gray if the colors don't work

    return {
        "fillColor": color,
        "color": "#1f2937",  # dark border for strong separation from the map tiles
        "weight": 1.8,
        "opacity": 1,
        "fillOpacity": 0.72,
        "dashArray": "",
        "lineJoin": "round",
        "lineCap": "round",
        "smoothFactor": 2,
    }


# New: add a hover/highlight state so the zones feel more fluid and readable.
# When the user hovers, the zone gets a darker border and slightly stronger fill color.
def highlight_style(feature):
    base = map_style(feature)
    return {
        **base,
        "weight": 3,
        "fillOpacity": 0.9,
        "color": "#111827",
    }


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
        # Create an open-source map centered on San Jose
        # The default tile layer is 'OpenStreetMap'
        # New: we explicitly use a light tile set to keep the colored hazard polygons readable.
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
            tiles="CartoDB Positron",
        )

        # Creates tiles, which are the many small square images that the map will stitch together
        # New: we still add a base layer with explicit attribution so it looks clean
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

        # Add the fire hazard zones to the map
        # New: use the actual GeoJSON data object rather than a file path so we can
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

        # After generating the map, we add our CSS file to style the map container
        # We can't add it to html directly because map generation changes everytime the script is run
        # New: keep this, but also style the map containers to make the layer borders softer.
        sj_map.get_root().header.add_child(
            folium.Element('<link rel="stylesheet" href="website.css"/>')
        )

        # New: keep the map layer control visible so users can toggle the base map/layer.
        folium.LayerControl().add_to(sj_map)

        # The map is added to our html file
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
