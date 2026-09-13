"""
AI Route Risk Predictor for Heavy Vehicles
Main Streamlit dashboard (app.py)

Run with:  streamlit run app.py
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

from utils.geocode import geocode_place
from services.route_service import get_route
from services.weather_service import get_weather
from services.risk_engine import calculate_risk, score_segments
from services.recommendation import generate_recommendations
from services.report_generator import generate_pdf_report

st.set_page_config(
    page_title="AI Route Risk Predictor",
    page_icon="🚚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🚚 AI Route Risk Predictor")
st.caption("Helping logistics companies make safer and smarter transportation decisions.")

# ---------------------------------------------------------------------------
# Input Section
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns([3, 3, 2])
with col1:
    source = st.text_input("Source", placeholder="e.g. Visakhapatnam, India")
with col2:
    destination = st.text_input("Destination", placeholder="e.g. Hyderabad, India")
with col3:
    departure_hour = st.slider("Planned Departure Hour", 0, 23, 9)

analyze_clicked = st.button("🔍 Analyze Route", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------
if analyze_clicked:
    if not source or not destination:
        st.warning("Please enter both a source and a destination.")
        st.stop()

    with st.spinner("Geocoding locations..."):
        origin_geo = geocode_place(source)
        dest_geo = geocode_place(destination)

    if not origin_geo:
        st.error(f"Could not find location: '{source}'. Try a more specific name (e.g. add city/State).")
        st.stop()
    if not dest_geo:
        st.error(f"Could not find location: '{destination}'. Try a more specific name (e.g. add city/State).")
        st.stop()

    with st.spinner("Fetching route..."):
        try:
            route = get_route(origin_geo, dest_geo)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

    if not route:
        st.error("No route could be found between these locations. They may not be connected by road.")
        st.stop()

    with st.spinner("Collecting weather data..."):
        try:
            weather = get_weather(dest_geo["lat"], dest_geo["lon"])
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

    if not weather:
        st.error("Could not fetch weather data for this route.")
        st.stop()

    with st.spinner("Analyzing risk..."):
        risk_result = calculate_risk(route, weather, departure_hour)
        segments = score_segments(
            route["segments"],
            base_weather_risk=(risk_result["factor_scores"]["rain"] + risk_result["factor_scores"]["visibility"]) / 2,
            departure_hour=departure_hour,
            distance_km=route["distance_km"],
        )
        recommendations = generate_recommendations(risk_result, weather, segments, departure_hour)

    # Save to session state so downstream widgets (like PDF download) persist
    st.session_state["result"] = {
        "origin_name": origin_geo["address"],
        "destination_name": dest_geo["address"],
        "origin_geo": origin_geo,
        "dest_geo": dest_geo,
        "route": route,
        "weather": weather,
        "risk_result": risk_result,
        "segments": segments,
        "recommendations": recommendations,
        "departure_hour": departure_hour,
    }

# ---------------------------------------------------------------------------
# Display Dashboard (if we have a result)
# ---------------------------------------------------------------------------
if "result" in st.session_state:
    r = st.session_state["result"]

    st.divider()

    # --- Route Map ---
    st.subheader("🗺️ Interactive Route Map")
    m = folium.Map(
        location=r["route"]["geometry"][len(r["route"]["geometry"]) // 2],
        zoom_start=7,
        tiles="OpenStreetMap",
    )
    folium.Marker(
        [r["origin_geo"]["lat"], r["origin_geo"]["lon"]],
        popup="Origin", icon=folium.Icon(color="green"),
    ).add_to(m)
    folium.Marker(
        [r["dest_geo"]["lat"], r["dest_geo"]["lon"]],
        popup="Destination", icon=folium.Icon(color="red"),
    ).add_to(m)
    folium.PolyLine(r["route"]["geometry"], color="#1f77b4", weight=4, opacity=0.8).add_to(m)

    # Heatmap overlay: color-coded segment markers (Module 4)
    color_map = {"green": "green", "yellow": "orange", "red": "red"}
    for seg in r["segments"]:
        folium.CircleMarker(
            location=seg["midpoint"],
            radius=6,
            color=color_map.get(seg["color"], "gray"),
            fill=True,
            fill_opacity=0.8,
            popup=f"Km {seg['start_km']} — Risk {seg['risk_score']}",
        ).add_to(m)

    st_folium(m, width=None, height=480, key="route_map")

    # --- Trip Summary Cards ---
    st.subheader("📊 Trip Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Distance", f"{r['route']['distance_km']} km")
    c2.metric("ETA", f"{round(r['route']['duration_min'])} min")
    c3.metric("Risk Score", f"{r['risk_result']['overall_score']}/100", r['risk_result']['risk_level'])
    fuel_estimate = round(r['route']['distance_km'] / 4.5, 1)  # ~4.5 km/l assumption for heavy vehicles
    c4.metric("Fuel Estimate", f"{fuel_estimate} L")
    c5.metric("Avg Temp", f"{r['weather']['temperature_c']} °C")

    # --- Weather Cards ---
    st.subheader("🌦️ Weather Conditions")
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Rain Probability", f"{r['weather']['rain_probability_pct']}%")
    w2.metric("Humidity", f"{r['weather']['humidity_pct']}%")
    w3.metric("Wind Speed", f"{r['weather']['wind_speed_kmh']} km/h")
    w4.metric("Visibility (est.)", f"{r['weather']['visibility_km']} km")

    # --- Risk Score Gauge + Factor Breakdown ---
    st.subheader("⚠️ Risk Score Breakdown")
    gauge_col, breakdown_col = st.columns([1, 2])

    with gauge_col:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=r["risk_result"]["overall_score"],
            title={"text": "Overall Route Risk"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 35], "color": "#d4edda"},
                    {"range": [35, 65], "color": "#fff3cd"},
                    {"range": [65, 100], "color": "#f8d7da"},
                ],
            },
        ))
        gauge.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(gauge, use_container_width=True)

    with breakdown_col:
        labels = {
            "rain": "Rain", "traffic": "Traffic", "visibility": "Visibility",
            "duration": "Duration", "road_type": "Road Type", "time_of_day": "Time of Day",
        }
        factor_scores = r["risk_result"]["factor_scores"]
        bar = go.Figure(go.Bar(
            x=[labels[k] for k in factor_scores],
            y=[factor_scores[k] for k in factor_scores],
            marker_color=["#e74c3c" if v >= 65 else "#f1c40f" if v >= 35 else "#2ecc71" for v in factor_scores.values()],
        ))
        bar.update_layout(
            title="Risk Factors (0-100 raw score)",
            yaxis_range=[0, 100], height=280, margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(bar, use_container_width=True)

    st.caption("ℹ️ Traffic and Road Type are heuristic estimates based on time-of-day and route characteristics "
               "(no live traffic feed in this free-tier MVP). Rain and Visibility come from live weather data.")

    # --- Route Heatmap Segment Table ---
    st.subheader("🔥 Route Heatmap — Segment Risk")
    heat_cols = st.columns(min(6, len(r["segments"])) or 1)
    for i, seg in enumerate(r["segments"]):
        col = heat_cols[i % len(heat_cols)]
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[seg["color"]]
        col.metric(f"Km {seg['start_km']}", f"{emoji} {seg['risk_score']}")

    # --- AI Recommendations ---
    st.subheader("🤖 AI Recommendations")
    for rec in r["recommendations"]:
        st.info(rec)

    # --- Report Download ---
    st.subheader("📄 Download Trip Report")
    pdf_buffer = generate_pdf_report(
        r["origin_name"], r["destination_name"], r["route"], r["weather"],
        r["risk_result"], r["recommendations"], r["departure_hour"],
    )
    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_buffer,
        file_name="route_risk_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

else:
    st.info("Enter a source and destination above, then click **Analyze Route** to get started.")
