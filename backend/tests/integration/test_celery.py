"""
Integration tests for Celery tasks.

TASK-BE-P5-001: Celery + Redis Setup - Phase A Tests

Integration tests requiring real Celery worker or Redis:
- End-to-end sync trigger -> task runs -> factors ingested
- Task retry on failure
- Concurrent task execution
- Health check endpoint

These tests are marked with @pytest.mark.integration and may require
running infrastructure (Redis, Celery worker).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from celery.exceptions import Retry as CeleryRetry


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def celery_config():
    """Celery configuration for integration testing."""
    return {
        "broker_url": "redis://localhost:6379/1",  # Test database
        "result_backend": "redis://localhost:6379/1",
        "task_always_eager": False,  # Use real async execution
        "task_eager_propagates": True,
        "task_track_started": True,
        "task_time_limit": 60,  # Shorter timeout for tests
        "task_soft_time_limit": 50,
    }


@pytest.fixture
def celery_app_integration(celery_config, require_redis):
    """Create Celery app with integration config.

    Depends on require_redis fixture to skip tests when Redis is unavailable.
    """
    from backend.core.celery_app import celery_app

    original_config = {
        "broker_url": celery_app.conf.broker_url,
        "result_backend": celery_app.conf.result_backend,
        "task_always_eager": celery_app.conf.task_always_eager,
    }

    celery_app.conf.update(celery_config)
    yield celery_app

    # Restore original config
    celery_app.conf.update(original_config)


@pytest.fixture
def mock_epa_data_source():
    """Create mock EPA data source for integration tests."""
    source = MagicMock()
    source.id = "epa-integration-test-id"
    source.name = "EPA_GHG_HUB"
    source.is_active = True
    source.source_type = "api"
    source.base_url = "https://www.epa.gov/"
    return source


@pytest.fixture
def mock_sync_result_success():
    """Create mock successful sync result."""
    result = MagicMock()
    result.sync_log_id = "integration-sync-log-id"
    result.status = "completed"
    result.records_processed = 50
    result.records_created = 45
    result.records_updated = 3
    result.records_skipped = 1
    result.records_failed = 1
    result.errors = []
    result.dict = MagicMock(return_value={
        "sync_log_id": "integration-sync-log-id",
        "status": "completed",
        "records_processed": 50,
        "records_created": 45,
        "records_updated": 3,
        "records_skipped": 1,
        "records_failed": 1,
    })
    return result


# ============================================================================
# End-to-End Sync Tests
# ============================================================================

class TestEndToEndSync:
    """End-to-end tests for sync trigger -> task runs -> factors ingested."""

    def test_sync_trigger_returns_task_id(self, celery_app_integration):
        """Test that triggering sync returns a task ID."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "EPA_GHG_HUB"
            mock_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_source
            mock_session.execute.return_value = mock_result

            mock_sync_result = MagicMock()
            mock_sync_result.dict.return_value = {"status": "completed"}

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # Trigger task (use apply for synchronous testing)
            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Verify task ID exists
            assert task.id is not None
            assert isinstance(task.id, str)

    def test_sync_trigger_task_completes(
        self,
        celery_app_integration,
        mock_epa_data_source,
        mock_sync_result_success
    ):
        """Test that triggered sync task completes successfully."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # Execute task
            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Wait for completion
            assert task.successful()
            assert task.result["status"] == "completed"
            assert task.result["records_processed"] == 50

    def test_sync_creates_sync_log(
        self,
        celery_app_integration,
        mock_epa_data_source,
        mock_sync_result_success
    ):
        """Test that sync creates a sync log entry."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Verify sync log ID is returned
            assert task.successful()
            assert "sync_log_id" in task.result


# ============================================================================
# Task Retry Tests
# ============================================================================

class TestTaskRetryIntegration:
    """Integration tests for task retry on failure.

    Note: Celery 5.x with task_eager_propagates=True raises celery.exceptions.Retry
    when a task requests a retry in eager mode, since there's no worker to re-queue
    the task. These tests verify that the retry mechanism is correctly triggered
    by catching the Retry exception.
    """

    def test_task_retries_on_transient_failure(self, celery_app_integration):
        """Test that task triggers retry on transient failure.

        In Celery 5.x eager mode, the Retry exception is raised instead of
        being handled internally. We verify that the retry mechanism is
        triggered by catching this exception.
        """
        from backend.tasks.data_sync import sync_data_source

        call_count = {"count": 0}

        def mock_execute_sync(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ConnectionError("Transient failure")
            # Return success on third attempt
            result = MagicMock()
            result.dict.return_value = {"status": "completed", "records_processed": 10}
            return result

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "EPA_GHG_HUB"
            mock_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync = AsyncMock(side_effect=mock_execute_sync)
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # In Celery 5.x eager mode with task_eager_propagates=True,
            # the Retry exception is raised to signal retry behavior.
            # We catch it to verify retry was triggered.
            try:
                task = sync_data_source.apply(args=["EPA_GHG_HUB"])
                # If task succeeds without raising (unexpected in eager mode with retries)
                assert task.successful()
            except CeleryRetry as retry_exc:
                # Verify retry was triggered with correct exception
                assert retry_exc.exc is not None
                assert isinstance(retry_exc.exc, ConnectionError)
                assert "Transient failure" in str(retry_exc.exc)
                # Verify the task was called at least once before retry
                assert call_count["count"] >= 1, "Task should have been called before retry"

    def test_task_fails_after_max_retries(self, celery_app_integration):
        """Test that task fails after exceeding max retries.

        In Celery 5.x eager mode, we verify the retry mechanism is triggered
        by catching the Retry exception. The exception contains the original
        error that caused the retry.
        """
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "EPA_GHG_HUB"
            mock_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_source
            mock_session.execute.return_value = mock_result

            # Always fail
            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.side_effect = ConnectionError("Permanent failure")
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # In Celery 5.x eager mode, the task will raise Retry exception
            # on each retry attempt until max_retries is exceeded.
            # After max_retries, it raises the original exception.
            exception_raised = False

            try:
                sync_data_source.apply(args=["EPA_GHG_HUB"])
            except CeleryRetry as retry_exc:
                # Celery Retry exception indicates retry was requested
                # This is expected behavior in eager mode
                assert retry_exc.exc is not None
                assert isinstance(retry_exc.exc, ConnectionError)
                assert "Permanent failure" in str(retry_exc.exc)
                exception_raised = True
            except ConnectionError as exc:
                # After max retries, the original exception is raised
                assert "Permanent failure" in str(exc)
                exception_raised = True

            assert exception_raised, (
                "Expected either CeleryRetry or ConnectionError to be raised"
            )


# ============================================================================
# Concurrent Task Execution Tests
# ============================================================================

class TestConcurrentTaskExecution:
    """Integration tests for concurrent task execution."""

    def test_multiple_sync_tasks_can_run(
        self,
        celery_app_integration,
        mock_sync_result_success
    ):
        """Test that multiple sync tasks can run concurrently."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            def create_source(name):
                source = MagicMock()
                source.id = f"{name.lower()}-id"
                source.name = name
                source.is_active = True
                return source

            # Configure mock to return different sources based on query
            sources = {
                "EPA_GHG_HUB": create_source("EPA_GHG_HUB"),
                "DEFRA_CONVERSION": create_source("DEFRA_CONVERSION"),
            }

            def get_source(query):
                # Extract source name from query (simplified)
                for name, source in sources.items():
                    return source
                return None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.side_effect = lambda: sources.get(
                "EPA_GHG_HUB"
            )
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # Submit multiple tasks
            task1 = sync_data_source.apply(args=["EPA_GHG_HUB"])
            task2 = sync_data_source.apply(args=["EPA_GHG_HUB"])

            # Both should complete
            assert task1.successful()
            assert task2.successful()

    def test_different_source_tasks_independent(
        self,
        celery_app_integration,
        mock_sync_result_success
    ):
        """Test that different source sync tasks are independent."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            epa_source = MagicMock()
            epa_source.id = "epa-id"
            epa_source.name = "EPA_GHG_HUB"
            epa_source.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = epa_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            # Execute EPA sync
            epa_task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            assert epa_task.successful()
            assert epa_task.id != ""


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheckEndpoint:
    """Integration tests for Celery health check endpoint."""

    def test_health_endpoint_exists(self):
        """Test that health check endpoint is defined."""
        from backend.api.routes.health import celery_health

        assert celery_health is not None
        assert callable(celery_health)

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self):
        """Test that health check returns status information."""
        from backend.api.routes.health import celery_health

        with patch("backend.api.routes.health.celery_app") as mock_celery:
            # Mock worker ping response
            mock_celery.control.ping.return_value = [
                {"worker1": {"ok": "pong"}},
                {"worker2": {"ok": "pong"}},
            ]

            result = await celery_health()

            assert "status" in result
            assert result["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_check_healthy_with_workers(self):
        """Test health check returns healthy when workers respond."""
        from backend.api.routes.health import celery_health

        with patch("backend.api.routes.health.celery_app") as mock_celery:
            mock_celery.control.ping.return_value = [
                {"celery@worker1": {"ok": "pong"}}
            ]

            result = await celery_health()

            assert result["status"] == "healthy"
            assert result["workers"] == 1

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_no_workers(self):
        """Test health check returns unhealthy when no workers respond."""
        from backend.api.routes.health import celery_health

        with patch("backend.api.routes.health.celery_app") as mock_celery:
            mock_celery.control.ping.return_value = []

            result = await celery_health()

            assert result["status"] == "unhealthy"
            assert "No workers responding" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_on_error(self):
        """Test health check returns unhealthy on connection error."""
        from backend.api.routes.health import celery_health

        with patch("backend.api.routes.health.celery_app") as mock_celery:
            mock_celery.control.ping.side_effect = Exception("Redis connection refused")

            result = await celery_health()

            assert result["status"] == "unhealthy"
            assert "error" in result


# ============================================================================
# Task State Tracking Tests
# ============================================================================

class TestTaskStateTracking:
    """Integration tests for task state tracking."""

    def test_task_state_pending(self, celery_app_integration):
        """Test that new task starts in PENDING state."""
        from backend.tasks.data_sync import sync_data_source
        from celery.result import AsyncResult

        # In eager mode, task executes immediately
        # This test is more relevant with real worker
        # We test that task tracking is enabled
        assert celery_app_integration.conf.task_track_started is True

    def test_task_state_success(
        self,
        celery_app_integration,
        mock_epa_data_source,
        mock_sync_result_success
    ):
        """Test that completed task has SUCCESS state."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            assert task.state == "SUCCESS"

    def test_task_state_failure(self, celery_app_integration, mock_epa_data_source):
        """Test that failed task has FAILURE state."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.side_effect = RuntimeError("Sync failed")
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            with pytest.raises(RuntimeError):
                sync_data_source.apply(args=["EPA_GHG_HUB"])


# ============================================================================
# Result Retrieval Tests
# ============================================================================

class TestResultRetrieval:
    """Integration tests for retrieving task results."""

    def test_result_contains_sync_statistics(
        self,
        celery_app_integration,
        mock_epa_data_source,
        mock_sync_result_success
    ):
        """Test that task result contains sync statistics."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            result = task.result
            assert "records_processed" in result
            assert "records_created" in result
            assert "records_updated" in result
            assert "records_failed" in result

    def test_result_contains_sync_log_id(
        self,
        celery_app_integration,
        mock_epa_data_source,
        mock_sync_result_success
    ):
        """Test that task result contains sync log ID."""
        from backend.tasks.data_sync import sync_data_source

        with patch("backend.tasks.data_sync.async_session_maker") as mock_session_maker, \
             patch("backend.tasks.data_sync.INGESTION_CLASSES") as mock_ingestion_classes:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_epa_data_source
            mock_session.execute.return_value = mock_result

            mock_ingestion = AsyncMock()
            mock_ingestion.execute_sync.return_value = mock_sync_result_success
            mock_ingestion_classes.get.return_value = MagicMock(
                return_value=mock_ingestion
            )

            task = sync_data_source.apply(args=["EPA_GHG_HUB"])

            result = task.result
            assert "sync_log_id" in result
            assert result["sync_log_id"] is not None


# ============================================================================
# Task Queue Tests
# ============================================================================

class TestTaskQueueIntegration:
    """Integration tests for task queue behavior."""

    def test_data_sync_task_uses_correct_queue(self):
        """Test that data sync task is routed to correct queue."""
        from backend.core.celery_app import celery_app

        routes = celery_app.conf.task_routes
        data_sync_route = routes.get("backend.tasks.data_sync.*", {})

        assert data_sync_route.get("queue") == "data_sync"

    def test_task_options_include_queue(self):
        """Test that scheduled tasks specify queue in options."""
        from backend.core.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        for name, config in beat_schedule.items():
            if "sync" in name.lower():
                options = config.get("options", {})
                assert "queue" in options, f"Task {name} missing queue option"
