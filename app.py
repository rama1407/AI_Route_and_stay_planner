import os, html, pathlib, base64, hashlib
import datetime as dt
from urllib.parse import quote_plus
import streamlit as st, pandas as pd
import numpy as np
from travel_checklist import render_travel_checklist

from planner_lib import hotels, nearby_hotels, plan_order, split_days, schedule, available_rooms, hav_km
from multi_city_planner import (
    optimise_city_order,
    allocate_leg_dates,
    estimate_road_km,
    estimate_transfer_hours,
    calculate_route_distance,
    schedule_with_transfer,
)
from pdf_generator import generate_itinerary_pdf

st.set_page_config(
    page_title="AI Travel Planner & Sightseeing Finder",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,400&family=Caveat:wght@600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
  background-color: #F7F0E2 !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  color: #1A2821 !important;
}

[data-testid="stSidebar"] {
  background-color: #F2ECE1 !important;
  border-right: 1px solid #DCE0D4 !important;
  padding: 1.2rem 0.8rem !important;
}
[data-testid="stSidebar"] hr {
  border-color: #DCE0D4 !important;
  margin: 14px 0 !important;
}

.block-container {
  max-width: 1100px !important;
  padding-top: 1.5rem !important;
  padding-bottom: 3.5rem !important;
}

/* Force Streamlit Header & Control Bar to be fully active and visible */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    visibility: visible !important;
    display: block !important;
    z-index: 999999 !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

/* When sidebar is collapsed (The expand button on top-left) */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 10px !important;
    left: 10px !important;
    z-index: 9999999 !important;
    background-color: #102F26 !important;
    border: 2px solid #D4A359 !important;
    border-radius: 8px !important;
    padding: 6px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
}

/* When sidebar is expanded (The collapse button inside/top of sidebar) */
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"] button {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background-color: #102F26 !important;
    border: 1.5px solid #D4A359 !important;
    border-radius: 8px !important;
    padding: 6px !important;
    z-index: 9999999 !important;
}

/* Force all toggle icons to render clearly in gold */
[data-testid="collapsedControl"] svg, 
button[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarHeader"] button svg {
    fill: #D4A359 !important;
    color: #D4A359 !important;
    width: 22px !important;
    height: 22px !important;
}

.hero-curved {
  background: linear-gradient(135deg, #102F26 0%, #173F32 100%);
  color: #FFFFFF;
  padding: 24px 36px 22px;
  border-radius: 0 0 32px 32px;
  margin: -1.0rem -1rem 22px -1rem;
  box-shadow: 0 10px 28px rgba(16, 47, 38, 0.20);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.hero-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.hero-left {
  flex: 1 1 520px;
}
.hero-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}
.hero-title {
  margin: 0;
  color: #FFFFFF !important;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.85rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.2;
}
.hero-tagline {
  margin: 4px 0 0;
  color: #D8E4DC;
  font-size: 0.95rem;
  font-weight: 400;
  opacity: 0.95;
}
.hero-right {
  flex: 0 0 260px;
  position: relative;
  min-height: 115px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
.hero-collage {
  position: relative;
  width: 250px;
  height: 115px;
}
.collage-card {
  position: absolute;
  border-radius: 8px;
  border: 2.5px solid #FFFFFF;
  box-shadow: 0 6px 20px rgba(0,0,0,0.30);
  object-fit: cover;
}
.c-card-1 { width: 125px; height: 85px; top: 8px; left: 0px; transform: rotate(-4deg); z-index: 1; }
.c-card-2 { width: 110px; height: 75px; top: 0px; right: 8px; transform: rotate(5deg); z-index: 2; }
.c-card-3 { width: 115px; height: 72px; bottom: 0px; right: 20px; transform: rotate(-3deg); z-index: 3; }
.script-tag-hero {
  position: absolute;
  top: 24px;
  left: 80px;
  font-family: 'Caveat', cursive;
  font-size: 1.25rem;
  color: #FFFFFF;
  line-height: 1.05;
  text-shadow: 0 2px 6px rgba(0,0,0,0.70);
  transform: rotate(-6deg);
  z-index: 4;
}

.page-sec-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}
.page-sec-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.55rem;
  font-weight: 800;
  color: #102F26;
  margin: 0;
  line-height: 1.2;
}
.page-sec-sub {
  color: #5C6B62;
  font-size: 0.92rem;
  margin-bottom: 18px;
  padding-left: 28px;
}

button[kind="primary"], div.stButton > button[kind="primary"], div.stButton > button[type="primary"] {
  background-color: #C45D3A !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 0.98rem !important;
  padding: 12px 24px !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 4px 14px rgba(196, 93, 58, 0.25) !important;
}
button[kind="primary"]:hover, div.stButton > button[kind="primary"]:hover {
  background-color: #A84D2E !important;
  box-shadow: 0 6px 18px rgba(196, 93, 58, 0.35) !important;
  transform: translateY(-1px);
}
button[kind="secondary"], div.stButton > button {
  background-color: #FFFFFF !important;
  color: #102F26 !important;
  border: 1px solid #D0D5C7 !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  padding: 8px 18px !important;
  transition: all 0.2s ease !important;
}
button[kind="secondary"]:hover, div.stButton > button:hover {
  background-color: #E7EFE9 !important;
  border-color: #102F26 !important;
}

div[data-testid="stDownloadButton"] > button {
  background-color: #C45D3A !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 1.05rem !important;
  padding: 14px 28px !important;
  width: 100% !important;
  box-shadow: 0 4px 16px rgba(196, 93, 58, 0.30) !important;
}

.city-sugg-card {
  background: #FFFFFF;
  border: 1px solid #DCE0D4;
  border-radius: 12px;
  overflow: hidden;
  text-align: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(16,47,38,0.04);
}
.city-sugg-card:hover {
  border-color: #C45D3A;
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(16,47,38,0.10);
}
.city-sugg-img {
  width: 100%;
  height: 95px;
  object-fit: cover;
}
.city-sugg-name {
  padding: 6px 8px 8px;
  font-weight: 700;
  font-size: 0.90rem;
  color: #102F26;
}

.chip {
  display: inline-block;
  color: #FFFFFF;
  padding: 2.5px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  margin: 2px 3px 4px 0;
  line-height: 1.4;
}

.sidebar-poster {
  border-radius: 14px;
  overflow: hidden;
  position: relative;
  margin-top: 18px;
  box-shadow: 0 6px 18px rgba(16,47,38,0.12);
}
.sidebar-poster-img {
  width: 100%;
  height: 230px;
  object-fit: cover;
  display: block;
}
.sidebar-poster-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, rgba(16,47,38,0.88) 0%, rgba(16,47,38,0.2) 75%, transparent 100%);
  padding: 24px 14px 14px;
  color: #FFFFFF;
}
.sidebar-poster-text {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.25rem;
  font-weight: 800;
  line-height: 1.15;
}

.sidebar-selection-box {
  background: #FFFFFF;
  border: 1px solid #DCE0D4;
  border-radius: 12px;
  padding: 12px 14px;
  margin-top: 14px;
  font-size: 0.82rem;
  color: #33443B;
}
.sidebar-selection-box h4 {
  font-size: 0.92rem;
  font-weight: 700;
  color: #102F26;
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.sidebar-sel-row {
  margin-bottom: 5px;
  line-height: 1.35;
}
.sidebar-sel-row strong {
  color: #102F26;
}

.attr-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
  color: #617066;
  margin-bottom: 6px;
}

.hotel-name-h {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.2rem;
  font-weight: 700;
  color: #102F26;
  margin-bottom: 4px;
}
.hotel-addr {
  font-size: 0.82rem;
  color: #5A6960;
  margin: 5px 0 3px;
}
.hotel-amenities {
  font-size: 0.78rem;
  color: #6C7A72;
  margin-bottom: 6px;
}

.itinerary-outdated {
  background: #FFF7E6;
  border: 1.5px solid #E8C84A;
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 16px;
  color: #8A6A00;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
  font-size: 0.92rem;
}

.sched-day-header {
  background: linear-gradient(135deg, #102F26 0%, #173F32 100%);
  color: #FFFFFF;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.95rem;
  display: inline-block;
  margin-bottom: 12px;
}
.sched-timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 8px 0;
  border-bottom: 1px dashed #E5E2D8;
}
.sched-time {
  flex: 0 0 140px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #173F32;
}
.sched-what {
  flex: 1 1 auto;
  font-size: 0.88rem;
  font-weight: 700;
  color: #102F26;
}
.sched-transfer {
  flex: 0 0 120px;
  font-size: 0.78rem;
  color: #5C6B62;
  text-align: right;
}

.budget-cell {
  background: #FDFBF7;
  border: 1px solid #E5DFD3;
  border-radius: 10px;
  padding: 10px 12px;
  text-align: center;
}
.budget-cell-label {
  font-size: 0.72rem;
  color: #5C6B62;
  font-weight: 600;
  text-transform: uppercase;
}
.budget-cell-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: #102F26;
  margin-top: 2px;
}
.budget-cell-total {
  background: #F7EFE9;
  border-color: #C45D3A;
}
.budget-cell-total .budget-cell-val {
  color: #C45D3A;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Data Loading & Enrichment
# ══════════════════════════════════════════════════════════════════════════════
cities = pd.read_csv("cities.csv", index_col=0)
if os.path.exists("cities_supplement.csv"):
    csupp = pd.read_csv("cities_supplement.csv", index_col=0)
    cities = pd.concat([cities, csupp])
    cities = cities[~cities.index.duplicated(keep="last")]

places = pd.read_csv("attractions_geo.csv")
if os.path.exists("attractions_supplement.csv"):
    supp = pd.read_csv("attractions_supplement.csv")
    places = pd.concat([places, supp], ignore_index=True).drop_duplicates(subset=["ckey", "name"])

for ckey, cnt in places.groupby("ckey").size().items():
    if ckey in cities.index:
        cities.loc[ckey, "n"] = cnt
        cities.loc[ckey, "max_days"] = max(1, min(7, cnt // 3))

if os.path.exists("image_override.csv"):
    ov = pd.read_csv("image_override.csv").drop_duplicates("name").set_index("name")["image"]
    places["image"] = places["name"].map(ov).fillna(places["image"])
if os.path.exists("image_links.csv"):
    il = pd.read_csv("image_links.csv").drop_duplicates("place_id").set_index("place_id")["image_url"]
    places["image"] = places["image"].fillna((places["ckey"] + "|" + places["name"]).map(il))

dl_frames = []
if os.path.exists("destination_links.csv"):
    dl_frames.append(pd.read_csv("destination_links.csv"))
if os.path.exists("destination_links_supplement.csv"):
    dl_frames.append(pd.read_csv("destination_links_supplement.csv"))
if dl_frames:
    dl = pd.concat(dl_frames, ignore_index=True).drop_duplicates("place_id").set_index("place_id")
else:
    dl = pd.DataFrame(columns=["url", "source_type"])

LABEL = {"official": "Official Website", "wikipedia": "Wikipedia", "search": "Search Destination"}

def dest_link(ckey, name):
    k = f"{ckey}|{name}"
    if k in dl.index:
        return dl.loc[k, "url"], LABEL.get(dl.loc[k, "source_type"], "Search Destination")
    return "https://en.wikipedia.org/wiki/Special:Search?search=" + quote_plus(f"{name} {ckey.title()} India"), "Search Destination"

CAT = {
    "Natural Landscapes & Wildlife":          ("🏞️", "#1B7F4A", "#8FE0B0", "Nature"),
    "Religious & Spiritual Pilgrimages":      ("🕉️", "#C2610C", "#F7C58B", "Spiritual"),
    "Cultural & Heritage Sites":              ("🏛️", "#6B3FBC", "#CBB4F5", "Heritage"),
    "Adventure & Outdoor Activities":         ("🧗", "#C0392B", "#F5A59B", "Adventure"),
    "Shopping & Markets":                     ("🛍️", "#C2185B", "#F7A8CF", "Shopping"),
    "Sightseeing & Exploration":              ("🗺️", "#1565C0", "#9CCBFA", "Sightseeing"),
    "Arts, Science & Literature Attractions": ("🔬", "#00796B", "#8FDCCB", "Arts & Science"),
    "Sports & Recreation":                    ("🏏", "#E65100", "#F9D68E", "Sports"),
    "Culinary & Food Experiences":            ("🍲", "#BF360C", "#F2B089", "Food"),
}
TIERS = {"All Stays": None, "Luxury": "Premium", "Premium": "Premium", "Standard": "Unrated / Small", "Budget": "Low-rated"}
TIER_COLOR = {"Luxury": "#8E44AD", "Premium": "#B8860B", "Standard": "#0E7C7B", "Budget": "#607D8B"}

CITY_TO_STATE = {
    'Agra': 'Uttar Pradesh', 'Ahmedabad': 'Gujarat', 'Ajmer': 'Rajasthan',
    'Allahabad': 'Uttar Pradesh', 'Alleppey': 'Kerala', 'Amritsar': 'Punjab',
    'Auli': 'Uttarakhand', 'Aurangabad': 'Maharashtra', 'Bangalore': 'Karnataka',
    'Bhopal': 'Madhya Pradesh', 'Bhuj': 'Gujarat', 'Bodh Gaya': 'Bihar',
    'Chandigarh': 'Punjab', 'Chennai': 'Tamil Nadu', 'Chikmagalur': 'Karnataka',
    'Coimbatore': 'Tamil Nadu', 'Coorg': 'Karnataka', 'Cuttack': 'Odisha',
    'Dalhousie': 'Himachal Pradesh', 'Darjeeling': 'West Bengal', 'Dehradun': 'Uttarakhand',
    'Delhi': 'Delhi', 'Dwarka': 'Gujarat', 'Ernakulam': 'Kerala',
    'Gandhinagar': 'Gujarat', 'Gangtok': 'Sikkim', 'Goa': 'Goa',
    'Gurgaon': 'Haryana', 'Guwahati': 'Assam', 'Gwalior': 'Madhya Pradesh',
    'Hampi': 'Karnataka', 'Haridwar': 'Uttarakhand', 'Havelock Island': 'Andaman & Nicobar Islands',
    'Hyderabad': 'Telangana', 'Indore': 'Madhya Pradesh', 'Jabalpur': 'Madhya Pradesh',
    'Jaipur': 'Rajasthan', 'Jaisalmer': 'Rajasthan', 'Kanpur': 'Uttar Pradesh',
    'Kanyakumari': 'Tamil Nadu', 'Khajuraho': 'Madhya Pradesh', 'Kodaikanal': 'Tamil Nadu',
    'Kohima': 'Nagaland', 'Kolhapur': 'Maharashtra', 'Kolkata': 'West Bengal',
    'Kozhikode': 'Kerala', 'Kullu': 'Himachal Pradesh', 'Leh': 'Ladakh',
    'Lonavala': 'Maharashtra', 'Lucknow': 'Uttar Pradesh', 'Madurai': 'Tamil Nadu',
    'Mahabalipuram': 'Tamil Nadu', 'Manali': 'Himachal Pradesh', 'Mangalore': 'Karnataka',
    'Matheran': 'Maharashtra', 'Mathura': 'Uttar Pradesh', 'Meerut': 'Uttar Pradesh',
    'Mumbai': 'Maharashtra', 'Munnar': 'Kerala', 'Mussoorie': 'Uttarakhand',
    'Mysore': 'Karnataka', 'Nagpur': 'Maharashtra', 'Nainital': 'Uttarakhand',
    'Namchi': 'Sikkim', 'Noida': 'Uttar Pradesh', 'Patna': 'Bihar',
    'Pelling': 'Sikkim', 'Port Blair': 'Andaman & Nicobar Islands', 'Puducherry': 'Puducherry',
    'Pune': 'Maharashtra', 'Puri': 'Odisha', 'Ranchi': 'Jharkhand',
    'Ranikhet': 'Uttarakhand', 'Ravangla': 'Sikkim', 'Rishikesh': 'Uttarakhand',
    'Satara': 'Maharashtra', 'Shimla': 'Himachal Pradesh', 'Siliguri': 'West Bengal',
    'Srinagar': 'Jammu & Kashmir', 'Thekkady': 'Kerala', 'Thiruvananthapuram': 'Kerala',
    'Udaipur': 'Rajasthan', 'Ujjain': 'Madhya Pradesh', 'Uttarkashi': 'Uttarakhand',
    'Vadodara': 'Gujarat', 'Varanasi': 'Uttar Pradesh', 'Vijayawada': 'Andhra Pradesh',
    'Visakhapatnam': 'Andhra Pradesh', 'Vrindavan': 'Uttar Pradesh', 'Wayanad': 'Kerala'
}
ALL_STATES = sorted(list(set(CITY_TO_STATE.values())))

@st.cache_data
def get_image_data_uri(rel_path: str) -> str:
    p = pathlib.Path(__file__).parent / rel_path
    if p.exists():
        ext = p.suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/webp"
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return ""

_ATTR_MANIFEST_PATH = pathlib.Path(__file__).parent / "attraction_image_manifest.csv"
_attr_manifest = {}
if _ATTR_MANIFEST_PATH.exists():
    try:
        _mdf = pd.read_csv(_ATTR_MANIFEST_PATH)
        for _, _row in _mdf.iterrows():
            _c = str(_row.get("city", "")).strip().lower()
            _a = str(_row.get("attraction_name", "")).strip()
            _attr_manifest[(_c, _a)] = _row.to_dict()
    except Exception:
        pass

# --- FAST IMAGE RESOLVER (Returns direct local paths for native st.image rendering) ---
@st.cache_data
def _resolve_attraction_img(city_key: str, name_str: str, raw_img_val: str):
    m_info = _attr_manifest.get((city_key, name_str))
    if not m_info:
        for (_mc, _ma), _val in _attr_manifest.items():
            if _mc == city_key and _ma.strip().lower() == name_str.strip().lower():
                m_info = _val
                break
    if m_info:
        local_rel = str(m_info.get("local_image_path", "")).strip()
        if local_rel:
            local_p = pathlib.Path(__file__).parent / local_rel
            if local_p.exists() and local_p.is_file() and local_p.stat().st_size > 0:
                lic_name = m_info.get("license_name", "CC BY-SA")
                author = m_info.get("author", "Wikimedia Commons")
                return str(local_p), f"📷 {lic_name} • {author}", True

    if isinstance(raw_img_val, str) and raw_img_val.strip().startswith("http"):
        return raw_img_val.strip(), "📷 Wikipedia / Wikimedia Commons", True

    return "", "", False

def get_attraction_image_info(r, ckey=None):
    city_key = str(ckey or getattr(r, "ckey", "")).strip().lower()
    name_str = str(getattr(r, "name", "")).strip()
    raw_img = getattr(r, "image", None)
    return _resolve_attraction_img(city_key, name_str, str(raw_img) if raw_img else "")

_CITY_IMG_DIR = pathlib.Path(__file__).parent / "assets" / "city_images"
_CITY_IMAGE_FILES = {
    "agra": "agra.jpg", "jaipur": "jaipur.jpg", "munnar": "munnar.jpg",
    "goa": "goa.jpg", "delhi": "delhi.jpg", "mumbai": "mumbai.jpg",
    "chennai": "chennai.jpg", "hyderabad": "hyderabad.jpg",
    "alleppey": "alleppey.jpg", "thekkady": "thekkady.jpg",
    "udaipur": "jaipur.jpg",
    "kolkata": "delhi.jpg"
}

def get_city_image_path(city_name: str) -> str:
    key = city_name.strip().lower()
    fname = _CITY_IMAGE_FILES.get(key, "jaipur.jpg")
    p = _CITY_IMG_DIR / fname
    return str(p) if p.exists() else ""

# Preload base64 images for hero collages
img_munnar = get_image_data_uri("assets/city_images/munnar.jpg")
img_jaipur = get_image_data_uri("assets/city_images/jaipur.jpg")
img_alleppey = get_image_data_uri("assets/city_images/alleppey.jpg")
img_agra = get_image_data_uri("assets/city_images/agra.jpg")
img_goa = get_image_data_uri("assets/city_images/goa.jpg")
img_delhi = get_image_data_uri("assets/city_images/delhi.jpg")

COMPASS_SVG = '''<svg width="38" height="38" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;flex-shrink:0;">
  <circle cx="50" cy="50" r="46" fill="#FDFBF7" stroke="#D4A359" stroke-width="6"/>
  <circle cx="50" cy="50" r="40" stroke="#E5C388" stroke-width="1.5" stroke-dasharray="3 3"/>
  <polygon points="50,15 56,45 50,50" fill="#C45D3A"/>
  <polygon points="50,15 44,45 50,50" fill="#E27D5B"/>
  <polygon points="50,85 56,55 50,50" fill="#173F32"/>
  <polygon points="50,85 44,55 50,50" fill="#2E7D63"/>
  <polygon points="85,50 55,56 50,50" fill="#D4A359"/>
  <polygon points="85,50 55,44 50,50" fill="#F3D197"/>
  <polygon points="15,50 45,56 50,50" fill="#D4A359"/>
  <polygon points="15,50 45,44 50,50" fill="#F3D197"/>
  <circle cx="50" cy="50" r="6" fill="#102F26" stroke="#D4A359" stroke-width="2"/>
</svg>'''

for _ckey in cities.index:
    cat_key = f"p3_c_{_ckey}"
    if cat_key not in st.session_state:
        st.session_state[cat_key] = "All"

if "page" not in st.session_state:
    st.session_state["page"] = 1
if "trip_mode" not in st.session_state:
    st.session_state["trip_mode"] = "Single City"
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "mc_step" not in st.session_state:
    st.session_state["mc_step"] = 1

if "selected_state" not in st.session_state:
    st.session_state["selected_state"] = "Uttar Pradesh"
if "selected_city" not in st.session_state:
    st.session_state["selected_city"] = "Agra"
if "city" not in st.session_state:
    st.session_state["city"] = "Agra"
if "ckey" not in st.session_state:
    st.session_state["ckey"] = "agra"
if "people" not in st.session_state:
    st.session_state["people"] = 2
if "budget_range" not in st.session_state:
    st.session_state["budget_range"] = "₹10,000 – ₹20,000"
if "chosen" not in st.session_state:
    st.session_state["chosen"] = []
if "hotel" not in st.session_state:
    st.session_state["hotel"] = None

if "mc_selected_cities" not in st.session_state:
    st.session_state["mc_selected_cities"] = ["Jaipur", "Udaipur", "Munnar"]
if "mc_active_city" not in st.session_state:
    st.session_state["mc_active_city"] = "Jaipur"
if "mc_chosen" not in st.session_state:
    st.session_state["mc_chosen"] = {}
if "mc_hotels" not in st.session_state:
    st.session_state["mc_hotels"] = {}
if "mc_people" not in st.session_state:
    st.session_state["mc_people"] = 2
if "mc_budget_range" not in st.session_state:
    st.session_state["mc_budget_range"] = "₹20,000 – ₹40,000"

if "itinerary_fingerprint" not in st.session_state:
    st.session_state["itinerary_fingerprint"] = ""
if "itinerary_dirty" not in st.session_state:
    st.session_state["itinerary_dirty"] = False

if "_preserved_widget_values" not in st.session_state:
    st.session_state["_preserved_widget_values"] = {}
for _k, _v in list(st.session_state["_preserved_widget_values"].items()):
    if _k not in st.session_state:
        st.session_state[_k] = _v

current_page = st.session_state["page"]
trip_mode = st.session_state["trip_mode"]

def compute_selections_fingerprint() -> str:
    if "Single" in trip_mode:
        s = f"{st.session_state.get('city')}|{st.session_state.get('check_in')}|{st.session_state.get('nights')}|{st.session_state.get('people')}|{sorted(st.session_state.get('chosen', []))}|{st.session_state.get('hotel')}"
    else:
        mc_c = st.session_state.get("mc_selected_cities", [])
        mc_ch = {k: sorted(v) for k, v in st.session_state.get("mc_chosen", {}).items()}
        mc_ht = st.session_state.get("mc_hotels", {})
        s = f"{mc_c}|{st.session_state.get('mc_start')}|{st.session_state.get('mc_people')}|{mc_ch}|{mc_ht}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def mark_dirty_if_changed():
    fp = compute_selections_fingerprint()
    if st.session_state.get("itinerary_fingerprint") and fp != st.session_state.get("itinerary_fingerprint"):
        st.session_state["itinerary_dirty"] = True

def render_curved_hero(title: str, subtitle: str):
    st.markdown(
        f'''<div class="hero-curved">
          <div class="hero-inner">
            <div class="hero-left">
              <div class="hero-title-row">
                {COMPASS_SVG}
                <h1 class="hero-title">{title}</h1>
              </div>
              <p class="hero-tagline">{subtitle}</p>
            </div>
            <div class="hero-right">
              <div class="hero-collage">
                <div class="script-tag-hero">Explore<br>Plan<br>Travel</div>
                <img class="collage-card c-card-1" src="{img_agra}" alt="Agra Taj" />
                <img class="collage-card c-card-2" src="{img_jaipur}" alt="Jaipur Palace" />
                <img class="collage-card c-card-3" src="{img_munnar}" alt="Munnar Hills" />
              </div>
            </div>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

if current_page != 1:
    with st.sidebar:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
            f'{COMPASS_SVG}'
            f'<div><div style="font-size:1.1rem;font-weight:800;color:#102F26;font-family:\'Playfair Display\',serif;">Trip Navigator</div>'
            f'<div style="font-size:0.75rem;color:#5C6B62;">AI Route &amp; Stay Planner</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("📅  1. Plan Details", width="stretch", type="primary" if current_page == 2 else "secondary", key="nav_plan_details"):
            st.session_state["page"] = 2
            st.session_state["step"] = 1
            st.session_state["mc_step"] = 1
            st.rerun()

        if st.button("📍  2. Places & Attractions", width="stretch", type="primary" if current_page == 3 else "secondary", key="nav_places_attractions"):
            st.session_state["page"] = 3
            st.session_state["step"] = 2
            st.session_state["mc_step"] = 2
            st.rerun()

        if current_page == 3 and "Multi-City" in trip_mode:
            st.markdown('<div style="margin:-4px 0 8px 12px;border-left:2px solid #C45D3A;padding-left:8px;">', unsafe_allow_html=True)
            for c_sub in st.session_state.get("mc_selected_cities", []):
                is_active = (c_sub == st.session_state.get("mc_active_city"))
                lbl = f"📍 {c_sub} {'✓' if is_active else ''}"
                if st.button(lbl, key=f"sb_city_p3_{c_sub}", width="stretch", type="primary" if is_active else "secondary"):
                    st.session_state["mc_active_city"] = c_sub
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🛏️  3. Hotels & Stays", width="stretch", type="primary" if current_page == 4 else "secondary", key="nav_hotels_stays"):
            st.session_state["page"] = 4
            st.session_state["step"] = 3
            st.session_state["mc_step"] = 3
            st.rerun()

        if current_page == 4 and "Multi-City" in trip_mode:
            st.markdown('<div style="margin:-4px 0 8px 12px;border-left:2px solid #C45D3A;padding-left:8px;">', unsafe_allow_html=True)
            for c_sub in st.session_state.get("mc_selected_cities", []):
                is_active = (c_sub == st.session_state.get("mc_active_city"))
                lbl = f"📍 {c_sub} {'✓' if is_active else ''}"
                if st.button(lbl, key=f"sb_city_p4_{c_sub}", width="stretch", type="primary" if is_active else "secondary"):
                    st.session_state["mc_active_city"] = c_sub
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🗺️  4. My Itinerary & Map", width="stretch", type="primary" if current_page == 5 else "secondary", key="nav_itinerary_map"):
            st.session_state["page"] = 5
            st.session_state["step"] = 4
            st.session_state["mc_step"] = 3
            st.rerun()
            
        if st.button("🧳  5. Smart Travel Checklist", width="stretch", type="primary" if current_page == 6 else "secondary", key="nav_travel_checklist"):
            st.session_state["page"] = 6
            st.rerun()

        if current_page == 2:
            st.markdown(
                f'''<div class="sidebar-poster">
                  <img class="sidebar-poster-img" src="{img_jaipur}" alt="Good Trips Create Stories" />
                  <div class="sidebar-poster-overlay">
                    <div class="sidebar-poster-text">Good<br>Trips<br>Create<br>Stories</div>
                  </div>
                </div>''',
                unsafe_allow_html=True,
            )
        else:
            c_mode = "Single-City" if "Single" in trip_mode else "Multi-City"
            if "Single" in trip_mode:
                cur_city = st.session_state.get("selected_city", "Agra")
                cur_state = st.session_state.get("selected_state", CITY_TO_STATE.get(cur_city, "India"))
                c_in = st.session_state.get("check_in", dt.date.today() + dt.timedelta(days=30))
                c_nights = st.session_state.get("nights", 2)
                c_out = c_in + dt.timedelta(days=c_nights)
                dates_str = f"{c_in:%d %b %Y} – {c_out:%d %b %Y} ({c_nights + 1} days)"
                ppl = st.session_state.get("people", 2)
                bdgt = st.session_state.get("budget_range", "₹10,000 – ₹20,000")

                st.markdown(
                    f'''<div class="sidebar-selection-box">
                      <h4>📍 Current Selection</h4>
                      <div class="sidebar-sel-row"><strong>Trip Mode:</strong> {c_mode}</div>
                      <div class="sidebar-sel-row"><strong>State:</strong> {cur_state}</div>
                      <div class="sidebar-sel-row"><strong>City:</strong> {cur_city}</div>
                      <div class="sidebar-sel-row"><strong>Travel Dates:</strong> {dates_str}</div>
                      <div class="sidebar-sel-row"><strong>Travellers:</strong> {ppl}</div>
                      <div class="sidebar-sel-row"><strong>Budget:</strong> {bdgt}</div>
                    </div>''',
                    unsafe_allow_html=True,
                )
            else:
                mc_cities = st.session_state.get("mc_selected_cities", ["Jaipur", "Udaipur", "Munnar"])
                mc_states = sorted(list(set(CITY_TO_STATE.get(c, "India") for c in mc_cities)))
                mc_st_dt = st.session_state.get("mc_start", dt.date.today() + dt.timedelta(days=30))
                tot_n = len(mc_cities) * 2
                mc_end_dt = mc_st_dt + dt.timedelta(days=tot_n)
                dates_str = f"{mc_st_dt:%d %b %Y} – {mc_end_dt:%d %b %Y} ({tot_n} days)"
                ppl = st.session_state.get("mc_people", 2)
                bdgt = st.session_state.get("mc_budget_range", "₹20,000 – ₹40,000")

                st.markdown(
                    f'''<div class="sidebar-selection-box">
                      <h4>📍 Current Selection</h4>
                      <div class="sidebar-sel-row"><strong>Trip Mode:</strong> {c_mode}</div>
                      <div class="sidebar-sel-row"><strong>States:</strong> {', '.join(mc_states)}</div>
                      <div class="sidebar-sel-row"><strong>Cities:</strong> {', '.join(mc_cities)}</div>
                      <div class="sidebar-sel-row"><strong>Travel Dates:</strong> {dates_str}</div>
                      <div class="sidebar-sel-row"><strong>Travellers:</strong> {ppl}</div>
                      <div class="sidebar-sel-row"><strong>Budget:</strong> {bdgt}</div>
                    </div>''',
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        if st.button("↺ Reset / Start Over", width="stretch", key="reset_start_over_btn"):
            st.session_state.clear()
            st.session_state["page"] = 1
            st.session_state["trip_mode"] = "Single City"
            st.rerun()

if current_page == 1:
    st.markdown("""
    <style>
    .main .block-container {
        max-width: 1040px !important;
        margin: 0 auto !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f'''<div class="hero-curved">
          <div class="hero-inner">
            <div class="hero-left">
              <div class="hero-title-row">
                {COMPASS_SVG}
                <h1 class="hero-title">AI Travel Planner & Sightseeing Finder</h1>
              </div>
              <p class="hero-tagline">Curated itineraries, handpicked stays &amp; intelligent route discovery</p>
              <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;">
                <span style="font-size:0.82rem;font-weight:600;color:#E2ECE5;">📖 Personalized Itineraries</span>
                <span style="font-size:0.82rem;font-weight:600;color:#E2ECE5;">🛏️ Recommended Stays</span>
                <span style="font-size:0.82rem;font-weight:600;color:#E2ECE5;">📍 Optimized Routes</span>
                <span style="font-size:0.82rem;font-weight:600;color:#E2ECE5;">🍃 Explore India</span>
              </div>
            </div>
            <div class="hero-right">
              <div class="hero-collage">
                <div class="script-tag-hero">Discover<br>Plan<br>Explore</div>
                <img class="collage-card c-card-1" src="{img_munnar}" alt="Munnar Hills" />
                <img class="collage-card c-card-2" src="{img_jaipur}" alt="Amber Fort Jaipur" />
                <img class="collage-card c-card-3" src="{img_alleppey}" alt="Alleppey Backwaters" />
              </div>
            </div>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '''<div style="font-size:1.45rem;font-weight:800;color:#102F26;border-left:4px solid #C45D3A;padding-left:12px;margin-bottom:4px;font-family:'Playfair Display',serif;">Start Your Journey</div>
            <div style="color:#5C6B62;font-size:0.92rem;margin-bottom:18px;padding-left:16px;">Choose your trip type and start planning your perfect journey across India.</div>''',
            unsafe_allow_html=True,
        )

        cur_m = st.session_state.get("trip_mode", "Single City")
        def_idx = 0 if "Single" in cur_m else 1

        selected_mode = st.radio(
            "Trip Planning Mode",
            ["Single City", "Multi-City Trip (2 to 5 cities)"],
            index=def_idx,
            format_func=lambda x: "🏛️  **Single-City Trip**\nExplore one city in detail" if "Single" in x else "📍  **Multi-City Trip**\nExplore multiple cities across India",
            horizontal=True,
            key="landing_trip_mode_radio",
        )
        st.session_state["trip_mode"] = selected_mode

        if st.button("Continue to Plan Details →", type="primary", width="stretch"):
            st.session_state["trip_mode"] = selected_mode
            st.session_state["page"] = 2
            st.session_state["step"] = 1
            st.session_state["mc_step"] = 1
            st.rerun()

    st.markdown(
        '''<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:20px;padding-top:16px;border-top:1px solid #DCE0D4;">
          <div style="text-align:center;padding:8px;">
            <div style="width:44px;height:44px;border-radius:50%;background:#E4ECE6;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:1.25rem;">🧭</div>
            <div style="font-weight:700;color:#102F26;font-size:0.92rem;">Handpicked Destinations</div>
            <div style="color:#637369;font-size:0.80rem;">Explore the best places across India</div>
          </div>
          <div style="text-align:center;padding:8px;">
            <div style="width:44px;height:44px;border-radius:50%;background:#E4ECE6;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:1.25rem;">🛏️</div>
            <div style="font-weight:700;color:#102F26;font-size:0.92rem;">Stay Recommendations</div>
            <div style="color:#637369;font-size:0.80rem;">Find quality stays for every budget</div>
          </div>
          <div style="text-align:center;padding:8px;">
            <div style="width:44px;height:44px;border-radius:50%;background:#E4ECE6;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:1.25rem;">🗺️</div>
            <div style="font-weight:700;color:#102F26;font-size:0.92rem;">Optimized Travel Routes</div>
            <div style="color:#637369;font-size:0.80rem;">Save time with smart itineraries</div>
          </div>
          <div style="text-align:center;padding:8px;">
            <div style="width:44px;height:44px;border-radius:50%;background:#E4ECE6;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:1.25rem;">🍃</div>
            <div style="font-weight:700;color:#102F26;font-size:0.92rem;">Tailored for You</div>
            <div style="color:#637369;font-size:0.80rem;">Plans based on your preferences</div>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )
    st.caption("Descriptions and images from Wikipedia / Wikimedia Commons (CC BY-SA). Hotel data is a past snapshot.")
    st.stop()

if current_page == 2:
    render_curved_hero("Plan Your Perfect Trip", "Discover · Plan · Explore · Enjoy")

    if "Single" in trip_mode:
        with st.container(border=True):
            st.markdown(
                '''<div class="page-sec-header">
                  <span style="font-size:1.45rem;">📍</span>
                  <h2 class="page-sec-title">Plan Details – Single-City Mode</h2>
                </div>
                <div class="page-sec-sub">Tell us about your trip to get personalized recommendations.</div>''',
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                cur_st = st.session_state.get("selected_state", "Uttar Pradesh")
                st_idx = ALL_STATES.index(cur_st) if cur_st in ALL_STATES else 0
                
                if "p2_state_sel" in st.session_state:
                    chosen_state = st.selectbox("📍 Select State", ALL_STATES, key="p2_state_sel")
                else:
                    chosen_state = st.selectbox("📍 Select State", ALL_STATES, index=st_idx, key="p2_state_sel")
                    
                st.session_state["_preserved_widget_values"]["p2_state_sel"] = chosen_state
                if chosen_state != cur_st:
                    st.session_state["selected_state"] = chosen_state
                    st.rerun()

            with c2:
                supported_in_state = sorted([c for c, s in CITY_TO_STATE.items() if s == chosen_state and c in cities["name"].values])
                if not supported_in_state:
                    supported_in_state = sorted(cities["name"].unique().tolist())
                cur_ct = st.session_state.get("selected_city", "Agra")
                ct_idx = supported_in_state.index(cur_ct) if cur_ct in supported_in_state else 0
                
                if "p2_city_sel" in st.session_state:
                    chosen_city = st.selectbox("🏛️ Select City", supported_in_state, key="p2_city_sel")
                else:
                    chosen_city = st.selectbox("🏛️ Select City", supported_in_state, index=ct_idx, key="p2_city_sel")
                    
                st.session_state["_preserved_widget_values"]["p2_city_sel"] = chosen_city
                st.session_state["selected_city"] = chosen_city
                st.session_state["city"] = chosen_city
                st.session_state["ckey"] = cities.index[cities["name"] == chosen_city][0]

            today = dt.date.today()
            def_in = st.session_state.get("check_in", today + dt.timedelta(days=30))
            def_nights = st.session_state.get("nights", 2)
            def_out = def_in + dt.timedelta(days=def_nights)

            dates = st.date_input("📅 Travel Dates", (def_in, def_out), min_value=today, key="p2_dates_input")
            st.session_state["_preserved_widget_values"]["p2_dates_input"] = dates
            ready_dates = (len(dates) == 2 and dates[1] > dates[0])
            if ready_dates:
                st.session_state["check_in"] = dates[0]
                st.session_state["nights"] = (dates[1] - dates[0]).days
                max_d = int(cities.loc[cities["name"] == chosen_city, "max_days"].iloc[0])
                st.session_state["days"] = min(st.session_state["nights"] + 1, max_d)

            ppl = st.number_input("👥 Number of Travellers", min_value=1, max_value=20, value=int(st.session_state.get("people", 2)), key="p2_people_input")
            st.session_state["people"] = ppl
            st.session_state["_preserved_widget_values"]["p2_people_input"] = ppl

            budget_opts = ["₹10,000 – ₹20,000", "₹20,000 – ₹40,000", "₹40,000 – ₹70,000", "₹70,000+"]
            cur_b = st.session_state.get("budget_range", "₹10,000 – ₹20,000")
            b_idx = budget_opts.index(cur_b) if cur_b in budget_opts else 0
            chosen_b = st.selectbox("💰 Budget Range (Optional)", budget_opts, index=b_idx, key="p2_budget_input")
            st.session_state["budget_range"] = chosen_b
            st.session_state["_preserved_widget_values"]["p2_budget_input"] = chosen_b

            st.markdown(
                '''<div style="margin:20px 0 8px;">
                  <div style="font-weight:700;color:#102F26;font-size:0.95rem;">💡 Quick City Suggestions</div>
                  <div style="color:#617066;font-size:0.80rem;">Popular destinations across India</div>
                </div>''',
                unsafe_allow_html=True,
            )
            sugg_cols = st.columns(5)
            sugg_list = [
                ("Agra", "Uttar Pradesh", img_agra),
                ("Jaipur", "Rajasthan", img_jaipur),
                ("Udaipur", "Rajasthan", img_jaipur),
                ("Munnar", "Kerala", img_munnar),
                ("Goa", "Goa", img_goa),
            ]
            for idx, (s_name, s_state, s_img) in enumerate(sugg_list):
                with sugg_cols[idx]:
                    st.markdown(
                        f'''<div class="city-sugg-card">
                          <img class="city-sugg-img" src="{s_img}" alt="{s_name}" />
                          <div class="city-sugg-name">{s_name}</div>
                        </div>''',
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Pick {s_name}", key=f"p2_pick_{s_name}", width="stretch"):
                        st.session_state["selected_state"] = s_state
                        st.session_state["selected_city"] = s_name
                        st.session_state["city"] = s_name
                        st.session_state["ckey"] = cities.index[cities["name"] == s_name][0]
                        mark_dirty_if_changed()
                        st.rerun()

            st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
            if st.button("Next: Places & Attractions →", type="primary", width="stretch", disabled=not ready_dates):
                mark_dirty_if_changed()
                st.session_state["page"] = 3
                st.session_state["step"] = 2
                st.rerun()

    else:
        with st.container(border=True):
            st.markdown(
                '''<div class="page-sec-header">
                  <span style="font-size:1.45rem;">📍</span>
                  <h2 class="page-sec-title">Plan Details – Multi-City Mode</h2>
                </div>
                <div class="page-sec-sub">Tell us about your trip to get personalized recommendations.</div>''',
                unsafe_allow_html=True,
            )

            all_cities_options = sorted(cities["name"].unique().tolist())
            cur_mc_cities = st.session_state.get("mc_selected_cities", ["Jaipur", "Udaipur", "Munnar"])
            cur_mc_cities = [c for c in cur_mc_cities if c in all_cities_options]
            if len(cur_mc_cities) < 2:
                cur_mc_cities = ["Jaipur", "Udaipur", "Munnar"]

            selected_cities = st.multiselect(
                "Select Cities (Add multiple cities)",
                all_cities_options,
                default=cur_mc_cities,
                key="p2_mc_cities_sel",
            )
            st.session_state["_preserved_widget_values"]["p2_mc_cities_sel"] = selected_cities
            if selected_cities != cur_mc_cities and len(selected_cities) >= 1:
                st.session_state["mc_selected_cities"] = selected_cities
                cur_mc_cities = selected_cities
                mark_dirty_if_changed()

            today = dt.date.today()
            def_start = st.session_state.get("mc_start", today + dt.timedelta(days=30))
            def_end = def_start + dt.timedelta(days=len(cur_mc_cities) * 2)
            mc_dates = st.date_input("📅 Travel Dates", (def_start, def_end), min_value=today, key="p2_mc_dates_in")
            st.session_state["_preserved_widget_values"]["p2_mc_dates_in"] = mc_dates
            ready_mc_dates = (len(mc_dates) == 2 and mc_dates[1] > mc_dates[0])
            if ready_mc_dates:
                st.session_state["mc_start"] = mc_dates[0]

            mc_ppl = st.number_input("👥 Number of Travellers", 1, 20, int(st.session_state.get("mc_people", 2)), key="p2_mc_ppl_in")
            st.session_state["mc_people"] = mc_ppl
            st.session_state["_preserved_widget_values"]["p2_mc_ppl_in"] = mc_ppl

            mc_budget_opts = ["₹20,000 – ₹40,000", "₹40,000 – ₹70,000", "₹70,000 – ₹1,20,000", "₹1,20,000+"]
            cur_mb = st.session_state.get("mc_budget_range", "₹20,000 – ₹40,000")
            mb_idx = mc_budget_opts.index(cur_mb) if cur_mb in mc_budget_opts else 0
            chosen_mb = st.selectbox("💰 Budget Range (Optional)", mc_budget_opts, index=mb_idx, key="p2_mc_budget_in")
            st.session_state["mc_budget_range"] = chosen_mb
            st.session_state["_preserved_widget_values"]["p2_mc_budget_in"] = chosen_mb

            st.markdown(
                '''<div style="margin:20px 0 8px;">
                  <div style="font-weight:700;color:#102F26;font-size:0.95rem;">💡 Quick City Suggestions</div>
                  <div style="color:#617066;font-size:0.80rem;">Popular destinations across India</div>
                </div>''',
                unsafe_allow_html=True,
            )
            mc_sugg_cols = st.columns(6)
            mc_suggs = [
                ("Jaipur", img_jaipur), ("Udaipur", img_jaipur), ("Munnar", img_munnar),
                ("Goa", img_goa), ("Kolkata", img_delhi), ("Delhi", img_delhi),
            ]
            for idx, (s_name, s_img) in enumerate(mc_suggs):
                with mc_sugg_cols[idx]:
                    st.markdown(
                        f'''<div class="city-sugg-card">
                          <img class="city-sugg-img" src="{s_img}" alt="{s_name}" />
                          <div class="city-sugg-name">{s_name}</div>
                        </div>''',
                        unsafe_allow_html=True,
                    )
                    if st.button(f"+ {s_name}", key=f"mc_add_{s_name}", width="stretch"):
                        if s_name not in cur_mc_cities:
                            cur_mc_cities.append(s_name)
                            st.session_state["mc_selected_cities"] = cur_mc_cities
                            mark_dirty_if_changed()
                            st.rerun()

            st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
            if st.button("Next: Places & Attractions →", type="primary", width="stretch", disabled=not ready_mc_dates or len(cur_mc_cities) < 2):
                mark_dirty_if_changed()
                st.session_state["mc_active_city"] = cur_mc_cities[0]
                st.session_state["page"] = 3
                st.session_state["mc_step"] = 2
                st.rerun()

elif current_page == 3:
    render_curved_hero("Places & Attractions", "Choose the places you want to include in your trip.")

    if "Single" in trip_mode:
        active_city = st.session_state.get("selected_city", "Agra")
    else:
        active_city = st.session_state.get("mc_active_city", st.session_state.get("mc_selected_cities", ["Jaipur"])[0])

    active_ckey = cities.index[cities["name"] == active_city][0]

    with st.container(border=True):
        st.markdown(
            f'''<div class="page-sec-header">
              <span style="font-size:1.45rem;">📍</span>
              <h2 class="page-sec-title">{active_city} – Places to Visit</h2>
            </div>
            <div class="page-sec-sub">Select the attractions you want to include in your itinerary.</div>''',
            unsafe_allow_html=True,
        )

        total_city_places = len(places[places["ckey"] == active_ckey])
        if total_city_places < 8:
            st.info(f"Limited attraction data for {active_city} ({total_city_places} places). You can explore all available spots below.")

        sc1, sc2 = st.columns([2, 3])
        with sc1:
            q_search = st.text_input("🔍 Search places (e.g., forts, temples, museums...)", key=f"p3_s_{active_ckey}").strip().lower()

        with sc2:
            cat_labels = ["All", "Heritage", "Nature", "Temples", "Museums", "Food", "Shopping"]
            if f"p3_c_{active_ckey}" not in st.session_state:
                st.session_state[f"p3_c_{active_ckey}"] = "All"
            sel_cat = st.radio("Category Filter", cat_labels, horizontal=True, label_visibility="collapsed", key=f"p3_c_{active_ckey}")

        city_places = places[places["ckey"] == active_ckey].copy()
        if q_search:
            city_places = city_places[city_places["name"].str.lower().str.contains(q_search) | city_places["description"].fillna("").str.lower().str.contains(q_search)]
        if sel_cat != "All":
            cat_map = {
                "Heritage": "Cultural & Heritage Sites",
                "Nature": "Natural Landscapes & Wildlife",
                "Temples": "Religious & Spiritual Pilgrimages",
                "Museums": "Arts, Science & Literature Attractions",
                "Food": "Culinary & Food Experiences",
                "Shopping": "Shopping & Markets"
            }
            if sel_cat in cat_map:
                city_places = city_places[city_places["primary_interest"] == cat_map[sel_cat]]

        city_places = city_places.sort_values("rating", ascending=False)

        if "Single" in trip_mode:
            current_chosen = st.session_state.get("chosen", [])
        else:
            if "mc_chosen" not in st.session_state:
                st.session_state["mc_chosen"] = {}
            current_chosen = st.session_state["mc_chosen"].get(active_ckey, [])

        display_places = city_places.head(12)
        cols = st.columns(3)
        for idx, r in enumerate(display_places.itertuples()):
            col_target = cols[idx % 3]
            with col_target:
                is_selected = (r.name in current_chosen)
                img_path, img_caption, has_img = get_attraction_image_info(r, active_ckey)
                short_info = CAT.get(getattr(r, "primary_interest", ""), ("🏛️", "#546E7A", "", "Heritage"))

                with st.container(border=True):
                    if has_img and img_path:
                        try:
                            st.image(img_path, width="stretch")
                        except Exception:
                            st.markdown(
                                f'<div style="height:110px;background:#EDE8DE;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#6A776F;font-size:1.6rem;margin-bottom:8px;">'
                                f'<span>{short_info[0]}</span></div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f'<div style="height:110px;background:#EDE8DE;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#6A776F;font-size:1.6rem;margin-bottom:8px;">'
                            f'<span>{short_info[0]}</span></div>',
                            unsafe_allow_html=True,
                        )

                    cb_key = f"cb_p3_{active_ckey}_{r.Index}"
                    if cb_key in st.session_state:
                        checked = st.checkbox(f"**{r.name}**", key=cb_key)
                    else:
                        checked = st.checkbox(f"**{r.name}**", value=is_selected, key=cb_key)

                    st.session_state["_preserved_widget_values"][cb_key] = checked

                    if checked != is_selected:
                        if checked and r.name not in current_chosen:
                            current_chosen.append(r.name)
                        elif not checked and r.name in current_chosen:
                            current_chosen.remove(r.name)

                        if "Single" in trip_mode:
                            st.session_state["chosen"] = current_chosen
                        else:
                            st.session_state["mc_chosen"][active_ckey] = current_chosen
                        mark_dirty_if_changed()

                    st.markdown(
                        f'<div class="attr-meta-row">'
                        f'<span>📍 {active_city}</span>'
                        f'<span>⭐ {getattr(r, "rating", 4.2)}</span>'
                        f'<span>⏱️ {getattr(r, "time_hours", 2.0)} h</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    badge_html = f'<span class="chip" style="background:{short_info[1]};">{short_info[3]}</span>'
                    st.markdown(badge_html, unsafe_allow_html=True)

                    desc_text = str(getattr(r, "description", ""))[:120]
                    if desc_text and desc_text != "nan":
                        st.caption(desc_text + "...")

                    url, _ = dest_link(active_ckey, r.name)
                    st.markdown(
                        f'<a href="{url}" target="_blank" style="color:#C45D3A;font-size:0.80rem;font-weight:600;text-decoration:none;">🔗 Search Destination →</a>',
                        unsafe_allow_html=True,
                    )
                    if img_caption:
                        st.caption(img_caption)

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        if st.button("Find hotels near my picks →", type="primary", width="stretch"):
            if not current_chosen:
                st.warning("Please select at least one attraction before continuing.")
            else:
                mark_dirty_if_changed()
                st.session_state["page"] = 4
                st.session_state["step"] = 3
                st.session_state["mc_step"] = 3
                st.rerun()

elif current_page == 4:
    render_curved_hero("Hotels & Stays", "Find the best stays for a comfortable trip.")

    if "Single" in trip_mode:
        active_city = st.session_state.get("selected_city", "Agra")
    else:
        active_city = st.session_state.get("mc_active_city", st.session_state.get("mc_selected_cities", ["Jaipur"])[0])

    active_ckey = cities.index[cities["name"] == active_city][0]

    with st.container(border=True):
        st.markdown(
            f'''<div class="page-sec-header">
              <span style="font-size:1.45rem;">📍</span>
              <h2 class="page-sec-title">{active_city} – Select Hotels</h2>
            </div>
            <div class="page-sec-sub">Choose the type of stay that suits your preferences.</div>''',
            unsafe_allow_html=True,
        )

        tier_choice = st.selectbox(
            "Hotel Type",
            ["All Stays", "Luxury", "Premium", "Standard", "Budget"],
            key=f"p4_tier_sel_{active_ckey}",
        )
        st.session_state["_preserved_widget_values"][f"p4_tier_sel_{active_ckey}"] = tier_choice

        if "Single" in trip_mode:
            sel_names = st.session_state.get("chosen", [])
            ci_date = st.session_state.get("check_in", dt.date.today() + dt.timedelta(days=30))
            n_nights = st.session_state.get("nights", 2)
            req_rooms = -(-st.session_state.get("people", 2) // 2)
        else:
            sel_names = st.session_state.get("mc_chosen", {}).get(active_ckey, [])
            ci_date = st.session_state.get("mc_start", dt.date.today() + dt.timedelta(days=30))
            n_nights = 2
            req_rooms = -(-st.session_state.get("mc_people", 2) // 2)

        sel_places = places[(places["ckey"] == active_ckey) & places["name"].isin(sel_names)]
        if sel_places.empty:
            sel_places = places[places["ckey"] == active_ckey].head(5)

        tier_val = TIERS.get(tier_choice)
        ranked_hotels = nearby_hotels(sel_places, radius_km=50, tier=tier_val, top=30)
        if ranked_hotels.empty:
            ranked_hotels = nearby_hotels(sel_places, radius_km=100, tier=None, top=20)

        if "Single" in trip_mode:
            current_selected_h = st.session_state.get("hotel")
        else:
            current_selected_h = st.session_state.get("mc_hotels", {}).get(active_ckey)

        if (current_selected_h is None or current_selected_h not in hotels.index) and not ranked_hotels.empty:
            current_selected_h = ranked_hotels.index[0]
            if "Single" in trip_mode:
                st.session_state["hotel"] = current_selected_h
            else:
                st.session_state["mc_hotels"][active_ckey] = current_selected_h
                st.session_state[f"mc_hotel_{active_ckey}"] = current_selected_h

        city_img_fallback = get_city_image_path(active_city)
        for h_idx, h_row in ranked_hotels.head(6).iterrows():
            is_chosen = (h_idx == current_selected_h)
            free_r = available_rooms(h_row, ci_date, n_nights)
            avail_txt = f"✅ {free_r} Rooms available (est.)" if free_r >= req_rooms else f"⚠️ Only {free_r} rooms left (est.)"

            tier_lbl = h_row.get("tier_label", "Premium")
            star_val = h_row.get("hotel_star_rating", 4.0)
            rating_val = h_row.get("site_review_rating", 4.3)
            rev_cnt = int(h_row.get("site_review_count", 120))
            address_str = str(h_row.get("address", ""))
            facilities_str = str(h_row.get("hotel_facilities", "")).replace("|", " • ")[:120]

            with st.container(border=True):
                col_info, col_act = st.columns([6, 2])
                with col_info:
                    st.markdown(f'<div class="hotel-name-h">{html.escape(str(h_row["property_name"]))}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<span class="chip" style="background:#B8860B;">{tier_lbl}</span>'
                        f'<span class="chip" style="background:#8A6A00;">⭐ {rating_val} ({rev_cnt} reviews)</span>'
                        f'<span class="chip" style="background:#2E7D32;">{avail_txt}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f'<div class="hotel-addr"><strong>Address:</strong> {html.escape(address_str[:80])} • ★★★★ ({star_val}★)</div>', unsafe_allow_html=True)
                    if facilities_str and facilities_str != "nan":
                        st.markdown(f'<div class="hotel-amenities"><strong>Amenities:</strong> {html.escape(facilities_str)}</div>', unsafe_allow_html=True)

                    g_maps = f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(h_row['property_name']) + ' ' + active_city + ', India')}"
                    st.markdown(f'<a href="{g_maps}" target="_blank" style="color:#102F26;font-size:0.80rem;font-weight:600;text-decoration:none;">📍 View on Google Maps →</a>', unsafe_allow_html=True)

                with col_act:
                    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                    btn_label = "✓ Selected Stay" if is_chosen else "Choose this hotel"
                    if st.button(btn_label, key=f"sel_h_{active_ckey}_{h_idx}", width="stretch", type="primary" if is_chosen else "secondary"):
                        if "Single" in trip_mode:
                            st.session_state["hotel"] = h_idx
                        else:
                            st.session_state["mc_hotels"][active_ckey] = h_idx
                            st.session_state[f"mc_hotel_{active_ckey}"] = h_idx
                        mark_dirty_if_changed()
                        st.rerun()

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        if st.button("Find the Map →", type="primary", width="stretch"):
            mark_dirty_if_changed()
            st.session_state["page"] = 5
            st.session_state["step"] = 4
            st.session_state["mc_step"] = 3
            st.rerun()

elif current_page == 5:
    render_curved_hero(
        "My Itinerary & Map",
        "Your complete travel plan for an amazing trip." if "Single" in trip_mode else "Your complete multi-city travel plan with optimized route."
    )

    current_fp = compute_selections_fingerprint()
    if st.session_state.get("itinerary_dirty") or (st.session_state.get("itinerary_fingerprint") and current_fp != st.session_state.get("itinerary_fingerprint")):
        st.markdown(
            '''<div class="itinerary-outdated">
              <span>⚠️ Your trip has changed. Regenerate your itinerary to apply the updates.</span>
            </div>''',
            unsafe_allow_html=True,
        )
        if st.button("Regenerate Itinerary", type="primary"):
            st.session_state["itinerary_fingerprint"] = current_fp
            st.session_state["itinerary_dirty"] = False
            st.rerun()
    else:
        st.session_state["itinerary_fingerprint"] = current_fp
        st.session_state["itinerary_dirty"] = False

    if "Single" in trip_mode:
        city_name = st.session_state.get("city", "Agra")
        ckey = st.session_state.get("ckey", cities.index[cities["name"] == city_name][0])
        chosen_names = st.session_state.get("chosen", [])
        ci_date = st.session_state.get("check_in", dt.date.today() + dt.timedelta(days=30))
        n_nights = st.session_state.get("nights", 2)
        co_date = ci_date + dt.timedelta(days=n_nights)
        people = int(st.session_state.get("people", 2))
        rooms = -(-people // 2)

        sel_places = places[(places["ckey"] == ckey) & places["name"].isin(chosen_names)]
        if sel_places.empty:
            sel_places = places[places["ckey"] == ckey].sort_values("rating", ascending=False).head(3)
            chosen_names = sel_places["name"].tolist()
            st.session_state["chosen"] = chosen_names

        h_idx = st.session_state.get("hotel")
        if h_idx is None or h_idx not in hotels.index:
            hot_df = nearby_hotels(sel_places, radius_km=50, top=10)
            h_idx = hot_df.index[0]
            st.session_state["hotel"] = h_idx
        hotel_row = hotels.loc[h_idx]

        est_stay = 2250 * n_nights * rooms
        est_food = 750 * (n_nights + 1) * people
        est_transport = 800 * (n_nights + 1)
        est_tickets = 500 * len(chosen_names) * people
        est_misc = 1000
        total_est = est_stay + est_food + est_transport + est_tickets + est_misc

        with st.container(border=True):
            st.markdown(
                f'''<div class="page-sec-header">
                  <span style="font-size:1.45rem;">📍</span>
                  <h2 class="page-sec-title">Trip Summary – {city_name}</h2>
                </div>
                <div class="page-sec-sub">Here is your selected places, stay and the optimized plan.</div>''',
                unsafe_allow_html=True,
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Destination City", city_name)
            m2.metric("Travel Dates", f"{ci_date:%d %b} – {co_date:%d %b}", f"{n_nights + 1} days")
            m3.metric("Travellers", f"{people} ({rooms} room)")
            m4.metric("Estimated Budget", f"₹{total_est:,}", "approx.")

        c_pv1, c_pv2 = st.columns([1, 1])
        with c_pv1:
            with st.container(border=True):
                st.markdown(f"**Selected Places & Attractions ({len(chosen_names)} total)**")
                p_cols = st.columns(min(3, len(chosen_names)))
                for p_i, p_name in enumerate(chosen_names[:3]):
                    with p_cols[p_i]:
                        p_match = sel_places[sel_places["name"] == p_name]
                        if not p_match.empty:
                            p_img, _, _ = get_attraction_image_info(p_match.iloc[0], ckey)
                            if p_img: st.image(p_img, width="stretch")
                        st.caption(f"**{p_name}**")

        with c_pv2:
            with st.container(border=True):
                st.markdown("**Selected Hotel**")
                h_img = get_city_image_path(city_name)
                h_c1, h_c2 = st.columns([1, 2])
                with h_c1:
                    if h_img: st.image(h_img, width="stretch")
                with h_c2:
                    st.markdown(f"**{hotel_row['property_name']}**")
                    st.caption(f"⭐ {hotel_row['site_review_rating']} • {hotel_row.get('tier_label', 'Premium')}")
                    st.caption(f"Address: {hotel_row['address'][:65]}")

        st.markdown(
            '''<div style="margin:24px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">📅 Day-wise Itinerary (Optimized Plan)</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">Places are arranged to minimize travel time and distance.</div>
            </div>''',
            unsafe_allow_html=True,
        )

        n_days = min(n_nights + 1, int(cities.loc[ckey, "max_days"]))
        ordered_plan = plan_order(sel_places, hotel_row)
        days_chunks = split_days(ordered_plan, n_days)

        sched_export_days = []
        all_stops_in_order = [{"name": hotel_row["property_name"], "is_hotel": True}]

        for d_num, day_df in enumerate(days_chunks, 1):
            cur_day_date = ci_date + dt.timedelta(days=d_num - 1)
            day_schedule = schedule(day_df, hotel_row)

            sched_export_days.append({
                "day_label": f"Day {d_num}",
                "date_str": f"{cur_day_date:%d %b %Y}",
                "stops": day_schedule
            })

            with st.container(border=True):
                st.markdown(f'<div class="sched-day-header">Day {d_num} • {cur_day_date:%a, %d %b %Y}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="sched-timeline-item">'
                    f'<div class="sched-time">09:00 AM</div>'
                    f'<div class="sched-what">🚗 Start from {hotel_row["property_name"]}</div>'
                    f'<div class="sched-transfer">Departure</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                for item in day_schedule:
                    w_name = item["what"]
                    t_slot = item["time"]
                    km_val = item.get("km", 0)
                    trans_note = f"🚗 {km_val} km" if km_val > 0 else "-"
                    if w_name != "Lunch break":
                        all_stops_in_order.append({"name": w_name, "is_hotel": False})

                    st.markdown(
                        f'<div class="sched-timeline-item">'
                        f'<div class="sched-time">🕒 {t_slot}</div>'
                        f'<div class="sched-what">{"🍽️ " if w_name == "Lunch break" else "📍 "}{w_name}</div>'
                        f'<div class="sched-transfer">{trans_note}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown(
            '''<div style="margin:26px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">🗺️ Optimized Route Map</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">This map shows the best route to cover all your selected places.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        map_c1, map_c2 = st.columns([1, 2])
        with map_c1:
            with st.container(border=True):
                st.markdown("**Places in Order**")
                for s_i, stp in enumerate(all_stops_in_order[:7], 1):
                    prefix = "🏨" if stp["is_hotel"] else f"{s_i}."
                    st.markdown(f"**{prefix}** {stp['name']}")

                gq = quote_plus(f"{hotel_row['property_name']}, {city_name}")
                st.markdown(f'<a href="https://www.google.com/maps/search/?api=1&query={gq}" target="_blank" style="color:#102F26;font-size:0.85rem;font-weight:700;text-decoration:none;">📍 Open in Google Maps →</a>', unsafe_allow_html=True)

        with map_c2:
            map_pts = pd.concat([
                sel_places[["latitude", "longitude"]],
                pd.DataFrame([{"latitude": hotel_row["latitude"], "longitude": hotel_row["longitude"]}])
            ])
            st.map(map_pts, zoom=11)

        st.markdown(
            '''<div style="margin:26px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">₹ Estimated Budget Breakdown</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">Based on your selections and optimized plan.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            b_cols = st.columns(6)
            b_cols[0].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Stay</div><div class="budget-cell-val">₹{est_stay:,}</div></div>', unsafe_allow_html=True)
            b_cols[1].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Food</div><div class="budget-cell-val">₹{est_food:,}</div></div>', unsafe_allow_html=True)
            b_cols[2].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Transport</div><div class="budget-cell-val">₹{est_transport:,}</div></div>', unsafe_allow_html=True)
            b_cols[3].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Tickets &amp; Entry</div><div class="budget-cell-val">₹{est_tickets:,}</div></div>', unsafe_allow_html=True)
            b_cols[4].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Miscellaneous</div><div class="budget-cell-val">₹{est_misc:,}</div></div>', unsafe_allow_html=True)
            b_cols[5].markdown(f'<div class="budget-cell budget-cell-total"><div class="budget-cell-label">Total Estimated</div><div class="budget-cell-val">₹{total_est:,}</div></div>', unsafe_allow_html=True)
            st.caption("All rates are simulated estimates based on seasonal averages, not live transaction prices.")

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        pdf_hotels = [{
            "name": hotel_row["property_name"],
            "city": city_name,
            "tier": hotel_row.get("tier_label", "Premium"),
            "rating": f"{hotel_row['site_review_rating']} ({int(hotel_row['site_review_count'])} reviews)",
            "address": hotel_row["address"],
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(hotel_row['property_name']) + ' ' + city_name)}"
        }]
        pdf_attrs = []
        for p_name in chosen_names:
            p_m = sel_places[sel_places["name"] == p_name]
            if not p_m.empty:
                r_m = p_m.iloc[0]
                url_m, _ = dest_link(ckey, p_name)
                pdf_attrs.append({
                    "name": p_name,
                    "city": city_name,
                    "category": CAT.get(r_m.primary_interest, ("", "", "", "Heritage"))[3],
                    "rating": str(r_m.rating),
                    "duration": str(r_m.time_hours),
                    "url": url_m
                })

        pdf_bytes = generate_itinerary_pdf(
            trip_title=f"Itinerary for {city_name}",
            trip_mode="Single-City Mode",
            cities_str=f"{city_name}, {CITY_TO_STATE.get(city_name, 'India')}",
            travel_dates_str=f"{ci_date:%d %b %Y} – {co_date:%d %b %Y}",
            travellers_count=people,
            total_budget_str=f"₹{total_est:,} (approx.)",
            hotels_info=pdf_hotels,
            attractions_info=pdf_attrs,
            schedule_days=sched_export_days,
            budget_breakdown={
                "Accommodation": f"₹{est_stay:,}",
                "Food & Meals": f"₹{est_food:,}",
                "Local Transport": f"₹{est_transport:,}",
                "Attraction Tickets": f"₹{est_tickets:,}",
                "Miscellaneous": f"₹{est_misc:,}",
                "Total Estimated Budget": f"₹{total_est:,}"
            }
        )
        st.download_button(
            label="Download Itinerary ⬇",
            data=pdf_bytes,
            file_name=f"itinerary_{city_name.lower()}.pdf",
            mime="application/pdf",
            width="stretch",
        )

    else:
        mc_cities = st.session_state.get("mc_selected_cities", ["Jaipur", "Udaipur", "Munnar"])
        mc_ckeys = [cities.index[cities["name"] == c][0] for c in mc_cities]
        mc_start = st.session_state.get("mc_start", dt.date.today() + dt.timedelta(days=30))
        mc_ppl = int(st.session_state.get("mc_people", 2))
        mc_rooms = -(-mc_ppl // 2)

        route_keys, tot_km, tot_hrs = optimise_city_order(mc_ckeys, cities)
        route_names = [cities.loc[k, "name"] for k in route_keys]

        city_nights = [(k, 2) for k in route_keys]
        legs = allocate_leg_dates(mc_start, city_nights)
        total_nights = sum(l["nights"] for l in legs)
        mc_end = mc_start + dt.timedelta(days=total_nights)

        est_mc_stay = 2500 * total_nights * mc_rooms
        est_mc_food = 800 * (total_nights + 1) * mc_ppl
        est_mc_intercity = int(tot_km * 12)
        est_mc_local = 600 * (total_nights + 1)
        tot_places_cnt = sum(len(st.session_state.get("mc_chosen", {}).get(k, [])) for k in route_keys)
        est_mc_tickets = 400 * max(1, tot_places_cnt) * mc_ppl
        est_mc_misc = 2500
        mc_total_est = est_mc_stay + est_mc_food + est_mc_intercity + est_mc_local + est_mc_tickets + est_mc_misc

        with st.container(border=True):
            st.markdown(
                f'''<div class="page-sec-header">
                  <span style="font-size:1.45rem;">📍</span>
                  <h2 class="page-sec-title">Trip Summary – {' → '.join(route_names)}</h2>
                </div>
                <div class="page-sec-sub">Here is your selected places, stays and the optimized plan across all cities.</div>''',
                unsafe_allow_html=True,
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Destinations", f"{len(route_names)} Cities")
            m2.metric("Travel Dates", f"{mc_start:%d %b} – {mc_end:%d %b}", f"{total_nights} days")
            m3.metric("Travellers", f"{mc_ppl} ({mc_rooms} rooms)")
            m4.metric("Estimated Budget", f"₹{mc_total_est:,}", "approx.")

        st.markdown(
            '''<div style="margin:24px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">📅 City-wise Itinerary &amp; Optimized Plan</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">The route is optimized to reduce travel time and distance between cities and within each city.</div>
            </div>''',
            unsafe_allow_html=True,
        )

        leg_cols = st.columns(min(3, len(legs)))
        pdf_schedule_days = []
        pdf_hotels_list = []
        pdf_attrs_list = []
        map_points = []

        for l_idx, leg in enumerate(legs):
            c_col = leg_cols[l_idx % len(leg_cols)]
            l_ckey = leg["ckey"]
            l_cname = cities.loc[l_ckey, "name"]
            l_ci = leg["check_in"]
            l_co = leg["check_out"]
            l_n = leg["nights"]

            l_chosen = st.session_state.get("mc_chosen", {}).get(l_ckey, [])
            l_places = places[(places["ckey"] == l_ckey) & places["name"].isin(l_chosen)]
            if l_places.empty:
                l_places = places[places["ckey"] == l_ckey].sort_values("rating", ascending=False).head(3)
                l_chosen = l_places["name"].tolist()

            h_sel_idx = st.session_state.get("mc_hotels", {}).get(l_ckey) or st.session_state.get(f"mc_hotel_{l_ckey}")
            if h_sel_idx is None or h_sel_idx not in hotels.index:
                hot_ranked = nearby_hotels(l_places, radius_km=50, top=10)
                h_sel_idx = hot_ranked.index[0]
            l_hotel = hotels.loc[h_sel_idx]

            pdf_hotels_list.append({
                "name": l_hotel["property_name"],
                "city": l_cname,
                "tier": l_hotel.get("tier_label", "Premium"),
                "rating": f"{l_hotel['site_review_rating']} ({int(l_hotel['site_review_count'])} reviews)",
                "address": l_hotel["address"],
                "maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(l_hotel['property_name']) + ' ' + l_cname)}"
            })

            map_points.append(l_places[["latitude", "longitude"]])
            map_points.append(pd.DataFrame([{"latitude": l_hotel["latitude"], "longitude": l_hotel["longitude"]}]))

            for a_name in l_chosen:
                a_m = l_places[l_places["name"] == a_name]
                if not a_m.empty:
                    url_a, _ = dest_link(l_ckey, a_name)
                    pdf_attrs_list.append({
                        "name": a_name,
                        "city": l_cname,
                        "category": CAT.get(a_m.iloc[0].primary_interest, ("", "", "", "Heritage"))[3],
                        "rating": str(a_m.iloc[0].rating),
                        "duration": str(a_m.iloc[0].time_hours),
                        "url": url_a
                    })

            with c_col:
                with st.container(border=True):
                    st.markdown(f"**Day {l_idx * 2 + 1} – {l_idx * 2 + 2} | {l_cname}**")
                    st.caption(f"{l_ci:%d %b} – {l_co:%d %b} ({l_n} days)")
                    st.markdown(f"**Stay:** {l_hotel['property_name']}")
                    st.markdown("**Places to Visit:**")
                    for p_item in l_chosen:
                        st.markdown(f"• {p_item}")

                    pdf_schedule_days.append({
                        "day_label": f"Leg {l_idx + 1} ({l_cname})",
                        "date_str": f"{l_ci:%d %b} – {l_co:%d %b}",
                        "stops": [{"time": "Full Day", "what": f"Explore {', '.join(l_chosen)}", "km": 5.0}]
                    })

        st.markdown(
            '''<div style="margin:26px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">🗺️ Optimized Multi-City Route Map</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">This map shows the best route across all cities and within each city.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        mc_m1, mc_m2 = st.columns([1, 2])
        with mc_m1:
            with st.container(border=True):
                st.markdown("**Route Overview**")
                for r_idx, r_cname in enumerate(route_names, 1):
                    tag = "(Start)" if r_idx == 1 else "(End)" if r_idx == len(route_names) else ""
                    st.markdown(f"**{r_idx}.** {r_cname} {tag}")
                st.caption(f"Estimated Inter-City Driving: ~{tot_km:.1f} km (~{tot_hrs:.1f} hrs)")
        with mc_m2:
            if map_points:
                st.map(pd.concat(map_points, ignore_index=True), zoom=6)

        st.markdown(
            '''<div style="margin:26px 0 10px;">
              <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#102F26;margin:0;">₹ Estimated Budget Breakdown (All Cities)</h3>
              <div style="color:#5C6B62;font-size:0.85rem;">Based on your selections and optimized plan.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            b_cols = st.columns(6)
            b_cols[0].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Stay</div><div class="budget-cell-val">₹{est_mc_stay:,}</div></div>', unsafe_allow_html=True)
            b_cols[1].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Food</div><div class="budget-cell-val">₹{est_mc_food:,}</div></div>', unsafe_allow_html=True)
            b_cols[2].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Inter-city Transport</div><div class="budget-cell-val">₹{est_mc_intercity:,}</div></div>', unsafe_allow_html=True)
            b_cols[3].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Local Transport</div><div class="budget-cell-val">₹{est_mc_local:,}</div></div>', unsafe_allow_html=True)
            b_cols[4].markdown(f'<div class="budget-cell"><div class="budget-cell-label">Tickets &amp; Entry</div><div class="budget-cell-val">₹{est_mc_tickets:,}</div></div>', unsafe_allow_html=True)
            b_cols[5].markdown(f'<div class="budget-cell budget-cell-total"><div class="budget-cell-label">Total Estimated</div><div class="budget-cell-val">₹{mc_total_est:,}</div></div>', unsafe_allow_html=True)
            st.caption("All rates are simulated estimates based on past averages, not live transaction prices.")

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        pdf_bytes = generate_itinerary_pdf(
            trip_title=f"Multi-City Circuit: {' → '.join(route_names)}",
            trip_mode="Multi-City Mode",
            cities_str=', '.join(route_names),
            travel_dates_str=f"{mc_start:%d %b %Y} – {mc_end:%d %b %Y}",
            travellers_count=mc_ppl,
            total_budget_str=f"₹{mc_total_est:,} (approx.)",
            hotels_info=pdf_hotels_list,
            attractions_info=pdf_attrs_list,
            schedule_days=pdf_schedule_days,
            budget_breakdown={
                "Accommodation": f"₹{est_mc_stay:,}",
                "Food & Meals": f"₹{est_mc_food:,}",
                "Inter-city Transport": f"₹{est_mc_intercity:,}",
                "Local Transport": f"₹{est_mc_local:,}",
                "Attraction Tickets": f"₹{est_mc_tickets:,}",
                "Miscellaneous": f"₹{est_mc_misc:,}",
                "Total Estimated Budget": f"₹{mc_total_est:,}"
            }
        )
        st.download_button(
            label="Download Itinerary ⬇",
            data=pdf_bytes,
            file_name="multi_city_itinerary.pdf",
            mime="application/pdf",
            width="stretch",
        )

elif current_page == 6:
    render_travel_checklist()

    st.markdown("---")

    if st.button("← Back to My Itinerary & Map"):
        st.session_state["page"] = 5
        st.rerun()

st.caption("Descriptions and images from Wikipedia / Wikimedia Commons (CC BY-SA). Hotel data is a past snapshot.")