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

        return await self._select_destination(user_input, feasibility)

    async def _select_destination(self, user_input: UserTravelInput, feasibility: TripFeasibilityOutput) -> DestinationOutput:
        """
        Select best destination using live geo, weather, and Overpass data.
        Falls back to curated data only when live APIs fail.
        """
        import asyncio
        candidates = self._get_candidates(user_input)
        geo = get_geo_service()
        weather_svc = get_weather_service()

        # Geocode source city once
        source_location = None
        try:
            source_location = await asyncio.wait_for(geo.geocode(user_input.source_city), timeout=6.0)
        except Exception:
            pass

        candidates_data = []
        for candidate in candidates[:3]:
            try:
                dest_location = await asyncio.wait_for(geo.geocode(candidate), timeout=6.0)
                if not dest_location:
                    continue

                # Run weather, hotels, attractions concurrently
                async def _get_weather():
                    try:
                        return await asyncio.wait_for(
                            weather_svc.get_current_weather(dest_location.latitude, dest_location.longitude),
                            timeout=6.0)
                    except Exception:
                        return weather_svc._get_fallback_weather()

                async def _get_hotels():
                    try:
                        return await asyncio.wait_for(
                            self._fetch_overpass_places(
                                dest_location.latitude, dest_location.longitude,
                                "node[tourism=hotel]", radius_m=5000, limit=5),
                            timeout=10.0)
                    except Exception:
                        return []

                async def _get_attractions():
                    try:
                        return await asyncio.wait_for(
                            self._fetch_overpass_places(
                                dest_location.latitude, dest_location.longitude,
                                "node[tourism=attraction];node[tourism=museum];node[leisure=park]",
                                radius_m=8000, limit=8),
                            timeout=10.0)
                    except Exception:
                        return []

                current_weather, hotels_raw, attractions_raw = await asyncio.gather(
                    _get_weather(), _get_hotels(), _get_attractions()
                )

                # Haversine distance
                distance_km = 0.0
                if source_location:
                    distance_km = await geo.calculate_distance(
                        source_location.latitude, source_location.longitude,
                        dest_location.latitude, dest_location.longitude,
                    )
                travel_hours = round(distance_km / 800.0, 1)

                candidates_data.append({
                    "name": candidate,
                    "location": dest_location,
                    "distance_km": round(distance_km, 1),
                    "travel_hours": travel_hours,
                    "hotels": hotels_raw,
                    "attractions": attractions_raw,
                    "weather": current_weather,
                    "daily_budget_estimate": feasibility.daily_budget,
                })
            except Exception as e:
                logger.warning(f"Skipping candidate {candidate}: {e}")
                continue

        if not candidates_data:
            logger.warning("No live data — using built-in fallback")
            return await self.fallback_response("", "", DestinationOutput)

        # Build DestinationOutput from best candidate (first = user's choice or top ranked)
        best = candidates_data[0]
        return self._build_destination_output(best, user_input, feasibility)

    async def _fetch_overpass_places(
        self,
        lat: float,
        lon: float,
        node_filters: str,
        radius_m: int = 5000,
        limit: int = 5,
    ) -> list:
        """Fetch places from Overpass API using around filter with retry and robust fallback."""
        import httpx
        import asyncio

        parts = [f"{f}(around:{radius_m},{lat},{lon});" for f in node_filters.split(";") if f.strip()]
        union = "".join(parts)
        query = f"[out:json][timeout:9];({union});out center {limit};"

        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://overpass-api.de/api/interpreter",
                        data={"data": query},
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "User-Agent": "TravelGenie/1.0 (travel planning app; contact@travelgenie.app)",
                        },
                        timeout=9.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                results = []
                for el in data.get("elements", []):
                    name = el.get("tags", {}).get("name") or el.get("tags", {}).get("name:en")
                    if not name:
                        continue
                    clat = el.get("lat") or el.get("center", {}).get("lat", lat)
                    clon = el.get("lon") or el.get("center", {}).get("lon", lon)
                    results.append({"name": name, "lat": clat, "lon": clon, "tags": el.get("tags", {})})
                return results[:limit]
            except Exception as e:
                logger.warning(f"[FALLBACK] Overpass fetch attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    await asyncio.sleep(0.5)
        return []

    def _build_destination_output(
        self,
        candidate: dict,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput,
    ) -> DestinationOutput:
        """Build a DestinationOutput from live candidate data."""
        dest_location = candidate["location"]
        weather = candidate["weather"]
        hotels_raw = candidate["hotels"]
        attractions_raw = candidate["attractions"]
        city = dest_location.city

        # Build hotel options from live data or curated fallback
        hotel_cfg_map = {
            "budget":  {"price": 45.0,  "rating": 3.8, "amenities": ["Free WiFi", "Air conditioning", "24h reception"]},
            "hostel":  {"price": 20.0,  "rating": 4.0, "amenities": ["Free WiFi", "Shared kitchen", "Locker"]},
            "luxury":  {"price": 250.0, "rating": 4.7, "amenities": ["Pool", "Spa", "Restaurant", "Concierge", "Free WiFi"]},
            "resort":  {"price": 150.0, "rating": 4.5, "amenities": ["Pool", "Beach access", "Restaurant", "Spa", "Free WiFi"]},
        }
        LIVE_HOTEL_FALLBACK = {
            "Paris":     {"budget": "Hôtel du Louvre", "hostel": "Generator Paris", "luxury": "Le Meurice", "resort": "Shangri-La Paris"},
            "Bali":      {"budget": "Kuta Paradiso Hotel", "hostel": "Puri Garden Hostel", "luxury": "Four Seasons Bali", "resort": "Alila Villas Uluwatu"},
            "Bangkok":   {"budget": "Lub d Bangkok", "hostel": "NapPark Hostel", "luxury": "Mandarin Oriental Bangkok", "resort": "Anantara Riverside"},
            "Tokyo":     {"budget": "Dormy Inn Asakusa", "hostel": "Khaosan Tokyo Kabuki", "luxury": "The Peninsula Tokyo", "resort": "Park Hyatt Tokyo"},
            "Barcelona": {"budget": "Hotel Praktik Rambla", "hostel": "Sant Jordi Hostels", "luxury": "Hotel Arts Barcelona", "resort": "W Barcelona"},
            "Kyoto":     {"budget": "Piece Hostel Kyoto", "hostel": "Kyoto Hana Hostel", "luxury": "The Ritz-Carlton Kyoto", "resort": "Aman Kyoto"},
            "Dubai":     {"budget": "Ibis Dubai Mall", "hostel": "Dubai Youth Hostel", "luxury": "Burj Al Arab", "resort": "Atlantis The Palm"},
            "Singapore": {"budget": "Hotel 81 Bugis", "hostel": "The Pod Boutique Capsule", "luxury": "Marina Bay Sands", "resort": "Capella Singapore"},
            "Mumbai":    {"budget": "Hotel Suba Palace", "hostel": "Backpacker Panda Colaba", "luxury": "The Taj Mahal Palace", "resort": "ITC Grand Central"},
            "Delhi":     {"budget": "Hotel Broadway", "hostel": "Zostel Delhi", "luxury": "The Imperial New Delhi", "resort": "ITC Maurya"},
            "Goa":       {"budget": "Hotel Baga Residency", "hostel": "Jungle Hostel Goa", "luxury": "Taj Exotica Goa", "resort": "W Goa"},
            "Jaipur":    {"budget": "Hotel Pearl Palace", "hostel": "Zostel Jaipur", "luxury": "Rambagh Palace", "resort": "Jai Mahal Palace"},
            "Rome":      {"budget": "Hotel Artemide", "hostel": "The Yellow Hostel", "luxury": "Hotel de Russie", "resort": "Rome Cavalieri"},
            "Lisbon":    {"budget": "Lisbon Destination Hostel", "hostel": "Home Lisbon Hostel", "luxury": "Bairro Alto Hotel", "resort": "Penha Longa Resort"},
            "Chennai":   {"budget": "Hotel Palmgrove", "hostel": "Zostel Chennai", "luxury": "ITC Grand Chola", "resort": "Taj Coromandel"},
            "Kolkata":   {"budget": "Hotel Hindusthan International", "hostel": "Zostel Kolkata", "luxury": "The Oberoi Grand", "resort": "ITC Royal Bengal"},
            "Hyderabad": {"budget": "Hotel Sitara Grand", "hostel": "Zostel Hyderabad", "luxury": "Taj Falaknuma Palace", "resort": "ITC Kohenur"},
            "Bengaluru": {"budget": "Hotel Empire International", "hostel": "Zostel Bangalore", "luxury": "The Leela Palace", "resort": "ITC Windsor"},
            "Mysuru":    {"budget": "Hotel Dasaprakash", "hostel": "Zostel Mysore", "luxury": "Radisson Blu Plaza Hotel Mysore", "resort": "The Windflower Resort & Spa"},
            "Kochi":     {"budget": "Hotel Abad Plaza", "hostel": "Zostel Kochi", "luxury": "Taj Malabar Resort & Spa", "resort": "Le Meridien Kochi"},
            "Agra":      {"budget": "Hotel Kamal", "hostel": "Zostel Agra", "luxury": "The Oberoi Amarvilas", "resort": "ITC Mughal"},
            "Varanasi":  {"budget": "Hotel Alka", "hostel": "Zostel Varanasi", "luxury": "Taj Ganges", "resort": "Brijrama Palace"},
            "Udaipur":   {"budget": "Hotel Badi Haveli", "hostel": "Zostel Udaipur", "luxury": "Taj Lake Palace", "resort": "The Leela Palace Udaipur"},
            "Rishikesh": {"budget": "Hotel Surya", "hostel": "Zostel Rishikesh", "luxury": "Aloha on the Ganges", "resort": "Ananda in the Himalayas"},
            "Coimbatore": {"budget": "Treebo Vinayak", "hostel": "Zostel Coimbatore", "luxury": "Vivanta Coimbatore", "resort": "Fairfield by Marriott Coimbatore"},
            "Manali":     {"budget": "Manali Heights", "hostel": "Zostel Manali", "luxury": "The Span Resort & Spa", "resort": "Solang Valley Resort"},
        }
        pref_key = str(user_input.hotel_preference).split(".")[-1].lower()
        hotel_cfg = hotel_cfg_map.get(pref_key, hotel_cfg_map["budget"])
        # Cap hotel price to the allocated hotel budget (45% of total / trip_days)
        trip_days = max(user_input.trip_days, 1)
        allocated_hotel_per_night = (feasibility.budget_allocation.get("accommodation", 45.0) / 100.0) * (feasibility.daily_budget * trip_days) / trip_days
        # Never assign a hotel that costs more than the allocated nightly budget
        price = min(hotel_cfg["price"], allocated_hotel_per_night)
        # But also never go below a sensible floor for the category
        FLOOR = {"hostel": 5.0, "budget": 10.0, "resort": 20.0, "luxury": 30.0}
        price = max(price, FLOOR.get(pref_key, 10.0))

        hotel_options = []
        city_hotels = LIVE_HOTEL_FALLBACK.get(city, {})
        if hotels_raw:
            for h in hotels_raw[:3]:
                hloc = Location(latitude=h["lat"], longitude=h["lon"], city=city, country=dest_location.country)
                raw_name = (h.get("name") or "").strip()
                if not raw_name or raw_name.lower() == city.lower() or raw_name.lower() in ("hotel", "resort", "lodging"):
                    raw_name = city_hotels.get(pref_key) or city_hotels.get("budget") or f"Central {pref_key.title()} Hotel"
                hotel_options.append(HotelOption(
                    name=raw_name,
                    category=user_input.hotel_preference,
                    price_per_night=round(price, 2),
                    rating=hotel_cfg["rating"],
                    amenities=hotel_cfg["amenities"],
                    location=hloc,
                    reviews_count=180,
                    check_in_checkout="14:00 / 11:00",
                    description=f"{raw_name} — located in {city}.",
                ))
        if not hotel_options:
            fallback_name = city_hotels.get(pref_key) or city_hotels.get("budget") or f"Central {pref_key.title()} Hotel"
            if fallback_name.lower() == city.lower():
                fallback_name = f"Central {pref_key.title()} Hotel"
            hotel_options.append(HotelOption(
                name=fallback_name,
                category=user_input.hotel_preference,
                price_per_night=round(price, 2),
                rating=hotel_cfg["rating"],
                amenities=hotel_cfg["amenities"],
                location=dest_location,
                reviews_count=240,
                check_in_checkout="14:00 / 11:00",
                description=f"Well-located {pref_key} accommodation in {city}.",
            ))

        # Build attractions from live data or curated fallback
        CURATED_ATTRACTIONS = {
            "Paris":      [("Eiffel Tower", "landmark", 2.0, 25.0), ("Louvre Museum", "museum", 3.0, 17.0), ("Notre-Dame Cathedral", "historical", 1.5, 0.0)],
            "Bali":       [("Tanah Lot Temple", "temple", 2.0, 5.0), ("Ubud Monkey Forest", "nature", 1.5, 5.0), ("Seminyak Beach", "beach", 3.0, 0.0)],
            "Bangkok":    [("Grand Palace", "historical", 2.5, 15.0), ("Wat Pho", "temple", 1.5, 5.0), ("Chatuchak Market", "shopping", 2.0, 0.0)],
            "Tokyo":      [("Senso-ji Temple", "temple", 1.5, 0.0), ("Shibuya Crossing", "landmark", 1.0, 0.0), ("teamLab Borderless", "museum", 3.0, 32.0)],
            "Barcelona":  [("Sagrada Familia", "landmark", 2.0, 26.0), ("Park Güell", "park", 2.0, 10.0), ("La Boqueria Market", "food", 1.5, 0.0)],
            "Kyoto":      [("Fushimi Inari Shrine", "temple", 2.0, 0.0), ("Arashiyama Bamboo Grove", "nature", 1.5, 0.0), ("Kinkaku-ji", "temple", 1.5, 5.0)],
            "Dubai":      [("Burj Khalifa", "landmark", 2.0, 35.0), ("Dubai Mall", "shopping", 3.0, 0.0), ("Desert Safari", "adventure", 4.0, 60.0)],
            "Singapore":  [("Gardens by the Bay", "park", 3.0, 28.0), ("Marina Bay Sands", "landmark", 2.0, 0.0), ("Sentosa Island", "beach", 4.0, 15.0)],
            "Mumbai":     [("Gateway of India", "landmark", 1.5, 0.0), ("Elephanta Caves", "historical", 3.0, 15.0), ("Marine Drive", "landmark", 1.0, 0.0), ("Chhatrapati Shivaji Terminus", "historical", 1.0, 0.0), ("Juhu Beach", "beach", 2.0, 0.0)],
            "Delhi":      [("Red Fort", "historical", 2.0, 10.0), ("Qutub Minar", "historical", 1.5, 10.0), ("India Gate", "landmark", 1.0, 0.0), ("Humayun's Tomb", "historical", 1.5, 10.0)],
            "Goa":        [("Baga Beach", "beach", 3.0, 0.0), ("Basilica of Bom Jesus", "historical", 1.5, 0.0), ("Dudhsagar Falls", "nature", 4.0, 5.0)],
            "Jaipur":     [("Amber Fort", "historical", 2.5, 10.0), ("Hawa Mahal", "landmark", 1.0, 5.0), ("City Palace", "historical", 2.0, 10.0)],
            "Rome":       [("Colosseum", "historical", 2.5, 18.0), ("Vatican Museums", "museum", 3.0, 20.0), ("Trevi Fountain", "landmark", 1.0, 0.0)],
            "Lisbon":     [("Belém Tower", "historical", 1.5, 6.0), ("Jerónimos Monastery", "historical", 2.0, 10.0), ("Alfama District", "culture", 2.0, 0.0)],
        }
        raw_attractions = attractions_raw
        curated = CURATED_ATTRACTIONS.get(city, [])
        attractions = []
        seen_names = set()

        # First add live Overpass results
        for i, a in enumerate(raw_attractions[:5]):
            if a["name"] in seen_names:
                continue
            seen_names.add(a["name"])
            aloc = Location(latitude=a["lat"], longitude=a["lon"], city=city, country=dest_location.country)
            tag = a["tags"].get("tourism") or a["tags"].get("leisure") or "attraction"
            attractions.append(Attraction(
                name=a["name"], category=tag, location=aloc,
                rating=4.1, distance_from_city_center=round(1.0 + i * 0.7, 1),
                visit_duration_hours=2.0, entry_fee=0.0,
                opening_hours="09:00-18:00",
                description=f"{a['name']} — a popular {tag} in {city}.",
            ))

        # Fill remaining slots from curated data
        for i, (name, cat, dur, fee) in enumerate(curated):
            if len(attractions) >= 5:
                break
            if name in seen_names:
                continue
            seen_names.add(name)
            attractions.append(Attraction(
                name=name, category=cat, location=dest_location,
                rating=4.3, distance_from_city_center=round(1.0 + i * 0.8, 1),
                visit_duration_hours=dur, entry_fee=fee,
                opening_hours="09:00-18:00",
                description=f"Popular {cat} attraction in {city}.",
            ))

        # Final fallback if still empty — use generic non-city-specific names
        if not attractions:
            for i, (name, cat, dur, fee) in enumerate([
                ("Old Town Walking Tour", "sightseeing", 2.0, 10.0),
                ("Central Market", "food", 1.5, 0.0),
                ("City History Museum", "museum", 2.0, 8.0),
            ]):
                attractions.append(Attraction(
                    name=name, category=cat, location=dest_location,
                    rating=4.0, distance_from_city_center=round(1.0 + i * 0.8, 1),
                    visit_duration_hours=dur, entry_fee=fee,
                    opening_hours="09:00-18:00",
                    description=f"Popular {cat} in {city}.",
                ))

        distance_km = candidate["distance_km"]
        travel_hours = candidate["travel_hours"]

        return DestinationOutput(
            destination=dest_location,
            reason=(
                f"{city} is an excellent match for a {user_input.travel_type} trip "
                f"with interests in {', '.join(user_input.interests)}. "
                f"Current weather: {weather.condition}, {weather.current_temp:.0f}°C."
            ),
            best_season=Season.SUMMER,
            weather=weather,
            hotel_options=hotel_options,
            selected_hotel=hotel_options[0],
            attractions=attractions,
            travel_distance=round(distance_km, 1),
            travel_time_hours=travel_hours,
            estimated_cost_per_day=feasibility.daily_budget,
            feasibility_with_budget=feasibility.is_feasible,
            confidence_score=0.88,
        )

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
        """Rich built-in fallback using curated destination data."""
        user_input = getattr(self, 'last_user_input', None)
        feasibility = getattr(self, 'last_feasibility', None)
        if not isinstance(user_input, UserTravelInput) or not isinstance(feasibility, TripFeasibilityOutput):
            raise AgentException(self.name, "Fallback unavailable without valid input")

        # Curated destination data keyed by city name
        CURATED = {
            "Paris":         {"lat": 48.8566, "lon": 2.3522,   "country": "France",       "region": "Île-de-France"},
            "Venice":        {"lat": 45.4408, "lon": 12.3155,  "country": "Italy",        "region": "Veneto"},
            "Bali":          {"lat": -8.3405, "lon": 115.0920, "country": "Indonesia",    "region": "Bali"},
            "Santorini":     {"lat": 36.3932, "lon": 25.4615,  "country": "Greece",       "region": "South Aegean"},
            "Kyoto":         {"lat": 35.0116, "lon": 135.7681, "country": "Japan",        "region": "Kansai"},
            "Bangkok":       {"lat": 13.7563, "lon": 100.5018, "country": "Thailand",     "region": "Bangkok"},
            "Barcelona":     {"lat": 41.3851, "lon": 2.1734,   "country": "Spain",        "region": "Catalonia"},
            "Lisbon":        {"lat": 38.7223, "lon": -9.1393,  "country": "Portugal",     "region": "Lisbon"},
            "Prague":        {"lat": 50.0755, "lon": 14.4378,  "country": "Czech Republic","region": "Bohemia"},
            "Budapest":      {"lat": 47.4979, "lon": 19.0402,  "country": "Hungary",      "region": "Central Hungary"},
            "Seoul":         {"lat": 37.5665, "lon": 126.9780, "country": "South Korea",  "region": "Seoul"},
            "Singapore":     {"lat": 1.3521,  "lon": 103.8198, "country": "Singapore",    "region": "Singapore"},
            "Dubai":         {"lat": 25.2048, "lon": 55.2708,  "country": "UAE",          "region": "Dubai"},
            "Tokyo":         {"lat": 35.6762, "lon": 139.6503, "country": "Japan",        "region": "Kanto"},
            "Orlando":       {"lat": 28.5383, "lon": -81.3792, "country": "USA",          "region": "Florida"},
            "Berlin":        {"lat": 52.5200, "lon": 13.4050,  "country": "Germany",      "region": "Berlin"},
            "Rome":          {"lat": 41.9028, "lon": 12.4964,  "country": "Italy",        "region": "Lazio"},
            "Chiang Mai":    {"lat": 18.7883, "lon": 98.9853,  "country": "Thailand",     "region": "Chiang Mai"},
            "Ho Chi Minh City": {"lat": 10.8231, "lon": 106.6297, "country": "Vietnam",  "region": "Ho Chi Minh"},
            "Mumbai":        {"lat": 19.0760, "lon": 72.8777,  "country": "India",        "region": "Maharashtra"},
            "Delhi":         {"lat": 28.6139, "lon": 77.2090,  "country": "India",        "region": "Delhi"},
            "Goa":           {"lat": 15.2993, "lon": 74.1240,  "country": "India",        "region": "Goa"},
            "Jaipur":        {"lat": 26.9124, "lon": 75.7873,  "country": "India",        "region": "Rajasthan"},
            "Chennai":       {"lat": 13.0827, "lon": 80.2707,  "country": "India",        "region": "Tamil Nadu"},
            "Kolkata":       {"lat": 22.5726, "lon": 88.3639,  "country": "India",        "region": "West Bengal"},
            "Hyderabad":     {"lat": 17.3850, "lon": 78.4867,  "country": "India",        "region": "Telangana"},
            "Bengaluru":     {"lat": 12.9716, "lon": 77.5946,  "country": "India",        "region": "Karnataka"},
            "Mysuru":        {"lat": 12.2958, "lon": 76.6394,  "country": "India",        "region": "Karnataka"},
            "Kochi":         {"lat": 9.9312,  "lon": 76.2673,  "country": "India",        "region": "Kerala"},
            "Agra":          {"lat": 27.1767, "lon": 78.0081,  "country": "India",        "region": "Uttar Pradesh"},
            "Varanasi":      {"lat": 25.3176, "lon": 82.9739,  "country": "India",        "region": "Uttar Pradesh"},
            "Udaipur":       {"lat": 24.5854, "lon": 73.7125,  "country": "India",        "region": "Rajasthan"},
            "Rishikesh":     {"lat": 30.0869, "lon": 78.2676,  "country": "India",        "region": "Uttarakhand"},
        }

        ATTRACTIONS = {
            "Paris":      [("Eiffel Tower", "landmark", 2.0, 25.0), ("Louvre Museum", "museum", 3.0, 17.0), ("Notre-Dame Cathedral", "historical", 1.5, 0.0)],
            "Bali":       [("Tanah Lot Temple", "temple", 2.0, 5.0), ("Ubud Monkey Forest", "nature", 1.5, 5.0), ("Seminyak Beach", "beach", 3.0, 0.0)],
            "Bangkok":    [("Grand Palace", "historical", 2.5, 15.0), ("Wat Pho", "temple", 1.5, 5.0), ("Chatuchak Market", "shopping", 2.0, 0.0)],
            "Tokyo":      [("Senso-ji Temple", "temple", 1.5, 0.0), ("Shibuya Crossing", "landmark", 1.0, 0.0), ("teamLab Borderless", "museum", 3.0, 32.0)],
            "Barcelona":  [("Sagrada Familia", "landmark", 2.0, 26.0), ("Park Güell", "park", 2.0, 10.0), ("La Boqueria Market", "food", 1.5, 0.0)],
            "Kyoto":      [("Fushimi Inari Shrine", "temple", 2.0, 0.0), ("Arashiyama Bamboo Grove", "nature", 1.5, 0.0), ("Kinkaku-ji", "temple", 1.5, 5.0)],
            "Dubai":      [("Burj Khalifa", "landmark", 2.0, 35.0), ("Dubai Mall", "shopping", 3.0, 0.0), ("Desert Safari", "adventure", 4.0, 60.0)],
            "Singapore":  [("Gardens by the Bay", "park", 3.0, 28.0), ("Marina Bay Sands", "landmark", 2.0, 0.0), ("Sentosa Island", "beach", 4.0, 15.0)],
            "Mumbai":     [("Gateway of India", "landmark", 1.5, 0.0), ("Elephanta Caves", "historical", 3.0, 15.0), ("Marine Drive", "landmark", 1.0, 0.0), ("Chhatrapati Shivaji Terminus", "historical", 1.0, 0.0), ("Juhu Beach", "beach", 2.0, 0.0)],
            "Delhi":      [("Red Fort", "historical", 2.0, 10.0), ("Qutub Minar", "historical", 1.5, 10.0), ("India Gate", "landmark", 1.0, 0.0), ("Humayun's Tomb", "historical", 1.5, 10.0)],
            "Goa":        [("Baga Beach", "beach", 3.0, 0.0), ("Basilica of Bom Jesus", "historical", 1.5, 0.0), ("Dudhsagar Falls", "nature", 4.0, 5.0)],
            "Jaipur":     [("Amber Fort", "historical", 2.5, 10.0), ("Hawa Mahal", "landmark", 1.0, 5.0), ("City Palace", "historical", 2.0, 10.0)],
            "Rome":       [("Colosseum", "historical", 2.5, 18.0), ("Vatican Museums", "museum", 3.0, 20.0), ("Trevi Fountain", "landmark", 1.0, 0.0)],
            "Lisbon":     [("Belém Tower", "historical", 1.5, 6.0), ("Jerónimos Monastery", "historical", 2.0, 10.0), ("Alfama District", "culture", 2.0, 0.0)],
            "Chennai":    [("Marina Beach", "beach", 2.0, 0.0), ("Kapaleeshwarar Temple", "temple", 1.5, 0.0), ("Fort St. George", "historical", 1.5, 5.0), ("Government Museum", "museum", 2.0, 5.0), ("Santhome Basilica", "historical", 1.0, 0.0)],
            "Kolkata":    [("Victoria Memorial", "historical", 2.0, 5.0), ("Howrah Bridge", "landmark", 1.0, 0.0), ("Dakshineswar Kali Temple", "temple", 1.5, 0.0), ("Indian Museum", "museum", 2.0, 5.0), ("Park Street", "culture", 1.5, 0.0)],
            "Hyderabad":  [("Charminar", "historical", 1.5, 5.0), ("Golconda Fort", "historical", 2.5, 10.0), ("Hussain Sagar Lake", "nature", 1.5, 0.0), ("Salar Jung Museum", "museum", 2.5, 10.0), ("Ramoji Film City", "entertainment", 4.0, 30.0)],
            "Bengaluru":  [("Lalbagh Botanical Garden", "nature", 2.0, 5.0), ("Bangalore Palace", "historical", 1.5, 10.0), ("Cubbon Park", "park", 1.5, 0.0), ("ISKCON Temple", "temple", 1.0, 0.0), ("Vidhana Soudha", "landmark", 1.0, 0.0)],
            "Mysuru":     [("Mysore Palace", "historical", 2.5, 10.0), ("Chamundi Hills", "temple", 2.0, 0.0), ("Brindavan Gardens", "nature", 2.0, 5.0), ("Mysore Zoo", "nature", 2.5, 10.0), ("St. Philomena's Church", "historical", 1.0, 0.0)],
            "Kochi":      [("Fort Kochi Beach", "beach", 2.0, 0.0), ("Chinese Fishing Nets", "landmark", 1.0, 0.0), ("Mattancherry Palace", "historical", 1.5, 5.0), ("Jewish Synagogue", "historical", 1.0, 5.0), ("Kerala Folklore Museum", "museum", 2.0, 10.0)],
            "Agra":       [("Taj Mahal", "historical", 3.0, 15.0), ("Agra Fort", "historical", 2.0, 10.0), ("Fatehpur Sikri", "historical", 2.5, 10.0), ("Mehtab Bagh", "nature", 1.5, 5.0)],
            "Varanasi":   [("Dashashwamedh Ghat", "temple", 2.0, 0.0), ("Kashi Vishwanath Temple", "temple", 1.5, 0.0), ("Sarnath", "historical", 2.0, 5.0), ("Assi Ghat", "culture", 1.5, 0.0)],
            "Udaipur":    [("City Palace", "historical", 2.5, 10.0), ("Lake Pichola", "nature", 2.0, 0.0), ("Jagdish Temple", "temple", 1.0, 0.0), ("Saheliyon Ki Bari", "nature", 1.5, 5.0)],
            "Rishikesh":  [("Laxman Jhula", "landmark", 1.5, 0.0), ("Triveni Ghat", "temple", 1.0, 0.0), ("Neelkanth Mahadev Temple", "temple", 2.0, 0.0), ("Rajaji National Park", "nature", 3.0, 10.0)],
        }

        HOTELS = {
            "budget":  {"price": 45.0,  "rating": 3.8, "amenities": ["Free WiFi", "Air conditioning", "24h reception"]},
            "hostel":  {"price": 20.0,  "rating": 4.0, "amenities": ["Free WiFi", "Shared kitchen", "Locker", "Common room"]},
            "luxury":  {"price": 250.0, "rating": 4.7, "amenities": ["Pool", "Spa", "Restaurant", "Concierge", "Free WiFi"]},
            "resort":  {"price": 150.0, "rating": 4.5, "amenities": ["Pool", "Beach access", "Restaurant", "Spa", "Free WiFi"]},
        }

        # Curated real hotel names per city — never concatenate city + suffix
        CURATED_HOTELS = {
            "Paris":     {"budget": "Hôtel du Louvre", "hostel": "Generator Paris", "luxury": "Le Meurice", "resort": "Shangri-La Paris"},
            "Bali":      {"budget": "Kuta Paradiso Hotel", "hostel": "Puri Garden Hostel", "luxury": "Four Seasons Bali", "resort": "Alila Villas Uluwatu"},
            "Bangkok":   {"budget": "Lub d Bangkok", "hostel": "NapPark Hostel", "luxury": "Mandarin Oriental Bangkok", "resort": "Anantara Riverside"},
            "Tokyo":     {"budget": "Dormy Inn Asakusa", "hostel": "Khaosan Tokyo Kabuki", "luxury": "The Peninsula Tokyo", "resort": "Park Hyatt Tokyo"},
            "Barcelona": {"budget": "Hotel Praktik Rambla", "hostel": "Sant Jordi Hostels", "luxury": "Hotel Arts Barcelona", "resort": "W Barcelona"},
            "Kyoto":     {"budget": "Piece Hostel Kyoto", "hostel": "Kyoto Hana Hostel", "luxury": "The Ritz-Carlton Kyoto", "resort": "Aman Kyoto"},
            "Dubai":     {"budget": "Ibis Dubai Mall", "hostel": "Dubai Youth Hostel", "luxury": "Burj Al Arab", "resort": "Atlantis The Palm"},
            "Singapore": {"budget": "Hotel 81 Bugis", "hostel": "The Pod Boutique Capsule", "luxury": "Marina Bay Sands", "resort": "Capella Singapore"},
            "Mumbai":    {"budget": "Hotel Suba Palace", "hostel": "Backpacker Panda Colaba", "luxury": "The Taj Mahal Palace", "resort": "ITC Grand Central"},
            "Delhi":     {"budget": "Hotel Broadway", "hostel": "Zostel Delhi", "luxury": "The Imperial New Delhi", "resort": "ITC Maurya"},
            "Goa":       {"budget": "Hotel Baga Residency", "hostel": "Jungle Hostel Goa", "luxury": "Taj Exotica Goa", "resort": "W Goa"},
            "Jaipur":    {"budget": "Hotel Pearl Palace", "hostel": "Zostel Jaipur", "luxury": "Rambagh Palace", "resort": "Jai Mahal Palace"},
            "Rome":      {"budget": "Hotel Artemide", "hostel": "The Yellow Hostel", "luxury": "Hotel de Russie", "resort": "Rome Cavalieri"},
            "Lisbon":    {"budget": "Lisbon Destination Hostel", "hostel": "Home Lisbon Hostel", "luxury": "Bairro Alto Hotel", "resort": "Penha Longa Resort"},
            "Chennai":   {"budget": "Hotel Palmgrove", "hostel": "Zostel Chennai", "luxury": "ITC Grand Chola", "resort": "Taj Coromandel"},
            "Kolkata":   {"budget": "Hotel Hindusthan International", "hostel": "Zostel Kolkata", "luxury": "The Oberoi Grand", "resort": "ITC Royal Bengal"},
            "Hyderabad": {"budget": "Hotel Sitara Grand", "hostel": "Zostel Hyderabad", "luxury": "Taj Falaknuma Palace", "resort": "ITC Kohenur"},
            "Bengaluru": {"budget": "Hotel Empire International", "hostel": "Zostel Bangalore", "luxury": "The Leela Palace", "resort": "ITC Windsor"},
            "Mysuru":    {"budget": "Hotel Dasaprakash", "hostel": "Zostel Mysore", "luxury": "Radisson Blu Plaza Hotel Mysore", "resort": "The Windflower Resort & Spa"},
            "Kochi":     {"budget": "Hotel Abad Plaza", "hostel": "Zostel Kochi", "luxury": "Taj Malabar Resort & Spa", "resort": "Le Meridien Kochi"},
            "Agra":      {"budget": "Hotel Kamal", "hostel": "Zostel Agra", "luxury": "The Oberoi Amarvilas", "resort": "ITC Mughal"},
            "Varanasi":  {"budget": "Hotel Alka", "hostel": "Zostel Varanasi", "luxury": "Taj Ganges", "resort": "Brijrama Palace"},
            "Udaipur":   {"budget": "Hotel Badi Haveli", "hostel": "Zostel Udaipur", "luxury": "Taj Lake Palace", "resort": "The Leela Palace Udaipur"},
            "Rishikesh": {"budget": "Hotel Surya", "hostel": "Zostel Rishikesh", "luxury": "Aloha on the Ganges", "resort": "Ananda in the Himalayas"},
            "Coimbatore": {"budget": "Treebo Vinayak", "hostel": "Zostel Coimbatore", "luxury": "Vivanta Coimbatore", "resort": "Fairfield by Marriott Coimbatore"},
            "Manali":     {"budget": "Manali Heights", "hostel": "Zostel Manali", "luxury": "The Span Resort & Spa", "resort": "Solang Valley Resort"},
            "Venice":    {"budget": "Hotel Dalla Mora", "hostel": "Generator Venice", "luxury": "Gritti Palace", "resort": "Belmond Hotel Cipriani"},
            "Prague":    {"budget": "Hotel Merkur", "hostel": "Czech Inn", "luxury": "Four Seasons Prague", "resort": "Mandarin Oriental Prague"},
            "Budapest":  {"budget": "Hotel Moments Budapest", "hostel": "Maverick City Lodge", "luxury": "Four Seasons Gresham Palace", "resort": "Corinthia Hotel Budapest"},
            "Seoul":     {"budget": "Ibis Ambassador Seoul", "hostel": "Kimchee Guesthouse", "luxury": "The Shilla Seoul", "resort": "Park Hyatt Seoul"},
            "Berlin":    {"budget": "Hotel Adlon Kempinski", "hostel": "Generator Berlin", "luxury": "Das Stue", "resort": "Schlosshotel Berlin"},
        }

        candidates = self._get_candidates(user_input)
        selected_name = candidates[0] if candidates else "Paris"
        geo_data = CURATED.get(selected_name, {
            "lat": 19.0760, "lon": 72.8777, "country": "India", "region": selected_name
        })

        dest_location = Location(
            latitude=geo_data["lat"], longitude=geo_data["lon"],
            city=selected_name, country=geo_data["country"], region=geo_data.get("region"),
        )

        hotel_cfg = HOTELS.get(str(user_input.hotel_preference).split(".")[-1].lower(), HOTELS["budget"])
        pref_key = str(user_input.hotel_preference).split(".")[-1].lower()
        city_hotels = CURATED_HOTELS.get(selected_name, {})
        hotel_name = city_hotels.get(pref_key) or city_hotels.get("budget") or f"Central {pref_key.title()} Hotel"
        if hotel_name.lower() == selected_name.lower():
            hotel_name = f"Central {pref_key.title()} Hotel"
        # Cap hotel price to allocated hotel budget
        trip_days = max(user_input.trip_days, 1)
        allocated_hotel_per_night = (feasibility.budget_allocation.get("accommodation", 45.0) / 100.0) * (feasibility.daily_budget * trip_days) / trip_days
        FLOOR = {"hostel": 5.0, "budget": 10.0, "resort": 20.0, "luxury": 30.0}
        price = max(min(hotel_cfg["price"], allocated_hotel_per_night), FLOOR.get(pref_key, 10.0))
        hotel = HotelOption(
            name=hotel_name,
            category=user_input.hotel_preference,
            price_per_night=round(price, 2),
            rating=hotel_cfg["rating"],
            amenities=hotel_cfg["amenities"],
            location=dest_location,
            reviews_count=240,
            check_in_checkout="14:00 / 11:00",
            description=f"Well-located {pref_key} accommodation in {selected_name}.",
        )

        raw_attractions = ATTRACTIONS.get(selected_name, [
            ("Old Town Walking Tour", "sightseeing", 2.0, 10.0),
            ("Central Market", "food", 1.5, 0.0),
            ("City History Museum", "museum", 2.0, 8.0),
        ])
        attractions = [
            Attraction(
                name=name, category=cat,
                location=dest_location,
                rating=4.2, distance_from_city_center=round(1.0 + i * 0.8, 1),
                visit_duration_hours=dur, entry_fee=fee,
                opening_hours="09:00-18:00",
                description=f"Popular {cat} attraction in {selected_name}.",
            )
            for i, (name, cat, dur, fee) in enumerate(raw_attractions)
        ]

        weather_svc = get_weather_service()
        weather = weather_svc._get_fallback_weather()

        distance_km = min(feasibility.max_affordable_distance, 8000.0)
        travel_hours = round(distance_km / 800.0, 1)

        return DestinationOutput(
            destination=dest_location,
            reason=(
                f"{selected_name} is an excellent match for a {user_input.travel_type} trip "
                f"with interests in {', '.join(user_input.interests)}. "
                f"It offers great value at ${feasibility.daily_budget:.0f}/day."
            ),
            best_season=Season.SUMMER,
            weather=weather,
            hotel_options=[hotel],
            selected_hotel=hotel,
            attractions=attractions,
            travel_distance=distance_km,
            travel_time_hours=travel_hours,
            estimated_cost_per_day=feasibility.daily_budget,
            feasibility_with_budget=feasibility.is_feasible,
            confidence_score=0.82,
        )
 
    def _get_candidates(self, user_input: UserTravelInput) -> List[str]:
        """Get destination candidates based on interests and travel type."""

        # If user explicitly specified a destination, use it first
        if user_input.destination_city and user_input.destination_city.strip():
            return [user_input.destination_city.strip()]

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

