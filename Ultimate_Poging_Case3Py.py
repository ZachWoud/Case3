import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px

# Voorbeeldbestanden
bestanden = [
    '2021 Q2 spring (Apr-Jun)-Central.csv',
    '2021 Q3 (Jul-Sep)-Central.csv',
    '2021 Q4 autumn (Oct-Dec)-Central.csv'
]

dfs = [pd.read_csv(file) for file in bestanden]
fiets_data_jaar = pd.concat(dfs, ignore_index=True)

# Weather-data inlezen; index_col=0 als de datum in de eerste kolom staat
weer_data = pd.read_csv('weather_london.csv', index_col=0)

# Metro-data
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')

# 1) Datumkolommen op juiste formaat
# Fietsdata: DD/MM/YYYY -> datetime
fiets_data_jaar['Date'] = pd.to_datetime(fiets_data_jaar['Date'], format='%d/%m/%Y')

# Weerdata: index omzetten naar datetime en daarna als kolom opslaan
weer_data.index = pd.to_datetime(weer_data.index, format='%Y-%m-%d', errors='coerce')
weer_data = weer_data.reset_index().rename(columns={'index': 'Date'})

# 2) Controleer op missing values en verwijder die indien nodig
#    Zo voorkom je dat 'lege' dagen toch meege-merged worden.
fiets_data_jaar.dropna(subset=['Date', 'Count'], inplace=True)
weer_data.dropna(subset=['Date', 'tavg'], inplace=True)

# 3) Groepeer fietsdata per dag en tel de counts op
bike_daily = fiets_data_jaar.groupby('Date')['Count'].sum().reset_index()

# 4) Merge alleen op overlappende data (inner) => uitsluitend dagen die in beide sets voorkomen
merged_data = pd.merge(weer_data, bike_daily, on='Date', how='inner')

# 5) Plot een scatterplot met Plotly
fig = px.scatter(
    merged_data,
    x='tavg', 
    y='Count',
    hover_data=['Date'],
    labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Count': 'Aantal Fietsers per Dag'},
    title='Correlatie tussen Weer en Fietsers'
)
st.plotly_chart(fig)

# ----------------------------------------------------
# Hieronder de rest van je code voor de Folium-kaart, 
# als je die ook wilt tonen.
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
