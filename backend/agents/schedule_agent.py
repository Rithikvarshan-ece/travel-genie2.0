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
 
        route_logistics = None

        if isinstance(input_model, tuple):
            if len(input_model) == 4:
                destination, user_input, feasibility, route_logistics = input_model
            elif len(input_model) == 3:
                destination, user_input, feasibility = input_model
            else:
                raise AgentException(
                    self.name,
                    f"Expected tuple of (DestinationOutput, UserTravelInput, TripFeasibilityOutput, optional RouteLogisticsOutput), got length {len(input_model)}"
                )
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
        self.last_route_logistics = route_logistics

        try:
            # Build user prompt with all available information
            user_prompt = self._build_user_prompt(destination, user_input)

            # Query LLM with output model for direct parsing
            llm_response = await self.query_llm(
                user_prompt=user_prompt,
                system_prompt=self.get_system_prompt(),
                output_model=ScheduleOutput,
            )

            # Validate reasonableness & sync costs via central cost calculator
            output = llm_response
            from backend.utils.cost_calculator import calculate_plan_costs
            summary = calculate_plan_costs(user_input, destination, route_logistics, output)
            output.accommodation_cost = summary.hotel_cost
            output.transport_cost = summary.transport_cost
            output.food_cost = summary.food_cost
            output.activities_cost = summary.activities_cost
            output.total_estimated_cost = summary.total_cost
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
    "destination": {{"latitude": {destination.destination.latitude}, "longitude": {destination.destination.longitude}, "city": "{destination.destination.city}", "country": "{destination.destination.country}", "region": null}},
    "start_date": null,
    "end_date": null,
    "daily_itinerary": [
        {{
            "day_number": 1,
            "title": "Arrival & Exploration",
            "activities": [
                {{"time": "HH:MM", "duration_minutes": 120, "activity": "...", "location": "...", "cost_usd": 0}},
                ...
            ],
            "meals": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
            "hotel_check_in": "14:00",
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
        """Generate a rich fallback schedule using real attraction data from DestinationAgent."""
        destination = getattr(self, 'last_destination', None)
        user_input = getattr(self, 'last_user_input', None)
        if not isinstance(destination, DestinationOutput):
            raise AgentException(self.name, "Fallback unavailable without valid destination")

        days = getattr(user_input, 'trip_days', 3) if user_input else 3
        city = destination.destination.city
        attractions = destination.attractions  # real attractions from DestinationAgent
        n = len(attractions)

        # Meal suggestions based on city
        CITY_MEALS = {
            "Paris":     {"b": "Café de Flore breakfast", "l": "Brasserie lunch near the Louvre", "d": "Dinner at a bistro in Le Marais"},
            "Bangkok":   {"b": "Khao tom (rice soup) at a street stall", "l": "Pad Thai at Thip Samai", "d": "Rooftop dinner at Vertigo"},
            "Tokyo":     {"b": "Tamago gohan at hotel", "l": "Ramen at Ichiran", "d": "Sushi at Tsukiji Outer Market"},
            "Mumbai":    {"b": "Vada pav at a local stall", "l": "Thali at Swati Snacks", "d": "Seafood dinner at Trishna"},
            "Delhi":     {"b": "Paratha at Paranthe Wali Gali", "l": "Butter chicken at Moti Mahal", "d": "Dinner at Indian Accent"},
            "Goa":       {"b": "Poha and chai at a beach shack", "l": "Fish curry rice at a local restaurant", "d": "Seafood BBQ at Baga Beach"},
            "Jaipur":    {"b": "Pyaaz kachori at Rawat Mishthan", "l": "Dal baati churma at Chokhi Dhani", "d": "Dinner at 1135 AD, Amber Fort"},
            "Chennai":   {"b": "Idli sambar at Murugan Idli Shop", "l": "Chettinad lunch at Ponnusamy Hotel", "d": "Dinner at Copper Chimney"},
            "Bali":      {"b": "Nasi goreng at the hotel", "l": "Babi guling at Ibu Oka", "d": "Sunset dinner at Jimbaran Bay"},
            "Singapore": {"b": "Kaya toast at Ya Kun", "l": "Chicken rice at Tian Tian", "d": "Dinner at Lau Pa Sat hawker centre"},
            "Dubai":     {"b": "Shakshuka at a café", "l": "Al Faham chicken at Al Mallah", "d": "Dinner at Pierchic"},
            "Rome":      {"b": "Cornetto and cappuccino at a bar", "l": "Cacio e pepe at Tonnarello", "d": "Dinner at La Pergola"},
            "Barcelona": {"b": "Pan con tomate at a café", "l": "Tapas at El Xampanyet", "d": "Paella dinner at La Mar Salada"},
            "Kyoto":     {"b": "Tofu kaiseki breakfast", "l": "Soba noodles at Honke Tagoto", "d": "Kaiseki dinner at Kikunoi"},
        }
        meals_tmpl = CITY_MEALS.get(city, {
            "b": "Breakfast at the hotel",
            "l": "Lunch at a local restaurant",
            "d": "Dinner at a recommended restaurant",
        })

        itinerary = []
        # Distribute attractions across days: 2 per day, cycling if needed
        for day in range(1, days + 1):
            # Pick 2 attractions for this day
            a1 = attractions[(day * 2 - 2) % n]
            a2 = attractions[(day * 2 - 1) % n]

            activities = [
                {"time": "08:00", "duration_minutes": 45,  "activity": meals_tmpl["b"],
                 "location": city, "cost_usd": 5.0},
                {"time": "09:30", "duration_minutes": int(a1.visit_duration_hours * 60),
                 "activity": f"Visit {a1.name}",
                 "location": a1.name, "cost_usd": a1.entry_fee},
                {"time": "12:30", "duration_minutes": 60,  "activity": meals_tmpl["l"],
                 "location": city, "cost_usd": 12.0},
                {"time": "14:30", "duration_minutes": int(a2.visit_duration_hours * 60),
                 "activity": f"Explore {a2.name}",
                 "location": a2.name, "cost_usd": a2.entry_fee},
                {"time": "17:30", "duration_minutes": 60,  "activity": "Evening stroll and local shopping",
                 "location": city, "cost_usd": 10.0},
                {"time": "19:30", "duration_minutes": 90,  "activity": meals_tmpl["d"],
                 "location": city, "cost_usd": 20.0},
            ]

            day_cost = sum(act["cost_usd"] for act in activities)
            itinerary.append(ItineraryDay(
                day_number=day,
                date=None,
                title=f"Day {day} — {a1.name} & {a2.name}",
                activities=activities,
                meals={"breakfast": meals_tmpl["b"], "lunch": meals_tmpl["l"], "dinner": meals_tmpl["d"]},
                hotel_check_in="14:00" if day == 1 else None,
                hotel_check_out="11:00" if day == days else None,
                estimated_cost=round(day_cost, 2),
                transportation_needed=["Metro", "Walking", "Auto-rickshaw"],
                notes=f"Book tickets for {a1.name} in advance. Carry water and sunscreen.",
            ))

        route_logistics = getattr(self, 'last_route_logistics', None)
        from backend.utils.cost_calculator import calculate_plan_costs
        summary = calculate_plan_costs(user_input, destination, route_logistics, None)

        return ScheduleOutput(
            destination=destination.destination,
            start_date=None,
            end_date=None,
            daily_itinerary=itinerary,
            total_estimated_cost=summary.total_cost,
            accommodation_cost=summary.hotel_cost,
            food_cost=summary.food_cost,
            transport_cost=summary.transport_cost,
            activities_cost=summary.activities_cost,
            transportation_method=getattr(user_input, 'transportation', 'flight') if user_input else 'flight',
            transportation_details="Local metro, taxis, and walking recommended.",
            packing_recommendations=[
                "Comfortable walking shoes",
                "Universal travel adapter",
                "Light layers for weather changes",
                "Portable charger",
                "Travel insurance documents",
            ],
            critical_notes=[
                f"Book {destination.selected_hotel.name} at least 2 weeks in advance.",
                f"Check visa requirements for {destination.destination.country}.",
                "Carry local currency for small vendors.",
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
