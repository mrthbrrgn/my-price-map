import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

st.set_page_config(layout="wide")
st.title("Raw Materials & Chemical Commodity Price Tracker")


# 1. Fetch live or benchmark market data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_commodity_data():
    # Define mapping of commodities, market symbols/tickers, and production hubs
    commodities = [
        {
            "Commodity": "Coconut Oil",
            "Ticker": "OJZ24.CBT",  # Benchmark vegetable oil / ag proxy
            "Default_Change_%": 3.4,
            "City": "Manila (Philippines Hub)",
            "lat": 14.5995,
            "lon": 120.9842,
        },
        {
            "Commodity": "Palm Oil",
            "Ticker": "FCPO.KL",  # Crude Palm Oil Futures (Bursa Malaysia)
            "Default_Change_%": -1.8,
            "City": "Kuala Lumpur (Malaysia Hub)",
            "lat": 3.1390,
            "lon": 101.6869,
        },
        {
            "Commodity": "IPA (Isopropyl Alcohol)",
            "Ticker": "CL=F",  # Petrochemical feedstock / Crude proxy
            "Default_Change_%": 2.1,
            "City": "Houston (US Gulf Coast Hub)",
            "lat": 29.7604,
            "lon": -95.3698,
        },
        {
            "Commodity": "Silicones",
            "Ticker": "SI=F",  # Silicon / Industrial Metal Proxy
            "Default_Change_%": 0.5,
            "City": "Shanghai (China Hub)",
            "lat": 31.2304,
            "lon": 121.4737,
        },
        {
            "Commodity": "Glycerin",
            "Ticker": "ZL=F",  # Oleochemical / Soybean Oil Proxy
            "Default_Change_%": -3.2,
            "City": "Rotterdam (EU Chemical Hub)",
            "lat": 51.9244,
            "lon": 4.4777,
        },
    ]

    records = []
    for item in commodities:
        try:
            # Try pulling live 1-month market trend from Yahoo Finance
            ticker = yf.Ticker(item["Ticker"])
            hist = ticker.history(period="1m")
            if len(hist) >= 2:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                pct_change = round(
                    ((end_price - start_price) / start_price) * 100, 2
                )
            else:
                pct_change = item["Default_Change_%"]
        except Exception:
            pct_change = item["Default_Change_%"]

        records.append({
            "Commodity": item["Commodity"],
            "Hub Location": item["City"],
            "lat": item["lat"],
            "lon": item["lon"],
            "Price_Change_%": pct_change,
        })

    return pd.DataFrame(records)


# Load data
df_data = get_commodity_data()

# 2. Interactive App Layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Edit Commodity Price Trends")
    st.caption(
        "Modify the values below or add new raw materials to update the map."
    )
    edited_df = st.data_editor(
        df_data,
        num_rows="dynamic",
        use_container_width=True,
    )

with col2:
    st.subheader("Global Commodity Trend Map")

    fig = px.scatter_map(
        edited_df,
        lat="lat",
        lon="lon",
        color="Price_Change_%",
        size=edited_df["Price_Change_%"].abs() + 1,  # Prevent 0 size
        color_continuous_scale="RdYlGn_r",  # Red = Price Increase, Green = Decrease
        hover_name="Commodity",
        hover_data={"Hub Location": True, "Price_Change_%": ":.2f%"},
        map_style="open-street-map",
        zoom=1,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)
