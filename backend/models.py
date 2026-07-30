"""
TravelGenie Pydantic Models

Structured data models for agent inputs and outputs.
Ensures type-safe communication between agents with JSON schema validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


# ===== Enums =====

class TravelStyle(str, Enum):
    """Travel style/group type."""
    SOLO = "solo"
    FAMILY = "family"
    COUPLE = "couple"
    FRIENDS = "friends"


class TransportMode(str, Enum):
    """Transportation mode."""
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"


class HotelCategory(str, Enum):
    """Hotel preference category."""
    BUDGET = "budget"
    LUXURY = "luxury"
    HOSTEL = "hostel"
    RESORT = "resort"


class Season(str, Enum):
    """Travel season."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    MONSOON = "monsoon"


# ===== User Input Models =====

class UserTravelInput(BaseModel):
    """User's initial travel request."""
    
    budget: float = Field(..., gt=0, description="Total trip budget in USD")
    source_city: str = Field(..., min_length=2, description="Departure city")
    destination_city: Optional[str] = Field(None, description="Desired destination city (optional)")
    trip_days: int = Field(..., ge=1, le=90, description="Number of days")
    travel_type: TravelStyle = Field(..., description="Travel group type")
    transportation: TransportMode = Field(..., description="Primary transport mode")
    interests: List[str] = Field(..., min_items=1, description="Travel interests/activities")
    hotel_preference: HotelCategory = Field(..., description="Hotel preference")
    travel_month: str = Field(..., description="Month of travel")
    special_requirements: Optional[str] = Field(None, description="Any special needs or constraints")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "budget": 3000,
                "source_city": "New York",
                "trip_days": 7,
                "travel_type": "couple",
                "transportation": "flight",
                "interests": ["beaches", "food", "culture"],
                "hotel_preference": "resort",
                "travel_month": "July",
            }
        }


# ===== Agent Output Models =====

class TripFeasibilityOutput(BaseModel):
    """Trip Feasibility Agent output."""
    
    is_feasible: bool = Field(..., description="Whether the trip is feasible with given budget")
    daily_budget: float = Field(..., gt=0, description="Recommended daily budget")
    budget_allocation: Dict[str, float] = Field(
        ..., 
        description="Breakdown of budget: accommodation, food, transport, activities"
    )
    max_affordable_distance: float = Field(..., description="Max distance in km from source")
    warnings: List[str] = Field(default_factory=list, description="Budget-related warnings")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in feasibility assessment")
    reasoning: str = Field(..., description="Explanation of feasibility assessment")

    class Config:
        json_schema_extra = {
            "example": {
                "is_feasible": True,
                "daily_budget": 428.57,
                "budget_allocation": {
                    "accommodation": 40.0,
                    "food": 35.0,
                    "transport": 15.0,
                    "activities": 10.0,
                },
                "max_affordable_distance": 2500,
                "warnings": [],
                "confidence_score": 0.95,
                "reasoning": "Budget is sufficient for quality trip in Southeast Asia",
            }
        }


class Location(BaseModel):
    """Geographic location."""
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: str = Field(..., min_length=2)
    country: str = Field(..., min_length=2)
    region: Optional[str] = None


class HotelOption(BaseModel):
    """Hotel option for a destination."""
    
    name: str = Field(..., min_length=1, description="Hotel name")
    category: HotelCategory = Field(..., description="Hotel category")
    price_per_night: float = Field(..., gt=0, description="Price in USD per night")
    rating: float = Field(..., ge=0, le=5, description="Guest rating out of 5")
    amenities: List[str] = Field(default_factory=list, description="Available amenities")
    location: Location = Field(..., description="Hotel location")
    reviews_count: int = Field(default=0, description="Number of guest reviews")
    check_in_checkout: Optional[str] = Field(None, description="Check-in/out times")
    description: Optional[str] = Field(None, description="Hotel description")


class Weather(BaseModel):
    """Weather information."""
    
    current_temp: float = Field(..., description="Current temperature in Celsius")
    max_temp: float = Field(..., description="Max temperature in Celsius")
    min_temp: float = Field(..., description="Min temperature in Celsius")
    condition: str = Field(..., description="Weather condition (e.g., 'Sunny', 'Rainy')")
    rain_probability: float = Field(..., ge=0, le=1, description="Probability of rain")
    humidity: float = Field(..., ge=0, le=1, description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    warnings: List[str] = Field(default_factory=list, description="Weather warnings")


class Attraction(BaseModel):
    """Tourist attraction or point of interest."""
    
    name: str = Field(..., min_length=1)
    category: str = Field(..., description="Type: museum, park, restaurant, historical, etc.")
    location: Location = Field(...)
    rating: float = Field(..., ge=0, le=5)
    distance_from_city_center: float = Field(..., description="Distance in km")
    visit_duration_hours: float = Field(..., gt=0, description="Recommended visit time in hours")
    entry_fee: float = Field(..., ge=0, description="Entry fee in USD")
    opening_hours: Optional[str] = Field(None, description="Operating hours")
    description: Optional[str] = None


class DestinationOutput(BaseModel):
    """Destination Agent output."""
    
    destination: Location = Field(..., description="Recommended destination")
    reason: str = Field(..., description="Justification for this destination")
    best_season: Season = Field(..., description="Best season to visit")
    
    weather: Weather = Field(..., description="Expected weather information")
    
    hotel_options: List[HotelOption] = Field(
        ..., 
        min_items=1, 
        max_items=5,
        description="Top hotel recommendations"
    )
    selected_hotel: HotelOption = Field(..., description="Recommended hotel choice")
    
    attractions: List[Attraction] = Field(
        ..., 
        min_items=1,
        description="Top attractions and activities"
    )
    
    travel_distance: float = Field(..., description="Distance from source in km")
    travel_time_hours: float = Field(..., description="Estimated travel time in hours")
    
    estimated_cost_per_day: float = Field(..., description="Estimated daily cost in USD")
    feasibility_with_budget: bool = Field(..., description="Fits within user's budget")
    
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in recommendation")


class ItineraryDay(BaseModel):
    """Single day in the itinerary."""
    
    day_number: int = Field(..., ge=1, description="Day number in the trip")
    date: Optional[str] = Field(None, description="ISO date string (if known)")
    title: str = Field(..., description="Day theme or title")
    
    activities: List[Dict[str, Any]] = Field(
        ...,
        description="Ordered list of activities with times, durations, locations"
    )
    
    meals: Dict[str, str] = Field(
        default_factory=dict,
        description="Recommended meals: breakfast, lunch, dinner"
    )
    
    hotel_check_in: Optional[str] = Field(None, description="Hotel check-in time")
    hotel_check_out: Optional[str] = Field(None, description="Hotel check-out time")
    
    estimated_cost: float = Field(..., ge=0, description="Estimated cost for the day")
    transportation_needed: List[str] = Field(
        default_factory=list, 
        description="Transportation required"
    )
    
    notes: Optional[str] = Field(None, description="Important notes or tips")

    @field_validator("meals", mode="before")
    @classmethod
    def normalize_meals(cls, v: Any) -> Dict[str, str]:
        defaults = {
            "breakfast": "Breakfast at hotel or local café",
            "lunch": "Lunch at a local restaurant",
            "dinner": "Dinner at a local restaurant",
        }
        if not isinstance(v, dict):
            return defaults
        res = {}
        for m_key in ["breakfast", "lunch", "dinner"]:
            val = v.get(m_key)
            if val is None or not isinstance(val, str) or not val.strip():
                res[m_key] = defaults[m_key]
            else:
                res[m_key] = val.strip()
        for k, val in v.items():
            if k not in res and val is not None:
                res[k] = str(val)
        return res


class ScheduleOutput(BaseModel):
    """Schedule Agent output."""
    
    destination: Location = Field(..., description="Trip destination")
    start_date: Optional[str] = Field(None, description="Trip start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Trip end date (ISO format)")
    
    daily_itinerary: List[ItineraryDay] = Field(
        ...,
        min_items=1,
        description="Day-by-day itinerary"
    )
    
    total_estimated_cost: float = Field(..., description="Total trip cost estimate in USD")
    accommodation_cost: float = Field(..., description="Total hotel cost")
    food_cost: float = Field(..., description="Total food cost")
    transport_cost: float = Field(..., description="Total transport cost")
    activities_cost: float = Field(..., description="Total activities cost")
    
    transportation_method: TransportMode = Field(..., description="Primary transport for trip")
    transportation_details: Optional[str] = Field(None, description="Transport booking details")
    
    packing_recommendations: List[str] = Field(
        default_factory=list,
        description="Items to pack based on weather"
    )
    
    critical_notes: List[str] = Field(
        default_factory=list,
        description="Important information about the destination or trip"
    )

    @field_validator("transportation_method", mode="before")
    @classmethod
    def normalize_transportation(cls, v: Any) -> Any:
        if isinstance(v, str):
            val_lower = v.strip().lower()
            if val_lower in ("flight", "plane", "air", "airplane", "fly"):
                return TransportMode.FLIGHT
            elif val_lower in ("train", "rail", "railway", "subway", "metro", "tram"):
                return TransportMode.TRAIN
            elif val_lower in ("bus", "shuttle", "coach"):
                return TransportMode.BUS
            elif val_lower in (
                "car", "cab", "taxi", "auto", "ride share", "rideshare",
                "local transport", "local", "driving", "drive", "vehicle"
            ):
                return TransportMode.CAR
            for mode in TransportMode:
                if mode.value in val_lower:
                    return mode
            return TransportMode.CAR
        return v


class ValidationIssue(BaseModel):
    """A validation issue found in the plan."""
    
    category: str = Field(..., description="Type of issue: budget, time, weather, etc.")
    severity: str = Field(..., pattern="^(critical|warning|info)$")
    description: str = Field(...)
    suggested_fix: Optional[str] = Field(None)


class ValidationOutput(BaseModel):
    """Validation Agent output."""
    
    is_valid: bool = Field(..., description="Whether the plan is valid overall")
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="Issues found in the plan"
    )
    
    budget_within_limit: bool = Field(..., description="Does plan fit the budget?")
    schedule_feasible: bool = Field(..., description="Is schedule realistic and doable?")
    weather_compatible: bool = Field(..., description="Are activities compatible with weather?")
    hotel_verified: bool = Field(..., description="Is hotel information verified?")
    
    total_cost: float = Field(..., description="Final verified trip cost")
    budget_buffer: float = Field(..., description="Remaining budget buffer in USD")
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for trip optimization"
    )
    
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in validation")


class PlannerOutput(BaseModel):
    """Planner Agent output — coordination summary."""

    destination: str = Field(..., description="Selected destination city")
    duration: str = Field(..., description="Trip duration string")
    total_budget: float = Field(..., description="Total budget in USD")
    within_budget: bool = Field(..., description="Whether plan is within budget")
    estimated_total_cost: float = Field(..., description="Estimated total cost")
    reasoning_steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Step-by-step coordination log"
    )
    coordination_notes: str = Field(default="", description="Planner coordination summary")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall plan confidence")


class FinalTravelPlan(BaseModel):
    """Final complete travel plan combining all agent outputs."""
    
    trip_id: Optional[int] = Field(None, description="Database trip ID if saved")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Original user input
    user_input: UserTravelInput = Field(...)
    
    # Agent outputs in sequence
    planner: Optional['PlannerOutput'] = Field(None, description="Planner agent coordination output")
    trip_feasibility: TripFeasibilityOutput = Field(...)
    destination: DestinationOutput = Field(...)
    route_logistics: Optional[Any] = Field(None, description="Route & Logistics agent output")
    schedule: ScheduleOutput = Field(...)
    validation: ValidationOutput = Field(...)
    
    # Overall plan status
    status: str = Field(default="completed", description="completed, needs_revision, failed")
    
    # Total plan statistics
    total_trip_cost: float = Field(..., description="Final total cost")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence in plan")
    
    # Execution recommendations
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps for user"
    )
