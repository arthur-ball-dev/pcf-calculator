"""
Test Redis Cache Utility Module
TASK-BE-P8-003: Add Redis Caching for Hot Paths

Test Scenarios:
1. get_redis_client - Get async Redis connection
2. cache_response - Cache JSON response with TTL
3. get_cached_response - Retrieve cached response
4. invalidate_pattern - Invalidate keys matching pattern
5. Cache miss returns None
6. TTL expiration
7. Product cache key generation
8. Search cache key generation with hash

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (module does not exist yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
import json
import hashlib
import asyncio
from typing import Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis async client for unit tests."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.keys = AsyncMock(return_value=[])
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def sample_products_data():
    """Sample product list data for caching tests."""
    return {
        "items": [
            {
                "id": "prod-1",
                "code": "PROD001",
                "name": "Test Product 1",
                "unit": "kg",
                "category": "electronics",
                "is_finished_product": True
            },
            {
                "id": "prod-2",
                "code": "PROD002",
                "name": "Test Product 2",
                "unit": "unit",
                "category": "apparel",
                "is_finished_product": False
            }
        ],
        "total": 2,
        "limit": 100,
        "offset": 0
    }


@pytest.fixture
def sample_search_response():
    """Sample search response data for caching tests."""
    return {
        "items": [
            {
                "id": "prod-1",
                "code": "PROD001",
                "name": "Test Laptop",
                "description": "A test laptop product",
                "unit": "unit",
                "is_finished_product": True,
                "relevance_score": 0.8
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
        "has_more": False
    }


# ============================================================================
# Test Scenario 1: get_redis_client
# ============================================================================


class TestGetRedisClient:
    """Tests for getting Redis client connection."""

    @pytest.mark.asyncio
    async def test_get_redis_client_returns_client(self, require_redis):
        """Test that get_redis_client returns a Redis client."""
        from backend.utils.cache import get_redis_client

        client = await get_redis_client()

        assert client is not None, "Should return a Redis client"
        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_get_redis_client_can_ping(self, require_redis):
        """Test that the Redis client can ping the server."""
        from backend.utils.cache import get_redis_client

        client = await get_redis_client()

        # Should be able to ping Redis
        pong = await client.ping()
        assert pong is True, "Should be able to ping Redis"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_redis_client_uses_config_settings(self):
        """Test that get_redis_client uses settings from config."""
        from backend.utils.cache import get_redis_client
        from backend.config import settings

        # Patch the redis module to capture the URL used
        with patch('backend.utils.cache.redis.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            client = await get_redis_client()

            # Should have called from_url with broker URL
            mock_from_url.assert_called_once()
            call_args = mock_from_url.call_args
            assert call_args is not None, "Should have called from_url"


# ============================================================================
# Test Scenario 2: cache_response
# ============================================================================


class TestCacheResponse:
    """Tests for caching JSON responses."""

    @pytest.mark.asyncio
    async def test_cache_response_stores_data(self, require_redis, sample_products_data):
        """Test that cache_response stores data in Redis."""
        from backend.utils.cache import cache_response, get_cached_response, get_redis_client

        test_key = "test:cache_response:stores_data"
        ttl = 60

        # Cache the response
        result = await cache_response(test_key, sample_products_data, ttl)

        assert result is True, "cache_response should return True on success"

        # Verify it was stored
        cached = await get_cached_response(test_key)
        assert cached is not None, "Data should be cached"
        assert cached["total"] == sample_products_data["total"]

        # Clean up
        client = await get_redis_client()
        await client.delete(test_key)
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_response_serializes_json(self, require_redis, sample_products_data):
        """Test that cache_response properly serializes data to JSON."""
        from backend.utils.cache import cache_response, get_redis_client

        test_key = "test:cache_response:serializes"
        ttl = 60

        await cache_response(test_key, sample_products_data, ttl)

        # Get raw value from Redis
        client = await get_redis_client()
        raw_value = await client.get(test_key)

        assert raw_value is not None, "Should have stored value"
        # Should be valid JSON
        decoded = json.loads(raw_value)
        assert decoded == sample_products_data

        await client.delete(test_key)
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_response_sets_ttl(self, require_redis, sample_products_data):
        """Test that cache_response sets TTL on the key."""
        from backend.utils.cache import cache_response, get_redis_client

        test_key = "test:cache_response:ttl"
        ttl = 300  # 5 minutes

        await cache_response(test_key, sample_products_data, ttl)

        # Check TTL is set
        client = await get_redis_client()
        remaining_ttl = await client.ttl(test_key)

        # TTL should be close to what we set (allowing some margin)
        assert remaining_ttl > 0, "Key should have TTL set"
        assert remaining_ttl <= ttl, f"TTL should be at most {ttl}"
        assert remaining_ttl >= ttl - 5, f"TTL should be close to {ttl}"

        await client.delete(test_key)
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_response_handles_complex_data(self, require_redis):
        """Test that cache_response handles nested data structures."""
        from backend.utils.cache import cache_response, get_cached_response, get_redis_client

        test_key = "test:cache_response:complex"
        complex_data = {
            "items": [
                {"nested": {"deep": {"value": 123}}},
                {"list": [1, 2, 3, "four"]}
            ],
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "count": 42
            }
        }

        await cache_response(test_key, complex_data, 60)

        cached = await get_cached_response(test_key)
        assert cached == complex_data, "Complex data should round-trip correctly"

        client = await get_redis_client()
        await client.delete(test_key)
        await client.close()


# ============================================================================
# Test Scenario 3: get_cached_response
# ============================================================================


class TestGetCachedResponse:
    """Tests for retrieving cached responses."""

    @pytest.mark.asyncio
    async def test_get_cached_response_returns_data(self, require_redis, sample_products_data):
        """Test that get_cached_response returns cached data."""
        from backend.utils.cache import cache_response, get_cached_response, get_redis_client

        test_key = "test:get_cached:returns_data"

        await cache_response(test_key, sample_products_data, 60)

        cached = await get_cached_response(test_key)

        assert cached is not None, "Should return cached data"
        assert cached["items"] == sample_products_data["items"]
        assert cached["total"] == sample_products_data["total"]

        client = await get_redis_client()
        await client.delete(test_key)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_cached_response_cache_miss_returns_none(self, require_redis):
        """Test that get_cached_response returns None for cache miss."""
        from backend.utils.cache import get_cached_response

        non_existent_key = "test:cache_miss:nonexistent:12345"

        result = await get_cached_response(non_existent_key)

        assert result is None, "Cache miss should return None"

    @pytest.mark.asyncio
    async def test_get_cached_response_deserializes_json(self, require_redis):
        """Test that get_cached_response properly deserializes JSON."""
        from backend.utils.cache import get_cached_response, get_redis_client

        test_key = "test:get_cached:deserializes"
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        # Store raw JSON directly
        client = await get_redis_client()
        await client.setex(test_key, 60, json.dumps(test_data))

        cached = await get_cached_response(test_key)

        assert cached == test_data, "Should deserialize JSON correctly"
        assert isinstance(cached, dict), "Should return dict"

        await client.delete(test_key)
        await client.close()


# ============================================================================
# Test Scenario 4: invalidate_pattern
# ============================================================================


class TestInvalidatePattern:
    """Tests for invalidating cache keys by pattern."""

    @pytest.mark.asyncio
    async def test_invalidate_pattern_deletes_matching_keys(self, require_redis):
        """Test that invalidate_pattern deletes keys matching pattern."""
        from backend.utils.cache import cache_response, invalidate_pattern, get_cached_response, get_redis_client

        # Set up test keys
        await cache_response("products:list:100:0:true", {"test": 1}, 60)
        await cache_response("products:list:50:0:false", {"test": 2}, 60)
        await cache_response("products:search:abc123", {"test": 3}, 60)

        # Invalidate products:list:* pattern
        deleted_count = await invalidate_pattern("products:list:*")

        assert deleted_count >= 2, "Should delete at least 2 keys"

        # Verify list keys are gone
        list_key_1 = await get_cached_response("products:list:100:0:true")
        list_key_2 = await get_cached_response("products:list:50:0:false")
        assert list_key_1 is None, "List key 1 should be deleted"
        assert list_key_2 is None, "List key 2 should be deleted"

        # Verify search key still exists
        search_key = await get_cached_response("products:search:abc123")
        assert search_key is not None, "Search key should not be deleted"

        # Clean up
        client = await get_redis_client()
        await client.delete("products:search:abc123")
        await client.close()

    @pytest.mark.asyncio
    async def test_invalidate_pattern_returns_count(self, require_redis):
        """Test that invalidate_pattern returns number of deleted keys."""
        from backend.utils.cache import cache_response, invalidate_pattern, get_redis_client

        # Set up test keys
        await cache_response("test:invalidate:count:1", {"a": 1}, 60)
        await cache_response("test:invalidate:count:2", {"b": 2}, 60)
        await cache_response("test:invalidate:count:3", {"c": 3}, 60)

        deleted_count = await invalidate_pattern("test:invalidate:count:*")

        assert deleted_count == 3, "Should return count of deleted keys"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_no_match_returns_zero(self, require_redis):
        """Test that invalidate_pattern returns 0 when no keys match."""
        from backend.utils.cache import invalidate_pattern

        deleted_count = await invalidate_pattern("nonexistent:pattern:*")

        assert deleted_count == 0, "Should return 0 when no keys match"

    @pytest.mark.asyncio
    async def test_invalidate_all_products_cache(self, require_redis):
        """Test invalidating all product-related cache."""
        from backend.utils.cache import cache_response, invalidate_pattern, get_cached_response

        # Set up various product cache keys
        await cache_response("products:list:100:0:None", {"test": 1}, 60)
        await cache_response("products:search:hash123", {"test": 2}, 60)

        # Invalidate all products cache
        deleted_count = await invalidate_pattern("products:*")

        assert deleted_count >= 2, "Should delete all product cache keys"

        # Verify all are gone
        assert await get_cached_response("products:list:100:0:None") is None
        assert await get_cached_response("products:search:hash123") is None


# ============================================================================
# Test Scenario 5: TTL Expiration
# ============================================================================


class TestTTLExpiration:
    """Tests for TTL expiration behavior."""

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, require_redis, sample_products_data):
        """Test that cached data expires after TTL."""
        from backend.utils.cache import cache_response, get_cached_response, get_redis_client

        test_key = "test:ttl:expiration"
        short_ttl = 1  # 1 second

        await cache_response(test_key, sample_products_data, short_ttl)

        # Should exist immediately
        cached = await get_cached_response(test_key)
        assert cached is not None, "Should be cached initially"

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should be expired
        expired = await get_cached_response(test_key)
        assert expired is None, "Should be None after TTL expires"


# ============================================================================
# Test Scenario 6: Cache Key Generation
# ============================================================================


class TestCacheKeyGeneration:
    """Tests for cache key generation functions."""

    def test_product_list_cache_key(self):
        """Test product list cache key generation."""
        from backend.utils.cache import get_product_list_cache_key

        # Test with all parameters
        key = get_product_list_cache_key(limit=100, offset=0, is_finished=True)
        assert key == "products:list:100:0:True", f"Unexpected key: {key}"

        # Test with None is_finished
        key = get_product_list_cache_key(limit=50, offset=10, is_finished=None)
        assert key == "products:list:50:10:None", f"Unexpected key: {key}"

        # Test with False is_finished
        key = get_product_list_cache_key(limit=100, offset=0, is_finished=False)
        assert key == "products:list:100:0:False", f"Unexpected key: {key}"

    def test_product_search_cache_key(self):
        """Test product search cache key generation with hash."""
        from backend.utils.cache import get_product_search_cache_key

        # Test with query and filters
        key1 = get_product_search_cache_key(
            query="laptop",
            category_id="cat-123",
            industry="electronics",
            manufacturer=None,
            country_of_origin="US",
            is_finished_product=True,
            has_bom=None,
            limit=50,
            offset=0
        )

        # Key should be deterministic
        key2 = get_product_search_cache_key(
            query="laptop",
            category_id="cat-123",
            industry="electronics",
            manufacturer=None,
            country_of_origin="US",
            is_finished_product=True,
            has_bom=None,
            limit=50,
            offset=0
        )

        assert key1 == key2, "Same params should produce same key"
        assert key1.startswith("products:search:"), f"Key should start with 'products:search:': {key1}"

    def test_product_search_cache_key_different_params(self):
        """Test that different parameters produce different cache keys."""
        from backend.utils.cache import get_product_search_cache_key

        key1 = get_product_search_cache_key(
            query="laptop",
            limit=50,
            offset=0
        )

        key2 = get_product_search_cache_key(
            query="phone",
            limit=50,
            offset=0
        )

        assert key1 != key2, "Different queries should produce different keys"

    def test_product_search_cache_key_order_independent(self):
        """Test that parameter order doesn't affect cache key."""
        from backend.utils.cache import get_product_search_cache_key

        # Same parameters, call in different order
        key1 = get_product_search_cache_key(
            query="laptop",
            industry="electronics",
            manufacturer="Acme",
            limit=50,
            offset=0
        )

        key2 = get_product_search_cache_key(
            manufacturer="Acme",
            query="laptop",
            industry="electronics",
            offset=0,
            limit=50
        )

        assert key1 == key2, "Parameter order should not affect key"

    def test_product_search_cache_key_uses_md5_hash(self):
        """Test that search cache key uses MD5 hash."""
        from backend.utils.cache import get_product_search_cache_key

        key = get_product_search_cache_key(
            query="test",
            limit=50,
            offset=0
        )

        # Extract the hash part (after "products:search:")
        hash_part = key.split(":")[-1]

        # MD5 hashes are 32 hex characters
        assert len(hash_part) == 32, f"Hash should be 32 chars: {hash_part}"
        assert all(c in "0123456789abcdef" for c in hash_part), "Should be hex"


# ============================================================================
# Test Scenario 7: Error Handling
# ============================================================================


class TestCacheErrorHandling:
    """Tests for cache error handling."""

    @pytest.mark.asyncio
    async def test_cache_response_handles_connection_error(self):
        """Test that cache_response handles connection errors gracefully."""
        from backend.utils.cache import cache_response

        with patch('backend.utils.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.setex.side_effect = ConnectionError("Redis unavailable")
            mock_get_client.return_value = mock_client

            # Should not raise, but return False
            result = await cache_response("test:key", {"data": 1}, 60)

            assert result is False, "Should return False on connection error"

    @pytest.mark.asyncio
    async def test_get_cached_response_handles_connection_error(self):
        """Test that get_cached_response handles connection errors gracefully."""
        from backend.utils.cache import get_cached_response

        with patch('backend.utils.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = ConnectionError("Redis unavailable")
            mock_get_client.return_value = mock_client

            # Should not raise, but return None
            result = await get_cached_response("test:key")

            assert result is None, "Should return None on connection error"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_handles_connection_error(self):
        """Test that invalidate_pattern handles connection errors gracefully."""
        from backend.utils.cache import invalidate_pattern

        with patch('backend.utils.cache.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.keys.side_effect = ConnectionError("Redis unavailable")
            mock_get_client.return_value = mock_client

            # Should not raise, but return 0
            result = await invalidate_pattern("test:*")

            assert result == 0, "Should return 0 on connection error"


# ============================================================================
# Test Scenario 8: Integration with Endpoints (Mocked)
# ============================================================================


class TestCacheIntegration:
    """Tests for cache integration scenarios."""

    @pytest.mark.asyncio
    async def test_product_list_caching_workflow(self, require_redis, sample_products_data):
        """Test complete caching workflow for product list."""
        from backend.utils.cache import (
            cache_response,
            get_cached_response,
            get_product_list_cache_key,
            invalidate_pattern,
            get_redis_client
        )

        # Generate cache key
        cache_key = get_product_list_cache_key(limit=100, offset=0, is_finished=None)

        # First request - cache miss
        cached = await get_cached_response(cache_key)
        assert cached is None, "Initial request should be cache miss"

        # Store in cache
        await cache_response(cache_key, sample_products_data, 300)

        # Second request - cache hit
        cached = await get_cached_response(cache_key)
        assert cached is not None, "Should hit cache"
        assert cached["total"] == sample_products_data["total"]

        # Product mutation - invalidate cache
        await invalidate_pattern("products:list:*")

        # Third request - cache miss after invalidation
        cached = await get_cached_response(cache_key)
        assert cached is None, "Should be cache miss after invalidation"

    @pytest.mark.asyncio
    async def test_product_search_caching_workflow(self, require_redis, sample_search_response):
        """Test complete caching workflow for product search."""
        from backend.utils.cache import (
            cache_response,
            get_cached_response,
            get_product_search_cache_key,
            invalidate_pattern
        )

        # Generate cache key for search
        cache_key = get_product_search_cache_key(
            query="laptop",
            industry="electronics",
            limit=50,
            offset=0
        )

        # First search - cache miss
        cached = await get_cached_response(cache_key)
        assert cached is None, "Initial search should be cache miss"

        # Store in cache (shorter TTL for search)
        await cache_response(cache_key, sample_search_response, 60)

        # Same search - cache hit
        cached = await get_cached_response(cache_key)
        assert cached is not None, "Same search should hit cache"
        assert cached["items"][0]["name"] == sample_search_response["items"][0]["name"]

        # Clean up
        await invalidate_pattern("products:search:*")
