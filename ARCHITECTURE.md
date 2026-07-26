# TravelGenie v2 - Real-Time Multi-Agent Travel Planning System

## Overview

TravelGenie v2 is a production-quality, real-time multi-agent AI travel planning system built with:

- **Backend**: FastAPI (async), LangChain, LangGraph
- **LLM**: Groq API (fast, open-source model)
- **External Services**: Real-time APIs for geocoding, routing, weather, and POI data
- **Database**: SQLite (primary), MongoDB (caching - optional)
- **Frontend**: React with TypeScript and Tailwind CSS

### Key Features

✨ **Real-Time Intelligence**
- Fetches live travel data from multiple APIs
- Uses Groq LLM for intelligent reasoning
- Adaptive planning based on current conditions

🛠️ **Production Architecture**
- Async/await throughout
- Service layer pattern for all external APIs
- Structured agent communication via Pydantic models
- LangGraph workflow orchestration
- Comprehensive error handling and retry logic

📍 **Service Integrations**
- **Geo Service**: Nominatim (OpenStreetMap) for geocoding
- **Places Service**: Overpass API for hotels, attractions, restaurants
- **Routing Service**: OSRM for distance & travel time calculation
- **Weather Service**: OpenWeatherMap for forecasting
- **Cache Service**: MongoDB/SQLite for response caching

🤖 **Multi-Agent Pipeline**
1. **Trip Feasibility Agent**: Validates budget and calculates allocation
2. **Destination Agent**: Recommends best destination with real data
3. **Schedule Agent**: Generates day-by-day itinerary
4. **Validation Agent**: Verifies plan feasibility and repairs issues

## Architecture

### System Diagram

```
User Input
    ↓
FastAPI Router
    ↓
Workflow (LangGraph)
    ├─→ Trip Feasibility Agent
    │       ├─→ Budget Validation
    │       └─→ Distance Calculation
    ├─→ Destination Agent
    │       ├─→ GeoService (Nominatim)
    │       ├─→ PlacesService (Overpass)
    │       ├─→ RoutingService (OSRM)
    │       ├─→ WeatherService (OpenWeatherMap)
    │       └─→ Groq LLM
    ├─→ Schedule Agent
    │       ├─→ WeatherService
    │       ├─→ RoutingService
    │       └─→ Groq LLM
    ├─→ Validation Agent
    │       ├─→ Budget Verification
    │       ├─→ Schedule Feasibility
    │       ├─→ Weather Compatibility
    │       └─→ Groq LLM
    └─→ Finalization
            └─→ Database Storage
```

### File Structure

```
backend/
├── config.py                    # Centralized configuration
├── models.py                    # Pydantic models for agent I/O
├── workflow.py                  # LangGraph workflow orchestration
│
├── services/
│   ├── __init__.py
│   ├── base_service.py         # Base class for all services
│   ├── groq_service.py         # Groq LLM service
│   ├── geo_service.py          # Geocoding (Nominatim)
│   ├── places_service.py       # Places search (Overpass)
│   ├── routing_service.py      # Route optimization (OSRM)
│   ├── weather_service.py      # Weather data (OpenWeatherMap)
│   └── cache_service.py        # Response caching
│
├── agents/
│   ├── async_base_agent.py     # Base async agent class
│   ├── trip_feasibility_agent.py
│   ├── destination_agent.py    # [NEEDS COMPLETION]
│   ├── schedule_agent.py
│   └── validation_agent.py
│
├── api/
│   ├── main.py                 # FastAPI app setup
│   ├── async_routes.py         # NEW: Async routes using new agents
│   └── routes.py               # OLD: Legacy routes
│
└── database/
    ├── database.py             # SQLite setup
    └── models.py               # SQLAlchemy models
```

## Setup & Configuration

### 1. Environment Variables

Create `.env` file in the backend directory:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=mixtral-8x7b-32768
GROQ_TEMPERATURE=0.7

# External APIs
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
NOMINATIM_TIMEOUT=10

OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OVERPASS_TIMEOUT=30

OSRM_BASE_URL=https://router.project-osrm.org
OSRM_TIMEOUT=15

# Weather (choose one provider)
WEATHER_API_PROVIDER=openweathermap
OPENWEATHER_API_KEY=your_openweather_api_key_here
# OR
WEATHERAPI_API_KEY=your_weatherapi_api_key_here

# Database
DATABASE_URL=sqlite:///./travel_genie.db

# Optional: MongoDB for caching
MONGODB_URL=mongodb://localhost:27017/  # If not provided, SQLite cache is used

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# Caching
CACHE_TTL_MINUTES=30
CACHE_ENABLED=True

# Performance
MAX_RETRIES=3
DEFAULT_HTTP_TIMEOUT=30
PLANNER_TIMEOUT_SECONDS=120
```

### 2. Get API Keys

**Groq** (Free tier, fast inference):
1. Visit: https://console.groq.com
2. Sign up / Login
3. Create API key
4. Use `mixtral-8x7b-32768` model

**OpenWeatherMap** (Optional, free tier available):
1. Visit: https://openweathermap.org/api
2. Sign up for free
3. Get API key from account page

**Note**: Nominatim (Geo), Overpass (Places), OSRM (Routing) are free, open-source, and don't require API keys!

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the Server

```bash
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the async routes (new system):

```bash
python -m uvicorn api.main_async:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Generate Travel Plan

**POST** `/api/plan`

```json
{
  "budget": 3000,
  "source_city": "New York",
  "trip_days": 7,
  "travel_style": "couple",
  "transportation": "flight",
  "interests": ["beaches", "food", "culture"],
  "hotel_preference": "resort",
  "travel_month": "July",
  "special_requirements": "No nightlife preferred"
}
```

Response includes:
- Day-by-day itinerary with times and activities
- Hotel and restaurant recommendations
- Budget breakdown
- Weather information
- Validation status
- Confidence scores

### Health Check

**GET** `/api/health`

### Service Status

**GET** `/api/services/status`

### History

**GET** `/api/history?limit=10`

### Agent List

**GET** `/api/agents`

## Key Improvements Over v1

| Feature | v1 (Static) | v2 (Real-Time) |
|---------|-----------|-----------------|
| Data Source | Seeded database | Live APIs |
| Destination Data | Pre-defined | Geocoded + searched |
| Weather | Static | Current + forecast |
| Hotels | Hardcoded list | Overpass search |
| Travel Times | Estimated | OSRM calculated |
| LLM Integration | Minimal | Full reasoning pipeline |
| Async Support | Partial | Complete |
| Error Handling | Basic | Comprehensive with retries |
| Caching | None | 30-min TTL with MongoDB fallback |
| Agent Communication | Free text | Structured JSON (Pydantic) |

## Agent I/O Models

All agents use structured Pydantic models for communication:

### Trip Feasibility Output
```python
{
  "is_feasible": bool,
  "daily_budget": float,
  "budget_allocation": {
    "accommodation": float,
    "food": float,
    "transport": float,
    "activities": float
  },
  "max_affordable_distance": float,
  "warnings": List[str],
  "confidence_score": float,
  "reasoning": str
}
```

### Destination Output
```python
{
  "destination": {"latitude": float, "longitude": float, "city": str, "country": str},
  "reason": str,
  "best_season": str,
  "weather": {...},
  "hotel_options": [{...}],
  "selected_hotel": {...},
  "attractions": [{...}],
  "travel_distance": float,
  "travel_time_hours": float,
  "estimated_cost_per_day": float,
  "feasibility_with_budget": bool,
  "confidence_score": float
}
```

## Error Handling & Fallbacks

The system implements multi-level error handling:

1. **Service Level**: Retry with exponential backoff (3 attempts)
2. **Agent Level**: Try alternative approaches, use fallback data
3. **Workflow Level**: Revision logic, plan repair
4. **Cache Level**: MongoDB → SQLite → Seeded data

Example failure scenario:
```
Nominatim fails
  → Retry 2x with backoff
  → Check cache
  → Use cached seeded destinations
  → Log warning, continue with degraded mode
```

## Logging

All components log execution:

```
[2024-07-26 14:53:00] INFO [service.Geo] ✅ Geocoding 'Paris'
[2024-07-26 14:53:01] DEBUG [agent.Destination] Using GeoService for locations
[2024-07-26 14:53:05] INFO [agent.Destination] ✅ Destination completed in 5.23s
```

## Performance Considerations

- **Concurrent API calls**: Services make requests in parallel when possible
- **Connection pooling**: HTTP clients reuse connections
- **Caching**: 30-minute TTL for all API responses
- **Timeouts**: All requests have configurable timeouts
- **Async/await**: Non-blocking throughout

## Testing

(To be implemented)

```bash
pytest tests/
pytest tests/services/  # Test individual services
pytest tests/agents/    # Test agents with mocked services
```

## Next Steps / TODOs

1. ✅ Complete Destination Agent implementation
2. ✅ Set up LangGraph workflow
3. ⏳ Create comprehensive test suite
4. ⏳ Implement proper async FastAPI integration
5. ⏳ Add schedule agent improvements
6. ⏳ Optimize performance with caching
7. ⏳ Add monitoring and analytics
8. ⏳ Deploy to production

## Troubleshooting

### Groq API Key Error
```
ValueError: GROQ_API_KEY is required
```
→ Add GROQ_API_KEY to .env file

### Service Timeouts
→ Increase timeout values in config.py
→ Check internet connection to external APIs

### Plan Generation Slow
→ Check weather API response time
→ Consider using MongoDB for caching
→ Increase PLANNER_TIMEOUT_SECONDS

### No Destination Recommendations
→ Try different interests
→ Check if APIs are accessible
→ Review logs for service errors

## References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Groq API Docs](https://console.groq.com/docs)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)
- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [OSRM API](http://project-osrm.org/docs/v5.24.0/api/)
- [OpenWeatherMap API](https://openweathermap.org/api)

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
1. Check logs for detailed error messages
2. Review configuration in .env
3. Test individual services with health checks
4. Create issues on GitHub

---

**Happy traveling! 🌍✈️🏖️**
