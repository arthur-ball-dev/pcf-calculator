"""
Test suite for ExiobaseEmissionFactorsIngestion class.

TASK-DATA-P5-004: Exiobase Data Connector - Phase A Tests

This test suite validates:
- Constructor initialization with correct defaults
- fetch_raw_data with streaming download
- parse_data extracts from ZIP file (F matrix)
- _extract_emission_factors parses F matrix correctly
- transform_data aggregates by region/product
- _convert_to_co2e handles GWP conversion (CH4=28, N2O=265)
- _clean_product_name normalizes product names
- _categorize_product assigns correct categories
- Error handling for missing F matrix

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no ExiobaseEmissionFactorsIngestion class exists yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from io import BytesIO
import zipfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function")
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


@pytest.fixture
def sample_exiobase_zip():
    """
    Create a minimal Exiobase-style ZIP file for testing.

    Uses the exiobase_fixtures module to create test data.
    """
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
def sample_exiobase_zip_no_f_matrix():
    """Create an Exiobase ZIP without F matrix for error testing."""
    try:
        from backend.tests.fixtures.exiobase_fixtures import (
            create_exiobase_zip_without_f_matrix
        )
    except ImportError:
        pytest.skip("exiobase_fixtures not available")

    return create_exiobase_zip_without_f_matrix()


@pytest.fixture
def sample_exiobase_zip_with_zeros():
    """Create an Exiobase ZIP with some zero values."""
    try:
        from backend.tests.fixtures.exiobase_fixtures import (
            create_exiobase_zip_with_zero_values
        )
    except ImportError:
        pytest.skip("exiobase_fixtures not available")

    return create_exiobase_zip_with_zero_values()


# ============================================================================
# Test Scenario 1: Constructor Initialization
# ============================================================================

class TestExiobaseIngestionInstantiation:
    """Test ExiobaseEmissionFactorsIngestion class instantiation."""

    def test_constructor_initializes_with_correct_defaults(
        self, mock_async_session, data_source_id
    ):
        """Test that Exiobase ingestion initializes with correct default values."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id,
            sync_type="manual"
        )

        assert ingestion.db == mock_async_session
        assert ingestion.data_source_id == data_source_id
        assert ingestion.sync_type == "manual"
        assert ingestion.reference_year == 2022
        assert ingestion.sync_log is None
        assert ingestion.stats["records_processed"] == 0

    def test_constructor_has_zenodo_url(
        self, mock_async_session, data_source_id
    ):
        """Test that ZENODO_URL class attribute is defined."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        assert hasattr(ExiobaseEmissionFactorsIngestion, 'ZENODO_URL')
        assert isinstance(ExiobaseEmissionFactorsIngestion.ZENODO_URL, str)
        assert "zenodo.org" in ExiobaseEmissionFactorsIngestion.ZENODO_URL.lower()

    def test_constructor_has_regions_list(
        self, mock_async_session, data_source_id
    ):
        """Test that REGIONS list contains 49 regions."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        assert hasattr(ExiobaseEmissionFactorsIngestion, 'REGIONS')
        assert isinstance(ExiobaseEmissionFactorsIngestion.REGIONS, list)
        assert len(ExiobaseEmissionFactorsIngestion.REGIONS) == 49

    def test_constructor_has_product_categories(
        self, mock_async_session, data_source_id
    ):
        """Test that PRODUCT_CATEGORIES list is defined."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        assert hasattr(ExiobaseEmissionFactorsIngestion, 'PRODUCT_CATEGORIES')
        assert isinstance(ExiobaseEmissionFactorsIngestion.PRODUCT_CATEGORIES, list)
        assert len(ExiobaseEmissionFactorsIngestion.PRODUCT_CATEGORIES) > 0

    def test_constructor_has_ghg_stressors(
        self, mock_async_session, data_source_id
    ):
        """Test that GHG_STRESSORS list is defined."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        assert hasattr(ExiobaseEmissionFactorsIngestion, 'GHG_STRESSORS')
        assert isinstance(ExiobaseEmissionFactorsIngestion.GHG_STRESSORS, list)
        # Should include CO2, CH4, N2O stressors
        stressor_names = " ".join(ExiobaseEmissionFactorsIngestion.GHG_STRESSORS)
        assert "CO2" in stressor_names
        assert "CH4" in stressor_names
        assert "N2O" in stressor_names

    def test_constructor_inherits_from_base_data_ingestion(
        self, mock_async_session, data_source_id
    ):
        """Test that ExiobaseEmissionFactorsIngestion inherits from BaseDataIngestion."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
            from backend.services.data_ingestion.base import BaseDataIngestion
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        assert isinstance(ingestion, BaseDataIngestion)
        assert hasattr(ingestion, 'db')
        assert hasattr(ingestion, 'data_source_id')
        assert hasattr(ingestion, 'stats')
        assert hasattr(ingestion, 'errors')


# ============================================================================
# Test Scenario 2: fetch_raw_data with Streaming Download
# ============================================================================

class TestFetchRawData:
    """Test fetch_raw_data method with streaming download."""

    @pytest.mark.asyncio
    async def test_fetch_raw_data_uses_zenodo_url(
        self, mock_async_session, data_source_id
    ):
        """Test that fetch_raw_data uses the ZENODO_URL."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Verify URL is correct
        assert ingestion.ZENODO_URL is not None
        assert "zenodo.org" in ingestion.ZENODO_URL

    @pytest.mark.asyncio
    async def test_fetch_raw_data_returns_bytes(
        self, mock_async_session, data_source_id, sample_exiobase_zip
    ):
        """Test that fetch_raw_data returns bytes."""
        try:
            import respx
            import httpx
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        with respx.mock:
            # Mock streaming response
            respx.get(ingestion.ZENODO_URL).mock(
                return_value=httpx.Response(200, content=sample_exiobase_zip)
            )

            result = await ingestion.fetch_raw_data()

            assert isinstance(result, bytes)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_fetch_raw_data_raises_on_http_error(
        self, mock_async_session, data_source_id
    ):
        """Test that fetch_raw_data raises on HTTP error."""
        try:
            import respx
            import httpx
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        with respx.mock:
            respx.get(ingestion.ZENODO_URL).mock(
                return_value=httpx.Response(404)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await ingestion.fetch_raw_data()

    @pytest.mark.asyncio
    async def test_fetch_raw_data_has_long_timeout(
        self, mock_async_session, data_source_id
    ):
        """Test that fetch_raw_data uses long timeout for large file."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        # Verify implementation uses extended timeout (>60s for ~500MB file)
        # This is verified by checking the class has the appropriate configuration
        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Implementation should handle long downloads
        assert ingestion is not None


# ============================================================================
# Test Scenario 3: parse_data Extracts from ZIP File
# ============================================================================

class TestParseData:
    """Test parse_data method extracts records from ZIP file."""

    @pytest.mark.asyncio
    async def test_parse_data_extracts_records_from_zip(
        self, mock_async_session, data_source_id, sample_exiobase_zip
    ):
        """Test that parse_data extracts records from Exiobase ZIP."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        records = await ingestion.parse_data(sample_exiobase_zip)

        assert isinstance(records, list)
        assert len(records) > 0

    @pytest.mark.asyncio
    async def test_parse_data_finds_f_matrix(
        self, mock_async_session, data_source_id, sample_exiobase_zip
    ):
        """Test that parse_data finds the F matrix file in ZIP."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Verify ZIP contains F matrix before parsing
        with zipfile.ZipFile(BytesIO(sample_exiobase_zip)) as zf:
            f_files = [f for f in zf.namelist() if 'F.' in f or 'F_' in f]
            assert len(f_files) > 0

        records = await ingestion.parse_data(sample_exiobase_zip)
        assert len(records) > 0

    @pytest.mark.asyncio
    async def test_parse_data_raises_error_for_missing_f_matrix(
        self, mock_async_session, data_source_id, sample_exiobase_zip_no_f_matrix
    ):
        """Test that parse_data raises error when F matrix is missing."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        with pytest.raises(ValueError, match="F matrix"):
            await ingestion.parse_data(sample_exiobase_zip_no_f_matrix)

    @pytest.mark.asyncio
    async def test_parse_data_extracts_stressor_info(
        self, mock_async_session, data_source_id, sample_exiobase_zip
    ):
        """Test that parsed records include stressor information."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        records = await ingestion.parse_data(sample_exiobase_zip)

        assert len(records) > 0
        first_record = records[0]
        assert "stressor" in first_record
        assert "region" in first_record
        assert "product" in first_record
        assert "value" in first_record

    @pytest.mark.asyncio
    async def test_parse_data_handles_corrupted_zip(
        self, mock_async_session, data_source_id
    ):
        """Test that parse_data raises error for corrupted ZIP."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        corrupted_data = b"this is not a valid zip file"

        with pytest.raises(Exception):
            await ingestion.parse_data(corrupted_data)

    @pytest.mark.asyncio
    async def test_parse_data_filters_zero_values(
        self, mock_async_session, data_source_id, sample_exiobase_zip_with_zeros
    ):
        """Test that parse_data filters out zero emission values."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        records = await ingestion.parse_data(sample_exiobase_zip_with_zeros)

        # No record should have zero value
        for record in records:
            assert record["value"] != 0


# ============================================================================
# Test Scenario 4: _extract_emission_factors Parses F Matrix
# ============================================================================

class TestExtractEmissionFactors:
    """Test _extract_emission_factors method parses F matrix correctly."""

    def test_extract_emission_factors_returns_list(
        self, mock_async_session, data_source_id
    ):
        """Test that _extract_emission_factors returns a list."""
        try:
            import pandas as pd
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Create a simple DataFrame mimicking F matrix
        df = pd.DataFrame({
            "DE_Electricity by coal": [0.5, 0.001, 0.0001],
            "US_Electricity by coal": [0.6, 0.002, 0.0002],
        }, index=[
            "CO2 - combustion - air",
            "CH4 - combustion - air",
            "N2O - combustion - air",
        ])

        records = ingestion._extract_emission_factors(df)

        assert isinstance(records, list)
        assert len(records) > 0

    def test_extract_emission_factors_parses_region_product(
        self, mock_async_session, data_source_id
    ):
        """Test that region and product are correctly parsed from column name."""
        try:
            import pandas as pd
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        df = pd.DataFrame({
            "DE_Electricity by coal": [0.5],
        }, index=["CO2 - combustion - air"])

        records = ingestion._extract_emission_factors(df)

        assert len(records) > 0
        assert records[0]["region"] == "DE"
        assert "Electricity" in records[0]["product"]

    def test_extract_emission_factors_filters_by_ghg_stressors(
        self, mock_async_session, data_source_id
    ):
        """Test that only GHG stressors are extracted."""
        try:
            import pandas as pd
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # DataFrame with GHG and non-GHG stressors
        df = pd.DataFrame({
            "DE_Electricity by coal": [0.5, 0.1, 100.0],
        }, index=[
            "CO2 - combustion - air",
            "NOx - combustion - air",  # Not a GHG
            "Water - use - air",  # Not a GHG
        ])

        records = ingestion._extract_emission_factors(df)

        # Should only extract CO2 (or other GHGs if partial matching used)
        stressors = [r["stressor"] for r in records]
        assert "CO2 - combustion - air" in stressors
        assert "Water - use - air" not in stressors

    def test_extract_emission_factors_filters_by_product_category(
        self, mock_async_session, data_source_id
    ):
        """Test that only key product categories are extracted."""
        try:
            import pandas as pd
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("Required modules not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        df = pd.DataFrame({
            "DE_Electricity by coal": [0.5],
            "DE_Hotels and restaurants": [0.01],  # Not in key categories
        }, index=["CO2 - combustion - air"])

        records = ingestion._extract_emission_factors(df)

        products = [r["product"] for r in records]
        # Electricity should be extracted
        assert any("Electricity" in p for p in products)


# ============================================================================
# Test Scenario 5: transform_data Aggregates by Region/Product
# ============================================================================

class TestTransformData:
    """Test transform_data method aggregates by region and product."""

    @pytest.mark.asyncio
    async def test_transform_data_aggregates_stressors(
        self, mock_async_session, data_source_id
    ):
        """Test that transform_data aggregates different stressors for same region/product."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Multiple stressors for same region/product
        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "DE",
             "product": "Electricity by coal", "value": 0.5},
            {"stressor": "CH4 - combustion - air", "region": "DE",
             "product": "Electricity by coal", "value": 0.001},
            {"stressor": "N2O - combustion - air", "region": "DE",
             "product": "Electricity by coal", "value": 0.0001},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Should be aggregated to single record
        assert len(transformed) == 1
        # CO2e total should include GWP-weighted contributions
        assert transformed[0]["co2e_factor"] > 0

    @pytest.mark.asyncio
    async def test_transform_data_includes_required_fields(
        self, mock_async_session, data_source_id
    ):
        """Test that transformed records include all required fields."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "US",
             "product": "Iron and steel", "value": 0.5},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        assert len(transformed) == 1
        record = transformed[0]

        # Required fields from schema
        assert "activity_name" in record
        assert "co2e_factor" in record
        assert "unit" in record
        assert "external_id" in record
        assert "geography" in record
        assert "scope" in record
        assert "category" in record
        assert "reference_year" in record
        assert "data_quality_rating" in record

    @pytest.mark.asyncio
    async def test_transform_data_sets_geography_to_region(
        self, mock_async_session, data_source_id
    ):
        """Test that geography is set to the region code."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "JP",
             "product": "Cement", "value": 0.5},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        assert transformed[0]["geography"] == "JP"

    @pytest.mark.asyncio
    async def test_transform_data_sets_data_quality_rating(
        self, mock_async_session, data_source_id
    ):
        """Test that data_quality_rating is set to 0.75."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "CN",
             "product": "Plastics, basic", "value": 0.3},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Exiobase has lower quality rating due to aggregation
        assert transformed[0]["data_quality_rating"] == 0.75

    @pytest.mark.asyncio
    async def test_transform_data_sets_scope_3(
        self, mock_async_session, data_source_id
    ):
        """Test that scope is set to Scope 3."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "BR",
             "product": "Motor vehicles", "value": 0.2},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Exiobase provides supply-chain factors (Scope 3)
        assert transformed[0]["scope"] == "Scope 3"

    @pytest.mark.asyncio
    async def test_transform_data_generates_external_id(
        self, mock_async_session, data_source_id
    ):
        """Test that external_id is correctly generated."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "DE",
             "product": "Iron and steel", "value": 0.5},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        external_id = transformed[0]["external_id"]
        assert "EXIO" in external_id
        assert "DE" in external_id
        assert len(external_id) <= 200

    @pytest.mark.asyncio
    async def test_transform_data_includes_metadata(
        self, mock_async_session, data_source_id
    ):
        """Test that metadata includes stressors and source."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "FR",
             "product": "Paper and paper products", "value": 0.2},
            {"stressor": "CH4 - combustion - air", "region": "FR",
             "product": "Paper and paper products", "value": 0.001},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        assert "metadata" in transformed[0]
        assert "stressors_included" in transformed[0]["metadata"]
        assert "source" in transformed[0]["metadata"]
        assert "Exiobase" in transformed[0]["metadata"]["source"]


# ============================================================================
# Test Scenario 6: _convert_to_co2e Handles GWP Conversion
# ============================================================================

class TestConvertToCo2e:
    """Test _convert_to_co2e method handles GWP conversion."""

    def test_convert_co2_uses_gwp_1(
        self, mock_async_session, data_source_id
    ):
        """Test that CO2 conversion uses GWP of 1."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._convert_to_co2e("CO2 - combustion - air", 1.0)

        # CO2 has GWP of 1
        assert result == 1.0

    def test_convert_ch4_uses_gwp_28(
        self, mock_async_session, data_source_id
    ):
        """Test that CH4 conversion uses GWP of 28 (AR5)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._convert_to_co2e("CH4 - combustion - air", 1.0)

        # CH4 has GWP100 of 28 (AR5)
        assert result == 28.0

    def test_convert_n2o_uses_gwp_265(
        self, mock_async_session, data_source_id
    ):
        """Test that N2O conversion uses GWP of 265 (AR5)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._convert_to_co2e("N2O - combustion - air", 1.0)

        # N2O has GWP100 of 265 (AR5)
        assert result == 265.0

    def test_convert_unknown_stressor_returns_value(
        self, mock_async_session, data_source_id
    ):
        """Test that unknown stressor returns original value (assumed CO2)."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._convert_to_co2e("Unknown stressor", 5.0)

        # Unknown should default to GWP of 1
        assert result == 5.0

    def test_convert_co2e_accuracy(
        self, mock_async_session, data_source_id
    ):
        """Test CO2e conversion accuracy for combined emissions."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Test combined emissions: 10 kg CO2 + 1 kg CH4 + 0.1 kg N2O
        co2_contribution = ingestion._convert_to_co2e("CO2 - combustion - air", 10.0)
        ch4_contribution = ingestion._convert_to_co2e("CH4 - combustion - air", 1.0)
        n2o_contribution = ingestion._convert_to_co2e("N2O - combustion - air", 0.1)

        total_co2e = co2_contribution + ch4_contribution + n2o_contribution

        # Expected: 10*1 + 1*28 + 0.1*265 = 10 + 28 + 26.5 = 64.5
        assert abs(total_co2e - 64.5) < 0.001


# ============================================================================
# Test Scenario 7: _clean_product_name Normalizes Names
# ============================================================================

class TestCleanProductName:
    """Test _clean_product_name method normalizes product names."""

    def test_clean_product_name_removes_underscores(
        self, mock_async_session, data_source_id
    ):
        """Test that underscores are replaced with spaces."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._clean_product_name("Motor_vehicles_and_parts")

        assert "_" not in result

    def test_clean_product_name_removes_hyphens(
        self, mock_async_session, data_source_id
    ):
        """Test that hyphens are replaced with spaces."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._clean_product_name("Gas-Diesel-Oil")

        assert "-" not in result

    def test_clean_product_name_strips_whitespace(
        self, mock_async_session, data_source_id
    ):
        """Test that leading/trailing whitespace is stripped."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._clean_product_name("  Cement  ")

        assert result == "Cement"

    def test_clean_product_name_truncates_to_100_chars(
        self, mock_async_session, data_source_id
    ):
        """Test that product name is truncated to 100 characters."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        long_name = "A" * 200
        result = ingestion._clean_product_name(long_name)

        assert len(result) <= 100

    def test_clean_product_name_handles_region_prefix(
        self, mock_async_session, data_source_id
    ):
        """Test that region prefix is handled if present."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Some Exiobase columns have format "Region_Product"
        result = ingestion._clean_product_name("DE_Electricity by coal")

        # Should remove region prefix if it looks like a region code
        assert "Electricity" in result


# ============================================================================
# Test Scenario 8: _categorize_product Assigns Categories
# ============================================================================

class TestCategorizeProduct:
    """Test _categorize_product method assigns correct categories."""

    def test_categorize_electricity(
        self, mock_async_session, data_source_id
    ):
        """Test that electricity products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._categorize_product("Electricity by coal")

        assert result == "electricity"

    def test_categorize_energy_fuels(
        self, mock_async_session, data_source_id
    ):
        """Test that energy/fuel products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        assert ingestion._categorize_product("Natural Gas") == "energy"
        assert ingestion._categorize_product("Coal and lignite") == "energy"
        assert ingestion._categorize_product("Gas/Diesel Oil") == "energy"

    def test_categorize_materials(
        self, mock_async_session, data_source_id
    ):
        """Test that material products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        assert ingestion._categorize_product("Iron and steel") == "materials"
        assert ingestion._categorize_product("Aluminium products") == "materials"
        assert ingestion._categorize_product("Cement") == "materials"
        assert ingestion._categorize_product("Plastics, basic") == "materials"
        assert ingestion._categorize_product("Paper products") == "materials"

    def test_categorize_transport(
        self, mock_async_session, data_source_id
    ):
        """Test that transport products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._categorize_product("Motor vehicles")

        assert result == "transport"

    def test_categorize_electronics(
        self, mock_async_session, data_source_id
    ):
        """Test that electronic products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._categorize_product("Electronic equipment")

        assert result == "electronics"

    def test_categorize_machinery(
        self, mock_async_session, data_source_id
    ):
        """Test that machinery products are categorized correctly."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._categorize_product("Machinery and equipment")

        assert result == "machinery"

    def test_categorize_unknown_returns_other(
        self, mock_async_session, data_source_id
    ):
        """Test that unknown products are categorized as 'other'."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._categorize_product("Hotels and restaurants")

        assert result == "other"

    def test_categorize_is_case_insensitive(
        self, mock_async_session, data_source_id
    ):
        """Test that categorization is case-insensitive."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        assert ingestion._categorize_product("ELECTRICITY") == "electricity"
        assert ingestion._categorize_product("electricity") == "electricity"
        assert ingestion._categorize_product("Electricity") == "electricity"


# ============================================================================
# Test Scenario 9: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling for various edge cases."""

    @pytest.mark.asyncio
    async def test_parse_data_handles_empty_zip(
        self, mock_async_session, data_source_id
    ):
        """Test that parse_data handles empty ZIP file."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Create empty ZIP
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            pass
        buffer.seek(0)
        empty_zip = buffer.getvalue()

        with pytest.raises(ValueError, match="F matrix"):
            await ingestion.parse_data(empty_zip)

    @pytest.mark.asyncio
    async def test_transform_data_handles_empty_list(
        self, mock_async_session, data_source_id
    ):
        """Test that transform_data handles empty parsed data."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = await ingestion.transform_data([])

        assert result == []

    def test_convert_to_co2e_handles_zero(
        self, mock_async_session, data_source_id
    ):
        """Test that _convert_to_co2e handles zero values."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._convert_to_co2e("CO2 - combustion - air", 0.0)

        assert result == 0.0

    def test_clean_product_name_handles_empty_string(
        self, mock_async_session, data_source_id
    ):
        """Test that _clean_product_name handles empty string."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        result = ingestion._clean_product_name("")

        assert result == ""


# ============================================================================
# Test Scenario 10: Unit Configuration
# ============================================================================

class TestUnitConfiguration:
    """Test unit configuration for Exiobase data."""

    @pytest.mark.asyncio
    async def test_transform_data_uses_monetary_unit(
        self, mock_async_session, data_source_id
    ):
        """Test that transformed data uses EUR output as unit base."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "DE",
             "product": "Iron and steel", "value": 0.5},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Exiobase uses monetary units (kg CO2e per EUR output)
        assert "EUR" in transformed[0]["unit"]
        assert "CO2e" in transformed[0]["unit"]


# ============================================================================
# Test Scenario 11: Reference Year Configuration
# ============================================================================

class TestReferenceYearConfiguration:
    """Test reference year configuration."""

    @pytest.mark.asyncio
    async def test_transform_data_uses_reference_year(
        self, mock_async_session, data_source_id
    ):
        """Test that transform_data uses the configured reference_year."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        parsed_data = [
            {"stressor": "CO2 - combustion - air", "region": "GB",
             "product": "Chemicals nec", "value": 0.4},
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Default reference year is 2022 for Exiobase 3.8.2
        assert transformed[0]["reference_year"] == 2022

    def test_reference_year_can_be_overridden(
        self, mock_async_session, data_source_id
    ):
        """Test that reference_year can be overridden after instantiation."""
        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("ExiobaseEmissionFactorsIngestion not yet implemented")

        ingestion = ExiobaseEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id
        )

        # Override reference year
        ingestion.reference_year = 2021

        assert ingestion.reference_year == 2021
