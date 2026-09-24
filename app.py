import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav, page_header
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

# -- Futuristic Homepage CSS --
st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(135deg, #1E2535 0%, #232D40 40%, #1c2844 100%);
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
    .kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .kpi-card {
        flex: 1; min-width: 140px;
        background: linear-gradient(135deg, #232A3B 0%, #2A3347 100%);
        border: 1px solid rgba(41,181,232,0.2);
        border-radius: 0.75rem;
        padding: 1rem 1.2rem;
        position: relative; overflow: hidden;
    }
    .kpi-card::after {
        content: ''; position: absolute;
        top: 0; left: 0; width: 100%; height: 3px;
        border-radius: 0.75rem 0.75rem 0 0;
    }
    .kpi-card.blue::after { background: linear-gradient(90deg, #29B5E8, #38BDF8); }
    .kpi-card.green::after { background: linear-gradient(90deg, #34D399, #6EE7B7); }
    .kpi-card.amber::after { background: linear-gradient(90deg, #FBBF24, #FB923C); }
    .kpi-card.red::after { background: linear-gradient(90deg, #F87171, #EF4444); }
    .kpi-card.purple::after { background: linear-gradient(90deg, #818CF8, #A78BFA); }
    .kpi-card.cyan::after { background: linear-gradient(90deg, #22D3EE, #06B6D4); }
    .kpi-label {
        font-size: 0.72rem; color: #8B949E;
        text-transform: uppercase; letter-spacing: 0.8px;
        margin-bottom: 0.3rem; font-weight: 600;
    }
    .kpi-value { font-size: clamp(1.4rem, 1.8rem, 2.2rem); font-weight: 800; color: #FAFAFA; line-height: 1.1; }
    .kpi-sub { font-size: 0.75rem; color: #6E7681; margin-top: 0.2rem; }
    .fleet-status { display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap; }
    .status-dot { display: flex; align-items: center; gap: 0.5rem; }
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .dot.green { background: #34D399; box-shadow: 0 0 8px rgba(52,211,153,0.5); }
    .dot.amber { background: #FBBF24; box-shadow: 0 0 8px rgba(251,191,36,0.5); }
    .dot.red { background: #F87171; box-shadow: 0 0 8px rgba(248,113,113,0.5); animation: pulse-dot 2s infinite; }
    @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .dot-label { font-size: 0.82rem; color: #C9D1D9; }
    .dot-count { font-weight: 700; font-size: 1rem; color: #FAFAFA; }
    .section-label {
        font-size: 0.7rem; text-transform: uppercase;
        letter-spacing: 1.5px; color: #484F58;
        font-weight: 700; margin-bottom: 0.75rem; margin-top: 0.5rem;
    }
    .insight-box {
        background: linear-gradient(135deg, #1E2B3D 0%, #253248 100%);
        border: 1px solid rgba(41,181,232,0.25);
        border-left: 4px solid #29B5E8;
        border-radius: 0.75rem;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0;
    }
    .insight-box .insight-title {
        font-size: 0.72rem; text-transform: uppercase;
        letter-spacing: 1px; color: #29B5E8;
        font-weight: 700; margin-bottom: 0.5rem;
    }
    .insight-box .insight-text {
        font-size: 0.9rem; color: #C9D1D9; line-height: 1.6;
    }
    .nav-card {
        background: linear-gradient(135deg, #232A3B 0%, #2A3347 100%);
        border: 1px solid rgba(41,181,232,0.18);
        border-radius: 0.75rem;
        padding: 1.1rem 1rem 0.9rem 1rem;
        min-height: 9.5rem;
        transition: all 0.3s ease;
        position: relative; overflow: hidden;
    }
    .nav-card::before {
        content: ''; position: absolute; top: 0; left: 0;
        width: 100%; height: 100%;
        background: radial-gradient(ellipse at top left, rgba(41,181,232,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .nav-card:hover {
        border-color: #29B5E8;
        box-shadow: 0 0 20px rgba(41,181,232,0.2), 0 4px 20px rgba(0,0,0,0.3);
        transform: translateY(-3px);
    }
    .nav-card .card-icon { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .nav-card .card-title {
        font-size: clamp(0.85rem, 0.95rem, 1.1rem);
        font-weight: 700; color: #E6EDF3;
        margin-bottom: 0.3rem;
    }
    .nav-card .card-desc {
        font-size: clamp(0.7rem, 0.78rem, 0.88rem);
        font-weight: 400; color: #6E7681; line-height: 1.4;
    }
    [data-testid="stMain"] [data-testid="stPageLink-NavLink"] {
        margin-top: -10.5rem !important;
        min-height: 10.5rem !important;
        opacity: 0 !important;
        cursor: pointer !important;
        border: none !important;
        background: transparent !important;
    }
    .powered-row {
        display: flex; gap: 1.5rem; align-items: center;
        justify-content: center; flex-wrap: wrap; padding: 0.5rem 0;
    }
    .tech-pill {
        background: rgba(41,181,232,0.08);
        border: 1px solid rgba(41,181,232,0.15);
        color: #8B949E; padding: 0.3rem 0.8rem;
        border-radius: 2rem; font-size: 0.72rem; font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# -- Load live data --
session = get_session()
try:
    kpi = run_query(session, Q.KPI_OVERVIEW).iloc[0]
    risk = run_query(session, Q.HIGH_RISK_VEHICLES).iloc[0]
    buckets = run_query(session, Q.FLEET_HEALTH_BUCKETS)
    forecast = run_query(session, Q.FORECAST_SUMMARY).iloc[0]
    suppliers = run_query(session, Q.SUPPLIER_RISK_RANKING)
    quality_score = run_query(session, Q.QUALITY_SCORE_OVERALL).iloc[0]
    warranty = run_query(session, Q.WARRANTY_COST_ESTIMATE).iloc[0]
    insights = run_query(session, Q.EXECUTIVE_INSIGHTS).iloc[0]
    trend = run_query(session, Q.WEEKLY_FAILURE_TREND)
    errors = run_query(session, Q.ERROR_CODE_DISTRIBUTION)
    data_loaded = True
except Exception:
    data_loaded = False

# -- Hero Banner --
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">EXECUTIVE SUMMARY</div>
    <h1 class="hero-title">Automotive Intelligence Platform</h1>
    <p class="hero-subtitle">Real-Time Vehicle Quality Analytics &mdash; Powered by Snowflake Cortex AI</p>
</div>
""", unsafe_allow_html=True)

# -- KPI Cards Row --
if data_loaded:
    total_v = int(kpi['TOTAL_VEHICLES'])
    total_f = int(kpi['TOTAL_FAILURES'])
    rate = kpi['FAILURE_RATE_PCT']
    high_risk = int(risk['HIGH_RISK_COUNT'])
    predicted = int(forecast['TOTAL_PREDICTED_FAILURES'])
    q_score = float(quality_score['QUALITY_SCORE'])
    cost_exposure = int(warranty['WARRANTY_COST_EXPOSURE'])
    worst_supplier = str(insights['WORST_SUPPLIER']).split(',')[0].split(' Inc')[0]
    top_cause = str(insights['TOP_ROOT_CAUSE'])

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card cyan">
            <div class="kpi-label">Quality Score</div>
            <div class="kpi-value">{q_score}%</div>
            <div class="kpi-sub">fleet-wide</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">Open Critical Issues</div>
            <div class="kpi-value">{high_risk}</div>
            <div class="kpi-sub">critical + high risk</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-label">Predicted Failures (30d)</div>
            <div class="kpi-value">{predicted:,}</div>
            <div class="kpi-sub">next 30 days</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label">Warranty Cost Exposure</div>
            <div class="kpi-value">${cost_exposure:,}</div>
            <div class="kpi-sub">estimated at $1,500/failure</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">Top Root Cause</div>
            <div class="kpi-value" style="font-size:1rem">{top_cause}</div>
            <div class="kpi-sub">most common defect type</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-label">Worst Supplier</div>
            <div class="kpi-value" style="font-size:1rem">{worst_supplier}</div>
            <div class="kpi-sub">{float(insights['WORST_SUPPLIER_RATE']):.1f}% failure rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Fleet Status
    bucket_map = {r['STATUS']: int(r['VEHICLE_COUNT']) for _, r in buckets.iterrows()}
    healthy = bucket_map.get('LOW', 0) + bucket_map.get('MEDIUM', 0)
    warning = bucket_map.get('HIGH', 0)
    critical = bucket_map.get('CRITICAL', 0)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #232A3B, #2A3347); border: 1px solid rgba(41,181,232,0.12);
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
                {total_v:,} vehicles monitored &bull; {len(suppliers)} suppliers tracked
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Executive Insight Box
    worst_rate = float(insights['WORST_SUPPLIER_RATE'])
    worst_failures = int(insights['WORST_SUPPLIER_FAILURES'])
    savings = int(warranty['POTENTIAL_SAVINGS'])
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">Executive Insight</div>
        <div class="insight-text">
            <strong>{worst_supplier}</strong> battery components are driving the highest failure rate at
            <strong>{worst_rate:.1f}%</strong> ({worst_failures:,} failures).
            Addressing this supplier's quality issues could reduce projected warranty costs by up to
            <strong>${savings:,}</strong> over the next 30 days.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-label">Weekly Failure Trend</div>', unsafe_allow_html=True)
        fig_trend = px.line(trend, x="WEEK_START", y="FAILURES")
        fig_trend.update_traces(line=dict(color=COLORS["primary"], width=2), fill="tozeroy",
                                fillcolor="rgba(41,181,232,0.1)")
        fig_trend.update_layout(**PLOTLY_LAYOUT, xaxis_title="", yaxis_title="Failures", height=300)
        st.plotly_chart(fig_trend, width="stretch")

    with c2:
        st.markdown('<div class="section-label">Supplier Risk Ranking</div>', unsafe_allow_html=True)
        fig_sup = px.bar(suppliers, x="FAILURE_RATE_PCT", y="SUPPLIER_NAME",
                         orientation="h", color="FAILURE_RATE_PCT",
                         color_continuous_scale=["#34D399", "#FBBF24", "#F87171"])
        fig_sup.update_layout(**PLOTLY_LAYOUT, yaxis_title="", xaxis_title="Failure Rate %", height=300,
                              coloraxis_showscale=False)
        st.plotly_chart(fig_sup, width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="section-label">Top Error Codes</div>', unsafe_allow_html=True)
        fig_err = px.bar(errors.head(6), x="EVENT_COUNT", y="ERROR_DESCRIPTION",
                         orientation="h")
        fig_err.update_traces(marker_color=COLORS["primary"])
        fig_err.update_layout(**PLOTLY_LAYOUT, yaxis_title="", xaxis_title="Occurrences", height=280)
        st.plotly_chart(fig_err, width="stretch")

    with c4:
        st.markdown('<div class="section-label">Fleet Health Distribution</div>', unsafe_allow_html=True)
        colors_map = {"LOW": "#34D399", "MEDIUM": "#FBBF24", "HIGH": "#FB923C", "CRITICAL": "#F87171"}
        fig_health = go.Figure(data=[go.Pie(
            labels=buckets["STATUS"], values=buckets["VEHICLE_COUNT"],
            hole=0.5, marker=dict(colors=[colors_map.get(s, "#888") for s in buckets["STATUS"]])
        )])
        fig_health.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=True,
                                 legend=dict(font=dict(size=11)))
        st.plotly_chart(fig_health, width="stretch")

# -- Navigation Cards --
st.markdown('<div class="section-label">Dashboard Modules</div>', unsafe_allow_html=True)

all_pages = [
    ("01_Vehicle_Quality_Health", "Vehicle Quality Health", "Fleet-wide quality status, defect trends & DTC analysis"),
    ("02_Root_Cause_Analysis", "Root Cause Analysis", "Defect-to-component mapping & supplier correlation"),
    ("03_Manufacturing_Quality", "Manufacturing Quality", "Production metrics, yield rates & control charts"),
    ("04_Supplier_Quality", "Supplier Quality", "PPM scores, certifications & failure heatmaps"),
    ("05_Predictive_Maintenance", "Predictive Maintenance", "30-day forecasts, RUL & warranty cost projections"),
    ("06_Anomaly_Detection", "Anomaly Detection", "Real-time alerts, sensor deviations & corrective actions"),
    ("07_AutoDoctor_Copilot", "AutoDoctor Copilot", "Natural language Q&A powered by Cortex Agent"),
]

icons = ["🏥", "🔬", "🏭", "📦", "📈", "🚨", "🤖"]

cols = st.columns(4)
for i, (filename, title, desc) in enumerate(all_pages):
    with cols[i % 4]:
        st.markdown(
            f'<div class="nav-card">'
            f'<div class="card-icon">{icons[i]}</div>'
            f'<div class="card-title">{title}</div>'
            f'<div class="card-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link(f"pages/{filename}.py", label=title, width="stretch")
    if (i + 1) % 4 == 0 and i + 1 < len(all_pages):
        cols = st.columns(4)

# -- Footer --
st.markdown("""
<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(41,181,232,0.1);">
    <div class="powered-row">
        <span class="tech-pill">Snowflake Cortex AI</span>
        <span class="tech-pill">Cortex Agents</span>
        <span class="tech-pill">Snowpark ML</span>
        <span class="tech-pill">Streamlit</span>
    </div>
    <p style="text-align:center; color:#484F58; font-size:0.72rem; margin-top:0.5rem;">
        Snowflake x Capgemini Hackathon 2026 &mdash; Automotive Intelligence Platform
    </p>
</div>
""", unsafe_allow_html=True)
