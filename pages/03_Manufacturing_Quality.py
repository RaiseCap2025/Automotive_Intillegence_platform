import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav, kpi_card, kpi_row, page_header
from utils.connection import get_session, run_query
from utils import queries as Q
from utils.ai import generate_insight

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Manufacturing Quality", "page_icon": "🏭"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown(page_header("🏭", "Manufacturing Quality", "Production quality metrics in real time", ["Plant Ops"]), unsafe_allow_html=True)

session = get_session()

# ── KPI Tiles ──
try:
    kpi = run_query(session, Q.MANUFACTURING_KPI)
    rework = run_query(session, Q.REWORK_RATE)

    st.markdown(kpi_row([
        kpi_card("First Pass Yield", f"{kpi['FIRST_PASS_YIELD'].iloc[0]}%", "production pass rate", accent="green"),
        kpi_card("Defect Rate", f"{kpi['DEFECT_RATE_PCT'].iloc[0]}%", "overall", accent="red"),
        kpi_card("Rework Rate", f"{rework['REWORK_RATE_PCT'].iloc[0]}%", "requires re-processing", accent="amber"),
        kpi_card("Scrap Candidates", f"{int(kpi['SCRAP_CANDIDATES'].iloc[0])}", "flagged units", accent="red"),
        kpi_card("Inspection Failures", f"{int(kpi['INSPECTION_FAILURES'].iloc[0])}", "QA rejects", accent="purple"),
    ], cols=5), unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")

st.markdown("---")

# ── Production Line Performance & Defect by Plant ──
try:
    line_df = run_query(session, Q.PRODUCTION_LINE_PERFORMANCE)
    plant_df = run_query(session, Q.DEFECT_BY_STATE_PLANT)

    left, right = st.columns(2)

    with left:
        st.markdown('<p class="section-header">Production Line Performance</p>', unsafe_allow_html=True)
        if not line_df.empty:
            fig_line = px.bar(
                line_df, x="DEFECT_RATE_PCT", y="PRODUCTION_LINE",
                orientation="h",
                color="DEFECT_RATE_PCT",
                color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
                text="DEFECT_RATE_PCT",
            )
            fig_line.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_line.add_vline(
                x=1.5, line_dash="dash", line_color="#F87171",
                annotation_text="Threshold 1.5%",
                annotation_position="top right",
            )
            fig_line.update_layout(
                **PLOTLY_LAYOUT, height=400, coloraxis_showscale=False,
                xaxis_title="Defect Rate (%)", yaxis_title="",
            )
            st.plotly_chart(fig_line, width="stretch")

    with right:
        st.markdown('<p class="section-header">Defect Rate by Plant</p>', unsafe_allow_html=True)
        if not plant_df.empty:
            fig_plant = px.bar(
                plant_df, x="DEFECT_RATE_PCT", y="STATE",
                orientation="h",
                color="DEFECT_RATE_PCT",
                color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
                text="DEFECT_RATE_PCT",
            )
            fig_plant.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_plant.update_layout(
                **PLOTLY_LAYOUT, height=400, coloraxis_showscale=False,
                xaxis_title="Defect Rate (%)", yaxis_title="",
            )
            st.plotly_chart(fig_plant, width="stretch")
except Exception as e:
    st.error(f"Failed to load production charts: {e}")

st.markdown("---")

# ── Control Chart ──
try:
    ctrl_df = run_query(session, Q.WEEKLY_CONTROL_CHART)

    if not ctrl_df.empty:
        st.markdown('<p class="section-header">Weekly Failure Rate Control Chart</p>', unsafe_allow_html=True)

        mean_val = ctrl_df['FAILURE_RATE_PCT'].mean()
        std_val = ctrl_df['FAILURE_RATE_PCT'].std()
        ucl = mean_val + 2 * std_val
        lcl = max(0, mean_val - 2 * std_val)

        fig_ctrl = go.Figure()
        fig_ctrl.add_trace(go.Scatter(
            x=ctrl_df['WEEK_START'], y=ctrl_df['FAILURE_RATE_PCT'],
            mode='lines+markers', name='Failure Rate',
            line=dict(color=COLORS['primary'], width=2),
            marker=dict(size=5),
        ))
        fig_ctrl.add_trace(go.Scatter(
            x=ctrl_df['WEEK_START'], y=[mean_val] * len(ctrl_df),
            mode='lines', name=f'Mean ({mean_val:.2f}%)',
            line=dict(color='#8B949E', dash='dash', width=1),
        ))
        fig_ctrl.add_trace(go.Scatter(
            x=ctrl_df['WEEK_START'], y=[ucl] * len(ctrl_df),
            mode='lines', name=f'UCL ({ucl:.2f}%)',
            line=dict(color=COLORS['critical'], dash='dash', width=1),
        ))
        fig_ctrl.add_trace(go.Scatter(
            x=ctrl_df['WEEK_START'], y=[lcl] * len(ctrl_df),
            mode='lines', name=f'LCL ({lcl:.2f}%)',
            line=dict(color=COLORS['healthy'], dash='dash', width=1),
        ))
        fig_ctrl.update_layout(
            **PLOTLY_LAYOUT, height=350,
            xaxis_title="Week", yaxis_title="Failure Rate (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_ctrl, width="stretch")
except Exception as e:
    st.error(f"Failed to load control chart: {e}")

st.markdown("---")

# ── Business Insight ──
try:
    if not line_df.empty:
        worst = line_df.iloc[0]
        worst_line = worst['PRODUCTION_LINE']
        worst_rate = worst['DEFECT_RATE_PCT']
        fpy = kpi['FIRST_PASS_YIELD'].iloc[0]
        defect_rate = kpi['DEFECT_RATE_PCT'].iloc[0]
        rework_rate_val = rework['REWORK_RATE_PCT'].iloc[0]
        context = (
            f"Manufacturing Quality Dashboard. "
            f"First pass yield: {fpy}%, Defect rate: {defect_rate}%, Rework rate: {rework_rate_val}%. "
            f"Worst production line: {worst_line} at {worst_rate}% defect rate "
            f"(threshold is 1.5%). "
            f"Production lines summary: {line_df[['PRODUCTION_LINE','DEFECT_RATE_PCT']].to_string(index=False)}"
        )
        insight = generate_insight(session, "manufacturing", context)
        st.info(f"**Business Insight:** {insight}")
except Exception:
    pass
