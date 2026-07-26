# 🎯 IMMEDIATE NEXT STEPS - Do This First

## Current State
✅ Foundation complete  
✅ Services complete  
✅ 3 of 4 agents complete  
✅ Workflow structure complete  
❌ **Destination Agent needs completion** ← THIS BLOCKS EVERYTHING  
❌ **Testing not started**  

---

## HIGHEST PRIORITY: Complete Destination Agent

### Why This is Blocking
- LangGraph workflow has a `NotImplementedError` in the destination node
- API endpoint `/api/plan` will fail if you test it now
- The system cannot select destinations without this agent

### Current Code (agents/destination_agent.py)
Currently has OLD static code:
```python
DESTINATIONS = [
    {"name": "Bali", "country": "Indonesia", ...},  # ← REMOVE THIS
    # Old hardcoded data
]
```

### What Needs to Change

Replace entire `destination_agent.py` with this pattern (follow exactly):

```python
"""Destination Agent - Selects best travel destination using real-time data."""

from typing import Optional
from pydantic import Field
from config import get_settings
from models import UserTravelInput, TripFeasibilityOutput, DestinationOutput
from agents.async_base_agent import AsyncBaseAgent
from services.geo_service import get_geo_service
from services.places_service import get_places_service
from services.routing_service import get_routing_service
from services.weather_service import get_weather_service
import json
import logging

logger = logging.getLogger(__name__)


class DestinationAgent(AsyncBaseAgent):
    """
    Analyzes feasibility output and determines best destination.
    
    Uses real-time data from:
    - GeoService (Nominatim)
    - PlacesService (Overpass)
    - RoutingService (OSRM)
    - WeatherService (OpenWeatherMap)
    
    Then asks Groq to select BEST destination based on user requirements.
    """
    
    async def process(
        self,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput
    ) -> DestinationOutput:
        """
        Process destination selection.
        
        Flow:
        1. Geocode source city
        2. Get 5-10 destination candidates
        3. Gather real data for each (hotels, attractions, weather)
        4. Use Groq to select BEST
        5. Return structured output
        """
        
        try:
            # Step 1: Geocode source location
            geo_service = get_geo_service()
            source_coords = await geo_service.geocode(
                user_input.source_city
            )
            if not source_coords:
                raise ValueError(f"Cannot geocode source: {user_input.source_city}")
            
            # Step 2: Determine destination candidates based on interests
            # (This is a simplified approach - you could also have a list of recommendations)
            candidates = await self._get_destination_candidates(
                interests=user_input.interests,
                travel_style=user_input.travel_style
            )
            
            # Step 3: Gather data for each candidate
            destination_data = []
            for candidate in candidates:
                data = await self._gather_destination_data(
                    candidate=candidate,
                    source_coords=source_coords,
                    travel_days=user_input.trip_days,
                    budget=feasibility.daily_budget,
                    travel_month=user_input.travel_month
                )
                destination_data.append(data)
            
            # Step 4: Use Groq to select BEST destination
            best_destination = await self._select_best_destination(
                user_input=user_input,
                feasibility=feasibility,
                candidates_data=destination_data
            )
            
            return best_destination
            
        except Exception as e:
            logger.error(f"Destination agent error: {e}")
            raise
    
    async def _get_destination_candidates(
        self,
        interests: list[str],
        travel_style: str
    ) -> list[dict]:
        """
        Get 5-10 destination candidates based on interests.
        
        TODO: Implement recommendation logic
        For now, return popular destinations matching travel style.
        """
        
        # Simple heuristic mapping
        style_destinations = {
            "couple": ["Paris", "Venice", "Barcelona", "Bangkok", "Bali"],
            "family": ["Orlando", "Tokyo", "Singapore", "Dubai", "Barcelona"],
            "adventure": ["Nepal", "Peru", "New Zealand", "Iceland", "Colorado"],
            "budget": ["Vietnam", "Cambodia", "Thailand", "Philippines", "Mexico"],
            "luxury": ["Maldives", "Maldives", "Switzerland", "Paris", "Japan"]
        }
        
        base_destinations = style_destinations.get(travel_style, [
            "Rome", "London", "Amsterdam", "Tokyo", "New York"
        ])
        
        return [
            {"name": dest, "country": "TBD"}
            for dest in base_destinations[:5]
        ]
    
    async def _gather_destination_data(
        self,
        candidate: dict,
        source_coords: dict,
        travel_days: int,
        budget: float,
        travel_month: str
    ) -> dict:
        """Gather real-time data for a destination candidate."""
        
        try:
            geo_service = get_geo_service()
            places_service = get_places_service()
            routing_service = get_routing_service()
            weather_service = get_weather_service()
            
            # Geocode destination
            dest_coords = await geo_service.geocode(candidate["name"])
            if not dest_coords:
                return None
            
            # Calculate distance
            distance = await routing_service.get_distance(
                start=(source_coords["latitude"], source_coords["longitude"]),
                end=(dest_coords["latitude"], dest_coords["longitude"]),
                mode="car"  # Could be configurable
            )
            
            # Get nearby hotels
            hotels = await places_service.search_nearby(
                latitude=dest_coords["latitude"],
                longitude=dest_coords["longitude"],
                search_type="hotels",
                radius=5000
            )
            
            # Get nearby attractions
            attractions = await places_service.search_nearby(
                latitude=dest_coords["latitude"],
                longitude=dest_coords["longitude"],
                search_type="attractions",
                radius=15000
            )
            
            # Get weather forecast
            weather = await weather_service.get_current_weather(
                latitude=dest_coords["latitude"],
                longitude=dest_coords["longitude"]
            )
            
            return {
                "name": candidate["name"],
                "coordinates": dest_coords,
                "distance_km": distance.get("distance_km") if distance else 0,
                "travel_hours": distance.get("travel_hours") if distance else 0,
                "hotels_available": len(hotels) if hotels else 0,
                "attractions_available": len(attractions) if attractions else 0,
                "top_hotels": hotels[:3] if hotels else [],
                "top_attractions": attractions[:5] if attractions else [],
                "current_weather": weather,
                "best_season": self._get_best_season(travel_month),
                "feasibility_score": self._calculate_feasibility(
                    distance=distance,
                    budget=budget,
                    hotels_count=len(hotels) if hotels else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Error gathering data for {candidate['name']}: {e}")
            return None
    
    async def _select_best_destination(
        self,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput,
        candidates_data: list[dict]
    ) -> DestinationOutput:
        """Use Groq to select BEST destination from candidates."""
        
        # Build user prompt with all candidate data
        user_prompt = self._build_selection_prompt(
            user_input=user_input,
            feasibility=feasibility,
            candidates_data=candidates_data
        )
        
        # Get Groq response
        response = await self.query_llm(
            system_prompt=self.get_system_prompt(),
            user_prompt=user_prompt,
            output_model=DestinationOutput
        )
        
        return response
    
    def get_system_prompt(self) -> str:
        """System prompt for destination selection."""
        return """You are an expert travel planner selecting the BEST destination.

Analyze the provided candidates based on:
1. Budget feasibility
2. Travel distance
3. Availability of requested attractions
4. Weather conditions for travel dates
5. Hotel options and prices
6. Overall trip value

Select ONE best destination and explain your reasoning.
Provide specific hotel recommendations, top attractions, and day-wise activities.

ALWAYS return valid JSON matching the DestinationOutput schema.
NO MARKDOWN, NO EXPLANATIONS, ONLY JSON."""
    
    def _build_selection_prompt(
        self,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput,
        candidates_data: list[dict]
    ) -> str:
        """Build prompt for Groq to select destination."""
        
        candidates_str = json.dumps(candidates_data, indent=2)
        
        return f"""
User Travel Requirements:
- Budget: ${user_input.budget} ({feasibility.daily_budget} per day)
- Travel Days: {user_input.trip_days}
- Travel Style: {user_input.travel_style}
- Interests: {', '.join(user_input.interests)}
- Hotel Preference: {user_input.hotel_preference}
- Travel Month: {user_input.travel_month}

Candidate Destinations with Real Data:
{candidates_str}

Select the BEST destination and return in DestinationOutput format with:
- destination name
- coordinates
- recommended_hotel (from top_hotels)
- nearby_attractions (select top 5)
- transport_mode and estimated_days_for_travel
- reason for selection
- weather_compatibility
- estimated_total_cost
"""
    
    def _calculate_feasibility(
        self,
        distance: dict,
        budget: float,
        hotels_count: int
    ) -> float:
        """Calculate feasibility score (0-100)."""
        
        score = 50
        
        # Adjust for distance
        travel_hours = distance.get("travel_hours", 0) if distance else 0
        if travel_hours < 8:
            score += 20
        elif travel_hours < 24:
            score += 10
        
        # Adjust for hotel availability
        if hotels_count > 10:
            score += 20
        elif hotels_count > 5:
            score += 10
        
        # Adjust for budget
        if budget > 100:  # per day
            score += 10
        
        return min(score, 100)
    
    def _get_best_season(self, travel_month: str) -> str:
        """Determine travel season suitability."""
        
        month_num = self._parse_month(travel_month)
        
        if month_num in [12, 1, 2]:
            return "winter"
        elif month_num in [3, 4, 5]:
            return "spring"
        elif month_num in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _parse_month(self, month_str: str) -> int:
        """Parse month string to number."""
        
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        return months.get(month_str.lower(), 6)


# Singleton instance
_destination_agent: Optional[DestinationAgent] = None


def get_destination_agent() -> DestinationAgent:
    """Get or create singleton instance."""
    global _destination_agent
    if _destination_agent is None:
        _destination_agent = DestinationAgent()
    return _destination_agent
```

### Testing This Agent Locally

```python
# test_destination_locally.py
import asyncio
from models import UserTravelInput, TripFeasibilityOutput
from agents.destination_agent import get_destination_agent

async def test():
    agent = get_destination_agent()
    
    user_input = UserTravelInput(
        budget=5000,
        source_city="Mumbai",
        trip_days=7,
        travelers=2,
        travel_style="couple",
        transportation="flight",
        interests=["beaches", "food", "culture"],
        hotel_preference="resort",
        travel_month="July"
    )
    
    feasibility = TripFeasibilityOutput(
        is_feasible=True,
        daily_budget=714.29,  # 5000/7
        max_distance_km=2000,
        budget_allocation={...}
    )
    
    result = await agent.process(user_input, feasibility)
    print(result)

asyncio.run(test())
```

---

## SECOND PRIORITY: Integration Testing

Create `tests/integration/test_workflow.py`:

```python
"""Test complete workflow end-to-end."""

import pytest
from workflow import plan_trip
from models import UserTravelInput

@pytest.mark.asyncio
async def test_complete_workflow():
    """Test all agents working together."""
    
    user_input = UserTravelInput(
        budget=3000,
        source_city="New York",
        trip_days=5,
        travelers=2,
        travel_style="couple",
        transportation="flight",
        interests=["food", "culture"],
        hotel_preference="hotel",
        travel_month="July"
    )
    
    result = await plan_trip(user_input)
    
    # Assertions
    assert result is not None
    assert result.destination is not None
    assert result.schedule is not None
    assert result.validation.is_valid

@pytest.mark.asyncio
async def test_error_handling():
    """Test system handles bad input gracefully."""
    
    user_input = UserTravelInput(
        budget=-1000,  # Invalid
        source_city="UnknownCity12345",
        trip_days=0,
        travelers=0,
        travel_style="invalid",
        transportation="teleport",
        interests=[],
        hotel_preference="none",
        travel_month="invalid"
    )
    
    with pytest.raises(ValueError):
        await plan_trip(user_input)
```

---

## THIRD PRIORITY: Update Main Routes

Edit `backend/api/main.py`:

```python
# Change from:
from api.routes import router
# To:
from api.async_routes import router

# OR include both:
from api import routes, async_routes
app.include_router(async_routes.router, prefix="/api")
```

---

## FOURTH PRIORITY: Environment Setup

Create `backend/.env`:

```
GROQ_API_KEY=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

# Services
GEO_SERVICE_ENABLED=true
PLACES_SERVICE_ENABLED=true
ROUTING_SERVICE_ENABLED=true
WEATHER_SERVICE_ENABLED=true
CACHE_SERVICE_ENABLED=true

# Timeouts
REQUEST_TIMEOUT=30
LLM_TIMEOUT=60

# Groq
GROQ_MODEL=mixtral-8x7b-32768
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=2048

# API URLs
GEO_SERVICE_URL=https://nominatim.openstreetmap.org
PLACES_SERVICE_URL=https://overpass-api.de
ROUTING_SERVICE_URL=https://router.project-osrm.org
WEATHER_SERVICE_URL=https://api.openweathermap.org

# Database
DATABASE_URL=sqlite:///./travel_genie.db
MONGODB_URL=mongodb://localhost:27017/travelgenie

# Logging
LOG_LEVEL=INFO
```

---

## How to Run After Completing

```bash
# 1. Complete destination agent
# (Edit agents/destination_agent.py with code above)

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your Groq API key

# 4. Test locally
python -m pytest tests/ -v

# 5. Run server
python -m uvicorn api.main:app --reload

# 6. Test endpoint
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 3000,
    "source_city": "New York",
    "trip_days": 5,
    "travelers": 2,
    "travel_style": "couple",
    "transportation": "flight",
    "interests": ["food", "culture"],
    "hotel_preference": "hotel",
    "travel_month": "July"
  }'
```

---

## Estimated Effort

| Task | Time | Status |
|------|------|--------|
| Complete Destination Agent | 2-3 hours | 🔴 CRITICAL |
| Write integration tests | 1-2 hours | 🔴 CRITICAL |
| Update main.py | 30 min | 🟡 NEEDED |
| Environment setup | 30 min | 🟡 NEEDED |
| **Total** | **4-6 hours** | **TO DEPLOY** |

---

## Success Checklist

After completing above:

- [ ] Destination agent processes without errors
- [ ] Real data from all 5 services flows correctly
- [ ] Groq LLM selects best destination
- [ ] Pydantic model validates output
- [ ] Integration tests pass
- [ ] API endpoint returns valid response
- [ ] All logs are clean (no errors)
- [ ] Response time under 40 seconds

---

**Everything is ready. Just finish the Destination Agent! 🚀**

Questions? See ARCHITECTURE.md or IMPLEMENTATION_STATUS.md
