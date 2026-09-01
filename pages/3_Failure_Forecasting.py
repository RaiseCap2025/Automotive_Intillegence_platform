import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.connection import get_session, run_query
from utils.queries import FORECAST_DATA, HISTORICAL_FAILURES

st.set_page_config(page_title="Failure Forecasting", page_icon="📈", layout="wide")
st.title("📈 Failure Forecasting")
st.markdown("ML-powered 30-day failure predictions per battery part using Snowflake ML.")

session = get_session()

# Load data
forecast_df = run_query(session, FORECAST_DATA)
historical_df = run_query(session, HISTORICAL_FAILURES)

if forecast_df.empty:
    st.warning("No forecast data available.")
    st.stop()

# Part selector
parts = sorted(forecast_df["PART_NUMBER"].unique())
selected_part = st.selectbox("Select Battery Part Number", parts, index=0)

# Filter data
part_forecast = forecast_df[forecast_df["PART_NUMBER"] == selected_part].copy()
part_history = historical_df[historical_df["PART_NUMBER"] == selected_part].copy()

st.markdown("---")

# --- Forecast Chart with Confidence Interval ---
st.subheader(f"30-Day Failure Forecast: {selected_part}")

fig = go.Figure()

# Historical actuals
if not part_history.empty:
    fig.add_trace(go.Scatter(
        x=part_history["EVENT_DATE"],
        y=part_history["ACTUAL_FAILURES"],
        mode="lines",
        name="Historical (Actual)",
        line=dict(color="#6366F1", width=2),
    ))

# Forecast
fig.add_trace(go.Scatter(
    x=part_forecast["FORECAST_DATE"],
    y=part_forecast["PREDICTED_FAILURES"],
    mode="lines+markers",
    name="Forecast",
    line=dict(color="#10B981", width=2, dash="dot"),
    marker=dict(size=5),
))

# Confidence band
fig.add_trace(go.Scatter(
    x=pd.concat([part_forecast["FORECAST_DATE"], part_forecast["FORECAST_DATE"][::-1]]),
    y=pd.concat([part_forecast["UPPER_BOUND"], part_forecast["LOWER_BOUND"][::-1]]),
    fill="toself",
    fillcolor="rgba(16, 185, 129, 0.15)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Confidence Interval",
    hoverinfo="skip",
))

fig.update_layout(
    template="plotly_dark",
    height=400,
    margin=dict(l=40, r=20, t=20, b=40),
    xaxis_title="Date",
    yaxis_title="Failure Count",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)

# --- Summary Metrics ---
st.markdown("---")
st.subheader("Forecast Summary")
c1, c2, c3 = st.columns(3)

max_forecast = part_forecast["PREDICTED_FAILURES"].max()
avg_forecast = part_forecast["PREDICTED_FAILURES"].mean()
peak_date = part_forecast.loc[part_forecast["PREDICTED_FAILURES"].idxmax(), "FORECAST_DATE"] if max_forecast > 0 else "N/A"

c1.metric("Peak Predicted Failures", f"{max_forecast:.1f}")
c2.metric("Avg Predicted Failures", f"{avg_forecast:.2f}")
c3.metric("Peak Date", str(peak_date)[:10] if peak_date != "N/A" else "N/A")

# --- Alert Table: Parts with highest forecast ---
st.markdown("---")
st.subheader("Parts Requiring Attention")
alert_df = forecast_df.groupby("PART_NUMBER").agg(
    max_forecast=("PREDICTED_FAILURES", "max"),
    avg_forecast=("PREDICTED_FAILURES", "mean"),
).reset_index().sort_values("max_forecast", ascending=False).head(10)
alert_df.columns = ["Part Number", "Max Predicted Failures", "Avg Predicted Failures"]
st.dataframe(alert_df, use_container_width=True, hide_index=True)
