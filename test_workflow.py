import asyncio
import traceback
import sys
import logging

logging.basicConfig(level=logging.WARNING)

async def test():
    print("Starting test...", flush=True)
    from backend.workflow import TravelPlanWorkflow
    from backend.models import UserTravelInput
    print("Imports OK", flush=True)

    user_input = UserTravelInput(
        budget=2000,
        source_city="New York",
        trip_days=5,
        travel_type="couple",
        transportation="flight",
        interests=["food", "culture"],
        hotel_preference="budget",
        travel_month="July",
    )
    print("Input created", flush=True)

    wf = TravelPlanWorkflow()
    print("Workflow created", flush=True)

    try:
        plan = await wf.plan_trip(user_input)
        print(f"Plan OK: {plan.destination.destination.city}, cost={plan.total_trip_cost}, status={plan.status}", flush=True)
    except Exception as e:
        print(f"PLAN ERROR: {e}", flush=True)
        traceback.print_exc()

asyncio.run(test())
