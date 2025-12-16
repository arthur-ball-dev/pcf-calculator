"""
Database connection management for PCF Calculator
Provides SQLAlchemy engine, session management, and FastAPI dependency injection

This module handles:
- SQLite database connection (development) with proper configuration
- PostgreSQL database connection (production) with connection pooling
- Foreign keys enforcement (PRAGMA for SQLite)
- Connection pooling (QueuePool for PostgreSQL, StaticPool option for SQLite)
- Session lifecycle management (sync and async)
- FastAPI dependency injection for database sessions
"""

from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool, NullPool

from backend.config import settings


def _create_engine():
    """
    Create the appropriate SQLAlchemy engine based on database configuration.

    Returns an engine configured for either SQLite or PostgreSQL.

    SQLite Configuration:
    - check_same_thread: False (required for FastAPI)
    - Foreign keys enabled via event listener

    PostgreSQL Configuration:
    - Connection pooling with configurable pool size
    - pool_pre_ping for connection health checks
    """
    if settings.is_sqlite:
        # SQLite configuration
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},  # Required for FastAPI/SQLite
            pool_pre_ping=True,  # Verify connections before using
            poolclass=StaticPool if "memory" in settings.database_url else QueuePool,
            pool_size=settings.db_pool_size if "memory" not in settings.database_url else 0,
            max_overflow=settings.db_max_overflow if "memory" not in settings.database_url else 0,
            echo=settings.debug,  # Log SQL queries in debug mode
        )

        # Enable foreign keys for SQLite connections
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """
            Enable foreign key constraints for SQLite connections.

            This is critical for SQLite as foreign keys are disabled by default.
            PRAGMA must be executed for each new connection.
            """
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    elif settings.is_postgresql:
        # PostgreSQL configuration
        engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.debug,  # Log SQL queries in debug mode
        )
        return engine

    else:
        # Fallback for unknown database types
        raise ValueError(
            f"Unsupported database URL: {settings.database_url}. "
            "Use sqlite:// or postgresql:// prefix."
        )


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


def create_test_engine(database_url: str = "sqlite:///:memory:"):
    """
    Create a test engine with appropriate configuration.

    Useful for creating isolated test databases.

    Args:
        database_url: Database URL for the test database

    Returns:
        Engine: SQLAlchemy engine configured for testing
    """
    if "sqlite" in database_url.lower():
        test_engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return test_engine

    elif "postgresql" in database_url.lower():
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )

    else:
        raise ValueError(f"Unsupported test database URL: {database_url}")


# =============================================================================
# Async Database Support
# =============================================================================

def _create_async_engine():
    """
    Create an async SQLAlchemy engine based on database configuration.

    Uses the async_database_url from settings which converts:
    - sqlite:/// to sqlite+aiosqlite:///
    - postgresql:// to postgresql+asyncpg://
    """
    async_url = settings.async_database_url

    if settings.is_sqlite:
        return create_async_engine(
            async_url,
            echo=settings.debug,
        )
    elif settings.is_postgresql:
        return create_async_engine(
            async_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            echo=settings.debug,
        )
    else:
        raise ValueError(f"Unsupported database URL: {settings.database_url}")


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
