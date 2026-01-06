"""
Root pytest fixtures for PCF Calculator backend tests.

TASK-BE-P5-002: Docker Compose Integration Test Infrastructure
TASK-QA-P7-029: Backend Test Authentication Fixtures

This module provides shared fixtures for all backend tests, including:
- Database session fixtures
- Redis availability checking for integration tests
- Common test utilities
- Authentication fixtures for JWT-protected endpoints (TASK-QA-P7-029)

Redis Availability:
    The `redis_available` fixture checks if Redis is accessible at localhost:6379.
    Integration tests that require Redis should use this fixture with
    `pytest.mark.skipif` to gracefully skip when Redis is unavailable.

Authentication Fixtures (TASK-QA-P7-029):
    The following fixtures provide authentication for tests accessing protected endpoints:
    - `test_user_factory`: Factory fixture to create test users
    - `test_user`: Standard user with 'user' role
    - `test_admin`: Admin user with 'admin' role
    - `auth_headers`: JWT Authorization headers for standard user
    - `admin_auth_headers`: JWT Authorization headers for admin user
    - `authenticated_client`: TestClient with user authentication
    - `admin_client`: TestClient with admin authentication

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

    # Authentication examples:
    def test_protected_endpoint(authenticated_client):
        # Uses standard user authentication
        response = authenticated_client.get("/api/v1/products")
        assert response.status_code == 200

    def test_admin_endpoint(admin_client):
        # Uses admin authentication
        response = admin_client.post("/admin/data-sources/123/sync")
        assert response.status_code == 202
"""

import os

# Set test JWT secret before importing any backend modules (P0 security fix)
# This must happen before any imports that trigger backend.config loading
os.environ.setdefault(
    "PCF_CALC_JWT_SECRET_KEY",
    "test-secret-key-for-pytest-only-32-chars-minimum"
)

import pytest
from typing import Generator, Callable

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# ============================================================================
# Redis Fixtures
# ============================================================================


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


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_engine():
    """
    Create in-memory SQLite engine for testing.

    This fixture creates a fresh in-memory database for each test function
    with proper SQLite configuration for thread safety and foreign key support.

    Returns:
        Engine: SQLAlchemy engine configured for testing
    """
    from backend.models import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create database session for testing.

    Provides a SQLAlchemy session connected to the test database.
    The session is automatically closed after the test completes.

    Args:
        test_engine: SQLAlchemy engine from test_engine fixture

    Yields:
        Session: SQLAlchemy database session
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with database override.

    Provides a TestClient that uses the test database session
    instead of the production database.

    Note: This client does NOT include authentication headers.
    For protected endpoints, use `authenticated_client` or `admin_client`.

    Args:
        db_session: Database session from db_session fixture

    Yields:
        TestClient: FastAPI test client
    """
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


# ============================================================================
# Authentication Fixtures (TASK-QA-P7-029)
# ============================================================================


@pytest.fixture(scope="function")
def test_user_factory(db_session) -> Generator[Callable, None, None]:
    """
    Factory fixture to create test users.

    Provides a function that creates User objects in the test database.
    Created users are automatically cleaned up after the test completes.

    Args:
        db_session: Database session from db_session fixture

    Yields:
        Callable: Function to create test users
    """
    from backend.models.user import User
    from backend.auth.password import hash_password

    created_users = []

    def _create_user(
        username: str = "testuser",
        email: str = "testuser@example.com",
        role: str = "user",
        is_active: bool = True,
        password: str = "testpassword123"
    ) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created_users.append(user)
        return user

    yield _create_user

    for user in created_users:
        try:
            db_session.delete(user)
        except Exception:
            pass
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()


@pytest.fixture(scope="function")
def test_user(test_user_factory):
    """Create a standard test user with 'user' role."""
    return test_user_factory(
        username="testuser",
        email="testuser@example.com",
        role="user"
    )


@pytest.fixture(scope="function")
def test_admin(test_user_factory):
    """Create a test admin user with 'admin' role."""
    return test_user_factory(
        username="testadmin",
        email="testadmin@example.com",
        role="admin"
    )


@pytest.fixture(scope="function")
def auth_headers(test_user) -> dict:
    """Generate authorization headers with valid user JWT."""
    from backend.auth.jwt import create_access_token

    token = create_access_token(data={
        "user_id": test_user.id,
        "username": test_user.username,
        "role": test_user.role
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(test_admin) -> dict:
    """Generate authorization headers with valid admin JWT."""
    from backend.auth.jwt import create_access_token

    token = create_access_token(data={
        "user_id": test_admin.id,
        "username": test_admin.username,
        "role": test_admin.role
    })
    return {"Authorization": f"Bearer {token}"}


class AuthenticatedTestClient:
    """TestClient wrapper that automatically includes authentication headers."""

    def __init__(self, client: TestClient, headers: dict):
        self._client = client
        self._headers = headers

    def _merge_headers(self, kwargs: dict) -> dict:
        request_headers = kwargs.pop("headers", {})
        merged = {**self._headers, **request_headers}
        kwargs["headers"] = merged
        return kwargs

    def get(self, url: str, **kwargs):
        return self._client.get(url, **self._merge_headers(kwargs))

    def post(self, url: str, **kwargs):
        return self._client.post(url, **self._merge_headers(kwargs))

    def put(self, url: str, **kwargs):
        return self._client.put(url, **self._merge_headers(kwargs))

    def patch(self, url: str, **kwargs):
        return self._client.patch(url, **self._merge_headers(kwargs))

    def delete(self, url: str, **kwargs):
        return self._client.delete(url, **self._merge_headers(kwargs))

    def options(self, url: str, **kwargs):
        return self._client.options(url, **self._merge_headers(kwargs))

    def head(self, url: str, **kwargs):
        return self._client.head(url, **self._merge_headers(kwargs))


@pytest.fixture(scope="function")
def authenticated_client(client, auth_headers) -> AuthenticatedTestClient:
    """TestClient wrapper with user auth headers."""
    return AuthenticatedTestClient(client, auth_headers)


@pytest.fixture(scope="function")
def admin_client(client, admin_auth_headers) -> AuthenticatedTestClient:
    """TestClient wrapper with admin auth headers."""
    return AuthenticatedTestClient(client, admin_auth_headers)


# ============================================================================
# Pytest Configuration
# ============================================================================


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
    config.addinivalue_line(
        "markers",
        "requires_auth: mark test as requiring authentication"
    )
