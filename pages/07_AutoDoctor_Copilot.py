import streamlit as st
import json
import threading
import time
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, COLORS, render_sidebar_nav, page_header
from utils.connection import get_session

st.set_page_config(**{**PAGE_CONFIG, "page_title": "AutoDoctor Copilot", "page_icon": "🤖"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()

# ── Futuristic Page CSS ──
st.markdown("""
<style>
/* ── Header ── */
.copilot-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
}
.copilot-header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #29B5E8 0%, #7B61FF 50%, #00F5D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.2;
}
.copilot-header .subtitle {
    color: rgba(180,195,220,0.7);
    font-size: 0.85rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}
.copilot-header .divider {
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #29B5E8, transparent);
    margin: 0.8rem auto 0;
}

/* ── Suggestion Cards ── */
.sug-grid { display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center; margin: 1rem 0 1.5rem; }
.sug-grid .stButton > button {
    background: rgba(41,181,232,0.06) !important;
    border: 1px solid rgba(41,181,232,0.25) !important;
    border-radius: 10px !important;
    color: #c8dce8 !important;
    font-size: 0.82rem !important;
    padding: 0.55rem 1.1rem !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(6px);
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 2.8rem !important;
}
.sug-grid .stButton > button:hover {
    background: rgba(41,181,232,0.15) !important;
    border-color: rgba(41,181,232,0.6) !important;
    box-shadow: 0 0 18px rgba(41,181,232,0.15), inset 0 0 12px rgba(41,181,232,0.05) !important;
    color: #fff !important;
    transform: translateY(-1px);
}
.sug-label {
    text-align: center;
    color: rgba(41,181,232,0.5);
    font-size: 0.72rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    border-radius: 12px !important;
    border: 1px solid rgba(41,181,232,0.08) !important;
    background: rgba(15,20,35,0.5) !important;
    backdrop-filter: blur(8px);
    margin-bottom: 0.8rem !important;
    padding: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-color: rgba(123,97,255,0.15) !important;
    background: rgba(123,97,255,0.04) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-color: rgba(41,181,232,0.12) !important;
    background: rgba(41,181,232,0.03) !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] {
    border-radius: 14px !important;
}
[data-testid="stChatInput"] textarea {
    border-radius: 14px !important;
    border: 1px solid rgba(41,181,232,0.2) !important;
    background: rgba(10,15,30,0.6) !important;
    color: #e0e8f0 !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: rgba(41,181,232,0.5) !important;
    box-shadow: 0 0 20px rgba(41,181,232,0.1) !important;
}

/* ── Glow line under header ── */
@keyframes scanline {
    0%   { left: -30%; }
    100% { left: 130%; }
}
.scan-line {
    position: relative;
    height: 1px;
    background: rgba(41,181,232,0.1);
    overflow: hidden;
    margin: 0.5rem 0 1rem;
}
.scan-line::after {
    content: '';
    position: absolute;
    top: 0; left: -30%;
    width: 30%; height: 100%;
    background: linear-gradient(90deg, transparent, #29B5E8, transparent);
    animation: scanline 3s ease-in-out infinite;
}
</style>

<div class="copilot-header">
    <h1>AutoDoctor Copilot</h1>
    <div class="subtitle">Powered by Snowflake Cortex Agent</div>
    <div class="divider"></div>
</div>
<div class="scan-line"></div>
""", unsafe_allow_html=True)

session = get_session()

# ── Sidebar LLM info ──
with st.sidebar:
    st.markdown(
        '<div style="margin-top:1.5rem;padding:0.8rem;background:rgba(41,181,232,0.04);'
        'border:1px solid rgba(41,181,232,0.12);border-radius:0.6rem;">'
        '<div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;'
        'color:#484F58;font-weight:700;margin-bottom:0.4rem;">LLM Engine</div>'
        '<div style="font-size:0.82rem;color:#C9D1D9;font-weight:600;">Cortex Agent</div>'
        '<div style="font-size:0.72rem;color:#6E7681;">VEHICLE_QUALITY_ORCHESTRATOR</div>'
        '<div style="font-size:0.62rem;color:#484F58;margin-top:0.3rem;">'
        'Snowflake Cortex · Data Agent Run</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def ask_agent(question: str, session) -> str:
    messages_json = json.dumps({
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": question}]}
        ]
    })
    escaped_json = messages_json.replace("'", "''")
    query = f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('VEHICLE_QUALITY_DB.PUBLIC.VEHICLE_QUALITY_ORCHESTRATOR', '{escaped_json}')::VARCHAR AS response"

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
    background: linear-gradient(90deg, #29B5E8, #1a8fc4);
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
    (15, 1.5, "Connecting to orchestrator agent..."),
    (30, 3.0, "Querying vehicle quality data..."),
    (50, 5.0, "Analyzing failure patterns..."),
    (65, 8.0, "Running diagnostics..."),
    (80, 12.0, "Generating insights..."),
    (90, 20.0, "Finalizing response..."),
]


def run_agent_threaded(question, session, result_holder):
    try:
        result_holder["response"] = ask_agent(question, session)
    except Exception as e:
        result_holder["error"] = str(e)


# ── Chat Interface ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Action bar (Attach / Chat History)
ab1, ab2, ab_spacer = st.columns([1, 1, 4])
with ab1:
    st.button("📎 Attach Document", disabled=True, help="Document upload coming soon")
with ab2:
    if st.button("📜 View Chat History"):
        if st.session_state.messages:
            with st.expander("Chat History", expanded=True):
                for m in st.session_state.messages:
                    role_lbl = "You" if m["role"] == "user" else "AutoDoctor"
                    st.markdown(f"**{role_lbl}:** {m['content'][:200]}{'...' if len(m['content']) > 200 else ''}")
        else:
            st.info("No chat history yet.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Suggested questions
if not st.session_state.messages and st.session_state.pending_prompt is None:
    suggestions = [
        "Give me a full quality report",
        "A customer reported battery failure in cold weather - investigate",
        "Which suppliers need immediate attention based on trends and risk?",
        "What is our biggest quality risk in the next 30 days?",
        "Show me the top 5 highest-risk vehicles and explain why they rank high",
        "Are there any early warning alerts I should act on today?",
    ]
    st.markdown('<div class="sug-label">Suggested Queries</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sug-grid">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            if cols[i % 3].button(s, key=f"sug_{i}"):
                st.session_state.pending_prompt = s
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Determine the prompt: from chat input or from a pending suggestion click
prompt = st.chat_input("Ask AutoDoctor about vehicle quality...")
if prompt is None and st.session_state.pending_prompt is not None:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
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
            response = f"**Error:** {result_holder['error']}"
        else:
            response = result_holder.get("response", "No response from agent.")

            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
