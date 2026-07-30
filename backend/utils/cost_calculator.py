"""
TravelGenie Single Source of Truth Cost Calculator

Dedicated reusable utility for calculating and validating all travel plan costs.
Consumed by:
- PlannerAgent
- ValidationAgent
- ScheduleAgent
- API Routes & Serialization
- PDF Export & Frontend Mapping
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class TripCostSummary:
    """Authoritative breakdown of trip costs."""
    user_budget: float
    hotel_cost: float
    transport_cost: float
    food_cost: float
    activities_cost: float
    emergency_buffer: float
    total_cost: float
    remaining_budget: float
    within_budget: bool
    utilization_pct: float
    
    # Category percentages
    hotel_pct: float
    food_pct: float
    activities_pct: float
    transport_pct: float
    emergency_pct: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary representation."""
        return {
            "user_budget": self.user_budget,
            "hotel_cost": self.hotel_cost,
            "transport_cost": self.transport_cost,
            "food_cost": self.food_cost,
            "activities_cost": self.activities_cost,
            "emergency_buffer": self.emergency_buffer,
            "total_cost": self.total_cost,
            "remaining_budget": self.remaining_budget,
            "within_budget": self.within_budget,
            "utilization_pct": self.utilization_pct,
            "hotel_pct": self.hotel_pct,
            "food_pct": self.food_pct,
            "activities_pct": self.activities_pct,
            "transport_pct": self.transport_pct,
            "emergency_pct": self.emergency_pct,
        }


def calculate_plan_costs(
    user_input: Any,
    destination: Any = None,
    route_logistics: Any = None,
    schedule: Any = None,
) -> TripCostSummary:
    """
    Calculate the authoritative cost breakdown for a travel plan.
    
    This is the SINGLE SOURCE OF TRUTH for:
    Hotel Cost + Selected Transport Cost + Food Cost + Activities Cost = Total Trip Cost
    
    Args:
        user_input: UserTravelInput model or dict
        destination: DestinationOutput model
        route_logistics: RouteLogisticsOutput model
        schedule: ScheduleOutput model
        
    Returns:
        TripCostSummary containing exact cost calculations
    """
    days = max(getattr(user_input, 'trip_days', 1), 1)
    user_budget = float(getattr(user_input, 'budget', 0.0))

    # 1. Hotel Cost: price_per_night * days
    hotel_cost = 0.0
    if destination and getattr(destination, 'selected_hotel', None):
        hotel_cost = round(float(destination.selected_hotel.price_per_night) * days, 2)
    elif schedule and getattr(schedule, 'accommodation_cost', None):
        hotel_cost = round(float(schedule.accommodation_cost), 2)

    # 2. Transport Cost: selected transport from route_logistics best_option
    transport_cost = 0.0
    if route_logistics:
        best = getattr(route_logistics, 'best_option', None)
        if best:
            if hasattr(best, 'total_cost'):
                transport_cost = round(float(best.total_cost), 2)
            elif isinstance(best, dict) and 'total_cost' in best:
                transport_cost = round(float(best['total_cost']), 2)

    if transport_cost == 0.0 and schedule and getattr(schedule, 'transport_cost', None):
        transport_cost = round(float(schedule.transport_cost), 2)

    # 3. Food Cost
    food_cost = 0.0
    if schedule and getattr(schedule, 'food_cost', None):
        food_cost = round(float(schedule.food_cost), 2)

    # 4. Activities Cost
    activities_cost = 0.0
    if schedule and getattr(schedule, 'activities_cost', None):
        activities_cost = round(float(schedule.activities_cost), 2)

    # 5. Total Cost
    total_cost = round(hotel_cost + transport_cost + food_cost + activities_cost, 2)

    # 6. Budget Status & Emergency Buffer
    remaining_budget = round(user_budget - total_cost, 2)
    emergency_buffer = max(0.0, remaining_budget)
    within_budget = total_cost <= user_budget
    utilization_pct = round((total_cost / user_budget) * 100, 1) if user_budget > 0 else 0.0

    # Category percentages relative to total cost
    den = total_cost if total_cost > 0 else 1.0
    hotel_pct = round((hotel_cost / den) * 100, 1)
    food_pct = round((food_cost / den) * 100, 1)
    activities_pct = round((activities_cost / den) * 100, 1)
    transport_pct = round((transport_cost / den) * 100, 1)
    emergency_pct = round((emergency_buffer / user_budget) * 100, 1) if user_budget > 0 else 0.0

    return TripCostSummary(
        user_budget=user_budget,
        hotel_cost=hotel_cost,
        transport_cost=transport_cost,
        food_cost=food_cost,
        activities_cost=activities_cost,
        emergency_buffer=emergency_buffer,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        within_budget=within_budget,
        utilization_pct=utilization_pct,
        hotel_pct=hotel_pct,
        food_pct=food_pct,
        activities_pct=activities_pct,
        transport_pct=transport_pct,
        emergency_pct=emergency_pct,
    )
