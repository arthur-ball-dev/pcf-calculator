"""
Pytest fixtures for integration tests.

TASK-BE-P5-002: Docker Compose Integration Test Infrastructure

This module provides fixtures specific to integration tests, including
automatic Redis availability checking and test skipping.
"""

import os
import pytest


@pytest.fixture(scope="module", autouse=True)
def check_redis_for_celery_tests(request, redis_available):
    """
    Automatically skip Celery integration tests if Redis is not available.

    This fixture is module-scoped and autouse=True, meaning it will run
    automatically for all tests in the integration test modules.

    Tests that mock Redis (like health check tests) will still run because
    they don't actually connect to Redis.
    """
    # Only check for test_celery.py module - other integration tests may not need Redis
    if "test_celery" in request.fspath.basename:
        # Check if this specific test class/method uses celery_app_integration
        # Those tests need Redis, others may mock it
        pass  # The require_redis fixture will handle skipping

    return redis_available


@pytest.fixture
def celery_eager_mode():
    """
    Configure Celery to run tasks eagerly (synchronously) for testing.

    This allows tests to run without a real Celery worker, but still
    requires Redis for the broker/result backend unless using memory backend.
    """
    from backend.core.celery_app import celery_app

    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates

    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )

    yield celery_app

    celery_app.conf.update(
        task_always_eager=original_always_eager,
        task_eager_propagates=original_eager_propagates,
    )


@pytest.fixture
def celery_memory_backend():
    """
    Configure Celery to use memory backend for testing without Redis.

    This is useful for unit tests that don't need persistent results.
    Note: This changes the global Celery configuration temporarily.
    """
    from backend.core.celery_app import celery_app

    original_broker = celery_app.conf.broker_url
    original_backend = celery_app.conf.result_backend

    celery_app.conf.update(
        broker_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,
        task_eager_propagates=True,
    )

    yield celery_app

    celery_app.conf.update(
        broker_url=original_broker,
        result_backend=original_backend,
    )
