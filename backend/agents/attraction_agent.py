"""
TravelGenie Attraction Agent
Generates places to visit based on interests:
- Museums, Parks, Beaches, Temples
- Adventure, Nightlife, Shopping
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent


class AttractionAgent(BaseAgent):
    """
    The Attraction Agent generates a list of must-visit places
    and activities based on the user's interests and destination.
    """

    # Attractions database by interest category
    ATTRACTIONS = {
        "beach": [
            {"name": "Sunset Beach", "type": "beach", "duration": "3-4 hours",
             "cost": "Free", "description": "Pristine beach with golden sand and stunning sunset views",
             "best_time": "Late afternoon", "tips": "Visit during low tide for best experience"},
            {"name": "Coral Reef Bay", "type": "beach", "duration": "Full day",
             "cost": "Moderate", "description": "Excellent snorkeling and diving spot with vibrant marine life",
             "best_time": "Morning", "tips": "Bring your own snorkeling gear for better fit"},
            {"name": "Hidden Cove", "type": "beach", "duration": "2-3 hours",
             "cost": "Free", "description": "Secluded beach accessible only by a short hike",
             "best_time": "Early morning", "tips": "Carry water and snacks, no facilities available"},
            {"name": "Beach Boardwalk", "type": "beach", "duration": "1-2 hours",
             "cost": "Free", "description": "Scenic boardwalk perfect for evening strolls and cycling",
             "best_time": "Evening", "tips": "Rent a bicycle for a fun ride along the coast"},
        ],
        "historical": [
            {"name": "Old City Heritage Walk", "type": "historical", "duration": "3-4 hours",
             "cost": "Low", "description": "Guided walking tour through centuries-old streets and landmarks",
             "best_time": "Morning", "tips": "Wear comfortable shoes and carry water"},
            {"name": "Grand Museum", "type": "historical", "duration": "4-5 hours",
             "cost": "Moderate", "description": "World-class museum housing artifacts spanning millennia",
             "best_time": "Weekdays", "tips": "Get audio guide for enriched experience"},
            {"name": "Ancient Temple Complex", "type": "historical", "duration": "2-3 hours",
             "cost": "Low", "description": "Magnificent temple complex with intricate architecture and history",
             "best_time": "Early morning", "tips": "Dress modestly, remove shoes before entering"},
            {"name": "Royal Palace", "type": "historical", "duration": "3-4 hours",
             "cost": "Moderate", "description": "Opulent palace showcasing royal heritage and architecture",
             "best_time": "Afternoon", "tips": "Photography may be restricted in some areas"},
        ],
        "adventure": [
            {"name": "Mountain Trek", "type": "adventure", "duration": "5-6 hours",
             "cost": "Moderate", "description": "Challenging trek through scenic mountain trails with panoramic views",
             "best_time": "Early morning", "tips": "Hire a local guide, carry altitude sickness medication if needed"},
            {"name": "White Water Rafting", "type": "adventure", "duration": "3-4 hours",
             "cost": "Moderate-High", "description": "Thrilling rafting experience through rapids and scenic gorges",
             "best_time": "Morning", "tips": "Listen carefully to safety briefing, wear life jacket"},
            {"name": "Skydiving Experience", "type": "adventure", "duration": "Half day",
             "cost": "High", "description": "Tandem skydive with experienced instructors - ultimate adrenaline rush",
             "best_time": "Clear weather days", "tips": "Book in advance, check weight requirements"},
            {"name": "Zip Lining", "type": "adventure", "duration": "2-3 hours",
             "cost": "Moderate", "description": "Soar through treetops on an exhilarating zip line course",
             "best_time": "Morning", "tips": "Wear closed-toe shoes, tuck in loose clothing"},
        ],
        "food": [
            {"name": "Local Food Market", "type": "food", "duration": "2-3 hours",
             "cost": "Low-Moderate", "description": "Vibrant market with local delicacies, street food, and fresh produce",
             "best_time": "Evening", "tips": "Go hungry! Try small portions from multiple stalls"},
            {"name": "Cooking Class", "type": "food", "duration": "3-4 hours",
             "cost": "Moderate", "description": "Learn to prepare authentic local dishes with expert chefs",
             "best_time": "Morning", "tips": "Arrive with empty stomach to enjoy your creations"},
            {"name": "Food Tour", "type": "food", "duration": "3-4 hours",
             "cost": "Moderate", "description": "Guided culinary tour exploring hidden gems and local favorites",
             "best_time": "Evening", "tips": "Don't eat breakfast, you'll sample 10+ dishes"},
            {"name": "Wine Tasting", "type": "food", "duration": "2-3 hours",
             "cost": "Moderate-High", "description": "Tour local vineyards and sample award-winning wines",
             "best_time": "Afternoon", "tips": "Use public transport or arrange a designated driver"},
        ],
        "shopping": [
            {"name": "Local Bazaar", "type": "shopping", "duration": "2-3 hours",
             "cost": "Variable", "description": "Traditional market with handicrafts, textiles, and souvenirs",
             "best_time": "Morning", "tips": "Bargain politely, compare prices across stalls"},
            {"name": "Modern Mall", "type": "shopping", "duration": "3-4 hours",
             "cost": "Variable", "description": "Contemporary shopping center with international and local brands",
             "best_time": "Afternoon", "tips": "Check for tourist tax refund facilities"},
            {"name": "Artisan Village", "type": "shopping", "duration": "2-3 hours",
             "cost": "Variable", "description": "Artists' colony with unique handmade crafts and art pieces",
             "best_time": "Late morning", "tips": "Watch artisans at work, buy direct for best prices"},
            {"name": "Night Market", "type": "shopping", "duration": "2-3 hours",
             "cost": "Low-Moderate", "description": "Bustling night market with food, fashion, and entertainment",
             "best_time": "Evening", "tips": "Keep valuables secure, bring cash for better deals"},
        ],
        "nightlife": [
            {"name": "Rooftop Bar", "type": "nightlife", "duration": "2-3 hours",
             "cost": "High", "description": "Trendy rooftop bar with incredible city views and craft cocktails",
             "best_time": "Sunset", "tips": "Dress smartly, arrive early for best seats"},
            {"name": "Live Music Venue", "type": "nightlife", "duration": "3-4 hours",
             "cost": "Moderate", "description": "Intimate venue featuring local and international live bands",
             "best_time": "Late evening", "tips": "Check the schedule and book tickets in advance"},
            {"name": "Night Club", "type": "nightlife", "duration": "4-5 hours",
             "cost": "High", "description": "Popular nightclub with top DJs and electrifying atmosphere",
             "best_time": "After 11 PM", "tips": "Guest list or VIP table recommended for weekends"},
            {"name": "Casino Night", "type": "nightlife", "duration": "3-4 hours",
             "cost": "High", "description": "Elegant casino with table games, slots, and live entertainment",
             "best_time": "Evening", "tips": "Set a budget beforehand, dress code applies"},
        ],
        "nature": [
            {"name": "Botanical Garden", "type": "nature", "duration": "2-3 hours",
             "cost": "Low", "description": "Beautiful garden with exotic plants, flowers, and peaceful walking paths",
             "best_time": "Morning", "tips": "Bring camera for butterfly and bird photography"},
            {"name": "National Park Safari", "type": "nature", "duration": "Full day",
             "cost": "Moderate-High", "description": "Guided safari through national park with diverse wildlife",
             "best_time": "Early morning", "tips": "Book safari jeep in advance, carry binoculars"},
            {"name": "Waterfall Trek", "type": "nature", "duration": "4-5 hours",
             "cost": "Moderate", "description": "Scenic hike to stunning waterfall with swimming hole",
             "best_time": "Morning", "tips": "Wear water shoes, bring change of clothes"},
            {"name": "Sunset Viewpoint", "type": "nature", "duration": "1-2 hours",
             "cost": "Free", "description": "Panoramic viewpoint offering spectacular sunset vistas",
             "best_time": "Sunset", "tips": "Arrive 30 mins early for best spot, bring jacket"},
        ],
        "culture": [
            {"name": "Cultural Show", "type": "culture", "duration": "2-3 hours",
             "cost": "Moderate", "description": "Traditional music, dance, and theatrical performances",
             "best_time": "Evening", "tips": "Book good seats, arrive 15 minutes early"},
            {"name": "Art Gallery", "type": "culture", "duration": "1-2 hours",
             "cost": "Low-Moderate", "description": "Gallery featuring contemporary and traditional local art",
             "best_time": "Afternoon", "tips": "Check for free entry days or student discounts"},
            {"name": "Heritage Village", "type": "culture", "duration": "3-4 hours",
             "cost": "Moderate", "description": "Living museum showcasing traditional village life and crafts",
             "best_time": "Morning", "tips": "Interact with artisans, try traditional activities"},
            {"name": "Festival Experience", "type": "culture", "duration": "Variable",
             "cost": "Variable", "description": "Immerse in local festival with parades, rituals, and celebrations",
             "best_time": "Check festival schedule", "tips": "Book accommodation early during festival season"},
        ]
    }

    def __init__(self):
        super().__init__(
            name="Attraction Agent",
            description="Generates places to visit based on user interests"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate attraction recommendations based on interests.
        
        Args:
            context: Dictionary containing user input and destination data
            
        Returns:
            Curated list of attractions and activities
        """
        self.log_step("Starting", "Finding attractions and activities")
        
        user_input = context.get("user_input", {})
        destination_data = context.get("destination", {})
        weather_data = context.get("weather", {})
        
        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        
        interests = user_input.get("interests", ["nature", "food"])
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        
        # Get weather-based activity suggestions
        weather_activities = weather_data.get("activity_suggestions", {})
        indoor_activities = weather_activities.get("indoor", [])
        outdoor_activities = weather_activities.get("outdoor", [])
        weather_note = weather_activities.get("note", "")

        # Get attractions based on interests
        all_attractions = []
        for interest in interests:
            if interest in self.ATTRACTIONS:
                all_attractions.extend(self.ATTRACTIONS[interest])
        
        # If no specific interests match, add general ones
        if not all_attractions:
            for key in ["nature", "food", "culture"]:
                all_attractions.extend(self.ATTRACTIONS[key])

        # Deduplicate and organize
        seen = set()
        unique_attractions = []
        for attr in all_attractions:
            if attr["name"] not in seen:
                seen.add(attr["name"])
                unique_attractions.append(attr)

        # Organize by day
        daily_breakdown = self._organize_by_day(unique_attractions, trip_days, weather_data)

        # Get top recommendations
        top_picks = unique_attractions[:5]

        result = {
            "agent": self.name,
            "destination": destination.get("name", "Unknown"),
            "interests_covered": interests,
            "attractions": unique_attractions,
            "top_picks": top_picks,
            "daily_breakdown": daily_breakdown,
            "weather_advisory": weather_note,
            "indoor_options": indoor_activities,
            "outdoor_options": outdoor_activities,
            "total_attractions": len(unique_attractions),
            "categories_found": list(set(a["type"] for a in unique_attractions)),
            "status": "success"
        }

        self.log_step("Complete",
                      f"Found {len(unique_attractions)} attractions across {len(interests)} interests")
        return result

    def _organize_by_day(self, attractions: List[Dict[str, Any]],
                          trip_days: int,
                          weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Organize attractions into daily schedules."""
        if not attractions:
            return []
        
        daily = []
        forecast = weather_data.get("forecast", [])
        
        for day in range(trip_days):
            # Get weather for this day
            day_weather = {}
            if day < len(forecast):
                day_weather = forecast[day]
            
            # Distribute attractions across days
            start_idx = (day * 3) % len(attractions)
            day_attractions = []
            
            # Morning attraction
            if start_idx < len(attractions):
                day_attractions.append({**attractions[start_idx], "time": "Morning 🌅"})
            
            # Afternoon attraction
            if start_idx + 1 < len(attractions):
                day_attractions.append({**attractions[start_idx + 1], "time": "Afternoon ☀️"})
            
            # Evening attraction
            if start_idx + 2 < len(attractions):
                day_attractions.append({**attractions[start_idx + 2], "time": "Evening 🌆"})
            
            daily.append({
                "day": day + 1,
                "attractions": day_attractions,
                "weather": day_weather,
                "theme": self._get_day_theme(day, trip_days)
            })
        
        return daily

    def _get_day_theme(self, day: int, total_days: int) -> str:
        """Get a theme for each day of the trip."""
        themes = [
            "Arrival & Exploration",
            "Main Attractions",
            "Adventure & Nature",
            "Culture & Food",
            "Relaxation & Shopping",
            "Off the Beaten Path",
            "Water Activities",
            "Local Immersion",
            "Photography Tour",
            "Farewell & Memories"
        ]
        
        idx = day % len(themes)
        return themes[idx]

