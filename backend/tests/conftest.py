"""
Root pytest fixtures for PCF Calculator backend tests.

TASK-BE-P5-002: Docker Compose Integration Test Infrastructure
TASK-QA-P7-029: Backend Test Authentication Fixtures
TASK-DB-P9-008: PostgreSQL Migration for All Backend Tests

This module provides shared fixtures for all backend tests, including:
- PostgreSQL database session fixtures with transaction rollback isolation
- Redis availability checking for integration tests
- Common test utilities
- Authentication fixtures for JWT-protected endpoints (TASK-QA-P7-029)

Database Strategy (TASK-DB-P9-008):
    All tests now use PostgreSQL (`pcf_calculator_test` database) instead of SQLite.
    Test isolation is achieved through transaction rollback:
    - Each test runs within a transaction
    - After the test, the transaction is rolled back
    - This is faster than recreating schemas and matches production behavior

    PostgreSQL test database URL:
        postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test

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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session


# ============================================================================
# PostgreSQL Test Database Configuration (TASK-DB-P9-008)
# ============================================================================

# Test database URL - uses dedicated test database for isolation from dev
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test"
)

# Session-scoped engine to avoid repeated connections
_test_engine = None


def get_test_engine():
    """
    Get or create the PostgreSQL test database engine.

    Uses session-level caching for performance.
    The engine connects to pcf_calculator_test database.
    """
    global _test_engine
    if _test_engine is None:
        _test_engine = create_engine(
            TEST_DATABASE_URL,
            echo=False,
            pool_pre_ping=True,  # Verify connections are alive
            pool_size=5,
            max_overflow=10,
        )
    return _test_engine


def _check_postgres_available() -> bool:
    """Check if PostgreSQL test database is available."""
    try:
        engine = get_test_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"PostgreSQL test database not available: {e}")
        return False


# Check PostgreSQL availability at module load
_POSTGRES_AVAILABLE = None


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
# Database Fixtures (TASK-DB-P9-008: PostgreSQL with Transaction Rollback)
# ============================================================================


@pytest.fixture(scope="session")
def postgres_available():
    """
    Check if PostgreSQL test database is available.

    Returns True if pcf_calculator_test database is accessible.
    Used to skip tests if PostgreSQL is not running.
    """
    global _POSTGRES_AVAILABLE
    if _POSTGRES_AVAILABLE is None:
        _POSTGRES_AVAILABLE = _check_postgres_available()
    return _POSTGRES_AVAILABLE


@pytest.fixture(scope="session")
def require_postgres(postgres_available):
    """
    Fixture that fails fast if PostgreSQL test database is not available.

    All tests now require PostgreSQL - SQLite is no longer supported.
    """
    if not postgres_available:
        pytest.fail(
            "PostgreSQL test database not available. "
            "Start PostgreSQL with: docker-compose up -d pcf-postgres\n"
            "Ensure pcf_calculator_test database exists: "
            "python backend/scripts/setup_test_db.py"
        )
    return True


@pytest.fixture(scope="session")
def test_engine(require_postgres):
    """
    Get PostgreSQL test database engine.

    This fixture provides a session-scoped engine connected to the
    pcf_calculator_test database. The engine is shared across all tests
    for performance.

    TASK-DB-P9-008: Migrated from SQLite in-memory to PostgreSQL.

    Returns:
        Engine: SQLAlchemy engine connected to PostgreSQL test database
    """
    engine = get_test_engine()

    # Ensure schema exists (run migrations)
    from backend.models import Base
    Base.metadata.create_all(bind=engine)

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create database session with transaction rollback for test isolation.

    This fixture:
    1. Starts a transaction at the beginning of each test
    2. Creates a session bound to that transaction
    3. Rolls back the transaction after the test completes

    This approach:
    - Is faster than recreating schemas for each test
    - Matches production PostgreSQL behavior
    - Provides complete test isolation

    TASK-DB-P9-008: Migrated from SQLite in-memory to PostgreSQL.

    Args:
        test_engine: PostgreSQL engine from test_engine fixture

    Yields:
        Session: SQLAlchemy database session (auto-rollback after test)
    """
    # Start a connection and begin a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        # Close session and rollback transaction (cleanup)
        session.close()
        transaction.rollback()
        connection.close()


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
    config.addinivalue_line(
        "markers",
        "requires_postgres: mark test as requiring PostgreSQL (TASK-DB-P9-008)"
    )


# ============================================================================
# Test Database Setup/Teardown (TASK-DB-P9-008)
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    """
    Session-scoped fixture to set up and tear down the test database.

    Runs automatically at the start of the test session.
    Ensures the test database has the correct schema.
    """
    global _POSTGRES_AVAILABLE

    # Check if PostgreSQL is available
    _POSTGRES_AVAILABLE = _check_postgres_available()

    if not _POSTGRES_AVAILABLE:
        print("\n⚠️  PostgreSQL test database not available. Tests will fail.")
        print("   Start PostgreSQL: docker-compose up -d pcf-postgres")
        print("   Setup test DB: python backend/scripts/setup_test_db.py\n")
        return

    # Create schema if needed
    from backend.models import Base
    engine = get_test_engine()

    # Create all tables (idempotent)
    Base.metadata.create_all(bind=engine)

    print(f"\n✓ Connected to PostgreSQL test database: {TEST_DATABASE_URL}\n")

    yield

    # Cleanup after all tests complete (optional)
    # We don't drop tables since transaction rollback handles isolation


@pytest.fixture(scope="function")
def clean_db_session(db_session) -> Generator[Session, None, None]:
    """
    Provide a clean database session with explicit table truncation.

    Use this fixture when you need a completely clean database state,
    not just transaction isolation. This truncates all tables before
    the test runs.

    Note: Most tests should use `db_session` instead. This fixture is
    for special cases like seed data tests.
    """
    from backend.models import (
        Product, BillOfMaterials, EmissionFactor, PCFCalculation,
        CalculationDetail, DataSource, DataSyncLog, ProductCategory
    )

    # Truncate tables in dependency order (children first)
    tables = [
        CalculationDetail, PCFCalculation, BillOfMaterials,
        Product, EmissionFactor, DataSyncLog, DataSource, ProductCategory
    ]

    for table in tables:
        try:
            db_session.execute(text(f"TRUNCATE TABLE {table.__tablename__} CASCADE"))
        except Exception:
            pass  # Table might not exist in some test scenarios

    db_session.commit()

    yield db_session
