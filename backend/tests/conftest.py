"""
Root pytest fixtures for PCF Calculator backend tests.

TASK-BE-P5-002: Docker Compose Integration Test Infrastructure

This module provides shared fixtures for all backend tests, including:
- Database session fixtures
- Redis availability checking for integration tests
- Common test utilities

Redis Availability:
    The `redis_available` fixture checks if Redis is accessible at localhost:6379.
    Integration tests that require Redis should use this fixture with
    `pytest.mark.skipif` to gracefully skip when Redis is unavailable.

Usage:
    @pytest.mark.skipif(
        not pytest.lazy_fixture("redis_available"),
        reason="Redis not available"
    )
    def test_celery_task(redis_available):
        # Test code that requires Redis
        pass

    # Or using the require_redis fixture for automatic skipping:
    def test_celery_task(require_redis, celery_app):
        # Test code that requires Redis
        pass
"""

import os
import pytest


@pytest.fixture(scope="session")
def redis_available():
    """
    Check if Redis is available for integration tests.

    This fixture attempts to connect to Redis at localhost:6379 (or the
    configured REDIS_HOST:REDIS_PORT) and returns True if successful,
    False otherwise.

    The fixture uses scope="session" to only check once per test session,
    avoiding repeated connection attempts.

    Returns:
        bool: True if Redis is available, False otherwise.

    Environment Variables:
        REDIS_HOST: Redis hostname (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_DB: Redis database number for tests (default: 1)
    """
    try:
        import redis

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "1"))  # Use DB 1 for tests

        client = redis.Redis(host=host, port=port, db=db, socket_timeout=2)
        client.ping()
        client.close()
        return True
    except (redis.ConnectionError, redis.TimeoutError, ConnectionRefusedError):
        return False
    except ImportError:
        # redis package not installed
        return False
    except Exception:
        # Any other error means Redis is not available
        return False


@pytest.fixture(scope="session")
def require_redis(redis_available):
    """
    Fixture that skips the test if Redis is not available.

    Use this fixture as a dependency for tests that require Redis.
    The test will be skipped with an informative message if Redis
    cannot be reached.

    Usage:
        def test_celery_task(require_redis, celery_app):
            # This test will be skipped if Redis is not available
            pass

    Returns:
        bool: Always True (test is skipped before returning if Redis unavailable)
    """
    if not redis_available:
        pytest.skip(
            "Redis is not available. Start Redis with: "
            "docker-compose up -d redis"
        )
    return True


@pytest.fixture(scope="session")
def celery_config_integration(redis_available):
    """
    Celery configuration for integration testing with real Redis.

    This fixture provides Celery configuration that uses a separate
    Redis database (db=1) for tests to avoid interfering with
    development data.

    Returns:
        dict: Celery configuration dictionary
    """
    if not redis_available:
        pytest.skip("Redis required for Celery integration tests")

    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))

    return {
        "broker_url": f"redis://{host}:{port}/1",  # Test database
        "result_backend": f"redis://{host}:{port}/1",
        "task_always_eager": False,  # Use real async execution
        "task_eager_propagates": True,
        "task_track_started": True,
        "task_time_limit": 60,  # Shorter timeout for tests
        "task_soft_time_limit": 50,
    }


@pytest.fixture
def redis_client(require_redis):
    """
    Provide a Redis client for tests that need direct Redis access.

    The client is automatically closed after the test completes.

    Returns:
        redis.Redis: Connected Redis client
    """
    import redis

    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "1"))

    client = redis.Redis(host=host, port=port, db=db)
    yield client
    client.close()


@pytest.fixture
def clean_redis(redis_client):
    """
    Provide a clean Redis database for tests.

    This fixture flushes the test Redis database before each test
    to ensure test isolation.

    Warning:
        This flushes ALL keys in the test database (db=1).
        Never use on production databases!

    Returns:
        redis.Redis: Redis client with empty database
    """
    redis_client.flushdb()
    yield redis_client
    # Optionally clean up after test as well
    redis_client.flushdb()


# Register custom pytest markers
def pytest_configure(config):
    """Register custom markers for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (may require external services)"
    )
    config.addinivalue_line(
        "markers",
        "requires_redis: mark test as requiring Redis"
    )


# Make fixtures from subfolder conftest files available
pytest_plugins = [
    "backend.tests.fixtures.conftest",
]
