"""
TravelGenie Workflow

Thin orchestration layer that delegates to PlannerAgent.

The PlannerAgent is the real coordinator — it runs all 5 specialist agents
in sequence and returns a FinalTravelPlan.

Workflow (owned by PlannerAgent):
  UserInput → PlannerAgent
                ↓ TripFeasibilityAgent
                ↓ DestinationAgent
                ↓ RouteLogisticsAgent
                ↓ ScheduleAgent
                ↓ ValidationAgent
              PlannerAgent → FinalTravelPlan
"""

import logging
from typing import Optional

from backend.models import UserTravelInput, FinalTravelPlan
from backend.agents.planner_agent import get_planner_agent
from backend.config import get_settings

logger = logging.getLogger(__name__)


class TravelPlanWorkflow:
    """
    Workflow entry point.  Delegates entirely to PlannerAgent.
    """

    def __init__(self):
        self.settings = get_settings()
        self.planner_agent = get_planner_agent()
        logger.info("TravelPlanWorkflow initialised — using PlannerAgent as coordinator")

    async def plan_trip(self, user_input: UserTravelInput) -> FinalTravelPlan:
        """
        Generate a complete travel plan via PlannerAgent.

        Args:
            user_input: User's travel preferences

        Returns:
            FinalTravelPlan with all agent outputs

        Raises:
            RuntimeError: If plan generation fails
        """
        logger.info(f"Workflow: starting plan for {user_input.source_city}")
        try:
            final_plan: FinalTravelPlan = await self.planner_agent.invoke(user_input)
            logger.info("Workflow: plan completed successfully")
            return final_plan
        except Exception as e:
            logger.error(f"Workflow: plan generation failed: {e}")
            raise RuntimeError(f"Failed to generate travel plan: {str(e)}")


# ── Singleton ─────────────────────────────────────────────────────────

_workflow: Optional[TravelPlanWorkflow] = None


def get_workflow() -> TravelPlanWorkflow:
    """Get or create the global workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = TravelPlanWorkflow()
    return _workflow
