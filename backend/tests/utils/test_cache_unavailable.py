"""
Cache behaviour when Redis is not reachable.

Production (Railway) runs without Redis. Every cached request used to attempt a
connection, fail, and log two warnings; across a day that is thousands of
error-severity lines for a condition that never changes while the process runs.

Expected behaviour: the first failure logs one warning and marks the cache
unavailable for this process; later calls return the "miss"/"not cached" result
immediately without touching Redis or logging again.
"""

import logging

import pytest
import redis

import backend.utils.cache as cache_module


@pytest.fixture(autouse=True)
def fresh_cache_state():
    """Each test starts with the cache considered available."""
    cache_module.reset_cache_availability()
    yield
    cache_module.reset_cache_availability()


@pytest.fixture
def redis_down(monkeypatch):
    """Make every Redis client factory fail like a refused connection and count attempts."""
    attempts = {"sync": 0, "async": 0}

    def failing_sync_client():
        attempts["sync"] += 1
        raise redis.ConnectionError("Error 111 connecting to localhost:6379. Connection refused.")

    async def failing_async_client():
        attempts["async"] += 1
        raise redis.ConnectionError("Error 111 connecting to localhost:6379. Connection refused.")

    monkeypatch.setattr(cache_module, "get_sync_redis_client", failing_sync_client)
    monkeypatch.setattr(cache_module, "get_redis_client", failing_async_client)
    return attempts


def _cache_warnings(caplog) -> list[logging.LogRecord]:
    return [
        r for r in caplog.records
        if r.name == "backend.utils.cache" and r.levelno >= logging.WARNING
    ]


class TestSyncCacheWhenRedisIsDown:
    def test_first_failure_logs_one_warning_and_returns_miss(self, redis_down, caplog):
        caplog.set_level(logging.DEBUG, logger="backend.utils.cache")

        assert cache_module.get_cached_response_sync("products:list") is None

        warnings = _cache_warnings(caplog)
        assert len(warnings) == 1
        assert "unavailable" in warnings[0].getMessage().lower()
        assert cache_module.is_cache_available() is False

    def test_later_calls_do_not_reconnect_or_log(self, redis_down, caplog):
        caplog.set_level(logging.DEBUG, logger="backend.utils.cache")

        cache_module.get_cached_response_sync("products:list")
        for _ in range(5):
            assert cache_module.get_cached_response_sync("products:list") is None
            assert cache_module.cache_response_sync("products:list", {"items": []}, ttl=60) is False

        assert redis_down["sync"] == 1, "only the first call should try to connect"
        assert len(_cache_warnings(caplog)) == 1

    def test_reset_makes_the_cache_try_again(self, redis_down, caplog):
        caplog.set_level(logging.DEBUG, logger="backend.utils.cache")

        cache_module.get_cached_response_sync("products:list")
        cache_module.reset_cache_availability()
        cache_module.get_cached_response_sync("products:list")

        assert redis_down["sync"] == 2
        assert len(_cache_warnings(caplog)) == 2


class TestAsyncCacheWhenRedisIsDown:
    @pytest.mark.asyncio
    async def test_async_calls_share_the_same_state(self, redis_down, caplog):
        caplog.set_level(logging.DEBUG, logger="backend.utils.cache")

        assert await cache_module.get_cached_response("products:list") is None
        for _ in range(3):
            assert await cache_module.cache_response("products:list", {"items": []}, ttl=60) is False
            assert await cache_module.get_cached_response("products:list") is None
        assert await cache_module.invalidate_pattern("products:*") == 0

        assert redis_down["async"] == 1
        assert len(_cache_warnings(caplog)) == 1

    @pytest.mark.asyncio
    async def test_sync_failure_also_stops_async_attempts(self, redis_down, caplog):
        caplog.set_level(logging.DEBUG, logger="backend.utils.cache")

        cache_module.get_cached_response_sync("products:list")
        assert await cache_module.get_cached_response("products:list") is None

        assert redis_down == {"sync": 1, "async": 0}
        assert len(_cache_warnings(caplog)) == 1
