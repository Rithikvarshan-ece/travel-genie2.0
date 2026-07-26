"""
TravelGenie Expense Agent
Calculates and tracks all trip expenses:
- Hotel Cost
- Travel Cost
- Food Cost
- Activity/Entry Tickets
- Remaining Budget
Displays pie chart data.
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent


class ExpenseAgent(BaseAgent):
    """
    The Expense Agent calculates the final expense breakdown,
    compares against the budget, and generates chart-ready data.
    """

    def __init__(self):
        super().__init__(
            name="Expense Agent",
            description="Calculates total trip expenses and budget utilization"
        )

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate final expenses and budget analysis.
        
        Args:
            context: Dictionary containing all agent outputs
            
        Returns:
            Detailed expense breakdown with visualization data
        """
        self.log_step("Starting", "Calculating total trip expenses")
        
        user_input = context.get("user_input", {})
        budget_data = context.get("budget", {})
        hotel_data = context.get("hotel", {})
        transport_data = context.get("transport", {})
        attraction_data = context.get("attraction", {})
        destination_data = context.get("destination", {})

        suggestions = destination_data.get("suggestions", [])
        destination = suggestions[0] if suggestions else {}
        
        total_budget = self.safe_float(user_input.get("budget", 0))
        trip_days = self.safe_int(user_input.get("trip_days", 1))
        travelers = self._get_traveler_count(user_input.get("travel_type", "solo"))
        hotel_pref = user_input.get("hotel_preference", "budget")

        # Calculate individual costs
        hotel_cost = self._calculate_hotel_cost(hotel_data, trip_days)
        transport_cost = self._calculate_transport_cost(transport_data, travelers)
        food_cost = self._calculate_food_cost(trip_days, travelers, destination)
        activities_cost = self._calculate_activities_cost(attraction_data, trip_days)
        
        # Calculate additional costs
        misc_cost = self._calculate_misc_cost(trip_days, travelers)
        emergency_fund = total_budget * 0.1  # 10% emergency fund
        
        # Total cost
        total_cost = hotel_cost + transport_cost + food_cost + activities_cost + misc_cost
        
        # Budget analysis
        remaining_budget = total_budget - total_cost - emergency_fund
        budget_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
        
        # Generate breakdown for pie chart
        expense_breakdown = {
            "hotel": {
                "amount": round(hotel_cost, 2),
                "percentage": round((hotel_cost / max(total_cost, 1)) * 100, 1),
                "color": "#4F46E5",
                "label": "Accommodation"
            },
            "transport": {
                "amount": round(transport_cost, 2),
                "percentage": round((transport_cost / max(total_cost, 1)) * 100, 1),
                "color": "#10B981",
                "label": "Transportation"
            },
            "food": {
                "amount": round(food_cost, 2),
                "percentage": round((food_cost / max(total_cost, 1)) * 100, 1),
                "color": "#F59E0B",
                "label": "Food & Dining"
            },
            "activities": {
                "amount": round(activities_cost, 2),
                "percentage": round((activities_cost / max(total_cost, 1)) * 100, 1),
                "color": "#EF4444",
                "label": "Activities & Tickets"
            },
            "miscellaneous": {
                "amount": round(misc_cost, 2),
                "percentage": round((misc_cost / max(total_cost, 1)) * 100, 1),
                "color": "#8B5CF6",
                "label": "Miscellaneous"
            }
        }

        # Per-person costs
        per_person = {
            "hotel": round(hotel_cost / max(travelers, 1), 2),
            "transport": round(transport_cost / max(travelers, 1), 2),
            "food": round(food_cost / max(travelers, 1), 2),
            "activities": round(activities_cost / max(travelers, 1), 2),
            "total": round(total_cost / max(travelers, 1), 2)
        }

        # Daily costs
        daily_costs = {
            "hotel": round(hotel_cost / max(trip_days, 1), 2),
            "food": round(food_cost / max(trip_days, 1), 2),
            "activities": round(activities_cost / max(trip_days, 1), 2),
            "total": round(total_cost / max(trip_days, 1), 2)
        }

        # Savings tips
        saving_tips = self._generate_saving_tips(
            expense_breakdown, total_budget, total_cost, hotel_pref
        )

        result = {
            "agent": self.name,
            "total_budget": total_budget,
            "total_cost": round(total_cost, 2),
            "remaining_budget": round(remaining_budget, 2),
            "budget_utilization_percentage": round(budget_utilization, 1),
            "emergency_fund": round(emergency_fund, 2),
            "expense_breakdown": expense_breakdown,
            "per_person_costs": per_person,
            "daily_costs": daily_costs,
            "destination": destination.get("name", "Unknown"),
            "travelers": travelers,
            "trip_days": trip_days,
            "budget_status": self._get_budget_status(remaining_budget, total_budget),
            "saving_tips": saving_tips,
            "chart_data": {
                "type": "pie",
                "labels": [v["label"] for v in expense_breakdown.values()],
                "datasets": [{
                    "data": [v["amount"] for v in expense_breakdown.values()],
                    "backgroundColor": [v["color"] for v in expense_breakdown.values()],
                    "borderColor": ["#ffffff"] * 5,
                    "borderWidth": 2
                }]
            },
            "status": "success"
        }

        self.log_step("Complete",
                      f"Total cost: ${total_cost:,.2f} | Budget remaining: ${remaining_budget:,.2f}")
        return result

    def _get_traveler_count(self, travel_type: str) -> int:
        """Get number of travelers."""
        counts = {"solo": 1, "couple": 2, "family": 4, "friends": 3}
        return counts.get(travel_type, 2)

    def _calculate_hotel_cost(self, hotel_data: Dict[str, Any], trip_days: int) -> float:
        """Calculate total hotel cost."""
        hotels = hotel_data.get("hotels", [])
        if not hotels:
            return trip_days * 100  # Default $100/night
        
        top_hotel = hotels[0] if hotels else {}
        price_per_night = top_hotel.get("price_per_night", 100)
        return price_per_night * trip_days

    def _calculate_transport_cost(self, transport_data: Dict[str, Any],
                                   travelers: int) -> float:
        """Calculate total transport cost."""
        best_option = transport_data.get("best_option", {})
        base_cost = best_option.get("total_cost", 200)
        return base_cost

    def _calculate_food_cost(self, trip_days: int, travelers: int,
                              destination: Dict[str, Any]) -> float:
        """Calculate total food cost."""
        # Food cost per person per day based on destination
        daily_cost = destination.get("avg_daily_cost", 100)
        food_per_person_per_day = daily_cost * 0.3  # ~30% of daily cost on food
        return food_per_person_per_day * travelers * trip_days

    def _calculate_activities_cost(self, attraction_data: Dict[str, Any],
                                    trip_days: int) -> float:
        """Calculate total activities cost."""
        attractions = attraction_data.get("attractions", [])
        if not attractions:
            return trip_days * 30  # Default $30/day on activities
        
        # Estimate average cost per attraction
        total = 0
        for attr in attractions[:trip_days * 3]:  # 3 attractions per day
            cost_str = attr.get("cost", "Free")
            if cost_str == "Free":
                continue
            elif cost_str == "Low":
                total += 10
            elif cost_str == "Low-Moderate":
                total += 25
            elif cost_str == "Moderate":
                total += 40
            elif cost_str == "Moderate-High":
                total += 65
            elif cost_str == "High":
                total += 100
            else:
                total += 30
        
        return total

    def _calculate_misc_cost(self, trip_days: int, travelers: int) -> float:
        """Calculate miscellaneous costs (tips, souvenirs, etc.)."""
        base_misc = 20  # $20 per day base
        return base_misc * trip_days

    def _get_budget_status(self, remaining: float, total_budget: float) -> Dict[str, Any]:
        """Determine the budget status."""
        if total_budget <= 0:
            return {"status": "unknown", "message": "No budget data", "color": "gray"}
        
        ratio = remaining / total_budget
        
        if ratio > 0.15:
            return {
                "status": "under_budget",
                "message": f"✅ ${remaining:,.0f} under budget - Great planning!",
                "color": "green"
            }
        elif ratio >= 0:
            return {
                "status": "on_track",
                "message": f"👍 ${remaining:,.0f} remaining - Right on track!",
                "color": "blue"
            }
        elif ratio > -0.1:
            return {
                "status": "slightly_over",
                "message": f"⚠️ ${abs(remaining):,.0f} over - Minor adjustments needed",
                "color": "yellow"
            }
        else:
            return {
                "status": "over_budget",
                "message": f"❌ ${abs(remaining):,.0f} over budget - Consider adjustments",
                "color": "red"
            }

    def _generate_saving_tips(self, breakdown: Dict[str, Any],
                               total_budget: float, total_cost: float,
                               hotel_pref: str) -> List[str]:
        """Generate money-saving tips based on expense breakdown."""
        tips = []
        
        if total_cost > total_budget:
            tips.append("📊 Overall: Consider reducing trip duration or choosing budget options")
        
        hotel_pct = breakdown.get("hotel", {}).get("percentage", 0)
        if hotel_pct > 40:
            tips.append(f"🏨 Accommodation is {hotel_pct}% of costs - Consider budget hotels or hostels")
        
        food_pct = breakdown.get("food", {}).get("percentage", 0)
        if food_pct > 30:
            tips.append("🍽️ Food costs are high - Try local street food and cook some meals")
        
        activities_pct = breakdown.get("activities", {}).get("percentage", 0)
        if activities_pct > 25:
            tips.append("🎯 Look for free attractions, walking tours, and museum free-entry days")
        
        transport_pct = breakdown.get("transport", {}).get("percentage", 0)
        if transport_pct > 25:
            tips.append("🚗 Use public transport instead of taxis/cabs for local travel")
        
        # General tips
        tips.extend([
            "💰 Book flights/trains 2-3 months in advance for best rates",
            "🏠 Use hotel rewards programs and cashback websites",
            "🎒 Pack light to avoid baggage fees",
            "📱 Get a local SIM card instead of international roaming",
        ])
        
        if hotel_pref == "luxury":
            tips.append("⭐ Consider luxury hostels or boutique hotels for premium experience at lower cost")
        
        return tips[:6]  # Return top 6 tips

