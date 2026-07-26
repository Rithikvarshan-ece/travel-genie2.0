"""
TravelGenie LangGraph Workflow

Orchestrates the multi-agent pipeline using LangGraph.
Manages the state and execution flow between agents.

Workflow:
1. User Input → Planner
2. Planner → Trip Feasibility Agent
3. Trip Feasibility → Destination Agent
4. Destination → Schedule Agent
5. Schedule → Validation Agent
6. Validation → Planner
7. Planner → Output

State flow ensures each agent receives outputs from previous agents.
"""

import logging
from typing import TypedDict, Any, Optional, Dict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from backend.models import (
    UserTravelInput,
    TripFeasibilityOutput,
    DestinationOutput,
    ScheduleOutput,
    ValidationOutput,
    FinalTravelPlan,
)
from backend.agents.async_base_agent import AsyncBaseAgent
from backend.agents.trip_feasibility_agent import get_trip_feasibility_agent
from backend.agents.destination_agent import get_destination_agent
from backend.agents.schedule_agent import get_schedule_agent
from backend.agents.validation_agent import get_validation_agent
from backend.config import get_settings

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """
    State object passed between agents in the workflow.
    Contains all intermediate and final results.
    """
    
    # Original user input
    user_input: UserTravelInput
    
    # Agent outputs in sequence
    trip_feasibility: Optional[TripFeasibilityOutput] = None
    destination: Optional[DestinationOutput] = None
    schedule: Optional[ScheduleOutput] = None
    validation: Optional[ValidationOutput] = None
    
    # Workflow control
    revision_count: int = 0
    max_revisions: int = 2
    needs_revision: bool = False
    error_message: Optional[str] = None
    
    # Final result
    final_plan: Optional[FinalTravelPlan] = None


class TravelPlanWorkflow:
    """
    LangGraph-based workflow orchestrator for multi-agent travel planning.
    
    Features:
    - Sequential agent execution
    - State management
    - Error handling and retries
    - Plan revision and repair
    - Comprehensive logging
    """

    def __init__(self):
        """Initialize the workflow."""
        self.settings = get_settings()
        self.logger = logging.getLogger("workflow")
        
        # Get agent instances
        self.trip_feasibility_agent = get_trip_feasibility_agent()
        self.destination_agent = get_destination_agent()
        self.schedule_agent = get_schedule_agent()
        self.validation_agent = get_validation_agent()
        
        # Build the graph
        self.graph = self._build_graph()
        self.logger.info("TravelPlanWorkflow initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(dict)

        # Define nodes
        workflow.add_node("trip_feasibility", self._node_trip_feasibility)
        workflow.add_node("destination", self._node_destination)
        workflow.add_node("schedule", self._node_schedule)
        workflow.add_node("validation", self._node_validation)
        workflow.add_node("finalize", self._node_finalize)

        # Define edges
        workflow.add_edge("trip_feasibility", "destination")
        workflow.add_edge("destination", "schedule")
        workflow.add_edge("schedule", "validation")
        workflow.add_conditional_edges(
            "validation",
            self._should_revise,
            {
                True: "schedule",  # Revise schedule if issues found
                False: "finalize",  # Finalize if no issues
            }
        )
        workflow.add_edge("finalize", END)

        # Set entry point
        workflow.set_entry_point("trip_feasibility")

        # Compile
        return workflow.compile()

    async def _node_trip_feasibility(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Trip Feasibility Agent node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with feasibility assessment
        """
        try:
            self.logger.info("Starting Executing Trip Feasibility Agent")
            
            result = await self.trip_feasibility_agent.invoke(state["user_input"])
            
            state["trip_feasibility"] = result
            self.logger.info("Trip Feasibility completed")
            
        except Exception as e:
            self.logger.error(f"Error Trip Feasibility failed: {e}")
            state["error_message"] = f"Trip Feasibility failed: {str(e)}"
        
        return state

    async def _node_destination(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Destination Agent node - selects best destination using real-time data.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with destination recommendation
        """
        try:
            self.logger.info("Geo Executing Destination Agent")
            
            if not state.get("trip_feasibility"):
                raise ValueError("Trip feasibility required for destination selection")
            
            result = await self.destination_agent.invoke(
                state["user_input"],
                state["trip_feasibility"]
            )
            
            state["destination"] = result
            self.logger.info("Destination selection completed")
            
        except Exception as e:
            self.logger.error(f"Error Destination Agent failed: {e}")
            state["error_message"] = f"Destination selection failed: {str(e)}"
        
        return state

    async def _node_schedule(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Schedule Agent node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with itinerary
        """
        try:
            self.logger.info("📅 Executing Schedule Agent")
            
            if not state.get("destination"):
                raise ValueError("Destination required for schedule generation")
            
            result = await self.schedule_agent.invoke(
                (state["destination"], state["user_input"], state["trip_feasibility"])
            )
            
            state["schedule"] = result
            self.logger.info("Schedule completed")
            
        except Exception as e:
            self.logger.error(f"Error Schedule Agent failed: {e}")
            state["error_message"] = f"Schedule generation failed: {str(e)}"
        
        return state

    async def _node_validation(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Validation Agent node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with validation results
        """
        try:
            self.logger.info("✔️ Executing Validation Agent")
            
            # Prepare inputs for validation
            if not all([
                state.get("user_input"),
                state.get("trip_feasibility"),
                state.get("destination"),
                state.get("schedule"),
            ]):
                raise ValueError("Missing required data for validation")
            
            validation_input = (
                state["user_input"],
                state["trip_feasibility"],
                state["destination"],
                state["schedule"],
            )
            
            result = await self.validation_agent.invoke(validation_input)
            
            state["validation"] = result
            state["needs_revision"] = not result.is_valid
            
            if state["needs_revision"]:
                self.logger.warning(f"Warning Validation found {len(result.issues)} issues")
                for issue in result.issues:
                    self.logger.warning(f"  - [{issue.severity}] {issue.description}")
            else:
                self.logger.info("Validation passed")
            
        except Exception as e:
            self.logger.error(f"Error Validation failed: {e}")
            state["error_message"] = f"Validation failed: {str(e)}"
        
        return state

    async def _node_finalize(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Finalize the travel plan.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final plan
        """
        try:
            self.logger.info("🎯 Finalizing travel plan")
            
            # Create final plan
            final_plan = FinalTravelPlan(
                user_input=state["user_input"],
                trip_feasibility=state["trip_feasibility"],
                destination=state["destination"],
                schedule=state["schedule"],
                validation=state["validation"],
                total_trip_cost=state["schedule"].total_estimated_cost,
                confidence_score=min(
                    state["trip_feasibility"].confidence_score,
                    state["destination"].confidence_score,
                    state["validation"].confidence_score,
                ),
                status="completed" if state["validation"].is_valid else "needs_revision",
            )
            
            state["final_plan"] = final_plan
            self.logger.info("Plan finalized successfully")
            
        except Exception as e:
            self.logger.error(f"Error Finalization failed: {e}")
            state["error_message"] = f"Finalization failed: {str(e)}"
        
        return state

    def _should_revise(self, state: WorkflowState) -> bool:
        """
        Determine if the plan needs revision.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if revision is needed and allowed
        """
        if not state.get("validation"):
            return False
        
        needs_revision = not state["validation"].is_valid
        revision_limit_reached = state.get("revision_count", 0) >= state.get("max_revisions", 2)
        
        if needs_revision and not revision_limit_reached:
            state["revision_count"] = state.get("revision_count", 0) + 1
            self.logger.info(
                f"🔄 Revising plan (attempt {state['revision_count']}/{state.get('max_revisions', 2)})"
            )
            return True
        
        if revision_limit_reached:
            self.logger.warning("Warning Max revision attempts reached")
        
        return False

    async def plan_trip(self, user_input: UserTravelInput) -> FinalTravelPlan:
        """
        Generate a complete travel plan.
        
        Args:
            user_input: User's travel preferences
            
        Returns:
            Complete travel plan
            
        Raises:
            RuntimeError: If plan generation fails
        """
        self.logger.info("Starting travel plan generation")
        
        try:
            # Initialize state
            state: WorkflowState = {
                "user_input": user_input,
                "revision_count": 0,
                "max_revisions": self.settings.max_retries,
            }
            
            # Execute workflow pipeline
            state = await self._node_trip_feasibility(state)
            if state.get("error_message"):
                raise RuntimeError(state["error_message"])
            
            state = await self._node_destination(state)
            if state.get("error_message"):
                raise RuntimeError(state["error_message"])
            
            state = await self._node_schedule(state)
            if state.get("error_message"):
                raise RuntimeError(state["error_message"])
            
            state = await self._node_validation(state)
            if state.get("error_message"):
                raise RuntimeError(state["error_message"])
            
            state = await self._node_finalize(state)
            if state.get("error_message"):
                raise RuntimeError(state["error_message"])
            
            return state["final_plan"]
            
        except Exception as e:
            self.logger.error(f"Error Travel plan generation failed: {e}")
            raise RuntimeError(f"Failed to generate travel plan: {str(e)}")


# Global workflow instance
_workflow: Optional[TravelPlanWorkflow] = None


def get_workflow() -> TravelPlanWorkflow:
    """
    Get or create the global workflow instance.
    
    Returns:
        TravelPlanWorkflow instance
    """
    global _workflow
    if _workflow is None:
        _workflow = TravelPlanWorkflow()
    return _workflow
