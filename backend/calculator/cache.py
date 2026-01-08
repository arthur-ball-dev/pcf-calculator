"""
Emission Factor Caching Layer.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module provides a caching wrapper for EmissionFactorProvider implementations,
reducing database load by caching emission factors with configurable TTL.

Key Features:
- TTL-based cache expiration
- Cache metrics (hits, misses, hit rate, size)
- Preload capability for warming cache on startup
- Thread-safe implementation using locks
- No SQLAlchemy dependencies (uses provider interface)

Performance Benefits:
- Eliminates redundant database queries for repeated calculations
- Especially effective for hierarchical BOM calculations where same
  emission factors are used multiple times
"""

import asyncio
import time
from typing import Dict, Optional, Tuple

from .providers import EmissionFactorDTO, EmissionFactorProvider


class CachedEmissionFactorProvider(EmissionFactorProvider):
    """
    Caching wrapper for EmissionFactorProvider with TTL-based expiration.

    This provider wraps another EmissionFactorProvider and caches results
    to reduce database load. Cache entries expire after the configured TTL.

    Thread Safety:
    - Uses asyncio.Lock for cache operations
    - Safe for concurrent async access

    Example:
        >>> sql_provider = SQLAlchemyEmissionFactorProvider(session)
        >>> cached = CachedEmissionFactorProvider(sql_provider, ttl_seconds=300)
        >>> ef = await cached.get_by_category("steel")  # Cache miss
        >>> ef = await cached.get_by_category("steel")  # Cache hit

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
    """

    def __init__(
        self,
        provider: EmissionFactorProvider,
        ttl_seconds: int = 300,
    ):
        """
        Initialize cached provider.

        Args:
            provider: Underlying EmissionFactorProvider to wrap
            ttl_seconds: Time-to-live for cache entries in seconds (default: 300)
                        Set to 0 to disable caching (always miss)
        """
        self._provider = provider
        self._ttl = ttl_seconds
        self._cache: Dict[str, Tuple[EmissionFactorDTO, float]] = {}
        self._all_cached: Optional[Tuple[Dict[str, EmissionFactorDTO], float]] = None
        self._lock = asyncio.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """
        Get emission factor by category with caching.

        First checks the cache for a valid (non-expired) entry. If not found
        or expired, fetches from the underlying provider and caches the result.

        Args:
            category: Material/process category name

        Returns:
            EmissionFactorDTO if found, None otherwise

        Note:
            None results are NOT cached to allow for data updates.
        """
        now = time.time()

        # Check cache (fast path, no lock needed for read)
        if category in self._cache:
            ef, cached_at = self._cache[category]
            if self._ttl > 0 and now - cached_at < self._ttl:
                self.hits += 1
                return ef

        # Cache miss - fetch from provider
        self.misses += 1

        async with self._lock:
            # Double-check after acquiring lock (another task may have cached it)
            if category in self._cache:
                ef, cached_at = self._cache[category]
                if self._ttl > 0 and now - cached_at < self._ttl:
                    # Another task cached it while we waited for lock
                    # Adjust metrics (we counted a miss but it was actually hit)
                    self.misses -= 1
                    self.hits += 1
                    return ef

            # Fetch from underlying provider
            ef = await self._provider.get_by_category(category)

            # Cache the result (only if not None)
            if ef is not None:
                self._cache[category] = (ef, time.time())

            return ef

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """
        Get all emission factors with caching.

        If the full cache is valid, returns cached result. Otherwise,
        fetches from underlying provider and updates the cache.

        Returns:
            Dictionary mapping category names to EmissionFactorDTO objects
        """
        now = time.time()

        # Check if we have a valid full cache
        if self._all_cached is not None:
            all_efs, cached_at = self._all_cached
            if self._ttl > 0 and now - cached_at < self._ttl:
                self.hits += 1
                return all_efs.copy()

        # Cache miss
        self.misses += 1

        async with self._lock:
            # Double-check after acquiring lock
            if self._all_cached is not None:
                all_efs, cached_at = self._all_cached
                if self._ttl > 0 and now - cached_at < self._ttl:
                    self.misses -= 1
                    self.hits += 1
                    return all_efs.copy()

            # Fetch from underlying provider
            all_efs = await self._provider.get_all()

            # Update caches
            now = time.time()
            self._all_cached = (all_efs.copy(), now)

            # Also populate individual cache entries
            for category, ef in all_efs.items():
                self._cache[category] = (ef, now)

            return all_efs.copy()

    async def preload_all(self) -> None:
        """
        Pre-warm cache with all emission factors.

        Calls get_all() on the underlying provider and populates
        both the full cache and individual category caches.

        This is useful for warming the cache on application startup
        to ensure fast response times for initial requests.

        Example:
            >>> cached_provider = CachedEmissionFactorProvider(sql_provider)
            >>> await cached_provider.preload_all()
            >>> # All subsequent lookups will be cache hits
        """
        await self.get_all()

    def clear_cache(self) -> None:
        """
        Clear all cached data.

        Removes all entries from both category and full caches.
        Does NOT reset hit/miss metrics (see get_metrics()).

        Use this when emission factors have been updated in the database
        and you want to force fresh data on next access.
        """
        self._cache.clear()
        self._all_cached = None

    def get_metrics(self) -> dict:
        """
        Get cache performance metrics.

        Returns:
            Dictionary with cache metrics:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Ratio of hits to total requests (0.0-1.0)
            - cache_size: Number of entries currently in cache

        Example:
            >>> metrics = cached_provider.get_metrics()
            >>> print(f"Hit rate: {metrics['hit_rate']:.1%}")
            Hit rate: 85.3%
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
        }

    def reset_metrics(self) -> None:
        """
        Reset cache hit/miss metrics.

        Use this if you want to measure performance for a specific
        time period without clearing the cached data.
        """
        self.hits = 0
        self.misses = 0
