import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, AVG_COST_PER_FAILURE, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Executive Command Center", "page_icon": "📊"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("📊 Executive Command Center")
st.caption("Real-time fleet intelligence at a glance")

session = get_session()

# ── KPI Row ──
kpi = run_query(session, Q.KPI_OVERVIEW).iloc[0]
high_risk = run_query(session, Q.HIGH_RISK_VEHICLES).iloc[0]["HIGH_RISK_COUNT"]
forecast_sum = run_query(session, Q.FORECAST_SUMMARY).iloc[0]["TOTAL_PREDICTED_FAILURES"]
predicted = max(int(forecast_sum or 0), 0)
savings = predicted * AVG_COST_PER_FAILURE

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Vehicles Monitored", f"{int(kpi['TOTAL_VEHICLES']):,}")
c2.metric("Active Incidents", f"{int(kpi['TOTAL_FAILURES']):,}")
c3.metric("High Risk Vehicles", f"{int(high_risk):,}")
c4.metric("Recall Risk", "High" if kpi["FAILURE_RATE_PCT"] > 3 else "Medium" if kpi["FAILURE_RATE_PCT"] > 1 else "Low")
c5.metric("Predicted Failures (30d)", f"{predicted:,}")
c6.metric("Potential Savings", f"${savings / 1e6:.1f}M")

st.markdown("---")

# ── Fleet Health + Failure Trend ──
left, right = st.columns([1, 2])

with left:
    st.markdown('<p class="section-header">Fleet Health Score</p>', unsafe_allow_html=True)
    health = run_query(session, Q.FLEET_HEALTH_BUCKETS)
    tier_order = {"LOW": "Healthy", "MEDIUM": "Warning", "HIGH": "At Risk", "CRITICAL": "Critical"}
    tier_colors = {"Healthy": COLORS["healthy"], "Warning": COLORS["warning"],
                   "At Risk": COLORS["accent3"], "Critical": COLORS["critical"]}
    health_map = {}
    for _, r in health.iterrows():
        label = tier_order.get(r["STATUS"], r["STATUS"])
        health_map[label] = health_map.get(label, 0) + int(r["VEHICLE_COUNT"])
    total = sum(health_map.values())

    fig_gauge = go.Figure(go.Pie(
        labels=list(health_map.keys()),
        values=list(health_map.values()),
        hole=0.65,
        marker=dict(colors=[tier_colors.get(k, "#8B949E") for k in health_map.keys()]),
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    healthy_pct = round(health_map.get("Healthy", 0) / max(total, 1) * 100)
    fig_gauge.add_annotation(
        text=f"<b>{healthy_pct}%</b><br>Healthy",
        font=dict(size=20, color=COLORS["healthy"]),
        showarrow=False,
    )
    fig_gauge.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    st.plotly_chart(fig_gauge, width="stretch")

    for status, count in health_map.items():
        pct = round(count / max(total, 1) * 100)
        color = tier_colors.get(status, "#8B949E")
        st.markdown(f"<span style='color:{color}; font-weight:600;'>● {status}</span>&nbsp; {pct}% ({count:,})", unsafe_allow_html=True)

with right:
    st.markdown('<p class="section-header">Failure Rate Trend (Weekly)</p>', unsafe_allow_html=True)
    trend = run_query(session, Q.WEEKLY_FAILURE_TREND)
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend["WEEK_START"], y=trend["FAILURE_RATE_PCT"],
        mode="lines+markers", name="Failure Rate %",
        line=dict(color=COLORS["critical"], width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(248,113,113,0.1)",
    ))
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=300, xaxis_title="Week", yaxis_title="Failure Rate (%)")
    st.plotly_chart(fig_trend, width="stretch")

st.markdown("---")

# ── Supplier Risk + Error Codes ──
left2, right2 = st.columns(2)

with left2:
    st.markdown('<p class="section-header">Supplier Risk Ranking</p>', unsafe_allow_html=True)
    suppliers = run_query(session, Q.SUPPLIER_RISK_RANKING)
    fig_sup = px.bar(
        suppliers, y="SUPPLIER_NAME", x="FAILURE_RATE_PCT", orientation="h",
        color="FAILURE_RATE_PCT", color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
        text="FAILURE_RATE_PCT",
    )
    fig_sup.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_sup.update_layout(**PLOTLY_LAYOUT, height=300, coloraxis_showscale=False,
                          xaxis_title="Failure Rate (%)", yaxis_title="")
    st.plotly_chart(fig_sup, width="stretch")

with right2:
    st.markdown('<p class="section-header">Top Error Codes</p>', unsafe_allow_html=True)
    errors = run_query(session, Q.ERROR_CODE_DISTRIBUTION)
    if not errors.empty:
        fig_err = px.bar(
            errors, x="EVENT_COUNT", y="DTC_CODE", orientation="h",
            color="EVENT_COUNT", color_continuous_scale="Reds",
            hover_data=["ERROR_DESCRIPTION"],
        )
        fig_err.update_layout(**PLOTLY_LAYOUT, height=300, coloraxis_showscale=False,
                              xaxis_title="Failure Events", yaxis_title="DTC Code")
        st.plotly_chart(fig_err, width="stretch")
