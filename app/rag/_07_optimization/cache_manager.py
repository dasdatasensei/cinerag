"""
Cache Manager

High-performance caching system for RAG pipeline optimization.
Includes search result caching, embedding caching, and performance monitoring.
"""

import logging
import time
import json
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from collections import defaultdict, OrderedDict
import os

# Optional Redis import
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def size_mb(self) -> float:
        """Cache size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)


class LRUCache:
    """
    High-performance LRU cache with TTL support and size limits.

    Features:
    - Least Recently Used eviction
    - Time-to-live (TTL) expiration
    - Memory size limits
    - Thread-safe operations
    - Performance monitoring
    """

    def __init__(
        self, max_size: int = 1000, max_memory_mb: int = 100, default_ttl: int = 3600
    ):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl

        self._cache = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()

        # Background cleanup
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            # Check if key exists
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check TTL expiration
            current_time = time.time()
            if entry.ttl and (current_time - entry.created_at) > entry.ttl:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._update_size_stats()
                return None

            # Update access info and move to end (most recent)
            entry.last_accessed = current_time
            entry.access_count += 1
            self._cache.move_to_end(key)

            self._stats.hits += 1

            # Periodic cleanup
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_expired()

            return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in cache."""
        with self._lock:
            current_time = time.time()

            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                # Fallback size estimation
                size_bytes = len(str(value).encode("utf-8"))

            # Check memory limit
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Item too large for cache: {size_bytes} bytes")
                return False

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                last_accessed=current_time,
                ttl=ttl or self.default_ttl,
                size_bytes=size_bytes,
            )

            # Remove old entry if exists
            if key in self._cache:
                del self._cache[key]

            # Evict items if necessary
            self._evict_if_needed(entry.size_bytes)

            # Add new entry
            self._cache[key] = entry
            self._update_size_stats()

            return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._update_size_stats()
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._update_size_stats()
            return self._stats

    def _evict_if_needed(self, new_item_size: int) -> None:
        """Evict items if cache limits would be exceeded."""
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_lru()

        # Check memory limit
        current_size = sum(entry.size_bytes for entry in self._cache.values())
        while current_size + new_item_size > self.max_memory_bytes and self._cache:
            evicted_size = self._evict_lru()
            current_size -= evicted_size

    def _evict_lru(self) -> int:
        """Evict least recently used item."""
        if not self._cache:
            return 0

        # Remove oldest (LRU) item
        oldest_key, oldest_entry = self._cache.popitem(last=False)
        self._stats.evictions += 1

        logger.debug(f"Evicted cache entry: {oldest_key}")
        return oldest_entry.size_bytes

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = []

        for key, entry in self._cache.items():
            if entry.ttl and (current_time - entry.created_at) > entry.ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1

        self._last_cleanup = current_time

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _update_size_stats(self) -> None:
        """Update size statistics."""
        self._stats.entry_count = len(self._cache)
        self._stats.total_size_bytes = sum(
            entry.size_bytes for entry in self._cache.values()
        )


class RedisCache:
    """
    Redis-based cache for persistent and distributed caching.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "cinerag:",
    ):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for namespacing
        """
        self.prefix = prefix
        self._stats = CacheStats()

        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available. Install with: pip install redis")

        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # We'll handle encoding manually
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            redis_key = f"{self.prefix}{key}"
            data = self.redis_client.get(redis_key)

            if data is None:
                self._stats.misses += 1
                return None

            # Deserialize
            value = pickle.loads(data)
            self._stats.hits += 1

            return value

        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            self._stats.misses += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in Redis cache."""
        try:
            redis_key = f"{self.prefix}{key}"

            # Serialize
            data = pickle.dumps(value)

            # Store with TTL
            if ttl:
                success = self.redis_client.setex(redis_key, ttl, data)
            else:
                success = self.redis_client.set(redis_key, data)

            return bool(success)

        except Exception as e:
            logger.error(f"Redis put error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete entry from Redis cache."""
        try:
            redis_key = f"{self.prefix}{key}"
            deleted = self.redis_client.delete(redis_key)
            return deleted > 0

        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

    def clear(self) -> None:
        """Clear all cache entries with our prefix."""
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        try:
            # Get Redis info
            info = self.redis_client.info("memory")
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)

            self._stats.entry_count = len(keys)
            # Note: Redis memory stats are global, not per-prefix

        except Exception as e:
            logger.error(f"Redis stats error: {str(e)}")

        return self._stats


class CacheManager:
    """
    Multi-tier cache manager for RAG pipeline optimization.

    Features:
    - L1: In-memory LRU cache for hot data
    - L2: Redis cache for persistent storage
    - Intelligent cache routing
    - Performance monitoring
    - Cache warming and preloading
    """

    def __init__(
        self,
        enable_redis: bool = True,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
        l1_ttl: int = 1800,  # 30 minutes
        l2_ttl: int = 86400,  # 24 hours
        redis_config: Optional[Dict] = None,
    ):
        """
        Initialize cache manager.

        Args:
            enable_redis: Whether to enable Redis L2 cache
            l1_max_size: L1 cache max entries
            l1_max_memory_mb: L1 cache max memory
            l1_ttl: L1 cache TTL
            l2_ttl: L2 cache TTL
            redis_config: Redis configuration
        """
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl

        # L1 Cache (In-memory LRU)
        self.l1_cache = LRUCache(
            max_size=l1_max_size, max_memory_mb=l1_max_memory_mb, default_ttl=l1_ttl
        )

        # L2 Cache (Redis)
        self.l2_cache = None
        if self.enable_redis:
            try:
                redis_config = redis_config or {}
                self.l2_cache = RedisCache(**redis_config)
                logger.info("Multi-tier caching enabled (L1: Memory + L2: Redis)")
            except Exception as e:
                logger.warning(f"Redis cache disabled: {str(e)}")
                self.enable_redis = False

        if not self.enable_redis:
            logger.info("Single-tier caching enabled (L1: Memory only)")

        # Cache key prefixes
        self.prefixes = {
            "search_results": "sr:",
            "query_embeddings": "qe:",
            "movie_details": "md:",
            "recommendations": "rec:",
        }

    def get_search_results(
        self, query: str, filters: Optional[Dict] = None
    ) -> Optional[List[Dict]]:
        """Get cached search results."""
        cache_key = self._build_search_key(query, filters)

        # Try L1 cache first
        result = self.l1_cache.get(cache_key)
        if result is not None:
            logger.debug(f"L1 cache hit for search: {query[:50]}")
            return result

        # Try L2 cache
        if self.l2_cache:
            result = self.l2_cache.get(cache_key)
            if result is not None:
                logger.debug(f"L2 cache hit for search: {query[:50]}")
                # Promote to L1
                self.l1_cache.put(cache_key, result, self.l1_ttl)
                return result

        logger.debug(f"Cache miss for search: {query[:50]}")
        return None

    def put_search_results(
        self, query: str, results: List[Dict], filters: Optional[Dict] = None
    ) -> None:
        """Cache search results."""
        cache_key = self._build_search_key(query, filters)

        # Store in L1
        self.l1_cache.put(cache_key, results, self.l1_ttl)

        # Store in L2
        if self.l2_cache:
            self.l2_cache.put(cache_key, results, self.l2_ttl)

        logger.debug(f"Cached search results for: {query[:50]}")

    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Get cached query embedding."""
        cache_key = self.prefixes["query_embeddings"] + self._hash_query(query)

        # Try L1 first
        embedding = self.l1_cache.get(cache_key)
        if embedding is not None:
            return embedding

        # Try L2
        if self.l2_cache:
            embedding = self.l2_cache.get(cache_key)
            if embedding is not None:
                # Promote to L1
                self.l1_cache.put(cache_key, embedding, self.l1_ttl)
                return embedding

        return None

    def put_query_embedding(self, query: str, embedding: List[float]) -> None:
        """Cache query embedding."""
        cache_key = self.prefixes["query_embeddings"] + self._hash_query(query)

        # Store in both tiers
        self.l1_cache.put(cache_key, embedding, self.l1_ttl)
        if self.l2_cache:
            self.l2_cache.put(cache_key, embedding, self.l2_ttl)

    def get_movie_details(self, movie_id: str) -> Optional[Dict]:
        """Get cached movie details."""
        cache_key = self.prefixes["movie_details"] + movie_id

        # Try L1 first
        details = self.l1_cache.get(cache_key)
        if details is not None:
            return details

        # Try L2
        if self.l2_cache:
            details = self.l2_cache.get(cache_key)
            if details is not None:
                # Promote to L1
                self.l1_cache.put(cache_key, details, self.l1_ttl)
                return details

        return None

    def put_movie_details(self, movie_id: str, details: Dict) -> None:
        """Cache movie details."""
        cache_key = self.prefixes["movie_details"] + movie_id

        # Store in both tiers (longer TTL for movie details)
        self.l1_cache.put(cache_key, details, self.l1_ttl * 2)
        if self.l2_cache:
            self.l2_cache.put(cache_key, details, self.l2_ttl * 2)

    def invalidate_search_cache(self, pattern: Optional[str] = None) -> None:
        """Invalidate search cache entries."""
        # For simplicity, clear all search results
        # In production, you'd want more granular invalidation
        self.clear_cache_type("search_results")
        logger.info("Search cache invalidated")

    def clear_cache_type(self, cache_type: str) -> None:
        """Clear specific type of cache entries."""
        # This is a simplified implementation
        # In production, you'd track keys by type
        if cache_type == "all":
            self.l1_cache.clear()
            if self.l2_cache:
                self.l2_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        l1_stats = self.l1_cache.get_stats()

        stats = {
            "l1_cache": {
                "hits": l1_stats.hits,
                "misses": l1_stats.misses,
                "hit_rate": l1_stats.hit_rate,
                "entry_count": l1_stats.entry_count,
                "size_mb": l1_stats.size_mb,
                "evictions": l1_stats.evictions,
            },
            "multi_tier": self.enable_redis,
        }

        if self.l2_cache:
            l2_stats = self.l2_cache.get_stats()
            stats["l2_cache"] = {
                "hits": l2_stats.hits,
                "misses": l2_stats.misses,
                "hit_rate": l2_stats.hit_rate,
                "entry_count": l2_stats.entry_count,
            }

            # Calculate combined hit rate
            total_hits = l1_stats.hits + l2_stats.hits
            total_requests = total_hits + l1_stats.misses
            stats["combined_hit_rate"] = (
                total_hits / total_requests if total_requests > 0 else 0.0
            )

        return stats

    def warm_cache(self, popular_queries: List[str], search_function) -> None:
        """Pre-warm cache with popular queries."""
        logger.info(f"Warming cache with {len(popular_queries)} popular queries")

        for query in popular_queries:
            if self.get_search_results(query) is None:
                try:
                    results = search_function(query)
                    if results and isinstance(results, dict) and "results" in results:
                        self.put_search_results(query, results["results"])
                    logger.debug(f"Cache warmed for: {query}")
                except Exception as e:
                    logger.error(f"Cache warm failed for '{query}': {str(e)}")

    def _build_search_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """Build cache key for search results."""
        key_parts = [self.prefixes["search_results"], self._hash_query(query)]

        if filters:
            # Sort filters for consistent key generation
            filter_str = json.dumps(filters, sort_keys=True)
            key_parts.append(hashlib.md5(filter_str.encode()).hexdigest()[:8])

        return "".join(key_parts)

    def _hash_query(self, query: str) -> str:
        """Generate hash for query string."""
        # Normalize query for consistent hashing
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()


# Global cache manager instance
_cache_manager = None


def get_cache_manager(**kwargs) -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager

    if _cache_manager is None:
        # Check environment variables for Redis config
        redis_config = {}
        if os.getenv("REDIS_URL"):
            # Parse Redis URL if provided
            import urllib.parse

            url = urllib.parse.urlparse(os.getenv("REDIS_URL"))
            redis_config = {
                "host": url.hostname or "localhost",
                "port": url.port or 6379,
                "password": url.password,
            }
        else:
            redis_config = {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "password": os.getenv("REDIS_PASSWORD"),
            }

        # Remove None values
        redis_config = {k: v for k, v in redis_config.items() if v is not None}

        # Prepare configuration
        config = {"redis_config": redis_config, **kwargs}

        # Only set enable_redis from environment if not explicitly provided
        if "enable_redis" not in kwargs:
            config["enable_redis"] = os.getenv("ENABLE_REDIS", "true").lower() == "true"

        _cache_manager = CacheManager(**config)

    return _cache_manager


# Convenience functions
def cache_search_results(
    query: str, results: List[Dict], filters: Optional[Dict] = None
) -> None:
    """Cache search results."""
    get_cache_manager().put_search_results(query, results, filters)


def get_cached_search_results(
    query: str, filters: Optional[Dict] = None
) -> Optional[List[Dict]]:
    """Get cached search results."""
    return get_cache_manager().get_search_results(query, filters)


def cache_query_embedding(query: str, embedding: List[float]) -> None:
    """Cache query embedding."""
    get_cache_manager().put_query_embedding(query, embedding)


def get_cached_query_embedding(query: str) -> Optional[List[float]]:
    """Get cached query embedding."""
    return get_cache_manager().get_query_embedding(query)


def get_cache_statistics() -> Dict[str, Any]:
    """Get cache performance statistics."""
    return get_cache_manager().get_cache_stats()
