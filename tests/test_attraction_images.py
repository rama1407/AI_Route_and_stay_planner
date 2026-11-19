import os
import pathlib
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

def test_manifest_schema_and_integrity():
    manifest_path = pathlib.Path("attraction_image_manifest.csv")
    assert manifest_path.exists(), "attraction_image_manifest.csv must exist"
    
    df = pd.read_csv(manifest_path)
    required_cols = [
        "city", "attraction_name", "local_image_path", "original_image_title",
        "author", "source_file_page_url", "license_name", "license_url",
        "is_modified", "verification_status"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column in manifest: {col}"
    
    assert len(df) >= 40, f"Expected at least 40 attraction images in manifest, found {len(df)}"

def test_manifest_files_exist_and_non_empty():
    df = pd.read_csv("attraction_image_manifest.csv")
    for _, row in df.iterrows():
        path = pathlib.Path(row["local_image_path"])
        assert path.exists(), f"Image file does not exist: {path} for {row['attraction_name']} ({row['city']})"
        assert path.stat().st_size > 1000, f"Image file is empty or too small: {path}"

def test_pothamedu_viewpoint_image_present():
    df = pd.read_csv("attraction_image_manifest.csv")
    poth = df[(df["city"] == "munnar") & (df["attraction_name"] == "Pothamedu View Point")]
    assert len(poth) == 1, "Pothamedu View Point must be in the manifest"
    row = poth.iloc[0]
    assert "pothamedu" in row["local_image_path"].lower()
    assert pathlib.Path(row["local_image_path"]).exists()
    assert "Vasant944" in row["author"]
    assert "commons.wikimedia.org" in row["source_file_page_url"]

def test_all_ten_cities_covered():
    df = pd.read_csv("attraction_image_manifest.csv")
    cities_in_manifest = set(df["city"].str.strip().str.lower().unique())
    target_10 = ["munnar", "thekkady", "alleppey", "goa", "delhi", "mumbai", "hyderabad", "chennai", "jaipur", "agra"]
    for city in target_10:
        assert city in cities_in_manifest, f"City '{city}' must have at least one attraction image in the manifest"

def test_apptest_munnar_pothamedu_renders_photo():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.session_state["selected_state"] = "Kerala"
    at.session_state["selected_city"] = "Munnar"
    at.session_state["page"] = 3
    at.run()

    # Verify attribution caption for Vasant944 (Pothamedu View Point photographer)
    captions = [c.value for c in at.caption]
    assert any("Vasant944" in c for c in captions), f"Attribution for Pothamedu (Vasant944) not found in captions: {captions}"

def test_apptest_fallback_behavior():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    at.session_state["selected_state"] = "Kerala"
    at.session_state["selected_city"] = "Alleppey"
    at.session_state["page"] = 3
    at.run()

    # Alleppey has some attractions with fallback (e.g. Chakkulathukavu Sree Bhagwathi Temple)
    # and some with local photos (e.g. Alappuzha Beach, Backwaters)
    markdown_values = " ".join([m.value for m in at.markdown])
    assert "Image unavailable" in markdown_values, "Neutral fallback must appear for attractions without photo"
