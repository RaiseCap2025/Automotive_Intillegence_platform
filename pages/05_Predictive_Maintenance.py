import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav, kpi_card, kpi_row, page_header
from utils.connection import get_session, run_query
from utils import queries as Q
from utils.ai import generate_insight

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Predictive Maintenance", "page_icon": "📈"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("📈", "Predictive Maintenance", "30-day forecasts & remaining life estimates", ["Snowpark ML"]), unsafe_allow_html=True)

session = get_session()

# ── KPI Tiles ─────────────────────────────────────────────────────────
try:
    forecast_summary = run_query(session, Q.FORECAST_SUMMARY)
    high_risk_df = run_query(session, Q.HIGH_RISK_VEHICLES)
    risk_top_df = run_query(session, Q.VEHICLE_RISK_TOP)
    warranty_df = run_query(session, Q.WARRANTY_COST_ESTIMATE)

    predicted_failures = int(forecast_summary["TOTAL_PREDICTED_FAILURES"].iloc[0]) if not forecast_summary.empty else 0
    vehicles_at_risk = int(high_risk_df["HIGH_RISK_COUNT"].iloc[0]) if not high_risk_df.empty else 0
    avg_risk = risk_top_df["RISK_SCORE"].mean() if not risk_top_df.empty else 0
    warranty_cost = float(warranty_df["WARRANTY_COST_EXPOSURE"].iloc[0]) if not warranty_df.empty else 0

    st.markdown(kpi_row([
        kpi_card("Predicted Failures", f"{predicted_failures:,}", "next 30 days", accent="red"),
        kpi_card("Vehicles at Risk", f"{vehicles_at_risk:,}", "high & critical tier", accent="amber"),
        kpi_card("Avg Failure Prob", f"{avg_risk:.1f}%", "top 50 riskiest", accent="purple"),
        kpi_card("Warranty Cost", f"${warranty_cost:,.0f}", "estimated exposure", accent="cyan"),
    ], cols=4), unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")

st.markdown("---")

# ── Business Insight ──────────────────────────────────────────────────
try:
    if not risk_top_df.empty:
        critical_count = int((risk_top_df["RISK_TIER"] == "CRITICAL").sum())
        high_count = int((risk_top_df["RISK_TIER"] == "HIGH").sum())
        top_supplier = risk_top_df["SUPPLIER_NAME"].value_counts().idxmax()
        top_state = risk_top_df["STATE"].value_counts().idxmax()
        context = (
            f"Predictive Maintenance Dashboard. "
            f"Predicted failures (30d): {predicted_failures:,}, "
            f"Vehicles at risk: {vehicles_at_risk:,}, "
            f"Avg failure probability: {avg_risk:.1f}%, "
            f"Estimated warranty cost: ${warranty_cost:,.0f}. "
            f"Of top {len(risk_top_df)} high-risk vehicles: {critical_count} Critical, {high_count} High. "
            f"Most common supplier: {top_supplier}, Most affected state: {top_state}."
        )
        insight = generate_insight(session, "predictive_maintenance", context)
        st.info(f"**Business Insight:** {insight}")
except Exception:
    pass

# ── RUL + Risk Distribution ───────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<p class="section-header">Remaining Life</p>', unsafe_allow_html=True)
    try:
        rul_df = run_query(session, Q.RUL_ESTIMATES)
        if not rul_df.empty:
            rul_top = rul_df.head(20)
            color_map = {"CRITICAL": "#F87171", "HIGH": "#FB923C"}
            fig_rul = px.bar(
                rul_top, x="RUL_MONTHS", y="VIN", color="RISK_TIER",
                orientation="h", color_discrete_map=color_map,
                labels={"RUL_MONTHS": "Remaining Life (months)", "VIN": ""},
            )
            fig_rul.update_layout(**PLOTLY_LAYOUT, height=500, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_rul, width="stretch")
        else:
            st.info("No RUL data available.")
    except Exception as e:
        st.error(f"RUL chart error: {e}")

with col_right:
    st.markdown('<p class="section-header">Failure Probability Distribution</p>', unsafe_allow_html=True)
    try:
        risk_dist = run_query(session, Q.RISK_DISTRIBUTION)
        if not risk_dist.empty:
            band_colors = {
                "80-100 (Critical)": "#F87171",
                "60-79 (High)": "#FB923C",
                "40-59 (Medium)": "#FBBF24",
                "20-39 (Low)": "#34D399",
                "0-19 (Minimal)": "#6EE7B7",
            }
            risk_dist["COLOR"] = risk_dist["RISK_BAND"].map(band_colors).fillna(COLORS["primary"])
            fig_dist = px.bar(
                risk_dist, x="RISK_BAND", y="VEHICLE_COUNT",
                color="RISK_BAND", color_discrete_map=band_colors,
                labels={"RISK_BAND": "Risk Band", "VEHICLE_COUNT": "Vehicle Count"},
            )
            fig_dist.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
            st.plotly_chart(fig_dist, width="stretch")
        else:
            st.info("No risk distribution data available.")
    except Exception as e:
        st.error(f"Risk distribution error: {e}")

st.markdown("---")

# ── High-Risk Vehicle List ────────────────────────────────────────────
st.markdown('<p class="section-header">High-Risk Vehicle List</p>', unsafe_allow_html=True)
try:
    if not risk_top_df.empty:
        display_cols = ["VIN", "VEHICLE_CONFIG", "STATE", "SUPPLIER_NAME", "RISK_SCORE", "RISK_TIER"]
        st.dataframe(risk_top_df[display_cols].head(20), width="stretch", hide_index=True, height=400)
    else:
        st.info("No high-risk vehicle data available.")
except Exception as e:
    st.error(f"Vehicle list error: {e}")

st.markdown("---")
