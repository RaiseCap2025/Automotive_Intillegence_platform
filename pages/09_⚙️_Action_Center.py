import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Action Center", "page_icon": "⚙️"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("⚙️ Action Center")
st.caption("Automated response rules and early warning alerts")

session = get_session()

# ── Alert Summary ──
alerts = run_query(session, Q.EARLY_WARNINGS)
alert_counts = run_query(session, Q.ALERTS_BY_SEVERITY)

severity_map = {r["SEVERITY"]: int(r["CNT"]) for _, r in alert_counts.iterrows()}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Alerts", f"{len(alerts):,}")
c2.metric("Critical", f"{severity_map.get('CRITICAL', 0):,}")
c3.metric("High", f"{severity_map.get('HIGH', 0):,}")
c4.metric("Medium", f"{severity_map.get('MEDIUM', 0):,}")

st.markdown("---")

# ── Auto-Action Rules ──
st.markdown('<p class="section-header">Automated Response Rules</p>', unsafe_allow_html=True)

rules = [
    {"condition": "Risk Score > 90%", "action": "Create Emergency Service Ticket",
     "target": "Service Operations", "icon": "🚨", "color": COLORS["critical"]},
    {"condition": "Supplier Defect Rate > 3%", "action": "Notify Procurement Team",
     "target": "Procurement & Supplier Mgmt", "icon": "📧", "color": COLORS["warning"]},
    {"condition": "Battery Failure Forecast > 10/week", "action": "Schedule Fleet Inspection",
     "target": "Fleet Maintenance", "icon": "🔧", "color": COLORS["accent3"]},
    {"condition": "DTC Spike Detected (2x WoW)", "action": "Trigger Root Cause Investigation",
     "target": "Quality Engineering", "icon": "🔬", "color": COLORS["accent1"]},
    {"condition": "Regional Risk > 70%", "action": "Issue Regional Recall Advisory",
     "target": "Executive Leadership", "icon": "📋", "color": COLORS["critical"]},
]

for rule in rules:
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border-left:4px solid {rule['color']};
                border-radius:8px; padding:14px 18px; margin-bottom:10px;">
        <span style="font-size:1.2rem;">{rule['icon']}</span>
        <b style="color:{rule['color']};">{rule['condition']}</b>
        <span style="color:{COLORS['text_dim']};">&nbsp;&rarr;&nbsp;</span>
        <b>{rule['action']}</b>
        <span style="color:{COLORS['text_dim']}; font-size:0.85rem;">&nbsp;|&nbsp;{rule['target']}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Active Triggered Actions ──
st.markdown('<p class="section-header">Triggered Actions (from Early Warning System)</p>', unsafe_allow_html=True)

# Map alerts to actions
critical_alerts = alerts[alerts["SEVERITY"] == "CRITICAL"]
high_alerts = alerts[alerts["SEVERITY"] == "HIGH"]

triggered = []
if len(critical_alerts) > 0:
    triggered.append({"action": "Emergency Service Tickets Created", "count": len(critical_alerts),
                       "severity": "CRITICAL", "badge": "badge-critical"})
if len(high_alerts) > 0:
    triggered.append({"action": "Root Cause Investigations Opened", "count": len(high_alerts),
                       "severity": "HIGH", "badge": "badge-warning"})
triggered.append({"action": "Supplier Quality Reviews Scheduled", "count": 2,
                   "severity": "MEDIUM", "badge": "badge-warning"})

for t in triggered:
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border-radius:8px; padding:12px 16px; margin-bottom:8px; display:flex; align-items:center; gap:12px;">
        <span class="{t['badge']}">{t['severity']}</span>
        <b>{t['action']}</b>
        <span style="color:{COLORS['primary']}; margin-left:auto; font-size:1.1rem; font-weight:700;">{t['count']}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Recent Alerts Table ──
st.markdown('<p class="section-header">Recent Early Warning Alerts</p>', unsafe_allow_html=True)

severity_filter = st.multiselect("Filter Severity", ["CRITICAL", "HIGH", "MEDIUM"],
                                  default=["CRITICAL", "HIGH"])
filtered_alerts = alerts[alerts["SEVERITY"].isin(severity_filter)]
st.dataframe(filtered_alerts.head(50), width="stretch", hide_index=True)
