import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav, kpi_card, kpi_row, page_header
from utils.connection import get_session, run_query
from utils import queries as Q
from utils.ai import generate_insight

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Root Cause Analysis", "page_icon": "🔬"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("🔬", "Root Cause Analysis", "AI-powered defect investigation", ["Cortex AI"]), unsafe_allow_html=True)

session = get_session()

# ── Load core data ────────────────────────────────────────────────────
try:
    rca_summary = run_query(session, Q.RCA_FAILURE_SUMMARY)
except Exception as e:
    st.error(f"Failed to load failure summary: {e}")
    st.stop()

if rca_summary.empty:
    st.warning("No failure data available.")
    st.stop()

# ── Sidebar Filters ───────────────────────────────────────────────────
all_suppliers_df = run_query(session, f"SELECT DISTINCT SUPPLIER_NAME FROM {Q.T}.FACT_QUALITY_EVENTS ORDER BY SUPPLIER_NAME")
all_suppliers = sorted(all_suppliers_df["SUPPLIER_NAME"].tolist()) if not all_suppliers_df.empty else []
with st.sidebar:
    st.markdown("### 🔬 RCA Filters")
    selected_suppliers = st.multiselect("Supplier", all_suppliers, default=[])

    error_codes = sorted(rca_summary["DTC_CODE"].dropna().unique().tolist())
    selected_errors = st.multiselect("Error Code", error_codes, default=[])

# Check for zero-error suppliers
if selected_suppliers:
    error_suppliers = set(rca_summary["SUPPLIER_NAME"].unique())
    zero_error = [s for s in selected_suppliers if s not in error_suppliers]
    if zero_error:
        st.success(f"✅ {', '.join(zero_error)} — **0 failure events recorded**. These suppliers have a clean quality record.")

# Apply filters
filtered = rca_summary.copy()
if selected_suppliers:
    filtered = filtered[filtered["SUPPLIER_NAME"].isin(selected_suppliers)]
if selected_errors:
    filtered = filtered[filtered["DTC_CODE"].isin(selected_errors)]

# ── KPI Row ───────────────────────────────────────────────────────────
total_failures = int(filtered["FAILURE_EVENTS"].sum())
vehicles_affected = int(filtered["VEHICLES_AFFECTED"].sum())
unique_patterns = len(filtered)
avg_temp = round(filtered["AVG_TEMP"].mean(), 1) if not filtered["AVG_TEMP"].isna().all() else 0

st.markdown(kpi_row([
    kpi_card("Total Failure Events", f"{total_failures:,}", "across all patterns", accent="red"),
    kpi_card("Vehicles Affected", f"{vehicles_affected:,}", "unique VINs", accent="amber"),
    kpi_card("Unique Defect Patterns", f"{unique_patterns:,}", "DTC combinations", accent="purple"),
    kpi_card("Avg Temp at Failure", f"{avg_temp}°F", "ambient reading", accent="cyan"),
], cols=4), unsafe_allow_html=True)

st.markdown("---")

# ── Supplier Contribution & Heatmap ───────────────────────────────────
col_pie, col_heat = st.columns(2)

with col_pie:
    st.markdown('<p class="section-header">Supplier Contribution Analysis</p>', unsafe_allow_html=True)
    try:
        supplier_data = run_query(session, Q.SUPPLIER_CONTRIBUTION)
        if not supplier_data.empty:
            fig_pie = px.pie(
                supplier_data,
                names="SUPPLIER_NAME",
                values="TOTAL_FAILURES",
                color_discrete_sequence=[
                    COLORS["primary"], COLORS["critical"], COLORS["warning"],
                    COLORS["accent1"], COLORS["accent2"], COLORS["accent3"],
                ],
                hole=0.4,
            )
            fig_pie.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=True)
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.info("No supplier contribution data.")
    except Exception as e:
        st.error(f"Supplier chart error: {e}")

with col_heat:
    st.markdown('<p class="section-header">Manufacturing Line Correlation</p>', unsafe_allow_html=True)
    try:
        heatmap_data = run_query(session, Q.RCA_CORRELATION_HEATMAP)
        if not heatmap_data.empty:
            pivot = heatmap_data.pivot_table(
                index="SUPPLIER_NAME",
                columns="BATTERY_TYPE_NAME",
                values="FAILURE_RATE_PCT",
                aggfunc="mean",
            ).fillna(0)

            fig_heat = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale="RdYlGn_r",
                text=pivot.values.round(2),
                texttemplate="%{text}%",
                hovertemplate="Supplier: %{y}<br>Battery: %{x}<br>Failure Rate: %{z:.2f}%<extra></extra>",
            ))
            fig_heat.update_layout(**PLOTLY_LAYOUT, height=400)
            st.plotly_chart(fig_heat, width="stretch")
        else:
            st.info("No heatmap data.")
    except Exception as e:
        st.error(f"Heatmap error: {e}")

st.markdown("---")

# ── Sankey Diagram ────────────────────────────────────────────────────
st.markdown('<p class="section-header">Defect Flow: Supplier → Battery Type → Error Code → State</p>', unsafe_allow_html=True)

try:
    sankey_data = run_query(session, Q.RCA_SANKEY_DATA)

    # Apply sidebar filters to Sankey data
    if selected_suppliers:
        sankey_data = sankey_data[sankey_data["SUPPLIER_NAME"].isin(selected_suppliers)]
    if selected_errors:
        sankey_data = sankey_data[sankey_data["DTC_CODE"].isin(selected_errors)]

    if not sankey_data.empty:
        suppliers_s = sankey_data["SUPPLIER_NAME"].unique().tolist()
        batteries_s = sankey_data["BATTERY_TYPE_NAME"].unique().tolist()
        errors_s = sankey_data["DTC_CODE"].dropna().unique().tolist()
        states_s = sankey_data["STATE"].unique().tolist()[:10]

        all_labels = suppliers_s + batteries_s + errors_s + states_s
        label_idx = {label: i for i, label in enumerate(all_labels)}

        sources, targets, values = [], [], []

        # Supplier → Battery Type
        for _, r in sankey_data.groupby(["SUPPLIER_NAME", "BATTERY_TYPE_NAME"])["FLOW_COUNT"].sum().reset_index().iterrows():
            if r["SUPPLIER_NAME"] in label_idx and r["BATTERY_TYPE_NAME"] in label_idx:
                sources.append(label_idx[r["SUPPLIER_NAME"]])
                targets.append(label_idx[r["BATTERY_TYPE_NAME"]])
                values.append(int(r["FLOW_COUNT"]))

        # Battery Type → Error Code
        for _, r in sankey_data.groupby(["BATTERY_TYPE_NAME", "DTC_CODE"])["FLOW_COUNT"].sum().reset_index().iterrows():
            if r["BATTERY_TYPE_NAME"] in label_idx and r["DTC_CODE"] in label_idx:
                sources.append(label_idx[r["BATTERY_TYPE_NAME"]])
                targets.append(label_idx[r["DTC_CODE"]])
                values.append(int(r["FLOW_COUNT"]))

        # Error Code → State
        state_flows = sankey_data[sankey_data["STATE"].isin(states_s)].groupby(["DTC_CODE", "STATE"])["FLOW_COUNT"].sum().reset_index()
        for _, r in state_flows.iterrows():
            if r["DTC_CODE"] in label_idx and r["STATE"] in label_idx:
                sources.append(label_idx[r["DTC_CODE"]])
                targets.append(label_idx[r["STATE"]])
                values.append(int(r["FLOW_COUNT"]))

        node_colors = (
            [COLORS["critical"]] * len(suppliers_s)
            + [COLORS["warning"]] * len(batteries_s)
            + [COLORS["accent1"]] * len(errors_s)
            + [COLORS["primary"]] * len(states_s)
        )

        fig_sankey = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, label=all_labels, color=node_colors),
            link=dict(
                source=sources, target=targets, value=values,
                color="rgba(41, 181, 232, 0.2)",
            ),
        ))
        fig_sankey.update_layout(**PLOTLY_LAYOUT, height=500, title="Supplier → Battery Type → Error Code → State")
        st.plotly_chart(fig_sankey, width="stretch")
    else:
        st.info("No Sankey data available for the current filters.")
except Exception as e:
    st.error(f"Sankey diagram error: {e}")

st.markdown("---")

# ── Root Cause Summary Table ──────────────────────────────────────────
st.markdown('<p class="section-header">Quality Issue → Likely Root Cause</p>', unsafe_allow_html=True)

top5 = filtered.nlargest(5, "FAILURE_EVENTS")[
    ["ERROR_DESCRIPTION", "SUPPLIER_NAME", "BATTERY_TYPE_NAME", "FAILURE_EVENTS", "VEHICLES_AFFECTED", "AVG_TEMP"]
].rename(columns={
    "ERROR_DESCRIPTION": "Error Description",
    "SUPPLIER_NAME": "Supplier",
    "BATTERY_TYPE_NAME": "Battery Type",
    "FAILURE_EVENTS": "Failure Events",
    "VEHICLES_AFFECTED": "Vehicles Affected",
    "AVG_TEMP": "Avg Temp (°F)",
})

st.dataframe(top5, width="stretch", hide_index=True)

st.markdown("---")

# ── Defect-to-Component Mapping ───────────────────────────────────────
with st.expander("Defect-to-Component Mapping", expanded=False):
    try:
        comp_map = run_query(session, Q.DEFECT_COMPONENT_MAP)
        if not comp_map.empty:
            st.dataframe(comp_map, width="stretch", hide_index=True)
        else:
            st.info("No component mapping data.")
    except Exception as e:
        st.error(f"Component map error: {e}")

st.markdown("---")

# ── AI Root Cause Analysis ────────────────────────────────────────────
st.markdown('<p class="section-header">AI-Powered Root Cause Analysis</p>', unsafe_allow_html=True)

if st.button("Generate AI Root Cause Analysis", type="primary"):
    with st.spinner("Analyzing with Cortex AI..."):
        try:
            top_pattern = filtered.iloc[0] if not filtered.empty else None
            context_lines = []
            for _, r in filtered.head(10).iterrows():
                context_lines.append(
                    f"Supplier={r['SUPPLIER_NAME']}, Battery={r['BATTERY_TYPE_NAME']}, "
                    f"Error={r['DTC_CODE']}, Desc={r['ERROR_DESCRIPTION']}, "
                    f"Events={r['FAILURE_EVENTS']}, Vehicles={r['VEHICLES_AFFECTED']}, "
                    f"AvgTemp={r['AVG_TEMP']}F, AvgDist={r['AVG_DISTANCE']}mi"
                )
            data_ctx = "\n".join(context_lines)

            prompt = f"""You are an automotive battery quality analyst. Analyze these vehicle battery failure patterns and provide a structured root cause analysis.

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
        except Exception as e:
            st.error(f"AI analysis error: {e}")

# ── Business Insight ──────────────────────────────────────────────────
st.markdown("---")
try:
    if not rca_summary.empty:
        top_error = rca_summary.iloc[0]
        total_failures = int(rca_summary["FAILURE_EVENTS"].sum())
        top_pct = round(int(top_error["FAILURE_EVENTS"]) / total_failures * 100, 1)
        unique_patterns = len(rca_summary)
        top3 = rca_summary.head(3)[["ERROR_DESCRIPTION", "SUPPLIER_NAME", "FAILURE_EVENTS"]].to_string(index=False)
        context = (
            f"Root Cause Analysis Dashboard. "
            f"Total failure events: {total_failures:,}, "
            f"Unique defect patterns: {unique_patterns}. "
            f"Top root cause: '{top_error['ERROR_DESCRIPTION']}' from {top_error['SUPPLIER_NAME']} "
            f"with {top_error['FAILURE_EVENTS']} events ({top_pct}% of total). "
            f"Top 3 patterns:\n{top3}"
        )
        insight = generate_insight(session, "root_cause", context)
        st.info(f"**Business Insight:** {insight}")
except Exception:
    pass
