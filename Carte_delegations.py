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
    ("0-20", "yellow"),
    ("21-40", "orange"),
    ("41-60", "red"),
    ("61-80", "purple"),
    ("81-100", "blue"),
    ("101+", "green")
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
if tunisia_geojson:
    tunisia_map = folium.Map(location=[33.8869, 9.5375], zoom_start=7)

    if uploaded_file:
        df = load_data(uploaded_file)

        if 'Valeurs' in df.columns and 'Delegations' in df.columns:
            delegation_color_map = {
                row['Delegations']: get_color(row['Valeurs'], intervals)
                for _, row in df.iterrows()
            }
        else:
            st.error("Le fichier doit contenir les colonnes 'Delegations' et 'Valeurs'.")
            delegation_color_map = {}

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

        st_folium(tunisia_map, width=700, height=900)
    else:
        st.info("Veuillez uploader un fichier pour voir les données.")
else:
    st.error("Le fichier n'est pas chargé. Veuillez vérifier le chemin.")
