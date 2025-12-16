"""
SQLAlchemy Base and utility functions for models.

This module provides the declarative base and common utilities
used by all models. It exists as a separate module to avoid
circular import issues between models.
"""

from sqlalchemy.orm import declarative_base
import uuid

# Create declarative base
Base = declarative_base()


def generate_uuid() -> str:
    """Generate lowercase hex UUID for primary keys"""
    return uuid.uuid4().hex


__all__ = ['Base', 'generate_uuid']
