"""
TravelGenie Itinerary Agent
Generates detailed day-by-day itinerary with:
- Morning, Afternoon, Evening, Night activities
- Repeat for every day of the trip
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent


class ItineraryAgent(BaseAgent):
    """
    The Itinerary Agent creates comprehensive daily schedules
    incorporating all recommendations from other agents.
    """

    # Time slots for each day
    TIME_SLOTS = [
        {"slot": "morning", "icon": "🌅", "label": "Morning", "hours": "8:00 AM - 12:00 PM"},
        {"slot": "afternoon", "icon": "☀️", "label": "Afternoon", "hours": "12:00 PM - 5:00 PM"},
        {"slot": "evening", "icon": "🌆", "label": "Evening", "hours": "5:00 PM - 9:00 PM"},
        {"slot": "night", "icon": "🌙", "label": "Night", "hours": "9:00 PM onwards"}
    ]

    # Meal suggestions
    MEALS = {
        "breakfast": ["Continental Breakfast", "Local Breakfast Special", "Hotel Buffet", "Cafe Breakfast"],
        "lunch": ["Local Cuisine Restaurant", "Street Food Adventure", "Beachside Lunch", "Food Market"],
        "dinner": ["Rooftop Dinner", "Traditional Restaurant", "Fine Dining", "Local Eatery"],
        "snacks": ["Fresh Coconut Water", "Local Street Snacks", "Fruit Platter", "Evening Tea"]
    }

    def __init__(self):
        super().__init__(
            name="Itinerary Agent",
            description="Generates detailed day-by-day travel itinerary"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive daily itinerary.
        
        Args:
            context: Dictionary containing all agent outputs
            
        Returns:
            Complete day-by-day itinerary
        """
        self.log_step("Starting", "Generating daily itinerary")
        
        user_input = context.get("user_input", {})
        destination_data = context.get("destination", {})
        weather_data = context.get("weather", {})
        hotel_data = context.get("hotel", {})
        transport_data = context.get("transport", {})
        attraction_data = context.get("attraction", {})
        budget_data = context.get("budget", {})

        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        interests = user_input.get("interests", ["nature"])
        travel_type = user_input.get("travel_type", "solo")
        hotel_pref = user_input.get("hotel_preference", "budget")

        # Get recommendations from other agents
        forecast = weather_data.get("forecast", [])
        hotels = hotel_data.get("hotels", [])
        top_hotel = hotels[0] if hotels else {}
        attractions = attraction_data.get("attractions", [])
        daily_breakdown = attraction_data.get("daily_breakdown", [])
        best_transport = transport_data.get("best_option", {})
        
        # Get budget info
        daily_budget = budget_data.get("daily_budget", {})
        per_day_total = daily_budget.get("per_day_total", 0)

        # Generate itinerary for each day
        days = []
        for day in range(1, trip_days + 1):
            day_weather = {}
            if day - 1 < len(forecast):
                day_weather = forecast[day - 1]

            day_attractions = []
            if day - 1 < len(daily_breakdown):
                day_attractions = daily_breakdown[day - 1].get("attractions", [])

            day_plan = self._generate_day_plan(
                day, trip_days, day_weather, day_attractions,
                top_hotel, best_transport, interests, travel_type,
                per_day_total, destination
            )
            days.append(day_plan)

        # Generate summary statistics
        summary = self._generate_summary(days, trip_days, destination)

        # Generate tips
        tips = self._generate_travel_tips(travel_type, interests, destination)

        result = {
            "agent": self.name,
            "destination": destination.get("name", "Unknown"),
            "trip_duration_days": trip_days,
            "travel_type": travel_type,
            "days": days,
            "summary": summary,
            "travel_tips": tips,
            "pace": self._get_pace(travel_type, interests),
            "status": "success"
        }

        self.log_step("Complete", f"Generated itinerary for {trip_days} days")
        return result

    def _generate_day_plan(self, day: int, total_days: int,
                            weather: Dict[str, Any],
                            day_attractions: List[Dict[str, Any]],
                            hotel: Dict[str, Any],
                            transport: Dict[str, Any],
                            interests: List[str],
                            travel_type: str,
                            daily_budget: float,
                            destination: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed plan for a single day."""
        
        day_theme = self._get_day_theme(day, total_days, interests)

        # Build time-slot activities
        slots = []
        
        # Morning
        morning_activities = []
        if day == 1:
            morning_activities.append({
                "activity": "Arrival & Check-in",
                "icon": "🏨",
                "description": f"Arrive at {destination.get('name', 'destination')}, check into {hotel.get('name', 'hotel')}",
                "duration": "2-3 hours",
                "cost": "Transport cost included"
            })
        else:
            morning_activities.append({
                "activity": "Breakfast",
                "icon": "🍳",
                "description": self._get_meal_suggestion("breakfast", day),
                "duration": "45 mins",
                "cost": f"~${daily_budget * 0.15:.0f}"
            })

        # Add morning attraction
        morning_attr = self._find_attraction_for_time(day_attractions, "Morning")
        if morning_attr:
            morning_activities.append({
                "activity": morning_attr.get("name", "Explore"),
                "icon": "📸",
                "description": morning_attr.get("description", ""),
                "duration": morning_attr.get("duration", "2 hours"),
                "cost": morning_attr.get("cost", "Variable")
            })
        else:
            # Add default morning activity
            morning_activities.append({
                "activity": self._get_default_activity("morning", interests),
                "icon": "🚶",
                "description": f"Explore the neighborhood and local attractions",
                "duration": "2 hours",
                "cost": "Free"
            })

        slots.append({
            "slot": "morning",
            "icon": "🌅",
            "label": "Morning",
            "hours": "8:00 AM - 12:00 PM",
            "activities": morning_activities,
            "weather_note": self._get_weather_note(weather, "morning")
        })

        # Afternoon
        afternoon_activities = [
            {
                "activity": "Lunch",
                "icon": "🍽️",
                "description": self._get_meal_suggestion("lunch", day),
                "duration": "1 hour",
                "cost": f"~${daily_budget * 0.2:.0f}"
            }
        ]

        afternoon_attr = self._find_attraction_for_time(day_attractions, "Afternoon")
        if afternoon_attr:
            afternoon_activities.append({
                "activity": afternoon_attr.get("name", "Explore"),
                "icon": "🏛️",
                "description": afternoon_attr.get("description", ""),
                "duration": afternoon_attr.get("duration", "3 hours"),
                "cost": afternoon_attr.get("cost", "Variable")
            })
        else:
            afternoon_activities.append({
                "activity": self._get_default_activity("afternoon", interests),
                "icon": "🛍️",
                "description": "Explore local markets and shops",
                "duration": "2-3 hours",
                "cost": "Variable"
            })

        # Add rest/break
        afternoon_activities.append({
            "activity": "Rest & Refresh",
            "icon": "☕",
            "description": "Coffee break or rest at hotel",
            "duration": "30 mins",
            "cost": "~$5"
        })

        slots.append({
            "slot": "afternoon",
            "icon": "☀️",
            "label": "Afternoon",
            "hours": "12:00 PM - 5:00 PM",
            "activities": afternoon_activities,
            "weather_note": self._get_weather_note(weather, "afternoon")
        })

        # Evening
        evening_activities = [
            {
                "activity": "Sunset Viewing",
                "icon": "🌅",
                "description": self._get_sunset_activity(destination),
                "duration": "1 hour",
                "cost": "Free"
            }
        ]

        evening_attr = self._find_attraction_for_time(day_attractions, "Evening")
        if evening_attr:
            evening_activities.append({
                "activity": evening_attr.get("name", "Explore"),
                "icon": "🎭",
                "description": evening_attr.get("description", ""),
                "duration": evening_attr.get("duration", "2 hours"),
                "cost": evening_attr.get("cost", "Variable")
            })
        else:
            evening_activities.append({
                "activity": self._get_default_activity("evening", interests),
                "icon": "🎵",
                "description": "Evening entertainment and cultural activities",
                "duration": "2 hours",
                "cost": "Variable"
            })

        evening_activities.append({
            "activity": "Dinner",
            "icon": "🍷",
            "description": self._get_meal_suggestion("dinner", day),
            "duration": "1.5 hours",
            "cost": f"~${daily_budget * 0.25:.0f}"
        })

        slots.append({
            "slot": "evening",
            "icon": "🌆",
            "label": "Evening",
            "hours": "5:00 PM - 9:00 PM",
            "activities": evening_activities,
            "weather_note": self._get_weather_note(weather, "evening")
        })

        # Night
        night_activities = []
        if "nightlife" in interests:
            night_activities.append({
                "activity": "Nightlife Exploration",
                "icon": "🌙",
                "description": "Experience the local nightlife scene",
                "duration": "2-3 hours",
                "cost": "~$30-50"
            })
        else:
            night_activities.append({
                "activity": "Relax at Hotel",
                "icon": "🏨",
                "description": f"Return to {hotel.get('name', 'hotel')}, rest and plan tomorrow",
                "duration": "Overnight",
                "cost": "Free"
            })
        
        night_activities.append({
            "activity": "Plan Next Day",
            "icon": "📋",
            "description": "Review itinerary for next day, get rest",
            "duration": "30 mins",
            "cost": "Free"
        })

        slots.append({
            "slot": "night",
            "icon": "🌙",
            "label": "Night",
            "hours": "9:00 PM onwards",
            "activities": night_activities,
            "weather_note": ""
        })

        # Calculate daily cost
        daily_cost = self._calculate_daily_cost(slots, daily_budget)

        return {
            "day": day,
            "title": f"Day {day}: {day_theme}",
            "date": f"Day {day} of {total_days}",
            "weather": weather,
            "hotel": hotel.get("name", "Hotel"),
            "transport_tip": self._get_transport_tip(transport, day),
            "slots": slots,
            "daily_cost_estimate": daily_cost,
            "budget_check": self._budget_check(daily_cost, daily_budget),
            "highlights": [slot["activities"][0]["activity"] for slot in slots if slot["activities"]]
        }

    def _get_day_theme(self, day: int, total_days: int, interests: List[str]) -> str:
        """Get a theme for each day."""
        default_themes = [
            "Arrival & City Introduction",
            "Main Exploration",
            "Adventure Day",
            "Culture & Food Journey",
            "Relaxation & Shopping",
            "Off the Beaten Path",
            "Nature & Outdoors",
            "Local Immersion",
            "Free & Easy",
            "Farewell & Memories"
        ]
        
        if day <= len(default_themes):
            theme = default_themes[day - 1]
        else:
            theme = f"Exploration Day {day}"
        
        # Customize based on interests
        if day == 2 and "historical" in interests:
            theme = "Heritage & History Tour"
        elif day == 3 and "adventure" in interests:
            theme = "Adventure & Thrills"
        elif day == total_days:
            theme = "Farewell & Last Explorations"
        
        return theme

    def _find_attraction_for_time(self, attractions: List[Dict[str, Any]],
                                    time_slot: str) -> Dict[str, Any]:
        """Find an attraction for a specific time slot."""
        for attr in attractions:
            if attr.get("time", "").startswith(time_slot):
                return attr
        return {}

    def _get_default_activity(self, time: str, interests: List[str]) -> str:
        """Get a default activity based on time and interests."""
        defaults = {
            "morning": {
                "beach": "Beach Morning Walk",
                "historical": "Heritage Walk",
                "adventure": "Morning Trek",
                "nature": "Nature Trail Walk",
                "food": "Local Breakfast Tour",
                "default": "City Walking Tour"
            },
            "afternoon": {
                "beach": "Swimming & Water Sports",
                "historical": "Museum Visit",
                "adventure": "Adventure Sports",
                "nature": "Botanical Garden Visit",
                "shopping": "Shopping District Exploration",
                "default": "Local Area Exploration"
            },
            "evening": {
                "beach": "Sunset Beach Walk",
                "historical": "Old City Evening Walk",
                "food": "Food Market Visit",
                "nightlife": "Pre-party Drinks",
                "shopping": "Night Market Shopping",
                "default": "Sunset Viewing"
            }
        }
        
        time_defaults = defaults.get(time, {})
        for interest in interests:
            if interest in time_defaults:
                return time_defaults[interest]
        return time_defaults.get("default", "Exploration Time")

    def _get_meal_suggestion(self, meal_type: str, day: int) -> str:
        """Get a meal suggestion."""
        meals = self.MEALS.get(meal_type, ["Local Cuisine"])
        idx = (day - 1) % len(meals)
        return meals[idx]

    def _get_sunset_activity(self, destination: Dict[str, Any]) -> str:
        """Get sunset activity suggestion."""
        dest_name = destination.get("name", "")
        activities = [
            f"Sunset at {dest_name} Beach",
            f"Sunset Viewing from Rooftop",
            f"Evening Walk along the Coast",
            "Sunset Photography Session",
            "Sunset Cruise Experience"
        ]
        import random
        return random.choice(activities)

    def _get_weather_note(self, weather: Dict[str, Any], time: str) -> str:
        """Get weather note for a time slot."""
        if not weather:
            return ""
        
        condition = weather.get("condition", "")
        temp = weather.get("temperature_c", 25)
        
        if condition in ["rainy", "stormy", "light rain"]:
            return "🌧️ Rain expected - carry umbrella"
        elif temp > 35 and time == "afternoon":
            return "🔥 Very hot - stay hydrated, avoid direct sun"
        elif temp < 10:
            return "❄️ Cold - dress warmly"
        elif condition in ["sunny", "clear"]:
            return "☀️ Perfect weather for outdoor activities"
        return ""

    def _get_transport_tip(self, transport: Dict[str, Any], day: int) -> str:
        """Get transportation tip for the day."""
        mode = transport.get("mode", "walking")
        tips = {
            "flight": "🚕 Use local taxis or rideshare for airport transfers",
            "train": "🚄 Train stations are well-connected to city centers",
            "bus": "🚌 Get a local transport pass for unlimited bus travel",
            "car": "🚗 Check parking availability at attractions",
            "rental_car": "🚙 Return rental car at least 2 hours before flight"
        }
        tip = tips.get(mode, "🚶 Walk or use local transport for short distances")
        
        if day == 1:
            return f"🚕 Airport/Hotel Transfer: {tip}"
        return f"🚗 Local Transport: {tip}"

    def _calculate_daily_cost(self, slots: List[Dict[str, Any]], daily_budget: float) -> float:
        """Calculate estimated daily cost."""
        total = 0
        for slot in slots:
            for activity in slot.get("activities", []):
                cost_str = activity.get("cost", "$0")
                # Extract numbers from cost string
                import re
                numbers = re.findall(r'\d+', cost_str.replace(",", ""))
                if numbers:
                    total += float(numbers[0])
        return round(total, 2)

    def _budget_check(self, daily_cost: float, daily_budget: float) -> Dict[str, Any]:
        """Check if daily cost is within budget."""
        if daily_budget <= 0:
            return {"status": "unknown", "message": "Budget data not available"}
        
        if daily_cost <= daily_budget:
            remaining = daily_budget - daily_cost
            return {
                "status": "within_budget",
                "message": f"✅ ${remaining:.0f} remaining for the day",
                "remaining": round(remaining, 2)
            }
        else:
            over = daily_cost - daily_budget
            return {
                "status": "over_budget",
                "message": f"⚠️ ${over:.0f} over daily budget",
                "over_by": round(over, 2)
            }

    def _generate_summary(self, days: List[Dict[str, Any]], total_days: int,
                           destination: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trip summary statistics."""
        total_cost = sum(d.get("daily_cost_estimate", 0) for d in days)
        total_activities = sum(len(d.get("highlights", [])) for d in days)
        
        return {
            "total_days": total_days,
            "estimated_total_cost": round(total_cost, 2),
            "total_activities": total_activities,
            "pace_description": f"{total_activities // total_days} activities per day on average",
            "destination": destination.get("name", "Unknown"),
            "best_memory_moments": [d.get("highlights", [])[0] for d in days if d.get("highlights")]
        }

    def _generate_travel_tips(self, travel_type: str, interests: List[str],
                               destination: Dict[str, Any]) -> List[str]:
        """Generate general travel tips."""
        tips = [
            "💧 Stay hydrated - carry a reusable water bottle",
            "📱 Download offline maps for navigation",
            "💊 Carry a basic first-aid kit",
            "🔌 Pack a universal travel adapter",
            "📸 Keep camera/phone charged for memories",
        ]
        
        if travel_type == "solo":
            tips.extend([
                "📍 Share your location with trusted contacts",
                "🤝 Join group tours to meet fellow travelers",
            ])
        elif travel_type == "family":
            tips.extend([
                "👶 Plan kid-friendly activities and breaks",
                "🍼 Pack snacks and entertainment for children",
            ])
        
        if "beach" in interests:
            tips.append("🧴 Apply reef-safe sunscreen before water activities")
        if "adventure" in interests:
            tips.append("🏥 Ensure your travel insurance covers adventure sports")
        
        return tips

    def _get_pace(self, travel_type: str, interests: List[str]) -> str:
        """Determine the pace of the trip."""
        if "adventure" in interests or travel_type == "friends":
            return "Fast-paced - maximum exploration"
        elif travel_type == "family" or "nature" in interests:
            return "Moderate - balanced activities and relaxation"
        elif travel_type == "couple":
            return "Relaxed - romantic and leisure focused"
        else:
            return "Flexible - at your own pace"

