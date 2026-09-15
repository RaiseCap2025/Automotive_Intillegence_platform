
import streamlit as st
import sys, os
import json
import threading
import time

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


def ask_agent(question: str, session) -> str:
    """Call the VEHICLE_QUALITY_ORCHESTRATOR Cortex Agent via SQL."""
    escaped_q = question.replace("\\", "\\\\").replace("'", "\\'")
    messages_json = json.dumps({
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": question}]}
        ]
    })
    escaped_json = messages_json.replace("'", "''")
    query = f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('VEHICLE_QUALITY_DB.PUBLIC.VEHICLE_QUALITY_ORCHESTRATOR', '{escaped_json}') AS response"

    cursor = session.connection.cursor()
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        raw = str(row[0])
    finally:
        cursor.close()

    try:
        resp = json.loads(raw)
        parts = []

        def extract_content(items):
            for item in items:
                t = item.get("type", "")
                if t == "text":
                    parts.append(item.get("text", ""))
                elif t == "tool_results":
                    tr = item.get("tool_results", {})
                    tool_name = tr.get("name", "")
                    if tool_name:
                        parts.append(f"\n---\n**Tool: {tool_name}**")
                    inner = tr.get("content", [])
                    if isinstance(inner, list):
                        extract_content(inner)
                    elif isinstance(inner, str):
                        parts.append(inner)
                elif t == "tool_use":
                    tool_name = item.get("name", "tool")
                    tool_input = item.get("input", {})
                    if isinstance(tool_input, dict) and "query" in tool_input:
                        parts.append(f"\n**Query ({tool_name}):**")
                        parts.append(f"```sql\n{tool_input['query']}\n```")
                elif t == "json":
                    j = item.get("json", {})
                    if isinstance(j, dict) and "sql" in j:
                        parts.append(f"```sql\n{j['sql']}\n```")
                    else:
                        parts.append(f"```json\n{json.dumps(j, indent=2)}\n```")
                elif t == "data":
                    d = item.get("data", item)
                    parts.append(f"```json\n{json.dumps(d, indent=2)}\n```")

        extract_content(resp.get("content", []))
        return "\n\n".join(parts) if parts else raw
    except (json.JSONDecodeError, KeyError):
        return raw


CAR_LOADER_HTML = """
<style>
@keyframes drive {{
    0%   {{ left: 0%; }}
    100% {{ left: {pct}%; }}
}}
@keyframes wheelSpin {{
    0%   {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}
@keyframes smoke {{
    0%   {{ opacity: 0.6; transform: translate(0, 0) scale(1); }}
    100% {{ opacity: 0; transform: translate(-30px, -10px) scale(2); }}
}}
.car-road {{
    position: relative;
    height: 90px;
    background: linear-gradient(to bottom, #1a1a2e 0%, #1a1a2e 55%, #333 55%, #333 60%, #555 60%, #555 100%);
    border-radius: 8px;
    overflow: hidden;
    margin: 10px 0;
}}
.road-line {{
    position: absolute;
    top: 57%;
    width: 100%;
    height: 2px;
    background: repeating-linear-gradient(to right, #ffcc00 0px, #ffcc00 20px, transparent 20px, transparent 40px);
}}
.car-container {{
    position: absolute;
    bottom: 12px;
    animation: drive {duration}s ease-out forwards;
}}
.car-body {{
    position: relative;
    width: 70px;
    height: 24px;
    background: linear-gradient(135deg, #e74c3c, #c0392b);
    border-radius: 8px 12px 3px 3px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
}}
.car-body::before {{
    content: '';
    position: absolute;
    top: -12px; left: 14px;
    width: 36px; height: 14px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    border-radius: 6px 6px 0 0;
    border: 1px solid rgba(255,255,255,0.2);
}}
.car-body::after {{
    content: '';
    position: absolute;
    top: 2px; right: 0px;
    width: 6px; height: 6px;
    background: #f1c40f;
    border-radius: 50%;
    box-shadow: 0 0 6px #f1c40f;
}}
.wheel {{
    position: absolute;
    bottom: -5px;
    width: 12px; height: 12px;
    background: #222;
    border: 2px solid #888;
    border-radius: 50%;
    animation: wheelSpin 0.4s linear infinite;
}}
.wheel.front {{ right: 6px; }}
.wheel.rear  {{ left: 8px; }}
.exhaust {{
    position: absolute;
    bottom: 2px; left: -8px;
    width: 6px; height: 6px;
    background: rgba(200,200,200,0.5);
    border-radius: 50%;
    animation: smoke 0.8s ease-out infinite;
}}
.status-bar {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0;
}}
.progress-track {{
    flex: 1;
    height: 6px;
    background: #333;
    border-radius: 3px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    width: {pct}%;
    background: linear-gradient(90deg, #e74c3c, #f39c12);
    border-radius: 3px;
    transition: width 0.5s ease;
}}
.status-text {{
    color: #aaa;
    font-size: 13px;
    min-width: 200px;
}}
</style>
<div class="car-road">
    <div class="road-line"></div>
    <div class="car-container">
        <div class="car-body">
            <div class="wheel front"></div>
            <div class="wheel rear"></div>
            <div class="exhaust"></div>
        </div>
    </div>
</div>
<div class="status-bar">
    <div class="progress-track"><div class="progress-fill"></div></div>
    <div class="status-text">{status}</div>
</div>
"""

STAGES = [
    (5,  0.5, "Starting engine..."),
    (15, 1.5, "Connecting to agent..."),
    (30, 3.0, "Querying data sources..."),
    (50, 5.0, "Analyzing patterns..."),
    (65, 8.0, "Running diagnostics..."),
    (80, 12.0, "Generating insights..."),
    (90, 20.0, "Finalizing response..."),
]


def run_agent_threaded(question, session, result_holder):
    """Run agent call in a thread, storing result in the dict."""
    try:
        result_holder["response"] = ask_agent(question, session)
    except Exception as e:
        result_holder["error"] = str(e)


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
        loader = st.empty()
        result_holder = {}

        agent_thread = threading.Thread(
            target=run_agent_threaded,
            args=(prompt, session, result_holder),
        )
        agent_thread.start()

        start_time = time.time()
        stage_idx = 0
        while agent_thread.is_alive():
            elapsed = time.time() - start_time
            while stage_idx < len(STAGES) - 1 and elapsed >= STAGES[stage_idx + 1][1]:
                stage_idx += 1
            pct, _, status = STAGES[stage_idx]
            duration = max(0.5, STAGES[min(stage_idx + 1, len(STAGES) - 1)][1] - elapsed)
            loader.markdown(
                CAR_LOADER_HTML.format(pct=pct, status=status, duration=duration),
                unsafe_allow_html=True,
            )
            time.sleep(0.5)

        agent_thread.join()
        loader.markdown(
            CAR_LOADER_HTML.format(pct=100, status="Done!", duration=0.3),
            unsafe_allow_html=True,
        )
        time.sleep(0.6)
        loader.empty()

        if "error" in result_holder:
            response = f"Error: {result_holder['error']}"
        else:
            response = result_holder.get("response", "No response from agent.")

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
