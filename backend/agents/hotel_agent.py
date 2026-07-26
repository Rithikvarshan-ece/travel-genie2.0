"""
TravelGenie Hotel Agent
Suggests hotels based on:
- Budget
- Ratings
- Distance from attractions
- Amenities
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent


class HotelAgent(BaseAgent):
    """
    The Hotel Agent recommends the best accommodation options
    based on user budget, preferences, and destination.
    """

    # Extended hotel database
    HOTEL_DATABASE = [
        # Bali
        {"name": "Bali Beach Resort", "destination": "Bali", "category": "resort",
         "price_per_night": 150, "rating": 4.5, "reviews": 1250,
         "amenities": ["pool", "spa", "restaurant", "beach access", "free wifi", "bar"],
         "latitude": -8.3405, "longitude": 115.0920, "distance_from_center": 2.0,
         "description": "Luxurious beachfront resort with stunning ocean views and world-class amenities"},
        {"name": "Bali Budget Inn", "destination": "Bali", "category": "budget",
         "price_per_night": 35, "rating": 3.8, "reviews": 890,
         "amenities": ["free wifi", "breakfast", "air conditioning", "laundry"],
         "latitude": -8.3500, "longitude": 115.1000, "distance_from_center": 3.5,
         "description": "Affordable and clean accommodation close to all major attractions"},
        {"name": "Bali Luxury Villa", "destination": "Bali", "category": "luxury",
         "price_per_night": 350, "rating": 4.9, "reviews": 560,
         "amenities": ["private pool", "butler service", "spa", "ocean view", "restaurant", "gym"],
         "latitude": -8.3300, "longitude": 115.0800, "distance_from_center": 1.5,
         "description": "Exclusive private villa with personalized butler service and breathtaking views"},
        {"name": "Bali Hostel", "destination": "Bali", "category": "hostel",
         "price_per_night": 15, "rating": 4.0, "reviews": 2100,
         "amenities": ["free wifi", "shared kitchen", "locker", "common room", "social events"],
         "latitude": -8.3600, "longitude": 115.1100, "distance_from_center": 4.0,
         "description": "Social backpacker hostel with great atmosphere and regular events"},
        
        # Tokyo
        {"name": "Tokyo Luxury Tower", "destination": "Tokyo", "category": "luxury",
         "price_per_night": 400, "rating": 4.8, "reviews": 1800,
         "amenities": ["sky bar", "spa", "multiple restaurants", "concierge", "free wifi", "gym"],
         "latitude": 35.6762, "longitude": 139.6503, "distance_from_center": 1.0,
         "description": "Premier luxury hotel in the heart of Tokyo with panoramic city views"},
        {"name": "Tokyo Capsule Inn", "destination": "Tokyo", "category": "budget",
         "price_per_night": 30, "rating": 3.5, "reviews": 3200,
         "amenities": ["free wifi", "locker", "shared bathroom", "lounge"],
         "latitude": 35.6800, "longitude": 139.6600, "distance_from_center": 2.0,
         "description": "Unique capsule hotel experience - clean, efficient, and ultra-modern"},
        {"name": "Tokyo Traditional Ryokan", "destination": "Tokyo", "category": "resort",
         "price_per_night": 250, "rating": 4.6, "reviews": 920,
         "amenities": ["hot spring", "traditional meals", "garden", "free wifi", "yukata robes"],
         "latitude": 35.6700, "longitude": 139.6400, "distance_from_center": 3.0,
         "description": "Authentic Japanese ryokan with onsen hot springs and kaiseki dining"},
        
        # Paris
        {"name": "Paris Luxury Palace", "destination": "Paris", "category": "luxury",
         "price_per_night": 500, "rating": 4.9, "reviews": 1450,
         "amenities": ["spa", "michelin restaurant", "eiffel tower view", "concierge", "pool", "butler"],
         "latitude": 48.8566, "longitude": 2.3522, "distance_from_center": 0.5,
         "description": "Iconic palace hotel with Eiffel Tower views and Michelin-starred dining"},
        {"name": "Paris Boutique Hotel", "destination": "Paris", "category": "budget",
         "price_per_night": 80, "rating": 4.0, "reviews": 1670,
         "amenities": ["free wifi", "breakfast", "air conditioning", "city view", "bicycle rental"],
         "latitude": 48.8600, "longitude": 2.3600, "distance_from_center": 1.5,
         "description": "Charming boutique hotel in the Latin Quarter with authentic Parisian ambiance"},
        {"name": "Paris Hostel", "destination": "Paris", "category": "hostel",
         "price_per_night": 40, "rating": 3.8, "reviews": 2800,
         "amenities": ["free wifi", "shared kitchen", "locker", "common room", "breakfast", "bar"],
         "latitude": 48.8700, "longitude": 2.3700, "distance_from_center": 2.5,
         "description": "Vibrant social hostel near major attractions with great community vibe"},
        
        # Dubai
        {"name": "Burj Al Arab", "destination": "Dubai", "category": "luxury",
         "price_per_night": 800, "rating": 5.0, "reviews": 2300,
         "amenities": ["private beach", "helicopter pad", "underwater restaurant", "spa", "butler", "pool"],
         "latitude": 25.1412, "longitude": 55.1852, "distance_from_center": 5.0,
         "description": "World's only 7-star hotel - an iconic sail-shaped masterpiece of luxury"},
        {"name": "Dubai Budget Stay", "destination": "Dubai", "category": "budget",
         "price_per_night": 60, "rating": 3.7, "reviews": 1450,
         "amenities": ["free wifi", "pool", "gym", "restaurant", "parking"],
         "latitude": 25.2000, "longitude": 55.2708, "distance_from_center": 3.0,
         "description": "Great value hotel in Dubai with excellent facilities and convenient location"},
        {"name": "Dubai Marina Hotel", "destination": "Dubai", "category": "resort",
         "price_per_night": 200, "rating": 4.3, "reviews": 1890,
         "amenities": ["pool", "spa", "marina view", "restaurant", "free wifi", "private beach"],
         "latitude": 25.0800, "longitude": 55.1400, "distance_from_center": 7.0,
         "description": "Stunning marina-front resort with panoramic water views and premium amenities"},
        
        # Goa
        {"name": "Goa Beach Resort", "destination": "Goa", "category": "resort",
         "price_per_night": 120, "rating": 4.4, "reviews": 2100,
         "amenities": ["pool", "beach access", "restaurant", "bar", "free wifi", "water sports"],
         "latitude": 15.2993, "longitude": 74.1240, "distance_from_center": 2.0,
         "description": "Beautiful beachfront resort with water sports and Goan charm"},
        {"name": "Goa Budget Guesthouse", "destination": "Goa", "category": "budget",
         "price_per_night": 25, "rating": 3.6, "reviews": 1800,
         "amenities": ["free wifi", "breakfast", "air conditioning", "bicycle rental"],
         "latitude": 15.3100, "longitude": 74.1300, "distance_from_center": 3.0,
         "description": "Cozy guesthouse with warm hospitality and authentic Goan atmosphere"},
        {"name": "Goa Portuguese Villa", "destination": "Goa", "category": "luxury",
         "price_per_night": 250, "rating": 4.7, "reviews": 780,
         "amenities": ["private pool", "garden", "restaurant", "spa", "free wifi", "library"],
         "latitude": 15.2800, "longitude": 74.1100, "distance_from_center": 1.5,
         "description": "Restored Portuguese villa offering old-world charm with modern luxury"},
        
        # Bangkok
        {"name": "Bangkok Riverside Hotel", "destination": "Bangkok", "category": "luxury",
         "price_per_night": 180, "rating": 4.6, "reviews": 3200,
         "amenities": ["pool", "spa", "river view", "restaurant", "free wifi", "fitness center"],
         "latitude": 13.7563, "longitude": 100.5018, "distance_from_center": 1.0,
         "description": "Elegant riverside hotel with stunning Chao Phraya River views"},
        {"name": "Bangkok Budget Inn", "destination": "Bangkok", "category": "budget",
         "price_per_night": 25, "rating": 3.8, "reviews": 4500,
         "amenities": ["free wifi", "breakfast", "air conditioning", "rooftop"],
         "latitude": 13.7600, "longitude": 100.5100, "distance_from_center": 2.0,
         "description": "Budget-friendly hotel in the heart of Bangkok's vibrant Khao San Road area"},
        {"name": "Bangkok Backpackers", "destination": "Bangkok", "category": "hostel",
         "price_per_night": 10, "rating": 4.0, "reviews": 5600,
         "amenities": ["free wifi", "shared kitchen", "common room", "bar", "rooftop pool"],
         "latitude": 13.7700, "longitude": 100.5200, "distance_from_center": 3.0,
         "description": "Award-winning backpacker hostel with rooftop pool and vibrant social scene"},
        
        # New York
        {"name": "NYC Luxury Suites", "destination": "New York", "category": "luxury",
         "price_per_night": 600, "rating": 4.8, "reviews": 2100,
         "amenities": ["spa", "fitness center", "restaurant", "bar", "central park view", "butler"],
         "latitude": 40.7128, "longitude": -74.0060, "distance_from_center": 1.0,
         "description": "Ultra-luxury suites overlooking Central Park with world-class amenities"},
        {"name": "NYC Budget Hotel", "destination": "New York", "category": "budget",
         "price_per_night": 100, "rating": 3.6, "reviews": 3800,
         "amenities": ["free wifi", "breakfast", "air conditioning", "laundry"],
         "latitude": 40.7200, "longitude": -74.0000, "distance_from_center": 2.5,
         "description": "Affordable comfort in Manhattan with easy access to all NYC attractions"},
        {"name": "NYC Hostel", "destination": "New York", "category": "hostel",
         "price_per_night": 50, "rating": 3.9, "reviews": 4200,
         "amenities": ["free wifi", "locker", "common room", "breakfast", "events"],
         "latitude": 40.7300, "longitude": -73.9900, "distance_from_center": 3.0,
         "description": "Popular NYC hostel with great location, community events, and city views"},

        # Manali
        {"name": "Manali Mountain Resort", "destination": "Manali", "category": "resort",
         "price_per_night": 100, "rating": 4.3, "reviews": 1200,
         "amenities": ["mountain view", "fireplace", "restaurant", "free wifi", "parking", "bonfire"],
         "latitude": 32.2396, "longitude": 77.1887, "distance_from_center": 1.5,
         "description": "Scenic mountain resort with stunning Himalayan views and cozy amenities"},
        {"name": "Manali Budget Lodge", "destination": "Manali", "category": "budget",
         "price_per_night": 30, "rating": 3.5, "reviews": 890,
         "amenities": ["free wifi", "heater", "parking", "breakfast", "hot water"],
         "latitude": 32.2500, "longitude": 77.1900, "distance_from_center": 2.0,
         "description": "Comfortable budget lodge with warm hospitality and mountain views"},
        {"name": "Manali Hostel", "destination": "Manali", "category": "hostel",
         "price_per_night": 12, "rating": 4.1, "reviews": 1500,
         "amenities": ["free wifi", "common room", "shared kitchen", "bonfire", "game room"],
         "latitude": 32.2400, "longitude": 77.1950, "distance_from_center": 2.5,
         "description": "Trendy hostel with bonfire nights, games, and amazing mountain backdrop"},
    ]

    def __init__(self):
        super().__init__(
            name="Hotel Agent",
            description="Suggests best accommodation options based on budget and preferences"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find and recommend hotels based on user preferences.
        
        Args:
            context: Dictionary containing user input and budget data
            
        Returns:
            Ranked hotel recommendations with details
        """
        self.log_step("Starting", "Searching for best hotels")
        
        user_input = context.get("user_input", {})
        budget_data = context.get("budget", {})
        destination_data = context.get("destination", {})
        
        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        dest_name = destination.get("name", user_input.get("destination", ""))
        
        budget = self.safe_float(user_input.get("budget", 0))
        hotel_pref = user_input.get("hotel_preference", "budget")
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        travel_type = user_input.get("travel_type", "solo")
        
        # Get hotel budget from budget agent
        hotel_budget = budget * 0.3  # Default 30%
        breakdown = budget_data.get("breakdown", {})
        if breakdown:
            hotel_budget = breakdown.get("hotel", {}).get("amount", hotel_budget)
        
        # Find matching hotels
        matching_hotels = self._find_hotels(dest_name, hotel_pref, hotel_budget, trip_days)
        
        # Score and rank
        ranked_hotels = self._score_and_rank(matching_hotels, hotel_pref, hotel_budget, travel_type)
        
        # Generate recommendations
        top_pick = ranked_hotels[0] if ranked_hotels else {}
        
        result = {
            "agent": self.name,
            "destination": dest_name,
            "hotels": ranked_hotels,
            "top_pick": top_pick,
            "total_found": len(ranked_hotels),
            "hotel_preference": hotel_pref,
            "budget_allocation": {
                "total_hotel_budget": round(hotel_budget, 2),
                "per_night_budget": round(hotel_budget / max(trip_days, 1), 2),
                "nights": trip_days
            },
            "booking_tips": self._get_booking_tips(hotel_pref, dest_name),
            "status": "success"
        }

        self.log_step("Complete",
                      f"Found {len(ranked_hotels)} hotels | Top: {top_pick.get('name', 'N/A')}")
        return result

    def _find_hotels(self, destination: str, preference: str,
                      budget: float, trip_days: int) -> List[Dict[str, Any]]:
        """Find hotels matching the destination and criteria."""
        matching = []
        
        for hotel in self.HOTEL_DATABASE:
            if hotel["destination"].lower() == destination.lower():
                # Check category match
                if preference == "budget" and hotel["category"] in ["budget", "hostel"]:
                    matching.append(hotel)
                elif preference == "luxury" and hotel["category"] == "luxury":
                    matching.append(hotel)
                elif preference == "resort" and hotel["category"] == "resort":
                    matching.append(hotel)
                elif preference == "hostel" and hotel["category"] == "hostel":
                    matching.append(hotel)
                else:
                    # Include if price fits budget
                    if hotel["price_per_night"] * trip_days <= budget:
                        matching.append(hotel)
        
        # If no exact matches, include all hotels at the destination
        if not matching:
            matching = [h for h in self.HOTEL_DATABASE if h["destination"].lower() == destination.lower()]
        
        return matching

    def _score_and_rank(self, hotels: List[Dict[str, Any]], preference: str,
                         budget: float, travel_type: str) -> List[Dict[str, Any]]:
        """Score and rank hotels based on multiple factors."""
        scored_hotels = []
        
        for hotel in hotels:
            score = 0
            
            # Price score (0-30)
            price_per_night = hotel["price_per_night"]
            daily_budget = budget / 7  # Assume 7 days max
            if price_per_night <= daily_budget * 0.5:
                score += 30
            elif price_per_night <= daily_budget * 0.75:
                score += 25
            elif price_per_night <= daily_budget:
                score += 20
            else:
                score += 10
            
            # Rating score (0-25)
            rating = hotel.get("rating", 0)
            score += (rating / 5) * 25
            
            # Reviews score (0-15)
            reviews = hotel.get("reviews", 0)
            if reviews >= 2000:
                score += 15
            elif reviews >= 1000:
                score += 12
            elif reviews >= 500:
                score += 8
            else:
                score += 4
            
            # Location score (0-15)
            distance = hotel.get("distance_from_center", 10)
            if distance <= 1:
                score += 15
            elif distance <= 2:
                score += 12
            elif distance <= 3:
                score += 8
            else:
                score += 4
            
            # Amenities score (0-10)
            amenities = hotel.get("amenities", [])
            score += min(len(amenities) * 2, 10)
            
            # Preference match bonus (0-5)
            if hotel["category"] == preference:
                score += 5
            elif preference == "budget" and hotel["category"] in ["budget", "hostel"]:
                score += 3
            
            scored_hotels.append({
                **hotel,
                "score": round(score, 1),
                "total_cost": round(hotel["price_per_night"], 2),  # Will be calculated with trip days
                "value_rating": self._get_value_rating(score),
                "recommended_for": self._get_recommended_for(hotel, travel_type)
            })
        
        # Sort by score descending
        scored_hotels.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_hotels

    def _get_value_rating(self, score: float) -> str:
        """Get value rating based on score."""
        if score >= 80:
            return "excellent"
        elif score >= 65:
            return "great"
        elif score >= 50:
            return "good"
        elif score >= 35:
            return "fair"
        else:
            return "okay"

    def _get_recommended_for(self, hotel: Dict[str, Any], travel_type: str) -> str:
        """Get recommendation context for a hotel."""
        category = hotel["category"]
        
        recommendations = {
            ("luxury", "couple"): "💑 Perfect for a romantic getaway",
            ("luxury", "solo"): "👤 Treat yourself to premium comfort",
            ("resort", "family"): "👨‍👩‍👧‍👦 Great for family vacations",
            ("resort", "couple"): "💑 Romantic resort experience",
            ("budget", "solo"): "🎒 Ideal for solo travelers",
            ("budget", "friends"): "👥 Perfect for group trips",
            ("hostel", "solo"): "🌍 Meet fellow travelers",
            ("hostel", "friends"): "👥 Fun social atmosphere"
        }
        
        key = (category, travel_type)
        if key in recommendations:
            return recommendations[key]
        return "👍 Recommended choice"

    def _get_booking_tips(self, preference: str, destination: str) -> List[str]:
        """Generate booking tips."""
        tips = [
            f"📅 Book {preference} accommodations in {destination} at least 2-3 weeks in advance",
            "⭐ Read recent reviews before booking",
            "📍 Check hotel location on the map - proximity to attractions matters",
            "💳 Look for free cancellation options",
        ]
        
        if preference == "budget":
            tips.append("🏨 Compare prices across multiple booking platforms")
            tips.append("🎯 Sign up for hotel loyalty programs for discounts")
        elif preference == "luxury":
            tips.append("🎯 Contact hotel directly for best available upgrades")
            tips.append("🌟 Ask about complimentary airport transfers")
        elif preference == "hostel":
            tips.append("🔒 Book lockers in advance for valuables")
            tips.append("🌍 Read hostel reviews from solo travelers")
        elif preference == "resort":
            tips.append("🏖️ Check if meals are included (all-inclusive deals)")
            tips.append("🎯 Book resort activities in advance")
        
        return tips

