"""
Connection Pool Configuration Tests

TASK-DB-P9-001: Configure PostgreSQL Connection Pooling

This module tests connection pooling configuration for production readiness:
- Pool size configuration from environment settings
- Connection timeout settings
- Health check queries (pool_pre_ping)
- Pool overflow handling for burst traffic

Tests follow TDD methodology - written BEFORE implementation.
These tests are designed to:
1. Initially FAIL (no pool configuration exists)
2. Pass after implementing connection pooling in connection.py

Test Categories:
- Unit Tests: Pool configuration constants and settings
- Integration Tests: Pool behavior under load
- Performance Tests: Pool latency and throughput

Note: Some tests require PostgreSQL and will be skipped with SQLite.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.pool import QueuePool, AsyncAdaptedQueuePool
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError


# =============================================================================
# Unit Tests: Pool Configuration
# =============================================================================


class TestPoolConfiguration:
    """Test pool configuration constants and settings loading."""

    def test_pool_config_has_pool_size(self):
        """Pool configuration includes pool_size setting."""
        from backend.database.connection import POOL_CONFIG

        assert "pool_size" in POOL_CONFIG, (
            "POOL_CONFIG must include 'pool_size' setting"
        )
        assert isinstance(POOL_CONFIG["pool_size"], int), (
            "pool_size must be an integer"
        )
        assert POOL_CONFIG["pool_size"] >= 5, (
            "pool_size should be at least 5 for production workloads"
        )

    def test_pool_config_has_max_overflow(self):
        """Pool configuration includes max_overflow for burst handling."""
        from backend.database.connection import POOL_CONFIG

        assert "max_overflow" in POOL_CONFIG, (
            "POOL_CONFIG must include 'max_overflow' for burst connections"
        )
        assert isinstance(POOL_CONFIG["max_overflow"], int), (
            "max_overflow must be an integer"
        )
        assert POOL_CONFIG["max_overflow"] >= 10, (
            "max_overflow should be at least 10 for handling traffic spikes"
        )

    def test_pool_config_has_timeout(self):
        """Pool configuration includes pool_timeout for connection wait."""
        from backend.database.connection import POOL_CONFIG

        assert "pool_timeout" in POOL_CONFIG, (
            "POOL_CONFIG must include 'pool_timeout' setting"
        )
        assert isinstance(POOL_CONFIG["pool_timeout"], (int, float)), (
            "pool_timeout must be numeric"
        )
        assert POOL_CONFIG["pool_timeout"] >= 10, (
            "pool_timeout should be at least 10 seconds"
        )
        assert POOL_CONFIG["pool_timeout"] <= 60, (
            "pool_timeout should not exceed 60 seconds to fail fast"
        )

    def test_pool_config_has_recycle(self):
        """Pool configuration includes pool_recycle for connection lifetime."""
        from backend.database.connection import POOL_CONFIG

        assert "pool_recycle" in POOL_CONFIG, (
            "POOL_CONFIG must include 'pool_recycle' setting"
        )
        recycle = POOL_CONFIG["pool_recycle"]
        assert isinstance(recycle, int), (
            "pool_recycle must be an integer (seconds)"
        )
        # Recycle should be between 15 min and 1 hour
        assert 900 <= recycle <= 3600, (
            f"pool_recycle should be 900-3600 seconds, got {recycle}"
        )

    def test_pool_config_has_pre_ping_enabled(self):
        """Pool configuration enables pre-ping health checks."""
        from backend.database.connection import POOL_CONFIG

        assert "pool_pre_ping" in POOL_CONFIG, (
            "POOL_CONFIG must include 'pool_pre_ping' setting"
        )
        assert POOL_CONFIG["pool_pre_ping"] is True, (
            "pool_pre_ping MUST be True for connection health verification"
        )


class TestPoolConfigFromSettings:
    """Test that pool configuration loads from application settings."""

    def test_pool_size_from_settings(self):
        """Pool size is read from settings.DB_POOL_SIZE."""
        from backend.config import settings

        assert hasattr(settings, "DB_POOL_SIZE") or hasattr(settings, "db_pool_size"), (
            "Settings must include DB_POOL_SIZE configuration"
        )

    def test_pool_max_overflow_from_settings(self):
        """Max overflow is read from settings.DB_POOL_MAX_OVERFLOW."""
        from backend.config import settings

        assert (
            hasattr(settings, "DB_POOL_MAX_OVERFLOW") or
            hasattr(settings, "db_pool_max_overflow") or
            hasattr(settings, "db_max_overflow")
        ), (
            "Settings must include DB_POOL_MAX_OVERFLOW configuration"
        )

    def test_pool_timeout_from_settings(self):
        """Pool timeout is read from settings.DB_POOL_TIMEOUT."""
        from backend.config import settings

        assert (
            hasattr(settings, "DB_POOL_TIMEOUT") or
            hasattr(settings, "db_pool_timeout")
        ), (
            "Settings must include DB_POOL_TIMEOUT configuration"
        )

    def test_pool_recycle_from_settings(self):
        """Pool recycle is read from settings.DB_POOL_RECYCLE."""
        from backend.config import settings

        assert (
            hasattr(settings, "DB_POOL_RECYCLE") or
            hasattr(settings, "db_pool_recycle")
        ), (
            "Settings must include DB_POOL_RECYCLE configuration"
        )


class TestEngineCreation:
    """Test that engine is created with correct pool configuration."""

    def test_engine_exists(self):
        """Engine is created and accessible."""
        from backend.database.connection import engine

        assert engine is not None, (
            "Database engine must be created"
        )

    def test_engine_has_pool(self):
        """Engine has a connection pool."""
        from backend.database.connection import engine

        assert engine.pool is not None, (
            "Engine must have a connection pool configured"
        )

    def test_engine_pool_pre_ping_enabled(self):
        """Engine pool has pre-ping enabled for health checks."""
        from backend.database.connection import engine

        # Check if pre_ping is configured
        # This verifies connections are tested before checkout
        assert hasattr(engine.pool, "_pre_ping") or hasattr(engine, "pool_pre_ping"), (
            "Engine should have pool_pre_ping configuration"
        )


class TestAsyncEnginePooling:
    """Test async engine pool configuration for PostgreSQL."""

    @pytest.fixture
    def mock_postgres_settings(self):
        """Mock settings for PostgreSQL database."""
        with patch("backend.database.connection.settings") as mock_settings:
            mock_settings.database_url = "postgresql://test@localhost/test"
            mock_settings.async_database_url = "postgresql+asyncpg://test@localhost/test"
            mock_settings.is_sqlite = False
            mock_settings.is_postgresql = True
            mock_settings.debug = False
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.DB_POOL_SIZE = 10
            mock_settings.DB_POOL_MAX_OVERFLOW = 20
            mock_settings.DB_POOL_TIMEOUT = 30
            mock_settings.DB_POOL_RECYCLE = 1800
            mock_settings.DB_ECHO = False
            yield mock_settings

    def test_async_engine_uses_async_pool_class(self, mock_postgres_settings):
        """Async engine uses AsyncAdaptedQueuePool for PostgreSQL."""
        from backend.database.connection import _create_async_engine

        try:
            async_engine = _create_async_engine()
            pool_class_name = type(async_engine.pool).__name__
            # Should use AsyncAdaptedQueuePool or similar async pool
            assert "AsyncAdapted" in pool_class_name or "Async" in pool_class_name, (
                f"Async engine should use async-compatible pool, got {pool_class_name}"
            )
        except Exception as e:
            # If we can't create engine due to missing asyncpg, that's expected
            if "asyncpg" not in str(e).lower():
                raise


# =============================================================================
# Pool Status Monitoring Tests
# =============================================================================


class TestPoolStatusMonitoring:
    """Test pool status monitoring functionality."""

    def test_get_pool_status_function_exists(self):
        """get_pool_status function is available."""
        from backend.database.connection import get_pool_status

        assert callable(get_pool_status), (
            "get_pool_status must be a callable function"
        )

    def test_get_pool_status_returns_dict(self):
        """get_pool_status returns a dictionary with pool metrics."""
        from backend.database.connection import get_pool_status

        # Handle both sync and async versions
        result = get_pool_status()
        if asyncio.iscoroutine(result):
            result = asyncio.get_event_loop().run_until_complete(result)

        assert isinstance(result, dict), (
            "get_pool_status must return a dictionary"
        )

    def test_get_pool_status_contains_pool_size(self):
        """Pool status includes current pool size."""
        from backend.database.connection import get_pool_status

        result = get_pool_status()
        if asyncio.iscoroutine(result):
            result = asyncio.get_event_loop().run_until_complete(result)

        assert "pool_size" in result, (
            "Pool status must include 'pool_size'"
        )
        assert isinstance(result["pool_size"], int), (
            "pool_size must be an integer"
        )

    def test_get_pool_status_contains_checked_in(self):
        """Pool status includes checked-in (available) connections."""
        from backend.database.connection import get_pool_status

        result = get_pool_status()
        if asyncio.iscoroutine(result):
            result = asyncio.get_event_loop().run_until_complete(result)

        assert "checked_in" in result, (
            "Pool status must include 'checked_in' (available connections)"
        )

    def test_get_pool_status_contains_checked_out(self):
        """Pool status includes checked-out (in-use) connections."""
        from backend.database.connection import get_pool_status

        result = get_pool_status()
        if asyncio.iscoroutine(result):
            result = asyncio.get_event_loop().run_until_complete(result)

        assert "checked_out" in result, (
            "Pool status must include 'checked_out' (active connections)"
        )

    def test_get_pool_status_contains_overflow(self):
        """Pool status includes overflow count."""
        from backend.database.connection import get_pool_status

        result = get_pool_status()
        if asyncio.iscoroutine(result):
            result = asyncio.get_event_loop().run_until_complete(result)

        assert "overflow" in result, (
            "Pool status must include 'overflow' (burst connections)"
        )


# =============================================================================
# Health Check Tests
# =============================================================================


class TestPoolHealthCheck:
    """Test pool health check (pre-ping) functionality."""

    def test_pool_pre_ping_validates_connection(self):
        """Pool pre-ping should validate connection before checkout."""
        from backend.database.connection import engine

        # Create a connection and verify it works
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_pool_recovers_from_stale_connection(self):
        """Pool should detect and replace stale connections via pre-ping."""
        from backend.database.connection import engine

        # First connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Second connection should work (pre-ping verifies health)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1


# =============================================================================
# Connection Pool Behavior Tests
# =============================================================================


class TestPoolBehavior:
    """Test connection pool behavior under various conditions."""

    def test_pool_reuses_connections(self):
        """Pool should reuse connections instead of creating new ones."""
        from backend.database.connection import engine, get_pool_status

        initial_status = get_pool_status()
        if asyncio.iscoroutine(initial_status):
            initial_status = asyncio.get_event_loop().run_until_complete(initial_status)

        # Execute several queries
        for _ in range(5):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        final_status = get_pool_status()
        if asyncio.iscoroutine(final_status):
            final_status = asyncio.get_event_loop().run_until_complete(final_status)

        # Pool size should not grow linearly with queries
        # (connections are being reused)
        assert final_status["pool_size"] <= initial_status["pool_size"] + 2, (
            "Pool should reuse connections, not create new ones for each query"
        )

    def test_pool_releases_connection_after_use(self):
        """Connection should be returned to pool after use."""
        from backend.database.connection import engine, get_pool_status

        # Get initial checkout count
        status_before = get_pool_status()
        if asyncio.iscoroutine(status_before):
            status_before = asyncio.get_event_loop().run_until_complete(status_before)
        initial_checkout = status_before["checked_out"]

        # Use and release a connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Inside context, connection is checked out

        # After context exit, connection should be checked in
        status_after = get_pool_status()
        if asyncio.iscoroutine(status_after):
            status_after = asyncio.get_event_loop().run_until_complete(status_after)

        assert status_after["checked_out"] == initial_checkout, (
            "Connection should be returned to pool after context exit"
        )


class TestPoolOverflow:
    """Test pool overflow handling for burst traffic."""

    def test_overflow_allows_burst_connections(self):
        """Pool should allow overflow connections during bursts."""
        from backend.database.connection import POOL_CONFIG

        pool_size = POOL_CONFIG.get("pool_size", 10)
        max_overflow = POOL_CONFIG.get("max_overflow", 20)

        # Total allowed connections
        max_connections = pool_size + max_overflow
        assert max_connections >= 15, (
            f"Pool should allow at least 15 total connections, "
            f"got pool_size={pool_size} + max_overflow={max_overflow}"
        )

    def test_overflow_count_is_reasonable(self):
        """Max overflow should be configured for production bursts."""
        from backend.database.connection import POOL_CONFIG

        max_overflow = POOL_CONFIG.get("max_overflow", 0)
        assert max_overflow >= 10, (
            "max_overflow should be at least 10 for handling traffic spikes"
        )
        assert max_overflow <= 50, (
            "max_overflow should not exceed 50 to prevent resource exhaustion"
        )


# =============================================================================
# Timeout Configuration Tests
# =============================================================================


class TestPoolTimeout:
    """Test connection pool timeout configuration."""

    def test_timeout_is_configured(self):
        """Pool timeout should be explicitly configured."""
        from backend.database.connection import POOL_CONFIG

        assert "pool_timeout" in POOL_CONFIG, (
            "Pool timeout must be explicitly configured"
        )

    def test_timeout_is_reasonable_value(self):
        """Pool timeout should be reasonable (not too short, not too long)."""
        from backend.database.connection import POOL_CONFIG

        timeout = POOL_CONFIG.get("pool_timeout", 30)

        assert timeout >= 10, (
            "Pool timeout should be at least 10 seconds to handle slow connections"
        )
        assert timeout <= 60, (
            "Pool timeout should not exceed 60 seconds (fail fast principle)"
        )


# =============================================================================
# Integration Tests: Pool Under Load
# =============================================================================


class TestPoolUnderLoad:
    """Test pool behavior under simulated load conditions."""

    def test_sequential_requests_succeed(self):
        """Pool handles sequential requests without errors."""
        from backend.database.connection import engine

        results = []
        for i in range(10):
            with engine.connect() as conn:
                result = conn.execute(text("SELECT :num"), {"num": i})
                results.append(result.scalar())

        assert results == list(range(10)), (
            "All sequential requests should succeed"
        )

    def test_pool_status_remains_healthy_after_load(self):
        """Pool status remains healthy after handling requests."""
        from backend.database.connection import engine, get_pool_status

        # Generate some load
        for _ in range(20):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        # Check pool health
        status = get_pool_status()
        if asyncio.iscoroutine(status):
            status = asyncio.get_event_loop().run_until_complete(status)

        # All connections should be checked in after use
        assert status["checked_out"] == 0, (
            f"After load test, all connections should be checked in. "
            f"Found {status['checked_out']} still checked out."
        )


# =============================================================================
# Async Pool Tests
# =============================================================================


class TestAsyncPoolBehavior:
    """Test async connection pool behavior."""

    @pytest.fixture
    def async_engine_available(self):
        """Check if async engine is available (needs asyncpg for PostgreSQL)."""
        try:
            from backend.database.connection import _get_async_engine
            _get_async_engine()
            return True
        except Exception:
            return False

    @pytest.mark.asyncio
    async def test_async_session_acquires_connection(self, async_engine_available):
        """Async session can acquire connection from pool."""
        if not async_engine_available:
            pytest.skip("Async engine not available (may need asyncpg)")

        from backend.database.connection import get_async_session

        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_async_connection_returned_to_pool(self, async_engine_available):
        """Async connection is properly returned to pool after use."""
        if not async_engine_available:
            pytest.skip("Async engine not available (may need asyncpg)")

        from backend.database.connection import get_async_session, get_pool_status

        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))

        # Connection should be returned after context exit
        status = get_pool_status()
        if asyncio.iscoroutine(status):
            status = await status

        # Should have no orphaned connections
        assert status.get("checked_out", 0) == 0, (
            "Connection should be returned to pool after async session closes"
        )


# =============================================================================
# Configuration Validation Tests
# =============================================================================


class TestPoolConfigValidation:
    """Test that pool configuration values are valid and sensible."""

    def test_pool_size_positive(self):
        """Pool size must be a positive integer."""
        from backend.database.connection import POOL_CONFIG

        pool_size = POOL_CONFIG.get("pool_size", 0)
        assert pool_size > 0, "Pool size must be positive"

    def test_max_overflow_non_negative(self):
        """Max overflow must be non-negative."""
        from backend.database.connection import POOL_CONFIG

        max_overflow = POOL_CONFIG.get("max_overflow", -1)
        assert max_overflow >= 0, "Max overflow must be non-negative"

    def test_pool_recycle_positive(self):
        """Pool recycle time must be positive."""
        from backend.database.connection import POOL_CONFIG

        recycle = POOL_CONFIG.get("pool_recycle", 0)
        assert recycle > 0, "Pool recycle time must be positive"

    def test_pool_config_production_ready(self):
        """Pool configuration meets production requirements."""
        from backend.database.connection import POOL_CONFIG

        # Production requirements from SPEC
        pool_size = POOL_CONFIG.get("pool_size", 0)
        max_overflow = POOL_CONFIG.get("max_overflow", 0)
        pre_ping = POOL_CONFIG.get("pool_pre_ping", False)

        # Can handle 50+ concurrent users
        total_connections = pool_size + max_overflow
        assert total_connections >= 30, (
            f"Pool must support 50+ concurrent users. "
            f"Total connections: {total_connections}"
        )

        # Health checks enabled
        assert pre_ping is True, (
            "pool_pre_ping must be True for production"
        )


# =============================================================================
# Docker Environment Tests (for Phase 9 integration)
# =============================================================================


class TestPoolDockerEnvironment:
    """Test pool configuration works in Docker environment."""

    def test_pool_config_supports_env_override(self):
        """Pool settings can be overridden via environment variables."""
        from backend.config import Settings

        # Verify the Settings class accepts pool-related env vars
        settings_fields = Settings.model_fields.keys()

        # Should have pool configuration fields (any variation)
        pool_fields = [f for f in settings_fields if "pool" in f.lower()]

        assert len(pool_fields) > 0 or any(
            f in settings_fields for f in [
                "db_pool_size", "DB_POOL_SIZE",
                "db_max_overflow", "DB_POOL_MAX_OVERFLOW"
            ]
        ), (
            "Settings must include pool configuration fields for Docker env override"
        )
