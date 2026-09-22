"""Shared styling and CSS for the Vehicle Quality Command Center."""
import base64
import os
import html as _html

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
        background-color: #232A3B;
        min-width: 14rem !important;
        width: clamp(14rem, 18vw, 22rem) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p {font-size: 0.9rem;}

    /* KPI Cards — responsive */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #232A3B 0%, #2A3347 100%);
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
    .stTabs [data-baseweb="tab"] {background-color: #232A3B; border-radius: 6px 6px 0 0; padding: 0.5rem 1rem;}

    /* Status badges — em-based so they scale with parent font */
    .badge-healthy {background:#065F46; color:#34D399; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}
    .badge-warning {background:#78350F; color:#FBBF24; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}
    .badge-critical {background:#7F1D1D; color:#F87171; padding:0.2em 0.7em; border-radius:0.75em; font-size:0.8em; font-weight:600;}

    /* Section headers */
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #29B5E8;
        border-bottom: 2px solid #29B5E8; padding-bottom: 0.375rem; margin-bottom: 0.75rem;
    }

    /* ── Rich KPI Cards v2 ── */
    .kpi-grid { display: grid; gap: 1rem; margin-bottom: 1.5rem; }
    .kpi-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }
    .kpi-grid.cols-5 { grid-template-columns: repeat(5, 1fr); }
    @media (max-width: 900px) {
        .kpi-grid.cols-4, .kpi-grid.cols-5 { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-v2 {
        background: linear-gradient(135deg, #232A3B 0%, #2A3347 100%);
        border: 1px solid rgba(41,181,232,0.15);
        border-radius: 0.75rem;
        padding: 1.1rem 1.25rem 0.9rem;
        position: relative; overflow: hidden;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .kpi-v2:hover {
        border-color: rgba(41,181,232,0.35);
        box-shadow: 0 0 16px rgba(41,181,232,0.08);
    }
    .kpi-v2::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        border-radius: 0.75rem 0.75rem 0 0;
    }
    .kpi-v2.accent-cyan::before    { background: linear-gradient(90deg, #22D3EE, #06B6D4); }
    .kpi-v2.accent-blue::before    { background: linear-gradient(90deg, #29B5E8, #38BDF8); }
    .kpi-v2.accent-green::before   { background: linear-gradient(90deg, #34D399, #6EE7B7); }
    .kpi-v2.accent-amber::before   { background: linear-gradient(90deg, #FBBF24, #FB923C); }
    .kpi-v2.accent-red::before     { background: linear-gradient(90deg, #F87171, #EF4444); }
    .kpi-v2.accent-purple::before  { background: linear-gradient(90deg, #818CF8, #A78BFA); }
    .kpi-v2 .kpi-v2-label {
        font-size: 0.7rem; color: #8B949E; text-transform: uppercase;
        letter-spacing: 0.8px; font-weight: 600; margin-bottom: 0.35rem;
    }
    .kpi-v2 .kpi-v2-row {
        display: flex; align-items: baseline; gap: 0.6rem; flex-wrap: wrap;
    }
    .kpi-v2 .kpi-v2-value {
        font-size: clamp(1.3rem, 1.7rem, 2.1rem); font-weight: 800;
        color: #FAFAFA; line-height: 1.1;
    }
    .kpi-v2 .kpi-v2-badge {
        font-size: 0.72rem; font-weight: 700; padding: 0.15em 0.55em;
        border-radius: 0.6em; line-height: 1;
    }
    .kpi-v2 .kpi-v2-badge.up   { background: #065F46; color: #34D399; }
    .kpi-v2 .kpi-v2-badge.down { background: #7F1D1D; color: #F87171; }
    .kpi-v2 .kpi-v2-badge.flat { background: #2D3548; color: #8B949E; }
    .kpi-v2 .kpi-v2-sub {
        font-size: 0.75rem; color: #6E7681; margin-top: 0.25rem;
    }

    /* ── Page header bar ── */
    .page-header-bar {
        display: flex; align-items: center; justify-content: space-between;
        background: linear-gradient(135deg, #1E2535 0%, #232D40 100%);
        border: 1px solid rgba(41,181,232,0.12);
        border-radius: 0.75rem;
        padding: 0.9rem 1.5rem;
        margin-bottom: 1.25rem;
    }
    .page-header-bar .phb-left {
        display: flex; align-items: center; gap: 0.75rem;
    }
    .page-header-bar .phb-icon {
        font-size: 1.6rem; line-height: 1;
    }
    .page-header-bar .phb-title {
        font-size: 1.35rem; font-weight: 700; color: #E6EDF3;
    }
    .page-header-bar .phb-subtitle {
        font-size: 0.8rem; color: #8B949E;
    }
    .page-header-bar .phb-right {
        display: flex; align-items: center; gap: 0.75rem;
    }
    .phb-pill {
        background: rgba(41,181,232,0.08); border: 1px solid rgba(41,181,232,0.18);
        color: #8B949E; padding: 0.25rem 0.7rem; border-radius: 2rem;
        font-size: 0.7rem; font-weight: 500;
    }
    .phb-live-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #34D399; display: inline-block;
        box-shadow: 0 0 6px rgba(52,211,153,0.6);
        animation: pulse-dot 2s infinite;
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

    /* ── Sidebar brand card ── */
    .sidebar-brand {
        background: linear-gradient(135deg, #1E2535 0%, #232D40 100%);
        border: 1px solid rgba(41,181,232,0.35);
        border-radius: 0.6rem;
        padding: 0.7rem 0.85rem;
        margin-bottom: 0.8rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .sidebar-brand::after {
        content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, #29B5E8, #818CF8, #00F5D4);
    }
    .sidebar-brand .brand-name {
        font-size: 1rem; font-weight: 800; color: #E6EDF3;
        letter-spacing: 0.5px;
    }
    .sidebar-brand .brand-icon {
        color: #29B5E8; margin-right: 0.3rem;
    }
    /* ── Sidebar user profile card ── */
    .sidebar-profile {
        background: linear-gradient(135deg, #1E2535 0%, #232D40 100%);
        border: 1px solid rgba(41,181,232,0.2);
        border-radius: 0.6rem;
        padding: 0.6rem 0.75rem;
        margin-top: 1rem;
        display: flex; align-items: center; gap: 0.55rem;
    }
    .sidebar-profile .avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: linear-gradient(135deg, #29B5E8, #818CF8);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.72rem; font-weight: 700; color: #fff;
        flex-shrink: 0;
    }
    .sidebar-profile .profile-name {
        font-size: 0.8rem; color: #C9D1D9; font-weight: 600;
    }
    .sidebar-profile .profile-role {
        font-size: 0.62rem; color: #29B5E8; font-weight: 600;
        letter-spacing: 0.3px;
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
        background: radial-gradient(ellipse at center, rgba(26,31,46,0.96) 0%, rgba(26,31,46,0.98) 100%);
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

    /* Chat avatars — prevent circular crop so full image is visible */
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"] {
        border-radius: 0.375rem !important;
        overflow: visible !important;
    }
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"] img {
        border-radius: 0.375rem !important;
        object-fit: contain !important;
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
    ("🏥", "Vehicle Quality Health", "pages/01_Vehicle_Quality_Health.py"),
    ("🔬", "Root Cause Analysis", "pages/02_Root_Cause_Analysis.py"),
    ("🏭", "Manufacturing Quality", "pages/03_Manufacturing_Quality.py"),
    ("📦", "Supplier Quality", "pages/04_Supplier_Quality.py"),
    ("📈", "Predictive Maintenance", "pages/05_Predictive_Maintenance.py"),
    ("🚨", "Anomaly Detection", "pages/06_Anomaly_Detection.py"),
    ("🤖", "AutoDoctor Copilot", "pages/07_AutoDoctor_Copilot.py"),
]


def render_sidebar_nav():
    """Render branded sidebar navigation and inject spinning car background."""
    import streamlit as st
    with st.sidebar:
        # App brand card
        st.markdown(
            '<div class="sidebar-brand">'
            '<div class="brand-name"><span class="brand-icon">⚡</span>AUTO INTEL AI</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        # Section label
        st.markdown(
            '<div style="padding:0.3rem 0.2rem 0.3rem;">'
            '<div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:1.8px;'
            'color:#484F58;font-weight:700;">Workspace Navigation</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.page_link("app.py", label="⚡ Home", width="stretch")
        for icon, title, path in SIDEBAR_PAGES:
            st.page_link(path, label=f"{icon} {title}", width="stretch")
        # User profile card at bottom
        st.markdown(
            '<div class="sidebar-profile">'
            '<div class="avatar">HP</div>'
            '<div>'
            '<div class="profile-name">HARSH_P</div>'
            '<div class="profile-role">● ACCOUNTADMIN</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    if _CAR_BG_HTML:
        st.markdown(_CAR_BG_HTML, unsafe_allow_html=True)


def kpi_card(
    label: str,
    value: str,
    subtitle: str = "",
    badge: str = "",
    badge_dir: str = "up",
    accent: str = "blue",
) -> str:
    """Return HTML string for a single rich KPI card."""
    badge_html = ""
    if badge:
        badge_html = f'<span class="kpi-v2-badge {_html.escape(badge_dir)}">{_html.escape(badge)}</span>'
    sub_html = ""
    if subtitle:
        sub_html = f'<div class="kpi-v2-sub">{_html.escape(subtitle)}</div>'
    return (
        f'<div class="kpi-v2 accent-{_html.escape(accent)}">'
        f'<div class="kpi-v2-label">{_html.escape(label)}</div>'
        f'<div class="kpi-v2-row">'
        f'<div class="kpi-v2-value">{value}</div>'
        f'{badge_html}'
        f'</div>'
        f'{sub_html}'
        f'</div>'
    )


def kpi_row(cards: list[str], cols: int = 4) -> str:
    """Wrap a list of kpi_card() HTML strings in a responsive grid."""
    inner = "\n".join(cards)
    return f'<div class="kpi-grid cols-{cols}">{inner}</div>'


def page_header(icon: str, title: str, subtitle: str = "", pills: list[str] | None = None) -> str:
    """Return branded page header bar HTML."""
    sub = f'<div class="phb-subtitle">{_html.escape(subtitle)}</div>' if subtitle else ""
    pill_html = ""
    if pills:
        pill_html = "".join(f'<span class="phb-pill">{_html.escape(p)}</span>' for p in pills)
    return (
        f'<div class="page-header-bar">'
        f'<div class="phb-left">'
        f'<span class="phb-icon">{icon}</span>'
        f'<div><div class="phb-title">{_html.escape(title)}</div>{sub}</div>'
        f'</div>'
        f'<div class="phb-right">'
        f'<span class="phb-live-dot"></span>'
        f'<span class="phb-pill">Live</span>'
        f'{pill_html}'
        f'</div>'
        f'</div>'
    )

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
    "bg_card": "#232A3B",
    "text_dim": "#8B949E",
}

RISK_COLORS = ["#34D399", "#6EE7B7", "#FCD34D", "#FBBF24", "#FB923C", "#F87171", "#EF4444", "#DC2626"]

AVG_COST_PER_FAILURE = 4000
AVG_RECALL_COST_PER_VEHICLE = 350
