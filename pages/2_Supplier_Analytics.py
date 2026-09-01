import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.connection import get_session, run_query
from utils.queries import (
    SUPPLIER_FAILURE_RATES,
    SUPPLIER_WEEKLY_TREND,
    BATTERY_TYPE_PERFORMANCE,
    TEMPERATURE_VS_FAILURES,
)

st.set_page_config(page_title="Supplier Analytics", page_icon="🏭", layout="wide")
st.title("🏭 Supplier Quality Analytics")
st.markdown("Compare supplier performance and identify quality issues by battery type.")

session = get_session()

# --- Supplier Scorecard ---
st.subheader("Supplier Performance Scorecard")
supplier_df = run_query(session, SUPPLIER_FAILURE_RATES)

if not supplier_df.empty:
    c1, c2, c3 = st.columns(3)
    worst = supplier_df.iloc[0]
    best = supplier_df.iloc[-1]
    c1.metric("Worst Supplier", worst["SUPPLIER_NAME"], f"{worst['FAILURE_RATE_PCT']}% failure rate")
    c2.metric("Best Supplier", best["SUPPLIER_NAME"], f"{best['FAILURE_RATE_PCT']}% failure rate")
    c3.metric("Total Vehicles Affected", f"{int(supplier_df['VEHICLES_AFFECTED'].sum()):,}")

    fig_supplier = px.bar(
        supplier_df,
        x="SUPPLIER_NAME",
        y="FAILURE_RATE_PCT",
        color="FAILURE_RATE_PCT",
        color_continuous_scale="RdYlGn_r",
        text="FAILURE_RATE_PCT",
        hover_data=["TOTAL_EVENTS", "TOTAL_FAILURES", "VEHICLES_AFFECTED"],
    )
    fig_supplier.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_supplier.update_layout(
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=20, b=80),
        xaxis_title="Supplier",
        yaxis_title="Failure Rate (%)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_supplier, use_container_width=True)

st.markdown("---")

# --- Supplier Trend Over Time ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Failure Rate Trend by Supplier")
    trend_df = run_query(session, SUPPLIER_WEEKLY_TREND)
    if not trend_df.empty:
        fig_trend = px.line(
            trend_df,
            x="WEEK_START",
            y="FAILURE_RATE_PCT",
            color="SUPPLIER_NAME",
            markers=True,
        )
        fig_trend.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis_title="Week",
            yaxis_title="Failure Rate (%)",
            legend_title="Supplier",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("Temperature vs Failure Rate")
    temp_df = run_query(session, TEMPERATURE_VS_FAILURES)
    if not temp_df.empty:
        fig_temp = px.scatter(
            temp_df,
            x="TEMP_BUCKET",
            y="FAILURE_RATE_PCT",
            size="TOTAL_EVENTS",
            color="FAILURE_RATE_PCT",
            color_continuous_scale="RdYlBu_r",
        )
        fig_temp.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis_title="Average Temperature (°F)",
            yaxis_title="Failure Rate (%)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_temp, use_container_width=True)

# --- Battery Type Performance ---
st.subheader("Failure Rate by Battery Type & Supplier")
batt_df = run_query(session, BATTERY_TYPE_PERFORMANCE)
if not batt_df.empty:
    fig_batt = px.bar(
        batt_df,
        x="BATTERY_TYPE_NAME",
        y="FAILURE_RATE_PCT",
        color="SUPPLIER_NAME",
        barmode="group",
        text="FAILURE_RATE_PCT",
    )
    fig_batt.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_batt.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title="Battery Type",
        yaxis_title="Failure Rate (%)",
        legend_title="Supplier",
    )
    st.plotly_chart(fig_batt, use_container_width=True)

# --- Detail Table ---
with st.expander("Supplier Detail Table"):
    st.dataframe(supplier_df, use_container_width=True, hide_index=True)
