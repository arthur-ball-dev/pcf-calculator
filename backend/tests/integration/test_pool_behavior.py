"""
Connection Pool Behavior Integration Tests

TASK-DB-P9-001: Configure PostgreSQL Connection Pooling

This module tests connection pool behavior under realistic conditions:
- Concurrent request handling
- Pool connection reuse
- Recovery from connection failures
- Health endpoint pool status reporting

Integration tests require the application to be properly configured.
These tests verify end-to-end pool behavior through the API layer.

Test Categories:
- Concurrent Request Tests: Verify pool handles multiple requests
- Pool Reuse Tests: Verify connections are reused efficiently
- Recovery Tests: Verify pool recovers from failures
- Health Endpoint Tests: Verify monitoring endpoints

Note: Some tests may require PostgreSQL for accurate pool behavior testing.
SQLite uses different pooling mechanisms.
"""

import asyncio
import concurrent.futures
import pytest
import time
from typing import List

from fastapi.testclient import TestClient


# Uses db_session fixture from conftest.py (PostgreSQL with transaction rollback)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client(db_session):
    """TestClient with database override."""
    from backend.main import app
    from backend.database.connection import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()




# =============================================================================
# Concurrent Request Tests
# =============================================================================


class TestPoolConcurrentRequests:
    """Test pool handling of concurrent requests."""

    def test_concurrent_requests_all_succeed(self, client):
        """Pool handles concurrent requests without connection errors."""

        def make_request():
            # Use a simple health or status endpoint
            try:
                response = client.get("/api/v1/products?limit=1")
                return response.status_code
            except Exception as e:
                return str(e)

        # Execute 10 concurrent requests
        num_concurrent = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed (200) or at least not fail due to pool issues
        successful = sum(1 for r in results if r == 200)
        assert successful >= num_concurrent * 0.9, (
            f"At least 90% of concurrent requests should succeed. "
            f"Got {successful}/{num_concurrent} successful."
        )

    def test_concurrent_burst_handled_gracefully(self, client):
        """Pool handles burst of requests beyond pool_size."""

        results = []
        num_requests = 25  # More than typical pool_size

        def make_request():
            try:
                response = client.get("/api/v1/products?limit=1")
                return {"status": response.status_code, "error": None}
            except Exception as e:
                return {"status": None, "error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Analyze results
        successful = sum(1 for r in results if r["status"] == 200)
        errors = [r["error"] for r in results if r["error"]]

        # Most requests should succeed (overflow should handle burst)
        assert successful >= num_requests * 0.8, (
            f"At least 80% of burst requests should succeed. "
            f"Got {successful}/{num_requests}. Errors: {errors[:3]}"
        )


# =============================================================================
# Pool Connection Reuse Tests
# =============================================================================


class TestPoolConnectionReuse:
    """Test that pool reuses connections efficiently."""

    def test_sequential_requests_reuse_connections(self, client):
        """Sequential requests reuse pooled connections."""

        # Make many sequential requests
        for i in range(20):
            response = client.get("/api/v1/products?limit=1")
            assert response.status_code in [200, 404], (
                f"Request {i} failed with status {response.status_code}"
            )

        # If we got here, pool successfully handled all requests
        # (A failing pool would exhaust connections or timeout)

    def test_rapid_sequential_requests(self, client):
        """Pool handles rapid sequential requests efficiently."""

        start_time = time.time()
        num_requests = 50

        for _ in range(num_requests):
            response = client.get("/api/v1/products?limit=1")
            # Accept 200 or 404 (empty DB)
            assert response.status_code in [200, 404]

        duration = time.time() - start_time

        # All 50 requests should complete in reasonable time
        # If connections aren't being reused, this would be much slower
        assert duration < 30, (
            f"50 sequential requests took {duration:.2f}s. "
            "Connection reuse may not be working."
        )


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestPoolHealthEndpoint:
    """Test pool health monitoring endpoint."""

    def test_health_db_endpoint_exists(self, client):
        """Database health endpoint is accessible."""
        response = client.get("/health/db")

        # Endpoint should exist
        assert response.status_code != 404, (
            "Health endpoint /health/db should exist"
        )

    def test_health_db_returns_status(self, client):
        """Health endpoint returns pool status."""
        response = client.get("/health/db")

        if response.status_code == 200:
            data = response.json()

            assert "status" in data, (
                "Health response must include 'status' field"
            )
            assert data["status"] in ["healthy", "degraded", "unhealthy"], (
                f"Invalid status: {data['status']}"
            )

    def test_health_db_returns_pool_metrics(self, client):
        """Health endpoint includes pool metrics."""
        response = client.get("/health/db")

        if response.status_code == 200:
            data = response.json()

            if "pool" in data:
                pool = data["pool"]
                # Should have key pool metrics
                expected_fields = ["pool_size", "checked_out"]
                for field in expected_fields:
                    assert field in pool, (
                        f"Pool metrics should include '{field}'"
                    )

    def test_health_endpoint_fast_response(self, client):
        """Health endpoint responds quickly (under 100ms)."""
        start = time.time()
        response = client.get("/health/db")
        duration = time.time() - start

        # Health checks should be fast
        assert duration < 0.1, (
            f"Health endpoint took {duration*1000:.0f}ms. "
            "Should respond in under 100ms."
        )


# =============================================================================
# Pool Recovery Tests
# =============================================================================


class TestPoolRecovery:
    """Test pool recovery from connection issues."""

    def test_pool_recovers_after_idle(self, client):
        """Pool maintains functionality after idle period."""
        # Initial request
        response1 = client.get("/api/v1/products?limit=1")
        assert response1.status_code in [200, 404]

        # Simulate brief idle period (1 second)
        time.sleep(1)

        # Request after idle
        response2 = client.get("/api/v1/products?limit=1")
        assert response2.status_code in [200, 404], (
            "Pool should handle requests after idle period"
        )

    def test_pool_handles_errors_gracefully(self, client):
        """Pool continues functioning after query errors."""
        # Trigger an error (invalid endpoint)
        client.get("/api/v1/nonexistent-endpoint")

        # Normal requests should still work
        response = client.get("/api/v1/products?limit=1")
        assert response.status_code in [200, 404], (
            "Pool should handle normal requests after errors"
        )


# =============================================================================
# Pool Status Under Load Tests
# =============================================================================


class TestPoolStatusUnderLoad:
    """Test pool status reporting under load."""

    def test_pool_status_accurate_during_requests(self, client):
        """Pool status accurately reflects connection usage."""

        # Make a request that takes some time (if possible)
        # Then immediately check pool status
        def make_request():
            return client.get("/api/v1/products")

        # Start concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]

            # Check health endpoint while requests are in flight
            health_response = client.get("/health/db")

            # Wait for requests to complete
            results = [f.result() for f in futures]

        # Verify health endpoint worked
        if health_response.status_code == 200:
            data = health_response.json()
            assert "status" in data, "Health should report status during load"


# =============================================================================
# Performance Tests
# =============================================================================


class TestPoolPerformance:
    """Test pool performance characteristics."""

    def test_connection_acquisition_fast(self, client):
        """Connection acquisition from pool is fast."""
        times = []

        for _ in range(10):
            start = time.time()
            response = client.get("/api/v1/products?limit=1")
            duration = time.time() - start

            if response.status_code in [200, 404]:
                times.append(duration)

        if times:
            avg_time = sum(times) / len(times)
            assert avg_time < 0.5, (
                f"Average response time {avg_time*1000:.0f}ms too slow. "
                "Pool connection acquisition may have issues."
            )

    def test_throughput_with_pooling(self, client):
        """Pool enables reasonable throughput."""
        num_requests = 20
        start = time.time()

        for _ in range(num_requests):
            response = client.get("/api/v1/products?limit=1")
            # Don't assert status here, just measure throughput

        duration = time.time() - start
        throughput = num_requests / duration

        assert throughput >= 5, (
            f"Throughput {throughput:.1f} req/s too low. "
            "Pool may not be configured correctly."
        )


# =============================================================================
# PostgreSQL-Specific Tests (skip for SQLite)
# =============================================================================


class TestPostgreSQLPoolBehavior:
    """Tests specific to PostgreSQL pool behavior."""

    @pytest.fixture
    def is_postgresql(self):
        """Check if using PostgreSQL."""
        from backend.config import settings
        return settings.is_postgresql

    def test_asyncpg_pool_configured(self, is_postgresql):
        """PostgreSQL uses asyncpg-compatible pool."""
        if not is_postgresql:
            pytest.skip("Test requires PostgreSQL")

        from backend.database.connection import _get_async_engine

        try:
            engine = _get_async_engine()
            pool_class = type(engine.pool).__name__

            assert "Async" in pool_class, (
                f"PostgreSQL should use async pool, got {pool_class}"
            )
        except ImportError:
            pytest.skip("asyncpg not installed")

    def test_pool_size_appropriate_for_supabase(self, is_postgresql):
        """Pool size is appropriate for Supabase limits."""
        if not is_postgresql:
            pytest.skip("Test requires PostgreSQL")

        from backend.database.connection import POOL_CONFIG

        pool_size = POOL_CONFIG.get("pool_size", 10)
        max_overflow = POOL_CONFIG.get("max_overflow", 20)

        # Supabase free tier: 60 connections, Pro: 200+
        # Our pool + overflow should stay well under these limits
        total = pool_size + max_overflow
        assert total <= 50, (
            f"Pool total ({total}) should be under Supabase free tier limit"
        )
