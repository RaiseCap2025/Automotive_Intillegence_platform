import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.connection import get_session, run_query
from utils.queries import (
    KPI_OVERVIEW,
    WEEKLY_FAILURE_TREND,
    ERROR_CODE_DISTRIBUTION,
    FAILURES_BY_STATE,
)

st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")
st.title("📊 Executive Dashboard")
st.markdown("Real-time overview of vehicle battery quality across the fleet.")

session = get_session()

# --- KPIs ---
kpi_df = run_query(session, KPI_OVERVIEW)
row = kpi_df.iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Vehicles Monitored", f"{int(row['TOTAL_VEHICLES']):,}")
c2.metric("Total Quality Events", f"{int(row['TOTAL_EVENTS']):,}")
c3.metric("Overall Failure Rate", f"{row['FAILURE_RATE_PCT']}%")
c4.metric("Vehicles with Failures", f"{int(row['VEHICLES_WITH_FAILURES']):,}")

st.markdown("---")

# --- Weekly Failure Trend ---
st.subheader("Weekly Failure Rate Trend")
trend_df = run_query(session, WEEKLY_FAILURE_TREND)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend_df["WEEK_START"],
    y=trend_df["FAILURE_RATE_PCT"],
    mode="lines+markers",
    name="Failure Rate %",
    line=dict(color="#EF4444", width=2),
    marker=dict(size=4),
))
fig_trend.update_layout(
    xaxis_title="Week",
    yaxis_title="Failure Rate (%)",
    template="plotly_dark",
    height=350,
    margin=dict(l=40, r=20, t=20, b=40),
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- Two-column section ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Error Code Distribution")
    error_df = run_query(session, ERROR_CODE_DISTRIBUTION)
    if not error_df.empty:
        fig_err = px.bar(
            error_df,
            x="EVENT_COUNT",
            y="DTC_CODE",
            orientation="h",
            color="EVENT_COUNT",
            color_continuous_scale="Reds",
            hover_data=["ERROR_DESCRIPTION"],
        )
        fig_err.update_layout(
            template="plotly_dark",
            height=320,
            margin=dict(l=40, r=20, t=20, b=40),
            showlegend=False,
            coloraxis_showscale=False,
            yaxis_title="DTC Error Code",
            xaxis_title="Failure Events",
        )
        st.plotly_chart(fig_err, use_container_width=True)

with col_right:
    st.subheader("Failures by State")
    state_df = run_query(session, FAILURES_BY_STATE)
    if not state_df.empty:
        fig_map = px.choropleth(
            state_df,
            locations="STATE_AB",
            locationmode="USA-states",
            color="FAILURE_COUNT",
            scope="usa",
            color_continuous_scale="OrRd",
            hover_name="STATE",
            hover_data=["FAILURE_COUNT", "AVG_TEMP"],
        )
        fig_map.update_layout(
            template="plotly_dark",
            height=320,
            margin=dict(l=0, r=0, t=0, b=0),
            geo=dict(bgcolor="rgba(0,0,0,0)"),
            coloraxis_colorbar=dict(title="Failures"),
        )
        st.plotly_chart(fig_map, use_container_width=True)

# --- Detailed Table ---
with st.expander("View Raw Weekly Data"):
    st.dataframe(trend_df, use_container_width=True, hide_index=True)
