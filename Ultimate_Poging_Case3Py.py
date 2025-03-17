import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd

bestanden = [
    '2021 Q2 spring (Apr-Jun)-Central.csv',
    '2021 Q3 (Jul-Sep)-Central.csv',
    '2021 Q4 autumn (Oct-Dec)-Central.csv'
]

dfs = [pd.read_csv(file) for file in bestanden]

fiets_data_jaar = pd.concat(dfs, ignore_index=True)
weer_data = pd.read_csv('weather_london.csv')
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')

# Convert AnnualisedEnEx to numeric to avoid string/float issues
metro_data["AnnualisedEnEx"] = pd.to_numeric(metro_data["AnnualisedEnEx"], errors="coerce")

# Dictionary of { "StationName": (latitude, longitude) }
stations_dict = {
    row["Station"]: (row["Latitude"], row["Longitude"])
    for _, row in metro_stations_data.iterrows()
}

# Use a simpler, "prettier" tile set
m = folium.Map(location=[51.509865, -0.118092], tiles='CartoDB positron', zoom_start=11)

# Loop through every station in AC2021_AnnualisedEntryExit
for idx, row in metro_data.iterrows():
    station_name = row["Station"]
    busy_value = row["AnnualisedEnEx"]

    # Check if this station exists in the dictionary and busy_value is valid
    if station_name in stations_dict and pd.notnull(busy_value):
        lat, lon = stations_dict[station_name]

        # Adjust the scale factor if needed
        scale_factor = 10000  # e.g. 100k instead of 1 million
        radius = busy_value / scale_factor

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=f"{station_name}: {busy_value:,}",
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

folium_static(m)
