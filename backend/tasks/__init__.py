"""
Celery tasks package for PCF Calculator.

TASK-BE-P5-001: Celery + Redis Setup

This package contains Celery tasks for background processing:
- data_sync: Data synchronization tasks for EPA, DEFRA, Exiobase

Usage:
    from backend.tasks.data_sync import sync_data_source, check_sync_status

    # Trigger async sync
    result = sync_data_source.delay("EPA_GHG_HUB")

    # Check sync status
    status = check_sync_status.delay("sync-log-id")
"""

from backend.tasks.data_sync import sync_data_source, check_sync_status

__all__ = [
    "sync_data_source",
    "check_sync_status",
]
