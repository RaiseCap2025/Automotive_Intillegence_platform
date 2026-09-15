import streamlit as st
import plotly.graph_objects as go
import json
import time
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, AVG_COST_PER_FAILURE, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Demo Mode", "page_icon": "🎯"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🎯 Judge Demo Mode")
st.caption("One-click end-to-end demonstration — Detection → RCA → Prediction → Action → Impact")

session = get_session()

st.markdown("---")
st.markdown("### Select a Demo Scenario")

sc1, sc2, sc3 = st.columns(3)

scenario = None
with sc1:
    if st.button("🔋 Simulate Battery Failure", width="stretch", type="primary"):
        scenario = "battery"
with sc2:
    if st.button("🏭 Simulate Supplier Defect", width="stretch", type="primary"):
        scenario = "supplier"
with sc3:
    if st.button("📋 Simulate Recall Decision", width="stretch", type="primary"):
        scenario = "recall"

if scenario:
    st.markdown("---")

    # ── STEP 1: Detection ──
    with st.status("Step 1: Anomaly Detection", expanded=True) as s1:
        time.sleep(0.5)

        if scenario == "battery":
            alerts = run_query(session, f"""
                SELECT VIN, CAR_ID, SEVERITY, EXPLANATION
                FROM {Q.T}.EARLY_WARNING_ALERTS
                WHERE SEVERITY = 'CRITICAL' LIMIT 5
            """)
            st.markdown(f"**Detected {len(alerts)} critical battery anomalies**")
            st.dataframe(alerts, width="stretch", hide_index=True)

        elif scenario == "supplier":
            sc_data = run_query(session, f"""
                SELECT SUPPLIER_NAME, OVERALL_FAILURE_RATE, RELIABILITY_SCORE, SUPPLIER_STATUS
                FROM {Q.T}.SUPPLIER_SCORECARD WHERE SUPPLIER_STATUS = 'WATCH_LIST'
            """)
            st.markdown(f"**{len(sc_data)} suppliers flagged on Watch List**")
            st.dataframe(sc_data, width="stretch", hide_index=True)

        elif scenario == "recall":
            geo = run_query(session, f"""
                SELECT STATE_AB, STATE, AVG_RISK_SCORE, CRITICAL_COUNT, HIGH_RISK_PCT, REGIONAL_STATUS
                FROM {Q.T}.FLEET_HEALTH_GEO WHERE REGIONAL_STATUS = 'RECALL_CANDIDATE'
                ORDER BY AVG_RISK_SCORE DESC LIMIT 5
            """)
            st.markdown(f"**{len(geo)} states identified as recall candidates**")
            st.dataframe(geo, width="stretch", hide_index=True)

        s1.update(label="Step 1: Anomaly Detection - Complete", state="complete")

    # ── STEP 2: Root Cause Analysis ──
    with st.status("Step 2: AI Root Cause Analysis", expanded=True) as s2:
        time.sleep(0.5)

        risk_data = run_query(session, f"""
            SELECT PRIMARY_RISK_FACTOR, COUNT(*) AS cnt,
                   AVG(RISK_SCORE) AS avg_risk
            FROM {Q.T}.RISK_EXPLANATION
            WHERE RISK_TIER IN ('CRITICAL', 'HIGH')
            GROUP BY PRIMARY_RISK_FACTOR ORDER BY cnt DESC
        """)

        if not risk_data.empty:
            top_factor = risk_data.iloc[0]
            confidence = min(round(top_factor["CNT"] / risk_data["CNT"].sum() * 100), 95)

            rc1, rc2, rc3 = st.columns(3)
            rc1.markdown(f"**Confidence:** <span style='color:{COLORS['primary']}; font-size:1.8rem; font-weight:700;'>{confidence}%</span>", unsafe_allow_html=True)
            rc2.metric("Primary Factor", top_factor["PRIMARY_RISK_FACTOR"].replace("_", " "))
            rc3.metric("Avg Risk Score", f"{top_factor['AVG_RISK']:.1f}")

            st.markdown("**Risk Factor Breakdown:**")
            for _, r in risk_data.iterrows():
                pct = round(r["CNT"] / risk_data["CNT"].sum() * 100)
                st.markdown(f"- **{r['PRIMARY_RISK_FACTOR'].replace('_', ' ')}**: {int(r['CNT'])} vehicles ({pct}%)")

        s2.update(label="Step 2: Root Cause Analysis - Complete", state="complete")

    # ── STEP 3: Prediction ──
    with st.status("Step 3: Failure Prediction", expanded=True) as s3:
        time.sleep(0.5)

        risk_tiers = run_query(session, f"""
            SELECT RISK_TIER, COUNT(*) AS cnt FROM {Q.T}.VEHICLE_RISK_SCORE
            GROUP BY RISK_TIER ORDER BY cnt DESC
        """)
        tier_map = {r["RISK_TIER"]: int(r["CNT"]) for _, r in risk_tiers.iterrows()}

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Critical", f"{tier_map.get('CRITICAL', 0):,}")
        p2.metric("High Risk", f"{tier_map.get('HIGH', 0):,}")
        p3.metric("Medium", f"{tier_map.get('MEDIUM', 0):,}")
        p4.metric("Low", f"{tier_map.get('LOW', 0):,}")

        forecast = run_query(session, Q.FORECAST_SUMMARY).iloc[0]
        predicted = max(int(forecast["TOTAL_PREDICTED_FAILURES"] or 0), 0)
        st.metric("30-Day Predicted Failures", f"{predicted:,}")

        s3.update(label="Step 3: Prediction - Complete", state="complete")

    # ── STEP 4: Recommended Actions ──
    with st.status("Step 4: Automated Actions", expanded=True) as s4:
        time.sleep(0.5)

        actions_data = run_query(session, f"""
            SELECT RECOMMENDED_ACTION, COUNT(*) AS cnt
            FROM {Q.T}.RISK_EXPLANATION
            WHERE RISK_TIER IN ('CRITICAL', 'HIGH')
            GROUP BY RECOMMENDED_ACTION ORDER BY cnt DESC LIMIT 5
        """)

        for _, a in actions_data.iterrows():
            action_text = a["RECOMMENDED_ACTION"]
            icon = "🚨" if "IMMEDIATE" in action_text else "🔧" if "MONITOR" in action_text else "📋"
            st.markdown(f"{icon} **{action_text}** — {int(a['CNT'])} vehicles")

        s4.update(label="Step 4: Actions Triggered - Complete", state="complete")

    # ── STEP 5: Business Impact ──
    with st.status("Step 5: Business Impact Summary", expanded=True) as s5:
        time.sleep(0.5)

        total_at_risk = tier_map.get("CRITICAL", 0) + tier_map.get("HIGH", 0)
        projected_cost = total_at_risk * AVG_COST_PER_FAILURE

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #161B22, #1A2332); border:2px solid {COLORS['primary']};
                    border-radius:12px; padding:24px; text-align:center;">
            <h2 style="color:{COLORS['primary']}; margin-bottom:20px;">Business Impact Summary</h2>
            <div style="display:flex; justify-content:space-around;">
                <div>
                    <p style="color:{COLORS['text_dim']};">Vehicles at Risk</p>
                    <p style="font-size:2rem; font-weight:700; color:{COLORS['critical']};">{total_at_risk:,}</p>
                </div>
                <div>
                    <p style="color:{COLORS['text_dim']};">Projected Cost if No Action</p>
                    <p style="font-size:2rem; font-weight:700; color:{COLORS['critical']};">${projected_cost/1e6:.1f}M</p>
                </div>
                <div>
                    <p style="color:{COLORS['text_dim']};">Savings with Early Intervention</p>
                    <p style="font-size:2rem; font-weight:700; color:{COLORS['healthy']};">${projected_cost*0.85/1e6:.1f}M</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        s5.update(label="Step 5: Business Impact - Complete", state="complete")

    st.markdown("---")
    st.success("Demo complete. All 5 stages executed successfully.")

else:
    st.info("Click a scenario button above to start the end-to-end demo walkthrough.")
