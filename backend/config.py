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

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to add Railway URL to CORS origins if set"""
        if self.railway_public_url and self.railway_public_url not in self.cors_origins:
            self.cors_origins.append(self.railway_public_url)


# Global settings instance
settings = Settings()
