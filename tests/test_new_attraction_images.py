from streamlit.testing.v1 import AppTest

def test_newly_integrated_images():
    """Verify that newly integrated images render correctly in AppTest for respective cities."""
    # Test Goa - Gallery Gitanjali
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Goa"
    at.session_state["selected_city"] = "Goa"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Google Maps Contributor" in c for c in captions)

    # Test Delhi - National Gallery of Modern Art
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Delhi"
    at.session_state["selected_city"] = "Delhi"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Google Maps Contributor" in c for c in captions)

    # Test Jaipur - Shree Khole Ki Hanuman Mandir
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Rajasthan"
    at.session_state["selected_city"] = "Jaipur"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Instagram Contributor" in c for c in captions)

    # Test Hyderabad - Inorbit Mall & Infinite Adventure Club
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Telangana"
    at.session_state["selected_city"] = "Hyderabad"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Inorbit Mall" in c for c in captions)
    assert any("Infinite Adventure Club" in c for c in captions)

    # Test Chennai - Queensland & Covelong Beach & MGR Film City & Scuba Diving
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Tamil Nadu"
    at.session_state["selected_city"] = "Chennai"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Google Maps Contributor" in c for c in captions)
    assert any("Kerala Tours Operator India" in c for c in captions)
    assert any("Cyber Travel Inc." in c for c in captions)
    assert any("Thrillophilia Contributor" in c for c in captions)

    # Test Agra - Humayun's Mosque & Shah Market & TDI Mall & Kinari Bazar
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.session_state["selected_state"] = "Uttar Pradesh"
    at.session_state["selected_city"] = "Agra"
    at.session_state["page"] = 3
    at.session_state["step"] = 2
    at.run()
    captions = [c.value for c in at.caption]
    assert any("Google Maps Contributor" in c for c in captions)
    assert any("Instagram Contributor" in c for c in captions)
    assert any("Alamy Stock Photo" in c for c in captions)
