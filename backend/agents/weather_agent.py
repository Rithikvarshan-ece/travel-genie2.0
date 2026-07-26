"""
TravelGenie Weather Agent
Checks weather conditions, suggests indoor/outdoor activities,
and warns about rain or extreme weather.
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent
import random
from datetime import datetime, timedelta


class WeatherAgent(BaseAgent):
    """
    The Weather Agent provides weather forecasts and recommendations
    based on the destination and travel dates.
    Uses simulated weather data (can be connected to OpenWeather API).
    """

    # Weather conditions by season
    SEASONAL_WEATHER = {
        "summer": {
            "conditions": ["sunny", "clear", "hot"],
            "temp_range": (28, 38),
            "humidity_range": (60, 85),
            "indoor": ["Visit museums", "Shopping malls", "Indoor cafes", "Aquariums"],
            "outdoor": ["Beach activities", "Hiking early morning", "Sunset viewing", "Swimming"],
            "packing": ["Sunscreen SPF 50+", "Light cotton clothes", "Sunglasses", "Hat", "Water bottle"]
        },
        "winter": {
            "conditions": ["cold", "cloudy", "snowy", "clear"],
            "temp_range": (-5, 15),
            "humidity_range": (40, 70),
            "indoor": ["Visit museums", "Indoor markets", "Cooking classes", "Spa treatments"],
            "outdoor": ["Skiing", "Ice skating", "Snow hiking", "Winter photography"],
            "packing": ["Warm jackets", "Thermal wear", "Gloves", "Scarf", "Winter boots"]
        },
        "spring": {
            "conditions": ["sunny", "cloudy", "light rain", "clear"],
            "temp_range": (15, 25),
            "humidity_range": (50, 75),
            "indoor": ["Art galleries", "Historical tours", "Cooking classes", "Wine tasting"],
            "outdoor": ["Garden visits", "Cycling", "Hiking", "Picnics", "Sightseeing"],
            "packing": ["Light jacket", "Comfortable shoes", "Umbrella", "Layers"]
        },
        "autumn": {
            "conditions": ["sunny", "cloudy", "windy", "clear"],
            "temp_range": (10, 22),
            "humidity_range": (45, 70),
            "indoor": ["Museum tours", "Harvest festivals", "Indoor concerts", "Art exhibitions"],
            "outdoor": ["Leaf peeping", "Hiking", "Photography", "Outdoor markets"],
            "packing": ["Warm sweaters", "Comfortable boots", "Light jacket", "Scarf"]
        },
        "monsoon": {
            "conditions": ["rainy", "stormy", "cloudy", "humid"],
            "temp_range": (25, 32),
            "humidity_range": (75, 95),
            "indoor": ["Temple tours", "Cooking classes", "Indoor markets", "Ayurvedic spa"],
            "outdoor": ["Limited - early morning walks", "Covered sightseeing", "Rain photography"],
            "packing": ["Raincoat", "Umbrella", "Waterproof shoes", "Quick-dry clothes"]
        }
    }

    def __init__(self):
        super().__init__(
            name="Weather Agent",
            description="Checks weather conditions and suggests appropriate activities"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate weather forecast and recommendations for the trip.
        
        Args:
            context: Dictionary containing user input and destination data
            
        Returns:
            Weather forecast, warnings, and activity recommendations
        """
        self.log_step("Starting", "Analyzing weather conditions")
        
        user_input = context.get("user_input", {})
        destination_data = context.get("destination", {})
        
        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        
        travel_month = user_input.get("travel_month", "")
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        interests = user_input.get("interests", [])

        # Determine season
        season = self._get_season(travel_month)
        
        # Generate daily forecast
        forecast = self._generate_forecast(season, trip_days)
        
        # Get weather warnings
        warnings = self._get_weather_warnings(forecast, season)
        
        # Suggest activities based on weather
        activities = self._suggest_activities(season, interests, forecast)

        # Generate packing suggestions
        packing = self.SEASONAL_WEATHER.get(season, self.SEASONAL_WEATHER["summer"])["packing"]

        result = {
            "agent": self.name,
            "destination": destination.get("name", "Unknown"),
            "season": season,
            "forecast": forecast,
            "warnings": warnings,
            "activity_suggestions": activities,
            "packing_suggestions": packing,
            "weather_summary": self._generate_summary(forecast, season),
            "best_time_for_outdoor": self._get_best_time_for_outdoor(forecast),
            "status": "success"
        }

        self.log_step("Complete",
                      f"Season: {season} | Days forecasted: {trip_days} | Warnings: {len(warnings)}")
        return result

    def _get_season(self, month: str) -> str:
        """Determine the season based on the month."""
        month_lower = month.lower()
        season_map = {
            "december": "winter", "january": "winter", "february": "winter",
            "march": "spring", "april": "spring", "may": "summer",
            "june": "summer", "july": "summer", "august": "summer",
            "september": "autumn", "october": "autumn", "november": "autumn"
        }
        # Check for monsoon specifically for some regions
        if month_lower in ["june", "july", "august", "september"]:
            return "monsoon"  # Can be overridden by destination
        return season_map.get(month_lower, "summer")

    def _generate_forecast(self, season: str, days: int) -> List[Dict[str, Any]]:
        """Generate daily weather forecast."""
        weather = self.SEASONAL_WEATHER.get(season, self.SEASONAL_WEATHER["summer"])
        forecast = []

        for i in range(days):
            day_date = datetime.now() + timedelta(days=i)
            condition = random.choice(weather["conditions"])
            temp = random.randint(weather["temp_range"][0], weather["temp_range"][1])
            humidity = random.randint(weather["humidity_range"][0], weather["humidity_range"][1])

            # Add some variation
            if i > 0 and random.random() < 0.3:
                # Change condition slightly from previous day
                condition = random.choice(weather["conditions"])

            forecast.append({
                "day": i + 1,
                "date": day_date.strftime("%Y-%m-%d"),
                "day_name": day_date.strftime("%A"),
                "condition": condition,
                "temperature_c": temp,
                "temperature_f": round((temp * 9/5) + 32, 1),
                "humidity": humidity,
                "wind_speed_kmh": random.randint(5, 30),
                "precipitation_chance": random.randint(0, 80) if "rain" in condition else random.randint(0, 20),
                "icon": self._get_weather_icon(condition),
                "recommendation": self._get_daily_recommendation(condition, temp)
            })

        return forecast

    def _get_weather_icon(self, condition: str) -> str:
        """Get emoji icon for weather condition."""
        icons = {
            "sunny": "☀️",
            "clear": "🌤️",
            "cloudy": "☁️",
            "hot": "🔥",
            "cold": "❄️",
            "snowy": "🌨️",
            "rainy": "🌧️",
            "stormy": "⛈️",
            "light rain": "🌦️",
            "windy": "💨",
            "humid": "💧",
            "foggy": "🌫️"
        }
        return icons.get(condition, "🌡️")

    def _get_daily_recommendation(self, condition: str, temp: int) -> str:
        """Get daily activity recommendation based on weather."""
        if condition in ["rainy", "stormy", "light rain"]:
            return "Indoor activities recommended"
        elif temp > 35:
            return "Avoid afternoon sun, stay hydrated"
        elif temp < 5:
            return "Dress warmly, limit outdoor exposure"
        elif condition in ["sunny", "clear"]:
            return "Perfect for outdoor activities! 🌟"
        elif condition == "snowy":
            return "Great for winter sports! ⛷️"
        else:
            return "Good for most activities"

    def _get_weather_warnings(self, forecast: List[Dict[str, Any]], season: str) -> List[str]:
        """Generate weather warnings based on forecast."""
        warnings = []
        
        # Check for extreme conditions
        for day in forecast:
            if day["temperature_c"] > 38:
                warnings.append(f"🔥 Extreme heat warning for {day['day_name']} ({day['date']}) - stay hydrated!")
            elif day["temperature_c"] < 0:
                warnings.append(f"❄️ Freezing temperatures on {day['day_name']} - dress warmly!")
            
            if "rain" in day["condition"] or "storm" in day["condition"]:
                if day["precipitation_chance"] > 60:
                    warnings.append(f"🌧️ High chance of rain on {day['day_name']} - carry an umbrella!")
            
            if day["wind_speed_kmh"] > 25:
                warnings.append(f"💨 Strong winds on {day['day_name']} - be careful outdoors!")

        # Season-specific warnings
        if season == "summer":
            warnings.append("☀️ Apply sunscreen regularly - UV index will be high")
        elif season == "monsoon":
            warnings.append("🌧️ Monsoon season - expect heavy showers, plan indoor activities")
        elif season == "winter":
            warnings.append("❄️ Winter season - pack warm clothes and check road conditions")

        # Remove duplicates while preserving order
        seen = set()
        unique_warnings = []
        for w in warnings:
            if w not in seen:
                seen.add(w)
                unique_warnings.append(w)

        return unique_warnings[:5]  # Max 5 warnings

    def _suggest_activities(self, season: str, interests: List[str],
                             forecast: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Suggest indoor and outdoor activities based on weather."""
        weather = self.SEASONAL_WEATHER.get(season, self.SEASONAL_WEATHER["summer"])
        
        # Check if any rainy days in forecast
        has_rain = any("rain" in day["condition"] or "storm" in day["condition"]
                      for day in forecast)
        
        # Start with seasonal suggestions
        indoor = list(weather["indoor"])
        outdoor = list(weather["outdoor"])

        # Add interest-based activities
        interest_activities = {
            "beach": ["Beach volleyball", "Snorkeling", "Sunbathing", "Beach photography"],
            "adventure": ["Bungee jumping", "Paragliding", "Scuba diving", "Rock climbing"],
            "historical": ["Guided heritage walks", "Museum tours", "Archaeological site visits"],
            "food": ["Street food tour", "Cooking class", "Food market visit", "Wine tasting"],
            "shopping": ["Local market shopping", "Mall exploration", "Souvenir hunting"],
            "nature": ["Nature trail hiking", "Bird watching", "Garden visits", "Sunset photography"],
            "nightlife": ["Club hopping", "Live music venues", "Rooftop bars", "Night markets"],
            "culture": ["Cultural shows", "Traditional dance performances", "Art workshops"],
        }

        for interest in interests:
            if interest in interest_activities:
                acts = interest_activities[interest]
                if has_rain:
                    indoor.extend(acts[:2])
                else:
                    outdoor.extend(acts[:2])

        # If rainy, add more indoor suggestions
        if has_rain:
            indoor.extend(["Spa treatments", "Reading at a cafe", "Movie marathon", "Indoor swimming"])

        return {
            "indoor": list(dict.fromkeys(indoor))[:5],  # Unique, max 5
            "outdoor": list(dict.fromkeys(outdoor))[:5],
            "note": "Indoor activities recommended" if has_rain else "Great weather for outdoor adventures!"
        }

    def _generate_summary(self, forecast: List[Dict[str, Any]], season: str) -> str:
        """Generate a human-readable weather summary."""
        if not forecast:
            return "Weather data not available"
        
        conditions = [day["condition"] for day in forecast]
        temps = [day["temperature_c"] for day in forecast]
        avg_temp = sum(temps) / len(temps)
        
        sunny_days = conditions.count("sunny") + conditions.count("clear")
        rainy_days = sum(1 for c in conditions if "rain" in c or "storm" in c)
        
        if sunny_days == len(forecast):
            return f"☀️ Beautiful weather throughout your trip! Average temperature: {avg_temp:.0f}°C"
        elif rainy_days > len(forecast) / 2:
            return f"🌧️ Mostly rainy during your stay. Avg temp: {avg_temp:.0f}°C. Pack an umbrella!"
        elif sunny_days > rainy_days:
            return f"🌤️ Mostly good weather with some clouds. Avg temp: {avg_temp:.0f}°C"
        else:
            return f"⛅ Mixed weather conditions. Avg temp: {avg_temp:.0f}°C. Be prepared for changes!"

    def _get_best_time_for_outdoor(self, forecast: List[Dict[str, Any]]) -> str:
        """Find the best day/time for outdoor activities."""
        best_day = None
        best_score = -1
        
        for day in forecast:
            score = 0
            if day["condition"] in ["sunny", "clear"]:
                score += 10
            elif day["condition"] in ["cloudy", "windy"]:
                score += 5
            
            if 20 <= day["temperature_c"] <= 30:
                score += 8
            elif 15 <= day["temperature_c"] <= 35:
                score += 4
            
            if day["precipitation_chance"] < 30:
                score += 6
            
            if score > best_score:
                best_score = score
                best_day = day
        
        if best_day:
            return f"Best day for outdoor activities: {best_day['day_name']} ({best_day['date']}) - {best_day['condition']}"
        return "No particularly good day for outdoor activities found"

