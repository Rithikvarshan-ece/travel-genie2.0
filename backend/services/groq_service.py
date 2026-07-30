"""
TravelGenie Groq Service

Centralized LLM service using Groq API.
Handles all LLM interactions for agents with retry logic and token counting.
"""

import logging
from typing import Optional, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.config import get_settings
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class GroqService:
    """
    Centralized Groq LLM service.
    
    Features:
    - Single LLM instance (no duplication)
    - Async-compatible
    - Token tracking
    - Error handling and retries
    - Structured output support
    """

    def __init__(self):
        """Initialize the Groq service with settings."""
        settings = get_settings()
        self.settings = settings
        self.llm = self._initialize_llm()
        self.total_tokens_used = 0
        logger.info("GroqService initialized")

    def _initialize_llm(self) -> Optional[ChatGroq]:
        """
        Initialize the Groq LLM client.
        
        Returns:
            Initialized ChatGroq instance or None when no API key is configured
        """
        settings = self.settings

        if not settings.groq_api_key:
            logger.warning("Warning Groq API key not configured. Direct Groq access is disabled.")
            return None

        try:
            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=settings.groq_temperature,
                max_tokens=settings.groq_max_tokens,
                timeout=30,
                max_retries=settings.max_retries,
            )
            logger.info(f"Groq LLM initialized with model: {settings.groq_model}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")
            return None

    async def async_invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            llm = self.llm
            if temperature is not None or max_tokens is not None:
                llm = self._create_configured_llm(temperature, max_tokens)
            if llm is None:
                raise RuntimeError("Groq client is not configured — set GROQ_API_KEY in .env")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: llm.invoke(messages)
            )
            result_text = getattr(response, 'content', str(response))
            self._track_tokens(result_text)
            logger.debug(f"LLM invocation successful ({len(result_text)} chars)")
            return result_text
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

    def sync_invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Invoke the LLM synchronously.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message/query
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            LLM response text
        """
        try:
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Prepare LLM with optional overrides
            llm = self.llm
            if temperature is not None or max_tokens is not None:
               llm = self._create_configured_llm(temperature, max_tokens)

            if llm is None:
               raise RuntimeError("Groq client is not configured")

            # Invoke
            response = llm.invoke(messages)

            # Extract text
            result_text = getattr(response, 'content', str(response))

            # Track tokens
            self._track_tokens(result_text)

            logger.debug(f"LLM invocation successful ({len(result_text)} chars)")
            return result_text

        except Exception as e:
            logger.error(f"Error LLM invocation failed: {e}")
            raise

    def _create_configured_llm(
        self, temperature: Optional[float], max_tokens: Optional[int]
    ) -> Optional[ChatGroq]:
        """
        Create a configured LLM instance with overrides.
         
        Args:
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
             
        Returns:
            Configured LLM instance or None if API key is missing
        """
        settings = self.settings
        if not settings.groq_api_key:
            return None
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=temperature or settings.groq_temperature,
            max_tokens=max_tokens or settings.groq_max_tokens,
            timeout=30,
            max_retries=settings.max_retries,
        )

    def _track_tokens(self, text: str) -> None:
        """
        Track token usage (approximate).
        
        Args:
            text: Response text to estimate tokens from
        """
        # Rough estimation: 1 token ≈ 4 characters (GPT estimation)
        estimated_tokens = len(text) // 4
        self.total_tokens_used += estimated_tokens

    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get total token usage statistics.
        
        Returns:
            Dictionary with token usage stats
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self.total_tokens_used * 0.00001,  # Groq pricing varies
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counter."""
        self.total_tokens_used = 0


# Global Groq service instance
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    """
    Get or create the global Groq service instance.
    Ensures singleton pattern - only one LLM client.
    
    Returns:
        GroqService instance
    """
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service


def with_groq_service(func):
    """
    Decorator to inject GroqService into functions.
    
    Usage:
        @with_groq_service
        async def my_function(groq_service: GroqService):
            pass
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        kwargs["groq_service"] = get_groq_service()
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        kwargs["groq_service"] = get_groq_service()
        return func(*args, **kwargs)

    # Return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
