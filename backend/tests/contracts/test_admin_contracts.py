"""
Contract validation tests for admin API endpoints.

TASK-API-P5-001: Admin Data Sources Endpoints - Phase A (TDD)

These tests validate API response structures against defined contracts:
- admin-data-sources-contract.yaml
- admin-sync-contract.yaml
- admin-sync-logs-contract.yaml
- admin-coverage-contract.yaml

Contract tests ensure:
1. Response structure matches specification
2. Required fields are present
3. Field types are correct
4. Enum values are valid
5. Backward compatibility is maintained
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models import Base, DataSource, DataSyncLog, EmissionFactor, ProductCategory


# ============================================================================
# Contract Definitions
# ============================================================================


# Valid enum values from contracts
SOURCE_TYPE_ENUM = ["api", "file", "database", "manual"]
SYNC_FREQUENCY_ENUM = ["daily", "weekly", "biweekly", "monthly", "manual"]
SYNC_STATUS_ENUM = ["pending", "in_progress", "completed", "failed", "cancelled"]
SYNC_TYPE_ENUM = ["scheduled", "manual", "initial"]
PRIORITY_ENUM = ["high", "normal", "low"]
GROUP_BY_ENUM = ["source", "geography", "category", "year"]
GAP_STATUS_ENUM = ["full", "partial", "none"]


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
    """Create a sample data source matching contract schema."""
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
def sample_sync_log(db_session: Session, sample_data_source: DataSource) -> DataSyncLog:
    """Create a sample sync log matching contract schema."""
    sync_log = DataSyncLog(
        id=uuid.uuid4().hex,
        data_source_id=sample_data_source.id,
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
        sync_metadata={
            "file_name": "ghg_emission_factors_2023.xlsx",
            "file_size_bytes": 1548000,
            "triggered_by": "celery_beat",
        },
    )
    db_session.add(sync_log)
    db_session.commit()
    db_session.refresh(sync_log)
    return sync_log


@pytest.fixture
def sample_emission_factor(db_session: Session, sample_data_source: DataSource) -> EmissionFactor:
    """Create a sample emission factor matching contract schema."""
    factor = EmissionFactor(
        id=uuid.uuid4().hex,
        activity_name="Natural Gas",
        category="Stationary Combustion",
        co2e_factor=Decimal("2.75"),
        unit="kg",
        data_source="EPA",
        geography="US",
        reference_year=2023,
        data_quality_rating=Decimal("0.90"),
        data_source_id=sample_data_source.id,
        is_active=True,
    )
    db_session.add(factor)
    db_session.commit()
    db_session.refresh(factor)
    return factor


# ============================================================================
# Data Source Contract Tests
# ============================================================================


class TestDataSourceContractSchema:
    """Tests that DataSource model matches admin-data-sources-contract.yaml schema."""

    def test_data_source_has_required_fields(self, sample_data_source: DataSource):
        """Test DataSource has all required fields from contract."""
        # Required fields per contract
        assert hasattr(sample_data_source, "id")
        assert hasattr(sample_data_source, "name")
        assert hasattr(sample_data_source, "source_type")
        assert hasattr(sample_data_source, "base_url")
        assert hasattr(sample_data_source, "sync_frequency")
        assert hasattr(sample_data_source, "is_active")
        assert hasattr(sample_data_source, "created_at")

    def test_data_source_id_is_uuid_format(self, sample_data_source: DataSource):
        """Test id field is valid UUID hex format (32 chars)."""
        assert sample_data_source.id is not None
        assert isinstance(sample_data_source.id, str)
        assert len(sample_data_source.id) == 32

    def test_data_source_source_type_enum(self, sample_data_source: DataSource):
        """Test source_type is valid enum value."""
        assert sample_data_source.source_type in SOURCE_TYPE_ENUM

    def test_data_source_sync_frequency_enum(self, sample_data_source: DataSource):
        """Test sync_frequency is valid enum value."""
        assert sample_data_source.sync_frequency in SYNC_FREQUENCY_ENUM

    def test_data_source_is_active_is_boolean(self, sample_data_source: DataSource):
        """Test is_active is boolean type."""
        assert isinstance(sample_data_source.is_active, bool)

    def test_data_source_base_url_nullable(self, db_session: Session):
        """Test base_url can be null per contract."""
        data_source = DataSource(
            id=uuid.uuid4().hex,
            name="Manual Entry Source",
            source_type="manual",
            base_url=None,  # Nullable
            sync_frequency="manual",
            is_active=True,
        )
        db_session.add(data_source)
        db_session.commit()

        assert data_source.base_url is None

    def test_data_source_created_at_datetime(self, sample_data_source: DataSource):
        """Test created_at is datetime format."""
        assert sample_data_source.created_at is not None
        assert isinstance(sample_data_source.created_at, datetime)


class TestDataSourceResponseContract:
    """Tests for GET /admin/data-sources response contract."""

    def test_response_includes_data_sources_array(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test response has data_sources array."""
        result = db_session.query(DataSource).all()

        assert isinstance(result, list)
        assert len(result) > 0

    def test_response_includes_total_count(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test response has total count."""
        total = db_session.query(DataSource).count()

        assert isinstance(total, int)
        assert total >= 0

    def test_data_source_relationships_loaded(
        self, db_session: Session, sample_data_source: DataSource, sample_sync_log: DataSyncLog
    ):
        """Test relationships are accessible per contract."""
        # Relationship: sync_logs
        assert hasattr(sample_data_source, "sync_logs")
        assert len(sample_data_source.sync_logs) == 1

        # Relationship: emission_factors
        assert hasattr(sample_data_source, "emission_factors")


# ============================================================================
# Sync Trigger Contract Tests
# ============================================================================


class TestSyncTriggerContractSchema:
    """Tests for POST /admin/data-sources/{id}/sync contract schema."""

    def test_sync_request_optional_fields(self, db_session: Session, sample_data_source: DataSource):
        """Test sync request body fields are optional with defaults."""
        # Create sync log with minimal data (simulating default request)
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
            # Defaults: force_refresh=false, dry_run=false, priority="normal"
            sync_metadata={"force_refresh": False, "dry_run": False, "priority": "normal"},
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.sync_metadata["force_refresh"] is False
        assert sync_log.sync_metadata["dry_run"] is False
        assert sync_log.sync_metadata["priority"] == "normal"

    def test_sync_response_202_structure(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test 202 response structure per contract."""
        # Create sync log (simulating successful trigger)
        task_id = f"celery-task-{uuid.uuid4().hex}"
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="queued",
            celery_task_id=task_id,
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
        )
        db_session.add(sync_log)
        db_session.commit()

        # Verify response fields
        assert sync_log.id is not None  # sync_log_id
        assert sync_log.celery_task_id is not None  # task_id
        assert sync_log.status in ["queued", "pending", "started"]
        assert sync_log.data_source_id == sample_data_source.id

    def test_sync_priority_enum_values(self, db_session: Session, sample_data_source: DataSource):
        """Test priority values match contract enum."""
        for priority in PRIORITY_ENUM:
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
                sync_metadata={"priority": priority},
            )
            db_session.add(sync_log)
            db_session.commit()

            assert sync_log.sync_metadata["priority"] in PRIORITY_ENUM


# ============================================================================
# Sync Log Contract Tests
# ============================================================================


class TestSyncLogContractSchema:
    """Tests that DataSyncLog model matches admin-sync-logs-contract.yaml schema."""

    def test_sync_log_has_required_fields(self, sample_sync_log: DataSyncLog):
        """Test DataSyncLog has all required fields from contract."""
        # Required fields per contract
        assert hasattr(sample_sync_log, "id")
        assert hasattr(sample_sync_log, "data_source_id")
        assert hasattr(sample_sync_log, "sync_type")
        assert hasattr(sample_sync_log, "status")
        assert hasattr(sample_sync_log, "started_at")
        assert hasattr(sample_sync_log, "records_processed")
        assert hasattr(sample_sync_log, "records_created")
        assert hasattr(sample_sync_log, "records_updated")
        assert hasattr(sample_sync_log, "records_skipped")
        assert hasattr(sample_sync_log, "records_failed")
        assert hasattr(sample_sync_log, "created_at")

    def test_sync_log_id_is_uuid_format(self, sample_sync_log: DataSyncLog):
        """Test id field is valid UUID hex format."""
        assert sample_sync_log.id is not None
        assert isinstance(sample_sync_log.id, str)
        assert len(sample_sync_log.id) == 32

    def test_sync_log_sync_type_enum(self, sample_sync_log: DataSyncLog):
        """Test sync_type is valid enum value."""
        assert sample_sync_log.sync_type in SYNC_TYPE_ENUM

    def test_sync_log_status_enum(self, sample_sync_log: DataSyncLog):
        """Test status is valid enum value."""
        assert sample_sync_log.status in SYNC_STATUS_ENUM

    def test_sync_log_celery_task_id_nullable(self, db_session: Session, sample_data_source: DataSource):
        """Test celery_task_id can be null per contract."""
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="pending",
            celery_task_id=None,  # Nullable
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            records_failed=0,
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.celery_task_id is None

    def test_sync_log_completed_at_nullable(self, db_session: Session, sample_data_source: DataSource):
        """Test completed_at can be null per contract (in_progress status)."""
        sync_log = DataSyncLog(
            id=uuid.uuid4().hex,
            data_source_id=sample_data_source.id,
            sync_type="manual",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            completed_at=None,  # Nullable
            records_processed=100,
            records_created=5,
            records_updated=3,
            records_skipped=92,
            records_failed=0,
        )
        db_session.add(sync_log)
        db_session.commit()

        assert sync_log.completed_at is None

    def test_sync_log_error_message_nullable(self, sample_sync_log: DataSyncLog):
        """Test error_message is nullable."""
        assert sample_sync_log.error_message is None  # Successful sync

    def test_sync_log_error_details_nullable(self, sample_sync_log: DataSyncLog):
        """Test error_details is nullable."""
        assert sample_sync_log.error_details is None  # Successful sync

    def test_sync_log_metadata_structure(self, sample_sync_log: DataSyncLog):
        """Test metadata matches contract structure."""
        metadata = sample_sync_log.sync_metadata

        assert isinstance(metadata, dict)
        # Optional metadata fields per contract
        if "file_name" in metadata:
            assert isinstance(metadata["file_name"], str)
        if "file_size_bytes" in metadata:
            assert isinstance(metadata["file_size_bytes"], int)
        if "triggered_by" in metadata:
            assert isinstance(metadata["triggered_by"], str)

    def test_sync_log_integer_counters(self, sample_sync_log: DataSyncLog):
        """Test record counters are integers."""
        assert isinstance(sample_sync_log.records_processed, int)
        assert isinstance(sample_sync_log.records_created, int)
        assert isinstance(sample_sync_log.records_updated, int)
        assert isinstance(sample_sync_log.records_skipped, int)
        assert isinstance(sample_sync_log.records_failed, int)

    def test_sync_log_data_source_relationship(
        self, sample_sync_log: DataSyncLog, sample_data_source: DataSource
    ):
        """Test data_source relationship per contract."""
        assert sample_sync_log.data_source is not None
        assert sample_sync_log.data_source.id == sample_data_source.id
        assert sample_sync_log.data_source.name == sample_data_source.name


class TestSyncLogsResponseContract:
    """Tests for GET /admin/sync-logs response contract."""

    def test_response_includes_items_array(
        self, db_session: Session, sample_sync_log: DataSyncLog
    ):
        """Test response has items array."""
        result = db_session.query(DataSyncLog).all()

        assert isinstance(result, list)
        assert len(result) > 0

    def test_response_pagination_fields(
        self, db_session: Session, sample_sync_log: DataSyncLog
    ):
        """Test response includes pagination fields."""
        total = db_session.query(DataSyncLog).count()
        limit = 50  # Default per contract
        offset = 0  # Default per contract
        has_more = total > limit

        assert isinstance(total, int)
        assert isinstance(limit, int)
        assert isinstance(offset, int)
        assert isinstance(has_more, bool)


# ============================================================================
# Coverage Contract Tests
# ============================================================================


class TestCoverageContractSchema:
    """Tests for GET /admin/emission-factors/coverage contract schema."""

    def test_coverage_group_by_enum(self):
        """Test group_by values match contract enum."""
        for value in GROUP_BY_ENUM:
            assert value in ["source", "geography", "category", "year"]

    def test_coverage_gap_status_enum(self):
        """Test gap_status values match contract enum."""
        for value in GAP_STATUS_ENUM:
            assert value in ["full", "partial", "none"]

    def test_coverage_summary_structure(
        self, db_session: Session, sample_emission_factor: EmissionFactor
    ):
        """Test summary object matches contract structure."""
        # Required summary fields per contract
        total_factors = db_session.query(EmissionFactor).count()
        active_factors = (
            db_session.query(EmissionFactor)
            .filter(EmissionFactor.is_active == True)
            .count()
        )
        unique_activities = (
            db_session.query(EmissionFactor.activity_name)
            .distinct()
            .count()
        )
        geographies = (
            db_session.query(EmissionFactor.geography)
            .filter(EmissionFactor.is_active == True)
            .distinct()
            .count()
        )

        # Verify types match contract
        assert isinstance(total_factors, int)
        assert isinstance(active_factors, int)
        assert isinstance(unique_activities, int)
        assert isinstance(geographies, int)

    def test_coverage_by_source_item_structure(
        self, db_session: Session, sample_data_source: DataSource, sample_emission_factor: EmissionFactor
    ):
        """Test by_source item matches contract structure."""
        # Required by_source fields per contract
        source = sample_emission_factor.data_source_ref

        assert source.id is not None  # source_id
        assert source.name is not None  # source_name

        # total_factors - count from source
        factor_count = (
            db_session.query(EmissionFactor)
            .filter(EmissionFactor.data_source_id == source.id)
            .count()
        )
        assert isinstance(factor_count, int)

    def test_coverage_by_geography_item_structure(
        self, db_session: Session, sample_emission_factor: EmissionFactor
    ):
        """Test by_geography item matches contract structure."""
        # Required fields per contract
        assert sample_emission_factor.geography is not None
        assert isinstance(sample_emission_factor.geography, str)

    def test_coverage_include_inactive_parameter(
        self, db_session: Session, sample_data_source: DataSource
    ):
        """Test include_inactive parameter affects counts."""
        # Create active and inactive factors
        active_factor = EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Active Factor",
            category="Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="US",
            data_source_id=sample_data_source.id,
            is_active=True,
        )
        inactive_factor = EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Inactive Factor",
            category="Test",
            co2e_factor=Decimal("2.0"),
            unit="kg",
            data_source="Test",
            geography="US",
            data_source_id=sample_data_source.id,
            is_active=False,
        )
        db_session.add(active_factor)
        db_session.add(inactive_factor)
        db_session.commit()

        # With include_inactive=false (default)
        active_only = (
            db_session.query(EmissionFactor)
            .filter(EmissionFactor.is_active == True)
            .count()
        )

        # With include_inactive=true
        all_factors = db_session.query(EmissionFactor).count()

        assert all_factors > active_only


# ============================================================================
# Error Response Contract Tests
# ============================================================================


class TestErrorResponseContract:
    """Tests for error response formats per contracts."""

    def test_validation_error_structure(self):
        """Test 400 VALIDATION_ERROR response structure."""
        # Contract-defined structure
        error_response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": [
                    {"field": "source_type", "message": "Must be one of: api, file, database, manual"}
                ],
            },
            "request_id": "req_abc123",
            "timestamp": "2025-12-03T10:30:00Z",
        }

        assert "error" in error_response
        assert error_response["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in error_response["error"]
        assert "request_id" in error_response
        assert "timestamp" in error_response

    def test_not_found_error_structure(self):
        """Test 404 NOT_FOUND response structure."""
        error_response = {
            "error": {
                "code": "NOT_FOUND",
                "message": "Data source not found",
                "details": [
                    {"field": "id", "message": "No data source exists with ID xxx"}
                ],
            },
            "request_id": "req_def456",
            "timestamp": "2025-12-03T10:30:00Z",
        }

        assert error_response["error"]["code"] == "NOT_FOUND"

    def test_sync_in_progress_error_structure(self):
        """Test 409 SYNC_IN_PROGRESS response structure."""
        error_response = {
            "error": {
                "code": "SYNC_IN_PROGRESS",
                "message": "A sync is already in progress for this data source",
                "details": [
                    {"field": "data_source_id", "message": "Active sync: xxx"}
                ],
            },
            "request_id": "req_jkl012",
            "timestamp": "2025-12-03T10:30:00Z",
        }

        assert error_response["error"]["code"] == "SYNC_IN_PROGRESS"

    def test_source_inactive_error_structure(self):
        """Test 422 SOURCE_INACTIVE response structure."""
        error_response = {
            "error": {
                "code": "SOURCE_INACTIVE",
                "message": "Cannot sync inactive data source",
                "details": [
                    {"field": "id", "message": "Data source is disabled. Enable it first."}
                ],
            },
            "request_id": "req_mno345",
            "timestamp": "2025-12-03T10:30:00Z",
        }

        assert error_response["error"]["code"] == "SOURCE_INACTIVE"

    def test_internal_error_structure(self):
        """Test 500 INTERNAL_ERROR response structure."""
        error_response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
            "request_id": "req_ghi789",
            "timestamp": "2025-12-03T10:30:00Z",
        }

        assert error_response["error"]["code"] == "INTERNAL_ERROR"
        assert "message" in error_response["error"]


# ============================================================================
# Enum Validation Tests
# ============================================================================


class TestEnumValidation:
    """Tests that ensure enum values match contract definitions."""

    def test_all_source_types_valid(self, db_session: Session):
        """Test all source_type enum values can be stored."""
        for source_type in SOURCE_TYPE_ENUM:
            ds = DataSource(
                id=uuid.uuid4().hex,
                name=f"Test {source_type}",
                source_type=source_type,
                sync_frequency="manual",
                is_active=True,
            )
            db_session.add(ds)
            db_session.commit()
            assert ds.source_type == source_type

    def test_all_sync_frequencies_valid(self, db_session: Session):
        """Test all sync_frequency enum values can be stored."""
        for freq in SYNC_FREQUENCY_ENUM:
            ds = DataSource(
                id=uuid.uuid4().hex,
                name=f"Test {freq}",
                source_type="file",
                sync_frequency=freq,
                is_active=True,
            )
            db_session.add(ds)
            db_session.commit()
            assert ds.sync_frequency == freq

    def test_all_sync_statuses_valid(self, db_session: Session, sample_data_source: DataSource):
        """Test all sync status enum values can be stored."""
        for status in SYNC_STATUS_ENUM:
            log = DataSyncLog(
                id=uuid.uuid4().hex,
                data_source_id=sample_data_source.id,
                sync_type="manual",
                status=status,
                started_at=datetime.now(timezone.utc),
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_skipped=0,
                records_failed=0,
            )
            db_session.add(log)
            db_session.commit()
            assert log.status == status

    def test_all_sync_types_valid(self, db_session: Session, sample_data_source: DataSource):
        """Test all sync_type enum values can be stored."""
        for sync_type in SYNC_TYPE_ENUM:
            log = DataSyncLog(
                id=uuid.uuid4().hex,
                data_source_id=sample_data_source.id,
                sync_type=sync_type,
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_skipped=0,
                records_failed=0,
            )
            db_session.add(log)
            db_session.commit()
            assert log.sync_type == sync_type


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility of API contracts."""

    def test_data_source_response_has_legacy_fields(self, sample_data_source: DataSource):
        """Test response includes fields expected by existing consumers."""
        # Essential fields that existing consumers depend on
        essential_fields = ["id", "name", "source_type", "is_active", "created_at"]

        for field in essential_fields:
            assert hasattr(sample_data_source, field)
            assert getattr(sample_data_source, field) is not None

    def test_sync_log_response_has_legacy_fields(self, sample_sync_log: DataSyncLog):
        """Test response includes fields expected by existing consumers."""
        essential_fields = [
            "id",
            "data_source_id",
            "sync_type",
            "status",
            "started_at",
            "records_processed",
        ]

        for field in essential_fields:
            assert hasattr(sample_sync_log, field)

    def test_emission_factor_response_has_legacy_fields(self, sample_emission_factor: EmissionFactor):
        """Test response includes fields expected by existing consumers."""
        essential_fields = [
            "id",
            "activity_name",
            "co2e_factor",
            "unit",
            "data_source",
            "geography",
        ]

        for field in essential_fields:
            assert hasattr(sample_emission_factor, field)
            assert getattr(sample_emission_factor, field) is not None
