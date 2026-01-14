"""
Configuration module for PCF Calculator Backend
Handles environment variables and application settings

Supports both SQLite (development) and PostgreSQL (production) databases.

TASK-BE-P5-001: Added Celery and Redis configuration settings.
TASK-BE-P7-003: Fixed database path resolution to use absolute path from project root.
TASK-BE-P7-018: Added JWT authentication configuration settings.
TASK-BE-P7-020: Added rate limiting configuration settings.
TASK-CALC-P7-022: Added emission factor cache TTL configuration.
TASK-DB-P9-001: Added connection pool timeout and recycle settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


def get_project_root() -> Path:
    """
    Get the project root directory.

    The project root is identified as the directory containing both
    'backend' and 'frontend' directories, or the parent of the 'backend' directory
    if this file is inside backend/.

    This ensures consistent database path resolution regardless of the
    current working directory when starting the server.

    TASK-BE-P7-003: Added to fix database path resolution bug where
    'cd backend && uvicorn main:app' would use a different database
    than 'uvicorn backend.main:app' from project root.
    """
    # This file is at: <project_root>/backend/config.py
    # So project root is the parent of the directory containing this file
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent
    project_root = backend_dir.parent

    return project_root


def get_default_database_url() -> str:
    """
    Get the default SQLite database URL with absolute path.

    Uses the project root to ensure the database path is always the same
    regardless of the current working directory.

    TASK-BE-P7-003: Changed from relative path './pcf_calculator.db' to
    absolute path to fix bug where different working directories would
    resolve to different database files.
    """
    project_root = get_project_root()
    db_path = project_root / "pcf_calculator.db"
    return f"sqlite:///{db_path}"


def load_secret_from_file(key_name: str, file_path: str = "/etc/environment.txt") -> Optional[str]:
    """
    Load a secret from a file containing KEY=VALUE pairs.

    This function provides a secure alternative to environment variables
    for storing secrets, by reading from a protected file.

    Args:
        key_name: The name of the key to look for (e.g., 'PCF_CALC_JWT_SECRET_KEY')
        file_path: Path to the file containing secrets (default: /etc/environment.txt)

    Returns:
        The secret value if found, None otherwise

    Security Note:
        The file should be readable only by the application user (chmod 600).
    """
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key_name}='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    except (FileNotFoundError, PermissionError):
        pass
    return None


def get_jwt_secret_key() -> str:
    """
    Get the JWT secret key from file or environment variable.

    Checks in order:
    1. /etc/environment.txt file (PCF_CALC_JWT_SECRET_KEY=...)
    2. Environment variable PCF_CALC_JWT_SECRET_KEY

    Raises:
        ValueError: If the secret key is not configured in either location

    Security Note:
        This function intentionally has no default fallback to prevent
        accidental deployment with a known/weak secret key.
    """
    # Try file-based secret first
    secret = load_secret_from_file('PCF_CALC_JWT_SECRET_KEY')
    if secret:
        return secret

    # Fall back to environment variable
    secret = os.getenv('PCF_CALC_JWT_SECRET_KEY')
    if secret:
        return secret

    # No default - fail fast in production
    raise ValueError(
        "PCF_CALC_JWT_SECRET_KEY not configured. "
        "Set it in /etc/environment.txt or as an environment variable. "
        "The key must be at least 32 characters for security."
    )


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
        db_pool_timeout: Connection pool timeout in seconds
        db_pool_recycle: Connection recycle time in seconds
        cors_origins: Allowed CORS origins for frontend
        api_v1_prefix: API version 1 prefix
        CELERY_BROKER_URL: Celery broker URL (Redis)
        CELERY_RESULT_BACKEND: Celery result backend URL (Redis)
        REDIS_HOST: Redis host
        REDIS_PORT: Redis port
        REDIS_DB: Redis database number
        PCF_CALC_JWT_SECRET_KEY: Secret key for JWT token signing (from file/env)
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time
        emission_factor_cache_ttl: Emission factor cache TTL in seconds
        RATE_LIMIT_GENERAL: General rate limit (requests/minute)
        RATE_LIMIT_CALCULATION: Calculation rate limit (requests/minute)
        RATE_LIMIT_AUTH_ATTEMPTS: Auth rate limit (attempts/5 minutes)
        RATE_LIMIT_STORAGE: Storage backend for rate limiting
        RATE_LIMIT_ADMIN_MULTIPLIER: Multiplier for admin rate limits
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
    # TASK-BE-P7-003: Default now uses absolute path via get_default_database_url()
    database_url: str = Field(
        default_factory=get_default_database_url,
        description="Database connection URL (SQLite or PostgreSQL)"
    )

    # PostgreSQL-specific settings (optional, only used when PostgreSQL is configured)
    database_url_pooled: Optional[str] = Field(
        default=None,
        description="PostgreSQL pooled connection URL (for PgBouncer)"
    )

    # Connection pool settings (primarily for PostgreSQL)
    # TASK-DB-P9-001: Added pool_timeout and pool_recycle for production readiness
    db_pool_size: int = Field(
        default=10,
        description="Database connection pool size (steady-state connections)"
    )
    db_max_overflow: int = Field(
        default=20,
        description="Maximum overflow connections beyond pool size (burst handling)"
    )
    db_pool_timeout: int = Field(
        default=30,
        description="Seconds to wait for available connection from pool"
    )
    db_pool_recycle: int = Field(
        default=1800,
        description="Seconds before recycling connections (30 min default)"
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

    # JWT Authentication settings (TASK-BE-P7-018)
    # P0 Security Fix: Removed hardcoded default - key MUST be configured externally
    # Reads from: 1) /etc/environment.txt, 2) PCF_CALC_JWT_SECRET_KEY env var
    PCF_CALC_JWT_SECRET_KEY: str = Field(
        default_factory=get_jwt_secret_key,
        description="Secret key for JWT token signing (loaded from file or env var)"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="JWT access token expiration time in minutes"
    )

    # Emission factor cache settings (TASK-CALC-P7-022)
    emission_factor_cache_ttl: int = Field(
        default=300,
        description="Emission factor cache TTL in seconds (default: 5 minutes)"
    )

    # Rate Limiting settings (TASK-BE-P7-020)
    RATE_LIMIT_GENERAL: int = Field(
        default=100,
        description="General rate limit: requests per minute"
    )
    RATE_LIMIT_CALCULATION: int = Field(
        default=10,
        description="Calculation rate limit: requests per minute (expensive operations)"
    )
    RATE_LIMIT_AUTH_ATTEMPTS: int = Field(
        default=5,
        description="Auth rate limit: login attempts per 5 minutes"
    )
    RATE_LIMIT_STORAGE: str = Field(
        default="memory",
        description="Rate limit storage backend: 'memory' or 'redis'"
    )
    RATE_LIMIT_ADMIN_MULTIPLIER: int = Field(
        default=10,
        description="Rate limit multiplier for admin users"
    )
    RATE_LIMIT_REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis URL for distributed rate limiting (optional)"
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

    @property
    def rate_limit_redis_url(self) -> Optional[str]:
        """Get Redis URL for rate limiting if configured."""
        if self.RATE_LIMIT_REDIS_URL:
            return self.RATE_LIMIT_REDIS_URL
        if self.RATE_LIMIT_STORAGE == "redis":
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return None

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to add Railway URL to CORS origins if set"""
        if self.railway_public_url and self.railway_public_url not in self.cors_origins:
            self.cors_origins.append(self.railway_public_url)


# Global settings instance
settings = Settings()
