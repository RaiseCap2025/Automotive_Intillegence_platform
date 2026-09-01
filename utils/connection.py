import streamlit as st
from snowflake.snowpark import Session


def get_session() -> Session:
    """Get Snowflake session - works both locally and in Streamlit-in-Snowflake."""
    if "snowpark_session" not in st.session_state:
        try:
            from snowflake.snowpark.context import get_active_session
            session = get_active_session()
        except Exception:
            sf_config = st.secrets["connections"]["snowflake"]
            connection_params = {
                "account": sf_config["account"],
                "user": sf_config["user"],
                "password": sf_config["password"],
                "database": sf_config.get("database", "VEHICLE_QUALITY_DB"),
                "schema": sf_config.get("schema", "PUBLIC"),
                "warehouse": sf_config.get("warehouse", "COMPUTE_WH"),
            }
            session = Session.builder.configs(connection_params).create()
        st.session_state.snowpark_session = session
    return st.session_state.snowpark_session


@st.cache_data(ttl=600)
def run_query(_session, query: str):
    """Execute a query and return results as a pandas DataFrame. Cached for 10 min."""
    return _session.sql(query).to_pandas()
