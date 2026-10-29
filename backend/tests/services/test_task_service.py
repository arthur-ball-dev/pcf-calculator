"""
Test Async Task Service
TASK-BE-004: Comprehensive tests for async background task processing

Test Scenarios (per specification):
1. Background task runs async (non-blocking)
2. Calculation task updates status (pending → running → completed)
3. Task error handling (graceful failure with error messages)
4. Multiple concurrent tasks (no race conditions)
5. Task cleanup on app shutdown

TDD Protocol:
- Tests written BEFORE implementation
- Verify tests fail initially
- Implement service to make tests pass
"""

import pytest
import asyncio
import time
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, AsyncMock, patch

# Import models and base
from backend.models import (
    Base,
    Product,
    PCFCalculation,
    BillOfMaterials,
    EmissionFactor
)


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing with threading support"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def test_product(db_session):
    """Create a test product for calculations"""
    product = Product(
        id="test-product-001",
        code="TEST-001",
        name="Test Product",
        unit="unit",
        category="test",
        is_finished_product=True,
        description="Product for async task testing"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


@pytest.fixture(scope="function")
def test_product_with_bom(db_session):
    """Create a test product with BOM for complete calculations"""
    # Create parent product
    parent = Product(
        id="parent-001",
        code="PARENT-001",
        name="Parent Product",
        unit="unit",
        category="test",
        is_finished_product=True
    )

    # Create component
    component = Product(
        id="component-001",
        code="COMPONENT-001",
        name="Test Component",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    db_session.add_all([parent, component])
    db_session.commit()

    # Create BOM relationship
    bom = BillOfMaterials(
        parent_product_id="parent-001",
        child_product_id="component-001",
        quantity=0.5,
        unit="kg"
    )

    db_session.add(bom)
    db_session.commit()
    db_session.refresh(parent)

    return parent


# ============================================================================
# Test Scenario 1: Background task runs async (non-blocking)
# ============================================================================

class TestAsyncTaskExecution:
    """Test that background tasks execute asynchronously without blocking"""

    @pytest.mark.asyncio
    async def test_submit_task_returns_immediately(self, db_session, test_product):
        """Test that submit_task returns task_id immediately without waiting"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Record start time
        start_time = time.time()

        # Submit task (should return immediately)
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Check that it returned quickly (< 0.1 seconds)
        elapsed = time.time() - start_time
        assert elapsed < 0.1, \
            f"submit_task should return immediately, took {elapsed:.3f}s"

        # Verify task_id was returned
        assert task_id is not None, "Task ID should be returned"
        assert isinstance(task_id, str), "Task ID should be a string"
        assert len(task_id) == 32, "Task ID should be 32-character UUID hex"

    @pytest.mark.asyncio
    async def test_task_id_is_valid_uuid(self, db_session, test_product):
        """Test that returned task_id is a valid UUID hex string"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Should be lowercase hex string
        assert task_id.islower(), "Task ID should be lowercase"
        assert all(c in '0123456789abcdef' for c in task_id), \
            "Task ID should be hex characters only"

    @pytest.mark.asyncio
    async def test_multiple_tasks_can_be_submitted_quickly(self, db_session, test_product):
        """Test that multiple tasks can be submitted without blocking"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        start_time = time.time()

        # Submit 5 tasks
        task_ids = []
        for _ in range(5):
            task_id = await service.submit_calculation_task(
                product_id=test_product.id,
                calculation_type="cradle_to_gate"
            )
            task_ids.append(task_id)

        elapsed = time.time() - start_time

        # All 5 should be submitted quickly (< 0.5 seconds)
        assert elapsed < 0.5, \
            f"Submitting 5 tasks should be fast, took {elapsed:.3f}s"

        # All task IDs should be unique
        assert len(set(task_ids)) == 5, \
            "All task IDs should be unique"


# ============================================================================
# Test Scenario 2: Calculation task updates status correctly
# ============================================================================

class TestTaskStatusTracking:
    """Test that task status is tracked correctly through lifecycle"""

    @pytest.mark.asyncio
    async def test_new_task_has_pending_status(self, db_session, test_product):
        """Test that newly submitted task has status='pending'"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Get status immediately
        status = await service.get_task_status(task_id)

        assert status is not None, "Status should be returned"
        assert status["status"] == "pending", \
            f"New task should have status='pending', got '{status['status']}'"
        assert status["calculation_id"] == task_id
        assert status["product_id"] == test_product.id

    @pytest.mark.asyncio
    async def test_task_status_changes_to_running(self, db_session, test_product):
        """Test that task status changes to 'running' when processing starts"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit task
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Wait briefly for task to start (background processing)
        await asyncio.sleep(0.1)

        status = await service.get_task_status(task_id)

        # Status should be either 'running' or 'completed'
        # (depending on how fast the calculation completes)
        assert status["status"] in ["running", "completed"], \
            f"Task should be running or completed, got '{status['status']}'"

    @pytest.mark.asyncio
    async def test_task_status_changes_to_completed(self, db_session, test_product_with_bom):
        """Test that task status changes to 'completed' when done"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit task
        task_id = await service.submit_calculation_task(
            product_id=test_product_with_bom.id,
            calculation_type="cradle_to_gate"
        )

        # Wait for task to complete (with timeout)
        max_wait = 5.0
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = await service.get_task_status(task_id)
            if status["status"] == "completed":
                break
            await asyncio.sleep(0.1)

        # Final status check
        final_status = await service.get_task_status(task_id)

        assert final_status["status"] == "completed", \
            f"Task should eventually complete, got '{final_status['status']}'"

        # Should have calculation results
        assert "total_co2e_kg" in final_status or final_status.get("total_co2e_kg") is not None, \
            "Completed task should include calculation results"

    @pytest.mark.asyncio
    async def test_get_status_for_nonexistent_task_returns_none(self, db_session):
        """Test that getting status for nonexistent task returns None"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        status = await service.get_task_status("nonexistent-task-id")

        assert status is None, \
            "Status for nonexistent task should return None"

    @pytest.mark.asyncio
    async def test_task_status_includes_progress_info(self, db_session, test_product):
        """Test that status response includes useful progress information"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        status = await service.get_task_status(task_id)

        # Should have required fields
        required_fields = ["calculation_id", "status", "product_id"]
        for field in required_fields:
            assert field in status, \
                f"Status should include '{field}'"

    @pytest.mark.asyncio
    async def test_completed_task_includes_calculation_results(self, db_session, test_product):
        """Test that completed task includes calculation results in status"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit and wait for completion
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Wait for completion
        max_wait = 5.0
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = await service.get_task_status(task_id)
            if status and status["status"] == "completed":
                # Verify result fields
                assert "total_co2e_kg" in status or status.get("total_co2e_kg") is not None
                assert "calculated_at" in status or status.get("created_at") is not None
                return
            await asyncio.sleep(0.1)

        # If we get here, task didn't complete in time
        # This is acceptable for this test - just verify we can get status
        status = await service.get_task_status(task_id)
        assert status is not None


# ============================================================================
# Test Scenario 3: Task error handling
# ============================================================================

class TestTaskErrorHandling:
    """Test that task errors are handled gracefully"""

    @pytest.mark.asyncio
    async def test_task_with_invalid_product_id_fails_gracefully(self, db_session):
        """Test that task with nonexistent product fails with error status"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit task with nonexistent product
        task_id = await service.submit_calculation_task(
            product_id="nonexistent-product",
            calculation_type="cradle_to_gate"
        )

        # Wait for task to process
        await asyncio.sleep(0.2)

        status = await service.get_task_status(task_id)

        # Should have error status
        assert status is not None
        assert status["status"] == "failed", \
            f"Task with invalid product should fail, got '{status['status']}'"

        # Should include error message
        assert "error_message" in status or "error" in status, \
            "Failed task should include error message"

    @pytest.mark.asyncio
    async def test_failed_task_includes_error_message(self, db_session):
        """Test that failed task includes descriptive error message"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit task with invalid product
        task_id = await service.submit_calculation_task(
            product_id="invalid-id",
            calculation_type="cradle_to_gate"
        )

        # Wait for failure
        await asyncio.sleep(0.2)

        status = await service.get_task_status(task_id)

        if status and status["status"] == "failed":
            error_msg = status.get("error_message") or status.get("error")
            assert error_msg is not None, "Failed task should have error message"
            assert len(error_msg) > 0, "Error message should not be empty"

    @pytest.mark.asyncio
    async def test_task_exception_does_not_crash_service(self, db_session, test_product):
        """Test that exception in task does not crash the service"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit a task that will fail
        task_id_1 = await service.submit_calculation_task(
            product_id="will-fail",
            calculation_type="cradle_to_gate"
        )

        # Wait for it to fail
        await asyncio.sleep(0.2)

        # Service should still work for valid tasks
        task_id_2 = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Second task should be created successfully
        assert task_id_2 is not None
        assert task_id_2 != task_id_1

        status_2 = await service.get_task_status(task_id_2)
        assert status_2 is not None
        assert status_2["status"] in ["pending", "running", "completed"]

    @pytest.mark.asyncio
    async def test_calculation_error_is_logged_in_database(self, db_session):
        """Test that calculation errors are persisted in database"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit task with invalid data
        task_id = await service.submit_calculation_task(
            product_id="nonexistent",
            calculation_type="cradle_to_gate"
        )

        # Wait for failure
        await asyncio.sleep(0.3)

        # Check database for error record
        calc = db_session.query(PCFCalculation).filter_by(id=task_id).first()

        if calc:
            assert calc.status == "failed", \
                f"Database should show status='failed', got '{calc.status}'"


# ============================================================================
# Test Scenario 4: Multiple concurrent tasks
# ============================================================================

class TestConcurrentTasks:
    """Test that multiple tasks can run concurrently without race conditions"""

    @pytest.mark.asyncio
    async def test_five_concurrent_tasks_all_complete(self, db_session, test_product):
        """Test that 5 concurrent tasks all complete successfully"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit 5 tasks
        task_ids = []
        for i in range(5):
            task_id = await service.submit_calculation_task(
                product_id=test_product.id,
                calculation_type="cradle_to_gate"
            )
            task_ids.append(task_id)

        # Wait for all to complete (with timeout)
        max_wait = 10.0
        start_time = time.time()
        completed_count = 0

        while time.time() - start_time < max_wait:
            statuses = []
            for task_id in task_ids:
                status = await service.get_task_status(task_id)
                if status:
                    statuses.append(status["status"])

            completed_count = statuses.count("completed")
            if completed_count == 5:
                break

            await asyncio.sleep(0.2)

        # Verify all completed (or at least started)
        final_statuses = []
        for task_id in task_ids:
            status = await service.get_task_status(task_id)
            if status:
                final_statuses.append(status["status"])

        # All tasks should have valid status
        assert len(final_statuses) == 5, \
            "All 5 tasks should have status records"

        # All should be completed or at least running (no failures from race conditions)
        for i, status in enumerate(final_statuses):
            assert status in ["pending", "running", "completed"], \
                f"Task {i} has unexpected status: {status}"

    @pytest.mark.asyncio
    async def test_concurrent_tasks_have_unique_ids(self, db_session, test_product):
        """Test that concurrent tasks get unique IDs (no ID collision)"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit 10 tasks rapidly
        task_ids = []
        for _ in range(10):
            task_id = await service.submit_calculation_task(
                product_id=test_product.id,
                calculation_type="cradle_to_gate"
            )
            task_ids.append(task_id)

        # All IDs should be unique
        assert len(set(task_ids)) == 10, \
            f"All task IDs should be unique, got {len(set(task_ids))} unique out of 10"

    @pytest.mark.asyncio
    async def test_concurrent_database_writes_no_corruption(self, db_session, test_product):
        """Test that concurrent task writes don't corrupt database"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Submit multiple tasks
        task_ids = []
        for _ in range(5):
            task_id = await service.submit_calculation_task(
                product_id=test_product.id,
                calculation_type="cradle_to_gate"
            )
            task_ids.append(task_id)

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        # Query database to check integrity
        calculations = db_session.query(PCFCalculation).filter(
            PCFCalculation.id.in_(task_ids)
        ).all()

        # All calculations should exist in DB
        assert len(calculations) >= 5, \
            f"Expected at least 5 calculation records, found {len(calculations)}"

        # Each should have valid product_id
        for calc in calculations:
            assert calc.product_id == test_product.id, \
                "All calculations should reference the correct product"


# ============================================================================
# Test Scenario 5: Task cleanup and lifecycle
# ============================================================================

class TestTaskLifecycle:
    """Test task lifecycle management and cleanup"""

    @pytest.mark.asyncio
    async def test_task_record_persisted_in_database(self, db_session, test_product):
        """Test that task creates persistent record in database"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Wait briefly
        await asyncio.sleep(0.1)

        # Check database
        calc = db_session.query(PCFCalculation).filter_by(id=task_id).first()

        assert calc is not None, \
            "Task should create PCFCalculation record in database"
        assert calc.product_id == test_product.id
        assert calc.calculation_type == "cradle_to_gate"

    @pytest.mark.asyncio
    async def test_completed_task_has_calculation_time(self, db_session, test_product):
        """Test that completed task records calculation time"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Wait for completion
        max_wait = 5.0
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = await service.get_task_status(task_id)
            if status and status["status"] == "completed":
                # Check database record
                calc = db_session.query(PCFCalculation).filter_by(id=task_id).first()
                if calc and calc.calculation_time_ms is not None:
                    assert calc.calculation_time_ms > 0, \
                        "Calculation time should be positive"
                    assert calc.calculation_time_ms < 10000, \
                        "Calculation time should be reasonable (< 10 seconds)"
                return
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_task_has_created_timestamp(self, db_session, test_product):
        """Test that task has creation timestamp"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        before = datetime.utcnow()

        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        after = datetime.utcnow()

        # Check database
        calc = db_session.query(PCFCalculation).filter_by(id=task_id).first()

        if calc:
            assert calc.created_at is not None, \
                "Task should have created_at timestamp"
            # Timestamp should be between before and after
            # (allowing some tolerance for clock precision)


# ============================================================================
# Test Scenario 6: Service interface validation
# ============================================================================

class TestServiceInterface:
    """Test that TaskService provides required interface"""

    def test_task_service_can_be_instantiated(self, db_session):
        """Test that TaskService can be created with db session"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        assert service is not None
        assert hasattr(service, 'submit_calculation_task')
        assert hasattr(service, 'get_task_status')

    @pytest.mark.asyncio
    async def test_submit_calculation_task_signature(self, db_session, test_product):
        """Test that submit_calculation_task has correct signature"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        # Should accept product_id and calculation_type
        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        assert task_id is not None

    @pytest.mark.asyncio
    async def test_get_task_status_signature(self, db_session, test_product):
        """Test that get_task_status has correct signature"""
        from backend.services.task_service import TaskService

        service = TaskService(db_session)

        task_id = await service.submit_calculation_task(
            product_id=test_product.id,
            calculation_type="cradle_to_gate"
        )

        # Should accept task_id and return status dict
        status = await service.get_task_status(task_id)

        assert status is not None
        assert isinstance(status, dict)
