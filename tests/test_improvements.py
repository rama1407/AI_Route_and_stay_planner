import os
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

def test_original_csvs_preserved():
    # Verify original files exist and row counts match original snapshot
    assert os.path.exists("attractions_geo.csv")
    assert len(pd.read_csv("attractions_geo.csv")) == 1110

    assert os.path.exists("hotels_final.csv")
    assert len(pd.read_csv("hotels_final.csv")) == 4000

    assert os.path.exists("cities.csv")
    assert len(pd.read_csv("cities.csv")) == 89

    assert os.path.exists("destination_links.csv")
    assert len(pd.read_csv("destination_links.csv")) == 1109

def test_attractions_supplement_schema():
    base = pd.read_csv("attractions_geo.csv")
    supp = pd.read_csv("attractions_supplement.csv")

    assert set(supp.columns) == set(base.columns)
    assert len(supp) == 4
    assert (supp["ckey"] == "munnar").all()

    # Check that each added attraction has valid coordinates and non-null metadata
    for _, r in supp.iterrows():
        assert 9.0 <= r["latitude"] <= 11.0 # In Kerala/Munnar latitude range
        assert 76.0 <= r["longitude"] <= 78.0 # In Kerala/Munnar longitude range
        assert 1.0 <= r["rating"] <= 5.0
        assert r["fee"] >= 0
        assert r["time_hours"] > 0
        assert pd.notna(r["description"])

def test_munnar_count_and_planner():
    base = pd.read_csv("attractions_geo.csv")
    supp = pd.read_csv("attractions_supplement.csv")
    combined = pd.concat([base, supp], ignore_index=True)

    munnar_places = combined[combined["ckey"] == "munnar"]
    assert len(munnar_places) == 8 # 4 original + 4 supplemented

def test_expander_removed_from_app():
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "How this planner works (the machine learning behind it)" not in content
    assert "st.expander" not in content

def test_limited_attraction_notice_in_ui():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Test Ajmer (which has 4 attractions < 8)
    at.session_state["selected_state"] = "Rajasthan"
    at.session_state["selected_city"] = "Ajmer"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    # Verify info message is displayed
    assert len(at.info) > 0
    assert any("Limited attraction data" in info.value for info in at.info)

def test_no_limited_notice_for_city_with_8_or_more():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # Test Munnar (now has 8 attractions)
    at.session_state["selected_state"] = "Kerala"
    at.session_state["selected_city"] = "Munnar"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    # Verify no limited attraction message is shown
    limited_notices = [info.value for info in at.info if "Limited attraction data" in info.value]
    assert len(limited_notices) == 0
