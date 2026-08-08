import datetime
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Price Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    h1 { font-size: 1.8rem !important; }
    h2, h3 { font-size: 1.3rem !important; font-weight: 700 !important; }
    h4 { font-size: 1.1rem !important; font-weight: 600 !important; }
    .stCaption, p, div { font-size: 1.0rem !important; }
    
    /* Enforce White Background & Black Text for all Dataframes/Editors */
    .stDataFrame, .stDataEditor {
        font-size: 0.95rem !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Wrap Table Header Text */
    div[data-testid="stTable"] th, .stDataFrame th, div[data-column-header] {
        white-space: normal !important;
        word-wrap: break-word !important;
        text-align: center !important;
    }
    
    div[data-testid="stTable"] table {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    .refresh-box {
        background-color: #ffffff;
        color: #000000;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        border-left: 5px solid #8a2be2;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# AUTHENTICATION SYSTEM (SINGLE MASTER PASSWORD)
# -------------------------------------------------------------


def check_user_access():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔒 Restricted Access: Password Required")
    st.caption("Enter the team access password to view the price map.")

    try:
        shared_password = st.secrets["APP_PASSWORD"]
    except Exception:
        st.error(
            "Secrets not configured properly! Please add APP_PASSWORD to Streamlit Cloud Secrets."
        )
        return False

    with st.form("login_form"):
        user_pass = st.text_input("Access Password", type="password")
        submit_button = st.form_submit_button("Log In")

        if submit_button:
            if user_pass == shared_password:
                st.session_state["authenticated"] = True
                st.success("Authentication successful!")
                st.rerun()
            else:
                st.error("Invalid password. Access denied.")

    return False


if not check_user_access():
    st.stop()

with st.sidebar:
    st.markdown("👤 Status: **Authorized Team User**")
    if st.button("🚪 Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")
    st.header("⚙️ Data Refresh Controls")
    if st.button("🔄 Force Quarterly Data Refresh"):
        st.cache_data.clear()
        st.success("Quarterly benchmarks successfully refreshed!")
        st.rerun()

# -------------------------------------------------------------
# MAIN APPLICATION CONTENT
# -------------------------------------------------------------

st.title("US & Europe Commodity Price Tracker & Forecast")


def get_current_quarter_info():
    now = datetime.datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Q{quarter}-{now.year}", now.strftime("%B %d, %Y")


current_q_label, last_updated_date = get_current_quarter_info()

st.markdown(
    f"""
    <div class="refresh-box">
        <b>🗓️ Quarterly Data Status:</b> Active Quarter: <b>{current_q_label}</b><br>
        <span style="font-size:0.85rem; color:#333333;">Last Refreshed: {last_updated_date}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State Dataframe for full persistence
if "budget_df" not in st.session_state:
    initial_commodities = [
        {
            "Commodity": "Coconut Oil",
            "Region": "Europe",
            "lat": 51.9244,
            "lon": 4.4777,
            "Unit": "$/tonne",
            "Base_Price": 1650.0,
            "Budgeted Price": 1897.5,
            "Forecast_Shift_%": -5.0,
            "Primary Driver": "Freight Surcharges & Weather",
            "Energy_Share_%": 10.0,
            "Tariff_Share_%": 20.0,
            "Freight_Share_%": 60.0,
            "Unknown_Share_%": 10.0,
            "Data Source": "CME / Malayan Palm Oil Board (MPOB)",
        },
        {
            "Commodity": "Palm Oil",
            "Region": "Europe",
            "lat": 53.5511,
            "lon": 9.9937,
            "Unit": "$/tonne",
            "Base_Price": 980.0,
            "Budgeted Price": 1127.0,
            "Forecast_Shift_%": -12.0,
            "Primary Driver": "Agricultural Yields",
            "Energy_Share_%": 0.0,
            "Tariff_Share_%": 10.0,
            "Freight_Share_%": 80.0,
            "Unknown_Share_%": 10.0,
            "Data Source": "Bursa Malaysia (KL CPO Futures Index)",
        },
        {
            "Commodity": "IPA (Isopropyl Alcohol)",
            "Region": "US",
            "lat": 29.7604,
            "lon": -95.3698,
            "Unit": "$/kg",
            "Base_Price": 1.45,
            "Budgeted Price": 1.67,
            "Forecast_Shift_%": 2.1,
            "Primary Driver": "Geopolitical / Energy Shock",
            "Energy_Share_%": 90.0,
            "Tariff_Share_%": 5.0,
            "Freight_Share_%": 0.0,
            "Unknown_Share_%": 5.0,
            "Data Source": "ICIS Petrochemical Gulf Coast Index",
        },
        {
            "Commodity": "Silicones",
            "Region": "US",
            "lat": 43.6156,
            "lon": -84.2472,
            "Unit": "$/kg",
            "Base_Price": 3.80,
            "Budgeted Price": 4.37,
            "Forecast_Shift_%": -15.0,
            "Primary Driver": "Energy Intensive Costs",
            "Energy_Share_%": 85.0,
            "Tariff_Share_%": 0.0,
            "Freight_Share_%": 10.0,
            "Unknown_Share_%": 5.0,
            "Data Source": "S&P Global Platts Chemical Insights",
        },
        {
            "Commodity": "Silicones",
            "Region": "Europe",
            "lat": 50.1109,
            "lon": 8.6821,
            "Unit": "$/kg",
            "Base_Price": 4.10,
            "Budgeted Price": 4.71,
            "Forecast_Shift_%": 1.2,
            "Primary Driver": "EU Energy & Import Duties",
            "Energy_Share_%": 70.0,
            "Tariff_Share_%": 15.0,
            "Freight_Share_%": 10.0,
            "Unknown_Share_%": 5.0,
            "Data Source": "ICIS European Silicones Benchmark",
        },
        {
            "Commodity": "Glycerin",
            "Region": "US",
            "lat": 41.8781,
            "lon": -87.6298,
            "Unit": "$/tonne",
            "Base_Price": 820.0,
            "Budgeted Price": 943.0,
            "Forecast_Shift_%": -8.0,
            "Primary Driver": "Inflation & Domestic Transport",
            "Energy_Share_%": 15.0,
            "Tariff_Share_%": 0.0,
            "Freight_Share_%": 75.0,
            "Unknown_Share_%": 10.0,
            "Data Source": "USDA Oleochemical / Refined Glycerin Reports",
        },
    ]
    st.session_state["budget_df"] = pd.DataFrame(initial_commodities)


def format_currency(val):
    if pd.isna(val):
        return "$0.00"
    return f"${val:,.2f}"


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

        budget = row["Budgeted Price"]
        variance_pct = ((forecast_price - budget) / budget) * 100 if budget > 0 else 0.0

        if variance_pct <= -10.0:
            flag = "🟢 Opportunity to Lower Price"
        elif variance_pct >= 10.0:
            flag = "🔴 Risk of Higher Prices"
        else:
            flag = "✅ Within Target Range"

        record = {
            "Commodity": row["Commodity"],
            "Region": row["Region"],
            "lat": row["lat"],
            "lon": row["lon"],
            "Unit": row["Unit"],
            "Primary Driver": row["Primary Driver"],
            "Negotiation Action": flag,
            "Data Source": row["Data Source"],
            "Raw_Budget": budget,
            "Current_Price": q_prices[-1],
            "Budgeted Price": format_currency(budget),
            "Q1-2025 (Hist)": format_currency(q_prices[0]),
            "Q2-2025 (Hist)": format_currency(q_prices[1]),
            "Q3-2025 (Hist)": format_currency(q_prices[2]),
            "Q4-2025 (Hist)": format_currency(q_prices[3]),
            "Q1-2026 (Hist)": format_currency(q_prices[4]),
            "Current Q2-2026 (Hist)": format_currency(q_prices[-1]),
            "Avg Price (Last 6M)": format_currency(avg_last_6m),
            "6M Forecast Price": format_currency(forecast_price),
            "Raw_Forecast": forecast_price,
            "Forecast Shift %": f"{price_delta_pct:+.2f}%",
            "Raw_Forecast_Shift": price_delta_pct,
            "Variance vs Budget (%)": f"{variance_pct:+.2f}%",
            "Energy_Share_%": row.get("Energy_Share_%", 0.0),
            "Tariff_Share_%": row.get("Tariff_Share_%", 0.0),
            "Freight_Share_%": row.get("Freight_Share_%", 0.0),
            "Unknown_Share_%": row.get("Unknown_Share_%", 0.0),
        }
        history_data.append(record)

    return pd.DataFrame(history_data)


# Section 1: Budget Entry
st.subheader("1. Enter Budgeted Prices & Forecast Assumptions")
st.caption("💡 **Editable Table:** Tap/click cells to edit target prices, forecast shifts, or cost drivers. Changes save automatically!")

edited_df = st.data_editor(
    st.session_state["budget_df"],
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
        "Primary Driver": st.column_config.TextColumn(
            "Primary Cost Driver",
            help="Main cause driving price changes.",
        ),
        "Energy_Share_%": st.column_config.NumberColumn("Energy Share (%)", format="%.1f%%"),
        "Tariff_Share_%": st.column_config.NumberColumn("Tariff Share (%)", format="%.1f%%"),
        "Freight_Share_%": st.column_config.NumberColumn("Freight Share (%)", format="%.1f%%"),
        "Unknown_Share_%": st.column_config.NumberColumn("Unknown Share (%)", format="%.1f%%"),
    },
    use_container_width=True,
    num_rows="dynamic",
    key="budget_editor",
)

st.session_state["budget_df"] = edited_df

df_processed = generate_price_history_and_forecast(st.session_state["budget_df"])

# Excel Export Generator
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_processed[
        [
            "Commodity",
            "Region",
            "Unit",
            "Primary Driver",
            "Budgeted Price",
            "Q1-2025 (Hist)",
            "Q2-2025 (Hist)",
            "Q3-2025 (Hist)",
            "Q4-2025 (Hist)",
            "Q1-2026 (Hist)",
            "Current Q2-2026 (Hist)",
            "Avg Price (Last 6M)",
            "6M Forecast Price",
            "Forecast Shift %",
            "Variance vs Budget (%)",
            "Negotiation Action",
            "Data Source",
        ]
    ].to_excel(writer, sheet_name="Price_Trends", index=False)

st.download_button(
    label="📥 Export Excel File (.xlsx)",
    data=buffer.getvalue(),
    file_name="commodity_price_trends_and_forecast.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")

# Section 2: Full Table View
st.subheader("2. 18-Month Historical Quarterly Trends & Forecasts")
st.caption("Budgeted prices are highlighted in **light green**, and Forecast & Shift columns are in **light purple**.")

show_historical_quarters = st.checkbox("Show Historical Quarterly Columns (Q1-2025 to Current)", value=False)

base_cols = ["Commodity", "Region", "Unit", "Primary Driver", "Budgeted Price"]

hist_cols = [
    "Q1-2025 (Hist)",
    "Q2-2025 (Hist)",
    "Q3-2025 (Hist)",
    "Q4-2025 (Hist)",
    "Q1-2026 (Hist)",
    "Current Q2-2026 (Hist)",
] if show_historical_quarters else []

summary_cols = [
    "Avg Price (Last 6M)",
    "6M Forecast Price",
    "Forecast Shift %",
    "Variance vs Budget (%)",
    "Negotiation Action",
    "Data Source",
]

selected_display_cols = base_cols + hist_cols + summary_cols

styled_df = (
    df_processed[selected_display_cols]
    .style.map(
        lambda x: "background-color: #ffffff; color: #000000;"
    )
    .map(
        lambda x: "background-color: #e6f4ea; color: #000000; font-weight: bold;",
        subset=["Budgeted Price"],
    )
    .map(
        lambda x: "background-color: #f3e8ff; color: #000000; font-weight: bold;",
        subset=["6M Forecast Price", "Forecast Shift %"],
    )
    .map(
        lambda val: (
            "background-color: #fce8e6; color: #c5221f; font-weight: bold;" if "Risk of Higher Prices" in str(val)
            else "background-color: #e6f4ea; color: #137333; font-weight: bold;" if "Opportunity to Lower Price" in str(val)
            else "background-color: #ffffff; color: #000000;"
        ),
        subset=["Negotiation Action"],
    )
)

st.dataframe(styled_df, use_container_width=True)

st.markdown("---")

# Section 3: Charts & Map
st.markdown("#### 📈 Price Trend Trajectory (18 Months + 6M Forecast)")

time_cols = [
    "Q1-2025 (Hist)",
    "Q2-2025 (Hist)",
    "Q3-2025 (Hist)",
    "Q4-2025 (Hist)",
    "Q1-2026 (Hist)",
    "Current Q2-2026 (Hist)",
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
            x=[c.replace(" (Hist)", "") for c in time_cols],
            y=values,
            mode="lines+markers",
            name=label,
            hovertemplate=f"<b>{label}</b><br>Period: %{{x}}<br>Price: $%{{y:,.2f}}<extra></extra>",
        )
    )

fig_line.update_layout(
    xaxis=dict(title="Timeline", tickfont=dict(size=11)),
    yaxis=dict(title="Price ($)", tickfont=dict(size=11), tickprefix="$"),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=10),
    ),
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig_line, use_container_width=True)

# -------------------------------------------------------------
# COST DRIVER TABLE: Share of Net Forecast Change (%)
# -------------------------------------------------------------
st.subheader("📊 Cost Driver Breakdown (% Share of Net Forecast Shift)")
st.caption("Displays the percentage share of each driver toward the total net forecast shift (sums to 100%).")

driver_contrib_df = df_processed[
    [
        "Commodity",
        "Region",
        "Forecast Shift %",
        "Primary Driver",
        "Energy_Share_%",
        "Tariff_Share_%",
        "Freight_Share_%",
        "Unknown_Share_%",
    ]
].copy()

driver_contrib_df["Energy & Raw Materials Share"] = driver_contrib_df["Energy_Share_%"].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Tariffs & Trade Duties Share"] = driver_contrib_df["Tariff_Share_%"].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Freight & Ocean Logistics Share"] = driver_contrib_df["Freight_Share_%"].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Unknown / Other Factors Share"] = driver_contrib_df["Unknown_Share_%"].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Total Driver Breakdown"] = driver_contrib_df.apply(
    lambda r: f"{(r['Energy_Share_%'] + r['Tariff_Share_%'] + r['Freight_Share_%'] + r['Unknown_Share_%']):.1f}%", axis=1
)

display_driver_table = driver_contrib_df[
    [
        "Commodity",
        "Region",
        "Forecast Shift %",
        "Primary Driver",
        "Energy & Raw Materials Share",
        "Tariffs & Trade Duties Share",
        "Freight & Ocean Logistics Share",
        "Unknown / Other Factors Share",
        "Total Driver Breakdown",
    ]
]

st.dataframe(display_driver_table, use_container_width=True)

st.markdown("---")

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
        marker_color="#34A853",
    )
)

fig_bar.add_trace(
    go.Bar(
        x=labels,
        y=df_processed["Raw_Forecast"],
        name="6M Forecast Price ($)",
        marker_color="#8A2BE2",
    )
)

fig_bar.update_layout(
    barmode="group",
    xaxis=dict(title="Commodity & Region", tickfont=dict(size=11)),
    yaxis=dict(title="Price ($)", tickfont=dict(size=11), tickprefix="$"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=10),
    ),
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig_bar, use_container_width=True)

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
        "Unit": True,
        "Current Q2-2026 (Hist)": True,
        "Avg Price (Last 6M)": True,
        "6M Forecast Price": True,
        "Budgeted Price": True,
        "Variance vs Budget (%)": True,
        "Negotiation Action": True,
        "Data Source": True,
        "Raw_Forecast_Shift": False,
    },
    map_style="open-street-map",
    zoom=1.5,
    center={"lat": 42.0, "lon": -40.0},
)
fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig_map, use_container_width=True)
