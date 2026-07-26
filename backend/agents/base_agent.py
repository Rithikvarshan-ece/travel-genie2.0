"""
TravelGenie Base Agent
Defines the abstract base class for all AI agents in the multi-agent system.
Each agent specializes in a specific domain of travel planning.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all TravelGenie agents.
    Provides common functionality and enforces the agent interface.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize a new agent.
        
        Args:
            name: Agent's display name
            description: What the agent does
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the given context and return results.
        Every agent must implement this method.
        
        Args:
            context: Dictionary containing all relevant data for processing
            
        Returns:
            Dictionary with the agent's output
        """
        pass

    def validate_input(self, context: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that required fields exist in the context.
        
        Args:
            context: The input context dictionary
            required_fields: List of field names that must be present
            
        Returns:
            True if all required fields are present, False otherwise
        """
        missing = [field for field in required_fields if field not in context]
        if missing:
            self.logger.warning(f"Missing required fields: {missing}")
            return False
        return True

    def safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert a value to float."""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    def safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert a value to int."""
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default

    def to_json(self, data: Any) -> str:
        """Convert data to JSON string."""
        return json.dumps(data, default=str, indent=2)

    def from_json(self, data: str) -> Any:
        """Parse JSON string to Python object."""
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
        return data

    def log_step(self, step_name: str, details: str = ""):
        """Log an agent processing step."""
        self.logger.info(f"[{self.name}] {step_name}: {details}")


class AgentContext:
    """
    Shared context that flows through the multi-agent pipeline.
    Each agent reads from and writes to this context.
    """

    def __init__(self, user_input: Dict[str, Any]):
        """
        Initialize the agent context with user input.
        
        Args:
            user_input: Dictionary containing user's travel preferences
        """
        self.user_input = user_input
        self.data: Dict[str, Any] = {
            "user_input": user_input,
            "planner": {},
            "budget": {},
            "destination": {},
            "weather": {},
            "transport": {},
            "hotel": {},
            "attraction": {},
            "itinerary": {},
            "expense": {},
            "errors": [],
            "warnings": [],
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a value in the context data."""
        self.data[key] = value

    def update(self, key: str, value: Dict[str, Any]):
        """Update a nested dictionary in the context."""
        if key in self.data and isinstance(self.data[key], dict):
            self.data[key].update(value)
        else:
            self.data[key] = value

    def add_error(self, error: str):
        """Add an error message."""
        self.data["errors"].append(error)

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.data["warnings"].append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire context to a dictionary."""
        return self.data

