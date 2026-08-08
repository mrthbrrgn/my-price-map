import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")
st.title("US & Europe Commodity Price Tracker & Forecast")

# 1. Base dataset for US and Europe Hubs with Specified Units
initial_commodities = [
    {
        "Commodity": "Coconut Oil",
        "Region": "Europe",
        "Hub Location": "Rotterdam (EU Hub)",
        "lat": 51.9244,
        "lon": 4.4777,
        "Unit": "$/tonne",
        "Base_Price": 1650.0,
    },
    {
        "Commodity": "Palm Oil",
        "Region": "Europe",
        "Hub Location": "Hamburg (EU Hub)",
        "lat": 53.5511,
        "lon": 9.9937,
        "Unit": "$/tonne",
        "Base_Price": 980.0,
    },
    {
        "Commodity": "IPA (Isopropyl Alcohol)",
        "Region": "US",
        "Hub Location": "Houston (US Gulf Coast)",
        "lat": 29.7604,
        "lon": -95.3698,
        "Unit": "$/kg",
        "Base_Price": 1.45,
    },
    {
        "Commodity": "Silicones",
        "Region": "US",
        "Hub Location": "Midland, MI (US)",
        "lat": 43.6156,
        "lon": -84.2472,
        "Unit": "$/kg",
        "Base_Price": 3.80,
    },
    {
        "Commodity": "Silicones",
        "Region": "Europe",
        "Hub Location": "Frankfurt (EU Hub)",
        "lat": 50.1109,
        "lon": 8.6821,
        "Unit": "$/kg",
        "Base_Price": 4.10,
    },
    {
        "Commodity": "Glycerin",
        "Region": "US",
        "Hub Location": "Chicago (US Hub)",
        "lat": 41.8781,
        "lon": -87.6298,
        "Unit": "$/tonne",
        "Base_Price": 820.0,
    },
]

df_base = pd.DataFrame(initial_commodities)


# 2. Helper function to generate 18-month historical trends and average of last 6 months
def generate_price_history_and_forecast(df):
    np.random.seed(42)  # Consistent trend simulation

    quarters = ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025", "Q1-2026", "Q2-2026"]

    history_data = []
    for idx, row in df.iterrows():
        base = row["Base_Price"]
        q_prices = [
            round(base * (1 + np.random.uniform(-0.08, 0.08)), 2)
            for _ in quarters
        ]

        # Calculate Average Price of Last 6 Months (Q1-2026 and Q2-2026)
        avg_last_6m = round((q_prices[-2] + q_prices[-1]) / 2, 2)

        # 6-Month Forecast calculated from current price
        forecast_price = round(q_prices[-1] * (1 + row["Forecast_Shift_%"] / 100), 2)
        price_delta_pct = round(
            ((forecast_price - q_prices[-1]) / q_prices[-1]) * 100, 2
        )

        record = {
            "Commodity": row["Commodity"],
            "Region": row["Region"],
            "Hub Location": row["Hub Location"],
            "lat": row["lat"],
            "lon": row["lon"],
            "Unit": row["Unit"],
            "Budgeted Price": row["Budgeted Price"],
            "Q1-2025": q_prices[0],
            "Q2-2025": q_prices[1],
            "Q3-2025": q_prices[2],
            "Q4-2025": q_prices[3],
            "Q1-2026": q_prices[4],
            "Current (Q2-2026)": q_prices[-1],
            "Avg Price (Last 6M)": avg_last_6m,
            "6M Forecast Price": forecast_price,
            "Forecast Shift %": price_delta_pct,
            "Variance vs Budget (%)": round(
                ((forecast_price - row["Budgeted Price"]) / row["Budgeted Price"])
                * 100,
                2,
            ),
        }
        history_data.append(record)

    return pd.DataFrame(history_data)


# Add default budget & forecast assumption columns to base table
df_base["Budgeted Price"] = df_base["Base_Price"] * 0.95
df_base["Forecast_Shift_%"] = [4.5, -2.0, 6.1, 1.8, 3.2, -4.0]

# -------------------------------------------------------------
# App Layout & User Inputs
# -------------------------------------------------------------

# Section 1: Budget Entry & Forecast Controls
st.subheader("1. Enter Budgeted Prices & Forecast Assumptions")
st.caption(
    "Set your internal budgeted prices and forecasted price shifts for US and Europe locations."
)

edited_input_df = st.data_editor(
    df_base[
        [
            "Commodity",
            "Region",
            "Hub Location",
            "Unit",
            "Budgeted Price",
            "Forecast_Shift_%",
        ]
    ],
    use_container_width=True,
    num_rows="dynamic",
)

# Merge edited inputs back with base dataset
df_full = df_base[
    ["Commodity", "Region", "Hub Location", "lat", "lon", "Base_Price"]
].merge(
    edited_input_df, on=["Commodity", "Region", "Hub Location"], how="left"
)

df_full["Budgeted Price"] = df_full["Budgeted Price"].fillna(1.0)
df_full["Forecast_Shift_%"] = df_full["Forecast_Shift_%"].fillna(0.0)

# Process trends & metrics
df_processed = generate_price_history_and_forecast(df_full)

st.markdown("---")

# Section 2: Historical Trends, 6-Month Average & 6-Month Forecast Table
st.subheader("2. 18-Month Quarterly Trends, 6M Average & 6M Forecast")
st.dataframe(
    df_processed[
        [
            "Commodity",
            "Region",
            "Hub Location",
            "Unit",
            "Budgeted Price",
            "Q1-2025",
            "Q2-2025",
            "Q3-2025",
            "Q4-2025",
            "Q1-2026",
            "Current (Q2-2026)",
            "Avg Price (Last 6M)",
            "6M Forecast Price",
            "Forecast Shift %",
            "Variance vs Budget (%)",
        ]
    ],
    use_container_width=True,
)

# Section 3: Interactive Spatial Heatmap
st.subheader("3. US & Europe Predictive Map")

fig = px.scatter_map(
    df_processed,
    lat="lat",
    lon="lon",
    color="Forecast Shift %",
    size=df_processed["Forecast Shift %"].abs() + 2,
    color_continuous_scale="RdYlGn_r",
    hover_name="Commodity",
    hover_data={
        "Region": True,
        "Hub Location": True,
        "Unit": True,
        "Current (Q2-2026)": ":.2f",
        "Avg Price (Last 6M)": ":.2f",
        "6M Forecast Price": ":.2f",
        "Budgeted Price": ":.2f",
        "Variance vs Budget (%)": ":.2f%",
    },
    map_style="open-street-map",
    zoom=2,
    center={"lat": 42.0, "lon": -40.0},
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig, use_container_width=True)
