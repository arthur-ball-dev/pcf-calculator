"""
Core module for PCF Calculator Backend.

Contains core application configuration and utilities:
- celery_app: Celery application instance
- config: Application settings (re-exported from backend.config)
"""

from backend.core.celery_app import celery_app

__all__ = [
    "celery_app",
]
