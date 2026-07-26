"""
TravelGenie Trip Feasibility Agent

Validates trip feasibility and calculates budget allocation.

Responsibilities:
- Validate budget adequacy for trip
- Calculate daily budget
- Allocate budget across categories
- Determine max affordable distance
- Return structured feasibility assessment
"""

import json
import logging
from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import UserTravelInput, TripFeasibilityOutput
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TripFeasibilityAgent(AsyncBaseAgent):
    """
    Validates trip feasibility based on budget and requirements.
    
    Input: UserTravelInput
    Output: TripFeasibilityOutput
    
    This is typically the first agent in the pipeline after the Planner.
    """

    def __init__(self):
        """Initialize Trip Feasibility Agent."""
        super().__init__(
            name="TripFeasibility",
            description="Validates trip feasibility and calculates budget allocation"
        )

    def get_system_prompt(self) -> str:
        """
        Get system prompt for trip feasibility assessment.
        
        Returns:
            System prompt for LLM
        """
        return """You are an expert travel budget analyst. Your task is to assess the feasibility of a trip given the user's budget, duration, travel style, and preferences.

INSTRUCTIONS:
1. Analyze the budget against standard travel costs for the given number of days
2. Calculate appropriate daily budget allocation
3. Break down budget by category: accommodation (40-50%), food (20-25%), transport (15-20%), activities (10-15%)
4. Consider the travel type (solo, family, couple, friends) when calculating needs
5. Identify any budget constraints or concerns
6. Be realistic - DO NOT hallucinate or overestimate affordability

IMPORTANT:
- Return ONLY valid JSON (no markdown, no code blocks)
- All fields are required
- confidence_score must be 0.0 to 1.0
- Double-check calculations before responding

Your response must be valid JSON that matches this schema:
{
    "is_feasible": boolean,
    "daily_budget": number (positive),
    "budget_allocation": {
        "accommodation": number (0-100, percentage),
        "food": number (0-100, percentage),
        "transport": number (0-100, percentage),
        "activities": number (0-100, percentage)
    },
    "max_affordable_distance": number (kilometers from source),
    "warnings": [list of warning strings],
    "confidence_score": number (0.0-1.0),
    "reasoning": string (explanation of assessment)
}"""

    async def process(self, input_model: BaseModel) -> TripFeasibilityOutput:
        """
        Assess trip feasibility.
        
        Args:
            input_model: UserTravelInput with trip preferences
            
        Returns:
            TripFeasibilityOutput with feasibility assessment
            
        Raises:
            AgentException: If processing fails
        """
        if not isinstance(input_model, UserTravelInput):
            raise AgentException(
                self.name,
                f"Expected UserTravelInput, got {type(input_model).__name__}"
            )

        self.last_input = input_model

        try:
            # Build user prompt
            user_prompt = self._build_user_prompt(input_model)

            # Query LLM
            llm_response = await self.query_llm(user_prompt)
 
            # Parse and validate output
            if isinstance(llm_response, BaseModel):
                output = llm_response
            else:
                output = self.parse_json_output(llm_response, TripFeasibilityOutput)

            # Validate percentages sum to 100
            budget_total = sum(output.budget_allocation.values())
            if abs(budget_total - 100) > 1.0:  # Allow small rounding errors
                self.logger.warning(
                    f"Budget allocation percentages sum to {budget_total}%, normalizing"
                )
                # Normalize
                scale = 100.0 / budget_total
                for key in output.budget_allocation:
                    output.budget_allocation[key] *= scale

            return output

        except AgentException:
            raise
        except Exception as e:
            self.logger.error(f"Feasibility assessment failed: {e}")
            raise AgentException(self.name, f"Failed to assess feasibility: {str(e)}", e)

    def _build_user_prompt(self, input_data: UserTravelInput) -> str:
        """
        Build the user prompt for LLM.
        
        Args:
            input_data: User travel input
            
        Returns:
            Formatted prompt for LLM
        """
        return f"""Please assess the feasibility of this trip:

Budget: ${input_data.budget} USD
Trip Duration: {input_data.trip_days} days
Travel Type: {input_data.travel_type}
Source City: {input_data.source_city}
Interests: {", ".join(input_data.interests)}
Hotel Preference: {input_data.hotel_preference}
Transportation Mode: {input_data.transportation}
Travel Month: {input_data.travel_month}
Special Requirements: {input_data.special_requirements or "None"}

Based on typical travel costs, determine:
1. Is this budget adequate for a {input_data.trip_days}-day trip for a {input_data.travel_type} traveler?
2. Calculate the daily budget
3. How should the budget be allocated across accommodation, food, transport, and activities?
4. What's the maximum distance (km) from {input_data.source_city} that could be affordably reached?
5. What are the main budget constraints or concerns?
6. How confident are you in this assessment (0.0-1.0)?"""

    async def fallback_response(self, user_prompt: str, system_prompt: str, output_model: type) -> TripFeasibilityOutput:
        """
        Generate a fallback trip feasibility response when the LLM is unavailable.
        """
        input_data = getattr(self, 'last_input', None)
        if not isinstance(input_data, UserTravelInput):
            raise AgentException(self.name, "Fallback unavailable without valid input")
 
        daily_budget = round(input_data.budget / max(input_data.trip_days, 1), 2)
        allocation = {
            "accommodation": 45.0,
            "food": 25.0,
            "transport": 20.0,
            "activities": 10.0,
        }
        total_distance = min(daily_budget * 50.0, 2500.0)
        warnings = []
        if daily_budget < 50:
            warnings.append("Budget is tight; expect modest accommodations and local experiences.")
        if input_data.trip_days >= 14 and input_data.budget < 1000:
            warnings.append("Longer trips require more flexible planning and low-cost lodging.")
 
        output = TripFeasibilityOutput(
            is_feasible=daily_budget >= 30,
            daily_budget=daily_budget,
            budget_allocation=allocation,
            max_affordable_distance=total_distance,
            warnings=warnings,
            confidence_score=0.72,
            reasoning=(
                f"Based on a {input_data.trip_days}-day trip with a total budget of ${input_data.budget}, "
                f"a sustainable daily budget of ${daily_budget:.2f} is estimated. "
                "Budget allocation follows reasonable percentages for accommodation, food, transport, and activities."
            ),
        )
        return output
 
    def validate_output(self, output: TripFeasibilityOutput) -> bool:
        """
        Validate output feasibility.
         
        Args:
            output: Output to validate
             
        Returns:
            True if output is valid
        """
        # Check that percentages sum to approximately 100
        total = sum(output.budget_allocation.values())
        if total < 95 or total > 105:
            self.logger.warning(f"Budget allocation sum {total}% is outside acceptable range")
            return False
 
        # Check that confidence score is valid
        if not (0 <= output.confidence_score <= 1):
            self.logger.warning("Invalid confidence score")
            return False
 
        return True


# Global Trip Feasibility Agent instance
_trip_feasibility_agent: TripFeasibilityAgent = None


def get_trip_feasibility_agent() -> TripFeasibilityAgent:
    """
    Get or create the global Trip Feasibility Agent instance.
    
    Returns:
        TripFeasibilityAgent instance
    """
    global _trip_feasibility_agent
    if _trip_feasibility_agent is None:
        _trip_feasibility_agent = TripFeasibilityAgent()
    return _trip_feasibility_agent
