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

fire_colors = {
    "Very High": "#b10000",  # deep red for highest danger
    "High": "#ff5a1f",       # strong orange/red warning color
    "Moderate": "#ffb000",   # amber to show medium risk
    "None": "#dfe4ea",       # light neutral for areas without a recorded fire hazard
}

# ---------------------------------------------------------------
# NEIGHBORHOOD BORDERS
# All points are [lat, lon], which is what folium.Polygon expects.
# ---------------------------------------------------------------

# Shared junction where all three neighborhoods meet (PLACEHOLDER, adjust to the real spot)
JUNCTION = [37.235, -121.818]

AB_NORTH = [37.262, -121.874]  # Almaden | Blossom Valley, north end
AB_MID   = [37.240, -121.835]  # Almaden | Blossom Valley, middle
AS_MID   = [37.218, -121.810]  # Almaden | Santa Teresa, middle
AS_SOUTH = [37.195, -121.800]  # Almaden | Santa Teresa, south end
BS_NORTH = [37.262, -121.805]  # Blossom Valley | Santa Teresa, north end
BS_MID   = [37.250, -121.808]  # Blossom Valley | Santa Teresa, middle

almaden = [
    [37.265, -121.885],  # NW corner (Los Gatos side)
    AB_NORTH, AB_MID, JUNCTION,  # shared border with Blossom Valley
    AS_MID, AS_SOUTH,            # shared border with Santa Teresa
    [37.175, -121.840],  # south (New Almaden area)
    [37.190, -121.885],  # SW foothills
    [37.230, -121.895],  # west foothills
]

blossom_valley = [
    [37.275, -121.874],  # NW corner
    [37.275, -121.800],  # NE corner
    BS_NORTH, BS_MID, JUNCTION,  # shared border with Santa Teresa
    AB_MID, AB_NORTH,            # shared border with Almaden
]

santa_teresa = [
    BS_NORTH,                    # shared border with Blossom Valley
    [37.262, -121.775],  # NE corner
    [37.235, -121.760],  # east edge
    [37.205, -121.760],
    [37.195, -121.775],  # SE corner
    AS_SOUTH, AS_MID, JUNCTION,  # shared border with Almaden
    BS_MID,                      # back to Blossom Valley border
]

# name -> (points, color)
NEIGHBORHOODS = {
    "Almaden": (almaden, "#2b7de9"),
    "Blossom Valley": (blossom_valley, "#2fa84f"),
    "Santa Teresa": (santa_teresa, "#8e44ad"),
}


# New: normalize a few possible variations of the hazard label.
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


def map_style(feature):
    properties = feature.get("properties", {})
    raw_level = properties.get(FIELD)
    level = normalize_hazard_level(raw_level)
    color = fire_colors.get(level, "#868e96")  # dark gray fallback

    return {
        "fillColor": color,
        "color": "#111111",
        "weight": 3.5,
        "opacity": 1,
        "fillOpacity": 0.88,
        "dashArray": "",
        "lineJoin": "round",
        "lineCap": "round",
        "smoothFactor": 2,
    }


def highlight_style(feature):
    base = map_style(feature)
    return {
        **base,
        "weight": 6,
        "fillOpacity": 1.0,
        "color": "#000000",
    }


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


def load_fire_zones_geojson():
    geojson_path = Path(__file__).resolve().parent / "fire_zones_d10.geojson"

    if not geojson_path.exists():
        raise FileNotFoundError(f"Missing fire zone file: {geojson_path}")

    with geojson_path.open("r", encoding="utf-8") as geojson_file:
        return json.load(geojson_file)


def main():
    try:
        sj_map = folium.Map(
            location=san_jose_coords,
            zoom_start=11,
            min_zoom=10,
            max_zoom=16,
            control_scale=True,
            min_lat=37.05,
            max_lat=37.45,
            min_lon=-122.1,
            max_lon=-121.65,
            max_bounds=True,
            tiles="CartoDB Positron",
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
                    "limit": 5,
                }
            },
            add_marker=True,
            suggestMinLength=3,
            suggestTimeout=250,
        ).add_to(sj_map)

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

        # NEW: neighborhood borders, added AFTER the fire layer so they draw on top.
        hood_group = folium.FeatureGroup(name="Neighborhood Borders")
        for name, (coords, color) in NEIGHBORHOODS.items():
            folium.Polygon(
                locations=coords,
                color=color,
                weight=4,
                fill=True,
                fill_color=color,
                fill_opacity=0.08,  # low so the fire zones underneath stay readable
                tooltip=name,
            ).add_to(hood_group)
        hood_group.add_to(sj_map)

        sj_map.get_root().header.add_child(
            folium.Element('<link rel="stylesheet" href="website.css"/>')
        )

        sj_map.get_root().html.add_child(folium.Element(create_legend_html()))

        folium.LayerControl().add_to(sj_map)

        output_path = Path(__file__).resolve().parent / "map.html"
        sj_map.save(output_path)
        print("Map was generated on website")

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
