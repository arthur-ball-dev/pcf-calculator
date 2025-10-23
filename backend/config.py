"""
Configuration module for PCF Calculator Backend
Handles environment variables and application settings
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    Attributes:
        app_name: Application name
        app_version: Application version
        debug: Debug mode flag
        database_url: SQLite database connection string
        cors_origins: Allowed CORS origins for frontend
        api_v1_prefix: API version 1 prefix
    """

    app_name: str = Field(default="PCF Calculator API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Database settings
    database_url: str = Field(
        default="sqlite:///./pcf_calculator.db",
        description="Database connection URL"
    )

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
