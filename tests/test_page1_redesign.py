from streamlit.testing.v1 import AppTest
import pytest

def test_page1_initial_state_and_elements():
    """Verify Page 1 loads by default, Single-City is selected, and no state/city selectbox is present."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Verify session state defaults
    assert at.session_state["page"] == 1
    assert at.session_state["trip_mode"] == "Single City"

    # Verify Trip Planning Mode radio is present and defaults to Single City
    assert len(at.radio) >= 1
    assert at.radio[0].value == "Single City"

    # Confirm NO state or city selectbox appears on Page 1
    assert len(at.selectbox) == 0

    # Verify Continue button is present
    continue_btns = [b for b in at.button if "Continue to Plan Details" in b.label]
    assert len(continue_btns) == 1

def test_page1_mode_selection_and_persistence():
    """Verify switching to Multi-City and navigating back preserves the mode."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Switch to Multi-City
    at.radio[0].set_value("Multi-City Trip (2 to 5 cities)").run()
    assert at.session_state["trip_mode"] == "Multi-City Trip (2 to 5 cities)"

    # Click Continue to Plan Details
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()

    # Now on Page 2 (Multi-City Route Setup)
    assert at.session_state["page"] == 2
    assert len(at.multiselect) >= 1  # Cities multiselect is on Page 2

    # Reset / Start Over in Sidebar
    reset_btns = [b for b in at.sidebar.button if "Reset / Start Over" in b.label]
    assert len(reset_btns) == 1
    reset_btns[0].click().run()

    # Verify we are back on Page 1
    assert at.session_state["page"] == 1

def test_page1_single_city_continue_to_plan_details():
    """Verify clicking Continue in Single-City mode navigates to Plan Details with destination selectbox."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Click Continue to Plan Details
    continue_btn = [b for b in at.button if "Continue to Plan Details" in b.label][0]
    continue_btn.click().run()

    # Now on Page 2
    assert at.session_state["page"] == 2
    assert at.session_state["step"] == 1

    # State & City selectboxes are now available on Page 2
    assert len(at.selectbox) >= 1
    assert "Goa" in at.selectbox[0].options
