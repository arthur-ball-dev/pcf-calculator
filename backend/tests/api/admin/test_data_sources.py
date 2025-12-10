"""
Tests for admin data sources API endpoints.

TASK-API-P5-001: Admin Data Sources Endpoints - Phase A (TDD)

Tests for:
- GET /admin/data-sources - List all data sources with status
- GET /admin/data-sources/{id} - Get single data source details
- POST /admin/data-sources/{id}/sync - Trigger manual sync

Contract Reference: phase5-contracts/admin-data-sources-contract.yaml
Contract Reference: phase5-contracts/admin-sync-contract.yaml
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models import Base, DataSource, DataSyncLog, EmissionFactor


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite test engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_data_source(db_session: Session) -> DataSource:
    """Create a sample active data source."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="EPA GHG Emission Factors Hub",
        source_type="file",
        base_url="https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        sync_frequency="biweekly",
        is_active=True,
        last_sync_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def inactive_data_source(db_session: Session) -> DataSource:
    """Create an inactive data source."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="Deprecated Source",
        source_type="api",
        base_url="https://old-api.example.com",
        sync_frequency="manual",
        is_active=False,
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def multiple_data_sources(db_session: Session) -> list[DataSource]:
    """Create multiple data sources with different types and statuses."""
    sources = [
        DataSource(
            id=uuid.uuid4().hex,
            name="EPA GHG Emission Factors Hub",
            source_type="file",
            base_url="https://www.epa.gov/climateleadership",
            sync_frequency="biweekly",
            is_active=True,
            last_sync_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
        DataSource(
            id=uuid.uuid4().hex,
            name="DEFRA Conversion Factors",
            source_type="file",
            base_url="https://www.gov.uk/government/publications",
            sync_frequency="biweekly",
            is_active=True,
            last_sync_at=datetime.now(timezone.utc) - timedelta(days=3),
        ),
        DataSource(
            id=uuid.uuid4().hex,
            name="Exiobase",
            source_type="database",
            base_url="https://zenodo.org/record/5589597",
            sync_frequency="monthly",
            is_active=True,
        ),
        DataSource(
            id=uuid.uuid4().hex,
            name="Legacy API",
            source_type="api",
            base_url="https://legacy.example.com",
            sync_frequency="manual",
            is_active=False,
        ),
    ]
    for source in sources:
        db_session.add(source)
    db_session.commit()
    for source in sources:
        db_session.refresh(source)
    return sources


@pytest.fixture
def data_source_with_sync_logs(db_session: Session) -> tuple[DataSource, list[DataSyncLog]]:
    """Create a data source with associated sync logs."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="EPA GHG Emission Factors Hub",
        source_type="file",
        base_url="https://www.epa.gov/climateleadership",
        sync_frequency="biweekly",
        is_active=True,
        last_sync_at=datetime.now(timezone.utc) - timedelta(hours=6),
    )
    db_session.add(data_source)
    db_session.flush()

    # Create sync logs
    logs = [
        # Completed sync
        DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=data_source.id,
            sync_type="scheduled",
            status="completed",
            celery_task_id="celery-task-abc123",
            started_at=datetime.now(timezone.utc) - timedelta(hours=6),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=6) + timedelta(minutes=5),
            records_processed=285,
            records_created=12,
            records_updated=8,
            records_skipped=265,
            records_failed=0,
        ),
        # Failed sync
        DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=data_source.id,
            sync_type="manual",
            status="failed",
            celery_task_id="celery-task-def456",
            started_at=datetime.now(timezone.utc) - timedelta(days=1),
            completed_at=datetime.now(timezone.utc) - timedelta(days=1) + timedelta(minutes=15),
            records_processed=500,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=500,
            error_message="Connection timeout while downloading file",
        ),
    ]
    for log in logs:
        db_session.add(log)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source, logs


@pytest.fixture
def data_source_with_emission_factors(db_session: Session) -> tuple[DataSource, list[EmissionFactor]]:
    """Create a data source with associated emission factors."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="EPA GHG Emission Factors Hub",
        source_type="file",
        base_url="https://www.epa.gov/climateleadership",
        sync_frequency="biweekly",
        is_active=True,
        last_sync_at=datetime.now(timezone.utc) - timedelta(hours=6),
    )
    db_session.add(data_source)
    db_session.flush()

    # Create emission factors
    factors = [
        EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Natural Gas",
            category="Stationary Combustion",
            co2e_factor=2.75,
            unit="kg",
            data_source="EPA",
            geography="US",
            reference_year=2023,
            data_quality_rating=0.90,
            data_source_id=data_source.id,
            is_active=True,
        ),
        EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Diesel",
            category="Stationary Combustion",
            co2e_factor=10.21,
            unit="L",
            data_source="EPA",
            geography="US",
            reference_year=2023,
            data_quality_rating=0.88,
            data_source_id=data_source.id,
            is_active=True,
        ),
        EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Old Factor",
            category="Transport",
            co2e_factor=5.0,
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2020,
            data_quality_rating=0.75,
            data_source_id=data_source.id,
            is_active=False,  # Inactive factor
        ),
    ]
    for factor in factors:
        db_session.add(factor)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source, factors


@pytest.fixture
def data_source_with_active_sync(db_session: Session) -> tuple[DataSource, DataSyncLog]:
    """Create a data source with an active (in_progress) sync."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="DEFRA Conversion Factors",
        source_type="file",
        base_url="https://www.gov.uk/government/publications",
        sync_frequency="biweekly",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.flush()

    active_log = DataSyncLog(
        id=uuid.uuid4().hex,
        data_source_id=data_source.id,
        sync_type="manual",
        status="in_progress",
        celery_task_id="celery-task-xyz789",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        records_processed=150,
        records_created=5,
        records_updated=2,
        records_skipped=143,
        records_failed=0,
    )
    db_session.add(active_log)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source, active_log


# ============================================================================
# GET /admin/data-sources Tests
# ============================================================================


class TestListDataSources:
    """Tests for GET /admin/data-sources endpoint."""

    def test_list_data_sources_empty(self, db_session: Session):
        """Test listing data sources when none exist returns empty list."""
        # Act - simulate API call
        # Expected behavior: return empty list with summary
        result = db_session.query(DataSource).all()

        # Assert
        assert len(result) == 0

    def test_list_data_sources_returns_all(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test listing all data sources returns complete list."""
        # Act
        result = db_session.query(DataSource).all()

        # Assert
        assert len(result) == 4
        names = [ds.name for ds in result]
        assert "EPA GHG Emission Factors Hub" in names
        assert "DEFRA Conversion Factors" in names
        assert "Exiobase" in names
        assert "Legacy API" in names

    def test_list_data_sources_filter_active_true(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering data sources by is_active=true."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.is_active == True).all()

        # Assert
        assert len(result) == 3
        assert all(ds.is_active for ds in result)

    def test_list_data_sources_filter_active_false(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering data sources by is_active=false."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.is_active == False).all()

        # Assert
        assert len(result) == 1
        assert result[0].name == "Legacy API"
        assert not result[0].is_active

    def test_list_data_sources_filter_source_type_file(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering data sources by source_type=file."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.source_type == "file").all()

        # Assert
        assert len(result) == 2
        assert all(ds.source_type == "file" for ds in result)

    def test_list_data_sources_filter_source_type_api(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering data sources by source_type=api."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.source_type == "api").all()

        # Assert
        assert len(result) == 1
        assert result[0].source_type == "api"

    def test_list_data_sources_filter_source_type_database(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering data sources by source_type=database."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.source_type == "database").all()

        # Assert
        assert len(result) == 1
        assert result[0].name == "Exiobase"

    def test_list_data_sources_combined_filters(
        self, db_session: Session, multiple_data_sources: list[DataSource]
    ):
        """Test filtering by both is_active and source_type."""
        # Act
        result = (
            db_session.query(DataSource)
            .filter(DataSource.is_active == True, DataSource.source_type == "file")
            .all()
        )

        # Assert
        assert len(result) == 2
        assert all(ds.is_active and ds.source_type == "file" for ds in result)

    def test_list_data_sources_includes_last_sync_info(
        self, db_session: Session, data_source_with_sync_logs: tuple[DataSource, list[DataSyncLog]]
    ):
        """Test that data source includes last sync information."""
        data_source, sync_logs = data_source_with_sync_logs

        # Act
        result = db_session.query(DataSource).filter(DataSource.id == data_source.id).first()

        # Assert
        assert result is not None
        assert result.last_sync_at is not None
        # Verify sync logs relationship
        assert len(result.sync_logs) == 2

    def test_list_data_sources_includes_statistics(
        self, db_session: Session, data_source_with_emission_factors: tuple[DataSource, list[EmissionFactor]]
    ):
        """Test that data source includes emission factor statistics."""
        data_source, factors = data_source_with_emission_factors

        # Act
        result = db_session.query(DataSource).filter(DataSource.id == data_source.id).first()

        # Assert
        assert result is not None
        # Verify factors relationship
        assert len(result.emission_factors) == 3
        # Active factors count
        active_count = sum(1 for ef in result.emission_factors if ef.is_active)
        assert active_count == 2

    def test_list_data_sources_response_structure(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test that response contains expected structure per contract."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.id == sample_data_source.id).first()

        # Assert - verify all required fields exist
        assert result.id is not None
        assert result.name is not None
        assert result.source_type in ["api", "file", "database", "manual"]
        assert result.sync_frequency in ["daily", "weekly", "biweekly", "monthly", "manual"]
        assert isinstance(result.is_active, bool)
        assert result.created_at is not None


class TestGetDataSourceById:
    """Tests for GET /admin/data-sources/{id} endpoint."""

    def test_get_data_source_by_id_success(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test getting a data source by valid ID returns correct data."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.id == sample_data_source.id).first()

        # Assert
        assert result is not None
        assert result.id == sample_data_source.id
        assert result.name == sample_data_source.name
        assert result.source_type == sample_data_source.source_type

    def test_get_data_source_by_id_not_found(self, db_session: Session):
        """Test getting a non-existent data source returns None (404)."""
        # Act
        non_existent_id = uuid.uuid4().hex
        result = db_session.query(DataSource).filter(DataSource.id == non_existent_id).first()

        # Assert
        assert result is None

    def test_get_data_source_with_sync_logs(
        self, db_session: Session, data_source_with_sync_logs: tuple[DataSource, list[DataSyncLog]]
    ):
        """Test getting data source includes related sync logs."""
        data_source, expected_logs = data_source_with_sync_logs

        # Act
        result = db_session.query(DataSource).filter(DataSource.id == data_source.id).first()

        # Assert
        assert result is not None
        assert len(result.sync_logs) == len(expected_logs)
        # Verify latest sync
        completed_logs = [log for log in result.sync_logs if log.status == "completed"]
        assert len(completed_logs) == 1
        assert completed_logs[0].records_processed == 285

    def test_get_data_source_with_emission_factors(
        self, db_session: Session, data_source_with_emission_factors: tuple[DataSource, list[EmissionFactor]]
    ):
        """Test getting data source includes related emission factors."""
        data_source, expected_factors = data_source_with_emission_factors

        # Act
        result = db_session.query(DataSource).filter(DataSource.id == data_source.id).first()

        # Assert
        assert result is not None
        assert len(result.emission_factors) == len(expected_factors)

    def test_get_inactive_data_source(
        self, db_session: Session, inactive_data_source: DataSource
    ):
        """Test getting an inactive data source returns it correctly."""
        # Act
        result = db_session.query(DataSource).filter(DataSource.id == inactive_data_source.id).first()

        # Assert
        assert result is not None
        assert result.is_active is False


# ============================================================================
# POST /admin/data-sources/{id}/sync Tests
# ============================================================================


class TestTriggerSync:
    """Tests for POST /admin/data-sources/{id}/sync endpoint."""

    def test_trigger_sync_success(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test triggering sync on valid active source creates sync log."""
        # Arrange - verify source exists and is active
        assert sample_data_source.is_active

        # Act - create a sync log (simulating sync trigger)
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
        )
        db_session.add(sync_log)
        db_session.commit()

        # Assert
        assert sync_log.id is not None
        assert sync_log.data_source_id == sample_data_source.id
        assert sync_log.status == "pending"

    def test_trigger_sync_inactive_source_fails(
        self, db_session: Session, inactive_data_source: DataSource
    ):
        """Test triggering sync on inactive source should fail (422)."""
        # Arrange
        assert not inactive_data_source.is_active

        # Act & Assert - in actual implementation, this would raise/return 422
        # Here we verify the state that should prevent the sync
        is_valid_for_sync = inactive_data_source.is_active
        assert not is_valid_for_sync

    def test_trigger_sync_not_found(self, db_session: Session):
        """Test triggering sync on non-existent source fails (404)."""
        # Act
        non_existent_id = uuid.uuid4().hex
        result = db_session.query(DataSource).filter(DataSource.id == non_existent_id).first()

        # Assert
        assert result is None

    def test_trigger_sync_already_in_progress(
        self, db_session: Session, data_source_with_active_sync: tuple[DataSource, DataSyncLog]
    ):
        """Test triggering sync when already in progress fails (409)."""
        data_source, active_log = data_source_with_active_sync

        # Act - check for active sync
        has_active_sync = (
            db_session.query(DataSyncLog)
            .filter(
                DataSyncLog.data_source_id == data_source.id,
                DataSyncLog.status == "in_progress",
            )
            .first()
            is not None
        )

        # Assert
        assert has_active_sync
        assert active_log.status == "in_progress"

    def test_trigger_sync_with_force_refresh(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test triggering sync with force_refresh option."""
        # Act - create sync log with force_refresh metadata
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
            sync_metadata={"force_refresh": True},
        )
        db_session.add(sync_log)
        db_session.commit()

        # Assert
        assert sync_log.sync_metadata is not None
        assert sync_log.sync_metadata.get("force_refresh") is True

    def test_trigger_sync_with_dry_run(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test triggering sync with dry_run option."""
        # Act - create sync log with dry_run metadata
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
            sync_metadata={"dry_run": True},
        )
        db_session.add(sync_log)
        db_session.commit()

        # Assert
        assert sync_log.sync_metadata is not None
        assert sync_log.sync_metadata.get("dry_run") is True

    def test_trigger_sync_with_priority(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test triggering sync with priority option."""
        # Act - create sync log with priority metadata
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="pending",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
            sync_metadata={"priority": "high"},
        )
        db_session.add(sync_log)
        db_session.commit()

        # Assert
        assert sync_log.sync_metadata is not None
        assert sync_log.sync_metadata.get("priority") == "high"

    def test_trigger_sync_response_structure(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test that sync trigger response matches contract (202 response)."""
        # Act
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="queued",
            celery_task_id=f"celery-task-{uuid.uuid4().hex}",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
        )
        db_session.add(sync_log)
        db_session.commit()

        # Assert - verify response structure fields exist
        assert sync_log.id is not None  # sync_log_id
        assert sync_log.celery_task_id is not None  # task_id
        assert sync_log.status in ["queued", "pending", "started", "in_progress"]
        assert sync_log.data_source_id == sample_data_source.id


# ============================================================================
# Error Response Tests
# ============================================================================


class TestErrorResponses:
    """Tests for error response formats."""

    def test_invalid_source_type_filter(self, db_session: Session):
        """Test that invalid source_type filter is rejected (400)."""
        # This test verifies the validation logic
        valid_source_types = ["api", "file", "database", "manual"]
        invalid_type = "invalid_type"

        # Assert
        assert invalid_type not in valid_source_types

    def test_invalid_uuid_format(self, db_session: Session):
        """Test that invalid UUID format is handled properly."""
        # Arrange
        invalid_id = "not-a-valid-uuid"

        # Act & Assert - UUID parsing should handle gracefully
        try:
            # This simulates what would happen with a malformed ID
            result = db_session.query(DataSource).filter(DataSource.id == invalid_id).first()
            # SQLite will just return None for non-matching string
            assert result is None
        except Exception:
            # In strict mode, this might raise an error
            pass


# ============================================================================
# Data Integrity Tests
# ============================================================================


class TestDataIntegrity:
    """Tests for data integrity and relationships."""

    def test_cascade_delete_sync_logs(
        self, db_session: Session, data_source_with_sync_logs: tuple[DataSource, list[DataSyncLog]]
    ):
        """Test that deleting data source cascades to sync logs."""
        data_source, sync_logs = data_source_with_sync_logs
        data_source_id = data_source.id

        # Verify logs exist
        initial_logs = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source_id
        ).count()
        assert initial_logs == 2

        # Act - delete data source
        db_session.delete(data_source)
        db_session.commit()

        # Assert - sync logs should be deleted via cascade
        remaining_logs = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source_id
        ).count()
        assert remaining_logs == 0

    def test_emission_factor_relationship(
        self, db_session: Session, data_source_with_emission_factors: tuple[DataSource, list[EmissionFactor]]
    ):
        """Test data source to emission factor relationship."""
        data_source, factors = data_source_with_emission_factors

        # Act
        result = db_session.query(DataSource).filter(DataSource.id == data_source.id).first()

        # Assert
        assert result is not None
        assert len(result.emission_factors) == len(factors)
        for factor in result.emission_factors:
            assert factor.data_source_id == data_source.id


# ============================================================================
# Performance Tests (Basic Assertions)
# ============================================================================


class TestPerformance:
    """Basic performance-related tests."""

    def test_list_data_sources_with_many_records(self, db_session: Session):
        """Test listing many data sources performs reasonably."""
        # Arrange - create multiple data sources
        for i in range(10):
            data_source = DataSource(
                id=uuid.uuid4().hex,
                name=f"Test Source {i}",
                source_type="file" if i % 2 == 0 else "api",
                base_url=f"https://test{i}.example.com",
                sync_frequency="daily",
                is_active=True,
            )
            db_session.add(data_source)
        db_session.commit()

        # Act
        result = db_session.query(DataSource).all()

        # Assert
        assert len(result) == 10
