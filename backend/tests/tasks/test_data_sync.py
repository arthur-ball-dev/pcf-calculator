"""
Unit tests for Celery data sync tasks.

TASK-BE-P5-001: Celery + Redis Setup - Phase A Tests

Tests for backend/tasks/data_sync.py:
- Task registration
- sync_data_source task execution with CELERY_ALWAYS_EAGER=True
- Error handling and retry logic
- Task state updates
- check_sync_status returns correct status
- Invalid source_name raises ValueError
- Inactive source raises ValueError

These tests use eager mode (CELERY_ALWAYS_EAGER=True) for synchronous execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def celery_config():
    """Celery configuration for testing with eager mode."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,
        "task_eager_propagates": True,
        "task_store_errors_even_if_ignored": True,
    }


@pytest.fixture
def mock_data_source():
    """Create a mock DataSource object."""
    source = MagicMock()
    source.id = "test-source-id-12345678"
    source.name = "EPA_GHG_HUB"
    source.is_active = True
    source.source_type = "api"
    source.base_url = "https://www.epa.gov/"
    return source


@pytest.fixture
def mock_inactive_data_source():
    """Create a mock inactive DataSource object."""
    source = MagicMock()
    source.id = "inactive-source-id-123"
    source.name = "INACTIVE_SOURCE"
    source.is_active = False
    source.source_type = "api"
    return source


@pytest.fixture
def mock_sync_result():
    """Create a mock SyncResult object."""
    result = MagicMock()
    result.sync_log_id = "sync-log-id-12345678"
    result.status = "completed"
    result.records_processed = 100
    result.records_created = 80
    result.records_updated = 15
    result.records_skipped = 3
    result.records_failed = 2
    result.errors = []
    result.dict = MagicMock(return_value={
        "sync_log_id": "sync-log-id-12345678",
        "status": "completed",
        "records_processed": 100,
        "records_created": 80,
        "records_updated": 15,
        "records_skipped": 3,
        "records_failed": 2,
    })
    return result


@pytest.fixture
def mock_data_sync_log():
    """Create a mock DataSyncLog object."""
    log = MagicMock()
    log.id = "sync-log-id-12345678"
    log.status = "completed"
    log.records_processed = 100
    log.records_created = 80
    log.records_updated = 15
    log.records_skipped = 3
    log.records_failed = 2
    log.error_message = None
    return log


# ============================================================================
# Task Registration Tests
# ============================================================================

class TestTaskRegistration:
    """Tests for Celery task registration."""

    def test_sync_data_source_task_exists(self):
        """Test that sync_data_source task is importable."""
        # This test will fail until the task is implemented
        from backend.tasks.data_sync import sync_data_source

        assert sync_data_source is not None
        assert hasattr(sync_data_source, "delay")
        assert hasattr(sync_data_source, "apply")
        assert hasattr(sync_data_source, "apply_async")

    def test_check_sync_status_task_exists(self):
        """Test that check_sync_status task is importable."""
        from backend.tasks.data_sync import check_sync_status

        assert check_sync_status is not None
        assert hasattr(check_sync_status, "delay")
        assert hasattr(check_sync_status, "apply")

    def test_sync_data_source_is_celery_task(self):
        """Test that sync_data_source is a registered Celery task."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        # Task should be registered in the Celery app
        task_name = "backend.tasks.data_sync.sync_data_source"
        assert task_name in celery_app.tasks

    def test_check_sync_status_is_celery_task(self):
        """Test that check_sync_status is a registered Celery task."""
        from backend.tasks.data_sync import check_sync_status
        from backend.core.celery_app import celery_app

        task_name = "backend.tasks.data_sync.check_sync_status"
        assert task_name in celery_app.tasks


# ============================================================================
# sync_data_source Task Tests (Eager Mode)
# ============================================================================

class TestSyncDataSourceTask:
    """Tests for sync_data_source task execution."""

    def test_sync_epa_source_success(
        self,
        celery_config,
        mock_data_source,
        mock_sync_result
    ):
        """Test successful EPA data source sync in eager mode."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        # Configure eager mode
        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            # Setup mock async session
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Setup mock query result for data source lookup
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            # Setup mock ingestion class
            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.return_value = mock_sync_result
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            # Execute task synchronously (eager mode)
            result = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Verify task completed successfully
            assert result.successful()
            assert result.result["status"] == "completed"
            assert result.result["records_processed"] == 100
            assert result.result["records_created"] == 80

    def test_sync_defra_source_success(
        self,
        celery_config,
        mock_sync_result
    ):
        """Test successful DEFRA data source sync in eager mode."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Create DEFRA data source
            defra_source = MagicMock()
            defra_source.id = "defra-source-id-123"
            defra_source.name = "DEFRA_CONVERSION"
            defra_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = defra_source
            mock_session.execute.return_value = mock_result

            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.return_value = mock_sync_result
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            result = sync_data_source.apply(args=["DEFRA_CONVERSION"])

            assert result.successful()
            assert result.result["status"] == "completed"

    def test_sync_with_force_refresh(
        self,
        celery_config,
        mock_data_source,
        mock_sync_result
    ):
        """Test sync with force_refresh=True parameter."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.return_value = mock_sync_result
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            result = sync_data_source.apply(
                args=["EPA_GHG_HUB"],
                kwargs={"force_refresh": True}
            )

            assert result.successful()

    def test_sync_with_dry_run(
        self,
        celery_config,
        mock_data_source,
        mock_sync_result
    ):
        """Test sync with dry_run=True parameter."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.return_value = mock_sync_result
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            result = sync_data_source.apply(
                args=["EPA_GHG_HUB"],
                kwargs={"dry_run": True}
            )

            assert result.successful()


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestSyncDataSourceErrorHandling:
    """Tests for error handling in sync_data_source task."""

    def test_invalid_source_name_raises_value_error(self, celery_config):
        """Test that invalid source_name raises ValueError."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Return None for data source lookup (not found)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            # Task should raise ValueError
            with pytest.raises(ValueError, match="Data source not found"):
                sync_data_source.apply(args=["NONEXISTENT_SOURCE"])

    def test_inactive_source_raises_value_error(
        self,
        celery_config,
        mock_inactive_data_source
    ):
        """Test that inactive source raises ValueError."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_inactive_data_source
            mock_session.execute.return_value = mock_result

            with pytest.raises(ValueError, match="Data source is inactive"):
                sync_data_source.apply(args=["INACTIVE_SOURCE"])

    def test_missing_ingestion_class_raises_value_error(
        self,
        celery_config,
        mock_data_source
    ):
        """Test that missing ingestion class raises ValueError."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Create source with unknown name
            unknown_source = MagicMock()
            unknown_source.id = "unknown-id"
            unknown_source.name = "UNKNOWN_SOURCE"
            unknown_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = unknown_source
            mock_session.execute.return_value = mock_result

            # No ingestion class for this source
            mock_ingestion_classes.get.return_value = None

            with pytest.raises(ValueError, match="No ingestion class for"):
                sync_data_source.apply(args=["UNKNOWN_SOURCE"])


# ============================================================================
# Retry Logic Tests
# ============================================================================

class TestSyncDataSourceRetry:
    """Tests for task retry logic."""

    def test_retry_on_connection_error(self, celery_config, mock_data_source):
        """Test task retries on ConnectionError."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            # Ingestion fails with ConnectionError
            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.side_effect = ConnectionError(
                "API unavailable"
            )
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            # In eager mode, exceptions are propagated after max retries
            with pytest.raises(ConnectionError):
                sync_data_source.apply(args=["EPA_GHG_HUB"])

    def test_retry_on_timeout_error(self, celery_config, mock_data_source):
        """Test task retries on TimeoutError."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.side_effect = TimeoutError(
                "Request timed out"
            )
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            with pytest.raises(TimeoutError):
                sync_data_source.apply(args=["EPA_GHG_HUB"])

    def test_task_has_retry_configuration(self):
        """Test that task has proper retry configuration."""
        from backend.tasks.data_sync import sync_data_source

        # Verify retry attributes are configured
        assert hasattr(sync_data_source, "max_retries") or \
               hasattr(sync_data_source, "retry_kwargs")

        # Task should have bind=True for self.retry()
        assert sync_data_source.bind is True


# ============================================================================
# Task State Tests
# ============================================================================

class TestTaskStateUpdates:
    """Tests for task state updates."""

    def test_task_updates_state_during_sync(
        self,
        celery_config,
        mock_data_source,
        mock_sync_result
    ):
        """Test that task updates state during sync operation."""
        from backend.tasks.data_sync import sync_data_source
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        state_updates = []

        def capture_state_update(state, meta):
            state_updates.append({"state": state, "meta": meta})

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion_instance = AsyncMock()
            mock_ingestion_instance.execute_sync.return_value = mock_sync_result
            mock_ingestion_class = MagicMock(return_value=mock_ingestion_instance)
            mock_ingestion_classes.get.return_value = mock_ingestion_class

            # Execute task and check state
            result = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Final state should be SUCCESS
            assert result.state == "SUCCESS"

    def test_task_tracks_started_state(self):
        """Test that task tracking is enabled for started state."""
        from backend.core.celery_app import celery_app

        # Verify task_track_started is enabled
        assert celery_app.conf.task_track_started is True


# ============================================================================
# check_sync_status Task Tests
# ============================================================================

class TestCheckSyncStatusTask:
    """Tests for check_sync_status task."""

    def test_check_status_completed(
        self,
        celery_config,
        mock_data_sync_log
    ):
        """Test check_sync_status returns correct status for completed sync."""
        from backend.tasks.data_sync import check_sync_status
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_data_sync_log
            mock_session.execute.return_value = mock_result

            result = check_sync_status.apply(args=["sync-log-id-12345678"])

            assert result.successful()
            assert result.result["status"] == "completed"
            assert result.result["records_processed"] == 100
            assert result.result["records_created"] == 80

    def test_check_status_not_found(self, celery_config):
        """Test check_sync_status returns not_found for invalid ID."""
        from backend.tasks.data_sync import check_sync_status
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            result = check_sync_status.apply(args=["nonexistent-id"])

            assert result.successful()
            assert result.result["status"] == "not_found"

    def test_check_status_in_progress(self, celery_config):
        """Test check_sync_status returns in_progress status."""
        from backend.tasks.data_sync import check_sync_status
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Create in-progress sync log
            in_progress_log = MagicMock()
            in_progress_log.id = "in-progress-log-id"
            in_progress_log.status = "in_progress"
            in_progress_log.records_processed = 50
            in_progress_log.records_created = 40
            in_progress_log.records_updated = 8
            in_progress_log.records_failed = 2
            in_progress_log.error_message = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = in_progress_log
            mock_session.execute.return_value = mock_result

            result = check_sync_status.apply(args=["in-progress-log-id"])

            assert result.successful()
            assert result.result["status"] == "in_progress"

    def test_check_status_failed_with_error(self, celery_config):
        """Test check_sync_status returns error message for failed sync."""
        from backend.tasks.data_sync import check_sync_status
        from backend.core.celery_app import celery_app

        celery_app.conf.update(celery_config)

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            # Create failed sync log
            failed_log = MagicMock()
            failed_log.id = "failed-log-id"
            failed_log.status = "failed"
            failed_log.records_processed = 30
            failed_log.records_created = 20
            failed_log.records_updated = 5
            failed_log.records_failed = 5
            failed_log.error_message = "API connection timeout"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = failed_log
            mock_session.execute.return_value = mock_result

            result = check_sync_status.apply(args=["failed-log-id"])

            assert result.successful()
            assert result.result["status"] == "failed"
            assert result.result["error_message"] == "API connection timeout"


# ============================================================================
# Task Binding Tests
# ============================================================================

class TestTaskBinding:
    """Tests for task binding configuration."""

    def test_sync_data_source_is_bound(self):
        """Test that sync_data_source task is bound (has self parameter)."""
        from backend.tasks.data_sync import sync_data_source

        assert sync_data_source.bind is True

    def test_check_sync_status_is_bound(self):
        """Test that check_sync_status task is bound."""
        from backend.tasks.data_sync import check_sync_status

        assert check_sync_status.bind is True


# ============================================================================
# Task Routing Tests
# ============================================================================

class TestTaskRouting:
    """Tests for task routing configuration."""

    def test_data_sync_tasks_routed_to_data_sync_queue(self):
        """Test that data sync tasks are routed to data_sync queue."""
        from backend.core.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert routes is not None

        # Data sync tasks should be routed to data_sync queue
        data_sync_route = routes.get("backend.tasks.data_sync.*")
        assert data_sync_route is not None
        assert data_sync_route.get("queue") == "data_sync"
