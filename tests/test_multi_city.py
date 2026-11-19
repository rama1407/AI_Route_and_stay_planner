import os
import datetime as dt
import numpy as np
import pandas as pd
import pytest

from planner_lib import hav_km, nearby_hotels, plan_order, split_days, schedule, available_rooms
from multi_city_planner import (
    estimate_road_km,
    estimate_transfer_hours,
    calculate_route_distance,
    optimise_city_order,
    allocate_leg_dates,
    schedule_with_transfer,
)

@pytest.fixture
def cities_data():
    cities = pd.read_csv("cities.csv", index_col=0)
    if os.path.exists("cities_supplement.csv"):
        supp = pd.read_csv("cities_supplement.csv", index_col=0)
        cities = pd.concat([cities, supp])
        cities = cities[~cities.index.duplicated(keep="last")]
    return cities

@pytest.fixture
def places_data():
    places = pd.read_csv("attractions_geo.csv")
    if os.path.exists("attractions_supplement.csv"):
        supp = pd.read_csv("attractions_supplement.csv")
        places = pd.concat([places, supp], ignore_index=True).drop_duplicates(subset=["ckey", "name"])
    return places

def test_road_distance_and_transfer_time():
    # Identical coordinates should yield 0 km and 0 hours
    assert estimate_road_km(10.0, 77.0, 10.0, 77.0) == 0.0
    assert estimate_transfer_hours(0.0) == 0.0

    # 100 km road distance at 45 km/h should take ~2.22 hours
    hrs = estimate_transfer_hours(100.0, speed_kmh=45.0)
    assert np.isclose(hrs, 100.0 / 45.0)

    # Road km must equal Haversine * 1.3
    lat1, lon1, lat2, lon2 = 28.61, 77.23, 27.18, 78.00 # Delhi to Agra
    direct_km = hav_km(lat1, lon1, lat2, lon2)
    road_km = estimate_road_km(lat1, lon1, lat2, lon2)
    assert np.isclose(road_km, direct_km * 1.3)

def test_city_order_permutations(cities_data):
    # Route: Delhi -> Agra -> Jaipur
    city_keys = ["delhi", "jaipur", "agra"] # Intentionally disordered
    best_order, min_km, min_hrs = optimise_city_order(city_keys, cities_data)

    assert len(best_order) == 3
    # Optimal road route should not bounce back and forth
    assert min_km > 0
    assert min_hrs > 0
    assert (best_order == ["delhi", "agra", "jaipur"]) or (best_order == ["jaipur", "agra", "delhi"])

def test_kerala_circuit_permutations(cities_data):
    # Route: Munnar, Thekkady, Alleppey
    city_keys = ["thekkady", "alleppey", "munnar"]
    best_order, min_km, min_hrs = optimise_city_order(city_keys, cities_data)

    # Direct circuit: ('munnar', 'thekkady', 'alleppey') or ('alleppey', 'thekkady', 'munnar')
    assert (best_order == ["munnar", "thekkady", "alleppey"]) or (best_order == ["alleppey", "thekkady", "munnar"])
    assert min_km < 200.0 # ~186 km

def test_date_allocation():
    start = dt.date(2027, 3, 1)
    legs = allocate_leg_dates(start, [("munnar", 2), ("thekkady", 1), ("alleppey", 2)])

    assert len(legs) == 3
    assert legs[0]["check_in"] == dt.date(2027, 3, 1)
    assert legs[0]["check_out"] == dt.date(2027, 3, 3)
    assert legs[0]["nights"] == 2

    assert legs[1]["check_in"] == dt.date(2027, 3, 3)
    assert legs[1]["check_out"] == dt.date(2027, 3, 4)
    assert legs[1]["nights"] == 1

    assert legs[2]["check_in"] == dt.date(2027, 3, 4)
    assert legs[2]["check_out"] == dt.date(2027, 3, 6)
    assert legs[2]["nights"] == 2

def test_invalid_and_zero_nights():
    start = dt.date(2027, 3, 1)
    with pytest.raises(ValueError, match="must be at least 1"):
        allocate_leg_dates(start, [("munnar", 0)])

def test_missing_coordinates_handling(cities_data):
    bad_cities = cities_data.copy()
    bad_cities.loc["delhi", "lat"] = np.nan

    with pytest.raises(ValueError, match="missing geographical coordinates"):
        optimise_city_order(["delhi", "agra"], bad_cities)

    with pytest.raises(ValueError, match="not found in cities"):
        optimise_city_order(["unknown_city", "agra"], cities_data)

def test_schedule_with_transfer(places_data):
    from planner_lib import hotels
    munnar_places = places_data[places_data["ckey"] == "munnar"].head(3)
    hotel = hotels.iloc[0]

    # Transfer of 2 hours (normal travel day)
    sched, is_light = schedule_with_transfer(munnar_places, hotel, transfer_km=90.0, transfer_hours=2.0, transfer_from_name="Kochi")
    assert not is_light
    assert sched[0]["what"].startswith("Inter-city road transfer")
    assert sched[0]["km"] == 90.0
    assert "09:00" in sched[0]["time"]

    # Transfer of 5 hours (triggers light travel day)
    sched_long, is_light_long = schedule_with_transfer(munnar_places, hotel, transfer_km=225.0, transfer_hours=5.0, transfer_from_name="Delhi")
    assert is_light_long

def test_end_to_end_kerala_multi_city(cities_data, places_data):
    # Test planning for Munnar -> Thekkady -> Alleppey
    city_keys = ["munnar", "thekkady", "alleppey"]
    start_date = dt.date(2027, 2, 10)
    city_nights = [("munnar", 2), ("thekkady", 1), ("alleppey", 2)]
    legs = allocate_leg_dates(start_date, city_nights)

    trip_plans = []
    for leg_idx, leg in enumerate(legs):
        ckey = leg["ckey"]
        c_places = places_data[places_data["ckey"] == ckey]
        assert len(c_places) > 0 # Every city in the route has valid attractions

        sel_places = c_places.head(min(len(c_places), leg["nights"] * 3))
        hot = nearby_hotels(sel_places, radius_km=30, tier=None, top=30)
        assert not hot.empty

        hot["free"] = [available_rooms(r, leg["check_in"], leg["nights"]) for r in hot.to_dict("records")]
        hot_avail = hot[hot["free"] >= 1]
        assert not hot_avail.empty
        best_hotel = hot_avail.iloc[0]

        ordered = plan_order(sel_places, best_hotel)
        day_splits = split_days(ordered, leg["days"])
        assert len(day_splits) == leg["days"]

        # Schedule each day
        for day_num, day_df in enumerate(day_splits, 1):
            if leg_idx > 0 and day_num == 1:
                prev_ckey = legs[leg_idx - 1]["ckey"]
                c_prev = cities_data.loc[prev_ckey]
                c_curr = cities_data.loc[ckey]
                trans_km = estimate_road_km(c_prev["lat"], c_prev["lon"], c_curr["lat"], c_curr["lon"])
                trans_hrs = estimate_transfer_hours(trans_km)
                day_sched, is_light = schedule_with_transfer(day_df, best_hotel, trans_km, trans_hrs, cities_data.loc[prev_ckey, "name"])
                assert len(day_sched) > 1
                assert "transfer" in day_sched[0]["what"].lower()
            else:
                day_sched = schedule(day_df, best_hotel)
                assert len(day_sched) > 0

        trip_plans.append({
            "city": cities_data.loc[ckey, "name"],
            "hotel": best_hotel["property_name"],
            "days": leg["days"]
        })

    assert len(trip_plans) == 3
    assert trip_plans[0]["city"] == "Munnar"
    assert trip_plans[1]["city"] == "Thekkady"
    assert trip_plans[2]["city"] == "Alleppey"

def test_preservation_of_single_city_goa(places_data):
    # Verifies single-city Goa baseline is 100% preserved
    goa_places = places_data[places_data["ckey"] == "goa"].sort_values("rating", ascending=False)
    assert len(goa_places) == 20

    top8_names = goa_places.head(8)["name"].tolist()
    sel = places_data[(places_data["ckey"] == "goa") & places_data["name"].isin(top8_names)]
    check_in = dt.date(2027, 1, 5)
    nights = 2

    hot = nearby_hotels(sel, radius_km=25, tier=None, top=60)
    hot["free"] = [available_rooms(r, check_in, nights) for r in hot.to_dict("records")]
    hot_avail = hot[hot["free"] >= 2].head(8)
    best_hotel = hot_avail.iloc[0]

    assert best_hotel["property_name"] == "Vilo Villa Guest House"
