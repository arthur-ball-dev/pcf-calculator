"""
Celery application configuration for PCF Calculator.

TASK-BE-P5-001: Celery + Redis Setup

This module configures Celery with Redis as the message broker for
background task processing, including:
- Task serialization and timezone settings
- Task time limits and acknowledgment settings
- Beat schedule for automated data syncs (EPA, DEFRA, Exiobase)
- Task routing to dedicated queues
- Auto-discovery of task modules

Usage:
    # Start Celery worker
    celery -A backend.core.celery_app worker -l info -Q data_sync,calculations

    # Start Celery Beat scheduler
    celery -A backend.core.celery_app beat -l info

    # Monitor with Flower (optional)
    celery -A backend.core.celery_app flower --port=5555
"""

from celery import Celery
from celery.schedules import crontab

from backend.config import settings


# Create Celery application instance
celery_app = Celery(
    "pcf_calculator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.tasks", "backend.tasks.data_sync"],
)

# Update Celery configuration
celery_app.conf.update(
    # Serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone settings
    timezone="UTC",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit for graceful shutdown (9 minutes)

    # Retry and acknowledgment settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result expiration (1 hour)
    result_expires=3600,

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for fair distribution
    worker_concurrency=4,

    # Beat schedule for automated data syncs
    beat_schedule={
        "sync-epa-biweekly": {
            "task": "backend.tasks.data_sync.sync_data_source",
            "schedule": crontab(day_of_week="mon,thu", hour=2, minute=0),
            "args": ("EPA_GHG_HUB",),
            "options": {"queue": "data_sync"},
        },
        "sync-defra-biweekly": {
            "task": "backend.tasks.data_sync.sync_data_source",
            "schedule": crontab(day_of_week="tue,fri", hour=3, minute=0),
            "args": ("DEFRA_CONVERSION",),
            "options": {"queue": "data_sync"},
        },
        "sync-exiobase-monthly": {
            "task": "backend.tasks.data_sync.sync_data_source",
            "schedule": crontab(day_of_month="1", hour=4, minute=0),
            "args": ("EXIOBASE",),
            "options": {"queue": "data_sync"},
        },
    },

    # Task routing - route tasks to dedicated queues
    task_routes={
        "backend.tasks.data_sync.*": {"queue": "data_sync"},
        "backend.tasks.calculations.*": {"queue": "calculations"},
    },
)

# Auto-discover tasks from backend.tasks package
celery_app.autodiscover_tasks(["backend.tasks"])

# Force-import task modules to ensure they're registered immediately
# This is needed for tests that check celery_app.tasks before task execution
import backend.tasks.data_sync  # noqa: E402, F401
