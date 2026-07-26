"""
TravelGenie Weather Service

Weather information retrieval using OpenWeatherMap API.
Features:
- Current weather conditions
- Weather forecast
- Rain probability
- Temperature and warnings
- Caching
"""

import logging
from typing import Optional, Dict, Any
import httpx
from backend.services.base_service import BaseService, ServiceException, get_memory_cache
from backend.models import Weather
from backend.config import get_settings

logger = logging.getLogger(__name__)


class WeatherService(BaseService):
    """
    Weather service using OpenWeatherMap API.
    
    Provides:
    - Current weather conditions
    - Weather forecast
    - Temperature and humidity
    - Rain probability and warnings
    """

    def __init__(self):
        """Initialize Weather Service."""
        settings = get_settings()
        super().__init__(
            name="Weather",
            base_url="https://api.openweathermap.org",
        )
        self.cache = get_memory_cache()
        self.api_key = settings.openweather_api_key
        
        if not self.api_key:
            self.logger.warning("Warning OpenWeatherMap API key not configured")

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Weather:
        """
        Get current weather for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Weather object with current conditions
            
        Raises:
            ServiceException: If fetch fails
        """
        # Check cache first
        cache_key = f"weather:current:{latitude:.4f}:{longitude:.4f}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if not self.api_key:
            self.logger.warning("Cannot fetch weather - API key not configured")
            return self._get_fallback_weather()

        try:
            result = await self.retry_with_backoff(
                self._get_current_weather_internal,
                latitude,
                longitude,
                operation_name=f"Get current weather for ({latitude:.4f}, {longitude:.4f})",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=30)  # Weather cache shorter TTL
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get weather: {e}")
            return self._get_fallback_weather()

    async def _get_current_weather_internal(
        self,
        latitude: float,
        longitude: float,
    ) -> Weather:
        """
        Internal weather fetch implementation.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Weather object
        """
        client = await self.get_http_client()

        url = f"{self.base_url}/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }

        response = await client.get(url, params=params, timeout=self.settings.weather_timeout)
        response.raise_for_status()

        data = response.json()

        # Extract weather data
        main = data.get("main", {})
        weather_info = data.get("weather", [{}])[0]
        clouds = data.get("clouds", {})
        rain = data.get("rain", {})

        # Calculate rain probability
        rain_prob = min(len(rain) * 0.5, 1.0)  # Rough estimate

        warnings = []
        if main.get("temp", 0) < 0:
            warnings.append("⚠️ Freezing temperature")
        if main.get("temp", 0) > 35:
            warnings.append("⚠️ Very hot weather")
        if rain_prob > 0.7:
            warnings.append("⚠️ High chance of rain")
        if data.get("wind", {}).get("speed", 0) > 10:
            warnings.append("⚠️ Strong winds")

        return Weather(
            current_temp=main.get("temp", 20),
            max_temp=main.get("temp_max", 20),
            min_temp=main.get("temp_min", 20),
            condition=weather_info.get("main", "Clear"),
            rain_probability=rain_prob,
            humidity=main.get("humidity", 50) / 100.0,
            wind_speed=data.get("wind", {}).get("speed", 0),
            warnings=warnings,
        )

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days to forecast (1-8)
            
        Returns:
            Dictionary with forecast data
        """
        cache_key = f"weather:forecast:{latitude:.4f}:{longitude:.4f}:{days}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if not self.api_key:
            return {"error": "Weather API not configured"}

        try:
            result = await self.retry_with_backoff(
                self._get_forecast_internal,
                latitude,
                longitude,
                days,
                operation_name=f"Get {days}-day forecast for ({latitude:.4f}, {longitude:.4f})",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=60)
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get forecast: {e}")
            return {"error": str(e)}

    async def _get_forecast_internal(
        self,
        latitude: float,
        longitude: float,
        days: int,
    ) -> Dict[str, Any]:
        """
        Internal forecast fetch implementation.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days
            
        Returns:
            Forecast data
        """
        client = await self.get_http_client()

        # OpenWeatherMap 5-day forecast endpoint
        url = f"{self.base_url}/data/2.5/forecast"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "cnt": min(days * 8, 40),  # 40 is max for free tier (5 days)
        }

        response = await client.get(url, params=params, timeout=self.settings.weather_timeout)
        response.raise_for_status()

        data = response.json()

        # Process forecast data
        forecast_list = []
        for forecast in data.get("list", []):
            forecast_list.append({
                "date": forecast.get("dt_txt"),
                "temp": forecast.get("main", {}).get("temp"),
                "condition": forecast.get("weather", [{}])[0].get("main"),
                "rain_prob": forecast.get("pop", 0),
            })

        return {
            "location": data.get("city", {}),
            "forecast": forecast_list[:days],
        }

    async def check_weather_compatibility(
        self,
        latitude: float,
        longitude: float,
        activity: str,
    ) -> Dict[str, Any]:
        """
        Check if current weather is suitable for an activity.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            activity: Activity name (hiking, swimming, sightseeing, etc.)
            
        Returns:
            Dictionary with compatibility assessment
        """
        weather = await self.get_current_weather(latitude, longitude)

        # Simple compatibility rules
        compatibility_rules = {
            "hiking": {
                "min_temp": 0,
                "max_temp": 35,
                "max_rain_prob": 0.5,
                "max_wind_speed": 15,
            },
            "swimming": {
                "min_temp": 15,
                "max_temp": 40,
                "max_rain_prob": 0.8,
                "max_wind_speed": 20,
            },
            "sightseeing": {
                "min_temp": -5,
                "max_temp": 40,
                "max_rain_prob": 0.6,
                "max_wind_speed": 25,
            },
            "beach": {
                "min_temp": 20,
                "max_temp": 40,
                "max_rain_prob": 0.3,
                "max_wind_speed": 15,
            },
        }

        rules = compatibility_rules.get(activity.lower(), compatibility_rules["sightseeing"])

        is_compatible = (
            rules["min_temp"] <= weather.current_temp <= rules["max_temp"]
            and weather.rain_probability <= rules["max_rain_prob"]
            and weather.wind_speed <= rules["max_wind_speed"]
        )

        return {
            "activity": activity,
            "is_compatible": is_compatible,
            "weather": weather.model_dump(),
            "requirements": rules,
            "issues": weather.warnings,
        }

    def _get_fallback_weather(self) -> Weather:
        """
        Get fallback weather data when API is unavailable.
        
        Returns:
            Default weather object
        """
        return Weather(
            current_temp=22,
            max_temp=28,
            min_temp=18,
            condition="Partly Cloudy",
            rain_probability=0.2,
            humidity=0.6,
            wind_speed=5,
            warnings=["⚠️ Using default weather - API unavailable"],
        )

    async def health_check(self) -> bool:
        """
        Check if OpenWeatherMap API is accessible.
        
        Returns:
            True if service is healthy
        """
        if not self.api_key:
            return False

        try:
            client = await self.get_http_client()
            response = await client.get(
                f"{self.base_url}/data/2.5/weather",
                params={"lat": 40.7128, "lon": -74.0060, "appid": self.api_key},
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False


# Global Weather service instance
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """
    Get or create the global Weather service instance.
    
    Returns:
        WeatherService instance
    """
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
