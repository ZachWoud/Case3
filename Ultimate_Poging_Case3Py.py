import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px

# Lees fietsdata (per dag) in
fiets_data = pd.read_csv('fietsdata2021_rentals_by_day.csv')

# Weather-data inlezen; index_col=0 als de datum in de eerste kolom staat
weer_data = pd.read_csv('weather_london.csv', index_col=0)

# Metro-data
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')

# 1) Datumkolommen op juiste formaat
# Fietsdata: 'Day' omzetten naar datetime en opslaan als 'Date'
fiets_data['Date'] = pd.to_datetime(fiets_data['Day'])
# Weerdata: index omzetten naar datetime en daarna als kolom opslaan
weer_data.index = pd.to_datetime(weer_data.index, format='%Y-%m-%d', errors='coerce')
weer_data = weer_data.reset_index().rename(columns={'index': 'Date'})

# 2) Controleer op missing values en verwijder die indien nodig
fiets_data.dropna(subset=['Date', 'Total Rentals'], inplace=True)
weer_data.dropna(subset=['Date', 'tavg'], inplace=True)

# 3) Merge de datasets op overlappende data (inner join)
merged_data = pd.merge(weer_data, fiets_data, on='Date', how='inner')

# 4) Plot de scatterplot met Plotly: tavg vs Total Rentals
fig = px.scatter(
    merged_data,
    x='tavg', 
    y='Total Rentals',
    hover_data=['Date'],
    labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Total Rentals': 'Aantal Fietsverhuur per Dag'},
    title='Correlatie tussen Weer en Fietsverhuur'
)
st.plotly_chart(fig)

# ----------------------------------------------------
# Folium-kaart code blijft ongewijzigd
# ----------------------------------------------------

# Dictionary van station-locaties
stations_dict = {
    row["Station"]: (row["Latitude"], row["Longitude"]) 
    for _, row in metro_stations_data.iterrows()
}

m = folium.Map(location=[51.509865, -0.118092], tiles='CartoDB positron', zoom_start=11)

for idx, row in metro_data.iterrows():
    station_name = row["Station"]
    busy_value = pd.to_numeric(row["AnnualisedEnEx"], errors="coerce")
    if station_name in stations_dict:
        lat, lon = stations_dict[station_name]
        scale_factor = 1000
        radius = busy_value / scale_factor if pd.notnull(busy_value) else 2
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=f"{station_name}: {busy_value:,}" if pd.notnull(busy_value) else station_name,
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

folium_static(m)
