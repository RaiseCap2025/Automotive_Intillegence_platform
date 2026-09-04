"""Shared styling and CSS for the Vehicle Quality Command Center."""

PAGE_CONFIG = dict(
    page_title="Vehicle Quality Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0.5rem;}
    [data-testid="stSidebar"] {background-color: #161B22;}
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p {font-size: 0.9rem;}

    /* KPI Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161B22 0%, #1A2332 100%);
        border: 1px solid #29B5E8;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 0 12px rgba(41, 181, 232, 0.08);
    }
    [data-testid="stMetric"] label {font-size: 0.82rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.5px;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.7rem; font-weight: 700;}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {gap: 4px;}
    .stTabs [data-baseweb="tab"] {background-color: #161B22; border-radius: 6px 6px 0 0; padding: 8px 16px;}

    /* Status badges */
    .badge-healthy {background:#065F46; color:#34D399; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;}
    .badge-warning {background:#78350F; color:#FBBF24; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;}
    .badge-critical {background:#7F1D1D; color:#F87171; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;}

    /* Section headers */
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #29B5E8;
        border-bottom: 2px solid #29B5E8; padding-bottom: 6px; margin-bottom: 12px;
    }

    /* Sidebar nav links — neon blue bordered outline */
    /* Target the stPageLink containers in the sidebar */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        border: 1.5px solid #29B5E8 !important;
        border-radius: 8px !important;
        margin: 4px 0px !important;
        padding: 8px 12px !important;
        transition: box-shadow 0.2s ease, background-color 0.2s ease;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        box-shadow: 0 0 10px rgba(41, 181, 232, 0.45), 0 0 20px rgba(41, 181, 232, 0.2) !important;
        background-color: rgba(41, 181, 232, 0.08) !important;
    }

    /* Hide the default auto-generated multipage nav */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
"""

# Sidebar navigation builder — call from every page
SIDEBAR_PAGES = [
    ("📊", "Executive Command Center", "pages/01_📊_Executive_Command_Center.py"),
    ("🔋", "Vehicle Health Monitor", "pages/02_🔋_Vehicle_Health_Monitor.py"),
    ("🔬", "Root Cause Investigator", "pages/03_🔬_Root_Cause_Investigator.py"),
    ("📈", "Failure Prediction", "pages/04_📈_Failure_Prediction.py"),
    ("🤖", "AutoDoctor Copilot", "pages/05_🤖_AutoDoctor_Copilot.py"),
    ("💰", "Recall Simulator", "pages/06_💰_Recall_Simulator.py"),
    ("🏭", "Supplier Intelligence", "pages/07_🏭_Supplier_Intelligence.py"),
    ("🌎", "Geo Intelligence", "pages/08_🌎_Geo_Intelligence.py"),
    ("⚙️", "Action Center", "pages/09_⚙️_Action_Center.py"),
    ("🎯", "Demo Mode", "pages/10_🎯_Demo_Mode.py"),
]


def render_sidebar_nav():
    """Render custom sidebar navigation with neon blue outlines."""
    import streamlit as st
    with st.sidebar:
        st.page_link("app.py", label="⚡ Home", use_container_width=True)
        for icon, title, path in SIDEBAR_PAGES:
            st.page_link(path, label=f"{icon} {title}", use_container_width=True)

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=30, b=40),
    font=dict(family="Inter, sans-serif", size=12, color="#FAFAFA"),
)

COLORS = {
    "primary": "#29B5E8",
    "healthy": "#34D399",
    "warning": "#FBBF24",
    "critical": "#F87171",
    "accent1": "#818CF8",
    "accent2": "#F472B6",
    "accent3": "#FB923C",
    "accent4": "#38BDF8",
    "bg_card": "#161B22",
    "text_dim": "#8B949E",
}

RISK_COLORS = ["#34D399", "#6EE7B7", "#FCD34D", "#FBBF24", "#FB923C", "#F87171", "#EF4444", "#DC2626"]

AVG_COST_PER_FAILURE = 4000
AVG_RECALL_COST_PER_VEHICLE = 350
