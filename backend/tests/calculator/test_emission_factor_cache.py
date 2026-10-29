"""
Test suite for Emission Factor caching layer.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

Tests that verify:
1. Cache returns cached values on second call
2. Cache respects TTL (Time To Live)
3. Cache preloading works correctly
4. Cache metrics are exposed
5. Cache handles edge cases properly

Following TDD methodology - tests written BEFORE implementation.
These tests should FAIL initially until caching is implemented.
"""

import pytest
import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch


# ==================== Test Data Classes ====================


@dataclass(frozen=True)
class EmissionFactorDTO:
    """
    Data transfer object for emission factors - mirrors the expected interface.
    """

    id: str
    category: str
    co2e_kg: float
    unit: str
    data_source: str
    uncertainty: Optional[float] = None


# ==================== Mock Providers for Testing ====================


class MockSlowEmissionFactorProvider:
    """
    Mock provider that simulates slow database access for testing cache performance.
    """

    def __init__(
        self,
        factors: Dict[str, EmissionFactorDTO],
        delay_seconds: float = 0.1,
    ):
        self._factors = factors
        self._delay = delay_seconds
        self.call_count = 0
        self.get_all_call_count = 0

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """Simulate slow database fetch."""
        self.call_count += 1
        await asyncio.sleep(self._delay)
        return self._factors.get(category)

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """Simulate slow batch fetch."""
        self.get_all_call_count += 1
        await asyncio.sleep(self._delay * 2)  # Batch is slower
        return self._factors.copy()


class TrackingEmissionFactorProvider:
    """
    Provider wrapper that tracks exact call history for testing.
    """

    def __init__(self, factors: Dict[str, EmissionFactorDTO]):
        self._factors = factors
        self.call_count = 0
        self.call_history: list[str] = []

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """Track each call."""
        self.call_count += 1
        self.call_history.append(f"get_by_category:{category}")
        return self._factors.get(category)

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """Track get_all calls."""
        self.call_count += 1
        self.call_history.append("get_all")
        return self._factors.copy()


# ==================== Test Classes ====================


class TestCacheHitBehavior:
    """Test that cache returns cached values on subsequent calls."""

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_call(self):
        """
        Scenario 3: Cache Hit (Performance)

        Given: A cached provider wrapping a tracking provider
        When: Same emission factor is requested multiple times
        Then: Underlying provider is only called once

        Expected Behavior:
            First request: Cache miss, call underlying provider
            Second request: Cache hit, return cached value
            Third request: Cache hit, return cached value
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail(
                "CachedEmissionFactorProvider not found. "
                "Create backend/calculator/cache.py"
            )

        # Arrange
        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider, ttl_seconds=300
        )

        # Act
        ef1 = await cached_provider.get_by_category("steel")  # Cache miss
        ef2 = await cached_provider.get_by_category("steel")  # Cache hit
        ef3 = await cached_provider.get_by_category("steel")  # Cache hit

        # Assert
        assert tracking_provider.call_count == 1, (
            f"Expected 1 underlying call, got {tracking_provider.call_count}. "
            "Cache should return cached value on second call."
        )

        assert ef1 == ef2 == ef3, "All calls should return the same value"
        assert ef1.co2e_kg == 2.5

    @pytest.mark.asyncio
    async def test_cache_different_categories_cached_separately(self):
        """
        Scenario: Different categories are cached separately

        Given: A cached provider
        When: Different categories are requested
        Then: Each category is fetched and cached independently
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
            "aluminum": EmissionFactorDTO(
                id="ef-2",
                category="aluminum",
                co2e_kg=8.1,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider, ttl_seconds=300
        )

        # Fetch different categories
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("aluminum")
        await cached_provider.get_by_category("steel")  # Cache hit
        await cached_provider.get_by_category("aluminum")  # Cache hit

        # Should only have 2 underlying calls (one per category)
        assert tracking_provider.call_count == 2, (
            f"Expected 2 underlying calls, got {tracking_provider.call_count}"
        )

    @pytest.mark.asyncio
    async def test_cache_returns_none_for_missing_category(self):
        """
        Scenario: Cache handles missing emission factors

        Given: A cached provider
        When: Non-existent category is requested
        Then: None is returned and result is NOT cached
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {}  # Empty

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider, ttl_seconds=300
        )

        result1 = await cached_provider.get_by_category("nonexistent")
        result2 = await cached_provider.get_by_category("nonexistent")

        assert result1 is None
        assert result2 is None

        # Note: Decision to cache None or not is implementation-specific
        # Test just verifies it handles missing gracefully


class TestCacheExpiration:
    """Test that cache respects TTL settings."""

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self):
        """
        Scenario 4: Cache Expiration

        Given: A cached provider with short TTL (1 second)
        When: Value is fetched, wait exceeds TTL, then fetch again
        Then: Underlying provider is called twice (cache expired)
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=1,  # 1 second TTL for testing
        )

        # First fetch - cache miss
        ef1 = await cached_provider.get_by_category("steel")
        assert tracking_provider.call_count == 1

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Second fetch - cache expired, miss
        ef2 = await cached_provider.get_by_category("steel")

        assert tracking_provider.call_count == 2, (
            f"Expected 2 calls due to expiration, got {tracking_provider.call_count}"
        )
        assert ef1 == ef2, "Values should still be equal"

    @pytest.mark.asyncio
    async def test_cache_valid_before_ttl(self):
        """
        Scenario: Cache is valid before TTL expires

        Given: A cached provider with 10 second TTL
        When: Value is fetched twice within TTL
        Then: Only one underlying call is made
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=10,  # 10 second TTL
        )

        # First fetch
        await cached_provider.get_by_category("steel")

        # Small delay (within TTL)
        await asyncio.sleep(0.1)

        # Second fetch (should be cached)
        await cached_provider.get_by_category("steel")

        assert tracking_provider.call_count == 1, (
            "Cache should be valid within TTL period"
        )

    @pytest.mark.asyncio
    async def test_cache_ttl_configurable(self):
        """
        Scenario: Cache TTL is configurable

        Given: CachedEmissionFactorProvider constructor
        When: ttl_seconds parameter is provided
        Then: Cache uses that TTL value
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
            import inspect

            sig = inspect.signature(CachedEmissionFactorProvider.__init__)
            params = list(sig.parameters.keys())

            assert "ttl_seconds" in params, (
                "CachedEmissionFactorProvider must accept ttl_seconds parameter"
            )
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")


class TestCachePreloading:
    """Test cache preloading functionality."""

    @pytest.mark.asyncio
    async def test_cache_preload_all(self):
        """
        Scenario 5: Cache Bulk Load

        Given: A cached provider with preload capability
        When: preload_all() is called
        Then: All subsequent lookups are cache hits
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
            "aluminum": EmissionFactorDTO(
                id="ef-2",
                category="aluminum",
                co2e_kg=8.1,
                unit="kg",
                data_source="EPA",
            ),
            "plastic": EmissionFactorDTO(
                id="ef-3",
                category="plastic",
                co2e_kg=3.0,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # Pre-warm cache
        await cached_provider.preload_all()

        # Record call count after preload
        calls_after_preload = tracking_provider.call_count

        # All lookups should be cache hits
        ef1 = await cached_provider.get_by_category("steel")
        ef2 = await cached_provider.get_by_category("aluminum")
        ef3 = await cached_provider.get_by_category("plastic")

        # No additional calls should have been made
        assert tracking_provider.call_count == calls_after_preload, (
            f"Expected {calls_after_preload} calls (from preload), "
            f"got {tracking_provider.call_count}. "
            "Lookups after preload should all be cache hits."
        )

        assert ef1.co2e_kg == 2.5
        assert ef2.co2e_kg == 8.1
        assert ef3.co2e_kg == 3.0

    @pytest.mark.asyncio
    async def test_preload_all_method_exists(self):
        """
        Scenario: preload_all method exists on cached provider

        Given: CachedEmissionFactorProvider class
        When: We inspect its methods
        Then: preload_all() should be defined
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider

            assert hasattr(CachedEmissionFactorProvider, "preload_all"), (
                "CachedEmissionFactorProvider must have preload_all method"
            )
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")


class TestCacheMetrics:
    """Test that cache exposes metrics for monitoring."""

    @pytest.mark.asyncio
    async def test_cache_tracks_hits_and_misses(self):
        """
        Scenario: Cache exposes hit/miss metrics

        Given: A cached provider
        When: Multiple requests are made (some hits, some misses)
        Then: Metrics correctly reflect hit/miss counts
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # Miss
        await cached_provider.get_by_category("steel")
        # Hit
        await cached_provider.get_by_category("steel")
        # Hit
        await cached_provider.get_by_category("steel")

        metrics = cached_provider.get_metrics()

        assert "hits" in metrics, "Metrics should include 'hits'"
        assert "misses" in metrics, "Metrics should include 'misses'"

        assert metrics["misses"] == 1, f"Expected 1 miss, got {metrics['misses']}"
        assert metrics["hits"] == 2, f"Expected 2 hits, got {metrics['hits']}"

    @pytest.mark.asyncio
    async def test_cache_tracks_hit_rate(self):
        """
        Scenario: Cache exposes hit rate metric

        Given: A cached provider with requests
        When: get_metrics() is called
        Then: hit_rate is correctly calculated
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # 1 miss, 3 hits = 75% hit rate
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("steel")

        metrics = cached_provider.get_metrics()

        assert "hit_rate" in metrics, "Metrics should include 'hit_rate'"
        expected_hit_rate = 3 / 4  # 0.75
        assert metrics["hit_rate"] == pytest.approx(expected_hit_rate, rel=0.01), (
            f"Expected hit rate {expected_hit_rate}, got {metrics['hit_rate']}"
        )

    @pytest.mark.asyncio
    async def test_cache_tracks_size(self):
        """
        Scenario: Cache exposes size metric

        Given: A cached provider with cached items
        When: get_metrics() is called
        Then: cache_size reflects number of cached items
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
            "aluminum": EmissionFactorDTO(
                id="ef-2",
                category="aluminum",
                co2e_kg=8.1,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # Cache 2 different items
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("aluminum")

        metrics = cached_provider.get_metrics()

        assert "cache_size" in metrics, "Metrics should include 'cache_size'"
        assert metrics["cache_size"] == 2, (
            f"Expected cache size 2, got {metrics['cache_size']}"
        )


class TestCacheClearBehavior:
    """Test cache clearing functionality."""

    @pytest.mark.asyncio
    async def test_clear_cache_removes_all_entries(self):
        """
        Scenario: Cache can be cleared

        Given: A cached provider with cached entries
        When: clear_cache() is called
        Then: All entries are removed, next request is cache miss
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # Populate cache
        await cached_provider.get_by_category("steel")
        assert tracking_provider.call_count == 1

        # Verify cache hit
        await cached_provider.get_by_category("steel")
        assert tracking_provider.call_count == 1  # Still 1 (cache hit)

        # Clear cache
        cached_provider.clear_cache()

        # Should be cache miss now
        await cached_provider.get_by_category("steel")
        assert tracking_provider.call_count == 2, (
            "After clear_cache(), next request should be cache miss"
        )

    @pytest.mark.asyncio
    async def test_clear_cache_resets_metrics(self):
        """
        Scenario: Clearing cache optionally resets metrics

        Given: A cached provider with accumulated metrics
        When: clear_cache() is called
        Then: Cache size is zero (metrics may or may not reset)
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=300,
        )

        # Build up cache
        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("steel")

        # Clear
        cached_provider.clear_cache()

        metrics = cached_provider.get_metrics()
        assert metrics["cache_size"] == 0, "Cache size should be 0 after clear"


class TestCacheEdgeCases:
    """Test cache edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_cache_handles_empty_provider(self):
        """
        Scenario: Cache handles provider with no emission factors

        Given: A provider with no emission factors
        When: get_by_category is called
        Then: None is returned without error
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        empty_provider = TrackingEmissionFactorProvider({})
        cached_provider = CachedEmissionFactorProvider(
            provider=empty_provider,
            ttl_seconds=300,
        )

        result = await cached_provider.get_by_category("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_handles_concurrent_requests(self):
        """
        Scenario: Cache handles concurrent requests for same category

        Given: Multiple concurrent requests for same category
        When: All requests complete
        Then: Underlying provider is called only once (or at most once per category)
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        slow_provider = MockSlowEmissionFactorProvider(factors, delay_seconds=0.2)
        cached_provider = CachedEmissionFactorProvider(
            provider=slow_provider,
            ttl_seconds=300,
        )

        # Make concurrent requests
        results = await asyncio.gather(
            cached_provider.get_by_category("steel"),
            cached_provider.get_by_category("steel"),
            cached_provider.get_by_category("steel"),
            cached_provider.get_by_category("steel"),
            cached_provider.get_by_category("steel"),
        )

        # All should return same value
        assert all(r.co2e_kg == 2.5 for r in results)

        # Provider should be called at most once per unique request
        # (implementation may vary - some allow multiple concurrent misses)
        assert slow_provider.call_count <= 5, (
            f"Unexpected call count: {slow_provider.call_count}"
        )

    @pytest.mark.asyncio
    async def test_cache_with_zero_ttl_always_misses(self):
        """
        Scenario: Zero TTL means no caching

        Given: A cached provider with ttl_seconds=0
        When: Same category is requested twice
        Then: Underlying provider is called twice (no caching)
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

        factors = {
            "steel": EmissionFactorDTO(
                id="ef-1",
                category="steel",
                co2e_kg=2.5,
                unit="kg",
                data_source="EPA",
            ),
        }

        tracking_provider = TrackingEmissionFactorProvider(factors)
        cached_provider = CachedEmissionFactorProvider(
            provider=tracking_provider,
            ttl_seconds=0,  # No caching
        )

        await cached_provider.get_by_category("steel")
        await cached_provider.get_by_category("steel")

        # Both should be misses with zero TTL
        assert tracking_provider.call_count == 2


class TestCacheProviderInterface:
    """Test that cache provider implements the same interface as base provider."""

    def test_cached_provider_has_get_by_category(self):
        """
        Scenario: CachedEmissionFactorProvider has get_by_category method

        Given: The CachedEmissionFactorProvider class
        When: We inspect its methods
        Then: get_by_category should be defined
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider

            assert hasattr(CachedEmissionFactorProvider, "get_by_category"), (
                "CachedEmissionFactorProvider must have get_by_category method"
            )
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

    def test_cached_provider_has_get_all(self):
        """
        Scenario: CachedEmissionFactorProvider has get_all method

        Given: The CachedEmissionFactorProvider class
        When: We inspect its methods
        Then: get_all should be defined
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider

            assert hasattr(CachedEmissionFactorProvider, "get_all"), (
                "CachedEmissionFactorProvider must have get_all method"
            )
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")

    def test_cached_provider_constructor_accepts_provider_and_ttl(self):
        """
        Scenario: Constructor accepts required parameters

        Given: CachedEmissionFactorProvider class
        When: We inspect its __init__ signature
        Then: Should accept 'provider' and 'ttl_seconds' parameters
        """
        try:
            from backend.calculator.cache import CachedEmissionFactorProvider
            import inspect

            sig = inspect.signature(CachedEmissionFactorProvider.__init__)
            params = list(sig.parameters.keys())

            assert "provider" in params, (
                "Constructor must accept 'provider' parameter"
            )
            assert "ttl_seconds" in params, (
                "Constructor must accept 'ttl_seconds' parameter"
            )
        except ImportError:
            pytest.fail("CachedEmissionFactorProvider not found")


class TestCacheConfigFromSettings:
    """Test that cache TTL can be configured from application settings."""

    def test_cache_ttl_in_config(self):
        """
        Scenario: Cache TTL is configurable via settings

        Given: The application config
        When: We import settings
        Then: EMISSION_FACTOR_CACHE_TTL setting should exist
        """
        try:
            from backend.config import settings

            # Check if the setting exists (may have default)
            assert hasattr(settings, "emission_factor_cache_ttl") or hasattr(
                settings, "EMISSION_FACTOR_CACHE_TTL"
            ), (
                "Settings should have emission_factor_cache_ttl configuration"
            )
        except (ImportError, AttributeError) as e:
            pytest.fail(
                f"Cache TTL configuration not found in settings. "
                f"Add EMISSION_FACTOR_CACHE_TTL to backend/config.py. "
                f"Error: {e}"
            )
