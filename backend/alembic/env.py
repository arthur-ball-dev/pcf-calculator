"""
Alembic environment configuration for PCF Calculator.

Supports both SQLite (development) and PostgreSQL (production) databases.
Handles dialect-specific features like foreign keys (SQLite) and connection pooling.
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, text, event, create_engine
from sqlalchemy import pool
from sqlalchemy.engine import Engine

from alembic import context

# Add parent directory to path to import models
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

# Import models for autogenerate support
from backend.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from environment variable if set
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def is_sqlite_url(url: str) -> bool:
    """Check if the database URL is for SQLite."""
    return url.lower().startswith("sqlite")


def is_postgresql_url(url: str) -> bool:
    """Check if the database URL is for PostgreSQL."""
    return "postgresql" in url.lower() or "postgres" in url.lower()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")

    # Determine if we should use batch mode (required for SQLite)
    render_as_batch = is_sqlite_url(url) if url else True

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Supports both SQLite and PostgreSQL with appropriate configuration.
    """
    url = config.get_main_option("sqlalchemy.url")

    # Create engine configuration
    engine_config = config.get_section(config.config_ini_section, {})

    if url and is_sqlite_url(url):
        # SQLite-specific configuration
        connectable = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=pool.NullPool,
        )

        # Enable foreign keys for SQLite
        @event.listens_for(connectable, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign keys for SQLite connections"""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    elif url and is_postgresql_url(url):
        # PostgreSQL-specific configuration
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,  # Don't pool during migrations
        )
    else:
        # Default configuration
        connectable = engine_from_config(
            engine_config,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    # Determine if we should use batch mode (required for SQLite)
    render_as_batch = is_sqlite_url(url) if url else True

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
