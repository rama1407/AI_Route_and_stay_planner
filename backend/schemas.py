from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class City(BaseModel):
    ckey: str
    name: str
    n: int
    lat: float
    lon: float
    hotels_25km: int
    max_days: int

class Attraction(BaseModel):
    name: str
    city: str
    ckey: str
    latitude: float
    longitude: float
    interest: str
    primary_interest: str
    rating: float
    fee: int
    time_hours: float
    best_time: str
    weekly_off: str
    coord_status: str
    description: Optional[str] = None
    image: Optional[str] = None
    dest_url: str
    dest_label: str

class HotelSearchRequest(BaseModel):
    ckey: str
    place_names: List[str] = Field(..., min_items=1)
    check_in: date
    nights: int = Field(..., ge=1, le=30)
    people: int = Field(..., ge=1, le=50)
    tier: Optional[str] = None
    radius_km: float = Field(25.0, ge=5.0, le=150.0)
    top: int = Field(10, ge=1, le=50)

class HotelItem(BaseModel):
    hotel_id: int
    property_name: str
    city: str
    latitude: float
    longitude: float
    hotel_star_rating: int
    site_review_rating: float
    site_review_count: int
    tier_name: str
    tier_label: str
    d_mean: float
    score: float
    available_rooms: int
    hotel_facilities: str
    address: str
    availability_status: str
    availability_disclaimer: str = "Estimated from demand simulation, not live inventory"

class TripPlanRequest(BaseModel):
    ckey: str
    place_names: List[str] = Field(..., min_items=1)
    hotel_id: int
    check_in: date
    nights: int = Field(..., ge=1, le=30)
    people: int = Field(..., ge=1, le=50)

class ScheduleItem(BaseModel):
    time: str
    what: str
    km: float

class DayPlan(BaseModel):
    day_number: int
    date: str
    items: List[ScheduleItem]

class TripPlanResponse(BaseModel):
    city: str
    hotel: HotelItem
    days: int
    nights: int
    people: int
    check_in: str
    check_out: str
    itinerary: List[DayPlan]
    places: List[Attraction]
    summary: Dict[str, Any]
    disclaimer: str = "Availability and scheduling are simulated estimates for planning purposes."
