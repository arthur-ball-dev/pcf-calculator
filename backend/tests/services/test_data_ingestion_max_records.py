"""
Test suite for BaseDataIngestion.execute_sync() max_records parameter.

TASK-DATA-P7-005: Add max_records Parameter to BaseDataIngestion

This test suite validates:
- max_records=N limits processing to N records
- max_records=None processes all records (default)
- max_records=0 processes all records
- Negative max_records processes all records
- max_records > total processes all available records
- max_records=1 processes exactly one record
- Backward compatibility (no argument processes all)

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (execute_sync() does not accept max_records)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession


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
# Test Scenario 11: execute_sync() - max_records Parameter
# TASK-DATA-P7-005: Add max_records Parameter to BaseDataIngestion
# ============================================================================

class TestExecuteSyncMaxRecords:
    """Test execute_sync() max_records parameter behavior.

    TASK-DATA-P7-005: Tests for limiting the number of records processed
    during a sync operation for smoke testing and development purposes.
    """

    @pytest.fixture
    def multi_record_ingestion(self, mock_async_session, data_source_id):
        """Create ingestion that returns 10 records."""
        from backend.services.data_ingestion.base import BaseDataIngestion

        class MultiRecordIngestion(BaseDataIngestion):
            async def fetch_raw_data(self) -> bytes:
                return b"test data"

            async def parse_data(self, raw_data: bytes):
                return [{"id": i} for i in range(10)]

            async def transform_data(self, parsed_data):
                return [
                    {
                        "activity_name": f"Activity {i}",
                        "co2e_factor": Decimal("1.0"),
                        "unit": "kg",
                        "external_id": f"TEST-{i:03d}"
                    }
                    for i in range(10)
                ]

        return MultiRecordIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_limits_processing(
        self, multi_record_ingestion
    ):
        """Test that max_records=5 processes only 5 records."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=5)

        assert result.records_processed == 5
        assert result.records_created == 5

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_none_processes_all(
        self, multi_record_ingestion
    ):
        """Test that max_records=None processes all records (default)."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=None)

        assert result.records_processed == 10

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_zero_processes_all(
        self, multi_record_ingestion
    ):
        """Test that max_records=0 processes all records."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=0)

        assert result.records_processed == 10

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_negative_processes_all(
        self, multi_record_ingestion
    ):
        """Test that negative max_records processes all records."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=-5)

        assert result.records_processed == 10

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_exceeds_total(
        self, multi_record_ingestion
    ):
        """Test that max_records > total processes all available records."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=100)

        assert result.records_processed == 10  # Only 10 available

    @pytest.mark.asyncio
    async def test_execute_sync_max_records_one(
        self, multi_record_ingestion
    ):
        """Test that max_records=1 processes exactly one record."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync(max_records=1)

        assert result.records_processed == 1
        assert result.records_created == 1

    @pytest.mark.asyncio
    async def test_execute_sync_default_no_argument_processes_all(
        self, multi_record_ingestion
    ):
        """Test that calling without argument processes all (backward compat)."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        multi_record_ingestion.db.execute = AsyncMock(return_value=mock_result)

        result = await multi_record_ingestion.execute_sync()

        assert result.records_processed == 10
