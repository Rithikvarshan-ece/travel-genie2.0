"""
TravelGenie Planner Agent
Main coordinator agent that understands user intent, validates inputs,
delegates tasks to other agents, and merges outputs into a final recommendation.
"""

from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent, AgentContext


class PlannerAgent(BaseAgent):
    """
    The Planner Agent acts as the main orchestrator.
    It follows a step-by-step reasoning process:
    1. Understand User
    2. Analyze Budget
    3. Choose Destination
    4. Estimate Costs
    5. Check Weather
    6. Choose Hotels
    7. Generate Itinerary
    8. Calculate Expenses
    9. Final Recommendation
    """

    def __init__(self):
        super().__init__(
            name="Planner Agent",
            description="Main coordinator that orchestrates the entire travel planning process"
        )
        self.reasoning_steps = []

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user input and coordinate the multi-agent pipeline.
        
        Args:
            context: Dictionary containing all agent outputs
            
        Returns:
            Final comprehensive travel recommendation
        """
        self.log_step("Starting", "Understanding user requirements")
        user_input = context.get("user_input", {})
        
        # Step 1: Understand User
        self.reasoning_steps.append(self._understand_user(user_input))
        
        # Step 2: Analyze Budget
        budget_data = context.get("budget", {})
        self.reasoning_steps.append(self._analyze_budget(budget_data))
        
        # Step 3: Choose Destination
        destination_data = context.get("destination", {})
        self.reasoning_steps.append(self._choose_destination(destination_data))
        
        # Step 4: Estimate Costs
        self.reasoning_steps.append(self._estimate_costs(budget_data, destination_data))
        
        # Step 5: Check Weather
        weather_data = context.get("weather", {})
        self.reasoning_steps.append(self._check_weather(weather_data))
        
        # Step 6: Choose Hotels
        hotel_data = context.get("hotel", {})
        self.reasoning_steps.append(self._choose_hotels(hotel_data))
        
        # Step 7: Generate Itinerary
        itinerary_data = context.get("itinerary", {})
        self.reasoning_steps.append(self._generate_itinerary(itinerary_data))
        
        # Step 8: Calculate Expenses
        expense_data = context.get("expense", {})
        self.reasoning_steps.append(self._calculate_expenses(expense_data))
        
        # Step 9: Final Recommendation
        final_recommendation = self._generate_final_recommendation(
            user_input, budget_data, destination_data,
            weather_data, hotel_data, itinerary_data, expense_data
        )
        
        self.log_step("Complete", "Travel plan generated successfully")
        
        return {
            "agent": self.name,
            "reasoning_steps": self.reasoning_steps,
            "final_recommendation": final_recommendation,
            "status": "success"
        }

    def _understand_user(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Understand and validate user requirements."""
        step = {
            "step": 1,
            "name": "Understand User",
            "description": "Analyzing user preferences and requirements"
        }
        
        required_fields = ["budget", "source_city", "trip_days", "travel_type",
                          "transportation", "interests", "hotel_preference", "travel_month"]
        
        missing = [f for f in required_fields if f not in user_input]
        if missing:
            step["status"] = "warning"
            step["details"] = f"Missing optional fields: {missing}"
        else:
            step["status"] = "success"
            step["details"] = f"User wants a {user_input.get('travel_type', 'N/A')} trip to a {'/'.join(user_input.get('interests', []))} destination"
        
        return step

    def _analyze_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Analyze budget breakdown."""
        total = budget_data.get("total_budget", 0)
        breakdown = budget_data.get("breakdown", {})
        
        return {
            "step": 2,
            "name": "Analyze Budget",
            "description": "Evaluating budget allocation",
            "status": "success",
            "details": f"Total budget: ${total:,.2f}" if total else "Budget analysis pending",
            "breakdown": breakdown
        }

    def _choose_destination(self, destination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Review chosen destination."""
        suggestions = destination_data.get("suggestions", [])
        top = suggestions[0] if suggestions else {}
        
        return {
            "step": 3,
            "name": "Choose Destination",
            "description": "Selecting best destination based on preferences",
            "status": "success" if top else "warning",
            "details": f"Recommended: {top.get('name', 'N/A')}" if top else "No destinations found",
            "top_destinations": [s.get("name") for s in suggestions[:3]]
        }

    def _estimate_costs(self, budget_data: Dict[str, Any],
                        destination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Estimate overall costs."""
        suggestions = destination_data.get("suggestions", [])
        top = suggestions[0] if suggestions else {}
        daily_cost = top.get("avg_daily_cost", 0)
        trip_days = budget_data.get("trip_days", 1)
        estimated_total = daily_cost * trip_days
        
        return {
            "step": 4,
            "name": "Estimate Costs",
            "description": "Estimating total trip cost",
            "status": "success",
            "details": f"Estimated cost: ${estimated_total:,.2f} for {trip_days} days",
            "daily_cost": daily_cost,
            "estimated_total": estimated_total
        }

    def _check_weather(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Check weather conditions."""
        forecast = weather_data.get("forecast", [])
        warnings = weather_data.get("warnings", [])
        
        return {
            "step": 5,
            "name": "Check Weather",
            "description": "Analyzing weather conditions for trip duration",
            "status": "success",
            "details": f"{len(forecast)} days forecast available",
            "has_warnings": len(warnings) > 0,
            "warnings": warnings[:3]
        }

    def _choose_hotels(self, hotel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Review hotel options."""
        hotels = hotel_data.get("hotels", [])
        best = hotels[0] if hotels else {}
        
        return {
            "step": 6,
            "name": "Choose Hotels",
            "description": "Selecting best accommodation options",
            "status": "success" if best else "warning",
            "details": f"Best option: {best.get('name', 'N/A')} (${best.get('price_per_night', 0):,.2f}/night)" if best else "No hotels found",
            "available": len(hotels)
        }

    def _generate_itinerary(self, itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 7: Generate daily itinerary."""
        days = itinerary_data.get("days", [])
        
        return {
            "step": 7,
            "name": "Generate Itinerary",
            "description": "Creating day-by-day travel plan",
            "status": "success",
            "details": f"Generated plan for {len(days)} days",
            "total_activities": sum(len(d.get("activities", [])) for d in days)
        }

    def _calculate_expenses(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 8: Calculate final expenses."""
        total = expense_data.get("total_cost", 0)
        remaining = expense_data.get("remaining_budget", 0)
        
        return {
            "step": 8,
            "name": "Calculate Expenses",
            "description": "Final expense calculation and budget check",
            "status": "success",
            "details": f"Total expenses: ${total:,.2f} | Remaining: ${remaining:,.2f}",
            "within_budget": remaining >= 0
        }

    def _generate_final_recommendation(self, user_input: Dict[str, Any],
                                       budget_data: Dict[str, Any],
                                       destination_data: Dict[str, Any],
                                       weather_data: Dict[str, Any],
                                       hotel_data: Dict[str, Any],
                                       itinerary_data: Dict[str, Any],
                                       expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 9: Generate the final comprehensive recommendation."""
        
        suggestions = destination_data.get("suggestions", [])
        top_dest = suggestions[0] if suggestions else {}
        hotels = hotel_data.get("hotels", [])
        best_hotel = hotels[0] if hotels else {}
        itinerary_days = itinerary_data.get("days", [])
        transport_opts = hotel_data.get("transport_options", [])
        best_transport = transport_opts[0] if transport_opts else {}
        
        recommendation = {
            "summary": {
                "destination": top_dest.get("name", "Not selected"),
                "country": top_dest.get("country", ""),
                "duration": f"{user_input.get('trip_days', 'N/A')} days",
                "travel_type": user_input.get("travel_type", "N/A"),
                "total_budget": budget_data.get("total_budget", 0),
                "estimated_cost": expense_data.get("total_cost", 0),
                "remaining_budget": expense_data.get("remaining_budget", 0),
                "within_budget": expense_data.get("remaining_budget", 0) >= 0,
            },
            "destination_details": top_dest,
            "budget_breakdown": budget_data.get("breakdown", {}),
            "weather_forecast": weather_data.get("forecast", []),
            "weather_warnings": weather_data.get("warnings", []),
            "transport_recommendation": best_transport,
            "hotel_recommendation": best_hotel,
            "daily_itinerary": itinerary_days,
            "expense_summary": expense_data.get("expense_breakdown", {}),
            "packing_suggestions": self._generate_packing_suggestions(
                top_dest, weather_data, user_input
            ),
            "travel_tips": self._generate_travel_tips(top_dest, user_input),
            "emergency_contacts": self._generate_emergency_contacts(top_dest),
            "carbon_footprint": self._estimate_carbon_footprint(
                best_transport, top_dest, user_input
            ),
        }
        
        return recommendation

    def _generate_packing_suggestions(self, destination: Dict[str, Any],
                                       weather_data: Dict[str, Any],
                                       user_input: Dict[str, Any]) -> List[str]:
        """Generate packing suggestions based on destination and weather."""
        suggestions = [
            "📱 Universal travel adapter",
            "🧴 Sunscreen (SPF 50+)",
            "💊 Basic first-aid kit",
            "📸 Camera for memories",
        ]
        
        # Weather-based suggestions
        has_rain = any(w.get("condition", "").lower() in ["rain", "storm", "thunderstorm"]
                      for w in weather_data.get("forecast", []))
        if has_rain:
            suggestions.extend(["🌂 Umbrella", "🧥 Light rain jacket"])
        
        # Destination-based suggestions
        interests = user_input.get("interests", [])
        if "beach" in interests:
            suggestions.extend(["🏊 Swimwear", "🕶️ Sunglasses", "👒 Sun hat"])
        if "adventure" in interests:
            suggestions.extend(["🥾 Hiking shoes", "🧗 Active wear"])
        if "historical" in interests:
            suggestions.extend(["👟 Comfortable walking shoes", "🧣 Modest clothing for temples"])
        
        return suggestions

    def _generate_travel_tips(self, destination: Dict[str, Any],
                               user_input: Dict[str, Any]) -> List[str]:
        """Generate travel tips for the destination."""
        tips = [
            f"🌍 Best time to visit: {destination.get('best_months', 'Year-round')}",
            f"💰 Currency: {destination.get('currency', 'Local currency')}",
            f"🗣️ Language: {destination.get('language', 'Local language')}",
            "📱 Download offline maps before traveling",
            "💳 Notify your bank about international travel",
            "🏥 Get comprehensive travel insurance",
        ]
        
        travel_type = user_input.get("travel_type", "")
        if travel_type == "solo":
            tips.append("👤 Share your itinerary with family/friends")
            tips.append("📍 Stay in well-reviewed areas")
        elif travel_type == "family":
            tips.append("👨‍👩‍👧‍👦 Book family-friendly accommodations")
            tips.append("🎒 Pack entertainment for kids")
        elif travel_type == "couple":
            tips.append("💑 Book romantic dinners in advance")
            tips.append("🌅 Plan sunset experiences")
        
        return tips

    def _generate_emergency_contacts(self, destination: Dict[str, Any]) -> Dict[str, Any]:
        """Generate emergency contact information."""
        return {
            "police": "112 (International) or 911 (US)",
            "ambulance": "112 (International) or 911 (US)",
            "fire": "112 (International) or 911 (US)",
            "embassy": f"Contact your country's embassy in {destination.get('country', 'the destination')}",
            "travel_insurance": "Contact your insurance provider's 24/7 helpline",
            "local_emergency": f"Check local emergency numbers for {destination.get('country', 'destination')}"
        }

    def _estimate_carbon_footprint(self, transport: Dict[str, Any],
                                    destination: Dict[str, Any],
                                    user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate carbon footprint for the trip."""
        transport_mode = transport.get("mode", user_input.get("transportation", "flight"))
        
        # Approximate CO2 emissions per km per mode (in kg)
        emissions_per_km = {
            "flight": 0.255,
            "train": 0.041,
            "bus": 0.105,
            "car": 0.171,
            "rental_car": 0.171,
        }
        
        # Estimate distance based on destination (rough)
        distance = destination.get("distance", 1000)
        co2_per_km = emissions_per_km.get(transport_mode, 0.2)
        total_emissions = distance * co2_per_km / 1000  # in tons
        
        offset_cost = total_emissions * 15  # ~$15 per ton
        
        return {
            "transport_mode": transport_mode,
            "estimated_distance_km": distance,
            "estimated_emissions_tons": round(total_emissions, 2),
            "offset_cost": round(offset_cost, 2),
            "tip": "Consider carbon offset programs to neutralize your travel impact"
        }


