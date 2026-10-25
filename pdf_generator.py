"""
PDF Itinerary Generator for AI Route & Stay Planner
Generates professional downloadable PDF itineraries with real clickable
Google Maps and Wikipedia/Search links using ReportLab.
"""

import io
import datetime as dt
from urllib.parse import quote_plus
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

FOREST_GREEN = colors.HexColor("#102F26")
LIGHT_GREEN  = colors.HexColor("#173F32")
TERRACOTTA   = colors.HexColor("#C45D3A")
WARM_CREAM   = colors.HexColor("#F7F0E2")
DARK_TEXT    = colors.HexColor("#1A2821")
MUTED_TEXT   = colors.HexColor("#5C6B62")
BORDER_COLOR = colors.HexColor("#DCE0D4")
BG_CARD      = colors.HexColor("#FFFFFF")

def generate_itinerary_pdf(
    trip_title: str,
    trip_mode: str,
    cities_str: str,
    travel_dates_str: str,
    travellers_count: int,
    total_budget_str: str,
    hotels_info: list[dict],
    attractions_info: list[dict],
    schedule_days: list[dict],
    budget_breakdown: dict,
) -> bytes:
    """
    Builds an in-memory PDF document and returns bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "TripTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=FOREST_GREEN,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "TripSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED_TEXT,
        spaceAfter=12,
    )
    section_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=FOREST_GREEN,
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT,
    )
    bold_style = ParagraphStyle(
        "BoldDark",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    link_maps = ParagraphStyle(
        "LinkMaps",
        parent=body_style,
        textColor=FOREST_GREEN,
    )
    link_wiki = ParagraphStyle(
        "LinkWiki",
        parent=body_style,
        textColor=TERRACOTTA,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=MUTED_TEXT,
        spaceBefore=10,
    )

    story = []

    # 1. Header Banner
    header_table = Table(
        [
            [
                Paragraph(f"<b>AI Route & Stay Planner</b>", title_style),
                Paragraph(f"<b>{trip_mode}</b>", ParagraphStyle("ModeBadge", parent=bold_style, textColor=TERRACOTTA, alignment=2, fontSize=11)),
            ],
            [
                Paragraph(f"{trip_title} &bull; {cities_str}", subtitle_style),
                Paragraph(f"Dates: {travel_dates_str} &bull; {travellers_count} Traveller(s)", ParagraphStyle("DatesMeta", parent=body_style, textColor=MUTED_TEXT, alignment=2)),
            ]
        ],
        colWidths=[360, 180],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=TERRACOTTA, spaceBefore=4, spaceAfter=10))

    # 2. Trip Overview Table
    overview_data = [
        [
            Paragraph("<b>Destination(s)</b>", bold_style),
            Paragraph("<b>Travel Dates</b>", bold_style),
            Paragraph("<b>Travellers</b>", bold_style),
            Paragraph("<b>Total Estimated Budget</b>", bold_style),
        ],
        [
            Paragraph(cities_str, body_style),
            Paragraph(travel_dates_str, body_style),
            Paragraph(f"{travellers_count}", body_style),
            Paragraph(f"<b>{total_budget_str}</b>", ParagraphStyle("BudVal", parent=bold_style, textColor=TERRACOTTA)),
        ]
    ]
    ov_table = Table(overview_data, colWidths=[150, 150, 80, 160])
    ov_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEAE1")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAF7F2")),
        ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ov_table)
    story.append(Spacer(1, 10))

    # 3. Selected Hotels Section
    story.append(Paragraph("Selected Accommodations & Stays", section_h2))
    hotel_rows = [
        [
            Paragraph("<b>City / Stay</b>", bold_style),
            Paragraph("<b>Tier & Rating</b>", bold_style),
            Paragraph("<b>Address & Details</b>", bold_style),
            Paragraph("<b>Google Maps Location</b>", bold_style),
        ]
    ]
    for h in hotels_info:
        h_name = h.get("name", "Hotel")
        h_city = h.get("city", "")
        h_tier = h.get("tier", "Standard")
        h_rating = str(h.get("rating", ""))
        h_addr = h.get("address", "")
        g_url = h.get("maps_url") or f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{h_name} {h_city} India')}"
        
        hotel_rows.append([
            Paragraph(f"<b>{h_name}</b><br/><font color='#5C6B62'>{h_city}</font>", body_style),
            Paragraph(f"{h_tier}<br/>Rating: {h_rating}", body_style),
            Paragraph(h_addr[:100] if h_addr else "Verified stay", body_style),
            Paragraph(f'<a href="{g_url}" color="#102F26"><u><b>View on Google Maps &rarr;</b></u></a>', link_maps),
        ])

    ht_table = Table(hotel_rows, colWidths=[150, 100, 160, 130])
    ht_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEAE1")),
        ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ht_table)
    story.append(Spacer(1, 10))

    # 4. Selected Places & Attractions Section
    story.append(Paragraph("Selected Places & Attractions", section_h2))
    attr_rows = [
        [
            Paragraph("<b>Attraction Name</b>", bold_style),
            Paragraph("<b>City & Category</b>", bold_style),
            Paragraph("<b>Rating / Duration</b>", bold_style),
            Paragraph("<b>Verified Information</b>", bold_style),
        ]
    ]
    for a in attractions_info:
        a_name = a.get("name", "Attraction")
        a_city = a.get("city", "")
        a_cat = a.get("category", "Heritage")
        a_rating = str(a.get("rating", ""))
        a_dur = str(a.get("duration", "2.0"))
        a_url = a.get("url") or f"https://www.google.com/search?q={quote_plus(f'{a_name} {a_city} India')}"

        attr_rows.append([
            Paragraph(f"<b>{a_name}</b>", body_style),
            Paragraph(f"{a_city} &bull; {a_cat}", body_style),
            Paragraph(f"★ {a_rating} &bull; {a_dur} hrs", body_style),
            Paragraph(f'<a href="{a_url}" color="#C45D3A"><u><b>Search Destination &rarr;</b></u></a>', link_wiki),
        ])

    at_table = Table(attr_rows, colWidths=[160, 140, 110, 130])
    at_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEAE1")),
        ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(at_table)
    story.append(Spacer(1, 10))

    # 5. Day-by-Day Schedule Section
    story.append(Paragraph("Optimized Day-Wise Schedule", section_h2))
    for day_item in schedule_days:
        day_label = day_item.get("day_label", "Day")
        day_date = day_item.get("date_str", "")
        day_stops = day_item.get("stops", [])

        story.append(Paragraph(f"<b>{day_label} &mdash; {day_date}</b>", ParagraphStyle("DayTitle", parent=bold_style, textColor=LIGHT_GREEN, fontSize=10, spaceBefore=6, spaceAfter=3)))

        day_table_data = [
            [
                Paragraph("<b>Time</b>", bold_style),
                Paragraph("<b>Activity / Stop</b>", bold_style),
                Paragraph("<b>Travel Distance / Details</b>", bold_style),
            ]
        ]
        for st_item in day_stops:
            t_str = st_item.get("time", "")
            w_str = st_item.get("what", "")
            km_str = str(st_item.get("km", "0"))
            details_str = f"{km_str} km driving" if km_str and float(km_str) > 0 else "-"
            if "hotel" in w_str.lower() and "start" in w_str.lower():
                details_str = "Departure from hotel"
            day_table_data.append([
                Paragraph(t_str, body_style),
                Paragraph(w_str, body_style),
                Paragraph(details_str, body_style),
            ])

        dt_table = Table(day_table_data, colWidths=[110, 260, 170])
        dt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FAF7F2")),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(dt_table)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 6))

    # 6. Budget Breakdown
    story.append(Paragraph("Estimated Trip Budget Breakdown", section_h2))
    b_rows = [
        [
            Paragraph(f"<b>{k}</b>", body_style),
            Paragraph(f"{v}", ParagraphStyle("BVal", parent=body_style, alignment=2)),
        ]
        for k, v in budget_breakdown.items()
    ]
    b_table = Table(b_rows, colWidths=[360, 180])
    b_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -2), colors.HexColor("#FFFFFF")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EFEAE1")),
        ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(b_table)

    # 7. Disclaimers & Attribution
    story.append(Paragraph(
        "<b>Important Notice:</b> All room availabilities and estimated budgets are simulated figures derived from historical seasonal demand models and benchmark averages &mdash; not guaranteed real-time transaction prices. Sights information and descriptions licensed under CC BY-SA (Wikipedia / Wikimedia Commons).",
        disclaimer_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
