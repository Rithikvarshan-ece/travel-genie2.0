"""
TravelGenie Multi-Agent Orchestrator
Coordinates all AI agents in a pipeline to generate comprehensive travel plans.
"""

from typing import Any, Dict
import time
import logging

from backend.agents.base_agent import AgentContext
from backend.agents.planner_agent import PlannerAgent
from backend.agents.budget_agent import BudgetAgent
from backend.agents.destination_agent import DestinationAgent
from backend.agents.weather_agent import WeatherAgent
from backend.agents.transport_agent import TransportAgent
from backend.agents.hotel_agent import HotelAgent
from backend.agents.attraction_agent import AttractionAgent
from backend.agents.itinerary_agent import ItineraryAgent
from backend.agents.expense_agent import ExpenseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TravelPlanOrchestrator:
    """
    Orchestrates the multi-agent pipeline for travel planning.
    
    Pipeline:
    1. User Input → Planner Agent (coordinator)
    2. Budget Agent → calculates budget breakdown
    3. Destination Agent → suggests destinations
    4. Weather Agent → checks weather
    5. Transport Agent → recommends transport
    6. Hotel Agent → suggests hotels
    7. Attraction Agent → generates attractions
    8. Itinerary Agent → creates daily plan
    9. Expense Agent → calculates costs
    10. Planner Agent → final recommendation
    """

    def __init__(self):
        """Initialize all agents."""
        logger.info("🤖 Initializing TravelGenie Multi-Agent System...")
        
        self.agents = {
            "planner": PlannerAgent(),
            "budget": BudgetAgent(),
            "destination": DestinationAgent(),
            "weather": WeatherAgent(),
            "transport": TransportAgent(),
            "hotel": HotelAgent(),
            "attraction": AttractionAgent(),
            "itinerary": ItineraryAgent(),
            "expense": ExpenseAgent(),
        }
        
        logger.info(f"Initialized {len(self.agents)} agents")

    def generate_plan(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete travel plan by running all agents in pipeline.
        
        Args:
            user_input: Dictionary with user's travel preferences
            
        Returns:
            Complete travel plan with all agent outputs
        """
        start_time = time.time()
        logger.info("Starting travel plan generation...")
        
        # Initialize context
        context = AgentContext(user_input)
        agent_times = {}
        
        # Pipeline execution with timing
        pipeline_steps = [
            ("budget", self.agents["budget"]),
            ("destination", self.agents["destination"]),
            ("weather", self.agents["weather"]),
            ("transport", self.agents["transport"]),
            ("hotel", self.agents["hotel"]),
            ("attraction", self.agents["attraction"]),
            ("itinerary", self.agents["itinerary"]),
            ("expense", self.agents["expense"]),
        ]

        for step_name, agent in pipeline_steps:
            step_start = time.time()
            logger.info(f"  ⚙️ Running {agent.name}...")
            
            try:
                # Agent processes the context
                result = agent.process(context.to_dict())
                context.set(step_name, result)
                
                elapsed = time.time() - step_start
                agent_times[step_name] = round(elapsed, 2)
                logger.info(f"  Success {agent.name} completed in {elapsed:.2f}s")
                
            except Exception as e:
                elapsed = time.time() - step_start
                logger.error(f"  Error {agent.name} failed after {elapsed:.2f}s: {str(e)}")
                context.add_error(f"{agent.name} error: {str(e)}")
                agent_times[step_name] = round(elapsed, 2)
                context.set(step_name, {"status": "error", "error": str(e)})

        # Final step: Planner Agent merges all outputs
        logger.info("  ⚙️ Running Planner Agent (final merge)...")
        try:
            planner_result = self.agents["planner"].process(context.to_dict())
            context.set("planner", planner_result)
            logger.info("  Success Planner Agent completed")
        except Exception as e:
            logger.error(f"  Error Planner Agent failed: {str(e)}")
            context.add_error(f"Planner Agent error: {str(e)}")

        total_time = time.time() - start_time
        logger.info(f"🎉 Travel plan generated in {total_time:.2f}s")
        
        # Build final response
        final_plan = {
            "plan_id": int(time.time()),
            "generation_time_seconds": round(total_time, 2),
            "agent_performance": agent_times,
            "user_input": user_input,
            "agents": {
                "planner": context.get("planner", {}),
                "budget": context.get("budget", {}),
                "destination": context.get("destination", {}),
                "weather": context.get("weather", {}),
                "transport": context.get("transport", {}),
                "hotel": context.get("hotel", {}),
                "attraction": context.get("attraction", {}),
                "itinerary": context.get("itinerary", {}),
                "expense": context.get("expense", {}),
            },
            "errors": context.get("errors", []),
            "warnings": context.get("warnings", []),
            "status": "completed" if not context.get("errors") else "completed_with_errors"
        }
        
        return final_plan

    def get_agent_info(self) -> list:
        """Get information about all available agents."""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "key": key
            }
            for key, agent in self.agents.items()
        ]


# Singleton instance
orchestrator = TravelPlanOrchestrator()

