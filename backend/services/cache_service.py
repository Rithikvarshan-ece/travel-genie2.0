"""
TravelGenie Cache Service

Caching layer for API responses with MongoDB/SQLite support.
Features:
- MongoDB caching if available
- SQLite fallback
- 30-minute TTL
- Automatic cache invalidation
"""

import logging
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from backend.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service for storing API responses.
    
    Uses MongoDB if configured, falls back to SQLite.
    All cached entries expire after 30 minutes.
    """

    def __init__(self):
        """Initialize Cache Service."""
        self.settings = get_settings()
        self.name = "Cache"
        self.logger = logging.getLogger(f"service.{self.name}")
        self.ttl_minutes = self.settings.cache_ttl_minutes
        self._use_mongodb = bool(self.settings.mongodb_url)
        self._mongo_client = None
        self._db = None
        
        if self._use_mongodb:
            self._init_mongodb()
        else:
            self._init_sqlite()
        
        self.logger.info("CacheService initialized")

    def _init_mongodb(self):
        """Initialize MongoDB connection."""
        try:
            from pymongo import MongoClient
            self._mongo_client = MongoClient(self.settings.mongodb_url, serverSelectionTimeoutMS=5000)
            self._db = self._mongo_client[self.settings.mongodb_database]
            # Create TTL index
            self._db.cache.create_index(
                "created_at",
                expireAfterSeconds=self.ttl_minutes * 60
            )
            self.logger.info("MongoDB cache initialized")
        except Exception as e:
            self.logger.warning(f"Warning MongoDB initialization failed: {e}, using SQLite fallback")
            self._use_mongodb = False
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite fallback cache."""
        try:
            import sqlite3
            self._sqlite_conn = sqlite3.connect(":memory:")
            self._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            self._sqlite_conn.commit()
            self.logger.info("SQLite cache initialized")
        except Exception as e:
            self.logger.error(f"Error SQLite cache initialization failed: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        try:
            if self._use_mongodb:
                return await self._get_mongodb(key)
            else:
                return self._get_sqlite(key)
        except Exception as e:
            self.logger.error(f"Cache get failed for {key}: {e}")
            return None

    async def _get_mongodb(self, key: str) -> Optional[Any]:
        """Get from MongoDB cache."""
        try:
            doc = self._db.cache.find_one({"_id": key})
            if doc:
                self.logger.debug(f"Cache hit: {key}")
                return json.loads(doc["value"])
            return None
        except Exception as e:
            self.logger.warning(f"MongoDB get failed: {e}")
            return None

    def _get_sqlite(self, key: str) -> Optional[Any]:
        """Get from SQLite cache."""
        try:
            cursor = self._sqlite_conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > datetime('now')",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                self.logger.debug(f"Cache hit: {key}")
                return json.loads(row[0])
            return None
        except Exception as e:
            self.logger.warning(f"SQLite get failed: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl_minutes: Time-to-live in minutes (defaults to configured TTL)
        """
        ttl = ttl_minutes or self.ttl_minutes
        
        try:
            if self._use_mongodb:
                await self._set_mongodb(key, value, ttl)
            else:
                self._set_sqlite(key, value, ttl)
        except Exception as e:
            self.logger.error(f"Cache set failed for {key}: {e}")

    async def _set_mongodb(self, key: str, value: Any, ttl_minutes: int) -> None:
        """Set in MongoDB cache."""
        try:
            self._db.cache.replace_one(
                {"_id": key},
                {
                    "_id": key,
                    "value": json.dumps(value, default=str),
                    "created_at": datetime.utcnow(),
                },
                upsert=True
            )
            self.logger.debug(f"Cache set: {key} (TTL={ttl_minutes}m)")
        except Exception as e:
            self.logger.warning(f"MongoDB set failed: {e}")

    def _set_sqlite(self, key: str, value: Any, ttl_minutes: int) -> None:
        """Set in SQLite cache."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            self._sqlite_conn.execute(
                """INSERT OR REPLACE INTO cache (key, value, created_at, expires_at)
                   VALUES (?, ?, datetime('now'), ?)""",
                (key, json.dumps(value, default=str), expires_at)
            )
            self._sqlite_conn.commit()
            self.logger.debug(f"Cache set: {key} (TTL={ttl_minutes}m)")
        except Exception as e:
            self.logger.warning(f"SQLite set failed: {e}")

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        try:
            if self._use_mongodb:
                self._db.cache.delete_one({"_id": key})
            else:
                self._sqlite_conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                self._sqlite_conn.commit()
            
            self.logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            self.logger.warning(f"Cache delete failed: {e}")

    async def clear(self) -> None:
        """Clear entire cache."""
        try:
            if self._use_mongodb:
                self._db.cache.delete_many({})
            else:
                self._sqlite_conn.execute("DELETE FROM cache")
                self._sqlite_conn.commit()
            
            self.logger.info("Cache cleared")
        except Exception as e:
            self.logger.warning(f"Cache clear failed: {e}")

    async def health_check(self) -> bool:
        """
        Check if cache service is healthy.
        
        Returns:
            True if cache is healthy
        """
        try:
            test_key = "__health_check__"
            await self.set(test_key, {"status": "ok"}, ttl_minutes=1)
            result = await self.get(test_key)
            await self.delete(test_key)
            return result is not None
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    def __repr__(self) -> str:
        """String representation."""
        backend = "MongoDB" if self._use_mongodb else "SQLite"
        return f"<CacheService(backend={backend}, ttl={self.ttl_minutes}m)>"

    def __del__(self):
        """Cleanup connections."""
        try:
            if self._use_mongodb and self._mongo_client:
                self._mongo_client.close()
            elif hasattr(self, '_sqlite_conn'):
                self._sqlite_conn.close()
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")


# Global Cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get or create the global Cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
