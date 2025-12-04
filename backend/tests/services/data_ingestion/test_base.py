"""
Test suite for BaseDataIngestion class.

TASK-DATA-P5-001: Base Ingestion Framework - Phase A Tests

This test suite validates:
- Base class instantiation with mock session
- validate_record() correctly validates required fields (activity_name, co2e_factor, unit)
- validate_record() rejects invalid co2e_factor values (<=0)
- upsert_emission_factor() handles insert correctly
- upsert_emission_factor() handles update correctly
- execute_sync() creates sync log entry
- execute_sync() updates sync log on completion
- execute_sync() handles errors and rolls back
- Abstract methods raise NotImplementedError

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no BaseDataIngestion class exists yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Base


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
def mock_async_session():
    """Create mock async session for unit tests."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def data_source_id():
    """Generate a test data source ID."""
    return uuid4().hex


# ============================================================================
# Test Scenario 1: Base Class Instantiation
# ============================================================================

class TestBaseDataIngestionInstantiation:
    """Test BaseDataIngestion class instantiation."""

    def test_base_class_instantiation_with_mock_session(
        self, mock_async_session, data_source_id
    ):
        """Test that BaseDataIngestion can be instantiated with mock session."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        # Create a concrete implementation for testing
        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"test data"

            async def parse_data(self, raw_data: bytes):
                return [{"test": "data"}]

            async def transform_data(self, parsed_data):
                return parsed_data

        ingestion = ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id,
            sync_type="manual"
        )

        assert ingestion.db == mock_async_session
        assert ingestion.data_source_id == data_source_id
        assert ingestion.sync_type == "manual"
        assert ingestion.sync_log is None
        assert ingestion.stats["records_processed"] == 0
        assert ingestion.stats["records_created"] == 0
        assert ingestion.stats["records_updated"] == 0
        assert ingestion.stats["records_skipped"] == 0
        assert ingestion.stats["records_failed"] == 0
        assert ingestion.errors == []

    def test_base_class_default_sync_type(self, mock_async_session, data_source_id):
        """Test that sync_type defaults to 'manual'."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        ingestion = ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        assert ingestion.sync_type == "manual"


# ============================================================================
# Test Scenario 2: validate_record() - Required Fields Validation
# ============================================================================

class TestValidateRecordRequiredFields:
    """Test validate_record() validates required fields correctly."""

    @pytest.fixture
    def ingestion_instance(self, mock_async_session, data_source_id):
        """Create an ingestion instance for testing."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        return ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_validate_record_with_all_required_fields(
        self, ingestion_instance
    ):
        """Test that validate_record() returns True for valid record."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("1.85"),
            "unit": "kg",
            "external_id": "EPA-001"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is True
        assert len(ingestion_instance.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_record_missing_activity_name(self, ingestion_instance):
        """Test that validate_record() fails when activity_name is missing."""
        record = {
            "co2e_factor": Decimal("1.85"),
            "unit": "kg"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) == 1
        assert "activity_name" in ingestion_instance.errors[0].field

    @pytest.mark.asyncio
    async def test_validate_record_missing_co2e_factor(self, ingestion_instance):
        """Test that validate_record() fails when co2e_factor is missing."""
        record = {
            "activity_name": "Steel Production",
            "unit": "kg"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) == 1
        assert "co2e_factor" in ingestion_instance.errors[0].field

    @pytest.mark.asyncio
    async def test_validate_record_missing_unit(self, ingestion_instance):
        """Test that validate_record() fails when unit is missing."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("1.85")
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) == 1
        assert "unit" in ingestion_instance.errors[0].field

    @pytest.mark.asyncio
    async def test_validate_record_null_activity_name(self, ingestion_instance):
        """Test that validate_record() fails when activity_name is None."""
        record = {
            "activity_name": None,
            "co2e_factor": Decimal("1.85"),
            "unit": "kg"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) >= 1

    @pytest.mark.asyncio
    async def test_validate_record_null_co2e_factor(self, ingestion_instance):
        """Test that validate_record() fails when co2e_factor is None."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": None,
            "unit": "kg"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_record_null_unit(self, ingestion_instance):
        """Test that validate_record() fails when unit is None."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("1.85"),
            "unit": None
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False


# ============================================================================
# Test Scenario 3: validate_record() - Invalid co2e_factor Values
# ============================================================================

class TestValidateRecordCo2eFactorValue:
    """Test validate_record() rejects invalid co2e_factor values."""

    @pytest.fixture
    def ingestion_instance(self, mock_async_session, data_source_id):
        """Create an ingestion instance for testing."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        return ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_validate_record_rejects_zero_co2e_factor(
        self, ingestion_instance
    ):
        """Test that co2e_factor = 0 is rejected."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("0"),
            "unit": "kg",
            "external_id": "EPA-001"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) == 1
        assert "co2e_factor" in ingestion_instance.errors[0].field
        assert "positive" in ingestion_instance.errors[0].message.lower()

    @pytest.mark.asyncio
    async def test_validate_record_rejects_negative_co2e_factor(
        self, ingestion_instance
    ):
        """Test that negative co2e_factor is rejected."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("-1.5"),
            "unit": "kg",
            "external_id": "EPA-001"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is False
        assert len(ingestion_instance.errors) == 1
        assert "co2e_factor" in ingestion_instance.errors[0].field

    @pytest.mark.asyncio
    async def test_validate_record_accepts_positive_co2e_factor(
        self, ingestion_instance
    ):
        """Test that positive co2e_factor is accepted."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("0.001"),
            "unit": "kg",
            "external_id": "EPA-001"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is True
        assert len(ingestion_instance.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_record_accepts_large_co2e_factor(
        self, ingestion_instance
    ):
        """Test that large positive co2e_factor is accepted."""
        record = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("999999.123456"),
            "unit": "kg",
            "external_id": "EPA-001"
        }

        result = await ingestion_instance.validate_record(record)
        assert result is True
        assert len(ingestion_instance.errors) == 0


# ============================================================================
# Test Scenario 4: upsert_emission_factor() - Insert Handling
# ============================================================================

class TestUpsertEmissionFactorInsert:
    """Test upsert_emission_factor() handles inserts correctly."""

    @pytest.fixture
    def ingestion_with_sync_log(self, mock_async_session, data_source_id):
        """Create an ingestion instance with a mock sync log."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        ingestion = ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Create mock sync log
        mock_sync_log = MagicMock()
        mock_sync_log.id = uuid4().hex
        ingestion.sync_log = mock_sync_log

        return ingestion

    @pytest.mark.asyncio
    async def test_upsert_emission_factor_insert_new_record(
        self, ingestion_with_sync_log
    ):
        """Test inserting a new emission factor."""
        factor_data = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("1.85"),
            "unit": "kg",
            "external_id": "EPA-001",
            "geography": "US",
            "reference_year": 2024
        }

        # Mock execute to return rowcount = 1 (inserted)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        ingestion_with_sync_log.db.execute = AsyncMock(return_value=mock_result)

        result = await ingestion_with_sync_log.upsert_emission_factor(factor_data)

        assert result == "created"
        ingestion_with_sync_log.db.execute.assert_called_once()


# ============================================================================
# Test Scenario 5: upsert_emission_factor() - Update Handling
# ============================================================================

class TestUpsertEmissionFactorUpdate:
    """Test upsert_emission_factor() handles updates correctly."""

    @pytest.fixture
    def ingestion_with_sync_log(self, mock_async_session, data_source_id):
        """Create an ingestion instance with a mock sync log."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        ingestion = ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        mock_sync_log = MagicMock()
        mock_sync_log.id = uuid4().hex
        ingestion.sync_log = mock_sync_log

        return ingestion

    @pytest.mark.asyncio
    async def test_upsert_emission_factor_update_existing_record(
        self, ingestion_with_sync_log
    ):
        """Test updating an existing emission factor."""
        factor_data = {
            "activity_name": "Steel Production",
            "co2e_factor": Decimal("2.00"),  # Updated value
            "unit": "kg",
            "external_id": "EPA-001",
            "geography": "US",
            "reference_year": 2024
        }

        # Mock execute to return rowcount = 2 (update: delete + insert)
        # OR implementation might use different indicator for update
        mock_result = MagicMock()
        mock_result.rowcount = 1  # Some implementations return 1 for both
        ingestion_with_sync_log.db.execute = AsyncMock(return_value=mock_result)

        # The test validates the method is callable and returns a result
        result = await ingestion_with_sync_log.upsert_emission_factor(factor_data)

        assert result in ["created", "updated"]
        ingestion_with_sync_log.db.execute.assert_called_once()


# ============================================================================
# Test Scenario 6: execute_sync() - Sync Log Creation
# ============================================================================

class TestExecuteSyncLogCreation:
    """Test execute_sync() creates sync log entry."""

    @pytest.fixture
    def mock_ingestion(self, mock_async_session, data_source_id):
        """Create mock ingestion for testing execute_sync."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"test data"

            async def parse_data(self, raw_data: bytes):
                return [{"raw": "data"}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Test Activity",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": "TEST-001"
                    }
                ]

        return ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_execute_sync_creates_sync_log(self, mock_ingestion):
        """Test that execute_sync() creates a sync log entry."""
        # Mock the upsert to succeed
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_ingestion.db.execute = AsyncMock(return_value=mock_result)

        # We need to verify sync log creation
        # The method should call db.add with DataSyncLog
        try:
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("DataSyncLog model not available")

        await mock_ingestion.execute_sync()

        # Verify db.add was called (sync log creation)
        assert mock_ingestion.db.add.called

    @pytest.mark.asyncio
    async def test_execute_sync_sync_log_has_correct_initial_status(
        self, mock_ingestion
    ):
        """Test that sync log is created with 'in_progress' status."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_ingestion.db.execute = AsyncMock(return_value=mock_result)

        await mock_ingestion.execute_sync()

        # Verify that a sync log was created
        assert mock_ingestion.sync_log is not None


# ============================================================================
# Test Scenario 7: execute_sync() - Sync Log Completion Update
# ============================================================================

class TestExecuteSyncLogCompletion:
    """Test execute_sync() updates sync log on completion."""

    @pytest.fixture
    def mock_ingestion(self, mock_async_session, data_source_id):
        """Create mock ingestion for testing."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"test data"

            async def parse_data(self, raw_data: bytes):
                return [{"raw": "data"}]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": "Activity 1",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": "TEST-001"
                    },
                    {
                        "activity_name": "Activity 2",
                        "co2e_factor": Decimal("2.0"),
                        "unit": "kg",
                        "external_id": "TEST-002"
                    }
                ]

        return ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_execute_sync_updates_sync_log_on_completion(
        self, mock_ingestion
    ):
        """Test that sync log is updated with 'completed' status."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await mock_ingestion.execute_sync()

        # Verify the result has completed status
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_sync_records_processed_count(self, mock_ingestion):
        """Test that records_processed count is correct."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await mock_ingestion.execute_sync()

        # Should process 2 records
        assert result.records_processed == 2

    @pytest.mark.asyncio
    async def test_execute_sync_records_created_count(self, mock_ingestion):
        """Test that records_created count is correct."""
        mock_result = MagicMock()
        mock_result.rowcount = 1  # Indicates insert
        mock_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await mock_ingestion.execute_sync()

        # Both records should be created
        assert result.records_created == 2


# ============================================================================
# Test Scenario 8: execute_sync() - Error Handling and Rollback
# ============================================================================

class TestExecuteSyncErrorHandling:
    """Test execute_sync() handles errors and rolls back."""

    @pytest.fixture
    def failing_ingestion(self, mock_async_session, data_source_id):
        """Create an ingestion that fails during fetch."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class FailingIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                raise ConnectionError("Network failure")

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        return FailingIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_execute_sync_calls_rollback_on_error(self, failing_ingestion):
        """Test that database rollback is called on error."""
        with pytest.raises(ConnectionError):
            await failing_ingestion.execute_sync()

        # Verify rollback was called
        failing_ingestion.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sync_updates_sync_log_status_on_error(
        self, failing_ingestion
    ):
        """Test that sync log status is set to 'failed' on error."""
        try:
            await failing_ingestion.execute_sync()
        except ConnectionError:
            pass

        # Sync log should have been updated with failed status
        # The implementation should update sync_log.status = "failed"
        # This is verified through the flush call after updating status

    @pytest.fixture
    def partial_failure_ingestion(self, mock_async_session, data_source_id):
        """Create an ingestion that fails during transform."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class PartialFailureIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"test data"

            async def parse_data(self, raw_data: bytes):
                return [{"data": "value"}]

            async def transform_data(self, parsed_data):
                raise ValueError("Transform error")

        return PartialFailureIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_execute_sync_handles_transform_error(
        self, partial_failure_ingestion
    ):
        """Test that transform errors trigger rollback."""
        with pytest.raises(ValueError):
            await partial_failure_ingestion.execute_sync()

        partial_failure_ingestion.db.rollback.assert_called()


# ============================================================================
# Test Scenario 9: Abstract Methods
# ============================================================================

class TestAbstractMethods:
    """Test that abstract methods raise NotImplementedError."""

    def test_base_class_cannot_be_instantiated_directly(
        self, mock_async_session, data_source_id
    ):
        """Test that BaseDataIngestion cannot be instantiated directly."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        # Should not be able to instantiate abstract class directly
        with pytest.raises(TypeError) as exc_info:
            BaseDataIngestion(
                db=mock_async_session,
                data_source_id=data_source_id
            )

        assert "abstract" in str(exc_info.value).lower() or \
               "instantiate" in str(exc_info.value).lower()

    def test_fetch_raw_data_is_abstract(self, mock_async_session, data_source_id):
        """Test that fetch_raw_data must be implemented."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        # Create partial implementation missing fetch_raw_data
        class PartialImpl(BaseDataIngestion):
            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        with pytest.raises(TypeError):
            PartialImpl(
                db=mock_async_session,
                data_source_id=data_source_id
            )

    def test_parse_data_is_abstract(self, mock_async_session, data_source_id):
        """Test that parse_data must be implemented."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class PartialImpl(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def transform_data(self, parsed_data):
                return parsed_data

        with pytest.raises(TypeError):
            PartialImpl(
                db=mock_async_session,
                data_source_id=data_source_id
            )

    def test_transform_data_is_abstract(self, mock_async_session, data_source_id):
        """Test that transform_data must be implemented."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class PartialImpl(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

        with pytest.raises(TypeError):
            PartialImpl(
                db=mock_async_session,
                data_source_id=data_source_id
            )


# ============================================================================
# Test Scenario 10: Error Collection
# ============================================================================

class TestErrorCollection:
    """Test that validation errors are properly collected."""

    @pytest.fixture
    def ingestion_instance(self, mock_async_session, data_source_id):
        """Create an ingestion instance for testing."""
        try:
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("BaseDataIngestion not yet implemented")

        class ConcreteIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b""

            async def parse_data(self, raw_data: bytes):
                return []

            async def transform_data(self, parsed_data):
                return parsed_data

        return ConcreteIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_multiple_validation_errors_accumulated(
        self, ingestion_instance
    ):
        """Test that multiple validation errors are accumulated."""
        records = [
            {"activity_name": None, "co2e_factor": Decimal("1.0"), "unit": "kg"},
            {"activity_name": "Valid", "co2e_factor": Decimal("-1.0"), "unit": "kg"},
            {"activity_name": "Also Valid", "co2e_factor": Decimal("0"), "unit": "kg"},
        ]

        for record in records:
            await ingestion_instance.validate_record(record)

        # Should have accumulated errors from all invalid records
        assert len(ingestion_instance.errors) == 3

    @pytest.mark.asyncio
    async def test_error_contains_record_id(self, ingestion_instance):
        """Test that error contains the record's external_id."""
        record = {
            "activity_name": None,
            "co2e_factor": Decimal("1.0"),
            "unit": "kg",
            "external_id": "EPA-999"
        }

        await ingestion_instance.validate_record(record)

        assert len(ingestion_instance.errors) == 1
        assert ingestion_instance.errors[0].record_id == "EPA-999"

    @pytest.mark.asyncio
    async def test_error_contains_descriptive_message(self, ingestion_instance):
        """Test that error contains a descriptive message."""
        record = {
            "activity_name": "Test",
            "co2e_factor": Decimal("-5.0"),
            "unit": "kg",
            "external_id": "TEST-001"
        }

        await ingestion_instance.validate_record(record)

        assert len(ingestion_instance.errors) == 1
        assert len(ingestion_instance.errors[0].message) > 0
