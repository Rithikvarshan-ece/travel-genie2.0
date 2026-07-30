"""
TravelGenie Async Base Agent

Base class for all refactored async agents using LangChain.
Each agent:
- Uses async/await
- Consumes Pydantic models
- Produces Pydantic models
- Logs execution metrics
- Handles errors gracefully
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel
from backend.services.groq_service import get_groq_service, GroqService
from backend.config import get_settings

logger = logging.getLogger(__name__)


class AgentException(Exception):
    """Exception raised by agents."""

    def __init__(self, agent_name: str, message: str, original_error: Optional[Exception] = None):
        """
        Initialize agent exception.
        
        Args:
            agent_name: Name of the agent that failed
            message: Error message
            original_error: Original exception that caused this
        """
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{agent_name}] {message}")


class AgentMetrics:
    """Metrics for a single agent execution."""

    def __init__(self, agent_name: str):
        """Initialize metrics."""
        self.agent_name = agent_name
        self.start_time = time.time()
        self.end_time = None
        self.duration_seconds = 0
        self.tokens_used = 0
        self.error = None

    def mark_complete(self):
        """Mark agent execution as complete."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "agent_name": self.agent_name,
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "error": self.error,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentMetrics({self.agent_name}, duration={self.duration_seconds:.2f}s)>"


class AsyncBaseAgent(ABC):
    """
    Abstract base class for all async TravelGenie agents.
    
    Each agent:
    - Accepts structured Pydantic input
    - Returns structured Pydantic output
    - Uses LLM for reasoning via GroqService
    - Logs execution metrics
    - Handles errors gracefully
    """

    def __init__(self, name: str, description: str):
        """
        Initialize async agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
        self.settings = get_settings()
        self.groq_service = get_groq_service()
        self.logger.info(f"{name} agent initialized")

    @abstractmethod
    async def process(self, input_model: BaseModel) -> BaseModel:
        """
        Process input and return output.
        Must be implemented by subclasses.
        
        Args:
            input_model: Pydantic input model
            
        Returns:
            Pydantic output model
            
        Raises:
            AgentException: If processing fails
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            System prompt string
        """
        pass

    async def invoke(self, input_model: BaseModel, _retries: int = 3) -> BaseModel:
        """
        Invoke the agent with metrics tracking and automatic retry (3 attempts).
        """
        metrics = AgentMetrics(self.name)
        last_exc: Exception = None

        for attempt in range(1, _retries + 1):
            try:
                self.logger.info(f"Starting {self.name} agent (attempt {attempt})")
                output = await self.process(input_model)
                metrics.mark_complete()
                self.logger.info(f"✅ {self.name} completed in {metrics.duration_seconds:.2f}s")
                if hasattr(output, '__dict__'):
                    output._agent_metrics = metrics
                return output
            except AgentException as e:
                last_exc = e
                metrics.error = str(e)
                self.logger.warning(f"⚠️ {self.name} attempt {attempt} failed: {e}")
                if attempt < _retries:
                    await __import__('asyncio').sleep(0.5 * attempt)
            except Exception as e:
                last_exc = AgentException(self.name, f"Unexpected error: {str(e)}", e)
                self.logger.warning(f"⚠️ {self.name} attempt {attempt} unexpected error: {e}")
                if attempt < _retries:
                    await __import__('asyncio').sleep(0.5 * attempt)

        metrics.mark_complete()
        self.logger.error(f"❌ {self.name} failed after {_retries} attempts")
        raise last_exc

    async def query_llm(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        output_model: Optional[Type[BaseModel]] = None,
    ) -> Any:
        sys_prompt = system_prompt or self.get_system_prompt()
        try:
            response = await self.groq_service.async_invoke(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )
            if output_model is not None:
                return self.parse_json_output(response, output_model)
            return response
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            if self.settings.use_fallback_seeded_data and hasattr(self, 'fallback_response'):
                self.logger.warning(f"Falling back to internal response generator for {self.name}")
                return await self.fallback_response(user_prompt, sys_prompt, output_model)
            raise AgentException(self.name, f"LLM query failed: {str(e)}", e)

    def parse_json_output(self, text: str, output_model: Type[BaseModel]) -> BaseModel:
        """
        Parse JSON output from LLM into Pydantic model.
        
        Handles common LLM quirks:
        - Extracts JSON from markdown code blocks (```json ... ```)
        - Unwraps nested structures where the top-level JSON has a single key
          whose value is a dict (e.g., {"validation_results": {"is_valid": ...}})
        
        Args:
            text: Text response from LLM (should be JSON)
            output_model: Pydantic model class to parse into
            
        Returns:
            Parsed Pydantic model instance
            
        Raises:
            AgentException: If parsing fails
        """
        import json
        
        try:
            # Try to extract JSON from text
            json_str = text
            
            # If text contains markdown code blocks, extract the JSON
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            
            # Parse JSON
            json_obj = json.loads(json_str)
            
            # Unwrap nested structures: if the top-level JSON has a single key
            # whose value is a dict, try to validate the inner dict instead.
            # This handles LLMs that wrap output like {"validation_results": {...}}
            if isinstance(json_obj, dict) and len(json_obj) == 1:
                inner = next(iter(json_obj.values()))
                if isinstance(inner, dict):
                    try:
                        return output_model.model_validate(inner)
                    except Exception:
                        # Inner dict didn't match — fall through to validate the
                        # original top-level object
                        pass
            
            # Validate and create Pydantic model
            return output_model.model_validate(json_obj)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            raise AgentException(
                self.name, 
                f"Failed to parse LLM output as JSON: {str(e)}", 
                e
            )
        except Exception as e:
            self.logger.error(f"Output validation failed: {e}")
            raise AgentException(
                self.name,
                f"Failed to validate output: {str(e)}",
                e
            )

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.name}Agent(description={self.description})>"
