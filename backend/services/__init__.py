"""
TravelGenie Services Module

Provides all external API integrations:
- GeoService (Nominatim/OpenStreetMap)
- PlacesService (Overpass API)
- RoutingService (OSRM)
- WeatherService (OpenWeatherMap/WeatherAPI)
- CacheService (MongoDB/SQLite)
"""

from backend.services.base_service import BaseService, ServiceException, InMemoryCache, get_memory_cache
from backend.services.geo_service import GeoService, get_geo_service
from backend.services.places_service import PlacesService, get_places_service
from backend.services.routing_service import RoutingService, get_routing_service
from backend.services.weather_service import WeatherService, get_weather_service
from backend.services.cache_service import CacheService, get_cache_service

__all__ = [
    "BaseService",
    "ServiceException",
    "InMemoryCache",
    "get_memory_cache",
    "GeoService",
    "get_geo_service",
    "PlacesService",
    "get_places_service",
    "RoutingService",
    "get_routing_service",
    "WeatherService",
    "get_weather_service",
    "CacheService",
    "get_cache_service",
]
