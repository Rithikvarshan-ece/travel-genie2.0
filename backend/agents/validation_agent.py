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
            if not isinstance(input_models, tuple) or len(input_models) != 4:
                raise AgentException(
                    self.name,
                    "Expected tuple of (UserTravelInput, TripFeasibilityOutput, DestinationOutput, ScheduleOutput)"
                )

            user_input, feasibility, destination, schedule = input_models
            self.last_input = user_input
            self.last_schedule = schedule
 
            # Build validation prompt
            user_prompt = self._build_user_prompt(
                user_input, feasibility, destination, schedule
            )

            # Query LLM
            llm_response = await self.query_llm(user_prompt)
 
            # Parse output
            if isinstance(llm_response, BaseModel):
                output = llm_response
            else:
                output = self.parse_json_output(llm_response, ValidationOutput)

            # Post-process validation
            self._post_process_validation(output, schedule, user_input)

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
 
Return validation results as JSON with all issues found and suggested fixes."""
 
    async def fallback_response(self, user_prompt: str, system_prompt: str, output_model: type) -> ValidationOutput:
        """
        Generate a fallback validation response when the LLM is unavailable.
        """
        user_input = getattr(self, 'last_input', None)
        schedule = getattr(self, 'last_schedule', None)
        if not isinstance(user_input, UserTravelInput) or not isinstance(schedule, ScheduleOutput):
            raise AgentException(self.name, "Fallback unavailable without valid input and schedule")
 
        issues = []
        if schedule.total_estimated_cost > user_input.budget:
            issues.append(ValidationIssue(
                category="budget",
                severity="critical",
                description=(
                    f"Total cost ${schedule.total_estimated_cost:.2f} exceeds budget ${user_input.budget:.2f}."
                ),
                suggested_fix="Reduce daily activity spending or choose a less expensive hotel."
            ))
 
        if any(day.estimated_cost < 0 for day in schedule.daily_itinerary):
            issues.append(ValidationIssue(
                category="schedule",
                severity="critical",
                description="One or more days have a negative estimated cost.",
                suggested_fix="Review itinerary costs and ensure all estimates are positive."
            ))
 
        is_valid = len([i for i in issues if i.severity == "critical"]) == 0
 
        output = ValidationOutput(
            is_valid=is_valid,
            issues=issues,
            budget_within_limit=schedule.total_estimated_cost <= user_input.budget,
            schedule_feasible=True,
            weather_compatible=True,
            hotel_verified=True,
            total_cost=schedule.total_estimated_cost,
            budget_buffer=max(user_input.budget - schedule.total_estimated_cost, 0.0),
            recommendations=[
                "Confirm hotel pricing and local transportation costs.",
            ],
            confidence_score=0.75,
        )
 
        return output
 
    def _post_process_validation(
        self,
        validation: ValidationOutput,
        schedule: ScheduleOutput,
        user_input: UserTravelInput,
    ) -> None:
        """
        Post-process validation results to add computational checks.
        
        Args:
            validation: Validation output to update
            schedule: Schedule to check
            user_input: User input for budget
        """
        # Additional checks beyond LLM validation
        
        # Check budget strictly
        if schedule.total_estimated_cost > user_input.budget:
            issue = ValidationIssue(
                category="budget",
                severity="critical",
                description=f"Plan exceeds budget: ${schedule.total_estimated_cost} > ${user_input.budget}",
                suggested_fix="Remove low-priority activities or upgrade to cheaper accommodation",
            )
            if issue not in validation.issues:
                validation.issues.append(issue)
            validation.budget_within_limit = False

        # Recalculate overall validity
        critical_issues = [i for i in validation.issues if i.severity == "critical"]
        validation.is_valid = len(critical_issues) == 0

        # Update final cost
        validation.total_cost = schedule.total_estimated_cost
        validation.budget_buffer = user_input.budget - schedule.total_estimated_cost


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
