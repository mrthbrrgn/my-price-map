import datetime
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Price Tracker & Pre-Negotiation Portal",
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
# SIDEBAR INSTRUCTIONS & FORMULAS
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("👤 Status: **Authorized Team User**")
    if st.button("🚪 Log Out"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")
    st.header("⚙️ Data Refresh Controls")
    if st.button("🔄 Force Reset & Refresh Data"):
        if "budget_df" in st.session_state:
            del st.session_state["budget_df"]
        st.cache_data.clear()
        st.success("Data structure successfully reset!")
        st.rerun()

    st.markdown("---")
    st.header("📖 Pre-Negotiation Playbook")
    st.markdown(
        """
        1. **Input Provider Quotes:** Enter your supplier's **Actual Provider Price ($)** in Section 1.
        2. **Compare vs Benchmark:** Evaluate the delta between provider quotes and external market benchmarks.
        3. **Leverage Dual-Sourcing:** Split strategic volume (e.g., 70/30) to test spot price leverage.
        4. **Unbundle Freight:** Isolate base commodity price from ocean/inland logistics surcharges.
        """
    )

    st.markdown("---")
    with st.expander("📐 Calculation Formulas"):
        st.markdown("**1. Provider vs. Benchmark Delta (%):**")
        st.latex(
            r"\left(\frac{\text{Actual Provider Price} - \text{Market"
            r" Benchmark}}{\text{Market Benchmark}}\right) \times 100"
        )

        st.markdown("**2. Blended Dual-Sourcing Price ($):**")
        st.latex(
            r"(\text{Primary Price} \times \text{Vol \%}) + (\text{Secondary"
            r" Price} \times \text{Vol \%})"
        )

        st.markdown("**3. Unbundled Base Price ($):**")
        st.latex(
            r"\text{Actual Provider Price} - (\text{Inland Freight} +"
            r" \text{Ocean Surcharge})"
        )

# -------------------------------------------------------------
# MAIN APPLICATION CONTENT
# -------------------------------------------------------------

st.title("US & Europe Commodity Price Tracker & Pre-Negotiation Portal")


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


def format_pct_diff(val, base):
    if base <= 0 or pd.isna(val) or pd.isna(base):
        return "0.00%"
    diff_pct = ((val - base) / base) * 100
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
        
        # Default Actual Provider Price (starts slightly above spot)
        item["Actual_Provider_Price"] = round(q2_26 * 1.04, 2)

        processed_list.append(item)

    return pd.DataFrame(processed_list)


if "budget_df" not in st.session_state or "Actual_Provider_Price" not in st.session_state["budget_df"].columns:
    st.session_state["budget_df"] = build_initial_dataset()


def generate_price_history_and_forecast(df):
    history_data = []
    for idx, row in df.iterrows():
        base_avg_2025 = row.get("Base_Price_2025_Avg", row.get("Seed_Price", 100.0))
        ytd_avg_2026 = row.get("YTD_2026_Avg", base_avg_2025)
        current_q = row.get("Current_Q2_2026", base_avg_2025)
        actual_provider = row.get("Actual_Provider_Price", current_q)

        shift_2026 = row.get("Forecast_Shift_%", 0.0)
        shift_2027 = row.get("Projection_2027_Shift_%", 2.0)

        proj_2026 = round(current_q * (1 + shift_2026 / 100), 2)
        price_delta_pct = round(((proj_2026 - current_q) / current_q) * 100, 2)

        proj_2027 = round(proj_2026 * (1 + shift_2027 / 100), 2)

        budget = row.get("Company_Budget_Price", base_avg_2025)
        variance_pct = (
            ((proj_2026 - budget) / budget) * 100 if budget > 0 else 0.0
        )

        if actual_provider > proj_2026:
            flag = "🟢 Opportunity to Lower Price"
        elif actual_provider > budget:
            flag = "🔴 Risk: Provider Over Budget"
        else:
            flag = "✅ Competitive Provider Price"

        record = {
            "Commodity": row["Commodity"],
            "Region": row["Region"],
            "lat": row.get("lat", 0.0),
            "lon": row.get("lon", 0.0),
            "Unit": row["Unit"],
            "Primary Driver": row.get("Primary Driver", "Market Shifts"),
            "Negotiation Action": flag,
            "Data Source": row.get("Data Source", "Industry Benchmark"),
            "Raw_Budget": budget,
            "Current_Price": current_q,
            "Raw_Actual_Provider": actual_provider,
            "Company_Budget_Price": budget,
            "Base_Price_2025_Avg": base_avg_2025,
            "YTD_2026_Avg": ytd_avg_2026,
            "Current_Q2_2026": current_q,
            "Forecast_Shift_%": shift_2026,
            "Projection_2027_Shift_%": shift_2027,
            "2026_Projection_Val": proj_2026,
            "2027_Projection_Val": proj_2027,
            "Actual Provider Price ($)": format_currency(actual_provider),
            "Company Budget Target ($)": format_currency(budget),
            "Baseline (2025 Avg Price)": format_currency(base_avg_2025),
            "Current YTD 2026 Avg Price": format_currency(ytd_avg_2026),
            "Current Q2-2026 Price": format_currency(current_q),
            "Provider vs Budget (%)": format_pct_diff(actual_provider, budget),
            "Provider vs Q2 Market (%)": format_pct_diff(actual_provider, current_q),
            "Provider vs 2026 Proj (%)": format_pct_diff(actual_provider, proj_2026),
            "2026 Market Shift (%)": f"{shift_2026:+.2f}%",
            "2026 Market Projection ($)": format_currency(proj_2026),
            "2027 Market Shift (%)": f"{shift_2027:+.2f}%",
            "2027 Market Projection ($)": format_currency(proj_2027),
            "Q1-2025 (Hist)": format_currency(row.get("Q1_2025", base_avg_2025)),
            "Q2-2025 (Hist)": format_currency(row.get("Q2_2025", base_avg_2025)),
            "Q3-2025 (Hist)": format_currency(row.get("Q3_2025", base_avg_2025)),
            "Q4-2025 (Hist)": format_currency(row.get("Q4_2025", base_avg_2025)),
            "Q1-2026 (Hist)": format_currency(row.get("Q1_2026", current_q)),
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


# -------------------------------------------------------------
# SECTION 1: BUDGET & ACTUAL PROVIDER PRICE ENTRY
# -------------------------------------------------------------
st.subheader("1. Enter Actual Provider Quotes, Budget & Forecast Assumptions")
st.caption("💡 **Pre-Negotiation Entry:** Type in your vendor's **Actual Provider Price ($)** to compare quotes directly against budget and benchmark projections.")

calc_df = generate_price_history_and_forecast(st.session_state["budget_df"])
st.session_state["budget_df"]["2026_Projection_Val"] = calc_df["2026_Projection_Val"]
st.session_state["budget_df"]["2027_Projection_Val"] = calc_df["2027_Projection_Val"]

# --- VISUAL 1: PORTFOLIO EXECUTIVE KPI CARDS ---
kpi_opps = sum(1 for f in calc_df["Negotiation Action"] if "Opportunity" in f)
kpi_risks = sum(1 for f in calc_df["Negotiation Action"] if "Risk" in f)
avg_provider_vs_spot = calc_df.apply(
    lambda r: ((r["Raw_Actual_Provider"] - r["Current_Price"]) / r["Current_Price"]) * 100, axis=1
).mean()

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
with kpi_col1:
    st.metric("🎯 Avg Provider vs. Spot Benchmark", f"{avg_provider_vs_spot:+.2f}%", delta=f"{avg_provider_vs_spot:+.2f}%", delta_color="inverse")
with kpi_col2:
    st.metric("🟢 Negotiation Opportunities", f"{kpi_opps} Commodities", help="Provider quotes higher than projected market benchmark.")
with kpi_col3:
    st.metric("🔴 Over-Budget Cost Risks", f"{kpi_risks} Commodities", help="Provider quotes exceeding company target budget.")

st.markdown("<br>", unsafe_allow_html=True)

editor_display_cols = [
    "Commodity",
    "Region",
    "Unit",
    "Actual_Provider_Price",
    "Company_Budget_Price",
    "Current_Q2_2026",
    "2026_Projection_Val",
    "Forecast_Shift_%",
    "2027_Projection_Val",
    "Projection_2027_Shift_%",
]

edited_df = st.data_editor(
    st.session_state["budget_df"][editor_display_cols],
    column_config={
        "Actual_Provider_Price": st.column_config.NumberColumn(
            "Actual Provider Price ($)",
            help="Current price charged by your provider.",
            format="$%,.2f",
            min_value=0,
        ),
        "Company_Budget_Price": st.column_config.NumberColumn(
            "Company Budget Target ($)",
            help="Company's target budget.",
            format="$%,.2f",
            min_value=0,
        ),
        "Current_Q2_2026": st.column_config.NumberColumn(
            "Current Q2-2026 Spot ($)",
            help="Active quarter spot benchmark.",
            format="$%,.2f",
            disabled=True,
        ),
        "2026_Projection_Val": st.column_config.NumberColumn(
            "2026 Market Projection ($)",
            format="$%,.2f",
            disabled=True,
        ),
        "Forecast_Shift_%": st.column_config.NumberColumn(
            "2026 Market Shift (%)",
            format="%.2f%%",
        ),
        "2027_Projection_Val": st.column_config.NumberColumn(
            "2027 Market Projection ($)",
            format="$%,.2f",
            disabled=True,
        ),
        "Projection_2027_Shift_%": st.column_config.NumberColumn(
            "2027 Market Shift (%)",
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

# Detailed Provider Comparison Table
sec1_comparison_cols = [
    "Commodity",
    "Region",
    "Unit",
    "Actual Provider Price ($)",
    "Company Budget Target ($)",
    "Provider vs Budget (%)",
    "Current Q2-2026 Price",
    "Provider vs Q2 Market (%)",
    "2026 Market Projection ($)",
    "Provider vs 2026 Proj (%)",
    "2027 Market Projection ($)",
    "Negotiation Action",
]

st.markdown("##### 📋 Actual Provider Quote vs. Market Benchmarks")
st.dataframe(
    df_processed[sec1_comparison_cols].style.map(
        lambda x: "text-align: center;"
    ),
    use_container_width=True,
)

st.markdown("---")

# -------------------------------------------------------------
# SECTION 2: HEDGING & PORTFOLIO OPPORTUNITIES
# -------------------------------------------------------------
st.subheader("🛡️ Hedging Strategy & Portfolio Opportunities")
st.caption("Identify leverage points, dual-sourcing splits, and raw material index-linking potential.")

hedging_tab1, hedging_tab2 = st.tabs([
    "🔀 Dual-Sourcing Allocation Strategy",
    "📉 Raw Material Indexing & Pass-Through",
])

with hedging_tab1:
    st.markdown("##### Dual-Sourcing Volume Allocation Model")
    st.caption("Model potential blended unit cost savings by splitting volumes between primary strategic suppliers and secondary spot vendors.")

    col1, col2 = st.columns(2)
    with col1:
        primary_share = st.slider("Primary Strategic Vendor Volume Share (%)", min_value=50, max_value=90, value=70, step=5)
    with col2:
        secondary_share = 100 - primary_share
        st.metric("Secondary Spot Vendor Share (%)", f"{secondary_share}%")

    dual_source_df = df_processed[["Commodity", "Region", "Unit", "Actual Provider Price ($)", "Current Q2-2026 Price"]].copy()
    
    dual_source_df["Primary Price ($)"] = df_processed["Raw_Actual_Provider"]
    dual_source_df["Secondary Spot Price ($)"] = df_processed["Current_Price"]
    
    dual_source_df["Blended Unit Price ($)"] = (
        (dual_source_df["Primary Price ($)"] * (primary_share / 100)) +
        (dual_source_df["Secondary Spot Price ($)"] * (secondary_share / 100))
    )
    
    dual_source_df["Potential Savings ($/unit)"] = dual_source_df["Primary Price ($)"] - dual_source_df["Blended Unit Price ($)"]
    
    display_dual_df = dual_source_df[[
        "Commodity", "Region", "Unit", 
        "Actual Provider Price ($)", 
        "Secondary Spot Price ($)", 
        "Blended Unit Price ($)", 
        "Potential Savings ($/unit)"
    ]].copy()

    display_dual_df["Blended Unit Price ($)"] = display_dual_df["Blended Unit Price ($)"].apply(format_currency)
    display_dual_df["Secondary Spot Price ($)"] = display_dual_df["Secondary Spot Price ($)"].apply(format_currency)
    display_dual_df["Potential Savings ($/unit)"] = display_dual_df["Potential Savings ($/unit)"].apply(format_currency)

    st.dataframe(display_dual_df.style.map(lambda x: "text-align: center;"), use_container_width=True)

with hedging_tab2:
    st.markdown("##### Index-Linked Pass-Through Transparency")
    st.caption("Isolate core raw material costs to prevent supplier markups on non-volatile overhead.")

    index_df = df_processed[[
        "Commodity", "Region", "Unit", 
        "Actual Provider Price ($)", 
        "Current Q2-2026 Price", 
        "Primary Driver", 
        "Energy_Share_%", 
        "Tariff_Share_%"
    ]].copy()

    index_df["Estimated Raw Material Base ($)"] = (df_processed["Current_Price"] * 0.70).apply(format_currency)
    index_df["Suggested Indexing Mechanism"] = index_df["Commodity"].apply(
        lambda c: "Cap/Floor Collar Agreement" if "Oil" in c else "Monthly Formula Pass-Through"
    )

    st.dataframe(index_df.style.map(lambda x: "text-align: center;"), use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# SECTION 3: FREIGHT & LOGISTICS UNBUNDLING
# -------------------------------------------------------------
st.subheader("🚚 Freight & Logistics Unbundling Tracker")
st.caption("Unbundle base commodity price from ocean container surcharges, inland freight, and fuel indices.")

freight_df = df_processed[["Commodity", "Region", "Unit", "Actual Provider Price ($)", "Freight_Share_%"]].copy()

freight_df["Est. Inland Freight ($)"] = (df_processed["Raw_Actual_Provider"] * (freight_df["Freight_Share_%"] / 100) * 0.4).apply(format_currency)
freight_df["Est. Ocean Surcharge ($)"] = (df_processed["Raw_Actual_Provider"] * (freight_df["Freight_Share_%"] / 100) * 0.6).apply(format_currency)
freight_df["Unbundled Base Material ($)"] = (df_processed["Raw_Actual_Provider"] * (1 - freight_df["Freight_Share_%"] / 100)).apply(format_currency)
freight_df["Freight Action"] = freight_df["Freight_Share_%"].apply(
    lambda s: "🔴 Renegotiate Peak Surcharge" if s >= 50.0 else "✅ Standard Freight Rate"
)

st.dataframe(freight_df.style.map(lambda x: "text-align: center;"), use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# SECTION 4: HISTORICAL TRENDS, CHARTS & MAP
# -------------------------------------------------------------
st.subheader("4. 18-Month Historical Quarterly Trends & Forecasts")
st.caption("Actual Provider Prices are highlighted in **light green**, and Market Projections are in **light purple**.")

# --- VISUAL 2: HORIZONTAL BUDGET ALIGNMENT CHART FOR TABLE 2 ---
st.markdown("##### 📊 Visual Benchmark Comparison: Provider Quote vs. Market Benchmarks")

plot_records = []
for _, r in df_processed.iterrows():
    item_label = f"{r['Commodity']} ({r['Region']})"
    plot_records.append({"Commodity": item_label, "Price Type": "Company Budget Target ($)", "Price": r["Raw_Budget"]})
    plot_records.append({"Commodity": item_label, "Price Type": "Actual Provider Price ($)", "Price": r["Raw_Actual_Provider"]})
    plot_records.append({"Commodity": item_label, "Price Type": "Current Q2 Spot ($)", "Price": r["Current_Price"]})
    plot_records.append({"Commodity": item_label, "Price Type": "2026 Market Projection ($)", "Price": r["2026_Projection_Val"]})

plot_df = pd.DataFrame(plot_records)

fig_align = px.bar(
    plot_df,
    x="Price",
    y="Commodity",
    color="Price Type",
    barmode="group",
    orientation="h",
    color_discrete_map={
        "Company Budget Target ($)": "#34A853",
        "Actual Provider Price ($)": "#EA4335",
        "Current Q2 Spot ($)": "#4285F4",
        "2026 Market Projection ($)": "#8A2BE2",
    },
    text_auto="$.2f",
)
fig_align.update_layout(
    xaxis_title="Price ($)",
    yaxis_title="Commodity & Region",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig_align, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

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
    "Actual Provider Price ($)",
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
    "Negotiation Action",
    "Data Source",
]

selected_display_cols = base_cols + hist_cols + summary_cols

styled_df = (
    df_processed[selected_display_cols]
    .style.map(lambda x: "background-color: #ffffff; color: #000000; text-align: center;")
    .map(
        lambda x: "background-color: #e6f4ea; color: #000000; font-weight: bold; text-align: center;",
        subset=["Actual Provider Price ($)"],
    )
    .map(
        lambda x: "background-color: #f3e8ff; color: #000000; font-weight: bold; text-align: center;",
        subset=["2026 Market Projection ($)", "2027 Market Projection ($)", "Forecast Shift %"],
    )
)

st.dataframe(styled_df, use_container_width=True)

# Excel Export Generator
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_processed[
        [
            "Commodity",
            "Region",
            "Unit",
            "Actual Provider Price ($)",
            "Company Budget Target ($)",
            "Provider vs Budget (%)",
            "Current Q2-2026 Price",
            "Provider vs Q2 Market (%)",
            "2026 Market Projection ($)",
            "2027 Market Projection ($)",
            "Primary Driver",
            "Negotiation Action",
            "Data Source",
        ]
    ].to_excel(writer, sheet_name="Pre_Negotiation_Summary", index=False)

st.download_button(
    label="📥 Export Full Pre-Negotiation Excel File (.xlsx)",
    data=buffer.getvalue(),
    file_name="commodity_pre_negotiation_and_hedging.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")

st.markdown("#### 📈 Price Trajectory vs. Provider Quote")

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

st.subheader("5. US & Europe Predictive Map")

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
        "Actual Provider Price ($)": True,
        "Company Budget Target ($)": True,
        "Current Q2-2026 Price": True,
        "2026 Market Projection ($)": True,
        "2027 Market Projection ($)": True,
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
