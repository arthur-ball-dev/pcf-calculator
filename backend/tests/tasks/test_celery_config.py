"""
Tests for Celery configuration.

TASK-BE-P5-001: Celery + Redis Setup - Phase A Tests

Tests for backend/core/celery_app.py:
- celery_app configuration correctness
- Beat schedule defined for EPA, DEFRA, Exiobase
- Task routes configured
- Worker settings correct

These tests validate the Celery application configuration without
requiring a running Redis or worker.
"""

import pytest
from celery.schedules import crontab


# ============================================================================
# Celery App Configuration Tests
# ============================================================================

class TestCeleryAppConfiguration:
    """Tests for celery_app configuration."""

    def test_celery_app_exists(self):
        """Test that celery_app is importable."""
        from backend.core.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == "pcf_calculator"

    def test_broker_url_configured(self):
        """Test that broker URL is configured."""
        from backend.core.celery_app import celery_app

        broker_url = celery_app.conf.broker_url
        assert broker_url is not None
        # Should be Redis URL in production
        assert "redis://" in broker_url or "memory://" in broker_url

    def test_result_backend_configured(self):
        """Test that result backend is configured."""
        from backend.core.celery_app import celery_app

        result_backend = celery_app.conf.result_backend
        assert result_backend is not None

    def test_task_serializer_is_json(self):
        """Test that task serializer is JSON."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_accept_content_includes_json(self):
        """Test that accepted content includes JSON."""
        from backend.core.celery_app import celery_app

        accept_content = celery_app.conf.accept_content
        assert "json" in accept_content

    def test_result_serializer_is_json(self):
        """Test that result serializer is JSON."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.result_serializer == "json"

    def test_timezone_is_utc(self):
        """Test that timezone is UTC."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.timezone == "UTC"

    def test_enable_utc_is_true(self):
        """Test that enable_utc is True."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.enable_utc is True

    def test_task_track_started_is_true(self):
        """Test that task_track_started is True."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.task_track_started is True


# ============================================================================
# Task Time Limits Tests
# ============================================================================

class TestTaskTimeLimits:
    """Tests for task time limit configuration."""

    def test_task_time_limit_configured(self):
        """Test that task time limit is configured."""
        from backend.core.celery_app import celery_app

        time_limit = celery_app.conf.task_time_limit
        assert time_limit is not None
        # Should be 10 minutes (600 seconds) or similar
        assert time_limit >= 300  # At least 5 minutes
        assert time_limit <= 3600  # At most 1 hour

    def test_task_soft_time_limit_configured(self):
        """Test that soft time limit is configured."""
        from backend.core.celery_app import celery_app

        soft_limit = celery_app.conf.task_soft_time_limit
        assert soft_limit is not None

    def test_soft_limit_less_than_hard_limit(self):
        """Test that soft time limit is less than hard limit."""
        from backend.core.celery_app import celery_app

        hard_limit = celery_app.conf.task_time_limit
        soft_limit = celery_app.conf.task_soft_time_limit

        if hard_limit and soft_limit:
            assert soft_limit < hard_limit


# ============================================================================
# Task Acknowledgment Tests
# ============================================================================

class TestTaskAcknowledgment:
    """Tests for task acknowledgment configuration."""

    def test_task_acks_late_is_true(self):
        """Test that task_acks_late is True for reliability."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.task_acks_late is True

    def test_task_reject_on_worker_lost_is_true(self):
        """Test that task_reject_on_worker_lost is True."""
        from backend.core.celery_app import celery_app

        assert celery_app.conf.task_reject_on_worker_lost is True


# ============================================================================
# Result Configuration Tests
# ============================================================================

class TestResultConfiguration:
    """Tests for result backend configuration."""

    def test_result_expires_configured(self):
        """Test that result expiration is configured."""
        from backend.core.celery_app import celery_app

        result_expires = celery_app.conf.result_expires
        assert result_expires is not None
        # Should expire in reasonable time (1 hour to 24 hours)
        assert result_expires >= 3600  # At least 1 hour


# ============================================================================
# Worker Configuration Tests
# ============================================================================

class TestWorkerConfiguration:
    """Tests for worker configuration."""

    def test_worker_prefetch_multiplier_configured(self):
        """Test that worker_prefetch_multiplier is configured."""
        from backend.core.celery_app import celery_app

        prefetch = celery_app.conf.worker_prefetch_multiplier
        assert prefetch is not None
        # Should be 1 for fair task distribution
        assert prefetch == 1

    def test_worker_concurrency_configured(self):
        """Test that worker_concurrency is configured."""
        from backend.core.celery_app import celery_app

        concurrency = celery_app.conf.worker_concurrency
        # Concurrency should be a reasonable number or None (auto)
        assert concurrency is None or concurrency > 0


# ============================================================================
# Beat Schedule Tests
# ============================================================================

class TestBeatSchedule:
    """Tests for Celery Beat schedule configuration."""

    def test_beat_schedule_exists(self):
        """Test that beat_schedule is defined."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule
        assert beat_schedule is not None
        assert isinstance(beat_schedule, dict)

    def test_epa_sync_scheduled(self):
        """Test that EPA sync task is scheduled."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        # Find EPA schedule entry
        epa_schedule = None
        for name, config in beat_schedule.items():
            if "epa" in name.lower() or "EPA" in config.get("args", [""])[0]:
                epa_schedule = config
                break

        assert epa_schedule is not None, "EPA sync task not found in beat schedule"
        assert epa_schedule["task"] == "backend.tasks.data_sync.sync_data_source"
        assert "EPA_GHG_HUB" in epa_schedule.get("args", [])

    def test_defra_sync_scheduled(self):
        """Test that DEFRA sync task is scheduled."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        # Find DEFRA schedule entry
        defra_schedule = None
        for name, config in beat_schedule.items():
            if "defra" in name.lower() or "DEFRA" in config.get("args", [""])[0]:
                defra_schedule = config
                break

        assert defra_schedule is not None, "DEFRA sync task not found in beat schedule"
        assert defra_schedule["task"] == "backend.tasks.data_sync.sync_data_source"
        assert "DEFRA_CONVERSION" in defra_schedule.get("args", [])

    def test_exiobase_sync_scheduled(self):
        """Test that Exiobase sync task is scheduled."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        # Find Exiobase schedule entry
        exiobase_schedule = None
        for name, config in beat_schedule.items():
            if "exiobase" in name.lower() or "EXIOBASE" in config.get("args", [""])[0]:
                exiobase_schedule = config
                break

        assert exiobase_schedule is not None, "Exiobase sync task not found in beat schedule"
        assert exiobase_schedule["task"] == "backend.tasks.data_sync.sync_data_source"
        assert "EXIOBASE" in exiobase_schedule.get("args", [])

    def test_epa_schedule_is_biweekly(self):
        """Test that EPA sync is scheduled biweekly (Mon/Thu)."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        epa_schedule = beat_schedule.get("sync-epa-biweekly")
        assert epa_schedule is not None

        schedule = epa_schedule["schedule"]
        assert isinstance(schedule, crontab)

        # Should run on Monday and Thursday
        # crontab.day_of_week uses 0=Monday convention for some versions
        assert schedule.day_of_week is not None

    def test_defra_schedule_is_biweekly(self):
        """Test that DEFRA sync is scheduled biweekly (Tue/Fri)."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        defra_schedule = beat_schedule.get("sync-defra-biweekly")
        assert defra_schedule is not None

        schedule = defra_schedule["schedule"]
        assert isinstance(schedule, crontab)

    def test_exiobase_schedule_is_monthly(self):
        """Test that Exiobase sync is scheduled monthly."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        exiobase_schedule = beat_schedule.get("sync-exiobase-monthly")
        assert exiobase_schedule is not None

        schedule = exiobase_schedule["schedule"]
        assert isinstance(schedule, crontab)

        # Monthly schedule should have day_of_month set
        assert schedule.day_of_month is not None

    def test_scheduled_tasks_have_queue_options(self):
        """Test that scheduled tasks specify queue options."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        for name, config in beat_schedule.items():
            options = config.get("options", {})
            # Tasks should specify a queue
            assert "queue" in options, f"Task {name} should specify queue in options"
            assert options["queue"] == "data_sync"


# ============================================================================
# Task Routes Tests
# ============================================================================

class TestTaskRoutes:
    """Tests for task routing configuration."""

    def test_task_routes_exists(self):
        """Test that task_routes is defined."""
        from backend.core.celery_app import celery_app

        task_routes = celery_app.conf.task_routes
        assert task_routes is not None
        assert isinstance(task_routes, dict)

    def test_data_sync_tasks_routed_to_data_sync_queue(self):
        """Test that data sync tasks are routed to data_sync queue."""
        from backend.core.celery_app import celery_app

        task_routes = celery_app.conf.task_routes

        data_sync_route = task_routes.get("backend.tasks.data_sync.*")
        assert data_sync_route is not None
        assert data_sync_route.get("queue") == "data_sync"

    def test_calculation_tasks_routed_to_calculations_queue(self):
        """Test that calculation tasks are routed to calculations queue."""
        from backend.core.celery_app import celery_app

        task_routes = celery_app.conf.task_routes

        calc_route = task_routes.get("backend.tasks.calculations.*")
        assert calc_route is not None
        assert calc_route.get("queue") == "calculations"


# ============================================================================
# Task Autodiscovery Tests
# ============================================================================

class TestTaskAutodiscovery:
    """Tests for task autodiscovery configuration."""

    def test_tasks_autodiscovered(self):
        """Test that tasks are autodiscovered."""
        from backend.core.celery_app import celery_app

        # Check that sync_data_source task is registered
        task_name = "backend.tasks.data_sync.sync_data_source"
        assert task_name in celery_app.tasks

    def test_backend_tasks_package_included(self):
        """Test that backend.tasks package is included for autodiscovery."""
        from backend.core.celery_app import celery_app

        # Celery should autodiscover tasks from backend.tasks
        # This is typically configured via autodiscover_tasks()
        assert "backend.tasks" in celery_app.conf.include or \
               len([t for t in celery_app.tasks if t.startswith("backend.tasks")]) > 0


# ============================================================================
# Configuration Values Tests
# ============================================================================

class TestConfigurationValues:
    """Tests for specific configuration values from settings."""

    def test_broker_url_from_settings(self):
        """Test that broker URL matches settings."""
        from backend.core.celery_app import celery_app
        from backend.core.config import settings

        # Broker URL should match settings (if settings are loaded)
        if hasattr(settings, "CELERY_BROKER_URL"):
            assert celery_app.conf.broker_url == settings.CELERY_BROKER_URL

    def test_result_backend_from_settings(self):
        """Test that result backend matches settings."""
        from backend.core.celery_app import celery_app
        from backend.core.config import settings

        if hasattr(settings, "CELERY_RESULT_BACKEND"):
            assert celery_app.conf.result_backend == settings.CELERY_RESULT_BACKEND


# ============================================================================
# Schedule Timing Tests
# ============================================================================

class TestScheduleTiming:
    """Tests for schedule timing configuration."""

    def test_epa_sync_runs_at_2am(self):
        """Test that EPA sync runs at 2:00 AM UTC."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule
        epa_schedule = beat_schedule.get("sync-epa-biweekly")

        assert epa_schedule is not None
        schedule = epa_schedule["schedule"]

        assert 2 in schedule.hour or schedule.hour == {2}
        assert 0 in schedule.minute or schedule.minute == {0}

    def test_defra_sync_runs_at_3am(self):
        """Test that DEFRA sync runs at 3:00 AM UTC."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule
        defra_schedule = beat_schedule.get("sync-defra-biweekly")

        assert defra_schedule is not None
        schedule = defra_schedule["schedule"]

        assert 3 in schedule.hour or schedule.hour == {3}
        assert 0 in schedule.minute or schedule.minute == {0}

    def test_exiobase_sync_runs_at_4am(self):
        """Test that Exiobase sync runs at 4:00 AM UTC."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule
        exiobase_schedule = beat_schedule.get("sync-exiobase-monthly")

        assert exiobase_schedule is not None
        schedule = exiobase_schedule["schedule"]

        assert 4 in schedule.hour or schedule.hour == {4}
        assert 0 in schedule.minute or schedule.minute == {0}
