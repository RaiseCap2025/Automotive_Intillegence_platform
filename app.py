import streamlit as st

st.set_page_config(
    page_title="Automotive Intelligence Platform",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    [data-testid="stMetric"] {
        background-color: #1A1D23;
        border: 1px solid #2D3139;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetric"] label {font-size: 0.85rem; color: #9CA3AF;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.8rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1D23;
        border-radius: 6px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Automotive Intelligence Platform")
st.markdown(
    "**Vehicle Battery Quality Analytics** — Powered by Snowflake + Cortex AI"
)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 📊 Dashboard")
    st.markdown("Real-time KPIs and failure trends across the entire fleet.")
    st.page_link("pages/1_Executive_Dashboard.py", label="Open Dashboard →")

with col2:
    st.markdown("### 🏭 Supplier Analytics")
    st.markdown("Compare supplier quality performance and identify root causes.")
    st.page_link("pages/2_Supplier_Analytics.py", label="Open Supplier Analytics →")

with col3:
    st.markdown("### 📈 Failure Forecasting")
    st.markdown("ML-powered 30-day failure predictions per battery part.")
    st.page_link("pages/3_Failure_Forecasting.py", label="Open Forecasting →")

st.markdown("")
col4, col5 = st.columns(2)
with col4:
    st.markdown("### 🤖 AI Assistant")
    st.markdown("Ask questions about quality data in natural language using Cortex AI.")
    st.page_link("pages/4_AI_Assistant.py", label="Open AI Assistant →")

with col5:
    st.markdown("### 🔍 Vehicle Lookup")
    st.markdown("Search by VIN and inspect individual vehicle event history.")
    st.page_link("pages/5_Vehicle_Lookup.py", label="Open Vehicle Lookup →")

st.markdown("---")
st.caption("Snowflake x Capgemini Hackathon 2026 | Built with Streamlit, Snowpark & Cortex AI")
