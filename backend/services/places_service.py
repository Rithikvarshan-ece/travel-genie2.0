"""
TravelGenie Places Service

Search for nearby places using Overpass API (OpenStreetMap).
Features:
- Search hotels, restaurants, attractions
- Search museums, parks, hospitals, fuel stations, shops
- Filtering by distance and category
- Caching results
"""

import logging
from typing import List, Optional, Dict, Any
from enum import Enum
import httpx
from backend.services.base_service import BaseService, ServiceException, get_memory_cache
from backend.models import Attraction, Location
from backend.config import get_settings

logger = logging.getLogger(__name__)


class PlaceCategory(str, Enum):
    """Categories of places to search."""
    HOTELS = "hotels"
    RESTAURANTS = "restaurants"
    ATTRACTIONS = "attractions"
    MUSEUMS = "museums"
    PARKS = "parks"
    HOSPITALS = "hospitals"
    FUEL = "fuel_stations"
    SHOPPING = "shopping"


class PlacesService(BaseService):
    """
    Places search service using Overpass API (OpenStreetMap).
    
    Provides:
    - Searching for hotels, restaurants, attractions
    - Searching for museums, parks, hospitals, fuel stations, shops
    - Results filtered by distance
    - Caching of results
    """

    # Overpass API queries for different categories
    OSM_QUERIES = {
        PlaceCategory.HOTELS: """
            [bbox:{{bbox}}];
            (node[tourism=hotel];way[tourism=hotel];relation[tourism=hotel];);
            out center;
        """,
        PlaceCategory.RESTAURANTS: """
            [bbox:{{bbox}}];
            (node[amenity=restaurant];way[amenity=restaurant];);
            out center;
        """,
        PlaceCategory.ATTRACTIONS: """
            [bbox:{{bbox}}];
            (node[tourism=attraction];way[tourism=attraction];);
            out center;
        """,
        PlaceCategory.MUSEUMS: """
            [bbox:{{bbox}}];
            (node[tourism=museum];way[tourism=museum];);
            out center;
        """,
        PlaceCategory.PARKS: """
            [bbox:{{bbox}}];
            (node[leisure=park];way[leisure=park];);
            out center;
        """,
        PlaceCategory.HOSPITALS: """
            [bbox:{{bbox}}];
            (node[amenity=hospital];way[amenity=hospital];);
            out center;
        """,
        PlaceCategory.FUEL: """
            [bbox:{{bbox}}];
            (node[amenity=fuel];way[amenity=fuel];);
            out center;
        """,
        PlaceCategory.SHOPPING: """
            [bbox:{{bbox}}];
            (node[shop];way[shop];);
            out center;
        """,
    }

    def __init__(self):
        """Initialize Places Service."""
        settings = get_settings()
        super().__init__(
            name="Places",
            base_url=settings.overpass_api_url,
        )
        self.cache = get_memory_cache()

    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        category: PlaceCategory,
        radius_km: float = 5.0,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for places near a location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            category: Place category to search for
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return
            
        Returns:
            List of place dictionaries with name, location, rating, etc.
            
        Raises:
            ServiceException: If search fails
        """
        # Check cache first
        cache_key = f"places:{category.value}:{latitude:.4f}:{longitude:.4f}:{radius_km}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached[:max_results]

        try:
            results = await self.retry_with_backoff(
                self._search_nearby_internal,
                latitude,
                longitude,
                category,
                radius_km,
                operation_name=f"Search {category.value} near ({latitude:.4f}, {longitude:.4f})",
            )
            
            # Cache full results
            self.cache.set(cache_key, results, ttl_minutes=self.settings.cache_ttl_minutes)
            
            return results[:max_results]
        except Exception as e:
            self.logger.error(f"Places search failed: {e}")
            raise ServiceException(self.name, f"Failed to search for {category.value}", e)

    async def _search_nearby_internal(
        self,
        latitude: float,
        longitude: float,
        category: PlaceCategory,
        radius_km: float,
    ) -> List[Dict[str, Any]]:
        """
        Internal implementation of nearby search using Overpass API.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            category: Place category
            radius_km: Search radius in km
            
        Returns:
            List of places
        """
        # Convert radius to bounding box (simplified)
        # 1 degree ≈ 111 km
        lat_delta = radius_km / 111.0
        lon_delta = lat_delta / abs(__import__("math").cos(__import__("math").radians(latitude)))
        
        bbox = f"{latitude - lat_delta},{longitude - lon_delta},{latitude + lat_delta},{longitude + lon_delta}"

        # Get Overpass query template
        query_template = self.OSM_QUERIES.get(category)
        if not query_template:
            raise ValueError(f"Unknown place category: {category}")

        # Format query with bbox
        query = query_template.format(bbox=bbox)

        client = await self.get_http_client()
        
        data = {
            "data": query,
        }

        response = await client.post(
            self.base_url,
            data={"data": query},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.settings.overpass_timeout,
        )
        response.raise_for_status()

        # Parse OSM response
        osm_data = response.json()
        results = []

        for element in osm_data.get("elements", []):
            place_name = element.get("tags", {}).get("name", f"{category.value} location")
            
            # Get coordinates
            if "center" in element:
                lat = element["center"]["lat"]
                lon = element["center"]["lon"]
            elif "lat" in element and "lon" in element:
                lat = element["lat"]
                lon = element["lon"]
            else:
                continue

            # Basic place info
            place_info = {
                "name": place_name,
                "latitude": lat,
                "longitude": lon,
                "category": category.value,
                "rating": element.get("tags", {}).get("rating", 0),
                "opening_hours": element.get("tags", {}).get("opening_hours", None),
                "website": element.get("tags", {}).get("website", None),
                "phone": element.get("tags", {}).get("phone", None),
            }

            results.append(place_info)

        return sorted(results, key=lambda x: x.get("rating", 0), reverse=True)

    async def search_hotels(
        self,
        latitude: float,
        longitude: float,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels near a location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            max_results: Maximum number of results
            
        Returns:
            List of hotels
        """
        return await self.search_nearby(
            latitude, longitude, PlaceCategory.HOTELS, radius_km=3.0, max_results=max_results
        )

    async def search_restaurants(
        self,
        latitude: float,
        longitude: float,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for restaurants near a location."""
        return await self.search_nearby(
            latitude, longitude, PlaceCategory.RESTAURANTS, radius_km=2.0, max_results=max_results
        )

    async def search_attractions(
        self,
        latitude: float,
        longitude: float,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for attractions near a location."""
        return await self.search_nearby(
            latitude, longitude, PlaceCategory.ATTRACTIONS, radius_km=5.0, max_results=max_results
        )

    async def search_museums(
        self,
        latitude: float,
        longitude: float,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for museums near a location."""
        return await self.search_nearby(
            latitude, longitude, PlaceCategory.MUSEUMS, radius_km=5.0, max_results=max_results
        )

    async def search_parks(
        self,
        latitude: float,
        longitude: float,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for parks near a location."""
        return await self.search_nearby(
            latitude, longitude, PlaceCategory.PARKS, radius_km=3.0, max_results=max_results
        )

    async def health_check(self) -> bool:
        """
        Check if Overpass API is accessible.
        
        Returns:
            True if service is healthy
        """
        try:
            client = await self.get_http_client()
            # Simple status check
            response = await client.get(
                "https://overpass-api.de/api/status",
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False


# Global Places service instance
_places_service: Optional[PlacesService] = None


def get_places_service() -> PlacesService:
    """
    Get or create the global Places service instance.
    
    Returns:
        PlacesService instance
    """
    global _places_service
    if _places_service is None:
        _places_service = PlacesService()
    return _places_service
