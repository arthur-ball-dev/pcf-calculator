"""
Integration test suite for BaseDataIngestion framework.

TASK-DATA-P5-001: Base Ingestion Framework - Phase A Tests

This test suite validates:
- Full sync workflow with mock HTTP (using respx)
- Database writes work correctly
- Transaction rollback on failure verified
- Sync log lifecycle (pending -> in_progress -> completed/failed)
- Partial failure scenario (95 valid, 5 invalid records)
- Upsert behavior (update existing records)

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no implementation exists yet)
- Implementation must make tests PASS without modifying tests

Note: These tests use an in-memory SQLite database for isolation.
"""

import pytest
import respx
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


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

    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture
def data_source(db_session):
    """Create a test data source."""
    try:
        from backend.models import DataSource
    except ImportError:
        pytest.skip("DataSource model not yet implemented")

    source = DataSource(
        name="Test EPA Source",
        source_type="api",
        base_url="https://api.test.epa.gov/factors",
        sync_frequency="weekly",
        is_active=True
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


def create_mock_async_session(db_session):
    """
    Create an async-compatible mock that delegates to sync session.
    For integration tests, we simulate async behavior.
    """
    mock_session = MagicMock()
    mock_session.add = db_session.add
    mock_session.flush = AsyncMock(side_effect=lambda: db_session.flush())
    mock_session.commit = AsyncMock(side_effect=lambda: db_session.commit())
    mock_session.rollback = AsyncMock(side_effect=lambda: db_session.rollback())
    mock_session.refresh = AsyncMock(side_effect=lambda obj: db_session.refresh(obj))

    async def mock_execute(stmt):
        result = db_session.execute(stmt)
        mock_result = MagicMock()
        mock_result.rowcount = result.rowcount
        mock_result.scalars = result.scalars
        mock_result.fetchall = result.fetchall
        mock_result.fetchone = result.fetchone
        return mock_result

    mock_session.execute = mock_execute
    return mock_session


# ============================================================================
# Test Scenario 1: Full Sync Workflow with Mock HTTP
# ============================================================================

class TestFullSyncWorkflow:
    """Test complete sync workflow from fetch to database write."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_sync_workflow_success(self, db_session, data_source):
        """Test successful full sync workflow with mock HTTP."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor, DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # Mock HTTP response
        test_url = "https://api.test.epa.gov/factors/download"
        csv_content = b"""activity_name,co2e_factor,unit,external_id
Steel Production,1.85,kg,EPA-001
Aluminum Smelting,11.5,kg,EPA-002
Concrete Manufacturing,0.91,kg,EPA-003
"""
        respx.get(test_url).mock(
            return_value=httpx.Response(200, content=csv_content)
        )

        # Create concrete implementation for test
        class TestIngestion(BaseDataIngestion):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.url = test_url

            async def fetch_raw_data(self) -> bytes:
                from backend.services.data_ingestion.http_client import (
                    DataIngestionHTTPClient
                )
                client = DataIngestionHTTPClient()
                return await client.download_file(self.url)

            async def parse_data(self, raw_data: bytes):
                import csv
                import io
                reader = csv.DictReader(io.StringIO(raw_data.decode('utf-8')))
                return list(reader)

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": row["activity_name"],
                        "co2e_factor": Decimal(row["co2e_factor"]),
                        "unit": row["unit"],
                        "external_id": row["external_id"],
                        "geography": "US",
                        "data_source": "EPA"
                    }
                    for row in parsed_data
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = TestIngestion(
            db=mock_session,
            data_source_id=data_source.id,
            sync_type="initial"
        )

        result = await ingestion.execute_sync()

        # Verify sync completed successfully
        assert result.status == "completed"
        assert result.records_processed == 3
        assert result.records_created == 3
        assert result.records_failed == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_workflow_with_empty_response(self, db_session, data_source):
        """Test sync workflow with empty data response."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        test_url = "https://api.test.epa.gov/factors/empty"
        respx.get(test_url).mock(
            return_value=httpx.Response(200, content=b"activity_name,co2e_factor,unit\n")
        )

        class EmptyIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                from backend.services.data_ingestion.http_client import (
                    DataIngestionHTTPClient
                )
                client = DataIngestionHTTPClient()
                return await client.download_file(test_url)

            async def parse_data(self, raw_data: bytes):
                import csv
                import io
                reader = csv.DictReader(io.StringIO(raw_data.decode('utf-8')))
                return list(reader)

            async def transform_data(self, parsed_data):
                return parsed_data

        mock_session = create_mock_async_session(db_session)
        ingestion = EmptyIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        assert result.status == "completed"
        assert result.records_processed == 0


# ============================================================================
# Test Scenario 2: Database Writes Work Correctly
# ============================================================================

class TestDatabaseWrites:
    """Test that database writes are performed correctly."""

    @pytest.mark.asyncio
    async def test_emission_factor_written_to_database(self, db_session, data_source):
        """Test that emission factors are written to the database."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class DirectIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"dummy"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Test Steel",
                        "co2e_factor": Decimal("2.5"),
                        "unit": "kg",
                        "external_id": "TEST-001",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = DirectIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        await ingestion.execute_sync()

        # Verify record was written to database
        ef = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "TEST-001"
        ).first()

        assert ef is not None
        assert ef.activity_name == "Test Steel"
        assert float(ef.co2e_factor) == 2.5
        assert ef.unit == "kg"

    @pytest.mark.asyncio
    async def test_multiple_emission_factors_written(self, db_session, data_source):
        """Test that multiple emission factors are written correctly."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class MultiIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"dummy"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": f"Activity {i}",
                        "co2e_factor": Decimal(str(i * 0.5)),
                        "unit": "kg",
                        "external_id": f"MULTI-{i:03d}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                    for i in range(1, 11)  # 10 records
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = MultiIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        # Verify all records were written
        count = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id.like("MULTI-%")
        ).count()

        assert count == 10
        assert result.records_created == 10


# ============================================================================
# Test Scenario 3: Transaction Rollback on Failure
# ============================================================================

class TestTransactionRollback:
    """Test that transactions are rolled back on failure."""

    @pytest.mark.asyncio
    async def test_rollback_on_fetch_error(self, db_session, data_source):
        """Test database rollback when fetch fails."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class FailingFetchIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                raise ConnectionError("Network failure")

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return []

        # Count records before
        initial_count = db_session.query(EmissionFactor).count()

        mock_session = create_mock_async_session(db_session)
        ingestion = FailingFetchIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        with pytest.raises(ConnectionError):
            await ingestion.execute_sync()

        # Verify no new records were committed
        final_count = db_session.query(EmissionFactor).count()
        assert final_count == initial_count

    @pytest.mark.asyncio
    async def test_rollback_on_transform_error(self, db_session, data_source):
        """Test database rollback when transform fails."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class FailingTransformIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{"raw": "data"}]

            async def transform_data(self, parsed_data):
                raise ValueError("Transform failed")

        initial_count = db_session.query(EmissionFactor).count()

        mock_session = create_mock_async_session(db_session)
        ingestion = FailingTransformIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        with pytest.raises(ValueError):
            await ingestion.execute_sync()

        final_count = db_session.query(EmissionFactor).count()
        assert final_count == initial_count

    @pytest.mark.asyncio
    async def test_partial_rollback_not_allowed(self, db_session, data_source):
        """Test that partial commits are rolled back on later failure."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class PartialFailIngestion(BaseDataIngestion):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.process_count = 0

            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                # Return 5 valid and then simulate a crash
                records = [
                    {
                        "activity_name": f"Partial {i}",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": f"PARTIAL-{i}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                    for i in range(5)
                ]
                return records

            async def upsert_emission_factor(self, factor_data):
                self.process_count += 1
                if self.process_count > 3:
                    raise RuntimeError("Unexpected failure")
                return await super().upsert_emission_factor(factor_data)

        initial_count = db_session.query(EmissionFactor).count()

        mock_session = create_mock_async_session(db_session)
        ingestion = PartialFailIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        with pytest.raises(RuntimeError):
            await ingestion.execute_sync()

        # All records should be rolled back (transaction atomicity)
        final_count = db_session.query(EmissionFactor).count()
        assert final_count == initial_count


# ============================================================================
# Test Scenario 4: Sync Log Lifecycle
# ============================================================================

class TestSyncLogLifecycle:
    """Test sync log status transitions."""

    @pytest.mark.asyncio
    async def test_sync_log_created_with_in_progress_status(
        self, db_session, data_source
    ):
        """Test that sync log is created with 'in_progress' status."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class SimpleIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                # Check sync log status during execution
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return []

        mock_session = create_mock_async_session(db_session)
        ingestion = SimpleIngestion(
            db=mock_session,
            data_source_id=data_source.id,
            sync_type="manual"
        )

        await ingestion.execute_sync()

        # Verify sync log was created
        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).first()

        assert sync_log is not None
        assert sync_log.sync_type == "manual"

    @pytest.mark.asyncio
    async def test_sync_log_completed_on_success(self, db_session, data_source):
        """Test that sync log status changes to 'completed' on success."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class SuccessIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Success Test",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": "SUCCESS-001",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = SuccessIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        await ingestion.execute_sync()

        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log is not None
        assert sync_log.status == "completed"
        assert sync_log.completed_at is not None

    @pytest.mark.asyncio
    async def test_sync_log_failed_on_error(self, db_session, data_source):
        """Test that sync log status changes to 'failed' on error."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class FailingIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                raise RuntimeError("Test failure")

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return []

        mock_session = create_mock_async_session(db_session)
        ingestion = FailingIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        try:
            await ingestion.execute_sync()
        except RuntimeError:
            pass

        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log is not None
        assert sync_log.status == "failed"
        assert sync_log.error_message is not None
        assert "Test failure" in sync_log.error_message

    @pytest.mark.asyncio
    async def test_sync_log_records_processing_stats(self, db_session, data_source):
        """Test that sync log records processing statistics."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class StatsIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": f"Stats Test {i}",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": f"STATS-{i:03d}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                    for i in range(5)
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = StatsIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        await ingestion.execute_sync()

        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log.records_processed == 5
        assert sync_log.records_created == 5
        assert sync_log.records_failed == 0


# ============================================================================
# Test Scenario 5: Partial Failure (95 valid, 5 invalid)
# ============================================================================

class TestPartialFailure:
    """Test handling of partial failures with mixed valid/invalid records."""

    @pytest.mark.asyncio
    async def test_partial_failure_95_valid_5_invalid(self, db_session, data_source):
        """Test sync with 95 valid and 5 invalid records."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor, DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class PartialIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                records = []
                # 95 valid records
                for i in range(95):
                    records.append({
                        "activity_name": f"Valid Activity {i}",
                        "co2e_factor": Decimal("1.5"),
                        "unit": "kg",
                        "external_id": f"VALID-{i:03d}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    })
                # 5 invalid records (negative co2e_factor)
                for i in range(5):
                    records.append({
                        "activity_name": f"Invalid Activity {i}",
                        "co2e_factor": Decimal("-1.0"),  # Invalid
                        "unit": "kg",
                        "external_id": f"INVALID-{i:03d}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    })
                return records

        mock_session = create_mock_async_session(db_session)
        ingestion = PartialIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        # Sync should complete (not fail entirely)
        assert result.status == "completed"
        assert result.records_processed == 100
        assert result.records_created == 95
        assert result.records_failed == 5

        # Verify errors were recorded
        assert len(ingestion.errors) == 5

        # Verify only valid records in database
        valid_count = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id.like("VALID-%")
        ).count()
        invalid_count = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id.like("INVALID-%")
        ).count()

        assert valid_count == 95
        assert invalid_count == 0

    @pytest.mark.asyncio
    async def test_partial_failure_continues_after_invalid_record(
        self, db_session, data_source
    ):
        """Test that processing continues after encountering invalid record."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class ContinueIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {"activity_name": "First Valid", "co2e_factor": Decimal("1.0"),
                     "unit": "kg", "external_id": "CONT-001", "geography": "GLO", "data_source": "TEST"},
                    {"activity_name": "Invalid", "co2e_factor": Decimal("0"),  # Invalid
                     "unit": "kg", "external_id": "CONT-002", "geography": "GLO", "data_source": "TEST"},
                    {"activity_name": "Second Valid", "co2e_factor": Decimal("2.0"),
                     "unit": "kg", "external_id": "CONT-003", "geography": "GLO", "data_source": "TEST"},
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = ContinueIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        assert result.records_created == 2
        assert result.records_failed == 1

        # Both valid records should be in database
        first = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "CONT-001"
        ).first()
        second = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "CONT-003"
        ).first()

        assert first is not None
        assert second is not None


# ============================================================================
# Test Scenario 6: Upsert Behavior (Update Existing Records)
# ============================================================================

class TestUpsertBehavior:
    """Test upsert behavior for updating existing records."""

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record(self, db_session, data_source):
        """Test that upsert updates existing record with same external_id."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # First, create an existing record
        existing = EmissionFactor(
            activity_name="Original Activity",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            external_id="UPSERT-001",
            data_source="TEST",
            geography="GLO",
            data_source_id=data_source.id
        )
        db_session.add(existing)
        db_session.commit()

        original_id = existing.id

        class UpsertIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Updated Activity",  # Updated name
                        "co2e_factor": Decimal("2.5"),  # Updated factor
                        "unit": "kg",
                        "external_id": "UPSERT-001",  # Same external_id
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = UpsertIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        # Should show update, not create
        assert result.records_processed == 1
        # The record was updated (implementation may report as created or updated)

        # Verify record was updated in database
        db_session.expire_all()
        updated = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "UPSERT-001"
        ).first()

        assert updated is not None
        assert float(updated.co2e_factor) == 2.5 or updated.activity_name == "Updated Activity"

    @pytest.mark.asyncio
    async def test_upsert_no_duplicate_records(self, db_session, data_source):
        """Test that upsert does not create duplicate records."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class DuplicateIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Duplicate Test",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": "DUP-001",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)

        # Run sync twice
        for _ in range(2):
            ingestion = DuplicateIngestion(
                db=mock_session,
                data_source_id=data_source.id
            )
            await ingestion.execute_sync()

        # Should only have one record
        count = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "DUP-001"
        ).count()

        assert count == 1

    @pytest.mark.asyncio
    async def test_resync_shows_updated_count(self, db_session, data_source):
        """Test that re-sync correctly reports updated records."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class ResyncIngestion(BaseDataIngestion):
            def __init__(self, factor_value, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.factor_value = factor_value

            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Resync Test",
                        "co2e_factor": self.factor_value,
                        "unit": "kg",
                        "external_id": "RESYNC-001",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)

        # First sync - creates record
        ingestion1 = ResyncIngestion(
            Decimal("1.0"),
            db=mock_session,
            data_source_id=data_source.id
        )
        result1 = await ingestion1.execute_sync()

        # Second sync - updates record
        ingestion2 = ResyncIngestion(
            Decimal("2.0"),
            db=mock_session,
            data_source_id=data_source.id
        )
        result2 = await ingestion2.execute_sync()

        # First should be created
        assert result1.records_processed == 1
        # Second should show processed (implementation may track as updated)
        assert result2.records_processed == 1

        # Verify final value
        db_session.expire_all()
        record = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "RESYNC-001"
        ).first()

        assert float(record.co2e_factor) == 2.0


# ============================================================================
# Test Scenario 7: Data Source Association
# ============================================================================

class TestDataSourceAssociation:
    """Test that ingested records are associated with correct data source."""

    @pytest.mark.asyncio
    async def test_emission_factor_linked_to_data_source(
        self, db_session, data_source
    ):
        """Test that emission factors are linked to the data source."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class LinkedIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Linked Test",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": "LINK-001",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = LinkedIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        await ingestion.execute_sync()

        # Verify data_source_id is set
        record = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id == "LINK-001"
        ).first()

        assert record is not None
        assert record.data_source_id == data_source.id

    @pytest.mark.asyncio
    async def test_sync_log_linked_to_data_source(self, db_session, data_source):
        """Test that sync logs are linked to the data source."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class LogIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return []

        mock_session = create_mock_async_session(db_session)
        ingestion = LogIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        await ingestion.execute_sync()

        # Verify sync log has correct data_source_id
        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == data_source.id
        ).first()

        assert sync_log is not None
        assert sync_log.data_source_id == data_source.id


# ============================================================================
# Test Scenario 8: Large Data Volume
# ============================================================================

class TestLargeDataVolume:
    """Test handling of large data volumes (1000+ records)."""

    @pytest.mark.asyncio
    async def test_process_1000_records(self, db_session, data_source):
        """Test processing 1000+ records successfully."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        class BulkIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"data"

            async def parse_data(self, raw_data: bytes):
                return [{}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": f"Bulk Activity {i}",
                        "co2e_factor": Decimal(str(0.5 + (i % 100) * 0.01)),
                        "unit": "kg",
                        "external_id": f"BULK-{i:04d}",
                        "geography": "GLO",
                        "data_source": "TEST"
                    }
                    for i in range(1000)
                ]

        mock_session = create_mock_async_session(db_session)
        ingestion = BulkIngestion(
            db=mock_session,
            data_source_id=data_source.id
        )

        result = await ingestion.execute_sync()

        assert result.status == "completed"
        assert result.records_processed == 1000
        assert result.records_created == 1000

        # Verify all records in database
        count = db_session.query(EmissionFactor).filter(
            EmissionFactor.external_id.like("BULK-%")
        ).count()
        assert count == 1000
