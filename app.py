import streamlit as st
from utils.styling import PAGE_CONFIG, CUSTOM_CSS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

# ── Futuristic Homepage CSS ──
st.markdown("""
<style>
    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #0D1117 0%, #101820 40%, #0a1628 100%);
        border: 1px solid rgba(41,181,232,0.15);
        border-radius: 1rem;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 60%; height: 200%;
        background: radial-gradient(ellipse, rgba(41,181,232,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-size: clamp(1.8rem, 2.6rem, 3.2rem);
        font-weight: 800;
        background: linear-gradient(135deg, #29B5E8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #8B949E;
        font-size: clamp(0.85rem, 1rem, 1.15rem);
        margin: 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(41,181,232,0.12);
        border: 1px solid rgba(41,181,232,0.3);
        color: #29B5E8;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }

    /* KPI stat cards */
    .kpi-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1;
        min-width: 140px;
        background: linear-gradient(135deg, #161B22 0%, #1A2332 100%);
        border: 1px solid rgba(41,181,232,0.2);
        border-radius: 0.75rem;
        padding: 1rem 1.2rem;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
        border-radius: 0.75rem 0.75rem 0 0;
    }
    .kpi-card.blue::after { background: linear-gradient(90deg, #29B5E8, #38BDF8); }
    .kpi-card.green::after { background: linear-gradient(90deg, #34D399, #6EE7B7); }
    .kpi-card.amber::after { background: linear-gradient(90deg, #FBBF24, #FB923C); }
    .kpi-card.red::after { background: linear-gradient(90deg, #F87171, #EF4444); }
    .kpi-card.purple::after { background: linear-gradient(90deg, #818CF8, #A78BFA); }
    .kpi-label {
        font-size: 0.72rem;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }
    .kpi-value {
        font-size: clamp(1.4rem, 1.8rem, 2.2rem);
        font-weight: 800;
        color: #FAFAFA;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #6E7681;
        margin-top: 0.2rem;
    }
    .kpi-trend-up { color: #34D399; font-weight: 600; }
    .kpi-trend-down { color: #F87171; font-weight: 600; }

    /* Fleet status indicators */
    .fleet-status {
        display: flex;
        gap: 1.5rem;
        align-items: center;
        flex-wrap: wrap;
    }
    .status-dot {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot.green { background: #34D399; box-shadow: 0 0 8px rgba(52,211,153,0.5); }
    .dot.amber { background: #FBBF24; box-shadow: 0 0 8px rgba(251,191,36,0.5); }
    .dot.red { background: #F87171; box-shadow: 0 0 8px rgba(248,113,113,0.5); animation: pulse-dot 2s infinite; }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .dot-label {
        font-size: 0.82rem;
        color: #C9D1D9;
    }
    .dot-count {
        font-weight: 700;
        font-size: 1rem;
        color: #FAFAFA;
    }

    /* Section label */
    .section-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #484F58;
        font-weight: 700;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
    }

    /* Nav cards grid */
    .nav-card {
        background: linear-gradient(135deg, #161B22 0%, #1A2332 100%);
        border: 1px solid rgba(41,181,232,0.18);
        border-radius: 0.75rem;
        padding: 1.1rem 1rem 0.9rem 1rem;
        min-height: 9.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .nav-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: radial-gradient(ellipse at top left, rgba(41,181,232,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .nav-card:hover {
        border-color: #29B5E8;
        box-shadow: 0 0 20px rgba(41,181,232,0.2), 0 4px 20px rgba(0,0,0,0.3);
        transform: translateY(-3px);
    }
    .nav-card .card-icon {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 0 4px rgba(41,181,232,0.3));
    }
    .nav-card .card-title {
        font-size: clamp(0.85rem, 0.95rem, 1.1rem);
        font-weight: 700;
        color: #E6EDF3;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .nav-card .card-desc {
        font-size: clamp(0.7rem, 0.78rem, 0.88rem);
        font-weight: 400;
        color: #6E7681;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* Invisible page_link overlay on cards */
    [data-testid="stMain"] [data-testid="stPageLink-NavLink"] {
        margin-top: -10.5rem !important;
        min-height: 10.5rem !important;
        opacity: 0 !important;
        cursor: pointer !important;
        border: none !important;
        background: transparent !important;
    }

    /* Powered-by footer */
    .powered-row {
        display: flex;
        gap: 1.5rem;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        padding: 0.5rem 0;
    }
    .tech-pill {
        background: rgba(41,181,232,0.08);
        border: 1px solid rgba(41,181,232,0.15);
        color: #8B949E;
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-size: 0.72rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ── Load live data ──
session = get_session()
try:
    kpi = run_query(session, Q.KPI_OVERVIEW).iloc[0]
    risk = run_query(session, Q.HIGH_RISK_VEHICLES).iloc[0]
    buckets = run_query(session, Q.FLEET_HEALTH_BUCKETS)
    forecast = run_query(session, Q.FORECAST_SUMMARY).iloc[0]
    suppliers = run_query(session, Q.SUPPLIER_RISK_RANKING)
    data_loaded = True
except Exception:
    data_loaded = False

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">LIVE MONITORING</div>
    <h1 class="hero-title">Vehicle Quality Command Center</h1>
    <p class="hero-subtitle">AI-Powered Automotive Battery Intelligence &mdash; Real-time fleet monitoring, predictive analytics & autonomous diagnostics</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards Row ──
if data_loaded:
    total_v = int(kpi['TOTAL_VEHICLES'])
    total_f = int(kpi['TOTAL_FAILURES'])
    rate = kpi['FAILURE_RATE_PCT']
    high_risk = int(risk['HIGH_RISK_COUNT'])
    predicted = int(forecast['TOTAL_PREDICTED_FAILURES'])
    top_supplier = suppliers.iloc[0]['SUPPLIER_NAME'].split(',')[0].split(' Inc')[0]

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card blue">
            <div class="kpi-label">Fleet Size</div>
            <div class="kpi-value">{total_v:,}</div>
            <div class="kpi-sub">vehicles monitored</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-label">Total Events</div>
            <div class="kpi-value">{int(kpi['TOTAL_EVENTS']):,}</div>
            <div class="kpi-sub">quality events recorded</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label">Failure Rate</div>
            <div class="kpi-value">{rate}%</div>
            <div class="kpi-sub">{total_f:,} total failures</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">High Risk</div>
            <div class="kpi-value">{high_risk}</div>
            <div class="kpi-sub">critical + high tier</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-label">30-Day Forecast</div>
            <div class="kpi-value">{predicted:,}</div>
            <div class="kpi-sub">predicted failures</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fleet Status Indicators ──
    bucket_map = {r['STATUS']: int(r['VEHICLE_COUNT']) for _, r in buckets.iterrows()}
    healthy = bucket_map.get('LOW', 0) + bucket_map.get('MEDIUM', 0)
    warning = bucket_map.get('HIGH', 0)
    critical = bucket_map.get('CRITICAL', 0)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161B22, #1A2332); border: 1px solid rgba(41,181,232,0.12);
                border-radius: 0.75rem; padding: 1rem 1.5rem; margin-bottom: 1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
            <div class="fleet-status">
                <div class="status-dot">
                    <span class="dot green"></span>
                    <span class="dot-label">Healthy</span>
                    <span class="dot-count">{healthy:,}</span>
                </div>
                <div class="status-dot">
                    <span class="dot amber"></span>
                    <span class="dot-label">Warning</span>
                    <span class="dot-count">{warning:,}</span>
                </div>
                <div class="status-dot">
                    <span class="dot red"></span>
                    <span class="dot-label">Critical</span>
                    <span class="dot-count">{critical:,}</span>
                </div>
            </div>
            <div style="color:#6E7681; font-size:0.78rem;">
                Top risk supplier: <span style="color:#FBBF24; font-weight:600;">{top_supplier}</span>
                &nbsp;&bull;&nbsp; {len(suppliers)} suppliers tracked
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Navigation Cards ──
st.markdown('<div class="section-label">Command Modules</div>', unsafe_allow_html=True)

all_pages = [
    ("📊", "Executive Command Center", "Fleet KPIs, health scores & risk rankings", "pages/01_📊_Executive_Command_Center.py"),
    ("🔋", "Vehicle Health Monitor", "Live vehicle status with health indicators", "pages/02_🔋_Vehicle_Health_Monitor.py"),
    ("🔬", "Root Cause Investigator", "AI-powered failure analysis & defect tracing", "pages/03_🔬_Root_Cause_Investigator.py"),
    ("📈", "Failure Prediction", "ML forecasts with risk scoring models", "pages/04_📈_Failure_Prediction.py"),
    ("🤖", "AutoDoctor Copilot", "Natural language Q&A over quality data", "pages/05_🤖_AutoDoctor_Copilot.py"),
    ("💰", "Recall Simulator", "What-if analysis for recall decisions", "pages/06_💰_Recall_Simulator.py"),
    ("🏭", "Supplier Intelligence", "Supplier quality scorecards & trends", "pages/07_🏭_Supplier_Intelligence.py"),
    ("🌎", "Geo Intelligence", "Geographic failure heatmaps & clusters", "pages/08_🌎_Geo_Intelligence.py"),
    ("⚙️", "Action Center", "Early warnings & automated response rules", "pages/09_⚙️_Action_Center.py"),
    ("🎯", "Demo Mode", "One-click guided demo for judges", "pages/10_🎯_Demo_Mode.py"),
]

for row_start in range(0, len(all_pages), 5):
    cols = st.columns(5)
    for i, (icon, title, desc, path) in enumerate(all_pages[row_start:row_start + 5]):
        with cols[i]:
            st.markdown(
                f'<div class="nav-card">'
                f'<div class="card-icon">{icon}</div>'
                f'<div class="card-title">{title}</div>'
                f'<div class="card-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.page_link(path, label=title, width="stretch")
    st.markdown("")

# ── Footer ──
st.markdown("""
<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(41,181,232,0.1);">
    <div class="powered-row">
        <span class="tech-pill">Snowflake</span>
        <span class="tech-pill">Cortex AI</span>
        <span class="tech-pill">Snowpark</span>
        <span class="tech-pill">Streamlit</span>
        <span class="tech-pill">Snowflake ML</span>
    </div>
    <p style="text-align:center; color:#484F58; font-size:0.72rem; margin-top:0.5rem;">
        Snowflake x Capgemini Hackathon 2026
    </p>
</div>
""", unsafe_allow_html=True)
