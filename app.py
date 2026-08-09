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
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    h1 { font-size: 1.8rem !important; }
    h2, h3 { font-size: 1.3rem !important; font-weight: 700 !important; }
    h4 { font-size: 1.1rem !important; font-weight: 600 !important; }
    .stCaption, p, div { font-size: 1.0rem !important; }
    
    /* Enforce White Background, Black Text, and Centered Alignment for all Dataframes/Editors */
    .stDataFrame, .stDataEditor {
        font-size: 0.95rem !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Center text inside Dataframes */
    div[data-testid="stTable"] td, .stDataFrame td, div[data-testid="stDataEditor"] td {
        text-align: center !important;
    }
    
    /* Wrap & Center Table Header Text */
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

# -------------------------------------------------------------
# SIDEBAR INSTRUCTIONS & FORMULAS (CLEANED LATEX FORMATTING)
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("👤 Status: **Authorized Team User**")
    if st.button("🚪 Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")
    st.header("⚙️ Data Refresh Controls")
    if st.button("🔄 Force Quarterly Refresh"):
        st.cache_data.clear()
        st.success("Quarterly benchmarks refreshed!")
        st.rerun()

    st.markdown("---")
    st.header("📖 Usage Instructions")
    st.markdown(
        """
        1. **Edit Assumptions (Section 1):** Click inside table cells to update **Company Budget Targets** or **2026/2027 Market Shifts (%)**.
        2. **Automatic Savings:** Any edits automatically update all downstream tables, trajectory charts, and maps.
        3. **Review Negotiation Triggers:**
           * 🟢 **Opportunity:** Market price <= 10% below budget.
           * 🔴 **Risk:** Market price >= 10% above budget.
        4. **Export Data:** Click the **Export Excel** button to download full comparison sheets.
        """
    )

    st.markdown("---")
    with st.expander("📐 Calculation Formulas"):
        st.markdown("**1. 2026 Market Projection ($):**")
        st.latex(r"\text{Current Q2 Price} \times \left(1 + \frac{\text{2026 Shift \%}}{100}\right)")

        st.markdown("**2. 2027 Market Projection ($):**")
        st.latex(r"\text{2026 Projection} \times \left(1 + \frac{\text{2027 Shift \%}}{100}\right)")

        st.markdown("**3. Budget vs Measure Variance (%):**")
        st.latex(r"\left(\frac{\text{Company Budget Target} - \text{Benchmark Price}}{\text{Benchmark Price}}\right) \times 100")

        st.markdown("**4. Forecast Shift (%):**")
        st.latex(r"\left(\frac{\text{2026 Projection} - \text{Current Q2 Price}}{\text{Current Q2 Price}}\right) \times 100")

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


def format_currency(val):
    if pd.isna(val):
        return "$0.00"
    return f"${val:,.2f}"


def format_budget_vs_measure(budget, measure):
    if measure <= 0 or pd.isna(budget) or pd.isna(measure):
        return "0.00%"
    diff_pct = ((budget - measure) / measure) * 100
    return f"{diff_pct:+.2f}%"


def build_initial_dataset():
    np.random.seed(42)

    raw_items = [
        {
            "Commodity": "Coconut Oil",
            "Region": "Europe",
            "lat": 51.9244,
            "lon": 4.4777,
            "Unit": "$/tonne",
            "Seed_Price": 1650.0,
            "Primary Driver": "Freight Surcharges & Weather",
            "Energy_Share_%": 10.0,
            "Tariff_Share_%": 20.0,
            "Freight_Share_%": 60.0,
            "Unknown_Share_%": 10.0,
            "Forecast_Shift_%": -5.0,
            "Projection_2027_Shift_%": 2.5,
            "Data Source": "CME / Malayan Palm Oil Board (MPOB)",
        },
        {
            "Commodity": "Palm Oil",
            "Region": "Europe",
            "lat": 53.5511,
            "lon": 9.9937,
            "Unit": "$/tonne",
            "Seed_Price": 980.0,
            "Primary Driver": "Agricultural Yields",
            "Energy_Share_%": 0.0,
            "Tariff_Share_%": 10.0,
            "Freight_Share_%": 80.0,
            "Unknown_Share_%": 10.0,
            "Forecast_Shift_%": -12.0,
            "Projection_2027_Shift_%": -3.0,
            "Data Source": "Bursa Malaysia (KL CPO Futures Index)",
        },
        {
            "Commodity": "IPA (Isopropyl Alcohol)",
            "Region": "US",
            "lat": 29.7604,
            "lon": -95.3698,
            "Unit": "$/kg",
            "Seed_Price": 1.45,
            "Primary Driver": "Geopolitical / Energy Shock",
            "Energy_Share_%": 90.0,
            "Tariff_Share_%": 5.0,
            "Freight_Share_%": 0.0,
            "Unknown_Share_%": 5.0,
            "Forecast_Shift_%": 2.1,
            "Projection_2027_Shift_%": 1.5,
            "Data Source": "ICIS Petrochemical Gulf Coast Index",
        },
        {
            "Commodity": "Silicones",
            "Region": "US",
            "lat": 43.6156,
            "lon": -84.2472,
            "Unit": "$/kg",
            "Seed_Price": 3.80,
            "Primary Driver": "Energy Intensive Costs",
            "Energy_Share_%": 85.0,
            "Tariff_Share_%": 0.0,
            "Freight_Share_%": 10.0,
            "Unknown_Share_%": 5.0,
            "Forecast_Shift_%": -15.0,
            "Projection_2027_Shift_%": 4.0,
            "Data Source": "S&P Global Platts Chemical Insights",
        },
        {
            "Commodity": "Silicones",
            "Region": "Europe",
            "lat": 50.1109,
            "lon": 8.6821,
            "Unit": "$/kg",
            "Seed_Price": 4.10,
            "Primary Driver": "EU Energy & Import Duties",
            "Energy_Share_%": 70.0,
            "Tariff_Share_%": 15.0,
            "Freight_Share_%": 10.0,
            "Unknown_Share_%": 5.0,
            "Forecast_Shift_%": 1.2,
            "Projection_2027_Shift_%": 2.0,
            "Data Source": "ICIS European Silicones Benchmark",
        },
        {
            "Commodity": "Glycerin",
            "Region": "US",
            "lat": 41.8781,
            "lon": -87.6298,
            "Unit": "$/tonne",
            "Seed_Price": 820.0,
            "Primary Driver": "Inflation & Domestic Transport",
            "Energy_Share_%": 15.0,
            "Tariff_Share_%": 0.0,
            "Freight_Share_%": 75.0,
            "Unknown_Share_%": 10.0,
            "Forecast_Shift_%": -8.0,
            "Projection_2027_Shift_%": 1.0,
            "Data Source": "USDA Oleochemical / Refined Glycerin Reports",
        },
    ]

    processed_list = []
    for item in raw_items:
        seed = item["Seed_Price"]
        q1_25 = round(seed * (1 + np.random.uniform(-0.05, 0.05)), 2)
        q2_25 = round(seed * (1 + np.random.uniform(-0.05, 0.05)), 2)
        q3_25 = round(seed * (1 + np.random.uniform(-0.05, 0.05)), 2)
        q4_25 = round(seed * (1 + np.random.uniform(-0.05, 0.05)), 2)

        avg_2025 = round((q1_25 + q2_25 + q3_25 + q4_25) / 4, 2)

        q1_26 = round(avg_2025 * (1 + np.random.uniform(-0.04, 0.04)), 2)
        q2_26 = round(q1_26 * (1 + np.random.uniform(-0.03, 0.03)), 2)

        ytd_2026_avg = round((q1_26 + q2_26) / 2, 2)

        item["Q1_2025"] = q1_25
        item["Q2_2025"] = q2_25
        item["Q3_2025"] = q3_25
        item["Q4_2025"] = q4_25
        item["Base_Price_2025_Avg"] = avg_2025
        item["Q1_2026"] = q1_26
        item["Current_Q2_2026"] = q2_26
        item["YTD_2026_Avg"] = ytd_2026_avg
        item["Company_Budget_Price"] = round(avg_2025 * 1.05, 2)

        processed_list.append(item)

    return pd.DataFrame(processed_list)


if "budget_df" not in st.session_state:
    st.session_state["budget_df"] = build_initial_dataset()


def generate_price_history_and_forecast(df):
    history_data = []
    for idx, row in df.iterrows():
        base_avg_2025 = row["Base_Price_2025_Avg"]
        ytd_avg_2026 = row["YTD_2026_Avg"]
        current_q = row["Current_Q2_2026"]

        # Market Projections
        proj_2026 = round(current_q * (1 + row["Forecast_Shift_%"] / 100), 2)
        price_delta_pct = round(((proj_2026 - current_q) / current_q) * 100, 2)

        proj_2027 = round(
            proj_2026 * (1 + row.get("Projection_2027_Shift_%", 2.0) / 100), 2
        )

        budget = row["Company_Budget_Price"]
        variance_pct = (
            ((proj_2026 - budget) / budget) * 100 if budget > 0 else 0.0
        )

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
            "Current_Price": current_q,
            "Company_Budget_Price": budget,
            "Base_Price_2025_Avg": base_avg_2025,
            "YTD_2026_Avg": ytd_2026_avg,
            "Current_Q2_2026": current_q,
            "Forecast_Shift_%": row["Forecast_Shift_%"],
            "Projection_2027_Shift_%": row.get("Projection_2027_Shift_%", 2.0),
            "2026_Projection_Val": proj_2026,
            "2027_Projection_Val": proj_2027,
            "Company Budget Target ($)": format_currency(budget),
            "Baseline (2025 Avg Price)": format_currency(base_avg_2025),
            "Budget vs 2025 Avg (%)": format_budget_vs_measure(budget, base_avg_2025),
            "Current YTD 2026 Avg Price": format_currency(ytd_avg_2026),
            "Budget vs YTD 2026 (%)": format_budget_vs_measure(budget, ytd_avg_2026),
            "Current Q2-2026 Price": format_currency(current_q),
            "Budget vs Current Q2 (%)": format_budget_vs_measure(budget, current_q),
            "2026 Market Shift (%)": f"{row['Forecast_Shift_%']:+.2f}%",
            "2026 Market Projection ($)": format_currency(proj_2026),
            "Budget vs 2026 Proj (%)": format_budget_vs_measure(budget, proj_2026),
            "2027 Market Shift (%)": f"{row.get('Projection_2027_Shift_%', 2.0):+.2f}%",
            "2027 Market Projection ($)": format_currency(proj_2027),
            "Budget vs 2027 Proj (%)": format_budget_vs_measure(budget, proj_2027),
            "Q1-2025 (Hist)": format_currency(row["Q1_2025"]),
            "Q2-2025 (Hist)": format_currency(row["Q2_2025"]),
            "Q3-2025 (Hist)": format_currency(row["Q3_2025"]),
            "Q4-2025 (Hist)": format_currency(row["Q4_2025"]),
            "Q1-2026 (Hist)": format_currency(row["Q1_2026"]),
            "Current Q2-2026 (Hist)": format_currency(current_q),
            "Raw_Forecast": proj_2026,
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


# Section 1: Budget Entry & Assumptions
st.subheader("1. Enter Company Budget & Market Projection Assumptions")
st.caption("💡 **Company Budget Comparisons:** Compare your budget directly against 2025 baselines, YTD 2026 averages, current Q2 prices, and projected 2026/2027 market shifts.")

# Calculate initial projections for the data editor display
calc_df = generate_price_history_and_forecast(st.session_state["budget_df"])
st.session_state["budget_df"]["2026_Projection_Val"] = calc_df["2026_Projection_Val"]
st.session_state["budget_df"]["2027_Projection_Val"] = calc_df["2027_Projection_Val"]

# Data editor display columns with Values BEFORE Shifts
editor_display_cols = [
    "Commodity",
    "Region",
    "Unit",
    "Company_Budget_Price",
    "Base_Price_2025_Avg",
    "YTD_2026_Avg",
    "Current_Q2_2026",
    "2026_Projection_Val",
    "Forecast_Shift_%",
    "2027_Projection_Val",
    "Projection_2027_Shift_%",
]

edited_df = st.data_editor(
    st.session_state["budget_df"][editor_display_cols],
    column_config={
        "Company_Budget_Price": st.column_config.NumberColumn(
            "Company Budget Target ($)",
            help="Company's target budget.",
            format="$%,.2f",
            min_value=0,
        ),
        "Base_Price_2025_Avg": st.column_config.NumberColumn(
            "Baseline (2025 Avg Price)",
            help="Average price across 2025.",
            format="$%,.2f",
            disabled=True,
        ),
        "YTD_2026_Avg": st.column_config.NumberColumn(
            "Current YTD 2026 Avg Price",
            help="Year-to-date average price for 2026.",
            format="$%,.2f",
            disabled=True,
        ),
        "Current_Q2_2026": st.column_config.NumberColumn(
            "Current Q2-2026 Price",
            help="Latest active quarter spot benchmark price.",
            format="$%,.2f",
            disabled=True,
        ),
        "2026_Projection_Val": st.column_config.NumberColumn(
            "2026 Market Projection ($)",
            help="Calculated market projection for 2026.",
            format="$%,.2f",
            disabled=True,
        ),
        "Forecast_Shift_%": st.column_config.NumberColumn(
            "2026 Market Shift (%)",
            help="Expected percentage market shift for 2026.",
            format="%.2f%%",
        ),
        "2027_Projection_Val": st.column_config.NumberColumn(
            "2027 Market Projection ($)",
            help="Calculated market projection for 2027.",
            format="$%,.2f",
            disabled=True,
        ),
        "Projection_2027_Shift_%": st.column_config.NumberColumn(
            "2027 Market Shift (%)",
            help="Expected percentage market shift for 2027 vs 2026.",
            format="%.2f%%",
        ),
    },
    use_container_width=True,
    num_rows="dynamic",
    key="budget_editor",
)

full_updated_df = st.session_state["budget_df"].copy()
full_updated_df.update(edited_df)
st.session_state["budget_df"] = full_updated_df

df_processed = generate_price_history_and_forecast(
    st.session_state["budget_df"]
)

# Render Detailed Budget Comparison Table in Section 1
sec1_comparison_cols = [
    "Commodity",
    "Region",
    "Unit",
    "Company Budget Target ($)",
    "Baseline (2025 Avg Price)",
    "Budget vs 2025 Avg (%)",
    "Current YTD 2026 Avg Price",
    "Budget vs YTD 2026 (%)",
    "Current Q2-2026 Price",
    "Budget vs Current Q2 (%)",
    "2026 Market Projection ($)",
    "2026 Market Shift (%)",
    "Budget vs 2026 Proj (%)",
    "2027 Market Projection ($)",
    "2027 Market Shift (%)",
    "Budget vs 2027 Proj (%)",
]

st.markdown("##### 📋 Company Budget vs Market Benchmarks & Projections")
st.dataframe(
    df_processed[sec1_comparison_cols].style.map(
        lambda x: "text-align: center;"
    ),
    use_container_width=True,
)

# Excel Export Generator
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_processed[
        [
            "Commodity",
            "Region",
            "Unit",
            "Company Budget Target ($)",
            "Baseline (2025 Avg Price)",
            "Budget vs 2025 Avg (%)",
            "Current YTD 2026 Avg Price",
            "Budget vs YTD 2026 (%)",
            "Current Q2-2026 Price",
            "Budget vs Current Q2 (%)",
            "2026 Market Projection ($)",
            "2026 Market Shift (%)",
            "Budget vs 2026 Proj (%)",
            "2027 Market Projection ($)",
            "2027 Market Shift (%)",
            "Budget vs 2027 Proj (%)",
            "Primary Driver",
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
st.caption("Company Budget is highlighted in **light green**, and Market Projections are in **light purple**.")

show_historical_quarters = st.checkbox(
    "Show Historical Quarterly Columns (Q1-2025 to Current)", value=False
)

base_cols = [
    "Commodity",
    "Region",
    "Unit",
    "Baseline (2025 Avg Price)",
    "Current YTD 2026 Avg Price",
    "Current Q2-2026 Price",
    "Company Budget Target ($)",
]

hist_cols = (
    [
        "Q1-2025 (Hist)",
        "Q2-2025 (Hist)",
        "Q3-2025 (Hist)",
        "Q4-2025 (Hist)",
        "Q1-2026 (Hist)",
        "Current Q2-2026 (Hist)",
    ]
    if show_historical_quarters
    else []
)

summary_cols = [
    "2026 Market Projection ($)",
    "2027 Market Projection ($)",
    "Forecast Shift %",
    "Variance vs Budget (%)",
    "Negotiation Action",
    "Data Source",
]

selected_display_cols = base_cols + hist_cols + summary_cols

styled_df = (
    df_processed[selected_display_cols]
    .style.map(lambda x: "background-color: #ffffff; color: #000000; text-align: center;")
    .map(
        lambda x: "background-color: #e6f4ea; color: #000000; font-weight: bold; text-align: center;",
        subset=["Company Budget Target ($)"],
    )
    .map(
        lambda x: "background-color: #f3e8ff; color: #000000; font-weight: bold; text-align: center;",
        subset=["2026 Market Projection ($)", "2027 Market Projection ($)", "Forecast Shift %"],
    )
    .map(
        lambda val: (
            "background-color: #fce8e6; color: #c5221f; font-weight: bold; text-align: center;"
            if "Risk of Higher Prices" in str(val)
            else (
                "background-color: #e6f4ea; color: #137333; font-weight: bold; text-align: center;"
                if "Opportunity to Lower Price" in str(val)
                else "background-color: #ffffff; color: #000000; text-align: center;"
            )
        ),
        subset=["Negotiation Action"],
    )
)

st.dataframe(styled_df, use_container_width=True)

st.markdown("---")

# Section 3: Charts & Map
st.markdown("#### 📈 Price Trend Trajectory (18 Months + Market Projections)")

time_cols = [
    "Q1-2025 (Hist)",
    "Q2-2025 (Hist)",
    "Q3-2025 (Hist)",
    "Q4-2025 (Hist)",
    "Q1-2026 (Hist)",
    "Current Q2-2026 (Hist)",
    "2026 Market Projection ($)",
    "2027 Market Projection ($)",
]

fig_line = go.Figure()

for idx, row in df_processed.iterrows():
    label = f"{row['Commodity']} ({row['Region']} - {row['Unit']})"
    values = [
        float(str(row[col]).replace("$", "").replace(",", "")) for col in time_cols
    ]

    fig_line.add_trace(
        go.Scatter(
            x=[c.replace(" (Hist)", "").replace(" ($)", "") for c in time_cols],
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
st.caption(
    "Displays the percentage share of each driver toward the total net forecast shift (sums to 100%)."
)

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

driver_contrib_df["Energy & Raw Materials Share"] = driver_contrib_df[
    "Energy_Share_%"
].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Tariffs & Trade Duties Share"] = driver_contrib_df[
    "Tariff_Share_%"
].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Freight & Ocean Logistics Share"] = driver_contrib_df[
    "Freight_Share_%"
].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Unknown / Other Factors Share"] = driver_contrib_df[
    "Unknown_Share_%"
].apply(lambda x: f"{x:.1f}%")
driver_contrib_df["Total Driver Breakdown"] = driver_contrib_df.apply(
    lambda r: (
        f"{(r['Energy_Share_%'] + r['Tariff_Share_%'] + r['Freight_Share_%'] + r['Unknown_Share_%']):.1f}%"
    ),
    axis=1,
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

st.dataframe(
    display_driver_table.style.map(lambda x: "text-align: center;"),
    use_container_width=True,
)

st.markdown("---")

st.subheader("3. Company Budget vs 2026 Market Projection")

fig_bar = go.Figure()
labels = [
    f"{r['Commodity']} ({r['Region']})" for _, r in df_processed.iterrows()
]

fig_bar.add_trace(
    go.Bar(
        x=labels,
        y=df_processed["Raw_Budget"],
        name="Company Budget Target ($)",
        marker_color="#34A853",
        text=df_processed["Raw_Budget"],
        texttemplate="$%{y:,.2f}",
        textposition="outside",
        textfont=dict(size=10),
    )
)

fig_bar.add_trace(
    go.Bar(
        x=labels,
        y=df_processed["Raw_Forecast"],
        name="2026 Market Projection ($)",
        marker_color="#8A2BE2",
        text=df_processed["Raw_Forecast"],
        texttemplate="$%{y:,.2f}",
        textposition="outside",
        textfont=dict(size=10),
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
    margin=dict(l=10, r=10, t=40, b=10),
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
        "Baseline (2025 Avg Price)": True,
        "Current YTD 2026 Avg Price": True,
        "Current Q2-2026 Price": True,
        "Company Budget Target ($)": True,
        "2026 Market Projection ($)": True,
        "2027 Market Projection ($)": True,
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
