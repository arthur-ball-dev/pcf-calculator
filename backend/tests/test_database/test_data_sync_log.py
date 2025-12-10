"""
Test suite for DataSyncLog model.

TASK-DB-P5-002: Extended Database Schema - Phase A Tests

This test suite validates:
- DataSyncLog CRUD operations (create, read, update, delete)
- Status transitions (pending -> in_progress -> completed/failed)
- Foreign key relationship with data_source
- Timestamps updated correctly
- Record counters
- Error handling fields

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no DataSyncLog model exists yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta
import json


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing."""
    from backend.models import Base
    try:
        from backend.models import DataSyncLog, DataSource
    except ImportError:
        pytest.skip("DataSyncLog or DataSource model not yet implemented")

    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def data_source(db_session):
    """Create a data source for sync log tests."""
    from backend.models import DataSource

    source = DataSource(
        name="Test Data Source",
        source_type="file"
    )
    db_session.add(source)
    db_session.commit()
    return source


# ============================================================================
# Test Scenario 1: DataSyncLog CRUD Operations
# ============================================================================

class TestDataSyncLogCRUD:
    """Test DataSyncLog model CRUD operations."""

    def test_create_sync_log_with_required_fields(self, db_session: Session, data_source):
        """Test creating a sync log with all required fields."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Sync log created with auto-generated UUID id
        assert sync_log.id is not None
        assert sync_log.data_source_id == data_source.id
        assert sync_log.sync_type == "scheduled"
        assert sync_log.status == "pending"
        assert sync_log.started_at is not None

        # Default values
        assert sync_log.records_processed == 0
        assert sync_log.records_created == 0
        assert sync_log.records_updated == 0
        assert sync_log.records_skipped == 0
        assert sync_log.records_failed == 0
        assert sync_log.created_at is not None

    def test_create_sync_log_with_all_fields(self, db_session: Session, data_source):
        """Test creating a sync log with all fields populated."""
        from backend.models import DataSyncLog

        now = datetime.now(timezone.utc)
        metadata_json = {"source_file": "data.csv", "version": "1.0"}

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="completed",
            celery_task_id="abc123-task-id",
            records_processed=100,
            records_created=80,
            records_updated=15,
            records_skipped=3,
            records_failed=2,
            error_message=None,
            error_details=None,
            metadata=metadata_json,
            started_at=now,
            completed_at=now + timedelta(minutes=5)
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.celery_task_id == "abc123-task-id"
        assert sync_log.records_processed == 100
        assert sync_log.records_created == 80
        assert sync_log.records_updated == 15
        assert sync_log.records_skipped == 3
        assert sync_log.records_failed == 2
        assert sync_log.completed_at is not None

    def test_read_sync_log_by_id(self, db_session: Session, data_source):
        """Test reading a sync log by ID."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        log_id = sync_log.id

        # Clear session cache
        db_session.expire_all()

        # Read by ID
        retrieved = db_session.get(DataSyncLog, log_id)
        assert retrieved is not None
        assert retrieved.sync_type == "initial"
        assert retrieved.status == "in_progress"

    def test_update_sync_log(self, db_session: Session, data_source):
        """Test updating a sync log."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Update sync log
        sync_log.status = "in_progress"
        sync_log.records_processed = 50
        db_session.commit()

        # Verify update
        db_session.expire_all()
        retrieved = db_session.get(DataSyncLog, sync_log.id)
        assert retrieved.status == "in_progress"
        assert retrieved.records_processed == 50

    def test_delete_sync_log(self, db_session: Session, data_source):
        """Test deleting a sync log."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        log_id = sync_log.id

        # Delete sync log
        db_session.delete(sync_log)
        db_session.commit()

        # Verify deletion
        retrieved = db_session.get(DataSyncLog, log_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 2: Status Transitions
# ============================================================================

class TestStatusTransitions:
    """Test sync log status transitions."""

    def test_pending_to_in_progress(self, db_session: Session, data_source):
        """Test transition from pending to in_progress."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.status == "pending"

        # Transition to in_progress
        sync_log.status = "in_progress"
        db_session.commit()

        assert sync_log.status == "in_progress"

    def test_in_progress_to_completed(self, db_session: Session, data_source):
        """Test transition from in_progress to completed."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            records_processed=100
        )
        db_session.add(sync_log)
        db_session.commit()

        # Transition to completed
        sync_log.status = "completed"
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.records_created = 95
        sync_log.records_updated = 5
        db_session.commit()

        assert sync_log.status == "completed"
        assert sync_log.completed_at is not None
        assert sync_log.records_created == 95
        assert sync_log.records_updated == 5

    def test_in_progress_to_failed(self, db_session: Session, data_source):
        """Test transition from in_progress to failed."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            records_processed=50
        )
        db_session.add(sync_log)
        db_session.commit()

        # Transition to failed
        sync_log.status = "failed"
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.error_message = "Connection timeout"
        sync_log.error_details = {"error_code": "TIMEOUT", "retry_count": 3}
        db_session.commit()

        assert sync_log.status == "failed"
        assert sync_log.error_message == "Connection timeout"
        assert sync_log.error_details["error_code"] == "TIMEOUT"

    def test_pending_to_cancelled(self, db_session: Session, data_source):
        """Test transition from pending to cancelled."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Transition to cancelled
        sync_log.status = "cancelled"
        sync_log.completed_at = datetime.now(timezone.utc)
        db_session.commit()

        assert sync_log.status == "cancelled"

    def test_full_lifecycle_pending_to_completed(self, db_session: Session, data_source):
        """Test full lifecycle: pending -> in_progress -> completed."""
        from backend.models import DataSyncLog

        # Create in pending state
        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Move to in_progress
        sync_log.status = "in_progress"
        db_session.commit()

        # Simulate processing
        sync_log.records_processed = 200
        sync_log.records_created = 150
        sync_log.records_updated = 45
        sync_log.records_skipped = 5
        db_session.commit()

        # Complete
        sync_log.status = "completed"
        sync_log.completed_at = datetime.now(timezone.utc)
        db_session.commit()

        assert sync_log.status == "completed"
        assert sync_log.records_processed == 200
        assert sync_log.records_created == 150
        assert sync_log.records_updated == 45
        assert sync_log.records_skipped == 5


# ============================================================================
# Test Scenario 3: Foreign Key Relationship with DataSource
# ============================================================================

class TestDataSyncLogDataSourceRelationship:
    """Test foreign key relationship with DataSource."""

    def test_sync_log_requires_data_source(self, db_session: Session):
        """Test that sync log requires a valid data source."""
        from backend.models import DataSyncLog

        # Try to create sync log without data source
        sync_log = DataSyncLog(
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_sync_log_invalid_data_source_fails(self, db_session: Session):
        """Test that sync log with invalid data source ID fails."""
        from backend.models import DataSyncLog
        import uuid

        sync_log = DataSyncLog(
            data_source_id=uuid.uuid4().hex,  # Non-existent ID
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_data_source_relationship_access(self, db_session: Session, data_source):
        """Test accessing data source via relationship."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Refresh to load relationship
        db_session.refresh(sync_log)

        # Access data source via relationship
        assert sync_log.data_source is not None
        assert sync_log.data_source.name == "Test Data Source"

    def test_data_source_sync_logs_backref(self, db_session: Session, data_source):
        """Test accessing sync logs from data source."""
        from backend.models import DataSyncLog

        # Create multiple sync logs
        log1 = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="completed",
            started_at=datetime.now(timezone.utc)
        )
        log2 = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        # Refresh data source
        db_session.refresh(data_source)

        # Access sync logs via relationship
        assert len(data_source.sync_logs) == 2


# ============================================================================
# Test Scenario 4: Timestamps
# ============================================================================

class TestSyncLogTimestamps:
    """Test timestamp fields behavior."""

    def test_created_at_auto_set(self, db_session: Session, data_source):
        """Test that created_at is automatically set."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.created_at is not None

    def test_started_at_required(self, db_session: Session, data_source):
        """Test that started_at is a required field."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending"
            # started_at not provided
        )
        db_session.add(sync_log)

        # This should fail due to NOT NULL constraint
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_completed_at_optional(self, db_session: Session, data_source):
        """Test that completed_at is optional."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="in_progress",
            started_at=datetime.now(timezone.utc)
            # completed_at not provided
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.completed_at is None

    def test_completed_at_set_on_completion(self, db_session: Session, data_source):
        """Test setting completed_at when sync completes."""
        from backend.models import DataSyncLog

        start_time = datetime.now(timezone.utc)
        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="in_progress",
            started_at=start_time
        )
        db_session.add(sync_log)
        db_session.commit()

        # Complete the sync
        end_time = datetime.now(timezone.utc)
        sync_log.status = "completed"
        sync_log.completed_at = end_time
        db_session.commit()

        assert sync_log.completed_at >= sync_log.started_at


# ============================================================================
# Test Scenario 5: Record Counters
# ============================================================================

class TestRecordCounters:
    """Test record counter fields."""

    def test_default_counters_are_zero(self, db_session: Session, data_source):
        """Test that all record counters default to 0."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.records_processed == 0
        assert sync_log.records_created == 0
        assert sync_log.records_updated == 0
        assert sync_log.records_skipped == 0
        assert sync_log.records_failed == 0

    def test_increment_counters(self, db_session: Session, data_source):
        """Test incrementing record counters."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Update counters
        sync_log.records_processed = 1000
        sync_log.records_created = 800
        sync_log.records_updated = 150
        sync_log.records_skipped = 30
        sync_log.records_failed = 20
        db_session.commit()

        # Verify
        db_session.expire_all()
        retrieved = db_session.get(DataSyncLog, sync_log.id)
        assert retrieved.records_processed == 1000
        assert retrieved.records_created == 800
        assert retrieved.records_updated == 150
        assert retrieved.records_skipped == 30
        assert retrieved.records_failed == 20

    def test_counters_sum_validation(self, db_session: Session, data_source):
        """Test that counters can reflect processing totals."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            records_processed=100,
            records_created=60,
            records_updated=30,
            records_skipped=5,
            records_failed=5
        )
        db_session.add(sync_log)
        db_session.commit()

        # Verify sum matches processed
        total_outcome = (
            sync_log.records_created +
            sync_log.records_updated +
            sync_log.records_skipped +
            sync_log.records_failed
        )
        assert total_outcome == sync_log.records_processed


# ============================================================================
# Test Scenario 6: Error Handling Fields
# ============================================================================

class TestErrorHandlingFields:
    """Test error handling fields behavior."""

    def test_error_message_text(self, db_session: Session, data_source):
        """Test storing error message."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="failed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            error_message="Database connection failed: timeout after 30s"
        )
        db_session.add(sync_log)
        db_session.commit()

        assert "timeout" in sync_log.error_message

    def test_error_details_json(self, db_session: Session, data_source):
        """Test storing structured error details as JSON."""
        from backend.models import DataSyncLog

        error_details = {
            "error_type": "ConnectionError",
            "error_code": "DB_TIMEOUT",
            "stack_trace": "File 'sync.py', line 42...",
            "retry_attempts": 3,
            "last_successful_record": 150
        }

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="failed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            error_message="Sync failed",
            error_details=error_details
        )
        db_session.add(sync_log)
        db_session.commit()

        # Verify JSON stored correctly
        db_session.expire_all()
        retrieved = db_session.get(DataSyncLog, sync_log.id)
        assert retrieved.error_details["error_type"] == "ConnectionError"
        assert retrieved.error_details["retry_attempts"] == 3

    def test_no_error_when_successful(self, db_session: Session, data_source):
        """Test that successful syncs have no error fields."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            records_processed=100,
            records_created=100
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.error_message is None
        assert sync_log.error_details is None


# ============================================================================
# Test Scenario 7: Sync Type Validation
# ============================================================================

class TestSyncTypeValidation:
    """Test sync_type field validation."""

    def test_valid_sync_types(self, db_session: Session, data_source):
        """Test that valid sync types are accepted."""
        from backend.models import DataSyncLog

        valid_types = ["scheduled", "manual", "initial"]

        for i, sync_type in enumerate(valid_types):
            sync_log = DataSyncLog(
                data_source_id=data_source.id,
                sync_type=sync_type,
                status="pending",
                started_at=datetime.now(timezone.utc)
            )
            db_session.add(sync_log)

        db_session.commit()

        # All should be created successfully
        from backend.models import DataSyncLog
        count = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).count()
        assert count == 3


# ============================================================================
# Test Scenario 8: Metadata Field
# ============================================================================

class TestMetadataField:
    """Test metadata JSON field behavior."""

    def test_metadata_optional(self, db_session: Session, data_source):
        """Test that metadata is optional."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
            # metadata not provided
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.metadata is None

    def test_metadata_stores_json(self, db_session: Session, data_source):
        """Test storing arbitrary JSON in metadata."""
        from backend.models import DataSyncLog

        metadata = {
            "source_file": "emission_factors_2024.csv",
            "file_hash": "abc123def456",
            "file_size_bytes": 1024000,
            "columns": ["activity", "factor", "unit"],
            "configuration": {
                "skip_header": True,
                "delimiter": ","
            }
        }

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            metadata=metadata
        )
        db_session.add(sync_log)
        db_session.commit()

        # Verify JSON stored correctly
        db_session.expire_all()
        retrieved = db_session.get(DataSyncLog, sync_log.id)
        assert retrieved.metadata["source_file"] == "emission_factors_2024.csv"
        assert retrieved.metadata["configuration"]["skip_header"] is True


# ============================================================================
# Test Scenario 9: Celery Task ID
# ============================================================================

class TestCeleryTaskId:
    """Test celery_task_id field behavior."""

    def test_celery_task_id_optional(self, db_session: Session, data_source):
        """Test that celery_task_id is optional."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.celery_task_id is None

    def test_celery_task_id_stored(self, db_session: Session, data_source):
        """Test storing celery task ID."""
        from backend.models import DataSyncLog

        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            celery_task_id="abc123-def456-ghi789"
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.celery_task_id == "abc123-def456-ghi789"

    def test_query_by_celery_task_id(self, db_session: Session, data_source):
        """Test querying sync log by celery task ID."""
        from backend.models import DataSyncLog

        task_id = "unique-task-id-12345"
        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            celery_task_id=task_id
        )
        db_session.add(sync_log)
        db_session.commit()

        # Query by task ID
        retrieved = db_session.query(DataSyncLog).filter(
            DataSyncLog.celery_task_id == task_id
        ).first()
        assert retrieved is not None
        assert retrieved.id == sync_log.id


# ============================================================================
# Test Scenario 10: Filtering and Queries
# ============================================================================

class TestSyncLogQueries:
    """Test common query patterns for sync logs."""

    def test_filter_by_status(self, db_session: Session, data_source):
        """Test filtering sync logs by status."""
        from backend.models import DataSyncLog

        # Create logs with different statuses
        pending = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        completed = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            started_at=datetime.now(timezone.utc)
        )
        failed = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="failed",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add_all([pending, completed, failed])
        db_session.commit()

        # Filter by status
        pending_logs = db_session.query(DataSyncLog).filter(
            DataSyncLog.status == "pending"
        ).all()
        assert len(pending_logs) >= 1

        completed_logs = db_session.query(DataSyncLog).filter(
            DataSyncLog.status == "completed"
        ).all()
        assert len(completed_logs) >= 1

    def test_order_by_started_at(self, db_session: Session, data_source):
        """Test ordering sync logs by started_at."""
        from backend.models import DataSyncLog

        now = datetime.now(timezone.utc)
        earlier = now - timedelta(hours=1)
        later = now + timedelta(hours=1)

        log1 = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            started_at=now
        )
        log2 = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            started_at=earlier
        )
        log3 = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            started_at=later
        )
        db_session.add_all([log1, log2, log3])
        db_session.commit()

        # Order by started_at descending (most recent first)
        logs = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).order_by(DataSyncLog.started_at.desc()).all()

        assert len(logs) >= 3
        # Most recent should be first
        assert logs[0].started_at >= logs[1].started_at

    def test_get_latest_sync_for_source(self, db_session: Session, data_source):
        """Test getting the latest sync log for a data source."""
        from backend.models import DataSyncLog

        # Create multiple logs
        for i in range(3):
            log = DataSyncLog(
                data_source_id=data_source.id,
                sync_type="scheduled",
                status="completed",
                started_at=datetime.now(timezone.utc) - timedelta(hours=i)
            )
            db_session.add(log)
        db_session.commit()

        # Get latest
        latest = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).order_by(DataSyncLog.started_at.desc()).first()

        assert latest is not None
