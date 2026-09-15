import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Supplier Intelligence", "page_icon": "🏭"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🏭 Supplier Intelligence Hub")
st.caption("Supplier quality scorecards and performance benchmarking")

session = get_session()

# ── Supplier Scorecard ──
sc = run_query(session, Q.SUPPLIER_SCORECARD_FULL)

if sc.empty:
    st.warning("No supplier data available.")
    st.stop()

# ── KPI Row ──
c1, c2, c3, c4 = st.columns(4)
approved = len(sc[sc["SUPPLIER_STATUS"] == "APPROVED"])
watchlist = len(sc[sc["SUPPLIER_STATUS"] == "WATCH_LIST"])
c1.metric("Total Suppliers", len(sc))
c2.metric("Approved", approved)
c3.metric("Watch List", watchlist)
c4.metric("Avg Reliability", f"{sc['RELIABILITY_SCORE'].mean():.1f}/100")

st.markdown("---")

# ── Scorecard Table ──
st.markdown('<p class="section-header">Supplier Scorecard</p>', unsafe_allow_html=True)

for _, s in sc.iterrows():
    status = s["SUPPLIER_STATUS"]
    color = COLORS["healthy"] if status == "APPROVED" else COLORS["critical"]
    badge = "badge-healthy" if status == "APPROVED" else "badge-critical"

    with st.container():
        cols = st.columns([3, 2, 2, 2, 2, 1])
        cols[0].markdown(f"**{s['SUPPLIER_NAME']}**")
        cols[1].markdown(f"Reliability: **{s['RELIABILITY_SCORE']:.0f}**/100")
        cols[2].markdown(f"Failure Rate: **{s['OVERALL_FAILURE_RATE']}%**")
        cols[3].markdown(f"Parts: **{int(s['PARTS_SUPPLIED'])}**")
        cols[4].markdown(f"Events: **{int(s['TOTAL_EVENTS']):,}**")
        cols[5].markdown(f"<span class='{badge}'>{status.replace('_', ' ')}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── Reliability Bar ──
left, right = st.columns(2)

with left:
    st.markdown('<p class="section-header">Reliability Score Comparison</p>', unsafe_allow_html=True)
    fig_rel = px.bar(
        sc, x="SUPPLIER_NAME", y="RELIABILITY_SCORE",
        color="RELIABILITY_SCORE", color_continuous_scale=["#F87171", "#FBBF24", "#34D399"],
        text="RELIABILITY_SCORE",
    )
    fig_rel.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig_rel.update_layout(**PLOTLY_LAYOUT, height=320, coloraxis_showscale=False,
                          xaxis_title="", yaxis_title="Reliability Score")
    st.plotly_chart(fig_rel, width="stretch")

with right:
    st.markdown('<p class="section-header">Failure Rate by Supplier</p>', unsafe_allow_html=True)
    fig_fr = px.bar(
        sc, x="SUPPLIER_NAME", y="OVERALL_FAILURE_RATE",
        color="OVERALL_FAILURE_RATE", color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
        text="OVERALL_FAILURE_RATE",
    )
    fig_fr.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_fr.update_layout(**PLOTLY_LAYOUT, height=320, coloraxis_showscale=False,
                         xaxis_title="", yaxis_title="Failure Rate (%)")
    st.plotly_chart(fig_fr, width="stretch")

st.markdown("---")

# ── Trend over time ──
st.markdown('<p class="section-header">Failure Rate Trend by Supplier</p>', unsafe_allow_html=True)
trend = run_query(session, Q.SUPPLIER_WEEKLY_TREND)
if not trend.empty:
    fig_trend = px.line(trend, x="WEEK_START", y="FAILURE_RATE_PCT", color="SUPPLIER_NAME", markers=True)
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=320, xaxis_title="Week",
                            yaxis_title="Failure Rate (%)", legend_title="Supplier")
    st.plotly_chart(fig_trend, width="stretch")

# ── Battery Type Performance ──
st.markdown("---")
st.markdown('<p class="section-header">Battery Type Performance by Supplier</p>', unsafe_allow_html=True)
batt = run_query(session, Q.BATTERY_TYPE_PERFORMANCE)
if not batt.empty:
    fig_batt = px.bar(batt, x="BATTERY_TYPE_NAME", y="FAILURE_RATE_PCT", color="SUPPLIER_NAME",
                      barmode="group", text="FAILURE_RATE_PCT")
    fig_batt.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_batt.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="Battery Type",
                           yaxis_title="Failure Rate (%)", legend_title="Supplier")
    st.plotly_chart(fig_batt, width="stretch")
