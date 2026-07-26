"""
TravelGenie Routing Service

Route optimization and travel time calculation using OSRM (Open Source Routing Machine).
Features:
- Calculate distance between two points
- Get travel time
- Optimize route with multiple waypoints
- Support different transportation modes
- Caching
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import httpx
from backend.services.base_service import BaseService, ServiceException, get_memory_cache
from backend.config import get_settings

logger = logging.getLogger(__name__)


class TransportMode(str, Enum):
    """Supported transportation modes for routing."""
    CAR = "car"
    BIKE = "bike"
    FOOT = "foot"


class RoutingService(BaseService):
    """
    Routing and distance calculation service using OSRM.
    
    Provides:
    - Distance calculation between points
    - Travel time estimation
    - Route optimization (TSP)
    - Support for multiple transportation modes
    """

    def __init__(self):
        """Initialize Routing Service."""
        settings = get_settings()
        super().__init__(
            name="Routing",
            base_url=settings.osrm_base_url,
        )
        self.cache = get_memory_cache()

    async def calculate_distance_and_time(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: TransportMode = TransportMode.CAR,
    ) -> Dict[str, Any]:
        """
        Calculate distance and travel time between two points.
        
        Args:
            start_lat: Start latitude
            start_lon: Start longitude
            end_lat: End latitude
            end_lon: End longitude
            mode: Transportation mode
            
        Returns:
            Dictionary with distance (km) and duration (hours)
            
        Raises:
            ServiceException: If calculation fails
        """
        # Check cache first
        cache_key = f"route:{mode.value}:{start_lat:.4f}:{start_lon:.4f}:{end_lat:.4f}:{end_lon:.4f}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await self.retry_with_backoff(
                self._calculate_internal,
                start_lat,
                start_lon,
                end_lat,
                end_lon,
                mode,
                operation_name=f"Calculate route ({start_lat:.4f},{start_lon:.4f}) → ({end_lat:.4f},{end_lon:.4f})",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=self.settings.cache_ttl_minutes)
            
            return result
        except Exception as e:
            self.logger.error(f"Route calculation failed: {e}")
            raise ServiceException(self.name, "Failed to calculate route", e)

    async def _calculate_internal(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: TransportMode,
    ) -> Dict[str, Any]:
        """
        Internal route calculation implementation.
        
        Args:
            start_lat, start_lon: Start coordinates
            end_lat, end_lon: End coordinates
            mode: Transportation mode
            
        Returns:
            Route data with distance and duration
        """
        client = await self.get_http_client()

        # OSRM format: longitude,latitude (note the order!)
        coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
        
        url = f"{self.base_url}/route/v1/{mode.value}/{coordinates}"
        params = {
            "overview": "simplified",
            "steps": "false",
        }

        response = await client.get(url, params=params, timeout=self.settings.osrm_timeout)
        response.raise_for_status()

        data = response.json()
        
        if data.get("code") != "Ok":
            raise ValueError(f"OSRM returned error: {data.get('message')}")

        route = data.get("routes", [{}])[0]
        
        # OSRM returns distance in meters and duration in seconds
        distance_km = route.get("distance", 0) / 1000.0
        duration_hours = route.get("duration", 0) / 3600.0

        return {
            "distance_km": distance_km,
            "duration_hours": duration_hours,
            "mode": mode.value,
        }

    async def optimize_route(
        self,
        waypoints: List[Tuple[float, float]],
        mode: TransportMode = TransportMode.CAR,
    ) -> Dict[str, Any]:
        """
        Optimize route through multiple waypoints (traveling salesman problem).
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode
            
        Returns:
            Optimized waypoint order and total distance/duration
            
        Raises:
            ServiceException: If optimization fails
        """
        if len(waypoints) < 2:
            raise ValueError("Need at least 2 waypoints")

        if len(waypoints) > 25:
            self.logger.warning(f"Too many waypoints ({len(waypoints)}), capping at 25")
            waypoints = waypoints[:25]

        # Check cache
        cache_key = f"optimize:{mode.value}:{len(waypoints)}:{hash(tuple(waypoints))}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await self.retry_with_backoff(
                self._optimize_internal,
                waypoints,
                mode,
                operation_name=f"Optimize route with {len(waypoints)} waypoints",
            )
            
            # Cache result
            self.cache.set(cache_key, result, ttl_minutes=self.settings.cache_ttl_minutes)
            
            return result
        except Exception as e:
            self.logger.error(f"Route optimization failed: {e}")
            raise ServiceException(self.name, "Failed to optimize route", e)

    async def _optimize_internal(
        self,
        waypoints: List[Tuple[float, float]],
        mode: TransportMode,
    ) -> Dict[str, Any]:
        """
        Internal route optimization implementation.
        
        Args:
            waypoints: List of waypoints as (lat, lon) tuples
            mode: Transportation mode
            
        Returns:
            Optimized route data
        """
        client = await self.get_http_client()

        # Convert to OSRM format (lon,lat order)
        coordinates = ";".join([f"{lon},{lat}" for lat, lon in waypoints])
        
        url = f"{self.base_url}/trip/v1/{mode.value}/{coordinates}"
        params = {
            "overview": "simplified",
            "steps": "false",
        }

        response = await client.get(url, params=params, timeout=self.settings.osrm_timeout)
        response.raise_for_status()

        data = response.json()
        
        if data.get("code") != "Ok":
            raise ValueError(f"OSRM returned error: {data.get('message')}")

        # Parse optimized order
        waypoint_order = data.get("waypoints", [])
        ordered_waypoints = [waypoints[wp["waypoint_index"]] for wp in waypoint_order]

        # Sum all route segments
        total_distance_km = 0
        total_duration_hours = 0
        
        for route in data.get("routes", []):
            total_distance_km += route.get("distance", 0) / 1000.0
            total_duration_hours += route.get("duration", 0) / 3600.0

        return {
            "optimized_waypoints": ordered_waypoints,
            "waypoint_order": [wp["waypoint_index"] for wp in waypoint_order],
            "total_distance_km": total_distance_km,
            "total_duration_hours": total_duration_hours,
            "mode": mode.value,
        }

    async def get_travel_time_hours(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: TransportMode = TransportMode.CAR,
    ) -> float:
        """
        Get travel time in hours between two points.
        
        Args:
            start_lat, start_lon: Start coordinates
            end_lat, end_lon: End coordinates
            mode: Transportation mode
            
        Returns:
            Travel time in hours
        """
        result = await self.calculate_distance_and_time(
            start_lat, start_lon, end_lat, end_lon, mode
        )
        return result["duration_hours"]

    async def get_distance(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        mode: TransportMode = TransportMode.CAR,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper to get distance and travel time between two points.
        """
        return await self.calculate_distance_and_time(
            start[0], start[1], end[0], end[1], mode
        )

    async def get_distance_km(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: TransportMode = TransportMode.CAR,
    ) -> float:
        """
        Get distance in km between two points.
        
        Args:
            start_lat, start_lon: Start coordinates
            end_lat, end_lon: End coordinates
            mode: Transportation mode
            
        Returns:
            Distance in kilometers
        """
        result = await self.calculate_distance_and_time(
            start_lat, start_lon, end_lat, end_lon, mode
        )
        return result["distance_km"]

    async def health_check(self) -> bool:
        """
        Check if OSRM service is accessible.
        
        Returns:
            True if service is healthy
        """
        try:
            client = await self.get_http_client()
            # Test with simple route
            response = await client.get(
                f"{self.base_url}/route/v1/car/13.3887,52.5170;13.3891,52.5172",
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False


# Global Routing service instance
_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """
    Get or create the global Routing service instance.
    
    Returns:
        RoutingService instance
    """
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
