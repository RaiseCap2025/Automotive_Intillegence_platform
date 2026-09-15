import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Root Cause Investigator", "page_icon": "🔬"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🔬 AI Root Cause Investigator")
st.caption("AI-powered failure analysis with defect path tracing")

session = get_session()

# ── Failure Summary ──
failures = run_query(session, Q.RCA_FAILURE_SUMMARY)

if failures.empty:
    st.warning("No failure data available.")
    st.stop()

# ── Select Investigation Focus ──
col1, col2 = st.columns(2)
with col1:
    supplier_sel = st.selectbox("Investigate Supplier", ["All"] + failures["SUPPLIER_NAME"].unique().tolist())
with col2:
    error_sel = st.selectbox("Error Code Filter", ["All"] + failures["DTC_CODE"].dropna().unique().tolist())

filt = failures.copy()
if supplier_sel != "All":
    filt = filt[filt["SUPPLIER_NAME"] == supplier_sel]
if error_sel != "All":
    filt = filt[filt["DTC_CODE"] == error_sel]

# ── Confidence & Key Metrics ──
total_failures = int(filt["FAILURE_EVENTS"].sum())
total_vehicles = int(filt["VEHICLES_AFFECTED"].sum())
top_supplier = filt.groupby("SUPPLIER_NAME")["FAILURE_EVENTS"].sum().idxmax()
supplier_pct = round(filt[filt["SUPPLIER_NAME"] == top_supplier]["FAILURE_EVENTS"].sum() / max(total_failures, 1) * 100)
top_error = filt.groupby("DTC_CODE")["FAILURE_EVENTS"].sum().idxmax() if "DTC_CODE" in filt.columns and not filt["DTC_CODE"].isna().all() else "N/A"
avg_temp = round(filt["AVG_TEMP"].mean(), 1)

st.markdown("---")

# ── RCA Card ──
st.markdown('<p class="section-header">Root Cause Analysis</p>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f"**Confidence**\n\n<span style='font-size:2rem; color:{COLORS['primary']}; font-weight:700;'>{supplier_pct}%</span>", unsafe_allow_html=True)
m2.metric("Failure Events", f"{total_failures:,}")
m3.metric("Vehicles Affected", f"{total_vehicles:,}")
m4.metric("Avg Temp at Failure", f"{avg_temp}°F")

st.markdown("---")

# ── Cortex AI Analysis ──
st.markdown('<p class="section-header">AI-Generated Analysis</p>', unsafe_allow_html=True)

if st.button("Generate AI Root Cause Analysis", type="primary"):
    with st.spinner("Analyzing with Cortex AI..."):
        context_lines = []
        for _, r in filt.head(15).iterrows():
            context_lines.append(
                f"Supplier={r['SUPPLIER_NAME']}, Battery={r['BATTERY_TYPE_NAME']}, "
                f"Error={r['DTC_CODE']}, Events={r['FAILURE_EVENTS']}, "
                f"Vehicles={r['VEHICLES_AFFECTED']}, AvgTemp={r['AVG_TEMP']}F, AvgDist={r['AVG_DISTANCE']}mi"
            )
        data_ctx = "\n".join(context_lines)

        prompt = f"""You are an automotive battery quality analyst. Analyze these failure patterns and provide a structured root cause analysis.

DATA:
{data_ctx}

Provide your analysis in this exact format:
PRIMARY CAUSE: [one line]
CONTRIBUTING FACTORS:
- [factor 1]
- [factor 2]
- [factor 3]
RECOMMENDED ACTIONS:
- [action 1]
- [action 2]
- [action 3]
ESTIMATED IMPACT: [vehicles at risk and potential cost]"""

        escaped = prompt.replace("'", "''")
        query = f"""SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b',
            [
                {{'role': 'system', 'content': 'You are a senior automotive quality engineer. Be concise and data-driven.'}},
                {{'role': 'user', 'content': '{escaped}'}}
            ], {{}}) AS response"""

        result = session.sql(query).collect()
        try:
            resp = json.loads(result[0]["RESPONSE"])
            answer = resp.get("choices", [{}])[0].get("messages", str(resp))
        except (json.JSONDecodeError, KeyError, IndexError):
            answer = str(result[0]["RESPONSE"])

        st.markdown(answer)

# ── Risk Explanations from pre-built table ──
st.markdown("---")
st.markdown('<p class="section-header">Detailed Risk Explanations (Top Vehicles)</p>', unsafe_allow_html=True)
risk_exp = run_query(session, Q.RISK_EXPLANATIONS)
if not risk_exp.empty:
    display = risk_exp[["VIN", "RISK_SCORE", "RISK_TIER", "ERROR_COUNT", "SUPPLIER_NAME",
                         "PRIMARY_RISK_FACTOR", "RECOMMENDED_ACTION"]].head(20)
    st.dataframe(display, width="stretch", hide_index=True)

# ── Defect Path Sankey ──
st.markdown("---")
st.markdown('<p class="section-header">Defect Path Visualization</p>', unsafe_allow_html=True)

sankey_data = run_query(session, Q.RCA_SANKEY_DATA)
if not sankey_data.empty:
    all_labels = []
    sources, targets, values = [], [], []

    suppliers = sankey_data["SUPPLIER_NAME"].unique().tolist()
    batteries = sankey_data["BATTERY_TYPE_NAME"].unique().tolist()
    errors = sankey_data["DTC_CODE"].dropna().unique().tolist()
    states = sankey_data["STATE"].unique().tolist()[:10]

    all_labels = suppliers + batteries + errors + states
    label_idx = {l: i for i, l in enumerate(all_labels)}

    # Supplier -> Battery
    for _, r in sankey_data.groupby(["SUPPLIER_NAME", "BATTERY_TYPE_NAME"])["FLOW_COUNT"].sum().reset_index().iterrows():
        if r["SUPPLIER_NAME"] in label_idx and r["BATTERY_TYPE_NAME"] in label_idx:
            sources.append(label_idx[r["SUPPLIER_NAME"]])
            targets.append(label_idx[r["BATTERY_TYPE_NAME"]])
            values.append(int(r["FLOW_COUNT"]))

    # Battery -> Error
    for _, r in sankey_data.groupby(["BATTERY_TYPE_NAME", "DTC_CODE"])["FLOW_COUNT"].sum().reset_index().iterrows():
        if r["BATTERY_TYPE_NAME"] in label_idx and r["DTC_CODE"] in label_idx:
            sources.append(label_idx[r["BATTERY_TYPE_NAME"]])
            targets.append(label_idx[r["DTC_CODE"]])
            values.append(int(r["FLOW_COUNT"]))

    # Error -> State (top 10)
    state_flows = sankey_data[sankey_data["STATE"].isin(states)].groupby(["DTC_CODE", "STATE"])["FLOW_COUNT"].sum().reset_index()
    for _, r in state_flows.iterrows():
        if r["DTC_CODE"] in label_idx and r["STATE"] in label_idx:
            sources.append(label_idx[r["DTC_CODE"]])
            targets.append(label_idx[r["STATE"]])
            values.append(int(r["FLOW_COUNT"]))

    node_colors = (
        [COLORS["critical"]] * len(suppliers) +
        [COLORS["warning"]] * len(batteries) +
        [COLORS["accent1"]] * len(errors) +
        [COLORS["primary"]] * len(states)
    )

    fig_sankey = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, label=all_labels, color=node_colors),
        link=dict(source=sources, target=targets, value=values,
                  color="rgba(41, 181, 232, 0.2)"),
    ))
    fig_sankey.update_layout(**PLOTLY_LAYOUT, height=450, title="Supplier → Battery → Error Code → State")
    st.plotly_chart(fig_sankey, width="stretch")
