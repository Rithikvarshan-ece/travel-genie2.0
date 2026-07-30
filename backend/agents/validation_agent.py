"""
TravelGenie Validation Agent

Validates and repairs travel plans for consistency and feasibility.

Responsibilities:
- Verify budget compliance
- Check schedule feasibility (travel times, opening hours)
- Validate weather compatibility
- Ensure hotel information is correct
- Auto-repair invalid plans
- Return validated plan or repair suggestions
"""

import json
import logging
from typing import List, Dict, Any
from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import (
    ScheduleOutput,
    ValidationOutput,
    ValidationIssue,
    FinalTravelPlan,
    UserTravelInput,
    TripFeasibilityOutput,
    DestinationOutput,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ValidationAgent(AsyncBaseAgent):
    """
    Validates the complete travel plan for consistency and feasibility.
    
    Input: (UserTravelInput, TripFeasibilityOutput, DestinationOutput, ScheduleOutput)
    Output: ValidationOutput
    
    This agent checks all constraints and automatically repairs issues when possible.
    """

    def __init__(self):
        """Initialize Validation Agent."""
        super().__init__(
            name="Validation",
            description="Validates and repairs travel plans"
        )

    def get_system_prompt(self) -> str:
        """
        Get system prompt for plan validation.
        
        Returns:
            System prompt for LLM
        """
        return """You are an expert travel plan validator and optimizer. Your task is to review a complete travel plan and identify any issues.

VALIDATION CHECKLIST:
1. BUDGET: Does the plan fit within the budget?
   - Sum all costs (accommodation + food + transport + activities)
   - Compare to total budget
   - Flag if over budget
   
2. SCHEDULE: Is the schedule realistic?
   - Check that travel times are respected
   - Verify no overlapping activities
   - Confirm adequate rest time
   - Check museum/attraction opening hours if known
   
3. WEATHER: Are activities suitable for weather?
   - Don't recommend beach in heavy rain
   - Check temperature ranges
   - Suggest alternatives if incompatible
   
4. TRANSPORTATION: Are transport methods realistic?
   - Flight times must match schedule
   - Local transport must be available
   
5. HOTEL: Is the hotel consistently referenced?
   - Check check-in/check-out times
   - Verify hotel name matches throughout

ISSUE SEVERITY:
- critical: Plan cannot proceed (missing data, impossible schedule)
- warning: Plan is suboptimal (slight budget overrun, long waits)
- info: Useful tips (bring umbrella, book ahead)

REPAIRS:
If issues can be fixed by reasonable adjustments, suggest them.
Examples: Remove low-priority activity, adjust meal budget, swap activities

IMPORTANT:
- Return ONLY valid JSON
- Be realistic and practical
- Don't hallucinate data
- Focus on feasibility
- Every issue must have a suggested fix if possible"""

    async def process(self, input_models: tuple) -> ValidationOutput:
        """
        Validate the travel plan.
        
        Args:
            input_models: Tuple of (UserTravelInput, TripFeasibilityOutput, 
                                    DestinationOutput, ScheduleOutput)
            
        Returns:
            ValidationOutput with validation results
            
        Raises:
            AgentException: If validation fails
        """
        try:
            # Extract inputs
            route_logistics = None
            if isinstance(input_models, tuple):
                if len(input_models) == 5:
                    user_input, feasibility, destination, route_logistics, schedule = input_models
                elif len(input_models) == 4:
                    user_input, feasibility, destination, schedule = input_models
                else:
                    raise AgentException(
                        self.name,
                        f"Expected tuple of 4 or 5 elements, got {len(input_models)}"
                    )
            else:
                raise AgentException(self.name, "Expected tuple input")

            self.last_input = user_input
            self.last_schedule = schedule
            self.last_destination = destination
            self.last_route_logistics = route_logistics

            # Build validation prompt
            user_prompt = self._build_user_prompt(
                user_input, feasibility, destination, schedule
            )

            # Query LLM
            llm_response = await self.query_llm(
                user_prompt=user_prompt,
                system_prompt=self.get_system_prompt(),
                output_model=ValidationOutput,
            )

            # Parse output
            if isinstance(llm_response, BaseModel):
                output = llm_response
            else:
                output = self.parse_json_output(llm_response, ValidationOutput)

            # Post-process validation — always uses actual costs via single source of truth calculator
            self._post_process_validation(output, schedule, user_input, destination, route_logistics)

            return output

        except AgentException:
            raise
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            raise AgentException(self.name, f"Failed to validate plan: {str(e)}", e)

    def _build_user_prompt(
        self,
        user_input: UserTravelInput,
        feasibility: TripFeasibilityOutput,
        destination: DestinationOutput,
        schedule: ScheduleOutput,
    ) -> str:
        """
        Build validation prompt.
        
        Args:
            user_input: Original user input
            feasibility: Feasibility assessment
            destination: Selected destination
            schedule: Generated schedule
            
        Returns:
            Formatted prompt for LLM
        """
        return f"""Validate this complete travel plan:
 
USER REQUIREMENTS:
- Budget: ${user_input.budget} USD
- Duration: {user_input.trip_days} days
- Travel type: {user_input.travel_type}
- Interests: {', '.join(user_input.interests)}
 
BUDGET ALLOCATION:
- Daily budget: ${feasibility.daily_budget}
- Accommodation: {feasibility.budget_allocation.get('accommodation', 0)}%
- Food: {feasibility.budget_allocation.get('food', 0)}%
- Transport: {feasibility.budget_allocation.get('transport', 0)}%
- Activities: {feasibility.budget_allocation.get('activities', 0)}%
 
DESTINATION:
- City: {destination.destination.city}, {destination.destination.country}
- Hotel: {destination.selected_hotel.name} (${destination.selected_hotel.price_per_night}/night)
- Weather: {destination.weather.condition}, {destination.weather.current_temp}°C
- Rain probability: {destination.weather.rain_probability * 100}%
 
PLANNED SCHEDULE:
{json.dumps(schedule.model_dump(), default=str, indent=2)}
 
TOTAL PLANNED COSTS:
- Accommodation: ${schedule.accommodation_cost}
- Food: ${schedule.food_cost}
- Transport: ${schedule.transport_cost}
- Activities: ${schedule.activities_cost}
- TOTAL: ${schedule.total_estimated_cost}
 
VALIDATION TASKS:
1. Check if total cost (${schedule.total_estimated_cost}) <= budget (${user_input.budget})
2. Verify schedule is realistic (no overlapping activities, adequate rest)
3. Check weather compatibility for activities
4. Verify hotel check-in/out times align with schedule
5. Ensure transportation is feasible
6. Identify any unrealistic assumptions
 
Return validation results as a flat JSON object. The JSON must have these fields at the root level:
- is_valid (boolean): whether the plan is valid overall
- issues (array): list of issues, each with category (string), severity ("critical"|"warning"|"info"), description (string), suggested_fix (string or null)
- budget_within_limit (boolean)
- schedule_feasible (boolean)
- weather_compatible (boolean)
- hotel_verified (boolean)
- total_cost (number)
- budget_buffer (number)
- recommendations (array of strings)
- confidence_score (number between 0 and 1)

Do NOT wrap the output in a key like "validation_results" or "validation" — return the raw object directly.
Example:
{{
  "is_valid": true,
  "issues": [{{"category": "budget", "severity": "warning", "description": "Slightly tight budget", "suggested_fix": "Consider budget hotel"}}],
  "budget_within_limit": true,
  "schedule_feasible": true,
  "weather_compatible": true,
  "hotel_verified": true,
  "total_cost": 2450.00,
  "budget_buffer": 550.00,
  "recommendations": ["Book early"],
  "confidence_score": 0.90
}}"""
 
    async def fallback_response(self, user_prompt: str, system_prompt: str, output_model: type) -> ValidationOutput:
        """Fallback validation using actual hotel cost from destination."""
        user_input = getattr(self, 'last_input', None)
        schedule = getattr(self, 'last_schedule', None)
        destination = getattr(self, 'last_destination', None)
        if not isinstance(user_input, UserTravelInput) or not isinstance(schedule, ScheduleOutput):
            raise AgentException(self.name, "Fallback unavailable without valid input and schedule")

        issues = []
        # Use actual hotel cost
        days = max(user_input.trip_days, 1)
        hotel_cost = destination.selected_hotel.price_per_night * days if destination else schedule.accommodation_cost
        actual_total = round(hotel_cost + schedule.transport_cost + schedule.food_cost + schedule.activities_cost, 2)

        if actual_total > user_input.budget:
            exceeded = round(actual_total - user_input.budget, 2)
            issues.append(ValidationIssue(
                category="budget",
                severity="critical",
                description=f"Actual cost ${actual_total:.2f} exceeds budget ${user_input.budget:.2f} by ${exceeded:.2f}.",
                suggested_fix="Choose a less expensive hotel or increase your budget."
            ))

        if any(day.estimated_cost < 0 for day in schedule.daily_itinerary):
            issues.append(ValidationIssue(
                category="schedule", severity="critical",
                description="One or more days have a negative estimated cost.",
                suggested_fix="Review itinerary costs."
            ))

        is_valid = not any(i.severity == "critical" for i in issues)
        return ValidationOutput(
            is_valid=is_valid,
            issues=issues,
            budget_within_limit=actual_total <= user_input.budget,
            schedule_feasible=True,
            weather_compatible=True,
            hotel_verified=True,
            total_cost=actual_total,
            budget_buffer=round(user_input.budget - actual_total, 2),
            recommendations=["Confirm hotel pricing and local transportation costs."],
            confidence_score=0.80,
        )
 
    def _post_process_validation(
        self,
        validation: ValidationOutput,
        schedule: ScheduleOutput,
        user_input: UserTravelInput,
        destination: DestinationOutput = None,
        route_logistics = None,
    ) -> None:
        """
        Recompute actual trip cost from real selected components using central cost calculator.
        Never trusts the LLM's total_estimated_cost — always recalculates from single source of truth.
        """
        days = max(user_input.trip_days, 1)

        from backend.utils.cost_calculator import calculate_plan_costs
        summary = calculate_plan_costs(user_input, destination, route_logistics, schedule)

        actual_total = summary.total_cost
        actual_hotel_cost = summary.hotel_cost
        actual_transport = summary.transport_cost

        # Sync schedule costs to match central calculation
        schedule.accommodation_cost = summary.hotel_cost
        schedule.transport_cost = summary.transport_cost
        schedule.food_cost = summary.food_cost
        schedule.activities_cost = summary.activities_cost
        schedule.total_estimated_cost = summary.total_cost

        over_budget = not summary.within_budget
        exceeded_by = round(actual_total - user_input.budget, 2) if over_budget else 0.0

        if over_budget:
            inr_exceeded = round(exceeded_by * 83)
            inr_total = round(actual_total * 83)
            inr_budget = round(user_input.budget * 83)
            hotel_name = destination.selected_hotel.name if destination and destination.selected_hotel else "Hotel"
            issue = ValidationIssue(
                category="budget",
                severity="critical",
                description=(
                    f"Actual total cost INR {inr_total:,} exceeds budget INR {inr_budget:,} "
                    f"by INR {inr_exceeded:,}. "
                    f"{hotel_name} costs INR {round(actual_hotel_cost*83):,} ({days} nights) "
                    f"and Transport costs INR {round(actual_transport*83):,}."
                ),
                suggested_fix=(
                    f"Switch to a cheaper transport mode (e.g. train/bus) or budget hotel to fit budget INR {inr_budget:,}."
                ),
            )
            # Avoid duplicate issues
            existing_cats = {i.category for i in validation.issues if i.severity == "critical"}
            if "budget" not in existing_cats:
                validation.issues.append(issue)
            validation.budget_within_limit = False
        else:
            validation.budget_within_limit = True

        # Recalculate overall validity from critical issues
        critical_issues = [i for i in validation.issues if i.severity == "critical"]
        validation.is_valid = len(critical_issues) == 0

        # Update final cost fields
        validation.total_cost = summary.total_cost
        validation.budget_buffer = summary.remaining_budget


# Global Validation Agent instance
_validation_agent: ValidationAgent = None


def get_validation_agent() -> ValidationAgent:
    """
    Get or create the global Validation Agent instance.
    
    Returns:
        ValidationAgent instance
    """
    global _validation_agent
    if _validation_agent is None:
        _validation_agent = ValidationAgent()
    return _validation_agent
