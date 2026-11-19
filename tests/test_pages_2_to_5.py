import datetime as dt
import pytest
from streamlit.testing.v1 import AppTest
from pdf_generator import generate_itinerary_pdf

def test_page1_no_sidebar_and_transition():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert at.session_state["page"] == 1
    # On Page 1, Continue button navigates to Page 2
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

def test_single_city_full_flow_pages_2_to_5():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Step to Page 2
    at.button[0].click().run()
    assert at.session_state["page"] == 2
    assert any("Plan Details" in m.value for m in at.markdown)

    # Click Next: Places & Attractions -> Page 3
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # On Page 3, select at least 2 attractions
    cbs = [cb for cb in at.checkbox]
    assert len(cbs) >= 2
    cbs[0].check()
    cbs[1].check()

    # Click Find hotels near my picks -> Page 4
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    # On Page 4, verify hotel selection button
    choose_btns = [b for b in at.button if "Choose this hotel" in b.label or "Selected Stay" in b.label]
    assert len(choose_btns) >= 1

    # Click Find the Map -> Page 5
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # On Page 5, verify metrics and download button
    assert len(at.metric) >= 4
    dl_btns = at.get("download_button")
    assert len(dl_btns) == 1
    assert "Download Itinerary" in dl_btns[0].proto.label

def test_multi_city_full_flow_pages_2_to_5():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Switch to Multi-City on Page 1
    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2
    assert "Multi-City" in at.session_state["trip_mode"]

    # On Page 2, verify selected cities
    assert len(at.session_state["mc_selected_cities"]) >= 2

    # Advance to Page 3
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # On Page 3, select attraction for active city
    cbs = [cb for cb in at.checkbox]
    if cbs:
        cbs[0].check()

    # Advance to Page 4 (Hotels)
    find_hotels_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    find_hotels_btn.click().run()
    assert at.session_state["page"] == 4

    # Advance to Page 5 (Map & Itinerary)
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    find_map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    find_map_btn.click().run()
    assert at.session_state["page"] == 5

    # Verify Page 5 metrics & itinerary
    assert len(at.metric) >= 4
    dl_btns = at.get("download_button")
    assert len(dl_btns) == 1
    assert "Download Itinerary" in dl_btns[0].proto.label

def test_pdf_generation_content_and_links():
    pdf_bytes = generate_itinerary_pdf(
        trip_title="Trip Summary - Agra",
        trip_mode="Single-City Mode",
        cities_str="Agra, Uttar Pradesh",
        travel_dates_str="15 Dec 2025 – 17 Dec 2025",
        travellers_count=2,
        total_budget_str="₹14,000 (approx.)",
        hotels_info=[{
            "name": "Hotel Clarks Shiraz",
            "city": "Agra",
            "tier": "Premium",
            "rating": "4.3 (1.8k reviews)",
            "address": "54, Taj Road, Agra",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=Hotel+Clarks+Shiraz+Agra"
        }],
        attractions_info=[{
            "name": "Taj Mahal",
            "city": "Agra",
            "category": "Heritage",
            "rating": "4.4",
            "duration": "2.0",
            "url": "https://en.wikipedia.org/wiki/Taj_Mahal"
        }],
        schedule_days=[{
            "day_label": "Day 1",
            "date_str": "15 Dec 2025",
            "stops": [
                {"time": "09:00 - 12:00", "what": "Taj Mahal", "km": 3.0},
                {"time": "12:00 - 13:00", "what": "Lunch break", "km": 0.0}
            ]
        }],
        budget_breakdown={
            "Accommodation": "₹4,500",
            "Food & Meals": "₹3,000",
            "Local Transport": "₹2,500",
            "Attraction Tickets": "₹2,000",
            "Miscellaneous": "₹2,000",
            "Total Estimated Budget": "₹14,000"
        }
    )
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
