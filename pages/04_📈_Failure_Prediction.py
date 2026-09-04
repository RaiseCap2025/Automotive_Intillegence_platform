import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Failure Prediction", "page_icon": "📈"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("📈 Failure Prediction Center")
st.caption("ML-powered failure forecasts and vehicle risk scoring")

session = get_session()

# ── Vehicle Risk Table ──
st.markdown('<p class="section-header">Top Risk Vehicles</p>', unsafe_allow_html=True)
risk_df = run_query(session, Q.VEHICLE_RISK_TOP)

if not risk_df.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Critical Vehicles", len(risk_df[risk_df["RISK_TIER"] == "CRITICAL"]))
    c2.metric("High Risk", len(risk_df[risk_df["RISK_TIER"] == "HIGH"]))
    c3.metric("Max Risk Score", f"{risk_df['RISK_SCORE'].max():.1f}")
    c4.metric("Avg Risk Score", f"{risk_df['RISK_SCORE'].mean():.1f}")

    display = risk_df[["VIN", "RISK_TIER", "RISK_SCORE", "SUPPLIER_NAME",
                        "BATTERY_TYPE_NAME", "STATE", "ERROR_COUNT"]].head(30)
    st.dataframe(display, use_container_width=True, hide_index=True, height=300)

st.markdown("---")

# ── Risk Heatmap ──
st.markdown('<p class="section-header">Risk Heatmap: Supplier x Battery Type</p>', unsafe_allow_html=True)
heatmap_df = run_query(session, Q.RISK_HEATMAP)
if not heatmap_df.empty:
    pivot = heatmap_df.pivot_table(index="SUPPLIER_NAME", columns="BATTERY_TYPE_NAME",
                                    values="FAILURE_RATE_PCT", fill_value=0)
    fig_heat = px.imshow(
        pivot, text_auto=".2f", color_continuous_scale="RdYlGn_r",
        labels=dict(x="Battery Type", y="Supplier", color="Failure Rate %"),
    )
    fig_heat.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ── Forecast Charts ──
st.markdown('<p class="section-header">30-Day Failure Forecast</p>', unsafe_allow_html=True)

forecast_df = run_query(session, Q.FORECAST_DATA)
historical_df = run_query(session, Q.HISTORICAL_FAILURES)

if not forecast_df.empty:
    parts = sorted(forecast_df["PART_NUMBER"].unique())
    selected_part = st.selectbox("Select Part Number", parts, index=0)

    part_fc = forecast_df[forecast_df["PART_NUMBER"] == selected_part]
    part_hist = historical_df[historical_df["PART_NUMBER"] == selected_part]

    fig = go.Figure()

    if not part_hist.empty:
        fig.add_trace(go.Scatter(
            x=part_hist["EVENT_DATE"], y=part_hist["ACTUAL_FAILURES"],
            mode="lines", name="Historical",
            line=dict(color=COLORS["accent1"], width=2),
        ))

    fig.add_trace(go.Scatter(
        x=part_fc["FORECAST_DATE"], y=part_fc["PREDICTED_FAILURES"],
        mode="lines+markers", name="Forecast",
        line=dict(color=COLORS["healthy"], width=2, dash="dot"),
    ))

    fig.add_trace(go.Scatter(
        x=pd.concat([part_fc["FORECAST_DATE"], part_fc["FORECAST_DATE"][::-1]]),
        y=pd.concat([part_fc["UPPER_BOUND"], part_fc["LOWER_BOUND"][::-1]]),
        fill="toself", fillcolor="rgba(52, 211, 153, 0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="Confidence Band",
    ))

    fig.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="Date", yaxis_title="Failure Count",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

    # Summary
    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Peak Predicted", f"{part_fc['PREDICTED_FAILURES'].max():.2f}")
    fc2.metric("Avg Predicted", f"{part_fc['PREDICTED_FAILURES'].mean():.2f}")
    peak_date = part_fc.loc[part_fc["PREDICTED_FAILURES"].idxmax(), "FORECAST_DATE"]
    fc3.metric("Peak Date", str(peak_date)[:10])
