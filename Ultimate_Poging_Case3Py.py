import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px

# Inlezen van de bestanden
bestanden = [
    '2021 Q2 spring (Apr-Jun)-Central.csv',
    '2021 Q3 (Jul-Sep)-Central.csv',
    '2021 Q4 autumn (Oct-Dec)-Central.csv'
]

dfs = [pd.read_csv(file) for file in bestanden]
fiets_data_jaar = pd.concat(dfs, ignore_index=True)

# Door index_col=0 te gebruiken, zorg je ervoor dat de eerste kolom (datum) als index wordt ingelezen.
weer_data = pd.read_csv('weather_london.csv', index_col=0)
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')

# Format de datumkolom in fiets_data_jaar van DD/MM/YYYY naar datetime
fiets_data_jaar['Date'] = pd.to_datetime(fiets_data_jaar['Date'], format='%d/%m/%Y')

# Weerdata: Zet de index (die nu de datum bevat) om naar datetime en maak er een 'Date'-kolom van.
weer_data.index = pd.to_datetime(weer_data.index, format='%Y-%m-%d')
weer_data = weer_data.reset_index().rename(columns={'index': 'Date'})

# Maak een dictionary met stations { "StationName": (latitude, longitude) }
stations_dict = {
    row["Station"]: (row["Latitude"], row["Longitude"]) 
    for _, row in metro_stations_data.iterrows()
}

# Maak een folium map
m = folium.Map(location=[51.509865, -0.118092], tiles='CartoDB positron', zoom_start=11)

# Voeg cirkelmarkers toe voor elk metrostation
for idx, row in metro_data.iterrows():
    station_name = row["Station"]  # Zorg dat deze kolomnaam klopt met je CSV
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

# Groepeer fietsdata per dag en tel de counts op (96 rijen per dag)
bike_daily = fiets_data_jaar.groupby('Date')['Count'].sum().reset_index()

# Merge de weerdata met de geaggregeerde fietsdata op datum
merged_data = pd.merge(weer_data, bike_daily, on='Date', how='inner')

# Maak de scatterplot met Plotly: gemiddelde temperatuur vs. aantal fietsers per dag
fig = px.scatter(merged_data, 
                 x='tavg', 
                 y='Count', 
                 hover_data=['Date'],
                 labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Count': 'Aantal Fietsers per Dag'},
                 title='Correlatie tussen Weer en Fietsers')

st.plotly_chart(fig)
