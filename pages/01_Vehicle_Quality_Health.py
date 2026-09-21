import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav, kpi_card, kpi_row, page_header
from utils.connection import get_session, run_query
from utils import queries as Q
from utils.ai import generate_insight

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Vehicle Quality Health", "page_icon": "🏥"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("🏥", "Vehicle Quality Health", "Overall quality status of vehicles in the field", ["Fleet Analytics"]), unsafe_allow_html=True)

session = get_session()

# ── KPI Tiles ────────────────────────────────────────────────────────────────
try:
    kpi = run_query(session, Q.KPI_OVERVIEW).iloc[0]
    high_risk = run_query(session, Q.HIGH_RISK_VEHICLES).iloc[0]
    qs = run_query(session, Q.QUALITY_SCORE_OVERALL).iloc[0]

    st.markdown(kpi_row([
        kpi_card("Total Vehicles", f"{int(kpi['TOTAL_VEHICLES']):,}", "monitored fleet", accent="blue"),
        kpi_card("Active Incidents", f"{int(kpi['TOTAL_FAILURES']):,}", "quality events", accent="red"),
        kpi_card("Defect Rate", f"{kpi['FAILURE_RATE_PCT']}%", "fleet-wide", accent="amber"),
        kpi_card("High Risk", f"{int(high_risk['HIGH_RISK_COUNT']):,}", "vehicles flagged", accent="red"),
        kpi_card("Quality Score", f"{qs['QUALITY_SCORE']}", "composite index", accent="green"),
    ], cols=5), unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")

st.divider()

# ── Row 1: Trend + Failures by Model ─────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<p class="section-header">Defect Trend Over Time</p>', unsafe_allow_html=True)
    try:
        trend = run_query(session, Q.WEEKLY_FAILURE_TREND)
        fig = px.line(trend, x="WEEK_START", y="FAILURES")
        fig.update_traces(line=dict(color=COLORS["critical"], width=2))
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Week", yaxis_title="Failures")
        st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.error(f"Failed to load trend: {e}")

with col_right:
    st.markdown('<p class="section-header">Failure Incidents by Vehicle Model</p>', unsafe_allow_html=True)
    try:
        model = run_query(session, Q.FAILURES_BY_MODEL)
        fig = px.bar(
            model, x="FAILURE_COUNT", y="VEHICLE_CONFIG", orientation="h",
        )
        fig.update_traces(marker_color=COLORS["primary"])
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Failure Count", yaxis_title="", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.error(f"Failed to load model failures: {e}")

# ── Row 2: Geo Map (full width) ───────────────────────────────────────────────
st.markdown('<p class="section-header">Geographic Heat Map</p>', unsafe_allow_html=True)
try:
    geo = run_query(session, Q.FAILURES_BY_STATE)
    fig = px.choropleth(
        geo,
        locations="STATE_AB",
        color="FAILURE_COUNT",
        locationmode="USA-states",
        scope="usa",
        color_continuous_scale=[COLORS["healthy"], COLORS["warning"], COLORS["critical"]],
    )
    fig.update_layout(**PLOTLY_LAYOUT, geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, width="stretch")
except Exception as e:
    st.error(f"Failed to load geo map: {e}")

# ── Quality by Model Year (expandable) ────────────────────────────────────────
with st.expander("📋 Quality Score by Model Year", expanded=False):
    try:
        my = run_query(session, Q.QUALITY_BY_MODEL_YEAR)
        st.dataframe(my, width="stretch", hide_index=True)
    except Exception as e:
        st.error(f"Failed to load model year data: {e}")

# ── Business Insight ──────────────────────────────────────────────────────────
try:
    my_data = run_query(session, Q.QUALITY_BY_MODEL_YEAR)
    if not my_data.empty:
        fleet_avg = my_data["AVG_RISK_SCORE"].mean()
        worst = my_data.loc[my_data["AVG_RISK_SCORE"].idxmax()]
        pct_higher = round((worst["AVG_RISK_SCORE"] - fleet_avg) / fleet_avg * 100, 1)
        context = (
            f"Vehicle Quality Health Dashboard. "
            f"Total vehicles: {int(kpi['TOTAL_VEHICLES']):,}, "
            f"Active quality incidents: {int(kpi['TOTAL_FAILURES']):,}, "
            f"Defect rate: {kpi['FAILURE_RATE_PCT']}%, "
            f"Vehicles at high risk: {int(high_risk['HIGH_RISK_COUNT']):,}, "
            f"Quality score: {qs['QUALITY_SCORE']}. "
            f"Worst model year: {int(worst['MODEL_YEAR'])} with avg risk score {worst['AVG_RISK_SCORE']:.1f} "
            f"({pct_higher}% above fleet average of {fleet_avg:.1f})."
        )
        insight = generate_insight(session, "vehicle_quality", context)
        st.info(f"**Business Insight:** {insight}")
except Exception as e:
    st.error(f"Failed to generate insight: {e}")
