"""
Alembic environment configuration for PCF Calculator.

PostgreSQL database is required.
TASK-DB-P9-SQLITE-REMOVAL: Removed SQLite support - PostgreSQL only.
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import pool

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
# Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
# (Railway and some providers use postgres:// shorthand)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Normalize postgres:// URLs to postgresql:// for SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


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

    if not url or not is_postgresql_url(url):
        raise ValueError(
            "DATABASE_URL must be a PostgreSQL connection string. "
            f"Got: {url}"
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    PostgreSQL only.
    """
    url = config.get_main_option("sqlalchemy.url")

    if not url or not is_postgresql_url(url):
        raise ValueError(
            "DATABASE_URL must be a PostgreSQL connection string. "
            f"Got: {url}"
        )

    # PostgreSQL configuration
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,  # Don't pool during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
