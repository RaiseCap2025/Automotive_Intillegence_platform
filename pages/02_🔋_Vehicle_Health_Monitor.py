import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styling import PAGE_CONFIG, CUSTOM_CSS, PLOTLY_LAYOUT, COLORS, render_sidebar_nav
from utils.connection import get_session, run_query
from utils import queries as Q

st.set_page_config(**{**PAGE_CONFIG, "page_title": "Vehicle Health Monitor", "page_icon": "🔋"})
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_sidebar_nav()
st.title("🔋 Live Vehicle Health Monitor")
st.caption("Real-time vehicle status with health indicators")

session = get_session()

# ── Load data ──
df = run_query(session, Q.VEHICLE_RISK_LIST)

# ── Sidebar Filters ──
with st.sidebar:
    st.markdown("### Filters")
    tier_filter = st.multiselect("Risk Tier", df["RISK_TIER"].unique().tolist(),
                                 default=df["RISK_TIER"].unique().tolist())
    supplier_filter = st.multiselect("Supplier", df["SUPPLIER_NAME"].unique().tolist(),
                                     default=df["SUPPLIER_NAME"].unique().tolist())
    state_filter = st.multiselect("State", sorted(df["STATE"].dropna().unique().tolist()),
                                  default=sorted(df["STATE"].dropna().unique().tolist()))
    vin_search = st.text_input("Search VIN", "")

filtered = df[
    (df["RISK_TIER"].isin(tier_filter)) &
    (df["SUPPLIER_NAME"].isin(supplier_filter)) &
    (df["STATE"].isin(state_filter))
]
if vin_search:
    filtered = filtered[filtered["VIN"].str.contains(vin_search, case=False, na=False)]

# ── Summary KPIs ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Vehicles", f"{len(filtered):,}")
c2.metric("Critical", f"{len(filtered[filtered['RISK_TIER']=='CRITICAL']):,}")
c3.metric("High Risk", f"{len(filtered[filtered['RISK_TIER']=='HIGH']):,}")
c4.metric("Healthy (Low)", f"{len(filtered[filtered['RISK_TIER']=='LOW']):,}")

st.markdown("---")

# ── Status color mapping ──
def risk_color(tier):
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(tier, "⚪")

display_df = filtered[["VIN", "RISK_TIER", "RISK_SCORE", "SUPPLIER_NAME", "BATTERY_TYPE_NAME",
                        "STATE", "ERROR_COUNT", "VEHICLE_CONFIG", "MODEL_YEAR"]].copy()
display_df.insert(0, "Status", display_df["RISK_TIER"].apply(risk_color))
display_df = display_df.rename(columns={
    "RISK_TIER": "Risk Tier", "RISK_SCORE": "Risk Score", "SUPPLIER_NAME": "Supplier",
    "BATTERY_TYPE_NAME": "Battery Type", "STATE": "State", "ERROR_COUNT": "Errors",
    "VEHICLE_CONFIG": "Config", "MODEL_YEAR": "Year"
})

st.dataframe(display_df, width="stretch", hide_index=True, height=400)

# ── Vehicle Detail Panel ──
st.markdown("---")
st.markdown('<p class="section-header">Vehicle Detail</p>', unsafe_allow_html=True)

selected_vin = st.selectbox("Select a vehicle to inspect", filtered["VIN"].head(50).tolist())
if selected_vin:
    vehicle = filtered[filtered["VIN"] == selected_vin].iloc[0]
    car_id = int(vehicle["CAR_ID"])

    v1, v2, v3, v4 = st.columns(4)
    tier = vehicle["RISK_TIER"]
    tier_color = {"CRITICAL": COLORS["critical"], "HIGH": COLORS["accent3"],
                  "MEDIUM": COLORS["warning"], "LOW": COLORS["healthy"]}.get(tier, "#8B949E")
    v1.markdown(f"**Risk Score:** <span style='color:{tier_color}; font-size:1.5rem; font-weight:700;'>{vehicle['RISK_SCORE']}</span>", unsafe_allow_html=True)
    v2.metric("Error Count", int(vehicle["ERROR_COUNT"]))
    v3.metric("Supplier", vehicle["SUPPLIER_NAME"][:25])
    v4.metric("Battery", vehicle["BATTERY_TYPE_NAME"][:25])

    # Event history
    events_query = Q.VEHICLE_EVENTS.format(car_id=car_id)
    events = run_query(session, events_query)
    if not events.empty:
        st.markdown("**Event History**")
        failures = events[events["HAS_ERROR"] == 1]
        if not failures.empty:
            fig = px.scatter(
                failures, x="EVENT_DATE", y="AVG_TEMP_F", color="DTC_CODE",
                hover_data=["ERROR_DESCRIPTION", "DISTANCE_MILES", "WIND_SPEED"],
                title="Failure Events Timeline",
            )
            fig.update_layout(**PLOTLY_LAYOUT, height=250, xaxis_title="Date", yaxis_title="Temp (°F)")
            st.plotly_chart(fig, width="stretch")
        with st.expander(f"All Events ({len(events)})"):
            st.dataframe(events, width="stretch", hide_index=True)

    # Battery specs
    part_number = vehicle["PART_NUMBER"].replace("'", "''")
    comp = run_query(session, Q.COMPONENT_DETAILS.format(part_number=part_number))
    if not comp.empty:
        c = comp.iloc[0]
        st.markdown("**Battery Specifications**")
        b1, b2, b3 = st.columns(3)
        b1.markdown(f"- **Type:** {c.get('BATTERY_TYPE_NAME', 'N/A')}\n- **Anode:** {c.get('ANODE', 'N/A')}\n- **Cathode:** {c.get('CATHODE', 'N/A')}")
        b2.markdown(f"- **Voltage:** {c.get('VOLTAGE_RANGE', 'N/A')}\n- **Charging V:** {c.get('RECOMMENDED_CHARGING_VOLTAGE_RANGE', 'N/A')}\n- **Discharge:** {c.get('DISCHARGE_CURRENT', 'N/A')}")
        b3.markdown(f"- **Overcharge Prot:** {'Yes' if c.get('OVERCHARGE_PROTECTION') == 1 else 'No'}\n- **Overcurrent Prot:** {'Yes' if c.get('OVERCURRENT_PROTECTION') == 1 else 'No'}\n- **Cut-off V:** {c.get('CUT_OFF_VOLTAGE', 'N/A')}")
