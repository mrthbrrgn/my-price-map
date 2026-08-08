import pandas as pd
import plotly.express as px
import streamlit as st

st.title("My First Interactive Price Map!")

# 1. Create fake data with locations and prices
data = {
    "City": ["New York", "London", "Tokyo", "Sydney"],
    "lat": [40.7128, 51.5074, 35.6762, -33.8688],
    "lon": [-74.0060, -0.1278, 139.6503, 151.2093],
    "Price_Change_%": [5.2, -2.1, 8.4, 1.1],
}
df = pd.DataFrame(data)

# 2. Add an interactive map using FREE OpenStreetMap tiles
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    color="Price_Change_%",
    size="Price_Change_%",
    hover_name="City",
    mapbox_style="open-street-map",  # 100% Free map background
    zoom=1,
)

# 3. Draw the map on the screen
st.plotly_chart(fig)
