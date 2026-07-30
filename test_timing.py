import asyncio, time, logging, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

async def test():
    from backend.workflow import TravelPlanWorkflow
    from backend.models import UserTravelInput

    user_input = UserTravelInput(
        budget=2000, source_city="New York", trip_days=5,
        travel_type="couple", transportation="flight",
        interests=["food", "culture"], hotel_preference="budget",
        travel_month="July",
    )

    wf = TravelPlanWorkflow()

    t0 = time.time()
    print("--- Trip Feasibility ---", flush=True)
    state = {"user_input": user_input}
    state = await wf._node_trip_feasibility(state)
    print(f"  done in {time.time()-t0:.2f}s | error={state.get('error_message')}", flush=True)

    t1 = time.time()
    print("--- Destination ---", flush=True)
    state = await wf._node_destination(state)
    print(f"  done in {time.time()-t1:.2f}s | error={state.get('error_message')}", flush=True)

    t2 = time.time()
    print("--- Schedule ---", flush=True)
    state = await wf._node_schedule(state)
    print(f"  done in {time.time()-t2:.2f}s | error={state.get('error_message')}", flush=True)

    t3 = time.time()
    print("--- Validation ---", flush=True)
    state = await wf._node_validation(state)
    print(f"  done in {time.time()-t3:.2f}s | error={state.get('error_message')}", flush=True)

    t4 = time.time()
    print("--- Finalize ---", flush=True)
    state = await wf._node_finalize(state)
    print(f"  done in {time.time()-t4:.2f}s | error={state.get('error_message')}", flush=True)

    print(f"\nTOTAL: {time.time()-t0:.2f}s", flush=True)
    if state.get("final_plan"):
        p = state["final_plan"]
        print(f"Destination: {p.destination.destination.city}", flush=True)
        print(f"Status: {p.status}", flush=True)

asyncio.run(test())
