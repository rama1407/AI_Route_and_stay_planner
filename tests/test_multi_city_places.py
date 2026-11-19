import pytest
from streamlit.testing.v1 import AppTest

def test_single_city_places_selection_preserved():
    """Verify the original Single City Places selection workflow works through Pages 1 to 5."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Page 1 -> Page 2
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    # Page 2 -> Page 3
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Select 2 specific places
    cbs = [cb for cb in at.checkbox]
    assert len(cbs) >= 2
    cbs[0].check()
    cbs[1].check()

    # Page 3 -> Page 4
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    # Page 4 -> Page 5
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    # Verify metrics and markdown
    assert len(at.metric) >= 4
    all_markdown = " ".join(m.value for m in at.markdown)
    for pick in at.session_state["chosen"]:
        assert pick in all_markdown

def test_multi_city_step_navigation_and_tabs():
    """Verify navigation to Page 3 (Choose Places) with multiple selected cities."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    at.multiselect[0].set_value(["Munnar", "Thekkady", "Alleppey"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Verify attraction checkboxes are rendered
    cbs = [cb for cb in at.checkbox if cb.key and "cb_p3_" in cb.key]
    assert len(cbs) > 0

    # Verify city navigation sub-buttons exist in sidebar
    city_btns = [b for b in at.button if any(c in b.label for c in ["Munnar", "Thekkady", "Alleppey"])]
    assert len(city_btns) >= 2

def test_multi_city_only_selected_places_in_itinerary():
    """Verify each city's itinerary contains only its selected attractions."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    at.multiselect[0].set_value(["Munnar", "Thekkady"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Active city is Munnar: select first place then run so mc_chosen is updated
    munnar_cbs = [cb for cb in at.checkbox if cb.key and "munnar" in cb.key]
    assert len(munnar_cbs) > 0
    munnar_cbs[0].check().run()

    # Switch to Thekkady via sidebar
    thekkady_btn = [b for b in at.button if "Thekkady" in b.label][0]
    thekkady_btn.click().run()

    thekkady_cbs = [cb for cb in at.checkbox if cb.key and "thekkady" in cb.key]
    assert len(thekkady_cbs) > 0
    thekkady_cbs[0].check().run()

    # Move to Page 4 (Hotels)
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()
    assert at.session_state["page"] == 4

    # Move to Page 5 (Itinerary)
    for cb in at.checkbox:
        at.session_state[cb.key] = False
    map_btn = [b for b in at.button if "Find the Map" in b.label][0]
    map_btn.click().run()
    assert at.session_state["page"] == 5

    user_chosen = at.session_state["mc_chosen"]
    assert len(user_chosen["munnar"]) == 1
    assert len(user_chosen["thekkady"]) == 1

    selected_munnar_place = user_chosen["munnar"][0]
    selected_thekkady_place = user_chosen["thekkady"][0]

    all_markdown = " ".join(m.value for m in at.markdown)
    assert selected_munnar_place in all_markdown
    assert selected_thekkady_place in all_markdown

def test_deselect_attraction_removes_from_itinerary():
    """Deselect an attraction and confirm it disappears from the generated itinerary."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    at.multiselect[0].set_value(["Munnar", "Thekkady"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Select 2 places for Munnar, run after each to persist to mc_chosen
    munnar_cbs = [cb for cb in at.checkbox if cb.key and "munnar" in cb.key]
    assert len(munnar_cbs) >= 2
    munnar_cbs[0].check().run()
    munnar_cbs = [cb for cb in at.checkbox if cb.key and "munnar" in cb.key]
    munnar_cbs[1].check().run()

    assert len(at.session_state["mc_chosen"]["munnar"]) == 2
    deselected_place = at.session_state["mc_chosen"]["munnar"][1]

    # Deselect the second place in Munnar
    munnar_cbs = [cb for cb in at.checkbox if cb.key and "munnar" in cb.key]
    munnar_cbs[1].uncheck().run()
    assert len(at.session_state["mc_chosen"]["munnar"]) == 1
    assert deselected_place not in at.session_state["mc_chosen"]["munnar"]

def test_validation_when_no_places_selected():
    """Verify validation warning when no attractions are selected for a city."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    at.multiselect[0].set_value(["Munnar", "Thekkady"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Ensure no attractions selected
    at.session_state["mc_chosen"] = {"munnar": []}

    # Click Find hotels near my picks
    hotel_btn = [b for b in at.button if "Find hotels near my picks" in b.label][0]
    hotel_btn.click().run()

    # Page must remain 3 (blocked) and warning displayed
    assert at.session_state["page"] == 3
    assert len(at.warning) > 0
    assert any("Please select at least one attraction" in w.value for w in at.warning)

def test_reconcile_when_city_list_changes():
    """Verify valid selections for retained cities persist when city list changes."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()
    assert at.session_state["page"] == 2

    at.multiselect[0].set_value(["Munnar", "Alleppey"]).run()
    next_btn = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn.click().run()
    assert at.session_state["page"] == 3

    # Check a place in Munnar, then run so mc_chosen is updated
    munnar_cbs = [cb for cb in at.checkbox if cb.key and "munnar" in cb.key]
    munnar_cbs[0].check().run()
    selected_munnar = at.session_state["mc_chosen"]["munnar"][0]

    # Go back to Page 2 via sidebar button
    p2_btn = [b for b in at.button if "1. Plan Details" in b.label][0]
    p2_btn.click().run()
    assert at.session_state["page"] == 2

    # Change cities to Munnar and Thekkady
    at.multiselect[0].set_value(["Munnar", "Thekkady"]).run()
    next_btn2 = [b for b in at.button if "Next: Places & Attractions" in b.label][0]
    next_btn2.click().run()
    assert at.session_state["page"] == 3

    # Verify Munnar selection is still preserved
    assert "munnar" in at.session_state["mc_chosen"]
    assert selected_munnar in at.session_state["mc_chosen"]["munnar"]
