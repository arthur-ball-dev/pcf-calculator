"""
Configuration re-export for backward compatibility.

This module re-exports the settings from backend.config
for consistency with the backend.core namespace.
"""

from backend.config import settings, Settings

__all__ = ["settings", "Settings"]
