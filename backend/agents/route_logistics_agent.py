"""
TravelGenie Route & Logistics Agent

Calculates travel distance, estimated travel time, and transport options
between the source city and the selected destination.

Responsibilities:
- Geocode source and destination cities
- Calculate travel distance (km) using geo service
- Estimate travel time for each transport mode
- Build transport option comparisons
- Return a structured RouteLogisticsOutput
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import UserTravelInput, DestinationOutput

logger = logging.getLogger(__name__)


class TransportOption(BaseModel):
    mode: str
    mode_emoji: str
    travel_time_hours: float
    travel_time_display: str
    total_cost: float
    cost_per_person: float
    overall_score: float
    co2_emissions_kg: float
    pros: List[str]
    cons: List[str]


class RouteLogisticsOutput(BaseModel):
    """Route & Logistics Agent output."""
    source: str = Field(..., description="Departure city")
    destination: str = Field(..., description="Destination city")
    travel_distance_km: float = Field(..., description="Distance in km")
    travel_time_hours: float = Field(..., description="Estimated travel time in hours")
    recommended_mode: str = Field(..., description="User's chosen transport mode")
    transport_options: List[TransportOption] = Field(default_factory=list)
    best_option: Optional[TransportOption] = None
    routing_notes: str = Field(default="", description="Notes about the route")


_MODE_CONFIG = {
    "flight": {"emoji": "✈️",  "cost_per_km": 0.20, "speed_kmh": 800, "co2_per_km": 0.24,
               "pros": ["Fastest option", "Comfortable for long distances"],
               "cons": ["Higher carbon footprint", "Airport time overhead"]},
    "train":  {"emoji": "🚆",  "cost_per_km": 0.12, "speed_kmh": 120, "co2_per_km": 0.06,
               "pros": ["Eco-friendly", "City-centre to city-centre"],
               "cons": ["Slower than flight", "Limited routes"]},
    "bus":    {"emoji": "🚌",  "cost_per_km": 0.08, "speed_kmh": 80,  "co2_per_km": 0.10,
               "pros": ["Most affordable", "Wide coverage"],
               "cons": ["Slowest option", "Less comfortable on long trips"]},
    "car":    {"emoji": "🚗",  "cost_per_km": 0.15, "speed_kmh": 100, "co2_per_km": 0.18,
               "pros": ["Flexible schedule", "Door-to-door convenience"],
               "cons": ["Fatigue on long drives", "Parking costs"]},
}


def _build_option(mode: str, distance_km: float) -> TransportOption:
    cfg = _MODE_CONFIG.get(mode, _MODE_CONFIG["car"])
    hours = round(max(distance_km / cfg["speed_kmh"], 0.5), 1)
    cost = round(max(distance_km * cfg["cost_per_km"], 20.0), 2)
    score = round(max(5.0, min(10.0, 10.0 - hours * 0.4)), 1)
    co2 = round(distance_km * cfg["co2_per_km"], 1)
    return TransportOption(
        mode=mode,
        mode_emoji=cfg["emoji"],
        travel_time_hours=hours,
        travel_time_display=f"{hours:.1f} hrs",
        total_cost=cost,
        cost_per_person=round(cost / 2, 2),
        overall_score=score,
        co2_emissions_kg=co2,
        pros=cfg["pros"],
        cons=cfg["cons"],
    )


class RouteLogisticsAgent(AsyncBaseAgent):
    """
    Calculates route and logistics between source and destination.

    Input:  tuple of (UserTravelInput, DestinationOutput)
    Output: RouteLogisticsOutput
    """

    def __init__(self):
        super().__init__(
            name="RouteLogistics",
            description="Calculates travel distance, time, and transport options",
        )

    def get_system_prompt(self) -> str:
        return (
            "You are a route and logistics specialist. "
            "Calculate travel distances and transport options accurately."
        )

    async def process(self, input_model: BaseModel) -> RouteLogisticsOutput:
        if not isinstance(input_model, tuple) or len(input_model) != 2:
            raise AgentException(
                self.name,
                f"Expected tuple of (UserTravelInput, DestinationOutput), got {type(input_model)}",
            )

        user_input, destination = input_model
        if not isinstance(user_input, UserTravelInput):
            raise AgentException(self.name, f"Expected UserTravelInput, got {type(user_input).__name__}")
        if not isinstance(destination, DestinationOutput):
            raise AgentException(self.name, f"Expected DestinationOutput, got {type(destination).__name__}")

        return await self._compute(user_input, destination)

    async def _compute(
        self, user_input: UserTravelInput, destination: DestinationOutput
    ) -> RouteLogisticsOutput:
        """Compute route logistics using geo service and destination data."""
        distance_km = destination.travel_distance
        dest_city = destination.destination.city

        # If destination already has a valid distance, use it directly.
        # Otherwise try to compute via geo service.
        if distance_km <= 0:
            try:
                from backend.services.geo_service import get_geo_service
                import asyncio
                geo = get_geo_service()
                src_loc = await asyncio.wait_for(geo.geocode(user_input.source_city), timeout=6.0)
                if src_loc:
                    distance_km = await geo.calculate_distance(
                        src_loc.latitude, src_loc.longitude,
                        destination.destination.latitude, destination.destination.longitude,
                    )
            except Exception as e:
                self.logger.warning(f"Geo distance fallback: {e}")
                distance_km = 1000.0

        distance_km = round(max(distance_km, 1.0), 1)

        # Build transport options for all 4 modes
        preferred = str(user_input.transportation).split(".")[-1].lower()
        all_modes = ["flight", "train", "bus", "car"]
        options = [_build_option(m, distance_km) for m in all_modes]

        # Put preferred mode first
        options.sort(key=lambda o: (o.mode != preferred, o.overall_score * -1))
        best = options[0]

        return RouteLogisticsOutput(
            source=user_input.source_city,
            destination=dest_city,
            travel_distance_km=distance_km,
            travel_time_hours=best.travel_time_hours,
            recommended_mode=preferred,
            transport_options=options,
            best_option=best,
            routing_notes=(
                f"Route from {user_input.source_city} to {dest_city}: "
                f"{distance_km} km. Recommended: {preferred} "
                f"({best.travel_time_hours} hrs, ${best.total_cost})."
            ),
        )


# ── Singleton ─────────────────────────────────────────────────────────

_route_logistics_agent: RouteLogisticsAgent = None


def get_route_logistics_agent() -> RouteLogisticsAgent:
    """Get or create the global RouteLogisticsAgent instance."""
    global _route_logistics_agent
    if _route_logistics_agent is None:
        _route_logistics_agent = RouteLogisticsAgent()
    return _route_logistics_agent
