# starting file

import folium
import webcolors
# allows us to load in stuff to have interactive maps -> python database
from folium.plugins import Geocoder

# Define the geographic coordinates for San Jose, California (don't know if they are specificly correct )
san_jose_coords = [37.23, -121.82]

# Define the field and color mapping for fire hazard severity zones
FIELD = "FIREHAZARDSEVERITYZONE"

fire_colors = {
    "Very High": "#d62828",
    "High": "#f77f00",
    "Moderate": "#B59A00",
    "None": "#adb5bd" 
}

# Function to define the style for each fire hazard zone on the map
def map_style(feature):
    level = feature["properties"].get(FIELD)
    color = fire_colors.get(level,"#868e96") # Comes out as dark gray if the colors don't work
    # I think we need something more if it's like faint but I don't think our map is there yet
    return {
        "fillColor": color, 
        "color": "#212529", 
        "weight": 6, 
        "opacity": 1,
        "fillOpacity": 0.9,
        "lineJoin": "round", 
        "lineCap": "round"
    }

# Function that holds main code (Used for error handling)
def main():
    try:
        # Create an open-source map centered on San Jose
        # The default tile layer is 'OpenStreetMap'
        sj_map = folium.Map(
            location=san_jose_coords, 
            zoom_start=11,
            min_zoom=11,
            control_scale=True,
            # Bounds for the map (limits the viewable area)
            min_lat=37.05,
            max_lat=37.45,
            min_lon=-122.1,
            max_lon=-121.65,
            max_bounds=True
        )

        # Creates tiles, which are the many small square images that the map will stitch together 
        folium.TileLayer(
             tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", # where to fetch the tile images from
             attr='&copy; OpenStreetMap contributors &copy; CARTO', # copyright text shown in corner
             name="Light Map", # labels for the layer 
        ).add_to(sj_map) # attaches these layers to our new map 

        # Adding the search tool (uses the Photon geocoding service)
        # Will have to check usage rights for Photon later
        Geocoder(
            provider = "photon",
            provider_options={
                "geocodingQueryParams": {
                    # Limits autocomplete results to San Jose
                    "bbox": "-122.1, 37.05, -121.65, 37.45",
                    # Max amount of suggested results
                    "limit": 5
                }
            },
            add_marker = True,
            suggestMinLength = 3,
            suggestTimeout = 250, 
        ).add_to(sj_map)

        # Add the fire hazard zones to the map
        folium.GeoJson(
            "fire_zones_d10.geojson",
            name = "Map of D10 Fire Hazards (by CalFire)",
            style_function = map_style,
            tooltip=folium.GeoJsonTooltip(
                fields=[FIELD], # Specify the field to display in the tooltip
                aliases=["Fire Hazard Level: "] # Specifies the description for the field
            )
        ).add_to(sj_map)
        
       
        # After generating the map, we add our CSS file to style the map container
        # We can't add it to html directly because map generation changes everytime the script is run
        sj_map.get_root().header.add_child(
            folium.Element('<link rel="stylesheet" href="website.css"/>')
        )


        folium.LayerControl().add_to(sj_map)

        # The map is added to our html file
        sj_map.save("map.html") # create map.html file 
        print("Map was generated on website") # To inform us that python script has successfully created the map.html file

    except FileNotFoundError as e:
        print(f"Missing file: {e}")
    except ValueError as e:
        print(f"Bad data or color mapping: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
