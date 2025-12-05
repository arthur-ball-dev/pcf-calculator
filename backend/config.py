"""
Configuration module for PCF Calculator Backend
Handles environment variables and application settings

Supports both SQLite (development) and PostgreSQL (production) databases.

TASK-BE-P5-001: Added Celery and Redis configuration settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    Attributes:
        app_name: Application name
        app_version: Application version
        debug: Debug mode flag
        database_url: Database connection string (SQLite or PostgreSQL)
        database_url_pooled: PostgreSQL pooled connection (for PgBouncer)
        db_pool_size: Database connection pool size
        db_max_overflow: Maximum overflow connections
        cors_origins: Allowed CORS origins for frontend
        api_v1_prefix: API version 1 prefix
        CELERY_BROKER_URL: Celery broker URL (Redis)
        CELERY_RESULT_BACKEND: Celery result backend URL (Redis)
        REDIS_HOST: Redis host
        REDIS_PORT: Redis port
        REDIS_DB: Redis database number
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="PCF Calculator API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Database settings - supports both SQLite and PostgreSQL
    database_url: str = Field(
        default="sqlite:///./pcf_calculator.db",
        description="Database connection URL (SQLite or PostgreSQL)"
    )

    # PostgreSQL-specific settings (optional, only used when PostgreSQL is configured)
    database_url_pooled: Optional[str] = Field(
        default=None,
        description="PostgreSQL pooled connection URL (for PgBouncer)"
    )

    # Connection pool settings (primarily for PostgreSQL)
    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size"
    )
    db_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections beyond pool size"
    )

    # Supabase settings (optional)
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL"
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase API key"
    )

    # CORS settings - allow multiple frontend ports (3000=old, 5173=Vite default, 5174-5175=alternates)
    # Railway deployment: Set CORS_ORIGINS env var with Railway URL
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
        ],
        description="Allowed CORS origins (comma-separated for Railway deployment)"
    )

    # Railway deployment URL (optional - auto-appends to CORS if set)
    railway_public_url: Optional[str] = Field(
        default=None,
        description="Railway public domain (e.g., https://pcf-calculator-production.up.railway.app)"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    # Celery settings
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL (Redis)"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL (Redis)"
    )

    # Redis settings
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host"
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis port"
    )
    REDIS_DB: int = Field(
        default=0,
        description="Redis database number"
    )

    @property
    def is_postgresql(self) -> bool:
        """Check if the database is PostgreSQL."""
        return "postgresql" in self.database_url.lower()

    @property
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return "sqlite" in self.database_url.lower()

    @property
    def async_database_url(self) -> str:
        """
        Get the async database URL for SQLAlchemy async operations.

        For PostgreSQL, converts postgresql:// to postgresql+asyncpg://
        For SQLite, converts sqlite:// to sqlite+aiosqlite://
        """
        url = self.database_url

        if self.is_postgresql:
            # Convert to asyncpg driver
            if "postgresql://" in url and "+asyncpg" not in url:
                return url.replace("postgresql://", "postgresql+asyncpg://")
            elif "postgres://" in url and "+asyncpg" not in url:
                # Handle postgres:// shorthand
                return url.replace("postgres://", "postgresql+asyncpg://")
        elif self.is_sqlite:
            # Convert to aiosqlite driver
            if "sqlite:///" in url and "+aiosqlite" not in url:
                return url.replace("sqlite:///", "sqlite+aiosqlite:///")

        return url

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to add Railway URL to CORS origins if set"""
        if self.railway_public_url and self.railway_public_url not in self.cors_origins:
            self.cors_origins.append(self.railway_public_url)


# Global settings instance
settings = Settings()
