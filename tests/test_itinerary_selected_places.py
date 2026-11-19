import pytest
from streamlit.testing.v1 import AppTest

def test_single_city_selected_places_appear_in_itinerary():
    """Verify that selected attractions appear in Single City itinerary."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Page 1: Single City Mode default, Continue
    assert at.session_state["page"] == 1
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    # Page 2: Select Goa or proceed with default Agra
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Page 3: Check first 2 attractions
    cbs = [cb for cb in at.checkbox]
    assert len(cbs) >= 2
    cbs[0].check()
    cbs[1].check()

    # Move to Page 4 (Hotels)
    find_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    find_btn.click().run()
    assert at.session_state["page"] == 4

    # Page 4: Choose hotel or proceed to Map/Itinerary
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # Verify metrics appear
    assert len(at.metric) >= 4

    # Selected places must appear in the schedule timeline or route map
    user_picks = at.session_state["chosen"]
    markdown_text = " ".join(m.value for m in at.markdown)
    for pick in user_picks:
        assert pick in markdown_text

def test_multi_city_selected_places_workflow_and_rerun():
    """Verify that selected attractions appear in Multi-City itinerary and survive reruns."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Page 1 -> Multi-City
    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    # Page 2: Set cities to Munnar and Thekkady
    at.multiselect[0].set_value(["Munnar", "Thekkady"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Select 2 attractions in Munnar (first active city)
    munnar_cbs = [cb for cb in at.checkbox]
    assert len(munnar_cbs) >= 2
    munnar_cbs[0].check()
    munnar_cbs[1].check()

    # Switch to Thekkady via sidebar
    thekkady_btns = [b for b in at.button if "Thekkady" in b.label]
    if thekkady_btns:
        thekkady_btns[0].click().run()
        thekkady_cbs = [cb for cb in at.checkbox]
        if thekkady_cbs:
            thekkady_cbs[0].check()

    # Advance to Page 4 (Hotels)
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    # Advance to Page 5 (Itinerary & Map)
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # Verify summary metrics
    assert len(at.metric) >= 4

    # Verify that selected places appear in the itinerary markdown
    chosen = at.session_state["mc_chosen"]
    all_markdown_text = " ".join(m.value for m in at.markdown)
    for ck, places_list in chosen.items():
        for place in places_list:
            assert place in all_markdown_text

    # Verify itinerary survives a normal rerun
    at.run()
    assert at.session_state["page"] == 5
    all_markdown_after = " ".join(m.value for m in at.markdown)
    for ck, places_list in chosen.items():
        for place in places_list:
            assert place in all_markdown_after
