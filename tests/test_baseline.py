import datetime as dt
import numpy as np
import pandas as pd
import pytest

from planner_lib import (
    hotels,
    hav_km,
    nearby_hotels,
    add_areas,
    order_nn,
    plan_order,
    split_days,
    schedule,
    occupancy,
    available_rooms,
)

def test_hav_km_known_distance():
    # Distance between two identical points is 0
    d0 = hav_km(15.2993, 74.1240, 15.2993, 74.1240)
    assert np.isclose(d0, 0.0)

    # Equator 1 degree longitude is approximately 111.19 km
    d1 = hav_km(0.0, 0.0, 0.0, 1.0)
    assert 110 < d1 < 112

def test_dbscan_attraction_areas():
    places = pd.read_csv("attractions_geo.csv")
    goa_places = places[places["ckey"] == "goa"].head(8)
    clustered = add_areas(goa_places, eps_km=8)
    assert "area" in clustered.columns
    # With min_samples=1, no noise points (-1) should exist
    assert (clustered["area"] == -1).sum() == 0
    # Clusters should be non-negative integers
    assert clustered["area"].nunique() >= 1

def test_occupancy_deterministic():
    d = dt.date(2027, 1, 5)
    hotel_name = "Vilo Villa Guest House"
    occ1 = occupancy(hotel_name, d)
    occ2 = occupancy(hotel_name, d)
    assert occ1 == occ2
    assert 0.05 <= occ1 <= 0.98

def test_available_rooms():
    sample_hotel = hotels.iloc[0]
    check_in = dt.date(2027, 1, 5)
    nights = 2
    free = available_rooms(sample_hotel, check_in, nights)
    assert isinstance(free, (int, np.integer))
    assert free >= 0

def test_goa_baseline_parity():
    cities = pd.read_csv("cities.csv", index_col=0)
    places = pd.read_csv("attractions_geo.csv")

    assert "goa" in cities.index

    goa_places = places[places["ckey"] == "goa"].sort_values("rating", ascending=False)
    assert len(goa_places) >= 8

    top8_names = goa_places.head(8)["name"].tolist()
    sel = places[(places["ckey"] == "goa") & places["name"].isin(top8_names)]

    people = 4
    rooms = -(-people // 2) # 2 rooms
    check_in = dt.date(2027, 1, 5)
    nights = 2

    hot = nearby_hotels(sel, radius_km=25, tier=None, top=60)
    assert not hot.empty

    hot["free"] = [available_rooms(r, check_in, nights) for r in hot.to_dict("records")]
    hot_avail = hot[hot["free"] >= rooms].head(8)
    assert not hot_avail.empty

    best_hotel = hot_avail.iloc[0]
    assert best_hotel["property_name"] == "Vilo Villa Guest House"
    assert best_hotel["free"] >= rooms

    days = 2
    ordered = plan_order(sel, best_hotel)
    assert len(ordered) == 8

    days_split = split_days(ordered, days)
    assert len(days_split) == 2

    # Check day 1 schedule
    plan_d1 = schedule(days_split[0], best_hotel)
    assert len(plan_d1) > 0
    # Day 1 should include lunch break
    assert any(item["what"] == "Lunch break" for item in plan_d1)

    # Check day 2 schedule
    plan_d2 = schedule(days_split[1], best_hotel)
    assert len(plan_d2) > 0
    assert any(item["what"] == "Lunch break" for item in plan_d2)
