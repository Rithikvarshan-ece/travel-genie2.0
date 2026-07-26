"""
Destination Agent - Real-Time Destination Selection

Uses live data from multiple services and Groq LLM to recommend the best destination.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import UserTravelInput, TripFeasibilityOutput, DestinationOutput, Location, HotelOption, Attraction, Season
from backend.services.geo_service import get_geo_service
from backend.services.places_service import get_places_service
from backend.services.routing_service import get_routing_service, TransportMode
from backend.services.weather_service import get_weather_service

logger = logging.getLogger(__name__)


class DestinationAgent(AsyncBaseAgent):
    """Selects best destination using real-time data from all services."""

    def __init__(self):
        super().__init__(
            name="Destination Agent",
            description="Selects best destination using real-time data"
        )

    async def process(self, input_model: BaseModel) -> DestinationOutput:
        """
        Process input for the destination agent.

        Args:
            input_model: Tuple of (UserTravelInput, TripFeasibilityOutput)

        Returns:
            DestinationOutput
        """
        if not isinstance(input_model, tuple) or len(input_model) != 2:
            raise AgentException(
                self.name,
                f"Expected tuple of (UserTravelInput, TripFeasibilityOutput), got {type(input_model).__name__}"
            )
 
        user_input, feasibility = input_model
        self.last_user_input = user_input
        self.last_feasibility = feasibility
        if not isinstance(user_input, UserTravelInput):
            raise AgentException(
                self.name,
                f"Expected UserTravelInput for first tuple item, got {type(user_input).__name__}"
            )
        if not isinstance(feasibility, TripFeasibilityOutput):
            raise AgentException(
                self.name,
                f"Expected TripFeasibilityOutput for second tuple item, got {type(feasibility).__name__}"
            )

        return await self.invoke(user_input, feasibility)

    async def invoke(self, user_input: UserTravelInput, feasibility: TripFeasibilityOutput) -> DestinationOutput:
        """
        Select best destination using real-time data.
        
        Args:
            user_input: User travel requirements
            feasibility: Trip feasibility assessment
            
        Returns:
            DestinationOutput with selected destination and details
        """
        try:
            self.last_user_input = user_input
            self.last_feasibility = feasibility
            logger.info(f"Geo Destination Agent: Selecting destination for {user_input.source_city}")
             
            # Get service instances
            geo = get_geo_service()
            places = get_places_service()
            routing = get_routing_service()
            weather = get_weather_service()
            
            # Get candidate destinations
            candidates = self._get_candidates(user_input)
            logger.info(f"Location Evaluating {len(candidates)} destination candidates")
            
            # Get source location once
            source_location = await geo.geocode(user_input.source_city)
            if not source_location:
                logger.warning(f"Warning Could not geocode source {user_input.source_city}")
                source_location = Location(
                    latitude=0.0,
                    longitude=0.0,
                    city=user_input.source_city,
                    country="Unknown",
                )
            
            source_lat = source_location.latitude
            source_lon = source_location.longitude
            
            # Gather real data for each candidate
            candidates_data = []
            for candidate in candidates:
                try:
                    # Geocode destination
                    dest_location = await geo.geocode(candidate)
                    if not dest_location:
                        logger.warning(f"Warning Could not geocode {candidate}")
                        continue
                    
                    # Get distance and travel time
                    dest_lat = dest_location.latitude
                    dest_lon = dest_location.longitude
 
                    route = await routing.get_distance(
                        start=(source_lat, source_lon),
                        end=(dest_lat, dest_lon),
                        mode=TransportMode.CAR
                    )
                    
                    # Search for hotels
                    hotels = await places.search_hotels(
                        latitude=dest_lat,
                        longitude=dest_lon,
                        max_results=5,
                    )
                    
                    # Search for attractions
                    attractions = await places.search_attractions(
                        latitude=dest_lat,
                        longitude=dest_lon,
                        max_results=7,
                    )
                    
                    # Get weather
                    current_weather = await weather.get_current_weather(
                        latitude=dest_lat,
                        longitude=dest_lon,
                    )
                    
                    candidates_data.append({
                        "name": candidate,
                        "location": dest_location,
                        "distance_km": route.get("distance_km", 0) if route else 0,
                        "travel_hours": route.get("duration_hours", 0) if route else 0,
                        "hotels": hotels or [],
                        "attractions": attractions or [],
                        "weather": current_weather,
                        "daily_budget_estimate": feasibility.daily_budget,
                    })
                    
                except Exception as e:
                    logger.error(f"Error Error processing candidate {candidate}: {e}")
                    continue
            
            if not candidates_data:
                logger.warning("Warning No valid candidates found from live services. Falling back to internal destination selection.")
                return await self.fallback_response("", "", DestinationOutput)
             
            # Use Groq to select best destination
            best = await self._select_best_with_groq(
                user_input, feasibility, candidates_data
            )
            
            logger.info(f"Selected destination: {best.destination.city}, {best.destination.country}")
            return best
            
        except Exception as e:
            logger.error(f"Error Destination Agent error: {e}")
            raise

    async def _select_best_with_groq(
        self,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput,
        candidates_data: List
    ) -> DestinationOutput:
        """Use Groq to select best destination from candidates."""
        
        # Build prompt with real data
        prompt = self._build_prompt(user_input, feasibility, candidates_data)
        
        # Query Groq
        response = await self.query_llm(
            system_prompt=self.get_system_prompt(),
            user_prompt=prompt,
            output_model=DestinationOutput
        )
        
        return response

    def _build_prompt(self, user_input: UserTravelInput, feasibility: TripFeasibilityOutput, candidates_data: List) -> str:
        """Build prompt with real data for Groq."""
        
        candidates_info = "\n\n".join([
            f"""
Destination: {c['name']}
Location: {c['location'].city}, {c['location'].country}
Distance: {c['distance_km']} km ({c['travel_hours']} hours)
Hotels Available: {len(c['hotels'])}
Attractions: {len(c['attractions'])}
Weather: {c['weather'].condition}
Daily Budget Estimate: ${c['daily_budget_estimate']:.2f}
"""
            for c in candidates_data[:3]  # Top 3
        ])
        
        return f"""
Select the BEST destination for this trip:
 
User Requirements:
- Budget: ${user_input.budget} ({feasibility.daily_budget} per day)
- Duration: {user_input.trip_days} days
- Travel Type: {user_input.travel_type}
- Interests: {', '.join(user_input.interests)}
- Hotel Preference: {user_input.hotel_preference}
- Travel Month: {user_input.travel_month}
 
Candidate Destinations with Real Data:
{candidates_info}
 
Select ONE destination and provide:
1. Destination name
2. Reason for selection
3. Top 3 hotels (extract from available)
4. Top 5 attractions (extract from available)
5. Weather compatibility
6. Estimated total cost
7. Confidence score (0-100)
 
Return ONLY valid JSON matching DestinationOutput schema.
"""
 
    async def fallback_response(self, user_prompt: str, system_prompt: str, output_model: type) -> DestinationOutput:
        """
        Generate a fallback destination recommendation when the LLM is unavailable.
        """
        user_input = getattr(self, 'last_user_input', None)
        feasibility = getattr(self, 'last_feasibility', None)
        if not isinstance(user_input, UserTravelInput) or not isinstance(feasibility, TripFeasibilityOutput):
            raise AgentException(self.name, "Fallback unavailable without valid input")
 
        candidates = self._get_candidates(user_input)
        selected_name = candidates[0] if candidates else user_input.source_city
 
        # Default hotel option with modest values
        hotel = HotelOption(
            name=f"{selected_name} Comfort Stay",
            category=user_input.hotel_preference,
            price_per_night=max(20.0, feasibility.daily_budget * 0.35),
            rating=4.0,
            amenities=["Free WiFi", "Breakfast included", "Central location"],
            location=Location(
                latitude=0.0,
                longitude=0.0,
                city=selected_name,
                country="Unknown",
                region=None,
            ),
            reviews_count=120,
            check_in_checkout="14:00 / 11:00",
            description="Comfortable stay with convenient access to local attractions.",
        )
 
        # Use weather service fallback or default weather
        weather_service = get_weather_service()
        weather = await weather_service.get_current_weather(0.0, 0.0) if weather_service else None
        if weather is None:
            weather = weather = weather_service._get_fallback_weather() if weather_service else None
 
        attraction = Attraction(
            name=f"Top attraction in {selected_name}",
            category="sightseeing",
            location=Location(
                latitude=0.0,
                longitude=0.0,
                city=selected_name,
                country="Unknown",
                region=None,
            ),
            rating=4.0,
            distance_from_city_center=1.5,
            visit_duration_hours=2.0,
            entry_fee=10.0,
            opening_hours="09:00-18:00",
            description="A popular local landmark and cultural experience.",
        )
 
        return DestinationOutput(
            destination=Location(
                latitude=0.0,
                longitude=0.0,
                city=selected_name,
                country="Unknown",
                region=None,
            ),
            reason=(
                f"{selected_name} is a strong match for a {user_input.travel_type} trip with interests in {', '.join(user_input.interests)}. "
                "It offers a balanced mix of attractions, hotel quality, and affordability."
            ),
            best_season=Season.SUMMER,
            weather=weather,
            hotel_options=[hotel],
            selected_hotel=hotel,
            attractions=[attraction],
            travel_distance=feasibility.max_affordable_distance,
            travel_time_hours=min(feasibility.max_affordable_distance / 80.0, 12.0),
            estimated_cost_per_day=feasibility.daily_budget,
            feasibility_with_budget=feasibility.is_feasible,
            confidence_score=feasibility.confidence_score,
        )
 
    def _get_candidates(self, user_input: UserTravelInput) -> List[str]:
        """Get destination candidates based on interests and travel type."""
        
        # Base destination suggestions for travel type
        travel_map = {
            "couple": ["Paris", "Venice", "Bali", "Santorini", "Kyoto"],
            "family": ["Orlando", "Tokyo", "Singapore", "Barcelona", "Sydney"],
            "friends": ["Bangkok", "Berlin", "Lisbon", "Prague", "Ho Chi Minh City"],
            "solo": ["Lisbon", "Chiang Mai", "Budapest", "Seoul", "Barcelona"],
        }

        base_candidates = travel_map.get(user_input.travel_type, ["Rome", "Paris", "Tokyo"])

        interest_map = {
            "nature": ["New Zealand", "Costa Rica", "Iceland"],
            "adventure": ["Nepal", "Peru", "Queenstown"],
            "food": ["Bangkok", "Istanbul", "Lima"],
            "shopping": ["Dubai", "Seoul", "Tokyo"],
            "historical": ["Rome", "Athens", "Kyoto"],
            "beach": ["Bali", "Phuket", "Maldives"],
            "nightlife": ["Berlin", "Miami", "Bangkok"],
            "culture": ["Paris", "Istanbul", "Kyoto"],
        }

        candidate_pool = list(base_candidates)
        for interest in user_input.interests:
            candidate_pool += interest_map.get(interest.lower(), [])

        # Deduplicate and preserve order
        seen = set()
        return [city for city in candidate_pool if not (city in seen or seen.add(city))][:8]

    def get_system_prompt(self) -> str:
        """System prompt for Groq."""
        return """You are an expert travel planner. 

Analyze destination candidates and select the ONE BEST destination based on:
1. Budget feasibility
2. Travel distance and time
3. Availability of user interests
4. Weather conditions
5. Hotel options and quality
6. Overall trip value and experience

Return ONLY valid JSON matching the DestinationOutput schema with the following fields:
- destination: {"latitude": number, "longitude": number, "city": string, "country": string, "region": string | null}
- reason: string
- best_season: string
- weather: {"current_temp": number, "max_temp": number, "min_temp": number, "condition": string, "rain_probability": number, "humidity": number, "wind_speed": number, "warnings": [string]}
- hotel_options: [ {"name": string, "category": string, "price_per_night": number, "rating": number, "amenities": [string], "location": {"latitude": number, "longitude": number, "city": string, "country": string, "region": string | null}, "reviews_count": number, "check_in_checkout": string | null, "description": string | null } ]
- selected_hotel: same structure as hotel_options items
- attractions: [ {"name": string, "category": string, "location": {"latitude": number, "longitude": number, "city": string, "country": string, "region": string | null}, "rating": number, "distance_from_city_center": number, "visit_duration_hours": number, "entry_fee": number, "opening_hours": string | null, "description": string | null } ]
- travel_distance: number
- travel_time_hours: number
- estimated_cost_per_day: number
- feasibility_with_budget: boolean
- confidence_score: number (0.0-1.0)

STRICT REQUIREMENTS:
- ONLY JSON output
- NO explanations
- NO markdown
- VALID schema"""


# Singleton instance
_destination_agent: Optional[DestinationAgent] = None


def get_destination_agent() -> DestinationAgent:
    """Get or create singleton instance."""
    global _destination_agent
    if _destination_agent is None:
        _destination_agent = DestinationAgent()
    return _destination_agent

