"""
TravelGenie Geo Service

Geocoding and reverse geocoding using Nominatim (OpenStreetMap).
Features:
- Geocode locations (convert place name to coordinates)
- Reverse geocode (convert coordinates to place name)
- Location validation
- Caching
"""

import logging
from typing import Optional, Dict, Any, Tuple
import httpx
from backend.services.base_service import BaseService, ServiceException, get_memory_cache
from backend.models import Location
from backend.config import get_settings

logger = logging.getLogger(__name__)


class GeoService(BaseService):
    """
    Geocoding service using Nominatim (OpenStreetMap).
    
    Provides:
    - Geocoding (place name → coordinates)
    - Reverse geocoding (coordinates → place name)
    - Location validation and formatting
    """

    FALLBACK_LOCATIONS = {
        "paris": {"latitude": 48.8566, "longitude": 2.3522, "city": "Paris", "country": "France", "region": "Île-de-France"},
        "venice": {"latitude": 45.4408, "longitude": 12.3155, "city": "Venice", "country": "Italy", "region": "Veneto"},
        "bali": {"latitude": -8.3405, "longitude": 115.0920, "city": "Bali", "country": "Indonesia", "region": "Bali"},
        "santorini": {"latitude": 36.3932, "longitude": 25.4615, "city": "Santorini", "country": "Greece", "region": "South Aegean"},
        "kyoto": {"latitude": 35.0116, "longitude": 135.7681, "city": "Kyoto", "country": "Japan", "region": "Kansai"},
        "orlando": {"latitude": 28.5383, "longitude": -81.3792, "city": "Orlando", "country": "United States", "region": "Florida"},
        "tokyo": {"latitude": 35.6762, "longitude": 139.6503, "city": "Tokyo", "country": "Japan", "region": "Kanto"},
        "singapore": {"latitude": 1.3521, "longitude": 103.8198, "city": "Singapore", "country": "Singapore", "region": "Singapore"},
        "barcelona": {"latitude": 41.3851, "longitude": 2.1734, "city": "Barcelona", "country": "Spain", "region": "Catalonia"},
        "sydney": {"latitude": -33.8688, "longitude": 151.2093, "city": "Sydney", "country": "Australia", "region": "New South Wales"},
        "bangkok": {"latitude": 13.7563, "longitude": 100.5018, "city": "Bangkok", "country": "Thailand", "region": "Bangkok"},
        "berlin": {"latitude": 52.5200, "longitude": 13.4050, "city": "Berlin", "country": "Germany", "region": "Berlin"},
        "lisbon": {"latitude": 38.7223, "longitude": -9.1393, "city": "Lisbon", "country": "Portugal", "region": "Lisbon"},
        "prague": {"latitude": 50.0755, "longitude": 14.4378, "city": "Prague", "country": "Czech Republic", "region": "Bohemia"},
        "chiang mai": {"latitude": 18.7883, "longitude": 98.9853, "city": "Chiang Mai", "country": "Thailand", "region": "Chiang Mai"},
        "budapest": {"latitude": 47.4979, "longitude": 19.0402, "city": "Budapest", "country": "Hungary", "region": "Central Hungary"},
        "seoul": {"latitude": 37.5665, "longitude": 126.9780, "city": "Seoul", "country": "South Korea", "region": "Seoul"},
        "rome": {"latitude": 41.9028, "longitude": 12.4964, "city": "Rome", "country": "Italy", "region": "Lazio"},
        "new zealand": {"latitude": -40.9006, "longitude": 174.8860, "city": "New Zealand", "country": "New Zealand", "region": ""},
        "costa rica": {"latitude": 9.7489, "longitude": -83.7534, "city": "Costa Rica", "country": "Costa Rica", "region": ""},
        "iceland": {"latitude": 64.9631, "longitude": -19.0208, "city": "Iceland", "country": "Iceland", "region": ""},
        "nepal": {"latitude": 28.3949, "longitude": 84.1240, "city": "Nepal", "country": "Nepal", "region": ""},
        "peru": {"latitude": -9.189967, "longitude": -75.015152, "city": "Peru", "country": "Peru", "region": ""},
        "queenstown": {"latitude": -45.0312, "longitude": 168.6626, "city": "Queenstown", "country": "New Zealand", "region": "Otago"},
        "istanbul": {"latitude": 41.0082, "longitude": 28.9784, "city": "Istanbul", "country": "Turkey", "region": "Marmara"},
        "lima": {"latitude": -12.0464, "longitude": -77.0428, "city": "Lima", "country": "Peru", "region": "Lima"},
        "dubai": {"latitude": 25.2048, "longitude": 55.2708, "city": "Dubai", "country": "United Arab Emirates", "region": "Dubai"},
        "miami": {"latitude": 25.7617, "longitude": -80.1918, "city": "Miami", "country": "United States", "region": "Florida"},
        "ho chi minh city": {"latitude": 10.8231, "longitude": 106.6297, "city": "Ho Chi Minh City", "country": "Vietnam", "region": "Ho Chi Minh"},
    }

    def __init__(self):
        """Initialize Geo Service."""
        settings = get_settings()
        super().__init__(
            name="Geo",
            base_url=settings.nominatim_base_url,
        )
        self.cache = get_memory_cache()

    async def geocode(self, location_query: str) -> Location:
        """
        Convert a location name to coordinates.
        
        Args:
            location_query: Location name (city, address, etc.)
            
        Returns:
            Location object with coordinates
            
        Raises:
            ServiceException: If geocoding fails
        """
        # Check cache first
        cache_key = f"geocode:{location_query.lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await self.retry_with_backoff(
                self._geocode_internal,
                location_query,
                operation_name=f"Geocode '{location_query}'",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=self.settings.cache_ttl_minutes)
            
            return result
        except Exception as e:
            self.logger.error(f"Geocoding failed for '{location_query}': {e}")
            fallback = self._get_fallback_location(location_query)
            if fallback:
                self.logger.warning(f"Using fallback geocode for '{location_query}'")
                return fallback
            raise ServiceException(self.name, f"Failed to geocode '{location_query}'", e)

    def _get_fallback_location(self, location_query: str) -> Optional[Location]:
        """
        Return a fallback location for known popular destinations.
        """
        normalized = location_query.strip().lower()
        data = self.FALLBACK_LOCATIONS.get(normalized)
        if not data:
            return None
        return Location(
            latitude=data["latitude"],
            longitude=data["longitude"],
            city=data["city"],
            country=data["country"],
            region=data.get("region"),
        )

    async def _geocode_internal(self, location_query: str) -> Location:
        """
        Internal geocoding implementation.
        
        Args:
            location_query: Location name
            
        Returns:
            Location object
        """
        client = await self.get_http_client()
        
        url = f"{self.base_url}/search"
        params = {
            "q": location_query,
            "format": "json",
            "limit": 1,
        }

        response = await client.get(url, params=params, timeout=self.settings.nominatim_timeout)
        response.raise_for_status()

        data = response.json()
        
        if not data:
            raise ValueError(f"No results found for '{location_query}'")

        result = data[0]
        
        return Location(
            latitude=float(result["lat"]),
            longitude=float(result["lon"]),
            city=result.get("name", location_query),
            country=result.get("address", {}).get("country", "Unknown"),
            region=result.get("address", {}).get("state", None),
        )

    async def reverse_geocode(self, latitude: float, longitude: float) -> Location:
        """
        Convert coordinates to location name.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Location object with place names
            
        Raises:
            ServiceException: If reverse geocoding fails
        """
        # Check cache first
        cache_key = f"reverse_geocode:{latitude:.4f}:{longitude:.4f}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await self.retry_with_backoff(
                self._reverse_geocode_internal,
                latitude,
                longitude,
                operation_name=f"Reverse geocode ({latitude:.4f}, {longitude:.4f})",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=self.settings.cache_ttl_minutes)
            
            return result
        except Exception as e:
            self.logger.error(f"Reverse geocoding failed: {e}")
            raise ServiceException(self.name, f"Failed to reverse geocode coordinates", e)

    async def _reverse_geocode_internal(self, latitude: float, longitude: float) -> Location:
        """
        Internal reverse geocoding implementation.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Location object
        """
        client = await self.get_http_client()
        
        url = f"{self.base_url}/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
        }

        response = await client.get(url, params=params, timeout=self.settings.nominatim_timeout)
        response.raise_for_status()

        data = response.json()
        address = data.get("address", {})

        return Location(
            latitude=latitude,
            longitude=longitude,
            city=address.get("city", address.get("town", "Unknown")),
            country=address.get("country", "Unknown"),
            region=address.get("state", None),
        )

    async def validate_location(self, latitude: float, longitude: float) -> bool:
        """
        Validate if coordinates are valid.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            True if coordinates are valid
        """
        try:
            if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                return True
        except (TypeError, ValueError):
            pass
        return False

    async def calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate approximate distance between two points (in km).
        Uses Haversine formula for rough estimation.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    async def health_check(self) -> bool:
        """
        Check if Nominatim service is accessible.
        
        Returns:
            True if service is healthy
        """
        try:
            client = await self.get_http_client()
            response = await client.get(
                f"{self.base_url}/search",
                params={"q": "New York", "format": "json"},
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False


# Global Geo service instance
_geo_service: Optional[GeoService] = None


def get_geo_service() -> GeoService:
    """
    Get or create the global Geo service instance.
    
    Returns:
        GeoService instance
    """
    global _geo_service
    if _geo_service is None:
        _geo_service = GeoService()
    return _geo_service
