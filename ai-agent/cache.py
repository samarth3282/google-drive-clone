"""
Simple in-memory caching layer for frequently accessed data.
For production, consider using Redis or Memcached.
"""
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
import json

class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
    
    def _is_expired(self, expiry: float) -> bool:
        """Check if cache entry has expired."""
        return time.time() > expiry
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if not self._is_expired(expiry):
                return value
            else:
                # Clean up expired entry
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete entry from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            del self._cache[key]

# Global cache instances
file_content_cache = SimpleCache(default_ttl=600)  # 10 minutes for file content
search_results_cache = SimpleCache(default_ttl=300)  # 5 minutes for search results
vector_cache = SimpleCache(default_ttl=1800)  # 30 minutes for vectors

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a stable string representation
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(cache: SimpleCache, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        cache: Cache instance to use
        ttl: Time-to-live for cached value (uses cache default if None)
        key_prefix: Prefix to add to cache key
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user."""
    # In a simple implementation, we clear related caches
    # In production, use more sophisticated cache key patterns
    search_results_cache.cleanup_expired()
    file_content_cache.cleanup_expired()
    vector_cache.cleanup_expired()
