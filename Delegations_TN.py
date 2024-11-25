import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# Set the title and description of the app
st.title("Carte des Délégations de Tunisie")

# File uploader section
uploaded_file = st.sidebar.file_uploader("Ajouter un fichier CSV ou Excel", type=["csv", "xlsx"])

# Text input fields for intervals
with st.sidebar.expander("2. Définir les Intervalles", expanded=True):
    try:
        interval1 = st.text_input("Intervalle 1", "0-20")
        interval2 = st.text_input("Intervalle 2", "21-40")
        interval3 = st.text_input("Intervalle 3", "41-60")
        interval4 = st.text_input("Intervalle 4", "61-80")
        interval5 = st.text_input("Intervalle 5", "81-100")
        interval6 = st.text_input("Intervalle 6", "101+")
    except ValueError:
        st.error("Veuillez vous assurer que les intervalles sont correctement formatés (par exemple, '0-20').")

# Optionally reset text inputs and file uploader
reset_button = st.sidebar.button("Réinitialiser")
if reset_button:
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# Load the GeoJSON file for Tunisia's delegation boundaries
geojson_path = 'delegations-full.geojson'  # Replace with the actual path to your GeoJSON file
try:
    with open(geojson_path, 'r', encoding='utf-8') as f:
        tunisia_geojson = json.load(f)
except FileNotFoundError:
    st.error("Fichier GeoJSON des limites des délégations non trouvé.")
    tunisia_geojson = None

# Function to get a color based on a value and intervals
def get_color(value):
    try:
        value = float(value)
        ranges = [
            (interval1, 'yellow'),
            (interval2, 'orange'),
            (interval3, 'red'),
            (interval4, 'purple'),
            (interval5, 'blue'),
            (interval6, 'green')
        ]
        for interval, color in ranges:
            if "-" in interval:
                start, end = map(float, interval.split("-"))
                if start <= value <= end:
                    return color
            elif interval.endswith("+"):
                start = float(interval.rstrip("+"))
                if value >= start:
                    return color
        return 'lightgrey'
    except ValueError:
        return 'lightgrey'

# Check if GeoJSON data is loaded
if tunisia_geojson is not None:

    # Initialize the map centered on Tunisia with a zoom level of 7
    tunisia_map = folium.Map(location=[33.8869, 9.5375], zoom_start=7)

    # Check if the file is uploaded
    if uploaded_file is not None:
        # Read the uploaded file based on its type
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        
        # Check if the required columns are present
        if 'Valeurs' in df.columns and 'Delegations' in df.columns:
            # Create a dictionary to map delegations to colors using the 'Valeurs' column
            delegation_color_map = {row['Delegations']: get_color(row['Valeurs']) for _, row in df.iterrows()}
        else:
            st.error("Le fichier doit contenir les colonnes 'Delegations' et 'Valeurs'.")
            delegation_color_map = {}
    else:
        # Default color mapping if no file is uploaded
        delegation_color_map = {}

    # Add the GeoJSON layer to the map, coloring each delegation
    folium.GeoJson(
        tunisia_geojson,
        style_function=lambda feature: {
            'fillColor': delegation_color_map.get(feature['properties']['deleg_na_1'], 'lightgrey'), 
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.3 if feature['properties']['deleg_na_1'] not in delegation_color_map else 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['deleg_na_1', 'gov_name_f'],  # Show both delegation and governorate names
            aliases=['Délégation:', 'Gouvernorat:']  # Labels for the tooltip
        ),
    ).add_to(tunisia_map)

    # Display the map in the Streamlit app
    st_folium(tunisia_map, width=700, height=900)

else:
    st.error("Le fichier GeoJSON n'est pas chargé. Veuillez vérifier le chemin du fichier.")
