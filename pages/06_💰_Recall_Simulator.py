import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, AVG_COST_PER_FAILURE, AVG_RECALL_COST_PER_VEHICLE, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Recall Simulator", "page_icon": "💰"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("💰 Recall Impact Simulator")
st.caption("What-if analysis for recall decisions — calculate cost, savings, and risk trade-offs")

session = get_session()

# ── Load base data ──
base_df = run_query(session, Q.RECALL_BASE)

# ── Scenario Configuration ──
st.markdown('<p class="section-header">Configure Recall Scenario</p>', unsafe_allow_html=True)

col_filter, col_sliders = st.columns([1, 1])

with col_filter:
    suppliers = base_df["SUPPLIER_NAME"].dropna().unique().tolist()
    sel_supplier = st.selectbox("Target Supplier", ["All Suppliers"] + suppliers)

    battery_types = base_df["BATTERY_TYPE_NAME"].dropna().unique().tolist()
    sel_battery = st.selectbox("Target Battery Type", ["All Types"] + battery_types)

with col_sliders:
    risk_threshold = st.slider("Risk Score Threshold (recall vehicles above this)", 20, 100, 50, 5)
    cost_per_failure = st.slider("Estimated Cost per Failure ($)", 1000, 10000, AVG_COST_PER_FAILURE, 500)
    recall_cost_per_vehicle = st.slider("Recall Cost per Vehicle ($)", 100, 1000, AVG_RECALL_COST_PER_VEHICLE, 50)

# ── Apply filters ──
scenario = base_df.copy()
if sel_supplier != "All Suppliers":
    scenario = scenario[scenario["SUPPLIER_NAME"] == sel_supplier]
if sel_battery != "All Types":
    scenario = scenario[scenario["BATTERY_TYPE_NAME"] == sel_battery]

recalled = scenario[scenario["RISK_SCORE"] >= risk_threshold]
not_recalled = scenario[scenario["RISK_SCORE"] < risk_threshold]

# ── Calculations ──
recalled_count = len(recalled)
recalled_with_errors = int(recalled["ERROR_COUNT"].sum())
future_failures_avoided = int(recalled[recalled["ERROR_COUNT"] > 0].shape[0] * 0.85)
total_recall_cost = recalled_count * recall_cost_per_vehicle
savings_from_avoided = future_failures_avoided * cost_per_failure
net_impact = savings_from_avoided - total_recall_cost

st.markdown("---")

# ── Results ──
st.markdown('<p class="section-header">Recall Impact Analysis</p>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Affected Vehicles", f"{recalled_count:,}")
c2.metric("Future Failures Avoided", f"{future_failures_avoided:,}")
c3.metric("Recall Cost", f"${total_recall_cost / 1e6:.2f}M")
net_color = "normal" if net_impact >= 0 else "inverse"
c4.metric("Net Savings", f"${net_impact / 1e6:.2f}M", delta=f"{'Positive' if net_impact >= 0 else 'Negative'} ROI", delta_color=net_color)

st.markdown("---")

# ── Waterfall Chart ──
st.markdown('<p class="section-header">Cost-Benefit Waterfall</p>', unsafe_allow_html=True)

fig_waterfall = go.Figure(go.Waterfall(
    x=["Potential Failure Cost", "Recall Execution Cost", "Net Impact"],
    y=[savings_from_avoided, -total_recall_cost, net_impact],
    measure=["relative", "relative", "total"],
    text=[f"${savings_from_avoided/1e6:.2f}M", f"-${total_recall_cost/1e6:.2f}M", f"${net_impact/1e6:.2f}M"],
    textposition="outside",
    connector=dict(line=dict(color=COLORS["text_dim"])),
    increasing=dict(marker=dict(color=COLORS["healthy"])),
    decreasing=dict(marker=dict(color=COLORS["critical"])),
    totals=dict(marker=dict(color=COLORS["primary"] if net_impact >= 0 else COLORS["critical"])),
))
fig_waterfall.update_layout(**PLOTLY_LAYOUT, height=350, yaxis_title="USD")
st.plotly_chart(fig_waterfall, width="stretch")

# ── Side-by-Side Comparison ──
st.markdown("---")
st.markdown('<p class="section-header">Scenario Comparison: Do Nothing vs Recall</p>', unsafe_allow_html=True)

do_nothing_cost = recalled_with_errors * cost_per_failure

left, right = st.columns(2)
with left:
    st.markdown(f"""
    <div style="background:#7F1D1D; border-radius:10px; padding:20px; border:1px solid {COLORS['critical']};">
        <h3 style="color:{COLORS['critical']};">Do Nothing</h3>
        <p>Expected failures: <b>{recalled_with_errors:,}</b></p>
        <p>Projected cost: <b>${do_nothing_cost/1e6:.2f}M</b></p>
        <p>Customer impact: <b>High</b></p>
        <p>Brand risk: <b style="color:{COLORS['critical']};">Severe</b></p>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown(f"""
    <div style="background:#065F46; border-radius:10px; padding:20px; border:1px solid {COLORS['healthy']};">
        <h3 style="color:{COLORS['healthy']};">Execute Recall</h3>
        <p>Vehicles recalled: <b>{recalled_count:,}</b></p>
        <p>Total recall cost: <b>${total_recall_cost/1e6:.2f}M</b></p>
        <p>Failures prevented: <b>{future_failures_avoided:,}</b></p>
        <p>Net savings: <b style="color:{COLORS['healthy']};">${net_impact/1e6:.2f}M</b></p>
    </div>
    """, unsafe_allow_html=True)

# ── Affected vehicles table ──
with st.expander(f"View Affected Vehicles ({recalled_count:,})"):
    if not recalled.empty:
        st.dataframe(
            recalled[["VIN", "RISK_SCORE", "RISK_TIER", "SUPPLIER_NAME", "BATTERY_TYPE_NAME", "STATE", "ERROR_COUNT"]].head(100),
            width="stretch", hide_index=True
        )
