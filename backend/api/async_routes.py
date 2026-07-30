"""
TravelGenie Async API Routes

Refactored API endpoints using async/await and the new agent system.
All endpoints are async and use real-time data services.
"""

import logging
import time
import json
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.models import UserTravelInput, FinalTravelPlan
from backend.agents.route_logistics_agent import RouteLogisticsOutput
from backend.workflow import get_workflow
from backend.database.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["TravelGenie API v2"])


# ===== Request/Response Models =====

class TravelPlanRequest(BaseModel):
    """Request model for travel plan generation."""
    budget: float = Field(..., gt=0, description="Total trip budget in INR")
    source_city: str = Field(..., min_length=2, description="Departure city")
    destination_city: Optional[str] = Field(None, description="Desired destination city (optional)")
    trip_days: int = Field(..., ge=1, le=30, description="Number of days")
    travel_type: str = Field(..., pattern="^(solo|family|couple|friends)$")
    transportation: str = Field(..., pattern="^(flight|train|bus|car)$")
    interests: List[str] = Field(..., min_items=1)
    hotel_preference: str = Field(..., pattern="^(budget|luxury|hostel|resort)$")
    travel_month: str = Field(..., min_length=2)
    special_requirements: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "budget": 3000,
                "source_city": "New York",
                "trip_days": 7,
                "travel_type": "couple",
                "transportation": "flight",
                "interests": ["beaches", "food", "culture"],
                "hotel_preference": "resort",
                "travel_month": "July",
            }
        }


class TravelPlanResponse(BaseModel):
    """Response model for travel plans."""
    status: str = Field(..., description="Status: success or error")
    plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generation_time_seconds: float = Field(..., description="Time taken to generate plan")
    message: str = Field(..., description="Human-readable message")


def _round(value: float, precision: int = 2) -> float:
    return round(value, precision)


def _money(value: float) -> float:
    return round(value, 2)


def _format_transport_option(mode: str, travel_time_hours: float, distance_km: float, budget: float, travelers: int) -> Dict[str, Any]:
    mode_lower = mode.lower()
    cost_multiplier = {
        'flight': 0.2,
        'train': 0.12,
        'bus': 0.08,
        'car': 0.15,
    }.get(mode_lower, 0.1)
    total_cost = max(20.0, distance_km * cost_multiplier)
    cost_per_person = total_cost / max(travelers, 1)
    score = max(5.0, min(10.0, 10.0 - travel_time_hours * 0.5))
    co2 = round(distance_km * ({'flight': 0.24, 'train': 0.06, 'bus': 0.1, 'car': 0.18}.get(mode_lower, 0.15)), 1)
    display = f"{travel_time_hours:.1f} hrs"
    emoji = {
        'flight': '✈️',
        'train': '🚆',
        'bus': '🚌',
        'car': '🚗',
    }.get(mode_lower, '🚗')

    pros = [
        f"Good balance of cost and speed for {mode_lower}",
        "Suitable for most travelers",
    ]
    cons = [
        f"May not be the fastest option compared to flight" if mode_lower != 'flight' else "Higher carbon footprint",
    ]

    return {
        'mode': mode_lower,
        'mode_emoji': emoji,
        'travel_time_hours': _round(travel_time_hours, 1),
        'travel_time_display': display,
        'total_cost': _money(total_cost),
        'cost_per_person': _money(cost_per_person),
        'overall_score': _round(score, 1),
        'co2_emissions_kg': co2,
        'pros': pros,
        'cons': cons,
    }


def _map_final_plan_to_frontend_plan(final_plan: FinalTravelPlan, generation_time: float) -> Dict[str, Any]:
    user_input = final_plan.user_input
    feasibility = final_plan.trip_feasibility
    destination = final_plan.destination
    schedule = final_plan.schedule
    validation = final_plan.validation
    planner = final_plan.planner  # real PlannerOutput from PlannerAgent

    from backend.utils.cost_calculator import calculate_plan_costs

    cost_summary = calculate_plan_costs(
        user_input,
        destination,
        getattr(final_plan, 'route_logistics', None),
        schedule
    )

    total_budget = cost_summary.user_budget
    total_cost = cost_summary.total_cost
    remaining_budget = cost_summary.remaining_budget
    budget_utilization = cost_summary.utilization_pct
    within_budget = cost_summary.within_budget
    budget_level = 'Comfortable' if within_budget else 'Tight'
    weather = destination.weather

    hotel_options = []
    for hotel in destination.hotel_options:
        hotel_options.append({
            'name': hotel.name,
            'destination': destination.destination.city,
            'category': hotel.category,
            'price_per_night': hotel.price_per_night,
            'rating': hotel.rating,
            'reviews': hotel.reviews_count,
            'amenities': hotel.amenities,
            'latitude': hotel.location.latitude,
            'longitude': hotel.location.longitude,
            'distance_from_center': _round(getattr(hotel, 'distance_from_city_center', 1.5) or 1.5, 1),
            'description': hotel.description or f"Comfortable {hotel.category} stay near the city center.",
            'score': _round(hotel.rating * 2, 1),
            'value_rating': 'Great value' if hotel.rating >= 4 else 'Good choice',
            'recommended_for': user_input.travel_type,
        })

    sh = destination.selected_hotel
    selected_hotel = {
        'name': sh.name,
        'destination': destination.destination.city,
        'category': sh.category,
        'price_per_night': sh.price_per_night,
        'rating': sh.rating,
        'reviews': sh.reviews_count,
        'amenities': sh.amenities,
        'latitude': sh.location.latitude,
        'longitude': sh.location.longitude,
        'distance_from_center': _round(getattr(sh, 'distance_from_city_center', 1.5) or 1.5, 1),
        'description': sh.description or f"Recommended stay in {destination.destination.city}.",
        'score': _round(sh.rating * 2, 1),
        'value_rating': 'Best value' if sh.rating >= 4 else 'Recommended',
        'recommended_for': user_input.travel_type,
    }

    weather_forecast = [
        {
            'day': i + 1,
            'date': schedule.start_date or '',
            'day_name': f'Day {i + 1}',
            'condition': weather.condition,
            'temperature_c': _round(weather.current_temp),
            'temperature_f': _round(weather.current_temp * 9 / 5 + 32),
            'humidity': _round(weather.humidity * 100, 0),
            'wind_speed_kmh': weather.wind_speed,
            'precipitation_chance': _round(weather.rain_probability * 100, 0),
            'icon': 'sun',
            'recommendation': 'Pack for mild weather and carry a light jacket.' if weather.rain_probability < 0.5 else 'Expect showers; carry an umbrella.',
        }
        for i in range(min(user_input.trip_days, 5))
    ]

    transport_options = []
    if final_plan.route_logistics and final_plan.route_logistics.transport_options:
        rl = final_plan.route_logistics
        transport_options = [o.model_dump() for o in rl.transport_options]
    else:
        # Fallback: build from destination data if route_logistics missing
        transport_options = [
            _format_transport_option(user_input.transportation, destination.travel_time_hours or max(1.0, destination.travel_distance / 800.0), destination.travel_distance or 1000.0, total_budget, 2),
        ]
        for fallback_mode in ['train', 'bus', 'car']:
            if fallback_mode != user_input.transportation:
                transport_options.append(_format_transport_option(fallback_mode, destination.travel_time_hours + 2.0, destination.travel_distance or 1000.0, total_budget, 2))

    itinerary_days = []
    for day in schedule.daily_itinerary:
        slots = []
        for activity in day.activities:
            time_label = activity.get('time') or '09:00'
            hour = int(time_label.split(':')[0]) if isinstance(time_label, str) and ':' in time_label else 9
            slot_key = 'morning' if hour < 12 else 'afternoon' if hour < 18 else 'evening'
            slots.append({
                'slot': slot_key,
                'icon': '☀️',
                'label': slot_key,
                'hours': time_label,
                'activities': [
                    {
                        'activity': activity.get('activity', ''),
                        'icon': '⭐',
                        'description': activity.get('activity', ''),
                        'duration': f"{activity.get('duration_minutes', 0)} min",
                        'cost': f"{activity.get('cost_usd', 0):.0f}",
                    }
                ],
                'weather_note': None,
            })

        itinerary_days.append({
            'day': day.day_number,
            'title': day.title,
            'date': day.date or '',
            'weather': {
                'condition': weather.condition,
                'temperature_c': _round(weather.current_temp),
                'humidity': _round(weather.humidity * 100, 0),
                'wind_speed_kmh': weather.wind_speed,
            },
            'hotel': destination.selected_hotel.name,
            'slots': slots,
            'daily_cost_estimate': _money(day.estimated_cost),
            'highlights': [a.name for a in destination.attractions[:3]],
        })

    attraction_data = [
        {
            'name': attraction.name,
            'type': attraction.category,
            'duration': f"{_round(attraction.visit_duration_hours, 1)} hrs",
            'cost': f"{_round(attraction.entry_fee, 0)}",
            'description': attraction.description or '',
            'best_time': 'Morning',
            'tips': 'Arrive early to avoid crowds.',
            'time': None,
        }
        for attraction in destination.attractions
    ]

    daily_breakdown = [
        {
            'day': day.day_number,
            'theme': day.title,
            'attractions': [act.get('name', '') for act in day.activities if isinstance(act, dict)] or [destination.attractions[0].name if destination.attractions else 'Local sightseeing'],
        }
        for day in schedule.daily_itinerary
    ]

    return {
        'plan_id': final_plan.trip_id or 0,
        'generation_time_seconds': _round(generation_time, 2),
        'agent_performance': getattr(final_plan, '_agent_metrics', {}),
        'why_reasons': getattr(final_plan, '_why_reasons', []),
        'total_time_s': getattr(final_plan, '_total_time', generation_time),
        'user_input': user_input.model_dump(),
        'agents': {
            'planner': {
                'final_recommendation': {
                    'summary': {
                        'destination': planner.destination if planner else destination.destination.city,
                        'duration': planner.duration if planner else f"{user_input.trip_days} days",
                        'total_budget': total_budget,
                        'within_budget': within_budget,
                        'estimated_total_cost': total_cost,
                    },
                },
                'reasoning_steps': planner.reasoning_steps if planner else [],
                'coordination_notes': planner.coordination_notes if planner else '',
                'confidence_score': planner.confidence_score if planner else validation.confidence_score,
            },
            'trip_feasibility': {
                'is_feasible': feasibility.is_feasible,
                'daily_budget': {
                    'per_day_total': _money(feasibility.daily_budget),
                    'per_person_per_day': _money(feasibility.daily_budget / max(user_input.trip_days, 1)),
                },
                'budget_allocation': feasibility.budget_allocation,
                'max_affordable_distance': feasibility.max_affordable_distance,
                'warnings': feasibility.warnings,
                'confidence_score': feasibility.confidence_score,
                'reasoning': feasibility.reasoning,
                'budget_level': budget_level,
                'total_budget': total_budget,
                'breakdown': {
                    'hotel': {
                        'amount': _money(cost_summary.hotel_cost),
                        'percentage': cost_summary.hotel_pct,
                        'description': 'Accommodation (Hotel)',
                        'per_night': _money(sh.price_per_night),
                    },
                    'food': {
                        'amount': _money(cost_summary.food_cost),
                        'percentage': cost_summary.food_pct,
                        'description': 'Food and dining',
                        'per_day': _money(cost_summary.food_cost / max(user_input.trip_days, 1)),
                    },
                    'activities': {
                        'amount': _money(cost_summary.activities_cost),
                        'percentage': cost_summary.activities_pct,
                        'description': 'Activities and tours',
                        'per_day': _money(cost_summary.activities_cost / max(user_input.trip_days, 1)),
                    },
                    'transport': {
                        'amount': _money(cost_summary.transport_cost),
                        'percentage': cost_summary.transport_pct,
                        'description': 'Transportation and transfers',
                        'per_trip': _money(cost_summary.transport_cost),
                    },
                    'emergency': {
                        'amount': _money(cost_summary.emergency_buffer),
                        'percentage': cost_summary.emergency_pct,
                        'description': 'Safety buffer',
                    },
                },
                'optimization_tips': validation.recommendations or ['Review your transportation and activity choices to keep costs low.'],
            },
            'destination': {
                'suggestions': [
                    {
                        'name': destination.destination.city,
                        'country': destination.destination.country,
                        'continent': 'International',
                        'season': [destination.best_season.value if hasattr(destination.best_season, 'value') else str(destination.best_season)],
                        'popularity': _round(destination.confidence_score * 100, 0),
                        'avg_daily_cost': destination.estimated_cost_per_day,
                        'interests': user_input.interests,
                        'description': destination.reason,
                        'latitude': destination.destination.latitude,
                        'longitude': destination.destination.longitude,
                        'currency': 'INR',
                        'language': 'English',
                        'best_months': user_input.travel_month,
                        'score': _round(destination.confidence_score * 100, 1),
                        'estimated_total_cost': total_cost,
                        'budget_fit': 'Within Budget' if validation.budget_within_limit else 'Over Budget',
                        'match_reason': destination.reason,
                    }
                ],
                'weather': {
                    'forecast': weather_forecast,
                    'warnings': weather.warnings,
                    'activity_suggestions': {
                        'indoor': ['Visit a local museum', 'Enjoy a cooking class'],
                        'outdoor': ['Take a scenic walking tour', 'Explore the city by bike'],
                        'note': 'Weather is generally stable, plan outdoor activities in the morning.',
                    },
                    'weather_summary': f"{weather.condition} with a high of {weather.max_temp}°C.",
                },
                'hotels': hotel_options,
                'top_pick': selected_hotel,
                'attractions': attraction_data,
                'daily_breakdown': daily_breakdown,
            },
            'route_logistics': {
                'source': user_input.source_city,
                'destination': destination.destination.city,
                'travel_distance_km': _round(final_plan.route_logistics.travel_distance_km if final_plan.route_logistics else destination.travel_distance, 1),
                'travel_time_hours': _round(final_plan.route_logistics.travel_time_hours if final_plan.route_logistics else destination.travel_time_hours, 1),
                'transport_options': transport_options,
                'best_option': transport_options[0] if transport_options else {},
                'recommended_mode': str(user_input.transportation).split('.')[-1].lower(),
                'routing_notes': final_plan.route_logistics.routing_notes if final_plan.route_logistics else '',
            },
            'schedule': {
                'days': itinerary_days,
                'summary': {
                    'total_days': len(itinerary_days),
                    'total_activities': sum(len(day['slots']) for day in itinerary_days),
                    'estimated_total_cost': total_cost,
                },
                'travel_tips': validation.recommendations or schedule.critical_notes,
                'packing_recommendations': schedule.packing_recommendations,
            },
            'validation': {
                'is_valid': validation.is_valid,
                'budget_within_limit': cost_summary.within_budget,
                'total_cost': cost_summary.total_cost,
                'remaining_budget': cost_summary.remaining_budget,
                'budget_utilization_percentage': cost_summary.utilization_pct,
                'confidence_score': validation.confidence_score,
                'issues': [i.model_dump() for i in validation.issues],
                'recommendations': validation.recommendations,
                'expense_breakdown': {
                    'accommodation': {'amount': cost_summary.hotel_cost, 'percentage': cost_summary.hotel_pct, 'description': 'Hotel charges'},
                    'food': {'amount': cost_summary.food_cost, 'percentage': cost_summary.food_pct, 'description': 'Meals and dining'},
                    'transport': {'amount': cost_summary.transport_cost, 'percentage': cost_summary.transport_pct, 'description': 'Transportation'},
                    'activities': {'amount': cost_summary.activities_cost, 'percentage': cost_summary.activities_pct, 'description': 'Tours and experiences'},
                },
                'chart_data': {
                    'type': 'pie',
                    'labels': ['Accommodation', 'Food', 'Transport', 'Activities'],
                    'datasets': [{
                        'data': [cost_summary.hotel_cost, cost_summary.food_cost, cost_summary.transport_cost, cost_summary.activities_cost],
                        'backgroundColor': ['#4F46E5', '#F59E0B', '#10B981', '#EF4444'],
                        'borderColor': ['#ffffff', '#ffffff', '#ffffff', '#ffffff'],
                        'borderWidth': 1,
                    }],
                },
                'budget_status': {
                    'status': 'within_budget' if cost_summary.within_budget else 'over_budget',
                    'message': f'Within Budget ({_money(cost_summary.remaining_budget)} remaining)' if cost_summary.within_budget else f'Over Budget by {_money(abs(cost_summary.remaining_budget))}',
                    'color': 'green' if cost_summary.within_budget else 'red',
                },
                'saving_tips': validation.recommendations or ['Book tickets early and choose local eateries to save money.'],
            },
        },
        'status': final_plan.status,
    }


# ===== Health & Info Endpoints =====

@router.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "TravelGenie API v2",
        "version": "2.0.0",
        "description": "Agentic AI Budget Travel Planner - Real-time Multi-Agent System",
        "status": "operational",
        "endpoints": {
            "POST /api/plan": "Generate a travel plan",
            "GET /api/health": "Health check",
            "GET /api/agents": "List available agents",
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        workflow = get_workflow()
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "workflow": "ready",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/agents")
async def list_agents():
    """List all available agents in the system."""
    return {
        "agents": [
            {"name": "Planner", "description": "Coordinates the full multi-agent pipeline", "status": "ready"},
            {"name": "Trip Feasibility", "description": "Validates trip feasibility and calculates budget allocation", "status": "ready"},
            {"name": "Destination", "description": "Recommends best destination using real-time data", "status": "ready"},
            {"name": "Route & Logistics", "description": "Calculates travel distance, time, and transport options", "status": "ready"},
            {"name": "Schedule", "description": "Generates optimized day-by-day itinerary", "status": "ready"},
            {"name": "Validation", "description": "Validates and repairs travel plans", "status": "ready"},
        ],
        "total_agents": 6,
    }


# ===== Core Endpoints =====

@router.post("/plan", response_model=TravelPlanResponse)
async def generate_travel_plan(request: TravelPlanRequest):
    """
    Generate a complete travel plan using the multi-agent system.
    
    This endpoint:
    1. Validates user input
    2. Runs the multi-agent pipeline
    3. Returns a comprehensive travel plan with day-by-day itinerary
    
    Args:
        request: Travel preferences from user
        
    Returns:
        Complete travel plan or error message
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting Generating travel plan for {request.source_city}")
        
        # Convert request to UserTravelInput — budget arrives in INR, convert to USD
        user_input = UserTravelInput(
            budget=round(request.budget / 83, 2),
            source_city=request.source_city,
            destination_city=request.destination_city,
            trip_days=request.trip_days,
            travel_type=request.travel_type,
            transportation=request.transportation,
            interests=request.interests,
            hotel_preference=request.hotel_preference,
            travel_month=request.travel_month,
            special_requirements=request.special_requirements,
        )
        
        # Get workflow and generate plan
        workflow = get_workflow()
        final_plan: FinalTravelPlan = await workflow.plan_trip(user_input)
        
        generation_time = time.time() - start_time
        
        # Map the final plan into the frontend-friendly schema
        plan_dict = _map_final_plan_to_frontend_plan(final_plan, generation_time)
        
        logger.info(f"Plan generated in {generation_time:.2f}s")
        
        return TravelPlanResponse(
            status="success",
            plan=plan_dict,
            error=None,
            generation_time_seconds=generation_time,
            message=f"Travel plan generated successfully for {request.source_city} in {generation_time:.2f} seconds"
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        generation_time = time.time() - start_time
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Plan generation failed: {e}", exc_info=True)
        generation_time = time.time() - start_time
        
        return TravelPlanResponse(
            status="error",
            plan=None,
            error=str(e),
            generation_time_seconds=generation_time,
            message=f"Failed to generate travel plan: {str(e)}"
        )


@router.post("/plan/stream")
async def stream_travel_plan(request: TravelPlanRequest):
    """
    Stream travel plan generation via Server-Sent Events.
    Emits one JSON event per agent step so the frontend can update progressively.
    Final event type is 'complete' and contains the full plan.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()

        async def emit(event: dict):
            await queue.put(event)

        async def run_pipeline():
            try:
                user_input = UserTravelInput(
                    budget=round(request.budget / 83, 2),
                    source_city=request.source_city,
                    destination_city=request.destination_city,
                    trip_days=request.trip_days,
                    travel_type=request.travel_type,
                    transportation=request.transportation,
                    interests=request.interests,
                    hotel_preference=request.hotel_preference,
                    travel_month=request.travel_month,
                    special_requirements=request.special_requirements,
                )
                from backend.agents.planner_agent import get_planner_agent
                planner = get_planner_agent()
                start = time.time()
                final_plan: FinalTravelPlan = await planner.coordinate_with_progress(
                    user_input, emit
                )
                generation_time = time.time() - start
                plan_dict = _map_final_plan_to_frontend_plan(final_plan, generation_time)
                await queue.put({"type": "complete", "plan": plan_dict,
                                  "generation_time_seconds": round(generation_time, 2)})
            except Exception as e:
                logger.error(f"Stream pipeline failed: {e}", exc_info=True)
                await queue.put({"type": "error", "message": str(e)})
            finally:
                await queue.put(None)  # sentinel

        task = asyncio.create_task(run_pipeline())

        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

        await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


class FollowUpRequest(BaseModel):
    original_request: dict
    instruction: str = Field(..., min_length=1)


@router.post("/plan/followup")
async def followup_plan(request: FollowUpRequest):
    """
    Smart follow-up: reuse previous plan context and regenerate only affected agents.
    """
    try:
        instruction = request.instruction.lower().strip()
        orig = dict(request.original_request)

        # Mutate the original request based on instruction
        if any(k in instruction for k in ("cheaper", "budget", "reduce", "less expensive")):
            orig["hotel_preference"] = "budget"
            orig["budget"] = float(orig.get("budget", 1000)) * 0.75
        elif "luxury" in instruction:
            orig["hotel_preference"] = "luxury"
            orig["budget"] = float(orig.get("budget", 1000)) * 1.5
        elif "family" in instruction:
            orig["travel_type"] = "family"
        elif "adventure" in instruction:
            interests = list(orig.get("interests", []))
            if "adventure" not in interests:
                interests.append("adventure")
            orig["interests"] = interests
        elif any(k in instruction for k in ("no beach", "remove beach", "without beach")):
            orig["interests"] = [i for i in orig.get("interests", []) if "beach" not in i.lower()]
        elif any(k in instruction for k in ("faster", "reduce travel", "flight")):
            orig["transportation"] = "flight"
        elif any(k in instruction for k in ("train",)):
            orig["transportation"] = "train"
        elif "more day" in instruction or "add day" in instruction:
            orig["trip_days"] = int(orig.get("trip_days", 3)) + 1
        elif "solo" in instruction:
            orig["travel_type"] = "solo"
        elif "couple" in instruction:
            orig["travel_type"] = "couple"

        # orig["budget"] is in INR (from user_input stored on frontend) — convert to USD
        orig["budget"] = round(float(orig.get("budget", 83)) / 83, 2)
        user_input = UserTravelInput(**orig)
        from backend.agents.planner_agent import get_planner_agent
        planner = get_planner_agent()
        start = time.time()
        final_plan = await planner.coordinate_with_progress(user_input, None)
        generation_time = time.time() - start
        plan_dict = _map_final_plan_to_frontend_plan(final_plan, generation_time)
        return {"status": "success", "plan": plan_dict, "instruction_applied": instruction}
    except ValueError as e:
        logger.warning(f"Follow-up validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Follow-up failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ConfirmTripRequest(BaseModel):
    plan: Dict[str, Any]
    user_input: Dict[str, Any]


@router.post("/plan/confirm")
async def confirm_trip(request: ConfirmTripRequest, db: Session = Depends(get_db)):
    """
    Save a confirmed trip to the database and return a unique trip ID.
    """
    try:
        from backend.database.models import Trip
        import json as _json

        ui = request.user_input
        plan = request.plan

        destination_name = (
            plan.get("agents", {}).get("planner", {}).get("final_recommendation", {})
            .get("summary", {}).get("destination")
            or plan.get("agents", {}).get("destination", {}).get("suggestions", [{}])[0].get("name", "")
        )

        trip = Trip(
            budget=float(ui.get("budget", 0)),
            source_city=str(ui.get("source_city", "")),
            trip_days=int(ui.get("trip_days", 1)),
            travel_type=str(ui.get("travel_type", "solo")),
            transportation=str(ui.get("transportation", "flight")),
            interests=_json.dumps(ui.get("interests", [])),
            hotel_preference=str(ui.get("hotel_preference", "budget")),
            travel_month=str(ui.get("travel_month", "")),
            destination=destination_name,
            final_recommendation=_json.dumps(plan),
            status="completed",
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        return {
            "status": "confirmed",
            "trip_id": trip.id,
            "destination": destination_name,
            "message": f"Trip to {destination_name} confirmed! Your Trip ID is #{trip.id}.",
        }
    except Exception as e:
        logger.error(f"Confirm trip failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/status")
async def services_status():
    """
    Get status of all external services.
    
    Returns:
        Status of each service: Geo, Places, Routing, Weather, Cache
    """
    from backend.services.geo_service import get_geo_service
    from backend.services.places_service import get_places_service
    from backend.services.routing_service import get_routing_service
    from backend.services.weather_service import get_weather_service
    from backend.services.cache_service import get_cache_service
    
    services_to_check = {
        "Geo (Nominatim)": get_geo_service(),
        "Places (Overpass)": get_places_service(),
        "Routing (OSRM)": get_routing_service(),
        "Weather (OpenWeatherMap)": get_weather_service(),
        "Cache": get_cache_service(),
    }
    
    status_results = {}
    for service_name, service in services_to_check.items():
        try:
            is_healthy = await service.health_check()
            status_results[service_name] = "operational" if is_healthy else "degraded"
        except Exception as e:
            logger.warning(f"Service check failed for {service_name}: {e}")
            status_results[service_name] = "error"
    
    return {
        "timestamp": time.time(),
        "services": status_results,
        "overall_status": "operational" if all(s != "error" for s in status_results.values()) else "degraded",
    }


# ===== Historical & Utility Endpoints =====

@router.get("/history")
async def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent travel plan history.
    
    Args:
        limit: Maximum number of plans to return
        db: Database session
        
    Returns:
        List of recent travel plans
    """
    try:
        from backend.database.models import Trip
        
        trips = db.query(Trip).order_by(Trip.created_at.desc()).limit(limit).all()
        
        return {
            "count": len(trips),
            "trips": [
                {
                    "id": t.id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "destination": t.destination,
                    "budget": t.budget,
                    "trip_days": t.trip_days,
                    "travel_type": t.travel_type,
                    "status": t.status,
                }
                for t in trips
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a previously generated plan by ID.
    
    Args:
        plan_id: Plan ID
        db: Database session
        
    Returns:
        Complete travel plan details
    """
    try:
        from backend.database.models import Trip
        
        trip = db.query(Trip).filter(Trip.id == plan_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {
            "id": trip.id,
            "created_at": trip.created_at.isoformat() if trip.created_at else None,
            "destination": trip.destination,
            "budget": trip.budget,
            "trip_days": trip.trip_days,
            "travel_type": trip.travel_type,
            "data": json.loads(trip.final_recommendation) if trip.final_recommendation else None,
            "status": trip.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plan")
