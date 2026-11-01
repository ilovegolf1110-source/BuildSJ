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
        sj_map = folium.Map(
            location=san_jose_coords,
            zoom_start=11,
            min_zoom=11,
            control_scale=True,
            min_lat=37.05,
            max_lat=37.45,
            min_lon=-122.1,
            max_lon=-121.65,
            max_bounds=True
        )

        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; OpenStreetMap contributors &copy; CARTO',
            name="Light Map",
        ).add_to(sj_map)

        Geocoder(
            provider="photon",
            provider_options={
                "geocodingQueryParams": {
                    "bbox": "-122.1, 37.05, -121.65, 37.45",
                    "limit": 5
                }
            },
            add_marker=True,
            suggestMinLength=3,
            suggestTimeout=250,
        ).add_to(sj_map)

        folium.GeoJson(
            "fire_zones_d10.geojson",
            name="Map of D10 Fire Hazards (by CalFire)",
            style_function=map_style,
            tooltip=folium.GeoJsonTooltip(
                fields=[FIELD],
                aliases=["Fire Hazard Level: "]
            )
        ).add_to(sj_map)

        sj_map.get_root().header.add_child(
            folium.Element('<link rel="stylesheet" href="website.css"/>')
        )

        # --- Neighborhood polygons (APPROXIMATE, folium uses [lat, lon]) ---
        JUNCTION = [37.240, -121.820]

        # Shared border points, defined once so adjacent polygons match exactly
        AB_NORTH = [37.262, -121.874]
        AB_MID   = [37.240, -121.835]
        AS_MID   = [37.218, -121.810]
        AS_SOUTH = [37.195, -121.800]
        BS_NORTH = [37.262, -121.805]
        BS_MID   = [37.250, -121.808]

        almaden = [
            [37.265, -121.885],
            AB_NORTH, AB_MID, JUNCTION,
            AS_MID, AS_SOUTH,
            [37.175, -121.840],
            [37.190, -121.885],
            [37.230, -121.895],
        ]

        blossom_valley = [
            [37.275, -121.874],
            [37.275, -121.800],
            BS_NORTH, BS_MID, JUNCTION,
            AB_MID, AB_NORTH,
        ]

        santa_teresa = [
            BS_NORTH,
            [37.262, -121.775],
            [37.235, -121.760],
            [37.205, -121.760],
            [37.195, -121.775],
            AS_SOUTH, AS_MID, JUNCTION,
            BS_MID,
        ]

        hoods = folium.FeatureGroup(name="Neighborhoods (approx.)")

        for name, coords, color in [
            ("Almaden Valley", almaden,        "#d62728"),
            ("Blossom Valley", blossom_valley, "#2ca02c"),
            ("Santa Teresa",   santa_teresa,   "#1f77b4"),
        ]:
            folium.Polygon(
                locations=coords,
                color=color, weight=3,
                fill=True, fill_color=color, fill_opacity=0.15,
                tooltip=name,
            ).add_to(hoods)

        hoods.add_to(sj_map)
        folium.LayerControl().add_to(sj_map)

        sj_map.save("map.html")
        print("Map was generated on website")

    except FileNotFoundError as e:
        print(f"Missing file: {e}")
    except ValueError as e:
        print(f"Bad data or color mapping: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
