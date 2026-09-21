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

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Anomaly Detection", "page_icon": "🚨"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("🚨", "Anomaly Detection", "Real-time monitoring and alerts", ["Cortex Agent"]), unsafe_allow_html=True)

session = get_session()

# ── Load data ──
try:
    alerts_df = run_query(session, Q.EARLY_WARNINGS)
except Exception:
    alerts_df = pd.DataFrame()

try:
    severity_df = run_query(session, Q.ALERTS_BY_SEVERITY)
except Exception:
    severity_df = pd.DataFrame()

try:
    temp_df = run_query(session, Q.ANOMALY_TEMP_PATTERNS)
except Exception:
    temp_df = pd.DataFrame()

try:
    risk_df = run_query(session, Q.ANOMALY_RISK_ACTIONS)
except Exception:
    risk_df = pd.DataFrame()

try:
    sensor_df = run_query(session, Q.SENSOR_DEVIATION_BY_SUPPLIER)
except Exception:
    sensor_df = pd.DataFrame()

# ── Helper to pull severity count ──
def _sev_count(sev: str) -> int:
    if severity_df.empty:
        return 0
    row = severity_df[severity_df["SEVERITY"] == sev]
    return int(row["CNT"].iloc[0]) if not row.empty else 0

# ── Prominent alert box ──
if not alerts_df.empty:
    critical = alerts_df[alerts_df["SEVERITY"] == "CRITICAL"]
    if not critical.empty:
        latest = critical.iloc[0]
        alert_type = latest.get("ALERT_TYPE", "Anomaly")
        count = len(critical)
        explanation = latest.get("EXPLANATION", "")
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#7F1D1D,#991B1B);border:1px solid #F87171;'
            f'border-radius:0.75rem;padding:1rem 1.25rem;margin-bottom:1rem;">'
            f'<span style="font-size:1.1rem;font-weight:700;color:#F87171;">⚠️ {alert_type}</span>'
            f' detected in <b style="color:#FBBF24;">{count}</b> vehicles. '
            f'<span style="color:#D1D5DB;">{explanation}</span></div>',
            unsafe_allow_html=True,
        )

# ── KPI tiles ──
st.markdown(kpi_row([
    kpi_card("Total Alerts", f"{len(alerts_df)}", "active warnings", accent="blue"),
    kpi_card("Critical", f"{_sev_count('CRITICAL')}", "immediate action", accent="red"),
    kpi_card("High", f"{_sev_count('HIGH')}", "escalated", accent="amber"),
    kpi_card("Medium", f"{_sev_count('MEDIUM')}", "monitoring", accent="cyan"),
], cols=4), unsafe_allow_html=True)

st.markdown("---")

# ── Alert Cards ──
st.markdown('<p class="section-header">Recent Alerts</p>', unsafe_allow_html=True)

SEVERITY_COLORS = {"CRITICAL": "#F87171", "HIGH": "#FB923C", "MEDIUM": "#FBBF24"}

if not alerts_df.empty:
    for _, row in alerts_df.head(10).iterrows():
        sev = row.get("SEVERITY", "MEDIUM")
        color = SEVERITY_COLORS.get(sev, "#FBBF24")
        badge_bg = {"CRITICAL": "#7F1D1D", "HIGH": "#78350F", "MEDIUM": "#713F12"}.get(sev, "#713F12")
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#161B22,#1A2332);'
            f'border:1px solid {color};border-left:4px solid {color};'
            f'border-radius:0.75rem;padding:1rem;margin-bottom:0.8rem;">'
            f'<span style="background:{badge_bg};color:{color};padding:0.2em 0.7em;'
            f'border-radius:0.75em;font-size:0.8em;font-weight:600;">{sev}</span> '
            f'<span style="color:#E5E7EB;font-weight:600;margin-left:0.5rem;">{row.get("ALERT_TYPE", "")}</span>'
            f'<span style="color:#8B949E;float:right;font-size:0.85em;">{row.get("DETECTED_AT", "")}</span>'
            f'<br/><span style="color:#9CA3AF;font-size:0.85em;">VIN: {row.get("VIN", "N/A")}</span>'
            f'<p style="color:#D1D5DB;margin:0.5rem 0 0 0;font-size:0.9em;">{row.get("EXPLANATION", "")}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("No alerts found.")

st.markdown("---")

# ── Sensor Temperature Deviation Chart ──
st.markdown('<p class="section-header">Sensor Temperature Deviation Chart</p>', unsafe_allow_html=True)

if not temp_df.empty:
    fig_temp = go.Figure()

    fig_temp.add_trace(go.Scatter(
        x=temp_df["WEEK"], y=temp_df["AVG_TEMP"],
        mode="lines+markers", name="Avg Temp",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=5),
    ))
    fig_temp.add_trace(go.Scatter(
        x=temp_df["WEEK"], y=temp_df["UPPER_BAND"],
        mode="lines", name="Upper 2σ",
        line=dict(color=COLORS["critical"], width=1, dash="dash"),
    ))
    fig_temp.add_trace(go.Scatter(
        x=temp_df["WEEK"], y=temp_df["LOWER_BAND"],
        mode="lines", name="Lower 2σ",
        line=dict(color=COLORS["healthy"], width=1, dash="dash"),
    ))

    # Mark high-error periods
    threshold = temp_df["ERRORS_IN_PERIOD"].quantile(0.75)
    anomaly = temp_df[temp_df["ERRORS_IN_PERIOD"] >= threshold]
    if not anomaly.empty:
        fig_temp.add_trace(go.Scatter(
            x=anomaly["WEEK"], y=anomaly["AVG_TEMP"],
            mode="markers", name="High Error Period",
            marker=dict(color="red", size=10, symbol="x"),
        ))

    fig_temp.update_layout(**PLOTLY_LAYOUT, height=400,
                           xaxis_title="Week", yaxis_title="Temperature (°F)")
    st.plotly_chart(fig_temp, width="stretch")
else:
    st.info("No temperature pattern data available.")

st.markdown("---")

# ── AI-Generated Risk Explanations ──
st.markdown('<p class="section-header">AI-Generated Risk Explanations</p>', unsafe_allow_html=True)
if not risk_df.empty:
    display_risk = risk_df[["VIN", "RISK_TIER", "PRIMARY_RISK_FACTOR", "RECOMMENDED_ACTION"]].head(10)
    display_risk.columns = ["VIN", "Risk Tier", "Primary Risk Factor", "Recommended Action"]
    st.dataframe(display_risk, width="stretch", hide_index=True, height=400)
else:
    st.info("No risk explanation data available.")

st.markdown("---")

# ── Recommended Corrective Actions ──
st.markdown('<p class="section-header">Recommended Corrective Actions</p>', unsafe_allow_html=True)

if not risk_df.empty:
    for tier in ["CRITICAL", "HIGH"]:
        tier_data = risk_df[risk_df["RISK_TIER"] == tier]
        if tier_data.empty:
            continue
        tier_color = SEVERITY_COLORS.get(tier, "#FBBF24")
        st.markdown(
            f'<span style="color:{tier_color};font-weight:700;font-size:1rem;">{tier}</span>',
            unsafe_allow_html=True,
        )
        actions = tier_data["RECOMMENDED_ACTION"].dropna().unique()
        for action in actions:
            st.markdown(f"- {action}")
else:
    st.info("No corrective action data available.")

# ── Business Insight ──────────────────────────────────────────────────
st.markdown("---")
try:
    alerts_df = run_query(session, Q.ALERTS_BY_SEVERITY)
    if not alerts_df.empty:
        total_alerts = int(alerts_df["ALERT_COUNT"].sum())
        critical_row = alerts_df[alerts_df["SEVERITY"].str.upper() == "CRITICAL"]
        critical_alerts = int(critical_row["ALERT_COUNT"].iloc[0]) if not critical_row.empty else 0
        pct_critical = round(critical_alerts / total_alerts * 100, 1) if total_alerts > 0 else 0
        context = (
            f"Anomaly Detection Dashboard. "
            f"Total active early warning alerts: {total_alerts}, "
            f"Critical alerts: {critical_alerts} ({pct_critical}%). "
            f"Alert breakdown by severity: {alerts_df.to_string(index=False)}. "
            f"Corrective actions are being recommended for Critical and High risk tiers."
        )
        insight = generate_insight(session, "anomaly_detection", context)
        st.info(f"**Business Insight:** {insight}")
except Exception:
    pass
