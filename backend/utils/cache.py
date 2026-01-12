"""
Redis Cache Utility Module
TASK-BE-P8-003: Add Redis Caching for Hot Paths

This module provides Redis caching utilities for the PCF Calculator API.
It is designed to cache frequently accessed data like product lists and search
results to reduce database load.

Provides both sync and async versions of cache operations:
- Async: cache_response, get_cached_response, invalidate_pattern
- Sync: cache_response_sync, get_cached_response_sync, invalidate_pattern_sync

Cache Key Patterns:
- products:list:{limit}:{offset}:{is_finished} - Product list endpoint
- products:search:{query_hash} - Product search endpoint (MD5 hash of params)

TTL Guidelines:
- Product list: 300 seconds (5 minutes)
- Product search: 60 seconds (1 minute - shorter for search)

Usage (Sync - for sync FastAPI endpoints):
    from backend.utils.cache import (
        cache_response_sync,
        get_cached_response_sync,
        invalidate_pattern_sync,
        get_product_list_cache_key,
        get_product_search_cache_key
    )

    # Cache a response (sync)
    cache_key = get_product_list_cache_key(limit=100, offset=0, is_finished=None)
    cache_response_sync(cache_key, response_data, ttl=300)

    # Get cached response (sync)
    cached = get_cached_response_sync(cache_key)
    if cached:
        return cached

Usage (Async - for async FastAPI endpoints):
    from backend.utils.cache import (
        cache_response,
        get_cached_response,
        invalidate_pattern
    )

    # Cache a response (async)
    await cache_response(cache_key, response_data, ttl=300)

    # Get cached response (async)
    cached = await get_cached_response(cache_key)
"""

import hashlib
import json
import logging
from typing import Any, Optional

import redis

from backend.config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# Cache Configuration Constants
# ============================================================================

PRODUCT_LIST_TTL = 300  # 5 minutes
PRODUCT_SEARCH_TTL = 60  # 1 minute


# ============================================================================
# Sync Redis Client
# ============================================================================


def get_sync_redis_client() -> redis.Redis:
    """
    Get a synchronous Redis client connection.

    Uses the CELERY_BROKER_URL from settings to connect to Redis.
    The caller should use it in a with statement or close it manually.

    Returns:
        redis.Redis: A sync Redis client instance.

    Example:
        client = get_sync_redis_client()
        try:
            client.set("key", "value")
        finally:
            client.close()
    """
    return redis.from_url(
        settings.CELERY_BROKER_URL,
        encoding="utf-8",
        decode_responses=True
    )


# ============================================================================
# Async Redis Client
# ============================================================================


async def get_redis_client() -> redis.asyncio.Redis:
    """
    Get an async Redis client connection.

    Uses the CELERY_BROKER_URL from settings to connect to Redis.
    The caller is responsible for closing the client when done.

    Returns:
        redis.Redis: An async Redis client instance.

    Example:
        client = await get_redis_client()
        try:
            await client.set("key", "value")
        finally:
            await client.close()
    """
    return redis.asyncio.from_url(
        settings.CELERY_BROKER_URL,
        encoding="utf-8",
        decode_responses=True
    )


# ============================================================================
# Sync Cache Operations (for sync FastAPI endpoints)
# ============================================================================


def cache_response_sync(key: str, data: Any, ttl: int) -> bool:
    """
    Cache a JSON-serializable response with TTL (synchronous version).

    Args:
        key: Cache key (e.g., "products:list:100:0:None")
        data: JSON-serializable data to cache (dict, list, etc.)
        ttl: Time to live in seconds

    Returns:
        bool: True if caching succeeded, False otherwise

    Example:
        success = cache_response_sync(
            "products:list:100:0:None",
            {"items": [...], "total": 50},
            ttl=300
        )
    """
    try:
        client = get_sync_redis_client()
        try:
            json_data = json.dumps(data)
            client.setex(key, ttl, json_data)
            logger.debug(f"Cached response for key: {key}, TTL: {ttl}s")
            return True
        finally:
            client.close()
    except (redis.ConnectionError, redis.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to cache response: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error caching response: {e}")
        return False


def get_cached_response_sync(key: str) -> Optional[Any]:
    """
    Retrieve a cached response (synchronous version).

    Args:
        key: Cache key to look up

    Returns:
        The cached data if found and valid, None otherwise (cache miss)

    Example:
        cached = get_cached_response_sync("products:list:100:0:None")
        if cached:
            return cached  # Cache hit
        # Cache miss - fetch from database
    """
    try:
        client = get_sync_redis_client()
        try:
            raw_data = client.get(key)
            if raw_data is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            data = json.loads(raw_data)
            logger.debug(f"Cache hit for key: {key}")
            return data
        finally:
            client.close()
    except (redis.ConnectionError, redis.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to get cached response: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in cache for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting cached response: {e}")
        return None


def invalidate_pattern_sync(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern (synchronous version).

    Uses Redis KEYS command to find matching keys, then deletes them.

    Args:
        pattern: Redis key pattern (e.g., "products:list:*")

    Returns:
        int: Number of keys deleted

    Example:
        # Invalidate all product list cache
        deleted = invalidate_pattern_sync("products:list:*")
    """
    try:
        client = get_sync_redis_client()
        try:
            # Find all matching keys
            keys = client.keys(pattern)

            if not keys:
                logger.debug(f"No keys match pattern: {pattern}")
                return 0

            # Delete all matching keys
            deleted = client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
            return deleted
        finally:
            client.close()
    except (redis.ConnectionError, redis.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to invalidate cache pattern: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error invalidating cache: {e}")
        return 0


# ============================================================================
# Async Cache Operations
# ============================================================================


async def cache_response(key: str, data: Any, ttl: int) -> bool:
    """
    Cache a JSON-serializable response with TTL (async version).

    Args:
        key: Cache key (e.g., "products:list:100:0:None")
        data: JSON-serializable data to cache (dict, list, etc.)
        ttl: Time to live in seconds

    Returns:
        bool: True if caching succeeded, False otherwise

    Example:
        success = await cache_response(
            "products:list:100:0:None",
            {"items": [...], "total": 50},
            ttl=300
        )
    """
    try:
        client = await get_redis_client()
        try:
            json_data = json.dumps(data)
            await client.setex(key, ttl, json_data)
            logger.debug(f"Cached response for key: {key}, TTL: {ttl}s")
            return True
        finally:
            await client.close()
    except (redis.asyncio.ConnectionError, redis.asyncio.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to cache response: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error caching response: {e}")
        return False


async def get_cached_response(key: str) -> Optional[Any]:
    """
    Retrieve a cached response (async version).

    Args:
        key: Cache key to look up

    Returns:
        The cached data if found and valid, None otherwise (cache miss)

    Example:
        cached = await get_cached_response("products:list:100:0:None")
        if cached:
            return cached  # Cache hit
        # Cache miss - fetch from database
    """
    try:
        client = await get_redis_client()
        try:
            raw_data = await client.get(key)
            if raw_data is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            data = json.loads(raw_data)
            logger.debug(f"Cache hit for key: {key}")
            return data
        finally:
            await client.close()
    except (redis.asyncio.ConnectionError, redis.asyncio.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to get cached response: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in cache for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting cached response: {e}")
        return None


async def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern (async version).

    Uses Redis KEYS command to find matching keys, then deletes them.
    The pattern supports Redis glob-style patterns:
    - * matches any sequence of characters
    - ? matches any single character
    - [abc] matches any character in brackets

    Args:
        pattern: Redis key pattern (e.g., "products:list:*")

    Returns:
        int: Number of keys deleted

    Example:
        # Invalidate all product list cache
        deleted = await invalidate_pattern("products:list:*")

        # Invalidate all product cache (list + search)
        deleted = await invalidate_pattern("products:*")

    Warning:
        The KEYS command should be used with caution in production.
        For very large keyspaces, consider using SCAN instead.
    """
    try:
        client = await get_redis_client()
        try:
            # Find all matching keys
            keys = await client.keys(pattern)

            if not keys:
                logger.debug(f"No keys match pattern: {pattern}")
                return 0

            # Delete all matching keys
            deleted = await client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
            return deleted
        finally:
            await client.close()
    except (redis.asyncio.ConnectionError, redis.asyncio.TimeoutError, ConnectionError) as e:
        logger.warning(f"Failed to invalidate cache pattern: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error invalidating cache: {e}")
        return 0


# ============================================================================
# Cache Key Generation
# ============================================================================


def get_product_list_cache_key(
    limit: int,
    offset: int,
    is_finished: Optional[bool]
) -> str:
    """
    Generate cache key for product list endpoint.

    Key pattern: products:list:{limit}:{offset}:{is_finished}

    Args:
        limit: Pagination limit
        offset: Pagination offset
        is_finished: Filter for finished products (True/False/None)

    Returns:
        str: Cache key

    Example:
        key = get_product_list_cache_key(100, 0, True)
        # Returns: "products:list:100:0:True"
    """
    return f"products:list:{limit}:{offset}:{is_finished}"


def get_product_search_cache_key(
    query: Optional[str] = None,
    category_id: Optional[str] = None,
    industry: Optional[str] = None,
    manufacturer: Optional[str] = None,
    country_of_origin: Optional[str] = None,
    is_finished_product: Optional[bool] = None,
    has_bom: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> str:
    """
    Generate cache key for product search endpoint.

    Uses MD5 hash of search parameters to create a deterministic,
    fixed-length cache key. Parameters are sorted alphabetically
    to ensure the same parameters always produce the same key.

    Key pattern: products:search:{md5_hash}

    Args:
        query: Search query text
        category_id: Category filter
        industry: Industry sector filter
        manufacturer: Manufacturer filter
        country_of_origin: Country code filter
        is_finished_product: Finished product filter
        has_bom: Has BOM filter
        limit: Pagination limit
        offset: Pagination offset

    Returns:
        str: Cache key with MD5 hash

    Example:
        key = get_product_search_cache_key(query="laptop", limit=50, offset=0)
        # Returns: "products:search:a1b2c3d4..."
    """
    # Build params dict with all parameters
    params = {
        "query": query,
        "category_id": category_id,
        "industry": industry,
        "manufacturer": manufacturer,
        "country_of_origin": country_of_origin,
        "is_finished_product": is_finished_product,
        "has_bom": has_bom,
        "limit": limit,
        "offset": offset
    }

    # Sort keys for deterministic ordering
    sorted_params = sorted(params.items())

    # Create a string representation
    param_str = json.dumps(sorted_params, sort_keys=True)

    # Generate MD5 hash
    hash_value = hashlib.md5(param_str.encode()).hexdigest()

    return f"products:search:{hash_value}"


# ============================================================================
# Sync Convenience Functions for Product Endpoints
# ============================================================================


def get_cached_product_list_sync(
    limit: int,
    offset: int,
    is_finished: Optional[bool]
) -> Optional[Any]:
    """
    Get cached product list response (sync).

    Convenience function that generates the cache key and retrieves
    the cached response in one call.

    Args:
        limit: Pagination limit
        offset: Pagination offset
        is_finished: Filter for finished products

    Returns:
        Cached response data or None if not cached

    Example:
        cached = get_cached_product_list_sync(100, 0, None)
        if cached:
            return cached
    """
    key = get_product_list_cache_key(limit, offset, is_finished)
    return get_cached_response_sync(key)


def cache_product_list_sync(
    limit: int,
    offset: int,
    is_finished: Optional[bool],
    data: Any
) -> bool:
    """
    Cache product list response (sync).

    Convenience function that generates the cache key and caches
    the response with the appropriate TTL.

    Args:
        limit: Pagination limit
        offset: Pagination offset
        is_finished: Filter for finished products
        data: Response data to cache

    Returns:
        bool: True if caching succeeded

    Example:
        cache_product_list_sync(100, 0, None, response_data)
    """
    key = get_product_list_cache_key(limit, offset, is_finished)
    return cache_response_sync(key, data, PRODUCT_LIST_TTL)


def invalidate_product_list_cache_sync() -> int:
    """
    Invalidate all product list cache entries (sync).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After creating a product
        invalidate_product_list_cache_sync()
    """
    return invalidate_pattern_sync("products:list:*")


def invalidate_product_search_cache_sync() -> int:
    """
    Invalidate all product search cache entries (sync).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After updating a product
        invalidate_product_search_cache_sync()
    """
    return invalidate_pattern_sync("products:search:*")


def invalidate_all_product_cache_sync() -> int:
    """
    Invalidate all product-related cache entries - list and search (sync).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After deleting a product
        invalidate_all_product_cache_sync()
    """
    return invalidate_pattern_sync("products:*")


# ============================================================================
# Async Convenience Functions for Product Endpoints
# ============================================================================


async def get_cached_product_list(
    limit: int,
    offset: int,
    is_finished: Optional[bool]
) -> Optional[Any]:
    """
    Get cached product list response (async).

    Convenience function that generates the cache key and retrieves
    the cached response in one call.

    Args:
        limit: Pagination limit
        offset: Pagination offset
        is_finished: Filter for finished products

    Returns:
        Cached response data or None if not cached

    Example:
        cached = await get_cached_product_list(100, 0, None)
        if cached:
            return cached
    """
    key = get_product_list_cache_key(limit, offset, is_finished)
    return await get_cached_response(key)


async def cache_product_list(
    limit: int,
    offset: int,
    is_finished: Optional[bool],
    data: Any
) -> bool:
    """
    Cache product list response (async).

    Convenience function that generates the cache key and caches
    the response with the appropriate TTL.

    Args:
        limit: Pagination limit
        offset: Pagination offset
        is_finished: Filter for finished products
        data: Response data to cache

    Returns:
        bool: True if caching succeeded

    Example:
        await cache_product_list(100, 0, None, response_data)
    """
    key = get_product_list_cache_key(limit, offset, is_finished)
    return await cache_response(key, data, PRODUCT_LIST_TTL)


async def invalidate_product_list_cache() -> int:
    """
    Invalidate all product list cache entries (async).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After creating a product
        await invalidate_product_list_cache()
    """
    return await invalidate_pattern("products:list:*")


async def invalidate_product_search_cache() -> int:
    """
    Invalidate all product search cache entries (async).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After updating a product
        await invalidate_product_search_cache()
    """
    return await invalidate_pattern("products:search:*")


async def invalidate_all_product_cache() -> int:
    """
    Invalidate all product-related cache entries - list and search (async).

    Should be called after product create/update/delete operations.

    Returns:
        int: Number of cache entries invalidated

    Example:
        # After deleting a product
        await invalidate_all_product_cache()
    """
    return await invalidate_pattern("products:*")
