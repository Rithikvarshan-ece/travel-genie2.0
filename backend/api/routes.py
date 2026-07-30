"""
TravelGenie API Routes
REST API endpoints for the multi-agent travel planning system.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from backend.agents.orchestrator import orchestrator
from backend.database.database import get_db, init_db
from backend.database.models import Trip, FavoriteDestination
from sqlalchemy.orm import Session
import json

router = APIRouter(prefix="/api", tags=["TravelGenie API"])


# ===== Request/Response Models =====

class TravelInput(BaseModel):
    """User input model for travel planning."""
    budget: float = Field(..., gt=0, description="Total trip budget in USD")
    source_city: str = Field(..., min_length=2, description="Departure city")
    trip_days: int = Field(..., ge=1, le=30, description="Number of days")
    travel_type: str = Field(..., pattern="^(solo|family|couple|friends)$")
    transportation: str = Field(..., pattern="^(flight|train|bus|car)$")
    interests: List[str] = Field(..., min_items=1)
    hotel_preference: str = Field(..., pattern="^(budget|luxury|hostel|resort)$")
    travel_month: str = Field(..., min_length=2)


class TravelPlanResponse(BaseModel):
    """Response model for generated travel plans."""
    plan_id: int
    generation_time_seconds: float
    user_input: Dict[str, Any]
    agents: Dict[str, Any]
    status: str


# ===== Utility Functions =====

def serialize_for_json(obj: Any) -> Any:
    """Serialize objects for JSON response."""
    import datetime
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    return str(obj)


# ===== API Endpoints =====

@router.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "TravelGenie API",
        "version": "1.0.0",
        "description": "Agentic AI Budget Travel Planner",
        "agents": orchestrator.get_agent_info(),
        "endpoints": {
            "POST /api/plan": "Generate a travel plan",
            "GET /api/plan/{plan_id}": "Get a saved plan",
            "GET /api/agents": "List all AI agents",
            "GET /api/destinations": "List destinations",
            "GET /api/history": "Get trip history",
            "POST /api/favorites": "Save favorite destination",
        }
    }


@router.get("/agents")
async def list_agents():
    """List all available AI agents."""
    return {
        "count": len(orchestrator.agents),
        "agents": orchestrator.get_agent_info()
    }


@router.post("/plan", response_model=TravelPlanResponse)
async def generate_plan(input_data: TravelInput):
    """
    Generate a complete travel plan using the multi-agent system.
    
    This endpoint:
    1. Takes user travel preferences
    2. Runs the multi-agent pipeline
    3. Returns comprehensive travel plan
    """
    try:
        # Convert input to dict (Pydantic v2 compatible)
        user_input = input_data.model_dump()
        # Convert interests list to comma-separated for storage
        user_input["interests_str"] = ",".join(user_input["interests"])
        
        # Generate plan using orchestrator
        plan = orchestrator.generate_plan(user_input)
        
        # Serialize for response
        serialized_plan = serialize_for_json(plan)
        
        return serialized_plan
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Plan generation failed: {str(e)}"
        )


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Retrieve a previously generated plan by ID."""
    trip = db.query(Trip).filter(Trip.id == plan_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {
        "id": trip.id,
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
        "user_input": {
            "budget": trip.budget,
            "source_city": trip.source_city,
            "trip_days": trip.trip_days,
            "travel_type": trip.travel_type,
            "transportation": trip.transportation,
            "interests": json.loads(trip.interests) if trip.interests else [],
            "hotel_preference": trip.hotel_preference,
            "travel_month": trip.travel_month,
        },
        "destination_suggestions": json.loads(trip.destination_suggestions) if trip.destination_suggestions else None,
        "budget_breakdown": json.loads(trip.budget_breakdown) if trip.budget_breakdown else None,
        "weather_info": json.loads(trip.weather_info) if trip.weather_info else None,
        "transport_options": json.loads(trip.transport_options) if trip.transport_options else None,
        "hotel_suggestions": json.loads(trip.hotel_suggestions) if trip.hotel_suggestions else None,
        "attractions": json.loads(trip.attractions) if trip.attractions else None,
        "daily_itinerary": json.loads(trip.daily_itinerary) if trip.daily_itinerary else None,
        "expense_summary": json.loads(trip.expense_summary) if trip.expense_summary else None,
        "status": trip.status,
    }


@router.get("/destinations")
async def list_destinations(
    interest: Optional[str] = None,
    max_budget: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List available destinations with optional filtering."""
    from backend.database.models import Destination
    query = db.query(Destination)
    
    if interest:
        query = query.filter(Destination.interests.contains(interest))
    if max_budget:
        query = query.filter(Destination.avg_daily_cost <= max_budget)
    
    destinations = query.all()
    
    return {
        "count": len(destinations),
        "destinations": [
            {
                "id": d.id,
                "name": d.name,
                "country": d.country,
                "continent": d.continent,
                "season": d.season,
                "popularity": d.popularity_score,
                "avg_daily_cost": d.avg_daily_cost,
                "interests": json.loads(d.interests) if d.interests else [],
                "description": d.description,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "best_months": d.best_months,
            }
            for d in destinations
        ]
    }


@router.get("/history")
async def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent trip history."""
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


@router.post("/favorites")
async def add_favorite(
    trip_id: int,
    destination: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Save a destination to favorites."""
    fav = FavoriteDestination(
        trip_id=trip_id,
        destination=destination,
        notes=notes
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    
    return {
        "message": "Destination saved to favorites",
        "favorite": {
            "id": fav.id,
            "destination": fav.destination,
            "saved_at": fav.saved_at.isoformat() if fav.saved_at else None,
        }
    }


@router.get("/favorites")
async def get_favorites(db: Session = Depends(get_db)):
    """Get all favorite destinations."""
    favorites = db.query(FavoriteDestination).all()
    
    return {
        "count": len(favorites),
        "favorites": [
            {
                "id": f.id,
                "destination": f.destination,
                "notes": f.notes,
                "saved_at": f.saved_at.isoformat() if f.saved_at else None,
            }
            for f in favorites
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TravelGenie API",
        "version": "1.0.0"
    }

