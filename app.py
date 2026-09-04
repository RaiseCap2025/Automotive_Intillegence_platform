import streamlit as st
from utils.styling import PAGE_CONFIG, CUSTOM_CSS, render_sidebar_nav

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

st.markdown("""
<div style="text-align:center; padding: 20px 0 10px 0;">
    <h1 style="color:#29B5E8; font-size:2.5rem; margin-bottom:0;">
        ⚡ Vehicle Quality Command Center
    </h1>
    <p style="color:#8B949E; font-size:1.1rem; margin-top:4px;">
        AI-Powered Automotive Battery Intelligence Platform &nbsp;|&nbsp; Snowflake + Cortex AI
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Navigation cards
all_pages = [
    ("📊", "Executive Command Center", "Fleet KPIs, health scores, risk rankings", "pages/01_📊_Executive_Command_Center.py"),
    ("🔋", "Vehicle Health Monitor", "Live vehicle status with health indicators", "pages/02_🔋_Vehicle_Health_Monitor.py"),
    ("🔬", "Root Cause Investigator", "AI-powered failure analysis with defect tracing", "pages/03_🔬_Root_Cause_Investigator.py"),
    ("📈", "Failure Prediction", "ML forecasts with risk scoring", "pages/04_📈_Failure_Prediction.py"),
    ("🤖", "AutoDoctor Copilot", "Natural language Q&A over quality data", "pages/05_🤖_AutoDoctor_Copilot.py"),
    ("💰", "Recall Simulator", "What-if analysis for recall decisions", "pages/06_💰_Recall_Simulator.py"),
    ("🏭", "Supplier Intelligence", "Supplier quality scorecards", "pages/07_🏭_Supplier_Intelligence.py"),
    ("🌎", "Geo Intelligence", "Geographic failure heatmaps", "pages/08_🌎_Geo_Intelligence.py"),
    ("⚙️", "Action Center", "Automated response rules", "pages/09_⚙️_Action_Center.py"),
    ("🎯", "Demo Mode", "One-click demo for judges", "pages/10_🎯_Demo_Mode.py"),
]

CARD = (
    "background:linear-gradient(135deg,#161B22 0%,#1A2332 100%);"
    "border:1.5px solid #29B5E8;border-radius:12px;"
    "padding:22px 18px 16px 18px;min-height:180px;"
    "box-shadow:0 0 14px rgba(41,181,232,0.10);"
)

for row_start in range(0, len(all_pages), 5):
    cols = st.columns(5)
    for i, (icon, title, desc, path) in enumerate(all_pages[row_start:row_start + 5]):
        with cols[i]:
            st.markdown(
                f'<div style="{CARD}">'
                f'<div style="font-size:2.2rem;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-size:1.05rem;font-weight:700;color:#FAFAFA;margin-bottom:6px;">{title}</div>'
                f'<div style="font-size:0.82rem;color:#8B949E;margin-bottom:12px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.page_link(path, label=f"Open {title}", use_container_width=True)
    st.markdown("")

st.markdown("---")
st.caption("Snowflake x Capgemini Hackathon 2026 | Built with Streamlit, Snowpark, Cortex AI & Snowflake ML")
