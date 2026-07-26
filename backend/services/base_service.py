"""
TravelGenie Base Service

Abstract base class for all external API services.
Provides common functionality: retry logic, timeouts, error handling.
"""

import logging
import asyncio
from typing import Optional, Any, Dict, Callable, TypeVar
from abc import ABC, abstractmethod
import httpx
from datetime import datetime, timedelta
from backend.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceException(Exception):
    """Base exception for service-related errors."""

    def __init__(self, service_name: str, message: str, original_error: Optional[Exception] = None):
        """
        Initialize service exception.
        
        Args:
            service_name: Name of the service that failed
            message: Error message
            original_error: Original exception that caused this
        """
        self.service_name = service_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{service_name}] {message}")


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_delay: float = 60.0,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            exponential_base: Base for exponential backoff
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class BaseService(ABC):
    """
    Abstract base class for all TravelGenie services.
    
    Provides:
    - Retry logic with exponential backoff
    - HTTP client management
    - Error handling
    - Logging
    """

    def __init__(self, name: str, base_url: Optional[str] = None):
        """
        Initialize base service.
        
        Args:
            name: Service name
            base_url: Optional base URL for API
        """
        self.name = name
        self.base_url = base_url
        self.settings = get_settings()
        self.retry_config = RetryConfig(
            max_retries=self.settings.max_retries,
            initial_delay=self.settings.retry_delay_seconds,
            exponential_base=self.settings.exponential_backoff_base,
        )
        self.logger = logging.getLogger(f"service.{name}")
        self._http_client: Optional[httpx.AsyncClient] = None
        logger.info(f"{name} service initialized")

    async def get_http_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client (connection pooling).
        
        Returns:
            AsyncClient instance
        """
        if self._http_client is None:
            headers = {
                "User-Agent": self.settings.service_user_agent,
                "Accept": "application/json",
            }
            if self.settings.service_contact_email:
                headers["From"] = self.settings.service_contact_email

            self._http_client = httpx.AsyncClient(
                timeout=self.settings.default_http_timeout,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                headers=headers,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def retry_with_backoff(
        self,
        func: Callable[..., Any],
        *args,
        operation_name: str = "Operation",
        **kwargs,
    ) -> Any:
        """
        Execute a function with retry logic and exponential backoff.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            operation_name: Name of operation for logging
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            ServiceException: If all retries fail
        """
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                self.logger.debug(f"[Attempt {attempt + 1}] {operation_name}")
                result = await func(*args, **kwargs)
                if attempt > 0:
                    self.logger.info(f"{operation_name} succeeded after {attempt} retries")
                return result

            except ServiceException as e:
                # Don't retry service exceptions
                raise
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.settings.default_http_timeout}s"
                self.logger.warning(f"Timeout {operation_name} - {last_error}")
            except httpx.HTTPError as e:
                last_error = f"HTTP Error: {str(e)}"
                self.logger.warning(f"Warning {operation_name} - {last_error}")
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Warning {operation_name} - {last_error}")

            # Wait before retry (except on last attempt)
            if attempt < self.retry_config.max_retries:
                delay = self.retry_config.get_delay(attempt)
                self.logger.debug(f"Retrying Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        # All retries exhausted
        error_msg = f"{operation_name} failed after {self.retry_config.max_retries + 1} attempts: {last_error}"
        self.logger.error(f"Error {error_msg}")
        raise ServiceException(self.name, error_msg)

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the service is healthy and accessible.
        
        Returns:
            True if service is accessible
        """
        pass

    def __repr__(self) -> str:
        """String representation of service."""
        return f"<{self.name}Service(base_url={self.base_url})>"


class CacheEntry:
    """Represents a cached value with TTL."""

    def __init__(self, value: Any, ttl_minutes: int = 30):
        """
        Initialize cache entry.
        
        Args:
            value: Value to cache
            ttl_minutes: Time-to-live in minutes
        """
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = timedelta(minutes=ttl_minutes)

    def is_expired(self) -> bool:
        """
        Check if cache entry has expired.
        
        Returns:
            True if expired
        """
        return datetime.utcnow() - self.created_at > self.ttl

    def __repr__(self) -> str:
        """String representation."""
        return f"<CacheEntry(created={self.created_at}, ttl={self.ttl})>"


class InMemoryCache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger("cache.memory")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self.logger.debug(f"Cache expired for key: {key}")
            return None

        self.logger.debug(f"Cache hit for key: {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_minutes: Time-to-live in minutes
        """
        self._cache[key] = CacheEntry(value, ttl_minutes)
        self.logger.debug(f"Cache set for key: {key} (TTL={ttl_minutes}m)")

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self.logger.info("Cache cleared")

    def __len__(self) -> int:
        """Get number of entries in cache."""
        return len(self._cache)


# Global in-memory cache instance
_memory_cache = InMemoryCache()


def get_memory_cache() -> InMemoryCache:
    """Get global memory cache instance."""
    return _memory_cache
