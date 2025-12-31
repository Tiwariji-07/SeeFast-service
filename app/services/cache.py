"""
Cache Service
=============

Redis-based caching for API responses and session data.

Features:
- API response caching with TTL
- Fallback to in-memory cache if Redis unavailable
"""

import redis
import json
from typing import Any, Optional
import hashlib

from app.config import settings


class CacheService:
    """Redis-based cache with in-memory fallback."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._memory_cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry)
        self._connected = False
        self._connect()
    
    def _connect(self):
        """Try to connect to Redis."""
        try:
            self._redis = redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
            self._redis.ping()
            self._connected = True
            print(f"✅ Connected to Redis at {settings.redis_url}")
        except Exception as e:
            print(f"⚠️ Redis unavailable ({e}), using in-memory cache")
            self._connected = False
            self._redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if self._connected and self._redis:
            try:
                value = self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        
        # Fallback to memory
        if key in self._memory_cache:
            value, _ = self._memory_cache[key]
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a value in cache with TTL."""
        ttl = ttl or settings.redis_ttl
        
        if self._connected and self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value))
                return True
            except Exception:
                pass
        
        # Fallback to memory (no TTL tracking for simplicity)
        self._memory_cache[key] = (value, 0)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if self._connected and self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        return True
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        count = 0
        if self._connected and self._redis:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    count = self._redis.delete(*keys)
            except Exception:
                pass
        
        return count
    
    @staticmethod
    def make_key(*parts) -> str:
        """Create a cache key from parts."""
        key_string = ":".join(str(p) for p in parts)
        return f"seefast:{key_string}"
    
    @staticmethod
    def hash_params(params: dict) -> str:
        """Create a hash of parameters for cache keys."""
        return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:10]


# Singleton
_cache: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get or create cache singleton."""
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
