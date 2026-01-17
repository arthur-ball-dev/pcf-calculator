"""
Database connection management for PCF Calculator
Provides SQLAlchemy engine, session management, and FastAPI dependency injection

This module handles:
- PostgreSQL database connection with connection pooling
- Connection pooling (QueuePool for PostgreSQL)
- Session lifecycle management (sync and async)
- FastAPI dependency injection for database sessions
- Pool status monitoring for health checks

TASK-DB-P9-001: Added POOL_CONFIG and get_pool_status for production readiness.
TASK-DB-P9-SQLITE-REMOVAL: Removed SQLite support - PostgreSQL only.
"""

from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool, AsyncAdaptedQueuePool

from backend.config import settings


# =============================================================================
# Connection Pool Configuration (TASK-DB-P9-001)
# =============================================================================

# Pool configuration constants for production readiness
# These settings ensure:
# - Adequate connections for 50+ concurrent users
# - Health checks before connection checkout (pool_pre_ping)
# - Connection recycling to prevent stale connections
# - Burst handling via max_overflow
POOL_CONFIG: Dict[str, Any] = {
    "pool_size": settings.db_pool_size,           # Steady-state connections (default: 10)
    "max_overflow": settings.db_max_overflow,     # Burst connections (default: 20)
    "pool_timeout": settings.db_pool_timeout,     # Wait time for connection (default: 30s)
    "pool_recycle": settings.db_pool_recycle,     # Recycle connections (default: 1800s = 30 min)
    "pool_pre_ping": True,                        # Health check before use (CRITICAL for production)
}


def _create_engine():
    """
    Create the SQLAlchemy engine for PostgreSQL.

    Returns an engine configured for PostgreSQL with connection pooling.

    PostgreSQL Configuration:
    - Connection pooling with configurable pool size
    - pool_pre_ping for connection health checks
    - Uses sync_database_url for URL normalization (handles Railway's postgres://)
    """
    # Use sync_database_url which normalizes postgres:// to postgresql://
    db_url = settings.sync_database_url

    if not settings.is_postgresql:
        raise ValueError(
            f"Only PostgreSQL is supported. Got: {settings.database_url}. "
            "Use postgresql:// or postgres:// prefix."
        )

    # PostgreSQL configuration with full pooling support
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=POOL_CONFIG["pool_size"],
        max_overflow=POOL_CONFIG["max_overflow"],
        pool_timeout=POOL_CONFIG["pool_timeout"],
        pool_recycle=POOL_CONFIG["pool_recycle"],
        pool_pre_ping=POOL_CONFIG["pool_pre_ping"],
        echo=settings.debug,  # Log SQL queries in debug mode
    )
    return engine


# Create SQLAlchemy engine
engine = _create_engine()


# Session factory for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,  # Explicit transaction control
    autoflush=False,  # Manual flush control for better performance
    bind=engine
)


def get_engine():
    """
    Get the SQLAlchemy engine instance.

    Used for direct database operations and testing.

    Returns:
        Engine: SQLAlchemy engine
    """
    return engine


def get_pool_status() -> Dict[str, Any]:
    """
    Get current connection pool status for monitoring.

    Returns a dictionary with pool metrics useful for health checks
    and performance monitoring.

    Returns:
        dict with pool metrics:
        - pool_size: Configured pool size
        - checked_in: Available connections in pool
        - checked_out: Active connections in use
        - overflow: Current overflow connections (above pool_size)
        - invalid: Number of invalidated connections (if available)

    TASK-DB-P9-001: Added for production health monitoring.
    """
    pool = engine.pool

    # QueuePool has these methods
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": getattr(pool, 'invalidatedcount', lambda: 0)(),
    }


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Provides a database session for the duration of a request.
    Automatically closes the session after the request completes.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Provides a database session within a context manager scope.
    Automatically closes the session on context exit.

    Usage:
        with db_context() as session:
            result = session.execute(text("SELECT 1"))

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_engine(database_url: str):
    """
    Create a test engine with appropriate configuration.

    Useful for creating isolated test databases.

    Args:
        database_url: PostgreSQL database URL for the test database

    Returns:
        Engine: SQLAlchemy engine configured for testing
    """
    if "postgresql" not in database_url.lower() and "postgres" not in database_url.lower():
        raise ValueError(f"Only PostgreSQL is supported. Got: {database_url}")

    return create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )


# =============================================================================
# Async Database Support
# =============================================================================

def _create_async_engine():
    """
    Create an async SQLAlchemy engine for PostgreSQL.

    Uses the async_database_url from settings which converts:
    - postgresql:// to postgresql+asyncpg://

    TASK-DB-P9-001: Updated to use POOL_CONFIG for consistency.
    """
    async_url = settings.async_database_url

    if not settings.is_postgresql:
        raise ValueError(f"Only PostgreSQL is supported. Got: {settings.database_url}")

    return create_async_engine(
        async_url,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=POOL_CONFIG["pool_size"],
        max_overflow=POOL_CONFIG["max_overflow"],
        pool_timeout=POOL_CONFIG["pool_timeout"],
        pool_recycle=POOL_CONFIG["pool_recycle"],
        pool_pre_ping=POOL_CONFIG["pool_pre_ping"],
        echo=settings.debug,
    )


# Lazy async engine initialization
# Avoids import-time errors in scripts that only need sync database access
_async_engine = None
_AsyncSessionLocal = None


def _get_async_engine():
    """Get or create the async engine lazily."""
    global _async_engine
    if _async_engine is None:
        _async_engine = _create_async_engine()
    return _async_engine


def _get_async_session_maker():
    """Get or create the async session maker lazily."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=_get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_async_session() as db:
            result = await db.execute(select(Model))

    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    AsyncSessionLocal = _get_async_session_maker()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
