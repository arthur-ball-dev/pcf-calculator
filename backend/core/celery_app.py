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

from celery import Celery, Task as CeleryTask
from celery.schedules import crontab

from backend.config import settings


class BoundTask(CeleryTask):
    """
    Custom Celery Task base class that exposes bind as a readable attribute.

    In Celery 5.x, the `bind` parameter to @app.task() decorator creates a
    bound task where the first argument is `self`. However, `Task.bind` is
    a method used internally by Celery, not a boolean attribute.

    This class overrides __getattribute__ to intercept `.bind` access after
    task registration, returning True if the task's run method takes `self`
    as its first parameter (indicating it was created with bind=True).

    The detection logic:
    - During task registration, Celery calls task.bind(app) - we let this through
    - After registration (_app is set), accessing task.bind returns True/False
      based on whether __wrapped__ is a MethodType (indicates bind=True was used)
    """

    def __getattribute__(self, name):
        """Override attribute access to make .bind return True for bound tasks.

        Detection logic:
        1. Check if _app is set (task fully registered)
        2. Check if __wrapped__ is a MethodType (indicates bind=True)
        3. During registration, return original bind method for Celery to call
        """
        if name == 'bind':
            from types import MethodType
            try:
                # Check if task is fully registered (has _app set)
                _app = super().__getattribute__('_app')
                if _app is not None:
                    # Task is registered, check if it's bound
                    wrapped = super().__getattribute__('__wrapped__')
                    if isinstance(wrapped, MethodType):
                        return True
            except AttributeError:
                pass
            # During registration or not bound, return original bind method
            return super().__getattribute__(name)
        return super().__getattribute__(name)


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
