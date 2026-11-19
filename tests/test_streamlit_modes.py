from streamlit.testing.v1 import AppTest
import pytest

def test_streamlit_single_city_flow():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Page 1: Single City Mode default, Continue
    assert at.session_state["page"] == 1
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    # Page 2: Advance to Places & Attractions
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Page 3: Choose 2 places
    cbs = [cb for cb in at.checkbox]
    assert len(cbs) >= 2
    cbs[0].check()
    cbs[1].check()

    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    # Page 4: Choose hotel
    choose_btns = [b for b in at.button if "Choose this hotel" in b.label or "Selected Stay" in b.label]
    assert len(choose_btns) >= 1

    for cb in at.checkbox:
        at.session_state[cb.key] = False

    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # Page 5: Verify metrics
    assert len(at.metric) >= 4

def test_streamlit_multi_city_kerala_flow():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Switch to Multi-City Mode
    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    # Verify cities multiselect on Page 2
    assert len(at.multiselect) >= 1
    at.multiselect[0].set_value(["Munnar", "Thekkady", "Alleppey"]).run()

    # Page 2 -> Page 3
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Select places
    cbs = [cb for cb in at.checkbox]
    if cbs:
        cbs[0].check()

    # Page 3 -> Page 4
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    for cb in at.checkbox:
        at.session_state[cb.key] = False

    # Page 4 -> Page 5
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # Verify metrics
    assert len(at.metric) >= 4
