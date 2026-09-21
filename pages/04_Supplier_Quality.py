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

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Supplier Quality", "page_icon": "📦"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("📦", "Supplier Quality", "Evaluate component supplier performance", ["Supplier Ops"]), unsafe_allow_html=True)

session = get_session()

# ── KPI Row ──
try:
    scorecard = run_query(session, Q.SUPPLIER_SCORECARD_FULL)
    total_suppliers = len(scorecard)
    approved = int(scorecard["SUPPLIER_STATUS"].str.upper().eq("APPROVED").sum())
    watch_list = int(scorecard["SUPPLIER_STATUS"].str.contains("Watch|Suspended", case=False, na=False).sum())
    avg_reliability = round(scorecard["RELIABILITY_SCORE"].mean(), 1)

    st.markdown(kpi_row([
        kpi_card("Total Suppliers", f"{total_suppliers}", "battery component vendors", accent="blue"),
        kpi_card("Approved", f"{approved}", "certified status", accent="green"),
        kpi_card("Watch List", f"{watch_list}", "under review", accent="amber"),
        kpi_card("Avg Reliability", f"{avg_reliability}", "composite score", accent="cyan"),
    ], cols=4), unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")
    scorecard = pd.DataFrame()

st.markdown("---")

# ── Supplier Rankings Table ──
try:
    st.markdown('<p class="section-header">Supplier Rankings</p>', unsafe_allow_html=True)
    ppm = run_query(session, Q.SUPPLIER_PPM)

    rankings = scorecard.copy()
    if not ppm.empty:
        rankings = rankings.merge(
            ppm[["SUPPLIER_NAME", "DEFECT_PPM"]],
            on="SUPPLIER_NAME", how="left",
        )
    else:
        rankings["DEFECT_PPM"] = None

    display_cols = {
        "SUPPLIER_NAME": "Supplier Name",
        "RELIABILITY_SCORE": "Quality Score",
        "DEFECT_PPM": "Defect PPM",
        "OVERALL_FAILURE_RATE": "Failure Rate %",
        "SUPPLIER_STATUS": "Status",
        "TOTAL_EVENTS": "Total Events",
        "TOTAL_FAILURES": "Total Failures",
    }
    available = [c for c in display_cols if c in rankings.columns]
    table_df = rankings[available].rename(columns=display_cols)
    st.dataframe(table_df, width="stretch", hide_index=True)

    # Certification badges
    badge_html = ""
    for _, row in rankings.iterrows():
        name = row["SUPPLIER_NAME"]
        status = str(row.get("SUPPLIER_STATUS", ""))
        if "APPROVED" in status.upper():
            badge_html += f'<span class="badge-healthy">{name}: {status}</span>&nbsp;&nbsp;'
        elif "Watch" in status:
            badge_html += f'<span class="badge-warning">{name}: {status}</span>&nbsp;&nbsp;'
        elif "Suspended" in status:
            badge_html += f'<span class="badge-critical">{name}: {status}</span>&nbsp;&nbsp;'
    if badge_html:
        st.markdown(badge_html, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load supplier rankings: {e}")

st.markdown("---")

# ── Defect Trends + Heatmap ──
left, right = st.columns(2)

with left:
    st.markdown('<p class="section-header">Supplier Defect Trends</p>', unsafe_allow_html=True)
    try:
        trend = run_query(session, Q.SUPPLIER_WEEKLY_TREND)
        fig_trend = px.line(
            trend, x="WEEK_START", y="FAILURE_RATE_PCT", color="SUPPLIER_NAME",
            markers=True,
        )
        fig_trend.update_layout(**PLOTLY_LAYOUT, height=400,
                                xaxis_title="Week", yaxis_title="Failure Rate (%)")
        st.plotly_chart(fig_trend, width="stretch")
    except Exception as e:
        st.error(f"Failed to load defect trends: {e}")

with right:
    st.markdown('<p class="section-header">Component Failure Heat Map</p>', unsafe_allow_html=True)
    try:
        heatmap_data = run_query(session, Q.SUPPLIER_COMPONENT_HEATMAP)
        pivot = heatmap_data.pivot_table(
            index="SUPPLIER_NAME", columns="BATTERY_TYPE_NAME",
            values="FAILURE_RATE_PCT", aggfunc="mean",
        ).fillna(0)

        fig_heat = go.Figure(go.Heatmap(
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            z=pivot.values.tolist(),
            colorscale=[[0, "#34D399"], [0.5, "#FBBF24"], [1, "#F87171"]],
            text=pivot.values.round(2).tolist(),
            texttemplate="%{text}%",
            hovertemplate="Supplier: %{y}<br>Battery: %{x}<br>Failure Rate: %{z:.2f}%<extra></extra>",
        ))
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=400,
                               xaxis_title="Battery Type", yaxis_title="Supplier")
        st.plotly_chart(fig_heat, width="stretch")
    except Exception as e:
        st.error(f"Failed to load heatmap: {e}")

st.markdown("---")

# ── Quality Scores + Battery Type Performance ──
left2, right2 = st.columns(2)

with left2:
    st.markdown('<p class="section-header">Supplier Quality Scores</p>', unsafe_allow_html=True)
    try:
        fig_scores = px.bar(
            scorecard, x="SUPPLIER_NAME", y="RELIABILITY_SCORE",
            color="RELIABILITY_SCORE",
            color_continuous_scale=[COLORS["critical"], COLORS["warning"], COLORS["healthy"]],
            text="RELIABILITY_SCORE",
        )
        fig_scores.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_scores.update_layout(**PLOTLY_LAYOUT, height=400, coloraxis_showscale=False,
                                 xaxis_title="Supplier", yaxis_title="Reliability Score")
        st.plotly_chart(fig_scores, width="stretch")
    except Exception as e:
        st.error(f"Failed to load quality scores: {e}")

with right2:
    st.markdown('<p class="section-header">Battery Type Performance</p>', unsafe_allow_html=True)
    try:
        batt = run_query(session, Q.BATTERY_TYPE_PERFORMANCE)
        fig_batt = px.bar(
            batt, x="BATTERY_TYPE_NAME", y="FAILURE_RATE_PCT",
            color="SUPPLIER_NAME", barmode="group",
            text="FAILURE_RATE_PCT",
        )
        fig_batt.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig_batt.update_layout(**PLOTLY_LAYOUT, height=400,
                               xaxis_title="Battery Type", yaxis_title="Failure Rate (%)")
        st.plotly_chart(fig_batt, width="stretch")
    except Exception as e:
        st.error(f"Failed to load battery type performance: {e}")

st.markdown("---")

# ── Certification Status ──
st.markdown('<p class="section-header">Certification Status</p>', unsafe_allow_html=True)
try:
    cert_html = '<div style="display:flex; flex-wrap:wrap; gap:0.75rem; margin-bottom:1rem;">'
    for _, row in scorecard.iterrows():
        name = row["SUPPLIER_NAME"]
        status = str(row.get("SUPPLIER_STATUS", "Unknown"))
        if "APPROVED" in status.upper():
            bg, fg = "#065F46", "#34D399"
        elif "Watch" in status:
            bg, fg = "#78350F", "#FBBF24"
        elif "Suspended" in status:
            bg, fg = "#7F1D1D", "#F87171"
        else:
            bg, fg = "#1F2937", "#8B949E"
        cert_html += (
            f'<span style="background:{bg}; color:{fg}; padding:0.4em 1em; '
            f'border-radius:0.75em; font-size:0.85rem; font-weight:600;">'
            f'{name} — {status}</span>'
        )
    cert_html += "</div>"
    st.markdown(cert_html, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load certification status: {e}")

# ── Business Insight ──
st.markdown("---")
try:
    contrib = run_query(session, Q.SUPPLIER_CONTRIBUTION)
    if not contrib.empty and not scorecard.empty:
        top = contrib.iloc[0]
        context = (
            f"Supplier Quality Dashboard. "
            f"Total suppliers: {total_suppliers}, Approved: {approved}, Watch list: {watch_list}. "
            f"Avg reliability score: {avg_reliability}. "
            f"Top failure contributor: {top['SUPPLIER_NAME']} with {top['PCT_OF_ALL_FAILURES']}% of all failures. "
            f"Supplier scorecard summary: {scorecard[['SUPPLIER_NAME','RELIABILITY_SCORE','OVERALL_FAILURE_RATE','SUPPLIER_STATUS']].to_string(index=False)}"
        )
        insight = generate_insight(session, "supplier_quality", context)
        st.info(f"**Business Insight:** {insight}")
except Exception:
    pass
