"""
TravelGenie Budget Agent
Calculates budget breakdown across all travel categories:
- Hotel Budget
- Food Budget
- Transport Budget
- Activities Budget
- Emergency Budget
"""

from typing import Any, Dict
from backend.agents.base_agent import BaseAgent


class BudgetAgent(BaseAgent):
    """
    The Budget Agent calculates an optimized budget breakdown
    based on the user's total budget, trip duration, and preferences.
    """

    def __init__(self):
        super().__init__(
            name="Budget Agent",
            description="Calculates budget allocation across all travel categories"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate budget breakdown based on user inputs.
        
        Args:
            context: Dictionary containing user input data
            
        Returns:
            Budget breakdown with allocations for each category
        """
        self.log_step("Starting", "Calculating budget allocation")
        
        user_input = context.get("user_input", {})
        total_budget = self.safe_float(user_input.get("budget", 0))
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        travel_type = user_input.get("travel_type", "solo")
        travelers = self._get_traveler_count(travel_type)
        hotel_pref = user_input.get("hotel_preference", "budget")
        transport_mode = user_input.get("transportation", "flight")

        # Calculate budget breakdown percentages based on trip type
        breakdown = self._calculate_breakdown(
            total_budget, trip_days, travel_type, hotel_pref, transport_mode
        )

        # Generate daily budget
        daily_budget = {
            "per_day_total": round(breakdown["per_day"]["total"], 2),
            "per_person_per_day": round(breakdown["per_day"]["total"] / travelers, 2),
            "breakdown_per_day": breakdown["per_day"]
        }

        result = {
            "agent": self.name,
            "total_budget": total_budget,
            "trip_days": trip_days,
            "travelers": travelers,
            "budget_per_person": round(total_budget / travelers, 2),
            "breakdown": breakdown["categories"],
            "daily_budget": daily_budget,
            "currency": "USD",
            "budget_level": self._get_budget_level(total_budget, trip_days),
            "optimization_tips": self._generate_tips(breakdown["categories"], total_budget, trip_days),
            "status": "success"
        }

        self.log_step("Complete",
                      f"Budget: ${total_budget:,.2f} | Daily: ${breakdown['per_day']['total']:,.2f}")
        return result

    def _get_traveler_count(self, travel_type: str) -> int:
        """Estimate number of travelers based on trip type."""
        counts = {
            "solo": 1,
            "couple": 2,
            "family": 4,
            "friends": 3
        }
        return counts.get(travel_type, 2)

    def _calculate_breakdown(self, total_budget: float, trip_days: int,
                              travel_type: str, hotel_pref: str,
                              transport_mode: str) -> Dict[str, Any]:
        """
        Calculate optimal budget allocation across categories.
        Uses different allocation strategies based on travel preferences.
        """
        # Base allocation percentages
        if hotel_pref == "luxury":
            hotel_pct = 0.45
            food_pct = 0.20
            activities_pct = 0.15
            transport_pct = 0.12
            emergency_pct = 0.08
        elif hotel_pref == "budget":
            hotel_pct = 0.25
            food_pct = 0.25
            activities_pct = 0.20
            transport_pct = 0.20
            emergency_pct = 0.10
        elif hotel_pref == "resort":
            hotel_pct = 0.50
            food_pct = 0.15
            activities_pct = 0.18
            transport_pct = 0.10
            emergency_pct = 0.07
        else:  # hostel
            hotel_pct = 0.15
            food_pct = 0.30
            activities_pct = 0.25
            transport_pct = 0.20
            emergency_pct = 0.10

        # Adjust based on transport mode
        transport_pct += 0.10 if transport_mode in ["flight", "rental_car"] else -0.05
        transport_pct = max(0.05, min(0.35, transport_pct))

        # Adjust based on travel type
        if travel_type == "family":
            food_pct += 0.05
            activities_pct -= 0.05
        elif travel_type == "friends":
            activities_pct += 0.05
            food_pct -= 0.05

        # Calculate amounts
        hotel_amount = round(total_budget * hotel_pct, 2)
        food_amount = round(total_budget * food_pct, 2)
        activities_amount = round(total_budget * activities_pct, 2)
        transport_amount = round(total_budget * transport_pct, 2)
        emergency_amount = round(total_budget * emergency_pct, 2)

        # Per day calculations
        per_day_total = round(total_budget / trip_days, 2)
        per_day = {
            "total": per_day_total,
            "hotel": round(hotel_amount / trip_days, 2),
            "food": round(food_amount / trip_days, 2),
            "activities": round(activities_amount / trip_days, 2),
            "transport": round(transport_amount / trip_days, 2),
            "emergency": round(emergency_amount / trip_days, 2),
        }

        return {
            "categories": {
                "hotel": {
                    "amount": hotel_amount,
                    "percentage": round(hotel_pct * 100, 1),
                    "description": f"Accommodation ({hotel_pref} preference)",
                    "per_night": round(hotel_amount / trip_days, 2)
                },
                "food": {
                    "amount": food_amount,
                    "percentage": round(food_pct * 100, 1),
                    "description": "Meals and dining",
                    "per_day": round(food_amount / trip_days, 2)
                },
                "activities": {
                    "amount": activities_amount,
                    "percentage": round(activities_pct * 100, 1),
                    "description": "Entry fees, tours, entertainment",
                    "per_day": round(activities_amount / trip_days, 2)
                },
                "transport": {
                    "amount": transport_amount,
                    "percentage": round(transport_pct * 100, 1),
                    "description": f"Local transportation ({transport_mode})",
                    "per_trip": round(transport_amount / trip_days, 2)
                },
                "emergency": {
                    "amount": emergency_amount,
                    "percentage": round(emergency_pct * 100, 1),
                    "description": "Emergency fund / buffer",
                    "per_day": round(emergency_amount / trip_days, 2)
                }
            },
            "per_day": per_day
        }

    def _get_budget_level(self, total_budget: float, trip_days: int) -> str:
        """Determine budget level description."""
        daily = total_budget / trip_days if trip_days > 0 else 0
        
        if daily >= 300:
            return "luxury"
        elif daily >= 150:
            return "comfortable"
        elif daily >= 75:
            return "moderate"
        else:
            return "budget"

    def _generate_tips(self, categories: Dict[str, Any],
                        total_budget: float, trip_days: int) -> list:
        """Generate budget optimization tips."""
        tips = []
        
        if categories["hotel"]["amount"] > total_budget * 0.4:
            tips.append("Consider reducing accommodation budget to free up funds for activities")
        
        if categories["food"]["amount"] < total_budget * 0.15:
            tips.append("Budget more for food to enjoy local cuisine experiences")
        
        if categories["emergency"]["amount"] < total_budget * 0.05:
            tips.append("Keep at least 5% for emergencies - safety first!")
        
        if total_budget / trip_days < 50:
            tips.append("Consider shortening your trip or increasing budget for better experience")
        
        if total_budget / trip_days >= 200:
            tips.append("Great budget! Consider upgrading your experiences")
        
        if not tips:
            tips.append("Your budget allocation looks well-balanced!")
        
        return tips
