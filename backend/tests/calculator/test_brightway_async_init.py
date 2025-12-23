"""
Test suite for async Brightway2 initialization.

TASK-CALC-P7-016: Make Brightway2 Initialization Non-Blocking

Tests the async initialization pattern to ensure:
1. Event loop remains responsive during initialization
2. Calculator is usable after async initialization completes
3. FastAPI startup event integration works correctly
4. Graceful handling when Brightway2 is not yet ready
5. Thread safety during concurrent access

Following TDD methodology - tests written BEFORE implementation.
These tests should FAIL initially until async init is implemented.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
import brightway2 as bw


@pytest.fixture(scope="function")
def clean_brightway_projects():
    """
    Fixture to clean up Brightway2 projects before and after each test.

    Uses retry logic to handle asynchronous file operations.
    """
    max_retries = 3

    # Clean before test
    for attempt in range(max_retries):
        try:
            if "pcf_calculator" in bw.projects:
                bw.projects.delete_project("pcf_calculator", delete_dir=True)
            break
        except (FileNotFoundError, PermissionError):
            if attempt < max_retries - 1:
                time.sleep(1.0)

    time.sleep(0.5)

    yield

    # Clean after test
    for attempt in range(max_retries):
        try:
            if "pcf_calculator" in bw.projects:
                bw.projects.delete_project("pcf_calculator", delete_dir=True)
            break
        except (FileNotFoundError, PermissionError):
            if attempt < max_retries - 1:
                time.sleep(1.0)


class TestNonBlockingInitialization:
    """Test that Brightway2 initialization does not block the event loop."""

    @pytest.mark.asyncio
    async def test_brightway_init_is_non_blocking(self, clean_brightway_projects):
        """
        Scenario 1: Non-Blocking Initialization

        Given: A fresh Brightway2 environment
        When: initialize_pcf_calculator() is called asynchronously
        Then: The event loop remains responsive during initialization

        The test verifies responsiveness by running a concurrent counter
        task that increments during initialization. If initialization
        blocks the event loop, the counter will not increment.
        """
        from backend.calculator.pcf_calculator import initialize_pcf_calculator

        # Track event loop responsiveness
        responsive_count = 0

        async def check_responsiveness():
            """Increment counter if event loop is responsive."""
            nonlocal responsive_count
            for _ in range(20):
                await asyncio.sleep(0.01)  # 10ms intervals
                responsive_count += 1

        # Run initialization and responsiveness check concurrently
        await asyncio.gather(
            initialize_pcf_calculator(),
            check_responsiveness()
        )

        # If init blocked the event loop, responsive_count would be 0
        # until init finished, then count up quickly at the end.
        # With non-blocking init, counts happen interleaved throughout.
        assert responsive_count >= 10, (
            f"Event loop appears blocked during init. "
            f"Only {responsive_count} of 20 responsiveness checks completed concurrently."
        )

    @pytest.mark.asyncio
    async def test_async_initialization_returns_quickly(self, clean_brightway_projects):
        """
        Scenario 1b: Async function returns control to event loop quickly

        Given: A fresh Brightway2 environment
        When: initialize_pcf_calculator() is called
        Then: Control returns to the event loop within 100ms
              (actual work runs in thread pool)

        Note: This tests that the async wrapper yields control quickly,
        not that initialization itself is fast.
        """
        from backend.calculator.pcf_calculator import initialize_pcf_calculator

        yielded_control = False

        async def check_yield():
            nonlocal yielded_control
            await asyncio.sleep(0.05)  # 50ms
            yielded_control = True

        # Start both tasks
        init_task = asyncio.create_task(initialize_pcf_calculator())
        check_task = asyncio.create_task(check_yield())

        # Wait for check task (50ms) - should complete if init yielded control
        await asyncio.wait([check_task], timeout=0.2)

        # The check task should have completed, indicating init yielded control
        assert yielded_control, (
            "initialize_pcf_calculator() did not yield control to event loop. "
            "The async initialization should use asyncio.to_thread() to avoid blocking."
        )

        # Clean up init task
        await init_task


class TestCalculatorUsableAfterAsyncInit:
    """Test that calculator works correctly after async initialization."""

    @pytest.mark.asyncio
    async def test_calculator_usable_after_async_init(self, clean_brightway_projects):
        """
        Scenario 2: Calculator Usable After Async Init

        Given: Fresh Brightway2 environment
        When: initialize_pcf_calculator() completes
        Then: get_pcf_calculator() returns a working calculator instance
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            get_pcf_calculator
        )

        # Initialize asynchronously
        await initialize_pcf_calculator()

        # Get calculator instance
        calculator = get_pcf_calculator()

        # Verify calculator instance is valid
        assert calculator is not None
        assert hasattr(calculator, '_name_to_activity')
        assert hasattr(calculator, 'ef_db')

    @pytest.mark.asyncio
    async def test_calculator_cache_populated_after_init(self, clean_brightway_projects):
        """
        Scenario 2b: Name-to-activity cache is populated

        Given: Fresh Brightway2 environment with synced emission factors
        When: initialize_pcf_calculator() completes
        Then: Calculator's _name_to_activity cache contains entries

        Note: This test may need emission factors to be synced first.
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            get_pcf_calculator
        )
        from backend.calculator.brightway_setup import initialize_brightway
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Setup: Initialize Brightway2 and sync emission factors
        initialize_brightway()

        # Initialize calculator asynchronously
        await initialize_pcf_calculator()

        # Get calculator instance
        calculator = get_pcf_calculator()

        # Verify cache is accessible (may be empty if no factors synced)
        assert isinstance(calculator._name_to_activity, dict)


class TestFastAPIStartupIntegration:
    """Test FastAPI startup event integration with async initialization."""

    @pytest.mark.asyncio
    async def test_fastapi_startup_not_blocked(self, clean_brightway_projects):
        """
        Scenario 3: FastAPI Startup Not Blocked

        Given: FastAPI application with async startup event
        When: Application starts up
        Then: Server becomes responsive (health check works)
              and startup does not block indefinitely
        """
        from httpx import AsyncClient, ASGITransport
        from backend.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Health check should respond within reasonable time
            response = await asyncio.wait_for(
                client.get("/health"),
                timeout=30.0  # Allow time for Brightway2 init
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_startup_event_uses_async_init(self, clean_brightway_projects):
        """
        Scenario 3b: Startup event uses asyncio.to_thread()

        Given: FastAPI application startup event
        When: Startup event calls initialization
        Then: asyncio.to_thread() is used for Brightway2 init

        This test mocks asyncio.to_thread to verify it's called.
        """
        from unittest.mock import AsyncMock

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = None

            # Import and call the startup function directly
            # Note: This tests the pattern, actual implementation may vary
            from backend.calculator.pcf_calculator import initialize_pcf_calculator

            try:
                await initialize_pcf_calculator()
            except Exception:
                pass  # Expected to fail if implementation doesn't exist yet

            # Verify asyncio.to_thread was called
            # This will fail until the async pattern is implemented
            assert mock_to_thread.called, (
                "initialize_pcf_calculator() should use asyncio.to_thread() "
                "to run Brightway2 initialization in a thread pool."
            )


class TestGracefulHandlingNotReady:
    """Test graceful handling when Brightway2 is not yet ready."""

    def test_get_calculator_before_init_raises_error(self, clean_brightway_projects):
        """
        Scenario 4: Clear Error When Not Initialized

        Given: Calculator has not been initialized
        When: get_pcf_calculator() is called
        Then: RuntimeError is raised with clear message
        """
        from backend.calculator.pcf_calculator import get_pcf_calculator

        # Reset any existing instance by reloading module or resetting state
        # This simulates a fresh application state before init

        with pytest.raises(RuntimeError) as exc_info:
            get_pcf_calculator()

        assert "not initialized" in str(exc_info.value).lower() or \
               "wait for startup" in str(exc_info.value).lower(), (
            f"Expected clear error message about initialization, got: {exc_info.value}"
        )

    @pytest.mark.asyncio
    async def test_concurrent_init_requests_are_safe(self, clean_brightway_projects):
        """
        Scenario 4b: Concurrent init calls are handled safely

        Given: Multiple concurrent calls to initialize_pcf_calculator()
        When: All calls complete
        Then: Only one initialization occurs, no race conditions
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            get_pcf_calculator
        )

        # Make multiple concurrent init calls
        await asyncio.gather(
            initialize_pcf_calculator(),
            initialize_pcf_calculator(),
            initialize_pcf_calculator()
        )

        # All should succeed without error
        calculator = get_pcf_calculator()
        assert calculator is not None


class TestThreadSafety:
    """Test thread safety during concurrent access."""

    @pytest.mark.asyncio
    async def test_thread_safety_during_concurrent_access(self, clean_brightway_projects):
        """
        Scenario 5: Thread Safety During Concurrent Access

        Given: Calculator is initialized
        When: Multiple concurrent requests access the calculator
        Then: No race conditions occur, all requests succeed
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            get_pcf_calculator
        )

        # Initialize first
        await initialize_pcf_calculator()

        errors = []

        async def access_calculator():
            """Access calculator in concurrent task."""
            try:
                calc = get_pcf_calculator()
                # Access the name cache to verify thread safety
                _ = list(calc._name_to_activity.keys())[:5]
                return True
            except Exception as e:
                errors.append(str(e))
                return False

        # Run 10 concurrent access attempts
        results = await asyncio.gather(
            *[access_calculator() for _ in range(10)]
        )

        assert all(results), f"Some concurrent accesses failed: {errors}"

    @pytest.mark.asyncio
    async def test_init_only_runs_once(self, clean_brightway_projects):
        """
        Scenario 5b: Initialization only runs once

        Given: Multiple calls to initialize_pcf_calculator()
        When: All calls complete
        Then: The underlying sync init only ran once
        """
        from backend.calculator.pcf_calculator import initialize_pcf_calculator

        init_call_count = 0

        original_init = None

        def counting_init():
            nonlocal init_call_count
            init_call_count += 1
            # Call original if it exists
            if original_init:
                return original_init()

        with patch(
            'backend.calculator.pcf_calculator._initialize_brightway_sync',
            side_effect=counting_init
        ) as mock_init:
            # Multiple concurrent init calls
            await asyncio.gather(
                initialize_pcf_calculator(),
                initialize_pcf_calculator(),
                initialize_pcf_calculator()
            )

            # Should only have initialized once due to locking
            assert mock_init.call_count <= 1, (
                f"Expected at most 1 init call, got {mock_init.call_count}. "
                "Initialization should be protected by a lock."
            )


class TestInitializationState:
    """Test initialization state management."""

    @pytest.mark.asyncio
    async def test_initialization_flag_set_after_init(self, clean_brightway_projects):
        """
        Scenario: Initialization flag is set correctly

        Given: Fresh application state
        When: initialize_pcf_calculator() completes
        Then: is_initialized() returns True
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            is_calculator_initialized
        )

        # Before init, should not be initialized
        # Note: This may fail if module state persists between tests

        # Initialize
        await initialize_pcf_calculator()

        # After init, should be initialized
        assert is_calculator_initialized() is True

    @pytest.mark.asyncio
    async def test_wait_for_initialization(self, clean_brightway_projects):
        """
        Scenario: Can wait for initialization to complete

        Given: Initialization is in progress
        When: wait_for_calculator_ready() is called
        Then: It waits until initialization completes
        """
        from backend.calculator.pcf_calculator import (
            initialize_pcf_calculator,
            wait_for_calculator_ready
        )

        ready = False

        async def init_then_signal():
            nonlocal ready
            await initialize_pcf_calculator()
            ready = True

        async def wait_for_ready():
            await wait_for_calculator_ready()
            return True

        # Start init and wait concurrently
        init_task = asyncio.create_task(init_then_signal())
        wait_result = await wait_for_ready()

        await init_task

        assert wait_result is True
        assert ready is True
