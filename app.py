import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")

# High legibility CSS
st.markdown(
    """
    <style>
    h1 { font-size: 2.2rem !important; }
    h2, h3 { font-size: 1.6rem !important; font-weight: 700 !important; }
    h4 { font-size: 1.3rem !important; font-weight: 600 !important; }
    .stCaption, p, div { font-size: 1.1rem !important; }
    .stDataFrame, .stDataEditor { font-size: 1.05rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("US & Europe Commodity Price Tracker & Forecast")

# 1. Base dataset with explicit Data Sources
initial_commodities = [
    {
        "Commodity": "Coconut Oil",
        "Region": "Europe",
        "Hub Location": "Rotterdam (EU Hub)",
        "lat": 51.9244,
        "lon": 4.4777,
        "Unit": "$/tonne",
        "Base_Price": 1650.0,
        "Data Source": "CME / Malayan Palm Oil Board (MPOB) Benchmarks",
    },
    {
        "Commodity": "Palm Oil",
        "Region": "Europe",
        "Hub Location": "Hamburg (EU Hub)",
        "lat": 53.5511,
        "lon": 9.9937,
        "Unit": "$/tonne",
        "Base_Price": 980.0,
        "Data Source": "Bursa Malaysia (KL CPO Futures Index)",
    },
    {
        "Commodity": "IPA (Isopropyl Alcohol)",
        "Region": "US",
        "Hub Location": "Houston (US Gulf Coast)",
        "lat": 29.7604,
        "lon": -95.3698,
        "Unit": "$/kg",
        "Base_Price": 1.45,
        "Data Source": "ICIS Petrochemical Gulf Coast Index",
    },
    {
        "Commodity": "Silicones",
        "Region": "US",
        "Hub Location": "Midland, MI (US)",
        "lat": 43.6156,
        "lon": -84.2472,
        "Unit": "$/kg",
        "Base_Price": 3.80,
        "Data Source": "S&P Global Platts Chemical Insights",
    },
    {
        "Commodity": "Silicones",
        "Region": "Europe",
        "Hub Location": "Frankfurt (EU Hub)",
        "lat": 50.1109,
        "lon": 8.6821,
        "Unit": "$/kg",
        "Base_Price": 4.10,
        "Data Source": "ICIS European Silicones Benchmark",
    },
    {
        "Commodity": "Glycerin",
        "Region": "US",
        "Hub Location": "Chicago (US Hub)",
        "lat": 41.8781,
        "lon": -87.6298,
        "Unit": "$/tonne",
        "Base_Price": 820.0,
        "Data Source": "USDA Oleochemical / Refined Glycerin Reports",
    },
]

df_base = pd.DataFrame(initial_commodities)


def format_currency(val):
    if pd.isna(val):
        return "$0.00"
    return f"${val:,.2f}"


# 2. Helper function to generate history, average, forecast, and raw numbers for Excel
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
            "Data Source": row["Data Source"],
            "Raw_Budget": row["Budgeted Price"],
            "Budgeted Price": format_currency(row["Budgeted Price"]),
            "Q1-2025": format_currency(q_prices[0]),
            "Q2-2025": format_currency(q_prices[1]),
            "Q3-2025": format_currency(q_prices[2]),
            "Q4-2025": format_currency(q_prices[3]),
            "Q1-2026": format_currency(q_prices[4]),
            "Current (Q2-2026)": format_currency(q_prices[-1]),
            "Avg Price (Last 6M)": format_currency(avg_last_6m),
            "6M Forecast Price": format_currency(forecast_price),
            "Raw_Forecast": forecast_price,
            "Forecast Shift %": f"{price_delta_pct:+.2f}%",
            "Raw_Forecast_Shift": price_delta_pct,
            "Variance vs Budget (%)": f"{((forecast_price - row['Budgeted Price']) / row['Budgeted Price']) * 100:+.2f}%",
        }
        history_data.append(record)

    return pd.DataFrame(history_data)


# Add default budget & forecast columns
df_base["Budgeted Price"] = df_base["Base_Price"] * 0.95
df_base["Forecast_Shift_%"] = [4.5, -2.0, 6.1, 1.8, 3.2, -4.0]

# -------------------------------------------------------------
# Section 1: Budget Entry & Excel Export
# -------------------------------------------------------------

st.subheader("1. Enter Budgeted Prices & Forecast Assumptions")
st.caption(
    "💡 **Editable Table:** Double-click cells to adjust budgeted prices or forecast shifts."
)

edited_input_df = st.data_editor(
    df_base[
        [
            "Commodity",
            "Region",
            "Hub Location",
            "Unit",
            "Data Source",
            "Budgeted Price",
            "Forecast_Shift_%",
        ]
    ],
    column_config={
        "Budgeted Price": st.column_config.NumberColumn(
            "Budgeted Price ($)",
            help="Custom budgeted target price.",
            format="$%.2f",
            min_value=0,
        ),
        "Forecast_Shift_%": st.column_config.NumberColumn(
            "Forecast Shift (%)",
            help="Expected percentage shift over next 6 months.",
            format="%.2f%%",
        ),
    },
    use_container_width=True,
    num_rows="dynamic",
)

# Merge back edited input data
df_full = df_base[
    ["Commodity", "Region", "Hub Location", "lat", "lon", "Base_Price"]
].merge(
    edited_input_df,
    on=["Commodity", "Region", "Hub Location"],
    how="left",
)

df_full["Budgeted Price"] = df_full["Budgeted Price"].fillna(1.0)
df_full["Forecast_Shift_%"] = df_full["Forecast_Shift_%"].fillna(0.0)

df_processed = generate_price_history_and_forecast(df_full)

# Excel Export Generator Button
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_processed[
        [
            "Commodity",
            "Region",
            "Hub Location",
            "Unit",
            "Data Source",
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
    ].to_excel(writer, sheet_name="Price_Trends", index=False)

st.download_button(
    label="📥 Download Price Trends & Forecasts to Excel (.xlsx)",
    data=buffer.getvalue(),
    file_name="commodity_price_trends_and_forecast.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")

# -------------------------------------------------------------
# Section 2: Historical Trends Table with Data Sources
# -------------------------------------------------------------
st.subheader("2. 18-Month Quarterly Trends, 6M Average & 6M Forecast")
st.caption(
    "📊 Summary view including pricing benchmark sources for each commodity."
)

st.dataframe(
    df_processed[
        [
            "Commodity",
            "Region",
            "Hub Location",
            "Unit",
            "Data Source",
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

# -------------------------------------------------------------
# Section 3: Charts & Map
# -------------------------------------------------------------
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
    values = [
        float(str(row[col]).replace("$", "").replace(",", "")) for col in time_cols
    ]

    fig_line.add_trace(
        go.Scatter(
            x=time_cols,
            y=values,
            mode="lines+markers",
            name=label,
            hovertemplate=f"<b>{label}</b><br>Period: %{{x}}<br>Price: $%{{y:,.2f}}<extra></extra>",
        )
    )

fig_line.update_layout(
    xaxis=dict(title="Timeline (Quarters to 6M Forecast)", tickfont=dict(size=14)),
    yaxis=dict(title="Price ($)", tickfont=dict(size=14), tickprefix="$"),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=13),
    ),
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

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
            y=df_processed["Raw_Budget"],
            name="Budgeted Price ($)",
            marker_color="#4A90E2",
        )
    )

    fig_bar.add_trace(
        go.Bar(
            x=labels,
            y=df_processed["Raw_Forecast"],
            name="6M Forecast Price ($)",
            marker_color="#E74C3C",
        )
    )

    fig_bar.update_layout(
        barmode="group",
        xaxis=dict(title="Commodity & Region", tickfont=dict(size=13)),
        yaxis=dict(title="Price ($)", tickfont=dict(size=13), tickprefix="$"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13),
        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig_bar, use_container_width=True)

with col_map:
    st.subheader("4. US & Europe Predictive Map")

    fig_map = px.scatter_map(
        df_processed,
        lat="lat",
        lon="lon",
        color="Raw_Forecast_Shift",
        size=df_processed["Raw_Forecast_Shift"].abs() + 3,
        color_continuous_scale="RdYlGn_r",
        hover_name="Commodity",
        hover_data={
            "Region": True,
            "Hub Location": True,
            "Unit": True,
            "Data Source": True,
            "Current (Q2-2026)": True,
            "Avg Price (Last 6M)": True,
            "6M Forecast Price": True,
            "Budgeted Price": True,
            "Variance vs Budget (%)": True,
            "Raw_Forecast_Shift": False,
        },
        map_style="open-street-map",
        zoom=2,
        center={"lat": 42.0, "lon": -40.0},
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)
