# AI Route Risk Predictor for Heavy Vehicles

An AI-powered dashboard that analyzes routes between a source and destination, estimates travel risk from weather, traffic, and road conditions, highlights risky sections on a heatmap, recommends departure times, and generates a downloadable PDF trip report.

Built with Streamlit, per the project PRD (MVP v1.0).

## Quick Start

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## No API Keys Needed

The original PRD specified OpenRouteService and OpenWeather, which both require free-tier signup. This build instead uses:

| Purpose | Service | Notes |
|---|---|---|
| Geocoding (place name → coordinates) | Nominatim (via `geopy`) | Free, no key. Respect 1 req/sec usage policy. |
| Route / distance / ETA | OSRM public demo server | Free, no key. Not for production-scale traffic — swap to a hosted OSRM or ORS instance if you outgrow it. |
| Weather | Open-Meteo | Free, no key, no rate-limit signup required. |

If you'd rather use OpenRouteService or OpenWeather (e.g. for their traffic-aware routing or more detailed weather), swap the request logic inside `services/route_service.py` or `services/weather_service.py` — the rest of the app expects the same return shape, so nothing else needs to change.

## Project Structure

```
AI-Route-Risk-Predictor/
├── app.py                       # Main Streamlit dashboard
├── services/
│   ├── route_service.py         # Module 1: Route, distance, ETA (OSRM)
│   ├── weather_service.py       # Module 2: Weather (Open-Meteo)
│   ├── risk_engine.py           # Module 3 + 4: Risk scoring + segment heatmap
│   ├── recommendation.py        # Module 5: Rules-based AI recommendations
│   └── report_generator.py      # Module 7: PDF report (ReportLab)
├── utils/
│   └── geocode.py                # Place name → lat/lon (Nominatim)
├── pages/                        # Reserved for future multi-page split
├── assets/                       # Reserved for icons/images
├── data/                         # Reserved for cached/sample data
├── requirements.txt
└── README.md
```

## Risk Scoring Model

Overall Route Risk Score (0–100) is a weighted sum of six factors, per the PRD:

| Factor | Weight | Data Source |
|---|---|---|
| Rain | 25% | Live — Open-Meteo |
| Traffic | 30% | **Heuristic** — time-of-day pattern + distance |
| Visibility | 15% | Live (estimated) — Open-Meteo cloud cover + precipitation |
| Travel Duration | 10% | Live — OSRM route duration |
| Road Type | 10% | **Heuristic** — inferred from average route speed |
| Time of Day | 10% | Rule-based on planned departure hour |

**Why some factors are heuristic:** free, key-less APIs with real-time traffic and detailed road-classification data don't really exist at production quality. Rather than fabricate the impression of live traffic data, this MVP is transparent in the UI and PDF report about which numbers are real-time and which are modeled estimates. For a production version, plug in a paid traffic API (TomTom, HERE, Google Roads) into `risk_engine.py`.

## Current Scope (matches PRD Section 5)

✅ Route visualization · ✅ Distance/ETA · ✅ Weather analysis · ✅ Risk score · ✅ Route heatmap · ✅ AI recommendations · ✅ Downloadable PDF report

Not in this MVP (see PRD "Future Enhancements"): live dashcam analysis, driver drowsiness detection, automatic emergency calling, vehicle diagnostics/IoT, live GPS fleet tracking.

## Known Limitations

- OSRM's public demo server is rate-limited and not intended for heavy production traffic — fine for demos/portfolio use, not for a live fleet product.
- Nominatim geocoding works best with specific place names (city + country); very ambiguous inputs may geocode to an unexpected location.
- Segment-level heatmap risk includes a seeded pseudo-random variation layered on top of weather/time risk, to simulate localized conditions where no free hyper-local data source exists — this is clearly a simplification, not real per-kilometer sensor data.
