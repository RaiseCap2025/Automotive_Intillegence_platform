import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.connection import get_session, run_query

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AI Quality Assistant")
st.markdown(
    "Ask questions about vehicle battery quality in natural language. "
    "Powered by **Snowflake Cortex AI**."
)

session = get_session()


def build_data_context(session):
    """Fetch live summary stats to inject into the LLM prompt."""
    summary = run_query(session, """
        SELECT
            COUNT(DISTINCT CAR_ID) AS total_vehicles,
            SUM(HAS_ERROR) AS total_failures,
            ROUND(SUM(HAS_ERROR)::FLOAT / COUNT(*) * 100, 2) AS failure_rate,
            COUNT(DISTINCT SUPPLIER_NAME) AS num_suppliers,
            COUNT(DISTINCT BATTERY_TYPE_NAME) AS num_battery_types
        FROM VEHICLE_QUALITY_DB.PUBLIC.FACT_QUALITY_EVENTS
    """)

    top_supplier = run_query(session, """
        SELECT SUPPLIER_NAME,
               ROUND(SUM(FAILURE_COUNT)::FLOAT / NULLIF(SUM(TOTAL_EVENTS),0) * 100, 2) AS rate
        FROM VEHICLE_QUALITY_DB.PUBLIC.AGG_FAILURE_RATES
        GROUP BY SUPPLIER_NAME ORDER BY rate DESC LIMIT 1
    """)

    top_error = run_query(session, """
        SELECT d.DESCRIPTION, COUNT(*) AS cnt
        FROM VEHICLE_QUALITY_DB.PUBLIC.FACT_QUALITY_EVENTS e
        JOIN VEHICLE_QUALITY_DB.PUBLIC.DTC_BATTERY_ERROR_CODES d ON e.DTC_ERROR_CODE = d.ERROR_ID
        WHERE e.HAS_ERROR = 1
        GROUP BY d.DESCRIPTION ORDER BY cnt DESC LIMIT 3
    """)

    s = summary.iloc[0]
    ctx = f"""LIVE DATA CONTEXT:
- Fleet: {int(s['TOTAL_VEHICLES']):,} vehicles monitored
- Total failures: {int(s['TOTAL_FAILURES']):,} ({s['FAILURE_RATE']}% failure rate)
- Suppliers: ABCD Technologies, 800-Battery Technologies, ACME Battery Energy, 123 Battery Manufacturers, EVR Battery
- Battery types: Lead Acid/Lead, Nickel-Metal-Hydride/NiMH, Lithium-Ion/Li-Ion, Cobalt Dioxide/Cobalt, LFP/Lithium Iron Phosphate
- Error codes: P1794 (Circuit Malfunction), B1317 (Voltage High), B1318 (Voltage Low), B1671 (Module Voltage OOR), B1676 (Pack Voltage OOR), C2100 (Voltage Below Threshold)
- Highest failure rate supplier: {top_supplier.iloc[0]['SUPPLIER_NAME']} at {top_supplier.iloc[0]['RATE']}%
- Top error types: {', '.join(top_error['DESCRIPTION'].tolist())}
- Data spans weekly aggregates from Jan 2022 onward
- Weather factors tracked: temperature, wind speed, precipitation, snowfall
- Geographic coverage: vehicles across all 50 US states"""
    return ctx


def ask_cortex(question: str, context: str, session) -> str:
    """Call Snowflake Cortex COMPLETE to answer user question."""
    system_prompt = (
        "You are an automotive battery quality analyst AI. "
        "Answer questions based on the provided data context. "
        "Be concise, data-driven, and provide actionable insights. "
        "If you cannot determine the answer from the context, say so clearly."
    )
    escaped_q = question.replace("'", "''")
    escaped_ctx = context.replace("'", "''")
    escaped_sys = system_prompt.replace("'", "''")

    query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        [
            {{'role': 'system', 'content': '{escaped_sys}'}},
            {{'role': 'user', 'content': '{escaped_ctx}\\n\\nQuestion: {escaped_q}'}}
        ],
        {{}}
    ) AS response
    """
    result = session.sql(query).collect()
    import json
    try:
        resp = json.loads(result[0]["RESPONSE"])
        return resp.get("choices", [{}])[0].get("messages", resp.get("messages", ""))
    except (json.JSONDecodeError, KeyError, IndexError):
        return str(result[0]["RESPONSE"])


# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Suggested questions
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    suggestions = [
        "Which supplier has the highest failure rate and why?",
        "What are the most common battery error codes?",
        "How does temperature affect battery failures?",
        "Which battery type is most reliable?",
        "Summarize the fleet quality status.",
    ]
    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        if cols[i].button(s, key=f"sug_{i}"):
            st.session_state.messages.append({"role": "user", "content": s})
            st.rerun()

# Chat input
if prompt := st.chat_input("Ask about vehicle battery quality..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing with Cortex AI..."):
            context = build_data_context(session)
            response = ask_cortex(prompt, context, session)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
