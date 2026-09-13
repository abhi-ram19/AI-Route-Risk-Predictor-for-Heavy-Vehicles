"""
Report Generator — Module 7
Builds a downloadable PDF trip summary using ReportLab.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_report(origin_name, destination_name, route, weather, risk_result, recommendations, departure_hour):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, spaceAfter=6)
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body_style = styles["BodyText"]

    story = []

    story.append(Paragraph("AI Route Risk Predictor — Trip Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Trip Overview", heading_style))
    overview_data = [
        ["Origin", origin_name],
        ["Destination", destination_name],
        ["Distance", f"{route['distance_km']} km"],
        ["Estimated Travel Time", f"{round(route['duration_min'])} min"],
        ["Planned Departure Hour", f"{departure_hour}:00"],
        ["Overall Risk Score", f"{risk_result['overall_score']} / 100 ({risk_result['risk_level']})"],
    ]
    overview_table = Table(overview_data, colWidths=[5.5 * cm, 9 * cm])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f2f6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(overview_table)

    story.append(Paragraph("Weather Conditions", heading_style))
    weather_data = [
        ["Temperature", f"{weather['temperature_c']} °C"],
        ["Rain Probability", f"{weather['rain_probability_pct']}%"],
        ["Humidity", f"{weather['humidity_pct']}%"],
        ["Wind Speed", f"{weather['wind_speed_kmh']} km/h"],
        ["Estimated Visibility", f"{weather['visibility_km']} km"],
    ]
    weather_table = Table(weather_data, colWidths=[5.5 * cm, 9 * cm])
    weather_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f2f6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(weather_table)

    story.append(Paragraph("Risk Factor Breakdown", heading_style))
    factor_labels = {
        "rain": "Rain",
        "traffic": "Traffic",
        "visibility": "Visibility",
        "duration": "Travel Duration",
        "road_type": "Road Type",
        "time_of_day": "Time of Day",
    }
    factor_rows = [["Factor", "Raw Score (0-100)", "Weighted Contribution"]]
    for key, label in factor_labels.items():
        factor_rows.append([
            label,
            str(risk_result["factor_scores"][key]),
            str(risk_result["factor_contributions"][key]),
        ])
    factor_table = Table(factor_rows, colWidths=[5.5 * cm, 5 * cm, 5 * cm])
    factor_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4a4a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(factor_table)

    story.append(Paragraph("AI Recommendations", heading_style))
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    disclaimer_style = ParagraphStyle("Disclaimer", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)
    story.append(Paragraph(
        "Note: Traffic and road-type risk values in this MVP are heuristic estimates based on time-of-day "
        "patterns and route characteristics, not live traffic feeds. Weather data is sourced from Open-Meteo.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
