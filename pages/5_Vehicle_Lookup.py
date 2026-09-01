import streamlit as st
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.connection import get_session, run_query

st.set_page_config(page_title="Vehicle Lookup", page_icon="🔍", layout="wide")
st.title("🔍 Vehicle Lookup")
st.markdown("Search by VIN to inspect individual vehicle history and battery details.")

session = get_session()

# --- Search ---
vin_input = st.text_input("Enter VIN (or partial VIN)", placeholder="e.g. 7jszg7js")

if vin_input:
    safe_vin = vin_input.replace("'", "''").replace("%", "").replace("_", "")
    search_query = f"""
    SELECT
        v.CAR_ID, v.VIN, v.MODEL_YEAR, v.VEHICLE_CONFIG, v.STATE, v.STATE_AB,
        v.PART_NUMBER, v.BATTERY_SERIAL_NUMBER, v.AH, v.AMP_HOURS,
        v.BATTERY_TYPE_ID, v.SUPPLIER_ID, v.TEMP_RANGE_CELSIUS, v.VOLTAGE_RANGE
    FROM VEHICLE_QUALITY_DB.PUBLIC.DIM_VEHICLES v
    WHERE v.VIN ILIKE '%{safe_vin}%'
    LIMIT 20
    """
    results = run_query(session, search_query)

    if results.empty:
        st.warning("No vehicles found matching that VIN.")
    else:
        st.success(f"Found {len(results)} vehicle(s)")

        # Select vehicle if multiple
        if len(results) > 1:
            vin_options = results["VIN"].tolist()
            selected_vin = st.selectbox("Select Vehicle", vin_options)
            vehicle = results[results["VIN"] == selected_vin].iloc[0]
        else:
            vehicle = results.iloc[0]

        # --- Vehicle Info Card ---
        st.markdown("---")
        st.subheader(f"Vehicle: {vehicle['VIN']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Model Year", int(vehicle["MODEL_YEAR"]))
        c2.metric("Configuration", vehicle["VEHICLE_CONFIG"].title())
        c3.metric("State", vehicle["STATE"])
        c4.metric("Part Number", vehicle["PART_NUMBER"])

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Battery Serial", vehicle["BATTERY_SERIAL_NUMBER"][:20])
        c6.metric("Amp Hours", f"{vehicle['AH']} AH")
        c7.metric("Temp Range", vehicle["TEMP_RANGE_CELSIUS"])
        c8.metric("Voltage Range", vehicle["VOLTAGE_RANGE"])

        # --- Event History ---
        st.markdown("---")
        st.subheader("Quality Event History")
        car_id = int(vehicle["CAR_ID"])
        events_query = f"""
        SELECT
            EVENT_DATE, DTC_CODE, ERROR_DESCRIPTION, HAS_ERROR,
            ROUND(AVG_TEMP_F, 1) AS AVG_TEMP_F,
            ROUND(DIST_IN_M, 1) AS DISTANCE_MILES,
            SUPPLIER_NAME, BATTERY_TYPE_NAME
        FROM VEHICLE_QUALITY_DB.PUBLIC.FACT_QUALITY_EVENTS
        WHERE CAR_ID = {car_id}
        ORDER BY EVENT_DATE DESC
        """
        events_df = run_query(session, events_query)

        if events_df.empty:
            st.info("No quality events recorded for this vehicle.")
        else:
            # Event summary
            total_events = len(events_df)
            failure_events = int(events_df["HAS_ERROR"].sum())
            e1, e2, e3 = st.columns(3)
            e1.metric("Total Events", total_events)
            e2.metric("Failure Events", failure_events)
            e3.metric("Failure Rate", f"{failure_events/total_events*100:.1f}%")

            # Failures over time
            failures_only = events_df[events_df["HAS_ERROR"] == 1]
            if not failures_only.empty:
                fig = px.scatter(
                    failures_only,
                    x="EVENT_DATE",
                    y="AVG_TEMP_F",
                    color="DTC_CODE",
                    size_max=10,
                    hover_data=["ERROR_DESCRIPTION", "DISTANCE_MILES"],
                    title="Failure Events Timeline",
                )
                fig.update_layout(
                    template="plotly_dark",
                    height=300,
                    margin=dict(l=40, r=20, t=40, b=40),
                    xaxis_title="Date",
                    yaxis_title="Temperature (°F)",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Full event table
            with st.expander("View All Events"):
                st.dataframe(events_df, use_container_width=True, hide_index=True)

        # --- Component Details ---
        st.markdown("---")
        st.subheader("Battery Component Specifications")
        part_number = vehicle["PART_NUMBER"].replace("'", "''")
        comp_query = f"""
        SELECT *
        FROM VEHICLE_QUALITY_DB.PUBLIC.DIM_COMPONENTS
        WHERE PART_NUMBER = '{part_number}'
        """
        comp_df = run_query(session, comp_query)
        if not comp_df.empty:
            comp = comp_df.iloc[0]
            cc1, cc2, cc3 = st.columns(3)
            cc1.markdown(f"""
            **Chemistry**
            - Type: {comp.get('BATTERY_TYPE_NAME', 'N/A')}
            - Anode: {comp.get('ANODE', 'N/A')}
            - Cathode: {comp.get('CATHODE', 'N/A')}
            - Electrolyte: {comp.get('ELECTROLYTE', 'N/A')}
            """)
            cc2.markdown(f"""
            **Electrical Specs**
            - Voltage Range: {comp.get('VOLTAGE_RANGE', 'N/A')}
            - Charging Voltage: {comp.get('RECOMMENDED_CHARGING_VOLTAGE_RANGE', 'N/A')}
            - Charging Current: {comp.get('RECOMMENDED_CHARGING_CURRENT_RANGE', 'N/A')}
            - Discharge Current: {comp.get('DISCHARGE_CURRENT', 'N/A')}
            """)
            cc3.markdown(f"""
            **Safety & Specs**
            - Overcharge Protection: {'Yes' if comp.get('OVERCHARGE_PROTECTION') == 1 else 'No'}
            - Overcurrent Protection: {'Yes' if comp.get('OVERCURRENT_PROTECTION') == 1 else 'No'}
            - Cut-off Voltage: {comp.get('CUT_OFF_VOLTAGE', 'N/A')}
            - Size: {comp.get('SIZE_LENGTH_CM', 'N/A')} cm
            """)
else:
    st.info("Enter a VIN above to search for a vehicle.")
