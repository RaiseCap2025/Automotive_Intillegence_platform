import streamlit as st
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "AutoDoctor Copilot", "page_icon": "🤖"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🤖 AutoDoctor Copilot")
st.caption("Ask questions about vehicle quality in natural language — Powered by Snowflake Cortex AI")

session = get_session()


def build_context(session):
    summary = run_query(session, Q.COPILOT_SUMMARY).iloc[0]
    suppliers = run_query(session, Q.TOP_SUPPLIER_FAILURES)
    errors = run_query(session, Q.TOP_ERRORS)
    risk = run_query(session, Q.HIGH_RISK_VEHICLES).iloc[0]

    sup_lines = "\n".join([
        f"  - {r['SUPPLIER_NAME']}: {r['RATE']}% failure rate, reliability={r['RELIABILITY_SCORE']}, status={r['SUPPLIER_STATUS']}"
        for _, r in suppliers.iterrows()
    ])
    err_lines = ", ".join([f"{r['DESCRIPTION']} ({r['CNT']})" for _, r in errors.iterrows()])

    return f"""VEHICLE QUALITY DATA CONTEXT (live from Snowflake):
- Fleet size: {int(summary['TOTAL_VEHICLES']):,} vehicles monitored
- Total failures: {int(summary['TOTAL_FAILURES']):,} events ({summary['FAILURE_RATE']}% failure rate)
- High/Critical risk vehicles: {int(risk['HIGH_RISK_COUNT']):,}
- Supplier Performance:
{sup_lines}
- Top error types: {err_lines}
- Error codes: P1794 (Circuit Malfunction), B1317 (Voltage High), B1318 (Voltage Low), B1671 (Module Voltage OOR), B1676 (Pack Voltage OOR), C2100 (Voltage Below Threshold)
- Battery types: Lead Acid, NiMH, Li-Ion, Cobalt Dioxide, NCM
- Geographic coverage: All 50 US states
- Data period: Jan-Feb 2022 with 30-day forecasts into March 2022
- Weather factors tracked: temperature, wind, precipitation, snowfall
- Key finding: 123 Battery Manufacturers (Cobalt) and ACME Battery Energy (Li-Ion) are the only suppliers with failures"""


def ask_cortex(question, context, session):
    system = "You are AutoDoctor, an AI automotive battery quality analyst. Provide concise, data-driven answers. Include specific numbers. When relevant, mention affected vehicle counts and estimated financial impact (use $4,000 per failure as baseline)."
    escaped_q = question.replace("'", "''")
    escaped_ctx = context.replace("'", "''")
    escaped_sys = system.replace("'", "''")

    query = f"""SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b',
        [
            {{'role': 'system', 'content': '{escaped_sys}'}},
            {{'role': 'user', 'content': '{escaped_ctx}\n\nQuestion: {escaped_q}'}}
        ], {{}}) AS response"""

    result = session.sql(query).collect()
    try:
        resp = json.loads(result[0]["RESPONSE"])
        return resp.get("choices", [{}])[0].get("messages", str(resp))
    except (json.JSONDecodeError, KeyError, IndexError):
        return str(result[0]["RESPONSE"])


# ── Chat Interface ──
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Suggested questions
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    suggestions = [
        "Why did battery failures increase?",
        "Which supplier has the most defects and why?",
        "What vehicles should be recalled?",
        "What is the projected impact next month?",
        "How does temperature affect battery failures?",
        "Compare supplier reliability scores",
    ]
    cols = st.columns(3)
    for i, s in enumerate(suggestions):
        if cols[i % 3].button(s, key=f"sug_{i}"):
            st.session_state.messages.append({"role": "user", "content": s})
            st.rerun()

if prompt := st.chat_input("Ask AutoDoctor about vehicle quality..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing with Cortex AI..."):
            context = build_context(session)
            response = ask_cortex(prompt, context, session)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
