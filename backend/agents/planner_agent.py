"""
TravelGenie Planner Agent

Top-level coordinator. Maintains a shared WorkflowContext passed to every
specialist agent. Supports self-correction: if Validation finds critical
issues it triggers a targeted re-run of only the affected stage (max 2
revisions). Emits real-time SSE progress events with estimated time remaining.
"""

import logging
import time
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Optional, List, Dict, Any
from pydantic import BaseModel

from backend.agents.async_base_agent import AsyncBaseAgent, AgentException
from backend.models import (
    UserTravelInput, FinalTravelPlan, PlannerOutput,
    TripFeasibilityOutput, DestinationOutput, ScheduleOutput, ValidationOutput,
)

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[dict], Awaitable[None]]]

# Rough per-agent time estimates (seconds) used for ETA calculation
_AGENT_ETA = {
    "trip_feasibility": 8,
    "destination": 18,
    "route_logistics": 5,
    "schedule": 20,
    "validation": 8,
}


@dataclass
class WorkflowContext:
    """
    Shared memory object passed through the entire pipeline.
    Each agent reads previous outputs from here instead of recalculating.
    """
    user_input: UserTravelInput
    feasibility: Optional[TripFeasibilityOutput] = None
    destination: Optional[DestinationOutput] = None
    route_logistics: Any = None
    schedule: Optional[ScheduleOutput] = None
    validation: Optional[ValidationOutput] = None
    revision_count: int = 0
    agent_metrics: Dict[str, Dict] = field(default_factory=dict)
    why_reasons: List[str] = field(default_factory=list)

    def record_metric(self, agent: str, duration_s: float, apis_used: List[str], confidence: float):
        self.agent_metrics[agent] = {
            "duration_s": round(duration_s, 2),
            "apis_used": apis_used,
            "confidence_pct": round(confidence * 100, 1),
        }


class PlannerAgent(AsyncBaseAgent):
    """
    Top-level coordinator agent.
    Input:  UserTravelInput
    Output: FinalTravelPlan
    """

    MAX_REVISIONS = 2

    def __init__(self):
        super().__init__(
            name="Planner",
            description="Coordinates the full 6-agent travel planning pipeline",
        )
        self._trip_feasibility_agent = None
        self._destination_agent = None
        self._route_logistics_agent = None
        self._schedule_agent = None
        self._validation_agent = None

    def get_system_prompt(self) -> str:
        return "You are the Planner Agent. You coordinate a multi-agent travel planning pipeline."

    async def process(self, input_model: BaseModel) -> FinalTravelPlan:
        if not isinstance(input_model, UserTravelInput):
            raise AgentException(self.name, f"Expected UserTravelInput, got {type(input_model).__name__}")
        return await self._coordinate(input_model)

    async def coordinate_with_progress(
        self,
        user_input: UserTravelInput,
        emit: ProgressCallback,
    ) -> FinalTravelPlan:
        return await self._coordinate(user_input, emit=emit)

    # ------------------------------------------------------------------

    def _get_agents(self):
        if self._trip_feasibility_agent is None:
            from backend.agents.trip_feasibility_agent import get_trip_feasibility_agent
            from backend.agents.destination_agent import get_destination_agent
            from backend.agents.route_logistics_agent import get_route_logistics_agent
            from backend.agents.schedule_agent import get_schedule_agent
            from backend.agents.validation_agent import get_validation_agent
            self._trip_feasibility_agent = get_trip_feasibility_agent()
            self._destination_agent = get_destination_agent()
            self._route_logistics_agent = get_route_logistics_agent()
            self._schedule_agent = get_schedule_agent()
            self._validation_agent = get_validation_agent()

    def _eta(self, completed_agents: List[str]) -> int:
        remaining = [k for k in _AGENT_ETA if k not in completed_agents]
        return sum(_AGENT_ETA[k] for k in remaining)

    async def _coordinate(
        self,
        user_input: UserTravelInput,
        emit: ProgressCallback = None,
    ) -> FinalTravelPlan:
        self._get_agents()
        ctx = WorkflowContext(user_input=user_input)
        steps = []
        t0 = time.time()
        completed: List[str] = []

        async def _e(event: dict):
            if emit:
                event.setdefault("eta_seconds", self._eta(completed))
                await emit(event)

        # ── Planner start ─────────────────────────────────────────────
        await _e({"agent": "planner", "status": "running",
                  "log": "Understanding user request...", "progress": 5})
        await _e({"agent": "planner", "status": "running",
                  "log": f"Planning {user_input.trip_days}-day trip from {user_input.source_city}",
                  "progress": 8})

        # ── Step 1: Trip Feasibility ──────────────────────────────────
        self.logger.info("Planner → Step 1: TripFeasibilityAgent")
        t1 = time.time()
        await _e({"agent": "trip_feasibility", "status": "running",
                  "log": f"Checking budget ${user_input.budget:.0f} for {user_input.trip_days} days...",
                  "progress": 12})
        await _e({"agent": "trip_feasibility", "status": "running",
                  "log": f"Analyzing {user_input.travel_type} travel style...",
                  "progress": 16})

        ctx.feasibility = await self._trip_feasibility_agent.invoke(user_input)
        d1 = round(time.time() - t1, 2)
        ctx.record_metric("trip_feasibility", d1, ["Internal reasoning"], ctx.feasibility.confidence_score)
        completed.append("trip_feasibility")

        await _e({"agent": "trip_feasibility", "status": "completed",
                  "log": f"Trip {'feasible' if ctx.feasibility.is_feasible else 'tight'} — ${ctx.feasibility.daily_budget:.0f}/day",
                  "progress": 20, "duration_s": d1,
                  "confidence_pct": ctx.agent_metrics["trip_feasibility"]["confidence_pct"]})
        steps.append({"step": 1, "name": "Trip Feasibility", "status": "success",
                      "details": ctx.feasibility.reasoning, "duration_s": d1})

        # ── Step 2: Destination (parallel: weather + hotels + attractions) ──
        self.logger.info("Planner → Step 2: DestinationAgent (parallel fetch)")
        t2 = time.time()
        hint = user_input.destination_city or "best match for interests"
        await _e({"agent": "destination", "status": "running",
                  "log": f"Searching destinations for {user_input.travel_type} traveler...",
                  "progress": 24})
        await _e({"agent": "destination", "status": "running",
                  "log": "Fetching live weather, hotels & attractions in parallel...",
                  "progress": 30})
        await _e({"agent": "destination", "status": "running",
                  "log": f"Comparing candidates near {hint}...", "progress": 36})

        # DestinationAgent already runs weather+hotels+attractions concurrently internally
        ctx.destination = await self._destination_agent.invoke((user_input, ctx.feasibility))
        d2 = round(time.time() - t2, 2)
        ctx.record_metric("destination", d2,
                          ["Geo Service", "Weather Service", "Overpass/Places"],
                          ctx.destination.confidence_score)
        completed.append("destination")

        # Build "Why this destination?" reasons
        dest = ctx.destination.destination
        ctx.why_reasons = [
            f"✓ Within ${user_input.budget:.0f} budget (${ctx.feasibility.daily_budget:.0f}/day)",
            f"✓ Weather: {ctx.destination.weather.condition}, {ctx.destination.weather.current_temp:.0f}°C",
            f"✓ {len(ctx.destination.attractions)} attractions matching your interests",
            f"✓ {len(ctx.destination.hotel_options)} hotel options available",
            f"✓ {ctx.destination.travel_distance:.0f} km from {user_input.source_city}",
        ]

        await _e({"agent": "destination", "status": "completed",
                  "log": f"Selected {dest.city}, {dest.country}",
                  "progress": 40, "duration_s": d2,
                  "confidence_pct": ctx.agent_metrics["destination"]["confidence_pct"],
                  "why_reasons": ctx.why_reasons})
        steps.append({"step": 2, "name": "Destination Selection", "status": "success",
                      "details": ctx.destination.reason, "duration_s": d2,
                      "why_reasons": ctx.why_reasons})

        # ── Step 3: Route & Logistics ─────────────────────────────────
        self.logger.info("Planner → Step 3: RouteLogisticsAgent")
        t3 = time.time()
        await _e({"agent": "route_logistics", "status": "running",
                  "log": f"Calculating distance from {user_input.source_city}...",
                  "progress": 44})
        await _e({"agent": "route_logistics", "status": "running",
                  "log": f"Comparing {user_input.transportation} vs alternatives...",
                  "progress": 50})

        ctx.route_logistics = await self._route_logistics_agent.invoke((user_input, ctx.destination))
        d3 = round(time.time() - t3, 2)
        ctx.record_metric("route_logistics", d3, ["Geo Service", "Routing Service"], 0.95)
        completed.append("route_logistics")

        await _e({"agent": "route_logistics", "status": "completed",
                  "log": f"{ctx.route_logistics.travel_distance_km} km — {ctx.route_logistics.travel_time_hours} hrs via {ctx.route_logistics.recommended_mode}",
                  "progress": 55, "duration_s": d3,
                  "confidence_pct": 95})
        steps.append({"step": 3, "name": "Route & Logistics", "status": "success",
                      "details": ctx.route_logistics.routing_notes, "duration_s": d3})

        # ── Step 4: Schedule ──────────────────────────────────────────
        self.logger.info("Planner → Step 4: ScheduleAgent")
        t4 = time.time()
        await _e({"agent": "schedule", "status": "running",
                  "log": f"Building {user_input.trip_days}-day itinerary...", "progress": 58})
        for day_n in range(1, min(user_input.trip_days, 4) + 1):
            await _e({"agent": "schedule", "status": "running",
                      "log": f"Day {day_n} activities planned", "progress": 58 + day_n * 4})

        ctx.schedule = await self._schedule_agent.invoke((ctx.destination, user_input, ctx.feasibility, ctx.route_logistics))
        d4 = round(time.time() - t4, 2)
        ctx.record_metric("schedule", d4, ["Groq LLM"], 0.88)
        completed.append("schedule")

        await _e({"agent": "schedule", "status": "completed",
                  "log": f"{len(ctx.schedule.daily_itinerary)} days scheduled — ${ctx.schedule.total_estimated_cost:.0f} total",
                  "progress": 80, "duration_s": d4, "confidence_pct": 88})
        steps.append({"step": 4, "name": "Schedule Generation", "status": "success",
                      "details": f"Created {len(ctx.schedule.daily_itinerary)} day(s) of itinerary.",
                      "duration_s": d4})

        # ── Step 5: Validation + self-correction loop ─────────────────
        self.logger.info("Planner → Step 5: ValidationAgent")
        t5 = time.time()
        await _e({"agent": "validation", "status": "running",
                  "log": "Verifying budget compliance...", "progress": 83})
        await _e({"agent": "validation", "status": "running",
                  "log": "Checking weather compatibility...", "progress": 88})
        await _e({"agent": "validation", "status": "running",
                  "log": "Confirming hotel availability...", "progress": 92})

        ctx.validation = await self._validation_agent.invoke(
            (user_input, ctx.feasibility, ctx.destination, ctx.route_logistics, ctx.schedule)
        )

        # Self-correction: if critical issues found, re-run only affected stage
        while not ctx.validation.is_valid and ctx.revision_count < self.MAX_REVISIONS:
            ctx.revision_count += 1
            critical = [i for i in ctx.validation.issues if i.severity == "critical"]
            categories = {i.category for i in critical}
            self.logger.warning(f"Validation failed (revision {ctx.revision_count}): {categories}")

            await _e({"agent": "validation", "status": "running",
                      "log": f"Issues found: {', '.join(categories)} — triggering revision {ctx.revision_count}...",
                      "progress": 85})

            if "budget" in categories or "schedule" in categories:
                # Downgrade hotel preference to budget and re-run destination + schedule
                pref = str(user_input.hotel_preference).split(".")[-1].lower()
                if pref in ("luxury", "resort"):
                    from backend.models import HotelCategory
                    user_input = user_input.model_copy(update={"hotel_preference": HotelCategory.BUDGET})
                    ctx.user_input = user_input
                    await _e({"agent": "destination", "status": "running",
                              "log": f"Revision {ctx.revision_count}: Downgrading to budget hotel to fit budget...",
                              "progress": 35})
                    ctx.destination = await self._destination_agent.invoke((user_input, ctx.feasibility))
                    ctx.route_logistics = await self._route_logistics_agent.invoke((user_input, ctx.destination))
                await _e({"agent": "schedule", "status": "running",
                          "log": f"Revision {ctx.revision_count}: Regenerating schedule...",
                          "progress": 70})
                ctx.schedule = await self._schedule_agent.invoke(
                    (ctx.destination, user_input, ctx.feasibility, ctx.route_logistics)
                )
            elif "destination" in categories or "weather" in categories:
                # Re-run destination + route + schedule
                await _e({"agent": "destination", "status": "running",
                          "log": f"Revision {ctx.revision_count}: Re-selecting destination...",
                          "progress": 35})
                ctx.destination = await self._destination_agent.invoke((user_input, ctx.feasibility))
                ctx.route_logistics = await self._route_logistics_agent.invoke((user_input, ctx.destination))
                ctx.schedule = await self._schedule_agent.invoke(
                    (ctx.destination, user_input, ctx.feasibility, ctx.route_logistics)
                )

            await _e({"agent": "validation", "status": "running",
                      "log": "Re-validating revised plan...", "progress": 90})
            ctx.validation = await self._validation_agent.invoke(
                (user_input, ctx.feasibility, ctx.destination, ctx.route_logistics, ctx.schedule)
            )

        d5 = round(time.time() - t5, 2)
        ctx.record_metric("validation", d5, ["Groq LLM"], ctx.validation.confidence_score)
        completed.append("validation")

        await _e({"agent": "validation", "status": "completed",
                  "log": "Travel plan approved" if ctx.validation.is_valid else "Plan flagged — review recommendations",
                  "progress": 96, "duration_s": d5,
                  "confidence_pct": ctx.agent_metrics["validation"]["confidence_pct"]})
        steps.append({"step": 5, "name": "Validation",
                      "status": "success" if ctx.validation.is_valid else "warning",
                      "details": " ".join(ctx.validation.recommendations or ["Plan validated."]),
                      "duration_s": d5})

        # ── Planner summary ───────────────────────────────────────────
        total_time = round(time.time() - t0, 2)
        overall_confidence = round(
            min(ctx.feasibility.confidence_score, ctx.destination.confidence_score,
                ctx.validation.confidence_score), 3
        )

        from backend.utils.cost_calculator import calculate_plan_costs
        cost_summary = calculate_plan_costs(user_input, ctx.destination, ctx.route_logistics, ctx.schedule)

        planner_output = PlannerOutput(
            destination=ctx.destination.destination.city,
            duration=f"{user_input.trip_days} days",
            total_budget=user_input.budget,
            within_budget=cost_summary.within_budget,
            estimated_total_cost=cost_summary.total_cost,
            reasoning_steps=steps,
            coordination_notes=(
                f"Planner coordinated 5 specialist agents in {total_time}s. "
                f"Destination: {ctx.destination.destination.city}. "
                f"Revisions: {ctx.revision_count}. "
                f"Plan is {'valid' if ctx.validation.is_valid else 'flagged for review'}."
            ),
            confidence_score=overall_confidence,
        )

        final_plan = FinalTravelPlan(
            user_input=user_input,
            planner=planner_output,
            trip_feasibility=ctx.feasibility,
            destination=ctx.destination,
            route_logistics=ctx.route_logistics,
            schedule=ctx.schedule,
            validation=ctx.validation,
            total_trip_cost=cost_summary.total_cost,
            confidence_score=overall_confidence,
            status="completed" if ctx.validation.is_valid else "needs_revision",
        )
        # Attach extra metadata for the API response
        final_plan._agent_metrics = ctx.agent_metrics
        final_plan._why_reasons = ctx.why_reasons
        final_plan._total_time = total_time

        await _e({"agent": "planner", "status": "completed",
                  "log": f"All agents done — {ctx.destination.destination.city} plan ready",
                  "progress": 100, "eta_seconds": 0,
                  "agent_metrics": ctx.agent_metrics,
                  "total_time_s": total_time})

        self.logger.info(
            f"Planner completed in {total_time}s — "
            f"{ctx.destination.destination.city}, confidence={overall_confidence}"
        )
        return final_plan


# ── Singleton ─────────────────────────────────────────────────────────

_planner_agent: PlannerAgent = None


def get_planner_agent() -> PlannerAgent:
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = PlannerAgent()
    return _planner_agent
