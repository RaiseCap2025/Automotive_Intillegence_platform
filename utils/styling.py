"""Shared styling and CSS for the Vehicle Quality Command Center."""
import base64
import os

PAGE_CONFIG = dict(
    page_title="Vehicle Quality Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0.5rem;}
    [data-testid="stSidebar"] {
        background-color: #161B22;
        min-width: 14rem !important;
        width: clamp(14rem, 18vw, 22rem) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p {font-size: 0.9rem;}

    /* KPI Cards — responsive */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161B22 0%, #1A2332 100%);
        border: 1px solid #29B5E8;
        border-radius: 0.625rem;
        padding: 0.875rem 1.125rem;
        box-shadow: 0 0 12px rgba(41, 181, 232, 0.08);
    }
    [data-testid="stMetric"] label {
        font-size: clamp(0.7rem, 0.82rem, 0.95rem);
        color: #8B949E; text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: clamp(1.2rem, 1.7rem, 2.2rem);
        font-weight: 700;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {gap: 4px;}
    .stTabs [data-baseweb="tab"] {background-color: #161B22; border-radius: 6px 6px 0 0; padding: 0.5rem 1rem;}

    /* Status badges — em-based so they scale with parent font */
    .badge-healthy {background:#065F46; color:#34D399; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}
    .badge-warning {background:#78350F; color:#FBBF24; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}
    .badge-critical {background:#7F1D1D; color:#F87171; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}

    /* Section headers */
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #29B5E8;
        border-bottom: 2px solid #29B5E8; padding-bottom: 0.375rem; margin-bottom: 0.75rem;
    }

    /* Sidebar nav links — clean minimal style, responsive sizing */
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        border: none !important;
        border-radius: 0.375rem !important;
        margin: 0.15rem 0 !important;
        padding: 0.5rem 0.75rem !important;
        background-color: transparent !important;
        color: #C9D1D9 !important;
        font-size: clamp(0.78rem, 0.9rem, 1.05rem) !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: background-color 0.2s ease;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        background-color: rgba(255, 255, 255, 0.06) !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background-color: rgba(41, 181, 232, 0.12) !important;
        color: #29B5E8 !important;
        font-weight: 600 !important;
    }

    /* Hide the default auto-generated multipage nav */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Responsive adjustments at high zoom / small screens */
    @media (max-width: 768px) {
        [data-testid="stMetric"] { padding: 0.6rem 0.75rem; }
        [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.2rem; }
        .section-header { font-size: 1rem; }
    }

    /* ── Car Loading Splash (CSS-only auto-hide) ── */
    .car-splash {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 9999 !important;
        pointer-events: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: radial-gradient(ellipse at center, rgba(10,15,30,0.95) 0%, rgba(10,15,30,0.98) 100%);
        animation: splash-dismiss 3.5s ease-in-out forwards;
    }
    @keyframes splash-dismiss {
        0%   { opacity: 1; visibility: visible; }
        75%  { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; }
    }
    .car-splash img {
        width: 65vw !important;
        min-width: 600px !important;
        max-width: 1000px !important;
        height: auto !important;
        opacity: 0.3;
        filter: drop-shadow(0 0 60px rgba(41,181,232,0.4));
    }
    .car-splash .splash-text {
        position: absolute;
        bottom: 25%;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(41,181,232,0.7);
        font-size: 0.95rem;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        animation: pulse-text 1.5s ease-in-out infinite;
    }
    @keyframes pulse-text {
        0%, 100% { opacity: 0.4; }
        50%      { opacity: 1; }
    }
</style>
"""

# Load car image from assets/car.png at runtime
_CAR_IMG_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'car.png')
_CAR_BG_HTML = ''
if os.path.isfile(_CAR_IMG_PATH):
    with open(_CAR_IMG_PATH, 'rb') as _f:
        _CAR_B64 = base64.b64encode(_f.read()).decode()
    _CAR_BG_HTML = (
        f'<div class="car-splash">'
        f'<img src="data:image/png;base64,{_CAR_B64}" alt="car"/>'
        f'<div class="splash-text">Loading...</div>'
        f'</div>'
    )

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
    """Render custom sidebar navigation and inject spinning car background."""
    import streamlit as st
    with st.sidebar:
        st.page_link("app.py", label="⚡ Home", width="stretch")
        for icon, title, path in SIDEBAR_PAGES:
            st.page_link(path, label=f"{icon} {title}", width="stretch")
    if _CAR_BG_HTML:
        st.markdown(_CAR_BG_HTML, unsafe_allow_html=True)

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
