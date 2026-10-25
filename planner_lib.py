import numpy as np, pandas as pd
import zlib, datetime as dt
from sklearn.cluster import DBSCAN

hotels = pd.read_csv("hotels_final.csv")
mu = hotels["site_review_rating"].mean()
hotels["adj_rating"] = (hotels["site_review_count"] * hotels["site_review_rating"] + 10 * mu) / (hotels["site_review_count"] + 10)
hotels["tier_label"] = hotels["tier_name"].map({"Premium": "Premium", "Unrated / Small": "Guest houses & small stays", "Low-rated": "Basic"})

def hav_km(lat1, lon1, lat2, lon2):
    p1, l1, p2, l2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def nearby_hotels(sel, radius_km=25, tier=None, top=10):
    c = sel[["latitude", "longitude"]].median()
    h = hotels.copy()
    h["d_center"] = hav_km(c.latitude, c.longitude, h["latitude"], h["longitude"])
    h["d_mean"] = np.mean([hav_km(r.latitude, r.longitude, h["latitude"], h["longitude"]) for r in sel.itertuples()], axis=0)
    h = h[h["d_center"] <= radius_km]
    if tier: h = h[h["tier_name"] == tier]
    h["score"] = h["adj_rating"] - h["d_mean"] / 30
    return h.sort_values("score", ascending=False).head(top)

def add_areas(sel, eps_km=8):
    X = np.radians(sel[["latitude", "longitude"]].to_numpy())
    sel = sel.copy()
    sel["area"] = DBSCAN(eps=eps_km / 6371, min_samples=1, metric="haversine").fit_predict(X)
    return sel

def order_nn(df, start):
    todo, cur, out = df.copy(), start, []
    while len(todo):
        d = hav_km(cur[0], cur[1], todo["latitude"], todo["longitude"])
        i = d.idxmin()
        out.append(i)
        cur = (todo.at[i, "latitude"], todo.at[i, "longitude"])
        todo = todo.drop(i)
    return df.loc[out]

def plan_order(sel, hotel):
    sel = add_areas(sel)
    cur = (hotel["latitude"], hotel["longitude"])
    cent = sel.groupby("area")[["latitude", "longitude"]].mean()
    parts = []
    for ar in order_nn(cent, cur).index:
        part = order_nn(sel[sel["area"] == ar], cur)
        parts.append(part)
        cur = (part["latitude"].iloc[-1], part["longitude"].iloc[-1])
    return pd.concat(parts)

def fmt(h):
    m = int(round(h * 60))
    return f"{m // 60:02d}:{m % 60:02d}"

def split_days(order, n_days):
    target, days, cur, acc = order["time_hours"].sum() / n_days, [], [], 0
    for r in order.itertuples():
        if cur and acc >= target and len(days) < n_days - 1:
            days.append(cur); cur, acc = [], 0
        cur.append(r.Index); acc += r.time_hours
    days.append(cur)
    return [order.loc[d] for d in days]

def schedule(day, hotel, speed=25, start=9.0):
    t, cur, lunch, out = start, (hotel["latitude"], hotel["longitude"]), False, []
    for r in day.itertuples():
        km = float(hav_km(cur[0], cur[1], r.latitude, r.longitude))
        t += km / speed
        if not lunch and t >= 13.0:
            out.append({"time": f"{fmt(t)}–{fmt(t + 1)}", "what": "Lunch break", "km": 0}); t += 1; lunch = True
        out.append({"time": f"{fmt(t)}–{fmt(t + r.time_hours)}", "what": r.name, "km": round(km, 1)})
        t, cur = t + r.time_hours, (r.latitude, r.longitude)
    return out

def occupancy(name, d):
    base = 0.45 + (0.25 if d.month in (12, 1) else 0.10 if d.month in (2, 3, 4, 5, 10, 11) else 0)
    base += 0.12 if d.weekday() in (4, 5) else 0          # Friday and Saturday nights are busier
    noise = (zlib.crc32(f"{name}{d}".encode()) % 100) / 100 * 0.4 - 0.2   # stable pseudo-random -0.2 .. +0.2
    return min(max(base + noise, 0.05), 0.98)

def available_rooms(h, check_in, nights):
    rooms = max(int(h["room_count"]), 5)   # unknown or tiny counts: assume at least 5 rooms
    free = [round(rooms * (1 - occupancy(h["property_name"], check_in + dt.timedelta(days=k)))) for k in range(nights)]
    return min(free)
