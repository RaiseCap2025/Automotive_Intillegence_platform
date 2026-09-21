import streamlit as st
import json


@st.cache_data(ttl=600, show_spinner=False)
def generate_insight(_session, page_name: str, data_context: str) -> str:
    prompt = data_context.replace("'", "''")
    query = f"""SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b',
        [
            {{'role': 'system', 'content': 'You are a senior automotive quality analyst. Given dashboard metrics, write ONE concise business insight (2-3 sentences max). Be data-driven, actionable, and specific. Do not use markdown formatting or bullet points.'}},
            {{'role': 'user', 'content': '{prompt}'}}
        ], {{}}) AS response"""
    result = _session.sql(query).collect()
    try:
        resp = json.loads(result[0]["RESPONSE"])
        return resp.get("choices", [{}])[0].get("messages", str(resp))
    except (json.JSONDecodeError, KeyError, IndexError):
        return str(result[0]["RESPONSE"])
