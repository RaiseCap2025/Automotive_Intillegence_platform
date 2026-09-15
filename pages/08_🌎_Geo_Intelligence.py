import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Geo Intelligence", "page_icon": "🌎"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🌎 Geo Intelligence Dashboard")
st.caption("Geographic failure analysis and regional risk zones")

session = get_session()

# ── State-level health data ──
geo = run_query(session, Q.GEO_STATE_HEALTH)

if geo.empty:
    st.warning("No geographic data available.")
    st.stop()

# ── KPIs ──
recall_states = geo[geo["REGIONAL_STATUS"] == "RECALL_CANDIDATE"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("States Analyzed", len(geo))
c2.metric("Recall Candidate Regions", len(recall_states))
c3.metric("Highest Risk State", geo.iloc[0]["STATE_AB"] if not geo.empty else "N/A")
c4.metric("Max Risk Score", f"{geo['AVG_RISK_SCORE'].max():.1f}")

st.markdown("---")

# ── Choropleth Map ──
st.markdown('<p class="section-header">Regional Risk Heatmap</p>', unsafe_allow_html=True)

fig_map = px.choropleth(
    geo, locations="STATE_AB", locationmode="USA-states",
    color="AVG_RISK_SCORE", scope="usa",
    color_continuous_scale=["#34D399", "#FBBF24", "#F87171", "#DC2626"],
    hover_name="STATE",
    hover_data=["TOTAL_VEHICLES", "CRITICAL_COUNT", "HIGH_RISK_PCT", "TOTAL_ERRORS", "REGIONAL_STATUS"],
)
fig_map.update_layout(
    **PLOTLY_LAYOUT, height=450,
    geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"),
    coloraxis_colorbar=dict(title="Avg Risk"),
)
st.plotly_chart(fig_map, width="stretch")

st.markdown("---")

# ── State Risk Table ──
left, right = st.columns(2)

with left:
    st.markdown('<p class="section-header">Recall Candidate Regions</p>', unsafe_allow_html=True)
    if not recall_states.empty:
        for _, r in recall_states.iterrows():
            st.markdown(
                f"<span class='badge-critical'>{r['STATE_AB']}</span> "
                f"**{r['STATE']}** — {int(r['CRITICAL_COUNT'])} critical, "
                f"{r['HIGH_RISK_PCT']}% high risk, {int(r['TOTAL_ERRORS'])} errors",
                unsafe_allow_html=True
            )
    else:
        st.info("No recall candidate regions detected.")

with right:
    st.markdown('<p class="section-header">Top Failure States</p>', unsafe_allow_html=True)
    fail_states = run_query(session, Q.FAILURES_BY_STATE)
    if not fail_states.empty:
        fig_bar = px.bar(
            fail_states.head(15), x="FAILURE_COUNT", y="STATE_AB", orientation="h",
            color="FAILURE_COUNT", color_continuous_scale="OrRd",
            hover_data=["AVG_TEMP", "VEHICLES_AFFECTED"],
        )
        fig_bar.update_layout(**PLOTLY_LAYOUT, height=400, coloraxis_showscale=False,
                              xaxis_title="Failure Count", yaxis_title="")
        st.plotly_chart(fig_bar, width="stretch")

# ── Full State Table ──
st.markdown("---")
with st.expander("View All States Data"):
    display_cols = ["STATE_AB", "STATE", "TOTAL_VEHICLES", "AVG_RISK_SCORE",
                    "CRITICAL_COUNT", "HIGH_COUNT", "MEDIUM_COUNT", "LOW_COUNT",
                    "HIGH_RISK_PCT", "TOTAL_ERRORS", "REGIONAL_STATUS"]
    st.dataframe(geo[display_cols], width="stretch", hide_index=True)
