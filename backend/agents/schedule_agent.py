"""
TravelGenie Schedule Agent

Generates day-by-day itinerary for the trip.

Responsibilities:
- Create detailed daily schedule
- Allocate activities based on travel time
- Consider weather and opening hours
- Suggest meals and rest times
- Calculate daily costs
- Minimize unnecessary travel
"""

import json
import logging
from typing import List, Dict, Any
from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import (
    DestinationOutput,
    ScheduleOutput,
    ItineraryDay,
)
from backend.services.weather_service import get_weather_service
from backend.services.routing_service import get_routing_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScheduleAgent(AsyncBaseAgent):
    """
    Creates detailed day-wise itinerary for the trip.
    
    Input: DestinationOutput
    Output: ScheduleOutput
    
    This agent uses real travel times, weather, and attraction information
    to create an optimized, realistic schedule.
    """

    def __init__(self):
        """Initialize Schedule Agent."""
        super().__init__(
            name="Schedule",
            description="Generates optimized day-by-day itinerary"
        )
        self.weather_service = get_weather_service()
        self.routing_service = get_routing_service()

    def get_system_prompt(self) -> str:
        """
        Get system prompt for schedule generation.
        
        Returns:
            System prompt for LLM
        """
        return """You are an expert travel itinerary planner. Your task is to create a detailed, realistic day-by-day schedule for a trip.

INSTRUCTIONS:
1. Create practical daily schedules that respect:
   - Realistic travel times between locations
   - Opening hours of attractions
   - Weather conditions and suitable activities
   - Rest and meal times
   - Budget constraints
   
2. For each day, provide:
   - Clear timeline of activities (with specific times)
   - Meal recommendations (breakfast, lunch, dinner)
   - Hotel check-in/check-out if relevant
   - Transportation requirements
   - Estimated costs
   - Special notes or tips

3. Minimize unnecessary travel:
   - Group nearby attractions
   - Optimize movement through the city
   - Consider fatigue levels

4. Consider weather:
   - Don't recommend outdoor activities in heavy rain
   - Adjust for temperature extremes
   - Plan indoor alternatives

IMPORTANT:
- Return ONLY valid JSON (no markdown)
- All times must be realistic and specific (HH:MM format)
- Costs must be actual estimates, not guesses
- Include comprehensive packing recommendations
- Highlight critical information about the destination

Your response must be valid JSON matching the provided schema."""

    async def process(self, input_model: BaseModel) -> ScheduleOutput:
        """
        Generate itinerary schedule.
         
        Args:
            input_model: Either DestinationOutput or tuple of (DestinationOutput, UserTravelInput, TripFeasibilityOutput)
             
        Returns:
            ScheduleOutput with day-by-day itinerary
             
        Raises:
            AgentException: If processing fails
        """
        destination = None
        user_input = None
        feasibility = None
 
        if isinstance(input_model, tuple):
            if len(input_model) != 3:
                raise AgentException(
                    self.name,
                    f"Expected tuple of (DestinationOutput, UserTravelInput, TripFeasibilityOutput), got length {len(input_model)}"
                )
            destination, user_input, feasibility = input_model
        else:
            destination = input_model
 
        if not isinstance(destination, DestinationOutput):
            raise AgentException(
                self.name,
                f"Expected DestinationOutput, got {type(destination).__name__}"
            )
 
        self.last_destination = destination
        self.last_user_input = user_input
        self.last_feasibility = feasibility
 
        try:
            # Build user prompt with all available information
            user_prompt = self._build_user_prompt(destination, user_input)

            # Query LLM
            llm_response = await self.query_llm(user_prompt)
 
            # Parse and validate output
            if isinstance(llm_response, BaseModel):
                output = llm_response
            else:
                output = self.parse_json_output(llm_response, ScheduleOutput)

            # Validate reasonableness
            self._validate_schedule(output)

            return output

        except AgentException:
            raise
        except Exception as e:
            self.logger.error(f"Schedule generation failed: {e}")
            raise AgentException(self.name, f"Failed to generate schedule: {str(e)}", e)

    def _build_user_prompt(self, destination: DestinationOutput, user_input=None) -> str:
        """
        Build the user prompt for LLM.
         
        Args:
            destination: Destination information from previous agent
            user_input: Optional original user input for trip length and budget
             
        Returns:
            Formatted prompt for LLM
        """
        days = getattr(user_input, "trip_days", 3) if user_input else 3
        daily_budget = getattr(user_input, "budget", destination.estimated_cost_per_day if hasattr(destination, 'estimated_cost_per_day') else 0)
 
        attractions_info = json.dumps(
            [
                {
                    "name": a.name,
                    "category": a.category,
                    "visit_duration": a.visit_duration_hours,
                    "entry_fee": a.entry_fee,
                    "rating": a.rating,
                }
                for a in destination.attractions
            ],
            indent=2
        )

        weather_info = json.dumps(destination.weather.model_dump(), indent=2)

        hotel_info = json.dumps(
            {
                "name": destination.selected_hotel.name,
                "location": destination.selected_hotel.location.city,
                "price_per_night": destination.selected_hotel.price_per_night,
            },
            indent=2
        )

        return f"""Create a detailed {days}-day itinerary for this destination:
 
DESTINATION:
- City: {destination.destination.city}, {destination.destination.country}
- Coordinates: ({destination.destination.latitude}, {destination.destination.longitude})
 
ACCOMMODATION:
{hotel_info}
 
WEATHER:
{weather_info}
 
TOP ATTRACTIONS & ACTIVITIES:
{attractions_info}
 
TRAVEL LOGISTICS:
- Travel method: By local transport
- Daily budget for activities: Approximately ${min(max(daily_budget * 0.1, 20), 60):.0f}
- Trip start: Tomorrow morning
- Trip end: In {days} days
 
REQUIREMENTS:
1. Create a realistic {days}-day itinerary
2. Include specific times for all activities
3. Suggest meals at local restaurants
4. Minimize backtracking and travel time
5. Group nearby attractions
6. Account for weather conditions
7. Include buffer time for rest and shopping

EXAMPLE STRUCTURE:
{{
    "daily_itinerary": [
        {{
            "day_number": 1,
            "title": "Arrival & Exploration",
            "activities": [
                {{"time": "HH:MM", "duration_minutes": 120, "activity": "...", "location": "...", "cost_usd": 0}},
                ...
            ],
            "meals": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
            "hotel_check_in": "HH:MM",
            "hotel_check_out": null,
            "estimated_cost": 100,
            "transportation_needed": ["Metro", "Walking"],
            "notes": "..."
        }},
        ...
    ],
    "total_estimated_cost": number,
    "accommodation_cost": number,
    "food_cost": number,
    "transport_cost": number,
    "activities_cost": number,
    "transportation_method": "flight",
    "packing_recommendations": [...],
    "critical_notes": [...]
}}

Generate the complete itinerary now as valid JSON only."""
 
    async def fallback_response(self, user_prompt: str, system_prompt: str, output_model: type) -> ScheduleOutput:
        """
        Generate a fallback schedule when the LLM is unavailable.
        """
        destination = getattr(self, 'last_destination', None)
        if not isinstance(destination, DestinationOutput):
            raise AgentException(self.name, "Fallback unavailable without valid destination")
 
        days = 3
        itinerary = []
        for day in range(1, days + 1):
            attraction = destination.attractions[day - 1] if len(destination.attractions) >= day else destination.attractions[0]
            itinerary.append(
                {
                    "day_number": day,
                    "date": None,
                    "title": f"Explore {destination.destination.city} - Day {day}",
                    "activities": [
                        {
                            "time": "09:00",
                            "duration_minutes": 120,
                            "activity": f"Visit {attraction.name}",
                            "location": attraction.location.model_dump(),
                            "cost_usd": min(20.0, attraction.entry_fee),
                        },
                        {
                            "time": "13:00",
                            "duration_minutes": 90,
                            "activity": "Lunch at a local restaurant",
                            "location": destination.destination.model_dump(),
                            "cost_usd": 30.0,
                        },
                        {
                            "time": "15:00",
                            "duration_minutes": 90,
                            "activity": "Relax at the hotel and explore nearby spots",
                            "location": destination.selected_hotel.location.model_dump(),
                            "cost_usd": 10.0,
                        },
                    ],
                    "meals": {
                        "breakfast": "Hotel breakfast",
                        "lunch": "Local restaurant",
                        "dinner": "Street food or casual dining",
                    },
                    "hotel_check_in": "14:00" if day == 1 else None,
                    "hotel_check_out": "11:00" if day == days else None,
                    "estimated_cost": round(destination.estimated_cost_per_day, 2),
                    "transportation_needed": ["Local taxi", "Walking"],
                    "notes": "Keep the day relaxed and easy to navigate.",
                }
            )
 
        total_cost = round(destination.estimated_cost_per_day * days, 2)
        hotel_cost = round(destination.selected_hotel.price_per_night * days, 2)
        other_cost = round(total_cost - hotel_cost, 2)
 
        return ScheduleOutput(
            destination=destination.destination,
            start_date=None,
            end_date=None,
            daily_itinerary=[
                ItineraryDay(**day) for day in itinerary
            ],
            total_estimated_cost=total_cost,
            accommodation_cost=hotel_cost,
            food_cost=other_cost * 0.5,
            transport_cost=other_cost * 0.3,
            activities_cost=other_cost * 0.2,
            transportation_method="flight",
            transportation_details="Local transport and airport transfers",
            packing_recommendations=[
                "Comfortable shoes",
                "Light weather layers",
                "Travel adapter",
            ],
            critical_notes=[
                f"Book the hotel in advance for {destination.destination.city}",
            ],
        )
 
    def _validate_schedule(self, schedule: ScheduleOutput) -> None:
        """
        Validate the generated schedule for reasonableness.
        
        Args:
            schedule: Generated schedule
            
        Raises:
            AgentException: If schedule is invalid
        """
        # Check that we have the right number of days
        if not schedule.daily_itinerary:
            raise AgentException(self.name, "Schedule has no days")

        # Validate cost calculations
        calculated_total = (
            schedule.accommodation_cost
            + schedule.food_cost
            + schedule.transport_cost
            + schedule.activities_cost
        )

        # Allow 10% tolerance for rounding
        if abs(calculated_total - schedule.total_estimated_cost) > schedule.total_estimated_cost * 0.1:
            self.logger.warning(
                f"Cost calculation mismatch: calculated={calculated_total}, total={schedule.total_estimated_cost}"
            )

        # Validate daily costs
        for day in schedule.daily_itinerary:
            if day.estimated_cost < 0:
                raise AgentException(self.name, f"Day {day.day_number} has negative cost")


# Global Schedule Agent instance
_schedule_agent: ScheduleAgent = None


def get_schedule_agent() -> ScheduleAgent:
    """
    Get or create the global Schedule Agent instance.
    
    Returns:
        ScheduleAgent instance
    """
    global _schedule_agent
    if _schedule_agent is None:
        _schedule_agent = ScheduleAgent()
    return _schedule_agent
