"""
Database connection management for PCF Calculator
Provides SQLAlchemy engine, session management, and FastAPI dependency injection

This module handles:
- SQLite database connection with proper configuration
- Foreign keys enforcement (PRAGMA foreign_keys = ON)
- Connection pooling
- Session lifecycle management
- FastAPI dependency injection for database sessions
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings


# Create SQLAlchemy engine with SQLite configuration
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for FastAPI/SQLite
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,  # Maximum number of permanent connections
    max_overflow=10,  # Maximum number of overflow connections
    echo=settings.debug,  # Log SQL queries in debug mode
)


# Event listener to enable foreign keys for each SQLite connection
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Enable foreign key constraints for SQLite connections.

    This is critical for SQLite as foreign keys are disabled by default.
    PRAGMA must be executed for each new connection.

    Args:
        dbapi_conn: Raw DB-API connection object
        connection_record: Connection record (unused)
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
