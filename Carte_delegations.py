import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# Cache reading the GeoJSON file
@st.cache_resource
def load_geojson(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Cache reading the uploaded file
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    return None

# Predefined intervals for color mapping
DEFAULT_INTERVALS = [
    ("0-1000", "yellow"),
    ("1001-2000", "orange"),
    ("2001-3000", "red"),
    ("3001-4000", "purple"),
    ("4001-5000", "blue"),
    ("5001+", "green")
]

# Function to map values to colors
def get_color(value, intervals):
    try:
        value = float(value)
        for interval, color in intervals:
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

# Load GeoJSON file
geojson_path = 'delegations-full.geojson'  # Replace with actual path
try:
    tunisia_geojson = load_geojson(geojson_path)
except FileNotFoundError:
    tunisia_geojson = None
    st.error("Fichier GeoJSON des limites des délégations non trouvé.")

# App Title
st.title("Carte des Délégations de Tunisie")

# Sidebar for file upload and intervals
uploaded_file = st.sidebar.file_uploader("Ajouter un fichier CSV ou Excel", type=["csv", "xlsx"])
interval_inputs = [st.sidebar.text_input(f"Intervalle {i+1}", default) for i, (default, _) in enumerate(DEFAULT_INTERVALS)]
intervals = [(interval, color) for interval, (_, color) in zip(interval_inputs, DEFAULT_INTERVALS)]

# Reset Button
if st.sidebar.button("Réinitialiser"):
    st.experimental_rerun()

# Initialize Map
tunisia_map = folium.Map(location=[33.8869, 9.5375], zoom_start=7)

# If GeoJSON is available, add it to the map
if tunisia_geojson:
    folium.GeoJson(
        tunisia_geojson,
        style_function=lambda feature: {
            'fillColor': 'lightgrey',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.3,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['deleg_na_1', 'gov_name_f'],
            aliases=['Délégation:', 'Gouvernorat:']
        ),
    ).add_to(tunisia_map)

# If file is uploaded, apply data to map
if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        if 'Valeurs' in df.columns and 'Delegations' in df.columns:
            delegation_color_map = {
                row['Delegations']: get_color(row['Valeurs'], intervals)
                for _, row in df.iterrows()
            }
            
            folium.GeoJson(
                tunisia_geojson,
                style_function=lambda feature: {
                    'fillColor': delegation_color_map.get(feature['properties']['deleg_na_1'], 'lightgrey'),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7 if feature['properties']['deleg_na_1'] in delegation_color_map else 0.3,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['deleg_na_1', 'gov_name_f'],
                    aliases=['Délégation:', 'Gouvernorat:']
                ),
            ).add_to(tunisia_map)
        else:
            st.error("Le fichier doit contenir les colonnes 'Delegations' et 'Valeurs'.")

# Display the map
st_folium(tunisia_map, width=700, height=900)
