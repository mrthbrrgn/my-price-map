import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")
st.title("US & Europe Commodity Price Tracker & Forecast")

# 1. Base dataset for US and Europe Hubs
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


# 2. Helper function to generate 18-month historical trends, averages, and forecasts
def generate_price_history_and_forecast(df):
    np.random.seed(42)

    quarters = ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025", "Q1-2026", "Q2-2026"]

    history_data = []
    for idx, row in df.iterrows():
        base = row["Base_Price"]
        q_prices = [
            round(base * (1 + np.random.uniform(-0.08, 0.08)), 2)
            for _ in quarters
        ]

        avg_last_6m = round((q_prices[-2] + q_prices[-1]) / 2, 2)
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

st.subheader("1. Enter Budgeted Prices & Forecast Assumptions")
st.caption("Set internal budgeted prices and forecast shifts for US/EU hubs.")

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

df_full = df_base[
    ["Commodity", "Region", "Hub Location", "lat", "lon", "Base_Price"]
].merge(
    edited_input_df, on=["Commodity", "Region", "Hub Location"], how="left"
)

df_full["Budgeted Price"] = df_full["Budgeted Price"].fillna(1.0)
df_full["Forecast_Shift_%"] = df_full["Forecast_Shift_%"].fillna(0.0)

df_processed = generate_price_history_and_forecast(df_full)

st.markdown("---")

# Section 2: Historical Trends Table & Interactive Line Chart
st.subheader("2. 18-Month Quarterly Trends & 6M Forecast")

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

# Graph 1: Historical Trend & Forecast Line Chart
st.markdown("#### 📈 Price Trend Trajectory (Past 18 Months + 6M Forecast)")

time_cols = [
    "Q1-2025",
    "Q2-2025",
    "Q3-2025",
    "Q4-2025",
    "Q1-2026",
    "Current (Q2-2026)",
    "6M Forecast Price",
]

fig_line = go.Figure()

for idx, row in df_processed.iterrows():
    label = f"{row['Commodity']} ({row['Region']} - {row['Unit']})"
    values = [row[col] for col in time_cols]

    fig_line.add_trace(
        go.Scatter(
            x=time_cols,
            y=values,
            mode="lines+markers",
            name=label,
            hovertemplate=f"<b>{label}</b><br>Period: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>",
        )
    )

fig_line.update_layout(
    xaxis_title="Timeline (Quarters to 6M Forecast)",
    yaxis_title="Price",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# Section 3: Budget Variance Bar Chart & Map
col_chart, col_map = st.columns([1, 1])

with col_chart:
    st.subheader("3. Budget vs Forecasted Price Comparison")

    fig_bar = go.Figure()

    labels = [
        f"{r['Commodity']} ({r['Region']})" for _, r in df_processed.iterrows()
    ]

    fig_bar.add_trace(
        go.Bar(
            x=labels,
            y=df_processed["Budgeted Price"],
            name="Budgeted Price",
            marker_color="#4A90E2",
        )
    )

    fig_bar.add_trace(
        go.Bar(
            x=labels,
            y=df_processed["6M Forecast Price"],
            name="6M Forecast Price",
            marker_color="#E74C3C",
        )
    )

    fig_bar.update_layout(
        barmode="group",
        xaxis_title="Commodity & Region",
        yaxis_title="Price",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig_bar, use_container_width=True)

with col_map:
    st.subheader("4. US & Europe Predictive Map")

    fig_map = px.scatter_map(
        df_processed,
        lat="lat",
        lon="lon",
        color="Forecast Shift %",
        size=df_processed["Forecast Shift %"].abs() + 3,
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
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)
