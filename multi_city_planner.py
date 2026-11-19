import itertools
import datetime as dt
import numpy as np
import pandas as pd
from planner_lib import hav_km, nearby_hotels, plan_order, split_days, schedule, available_rooms, fmt

ROAD_FACTOR = 1.3
TRANSFER_SPEED_KMH = 45.0 # Average inter-city road transfer speed in km/h

def estimate_road_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates estimated road distance between two coordinates using Haversine * 1.3."""
    return float(hav_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR)

def estimate_transfer_hours(road_km: float, speed_kmh: float = TRANSFER_SPEED_KMH) -> float:
    """Estimates inter-city road transfer time in hours."""
    if speed_kmh <= 0:
        return 0.0
    return road_km / speed_kmh

def calculate_route_distance(city_keys: list[str], cities_df: pd.DataFrame) -> float:
    """Calculates total road distance for a sequence of city keys."""
    total_km = 0.0
    for i in range(len(city_keys) - 1):
        c1 = cities_df.loc[city_keys[i]]
        c2 = cities_df.loc[city_keys[i + 1]]
        total_km += estimate_road_km(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
    return total_km

def optimise_city_order(city_keys: list[str], cities_df: pd.DataFrame) -> tuple[list[str], float, float]:
    """
    Evaluates all permutations for up to 5 cities to find the minimum road travel order.
    Returns (optimal_city_keys, total_road_km, total_transfer_hours).
    """
    if not city_keys:
        return [], 0.0, 0.0
    
    # Verify all cities have valid coordinates
    for c in city_keys:
        if c not in cities_df.index:
            raise ValueError(f"City key '{c}' not found in cities dataset.")
        if pd.isna(cities_df.loc[c, "lat"]) or pd.isna(cities_df.loc[c, "lon"]):
            raise ValueError(f"City '{c}' has missing geographical coordinates.")

    if len(city_keys) <= 2:
        dist = calculate_route_distance(city_keys, cities_df)
        return list(city_keys), round(dist, 1), round(estimate_transfer_hours(dist), 1)

    # Evaluate all permutations for <= 8 cities (max 8! = 40,320 permutations)
    if len(city_keys) <= 8:
        perms = list(itertools.permutations(city_keys))
        best_perm = None
        min_dist = float("inf")

        for p in perms:
            d = calculate_route_distance(list(p), cities_df)
            if d < min_dist:
                min_dist = d
                best_perm = list(p)

        hrs = estimate_transfer_hours(min_dist)
        return best_perm, round(min_dist, 1), round(hrs, 1)
    else:
        # Greedy Nearest-Neighbor search for > 8 cities without arbitrary upper limit
        best_route = None
        min_dist = float("inf")
        for start_city in city_keys:
            unvisited = set(city_keys) - {start_city}
            curr = start_city
            route = [curr]
            while unvisited:
                c1 = cities_df.loc[curr]
                next_c = min(
                    unvisited,
                    key=lambda c: estimate_road_km(c1["lat"], c1["lon"], cities_df.loc[c, "lat"], cities_df.loc[c, "lon"])
                )
                route.append(next_c)
                unvisited.remove(next_c)
                curr = next_c
            d = calculate_route_distance(route, cities_df)
            if d < min_dist:
                min_dist = d
                best_route = route
        hrs = estimate_transfer_hours(min_dist)
        return best_route, round(min_dist, 1), round(hrs, 1)

def allocate_leg_dates(start_date: dt.date, city_nights: list[tuple[str, int]]) -> list[dict]:
    """
    Allocates sequential check-in and check-out dates for each city leg.
    Returns a list of leg dictionaries.
    """
    legs = []
    current_date = start_date

    for ckey, nights in city_nights:
        if nights < 1:
            raise ValueError(f"Nights for city '{ckey}' must be at least 1.")
        check_in = current_date
        check_out = check_in + dt.timedelta(days=nights)
        legs.append({
            "ckey": ckey,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "days": nights
        })
        current_date = check_out

    return legs

def schedule_with_transfer(
    day_places: pd.DataFrame,
    hotel: pd.Series,
    transfer_km: float = 0.0,
    transfer_hours: float = 0.0,
    transfer_from_name: str = "",
    local_speed: float = 25.0
) -> tuple[list[dict], bool]:
    """
    Schedules a day plan, accounting for inter-city transfer from the previous city.
    If transfer_hours > 4.0, flags as a light travel day and restricts late stops.
    Returns (schedule_items, is_light_day).
    """
    out = []
    is_light_day = transfer_hours > 4.0

    if transfer_hours > 0:
        start_t = 9.0
        end_transfer_t = start_t + transfer_hours
        out.append({
            "time": f"{fmt(start_t)}–{fmt(end_transfer_t)}",
            "what": f"Inter-city road transfer from {transfer_from_name} to hotel (est.)",
            "km": round(transfer_km, 1)
        })
        cur_t = end_transfer_t
    else:
        cur_t = 9.0

    cur_loc = (hotel["latitude"], hotel["longitude"])
    lunch_done = False

    # Filter/cap places if it is a light travel day
    places_to_visit = day_places
    if is_light_day and len(day_places) > 2:
        # Long travel day: keep only top 1 or 2 nearby attractions
        places_to_visit = day_places.head(2)

    for r in places_to_visit.itertuples():
        km = float(hav_km(cur_loc[0], cur_loc[1], r.latitude, r.longitude))
        travel_time = km / local_speed
        arrival_t = cur_t + travel_time

        # Lunch break: insert around or after 13:00 if not yet taken
        if not lunch_done and arrival_t >= 13.0:
            lunch_start = arrival_t
            out.append({
                "time": f"{fmt(lunch_start)}–{fmt(lunch_start + 1.0)}",
                "what": "Lunch break",
                "km": 0.0
            })
            arrival_t += 1.0
            lunch_done = True

        departure_t = arrival_t + r.time_hours
        out.append({
            "time": f"{fmt(arrival_t)}–{fmt(departure_t)}",
            "what": r.name,
            "km": round(km, 1)
        })
        cur_t = departure_t
        cur_loc = (r.latitude, r.longitude)

    return out, is_light_day
