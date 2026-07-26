"""
TravelGenie Configuration Module

Centralized configuration for all backend services, API keys, and settings.
Reads from environment variables with secure defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings from environment variables.
    Uses pydantic-settings for environment variable validation.
    """

    # ===== LLM Configuration =====
    groq_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"
    groq_temperature: float = 0.7
    groq_max_tokens: int = 2048

    # ===== External API Configuration =====
    # Geo Service (Nominatim - OpenStreetMap)
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_timeout: int = 10

    # Places Service (Overpass API)
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    overpass_timeout: int = 30

    # Routing Service (OSRM - Open Source Routing Machine)
    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout: int = 15

    # Weather Service
    weather_api_provider: str = "openweathermap"  # or "weatherapi"
    openweather_api_key: Optional[str] = None
    weatherapi_api_key: Optional[str] = None
    weather_timeout: int = 10

    # ===== Database Configuration =====
    # SQLite for primary data
    database_url: str = "sqlite:///./travel_genie.db"
    
    # MongoDB for caching and analytics (optional)
    mongodb_url: Optional[str] = None
    mongodb_database: str = "travel_genie"

    # ===== Cache Configuration =====
    cache_ttl_minutes: int = 30
    cache_enabled: bool = True

    # ===== Server Configuration =====
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # ===== API Rate Limiting =====
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    exponential_backoff_base: float = 2.0

    # ===== Timeout Configuration =====
    default_http_timeout: int = 30
    planner_timeout_seconds: int = 120

    # ===== Service Headers =====
    service_user_agent: str = "TravelGenie/1.0 (+https://github.com/travelgenie)"
    service_contact_email: Optional[str] = None

    # ===== Feature Flags =====
    use_real_time_data: bool = True
    enable_caching: bool = True
    enable_logging: bool = True
    use_fallback_seeded_data: bool = True

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate_settings(self) -> bool:
        """
        Validate that all required settings are properly configured.
        
        Returns:
            True if all required settings are valid
            
        Raises:
            ValueError: If critical settings are missing
        """
        if not self.groq_api_key and not self.use_fallback_seeded_data:
            raise ValueError("GROQ_API_KEY is required when fallback is disabled")
        
        logger.info("All settings validated successfully")
        return True


# Global settings instance
try:
    settings = Settings()
    settings.validate_settings()
except Exception as e:
    logger.error(f"Error Settings initialization failed: {e}")
    raise


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings instance with all configuration
    """
    return settings


# Configuration constants for services
SERVICE_CONFIG = {
    "geo": {
        "name": "Nominatim (OpenStreetMap)",
        "base_url": settings.nominatim_base_url,
        "timeout": settings.nominatim_timeout,
        "max_retries": settings.max_retries,
    },
    "places": {
        "name": "Overpass API",
        "base_url": settings.overpass_api_url,
        "timeout": settings.overpass_timeout,
        "max_retries": settings.max_retries,
    },
    "routing": {
        "name": "OSRM (Open Source Routing Machine)",
        "base_url": settings.osrm_base_url,
        "timeout": settings.osrm_timeout,
        "max_retries": settings.max_retries,
    },
    "weather": {
        "name": settings.weather_api_provider,
        "timeout": settings.weather_timeout,
        "max_retries": settings.max_retries,
    },
}
