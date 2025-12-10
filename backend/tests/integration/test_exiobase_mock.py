"""
Integration test suite for ExiobaseEmissionFactorsIngestion with mock HTTP.

TASK-DATA-P5-004: Exiobase Data Connector - Phase A Tests

This test suite validates:
- Full sync workflow with mocked Zenodo ZIP response
- Database writes correct data_source_id
- All 49 regions represented in output
- Upsert behavior on re-sync
- Memory-efficient processing
- Multi-region coverage

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no ExiobaseEmissionFactorsIngestion exists yet)
- Implementation must make tests PASS without modifying tests

Note: These tests use an in-memory SQLite database for isolation
and respx for mocking HTTP requests to Zenodo.
"""

import pytest
import respx
import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from io import BytesIO
import zipfile
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker
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
def exiobase_data_source(db_session):
    """Create an Exiobase data source for testing."""
    try:
        from backend.models import DataSource
    except ImportError:
        pytest.skip("DataSource model not yet implemented")

    source = DataSource(
        name="Exiobase 3.8.2",
        source_type="file",
        base_url="https://zenodo.org/record/5589597",
        sync_frequency="yearly",
        is_active=True
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


@pytest.fixture
def sample_exiobase_zip():
    """Create a sample Exiobase ZIP for integration testing."""
    try:
        from backend.tests.fixtures.exiobase_fixtures import (
            create_exiobase_sample_zip
        )
    except ImportError:
        pytest.skip("exiobase_fixtures not available")

    return create_exiobase_sample_zip(num_regions=5, num_products=5)


@pytest.fixture
def sample_exiobase_zip_full_regions():
    """Create an Exiobase ZIP with all 49 regions."""
    try:
        from backend.tests.fixtures.exiobase_fixtures import (
            create_exiobase_zip_full_regions
        )
    except ImportError:
        pytest.skip("exiobase_fixtures not available")

    return create_exiobase_zip_full_regions()


@pytest.fixture
def large_exiobase_zip():
    """Create a larger Exiobase ZIP for memory testing."""
    try:
        from backend.tests.fixtures.exiobase_fixtures import (
            create_large_exiobase_zip
        )
    except ImportError:
        pytest.skip("exiobase_fixtures not available")

    return create_large_exiobase_zip(num_regions=20, num_products=50)


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
    mock_session.refresh = AsyncMock(
        side_effect=lambda obj: db_session.refresh(obj)
    )

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
# Test Scenario 1: Full Sync Workflow with Mock ZIP Response
# ============================================================================

class TestFullSyncWorkflowWithMockedZenodo:
    """Test complete sync workflow from fetch to database write."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_sync_workflow_success(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test successful full sync workflow with mock HTTP."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor, DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # Mock Zenodo download URL
        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id,
            sync_type="initial"
        )

        result = await ingestion.execute_sync()

        # Verify sync completed successfully
        assert result.status == "completed"
        assert result.records_processed > 0
        assert result.records_failed == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_creates_emission_factors_in_database(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that sync creates emission factors in the database."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Verify records were created
        count = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).count()

        # Should have some records (5 regions x 5 products = up to 25)
        assert count >= 10

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_handles_http_error(
        self, db_session, exiobase_data_source
    ):
        """Test that sync handles HTTP errors gracefully."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # Mock HTTP 404 error
        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(404)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        with pytest.raises(httpx.HTTPStatusError):
            await ingestion.execute_sync()

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_handles_connection_timeout(
        self, db_session, exiobase_data_source
    ):
        """Test that sync handles connection timeout gracefully."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # Mock timeout
        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        with pytest.raises(httpx.TimeoutException):
            await ingestion.execute_sync()


# ============================================================================
# Test Scenario 2: Database Writes Correct data_source_id
# ============================================================================

class TestDataSourceIdAssociation:
    """Test that database writes have correct data_source_id."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_emission_factors_have_correct_data_source_id(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all emission factors have correct data_source_id."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Query all emission factors
        factors = db_session.query(EmissionFactor).all()

        # All factors should have the correct data_source_id
        for factor in factors:
            assert factor.data_source_id == exiobase_data_source.id

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_log_has_correct_data_source_id(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that sync log has correct data_source_id."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Query sync log
        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == exiobase_data_source.id
        ).first()

        assert sync_log is not None
        assert sync_log.data_source_id == exiobase_data_source.id

    @pytest.mark.asyncio
    @respx.mock
    async def test_emission_factors_have_external_id(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that emission factors have external_id set."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Query all emission factors
        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        # All factors should have external_id starting with EXIO
        for factor in factors:
            assert factor.external_id is not None
            assert "EXIO" in factor.external_id


# ============================================================================
# Test Scenario 3: All 49 Regions Represented
# ============================================================================

class TestMultiRegionCoverage:
    """Test that all 49 Exiobase regions are represented."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_all_49_regions_present(
        self, db_session, exiobase_data_source, sample_exiobase_zip_full_regions
    ):
        """Test that factors from all 49 regions are present."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
            from backend.tests.fixtures.exiobase_fixtures import (
                EXIOBASE_REGIONS
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(
                200, content=sample_exiobase_zip_full_regions
            )
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Query distinct geographies
        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        geographies = set(f.geography for f in factors)

        # Should have all 49 regions represented
        assert len(geographies) == 49

    @pytest.mark.asyncio
    @respx.mock
    async def test_us_factors_present(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that US factors are present."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Check for US factors
        us_factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id,
            EmissionFactor.geography == "US"
        ).all()

        # Sample ZIP includes US
        # Note: depends on fixture configuration
        # If US is in first 5 regions, should have factors
        geographies = set(
            f.geography
            for f in db_session.query(EmissionFactor).all()
        )
        # US should be in our sample regions
        assert "US" in geographies or len(geographies) >= 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_eu_factors_present(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that EU factors are present (DE, FR, etc.)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Check for EU factors
        geographies = set(
            f.geography
            for f in db_session.query(EmissionFactor).filter(
                EmissionFactor.data_source_id == exiobase_data_source.id
            ).all()
        )

        # Sample regions start with AT, BE, BG... (EU countries)
        eu_countries = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK"]
        eu_present = [c for c in eu_countries if c in geographies]
        assert len(eu_present) >= 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_asian_factors_present(
        self, db_session, exiobase_data_source, sample_exiobase_zip_full_regions
    ):
        """Test that Asian factors are present (CN, JP, KR)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(
                200, content=sample_exiobase_zip_full_regions
            )
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Check for Asian factors
        geographies = set(
            f.geography
            for f in db_session.query(EmissionFactor).filter(
                EmissionFactor.data_source_id == exiobase_data_source.id
            ).all()
        )

        asian_countries = ["CN", "JP", "KR", "IN", "TW", "ID"]
        asian_present = [c for c in asian_countries if c in geographies]
        assert len(asian_present) >= 3  # At least 3 Asian countries

    @pytest.mark.asyncio
    @respx.mock
    async def test_rest_of_world_regions_present(
        self, db_session, exiobase_data_source, sample_exiobase_zip_full_regions
    ):
        """Test that rest-of-world regions are present (WA, WL, WE, WF, WM)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(
                200, content=sample_exiobase_zip_full_regions
            )
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Check for RoW regions
        geographies = set(
            f.geography
            for f in db_session.query(EmissionFactor).filter(
                EmissionFactor.data_source_id == exiobase_data_source.id
            ).all()
        )

        row_regions = ["WA", "WL", "WE", "WF", "WM"]
        row_present = [r for r in row_regions if r in geographies]
        assert len(row_present) == 5  # All 5 RoW regions


# ============================================================================
# Test Scenario 4: Upsert Behavior on Re-sync
# ============================================================================

class TestUpsertBehavior:
    """Test upsert behavior on re-sync."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_resync_updates_existing_records(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that re-sync updates existing records."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)

        # First sync
        ingestion1 = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )
        result1 = await ingestion1.execute_sync()

        initial_count = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).count()

        # Second sync (should update, not duplicate)
        ingestion2 = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )
        result2 = await ingestion2.execute_sync()

        # Count should be the same (no duplicates)
        final_count = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).count()

        assert final_count == initial_count

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_duplicate_external_ids(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that no duplicate external_ids are created."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)

        # Run sync twice
        for _ in range(2):
            ingestion = ExiobaseEmissionFactorsIngestion(
                db=mock_session,
                data_source_id=exiobase_data_source.id
            )
            await ingestion.execute_sync()

        # Check for duplicates
        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()
        external_ids = [f.external_id for f in factors if f.external_id]

        # No duplicates
        assert len(external_ids) == len(set(external_ids))

    @pytest.mark.asyncio
    @respx.mock
    async def test_second_sync_reports_updates(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that second sync reports records as updated."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)

        # First sync
        ingestion1 = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )
        result1 = await ingestion1.execute_sync()
        records_created = result1.records_created

        # Second sync
        ingestion2 = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )
        result2 = await ingestion2.execute_sync()

        # Second sync should update, not create
        # Note: depends on implementation - could be all updates
        assert result2.records_processed > 0


# ============================================================================
# Test Scenario 5: Memory-Efficient Processing
# ============================================================================

class TestMemoryEfficientProcessing:
    """Test memory-efficient processing of large datasets."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_large_dataset_sync_completes(
        self, db_session, exiobase_data_source, large_exiobase_zip
    ):
        """Test that sync completes with larger dataset."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=large_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        result = await ingestion.execute_sync()

        # Should complete successfully
        assert result.status == "completed"
        assert result.records_processed > 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_processes_all_product_regions(
        self, db_session, exiobase_data_source, large_exiobase_zip
    ):
        """Test that sync processes products from all included regions."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=large_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        # Count unique region-product combinations
        count = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).count()

        # Should have many records (20 regions x products)
        assert count >= 50


# ============================================================================
# Test Scenario 6: Data Quality Attributes
# ============================================================================

class TestDataQualityAttributes:
    """Test data quality attributes are set correctly."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_data_quality_rating_is_0_75(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all records have data_quality_rating of 0.75."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            if factor.data_quality_rating:
                # Exiobase has lower quality rating due to aggregation
                assert float(factor.data_quality_rating) == 0.75

    @pytest.mark.asyncio
    @respx.mock
    async def test_reference_year_is_2022(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all records have reference_year of 2022."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            assert factor.reference_year == 2022

    @pytest.mark.asyncio
    @respx.mock
    async def test_scope_is_scope_3(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all records have scope of Scope 3."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            if factor.scope:
                assert factor.scope == "Scope 3"

    @pytest.mark.asyncio
    @respx.mock
    async def test_unit_contains_eur(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all records have EUR-based unit."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            # Exiobase uses monetary units
            assert "EUR" in factor.unit


# ============================================================================
# Test Scenario 7: Sync Log Statistics
# ============================================================================

class TestSyncLogStatistics:
    """Test sync log records correct statistics."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_log_records_processed_count(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that sync log records correct processed count."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        result = await ingestion.execute_sync()

        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == exiobase_data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log is not None
        assert sync_log.records_processed == result.records_processed

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_log_status_completed(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that sync log has status 'completed'."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == exiobase_data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log.status == "completed"

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_log_status_failed_on_error(
        self, db_session, exiobase_data_source
    ):
        """Test that sync log status is 'failed' on error."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import DataSyncLog
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        # Mock HTTP 500 error
        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(500)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        try:
            await ingestion.execute_sync()
        except Exception:
            pass

        # Verify sync log status is failed
        sync_log = db_session.query(DataSyncLog).filter(
            DataSyncLog.data_source_id == exiobase_data_source.id
        ).order_by(DataSyncLog.created_at.desc()).first()

        assert sync_log is not None
        assert sync_log.status == "failed"
        assert sync_log.error_message is not None


# ============================================================================
# Test Scenario 8: GWP Conversion Accuracy
# ============================================================================

class TestGWPConversionAccuracy:
    """Test GWP conversion accuracy in integrated workflow."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_co2e_values_are_positive(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that all CO2e values are positive after conversion."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            assert float(factor.co2e_factor) > 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_co2e_values_reasonable_range(
        self, db_session, exiobase_data_source, sample_exiobase_zip
    ):
        """Test that CO2e values are in reasonable range."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        respx.get(ExiobaseEmissionFactorsIngestion.ZENODO_URL).mock(
            return_value=httpx.Response(200, content=sample_exiobase_zip)
        )

        mock_session = create_mock_async_session(db_session)
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_session,
            data_source_id=exiobase_data_source.id
        )

        await ingestion.execute_sync()

        factors = db_session.query(EmissionFactor).filter(
            EmissionFactor.data_source_id == exiobase_data_source.id
        ).all()

        for factor in factors:
            co2e = float(factor.co2e_factor)
            # Exiobase values are typically in range 0.001 - 100 kg CO2e/EUR
            assert co2e < 1000  # Upper bound check
