"""In-memory cache manager for query results and schema data."""

import time
from typing import Any, Optional, Dict
from dataclasses import dataclass, field

from ..config.settings import CacheConfig


@dataclass
class CacheEntry:
    """A single cache entry with TTL tracking."""

    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: float = 300  # 5 minutes default


class CacheManager:
    """In-memory cache manager with TTL support.

    Provides separate caches for different categories (queries, schema)
    with configurable TTL per category.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager.

        Args:
            config: Cache configuration. Uses defaults if not provided.
        """
        self.config = config or CacheConfig()
        self._enabled = self.config.enabled

        # Separate caches for different data types
        self._query_cache: Dict[str, CacheEntry] = {}
        self._schema_cache: Dict[str, CacheEntry] = {}

        # TTL settings (in seconds)
        self._query_ttl = self.config.query_ttl_minutes * 60
        self._schema_ttl = self.config.schema_ttl_minutes * 60

    def get(self, key: str, category: str = "query") -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key.
            category: Cache category ('query' or 'schema').

        Returns:
            Cached value if found and not expired, None otherwise.
        """
        if not self._enabled:
            return None

        cache = self._get_cache(category)
        entry = cache.get(key)

        if entry is None:
            return None

        # Check if expired
        if self._is_expired(entry):
            del cache[key]
            return None

        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        category: str = "query",
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """Store a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            category: Cache category ('query' or 'schema').
            ttl_seconds: Optional custom TTL. Uses category default if not specified.
        """
        if not self._enabled:
            return

        cache = self._get_cache(category)
        ttl = ttl_seconds or self._get_default_ttl(category)

        cache[key] = CacheEntry(value=value, ttl_seconds=ttl)

        # Periodic cleanup
        if len(cache) > 100:
            self._cleanup(category)

    def delete(self, key: str, category: str = "query") -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key.
            category: Cache category.

        Returns:
            True if key was found and deleted.
        """
        cache = self._get_cache(category)
        if key in cache:
            del cache[key]
            return True
        return False

    def clear(self, category: Optional[str] = None) -> None:
        """Clear cache entries.

        Args:
            category: Specific category to clear. Clears all if not specified.
        """
        if category is None:
            self._query_cache.clear()
            self._schema_cache.clear()
        elif category == "query":
            self._query_cache.clear()
        elif category == "schema":
            self._schema_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        return {
            "enabled": self._enabled,
            "query_entries": len(self._query_cache),
            "schema_entries": len(self._schema_cache),
            "query_ttl_minutes": self.config.query_ttl_minutes,
            "schema_ttl_minutes": self.config.schema_ttl_minutes,
        }

    def _get_cache(self, category: str) -> Dict[str, CacheEntry]:
        """Get the cache dictionary for a category.

        Args:
            category: Cache category.

        Returns:
            Cache dictionary.
        """
        if category == "schema":
            return self._schema_cache
        return self._query_cache

    def _get_default_ttl(self, category: str) -> float:
        """Get default TTL for a category.

        Args:
            category: Cache category.

        Returns:
            TTL in seconds.
        """
        if category == "schema":
            return self._schema_ttl
        return self._query_ttl

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired.

        Args:
            entry: Cache entry to check.

        Returns:
            True if expired.
        """
        age = time.time() - entry.created_at
        return age > entry.ttl_seconds

    def _cleanup(self, category: str) -> None:
        """Remove expired entries from cache.

        Args:
            category: Cache category to clean.
        """
        cache = self._get_cache(category)
        expired_keys = [
            key for key, entry in cache.items() if self._is_expired(entry)
        ]
        for key in expired_keys:
            del cache[key]
