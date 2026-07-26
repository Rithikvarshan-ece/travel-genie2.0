"""
TravelGenie Transport Agent
Chooses best transportation mode by comparing:
- Flight, Train, Bus, Taxi, Rental Car
- Travel Time, Price, Comfort
Returns best option with reasoning.
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent


class TransportAgent(BaseAgent):
    """
    The Transport Agent analyzes different transportation options
    and recommends the best mode based on budget, distance, and preferences.
    """

    # Average speeds for different transport modes (km/h)
    SPEEDS = {
        "flight": 800,
        "train": 120,
        "bus": 60,
        "car": 80,
        "rental_car": 80
    }

    # Comfort ratings (1-10)
    COMFORT = {
        "flight": 8,
        "train": 7,
        "bus": 5,
        "car": 6,
        "rental_car": 6
    }

    # Environmental impact (CO2 kg/km, lower is better)
    ENVIRONMENTAL_IMPACT = {
        "flight": 0.255,
        "train": 0.041,
        "bus": 0.105,
        "car": 0.171,
        "rental_car": 0.171
    }

    def __init__(self):
        super().__init__(
            name="Transport Agent",
            description="Compares transportation modes and recommends the best option"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and recommend transportation options.
        
        Args:
            context: Dictionary containing user input and destination data
            
        Returns:
            Best transport options with comparisons
        """
        self.log_step("Starting", "Analyzing transportation options")
        
        user_input = context.get("user_input", {})
        destination_data = context.get("destination", {})
        budget_data = context.get("budget", {})
        
        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        
        budget = self.safe_float(user_input.get("budget", 0))
        source = user_input.get("source_city", "Unknown")
        transport_pref = user_input.get("transportation", "flight")
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        travel_type = user_input.get("travel_type", "solo")
        travelers = self._get_traveler_count(travel_type)

        # Estimate distance (simulated based on destination)
        distance = self._estimate_distance(source, destination.get("name", ""))
        
        # Get budget allocation for transport
        transport_budget = 0
        breakdown = budget_data.get("breakdown", {})
        if breakdown:
            transport_budget = breakdown.get("transport", {}).get("amount", budget * 0.2)

        # Evaluate all transport modes
        options = self._evaluate_options(distance, transport_budget, travelers, transport_pref)
        
        # Sort by overall score
        options.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Get the best option
        best_option = options[0] if options else {}

        # Generate comparison table
        comparison = self._generate_comparison(options)

        result = {
            "agent": self.name,
            "source": source,
            "destination": destination.get("name", "Unknown"),
            "estimated_distance_km": distance,
            "preferred_mode": transport_pref,
            "options": options,
            "best_option": best_option,
            "comparison": comparison,
            "recommendation_reason": self._get_recommendation_reason(best_option, distance),
            "status": "success"
        }

        self.log_step("Complete",
                      f"Best option: {best_option.get('mode', 'N/A')} | Score: {best_option.get('overall_score', 0)}")
        return result

    def _get_traveler_count(self, travel_type: str) -> int:
        """Estimate number of travelers."""
        counts = {"solo": 1, "couple": 2, "family": 4, "friends": 3}
        return counts.get(travel_type, 2)

    def _estimate_distance(self, source: str, destination: str) -> int:
        """
        Estimate distance between source and destination.
        Uses a simplified mapping - in production, use Google Maps API.
        """
        # Approximate distances from common source cities (km)
        distance_map = {
            "New York": {"Paris": 5840, "London": 5570, "Tokyo": 10840, "Bali": 16230, "Dubai": 11000},
            "London": {"Paris": 344, "New York": 5570, "Tokyo": 9570, "Bali": 12700, "Dubai": 5500},
            "Mumbai": {"Paris": 7000, "London": 7200, "Tokyo": 6800, "Bali": 5800, "Dubai": 2900},
            "Delhi": {"Paris": 6500, "London": 6700, "Tokyo": 5900, "Bali": 5100, "Dubai": 2200},
            "Dubai": {"Paris": 5250, "London": 5500, "Tokyo": 7900, "Bali": 8200, "New York": 11000},
            "Singapore": {"Paris": 10700, "London": 10900, "Tokyo": 5300, "Bali": 1600, "Dubai": 6200},
            "Sydney": {"Paris": 16900, "London": 17000, "Tokyo": 7800, "Bali": 4600, "New York": 16000},
        }

        # Try to find distance from source to destination
        if source in distance_map and destination in distance_map[source]:
            return distance_map[source][destination]
        
        # Return a random-ish default based on continent proximity
        continent_distances = {
            ("Asia", "Asia"): 3000,
            ("Asia", "Europe"): 6000,
            ("Asia", "North America"): 11000,
            ("Europe", "Europe"): 1000,
            ("Europe", "Asia"): 6000,
            ("Europe", "North America"): 6000,
            ("North America", "Europe"): 6000,
            ("North America", "Asia"): 11000,
        }
        
        return 3000  # Default distance

    def _evaluate_options(self, distance: int, budget: float,
                           travelers: int, preference: str) -> List[Dict[str, Any]]:
        """Evaluate all transportation options."""
        options = []
        
        for mode in ["flight", "train", "bus", "car", "rental_car"]:
            option = self._calculate_option(mode, distance, budget, travelers, preference)
            options.append(option)
        
        return options

    def _calculate_option(self, mode: str, distance: int, budget: float,
                           travelers: int, preference: str) -> Dict[str, Any]:
        """Calculate detailed metrics for a transport mode."""
        
        speed = self.SPEEDS.get(mode, 60)
        comfort = self.COMFORT.get(mode, 5)
        co2_km = self.ENVIRONMENTAL_IMPACT.get(mode, 0.2)
        
        # Calculate travel time (in hours)
        if mode == "flight":
            # Include check-in, security, boarding time
            travel_time_hours = 3 + (distance / speed)  # 3 hours for airport procedures
        elif mode == "train":
            travel_time_hours = distance / speed
        elif mode == "bus":
            travel_time_hours = distance / speed
        else:  # car / rental_car
            travel_time_hours = distance / speed + 2  # 2 hours for breaks
        
        # Calculate cost
        cost_per_km = {
            "flight": 0.12,
            "train": 0.06,
            "bus": 0.03,
            "car": 0.08,
            "rental_car": 0.10
        }
        
        base_cost = distance * cost_per_km.get(mode, 0.08)
        
        # Apply traveler multiplier
        if mode in ["car", "rental_car"]:
            total_cost = base_cost + 50  # Base rental/parking fee
        elif mode == "flight":
            total_cost = base_cost * travelers * 0.8  # Slight discount per traveler
        elif mode == "train":
            total_cost = base_cost * travelers * 0.6
        else:  # bus
            total_cost = base_cost * travelers * 0.4
        
        # Calculate scores (0-10)
        # Cost score (lower is better)
        cost_score = max(0, min(10, 10 - (total_cost / (budget / 10))))
        
        # Time score (faster is better)
        max_time = 48  # 2 days max considered
        time_score = max(0, min(10, 10 - (travel_time_hours / max_time * 10)))
        
        # Comfort score
        comfort_score = comfort
        
        # Eco score (lower CO2 is better)
        max_co2 = 0.3
        eco_score = max(0, min(10, 10 - (co2_km / max_co2 * 10)))
        
        # Preference bonus
        pref_bonus = 2 if mode == preference else 0
        
        # Weighted overall score
        overall_score = (
            cost_score * 0.30 +
            time_score * 0.25 +
            comfort_score * 0.20 +
            eco_score * 0.10 +
            pref_bonus * 0.15
        )
        
        return {
            "mode": mode,
            "mode_emoji": self._get_mode_emoji(mode),
            "distance_km": distance,
            "travel_time_hours": round(travel_time_hours, 1),
            "travel_time_display": self._format_time(travel_time_hours),
            "total_cost": round(total_cost, 2),
            "cost_per_person": round(total_cost / max(travelers, 1), 2),
            "cost_score": round(cost_score, 1),
            "time_score": round(time_score, 1),
            "comfort_score": round(comfort_score, 1),
            "eco_score": round(eco_score, 1),
            "overall_score": round(overall_score, 1),
            "co2_emissions_kg": round(co2_km * distance, 2),
            "recommended_for": self._get_recommended_for(mode, distance, budget),
            "pros": self._get_pros(mode),
            "cons": self._get_cons(mode)
        }

    def _get_mode_emoji(self, mode: str) -> str:
        """Get emoji for transport mode."""
        emojis = {
            "flight": "✈️",
            "train": "🚄",
            "bus": "🚌",
            "car": "🚗",
            "rental_car": "🚙"
        }
        return emojis.get(mode, "🚗")

    def _format_time(self, hours: float) -> str:
        """Format hours into readable time."""
        if hours < 1:
            return f"{int(hours * 60)} minutes"
        elif hours < 24:
            return f"{int(hours)}h {int((hours % 1) * 60)}m"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            return f"{days}d {remaining_hours}h"

    def _get_recommended_for(self, mode: str, distance: int, budget: float) -> str:
        """Get recommendation context for transport mode."""
        recommendations = {
            "flight": "Best for long distances >1000km",
            "train": "Great for medium distances with scenic routes",
            "bus": "Most economical for short to medium distances",
            "car": "Flexible for road trips and short distances",
            "rental_car": "Freedom to explore at your own pace"
        }
        return recommendations.get(mode, "Suitable option")

    def _get_pros(self, mode: str) -> List[str]:
        """Get advantages of transport mode."""
        pros = {
            "flight": ["Fastest option", "Great for long distances", "Global connectivity"],
            "train": ["Scenic routes", "Comfortable seating", "No traffic", "Eco-friendly"],
            "bus": ["Most affordable", "Extensive network", "No booking needed"],
            "car": ["Door-to-door convenience", "Privacy", "Flexible schedule"],
            "rental_car": ["Freedom to explore", "Privacy", "Flexible itinerary"]
        }
        return pros.get(mode, [])

    def _get_cons(self, mode: str) -> List[str]:
        """Get disadvantages of transport mode."""
        cons = {
            "flight": ["Check-in time required", "Luggage restrictions", "Weather dependent"],
            "train": ["Limited routes", "Can be delayed", "Less flexible timing"],
            "bus": ["Longer travel time", "Less comfortable", "Limited luggage"],
            "car": ["Driver fatigue", "Parking issues", "Traffic", "Tolls"],
            "rental_car": ["Rental costs", "Insurance needed", "Navigation required"]
        }
        return cons.get(mode, [])

    def _generate_comparison(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comparison summary."""
        if not options:
            return {}
        
        fastest = min(options, key=lambda x: x["travel_time_hours"])
        cheapest = min(options, key=lambda x: x["total_cost"])
        most_comfortable = max(options, key=lambda x: x["comfort_score"])
        most_eco = max(options, key=lambda x: x["eco_score"])
        
        return {
            "fastest": {
                "mode": fastest["mode"],
                "emoji": fastest["mode_emoji"],
                "time": fastest["travel_time_display"]
            },
            "cheapest": {
                "mode": cheapest["mode"],
                "emoji": cheapest["mode_emoji"],
                "cost": cheapest["total_cost"]
            },
            "most_comfortable": {
                "mode": most_comfortable["mode"],
                "emoji": most_comfortable["mode_emoji"],
                "comfort_score": most_comfortable["comfort_score"]
            },
            "most_eco_friendly": {
                "mode": most_eco["mode"],
                "emoji": most_eco["mode_emoji"],
                "co2_kg": most_eco["co2_emissions_kg"]
            }
        }

    def _get_recommendation_reason(self, best: Dict[str, Any], distance: int) -> str:
        """Generate human-readable recommendation reason."""
        if not best:
            return "No suitable transport option found"
        
        mode = best.get("mode", "")
        score = best.get("overall_score", 0)
        
        reasons = {
            "flight": f"✈️ Flying is the fastest option at {best.get('travel_time_display', 'N/A')}",
            "train": f"🚄 Train offers the best balance of comfort and cost",
            "bus": f"🚌 Bus is the most economical choice",
            "car": f"🚗 Driving gives you maximum flexibility",
            "rental_car": f"🚙 Rental car lets you explore freely"
        }
        
        reason = reasons.get(mode, f"Recommended based on your preferences (score: {score})")
        
        if distance > 1000 and mode != "flight":
            reason += " | However, flying may be more practical for this distance"
        elif distance < 500 and mode == "flight":
            reason += " | Consider train/bus for shorter distance"
        
        return reason

