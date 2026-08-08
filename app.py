import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")
st.title("My First Interactive Price Map!")
st.write("Edit the table below to see the map update live!")

# 1. Default starting data
default_data = pd.DataFrame(
    [
        {"City": "New York", "lat": 40.7128, "lon": -74.0060, "Price_Change_%": 5.2},
        {"City": "London", "lat": 51.5074, "lon": -0.1278, "Price_Change_%": -2.1},
        {"City": "Tokyo", "lat": 35.6762, "lon": 139.6503, "Price_Change_%": 8.4},
        {"City": "Sydney", "lat": -33.8688, "lon": 151.2093, "Price_Change_%": 1.1},
        {"City": "Mexico City", "lat": 19.4326, "lon": -99.1332, "Price_Change_%": 3.5},
    ]
)

# 2. Layout columns
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Edit Data")
    edited_df = st.data_editor(
        default_data,
        num_rows="dynamic",
        use_container_width=True,
    )

with col2:
    st.subheader("Live Map")
    
    # Updated to px.scatter_map (avoids Plotly version deprecation errors)
    fig = px.scatter_map(
        edited_df,
        lat="lat",
        lon="lon",
        color="Price_Change_%",
        size=edited_df["Price_Change_%"].abs(),
        color_continuous_scale="RdYlGn_r",
        hover_name="City",
        map_style="open-street-map",  # Updated parameter name
        zoom=1,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)
