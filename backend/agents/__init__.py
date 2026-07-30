# TravelGenie AI Agents Package — 6 real async agents
# Lazy imports to avoid circular dependency at module load time.
# Use get_*_agent() factory functions instead of importing classes directly.
from backend.agents.async_base_agent import AsyncBaseAgent, AgentException, AgentMetrics


def get_planner_agent():
    from backend.agents.planner_agent import get_planner_agent as _g
    return _g()


def get_trip_feasibility_agent():
    from backend.agents.trip_feasibility_agent import get_trip_feasibility_agent as _g
    return _g()


def get_destination_agent():
    from backend.agents.destination_agent import get_destination_agent as _g
    return _g()


def get_route_logistics_agent():
    from backend.agents.route_logistics_agent import get_route_logistics_agent as _g
    return _g()


def get_schedule_agent():
    from backend.agents.schedule_agent import get_schedule_agent as _g
    return _g()


def get_validation_agent():
    from backend.agents.validation_agent import get_validation_agent as _g
    return _g()
