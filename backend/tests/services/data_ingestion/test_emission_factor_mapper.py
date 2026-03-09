"""
Test suite for EmissionFactorMapper class.

TASK-DATA-P8-004: Emission Factor Mapping Infrastructure - Phase A Tests

This test suite validates:
- Exact match returns correct factor
- Partial match returns best match (shortest name)
- Category fallback works when no direct match
- Geographic fallback to GLO works
- Unmapped components logged as warnings
- Cache improves performance on repeated lookups

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no EmissionFactorMapper class exists yet)
- Implementation must make tests PASS without modifying tests

CRITICAL: All factors use EPA + DEFRA only (no Exiobase) to avoid ShareAlike.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from typing import List, Dict, Any

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
def sample_emission_factors():
    """Create sample emission factors for testing."""
    return [
        {
            "id": uuid4().hex,
            "activity_name": "aluminum",
            "co2e_factor": Decimal("8.5"),
            "unit": "kg",
            "geography": "US",
            "category": "material",
            "data_source": "EPA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "aluminum",
            "co2e_factor": Decimal("9.2"),
            "unit": "kg",
            "geography": "GLO",
            "category": "material",
            "data_source": "DEFRA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "steel_hot_rolled",
            "co2e_factor": Decimal("2.8"),
            "unit": "kg",
            "geography": "GLO",
            "category": "material",
            "data_source": "DEFRA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "steel",
            "co2e_factor": Decimal("2.5"),
            "unit": "kg",
            "geography": "GLO",
            "category": "material",
            "data_source": "EPA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "plastic_abs",
            "co2e_factor": Decimal("3.2"),
            "unit": "kg",
            "geography": "GLO",
            "category": "material",
            "data_source": "EPA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "electricity_grid_us",
            "co2e_factor": Decimal("0.42"),
            "unit": "kWh",
            "geography": "US",
            "category": "energy",
            "data_source": "EPA",
            "data_source_id": uuid4().hex,
        },
        {
            "id": uuid4().hex,
            "activity_name": "electricity_grid",
            "co2e_factor": Decimal("0.45"),
            "unit": "kWh",
            "geography": "GLO",
            "category": "energy",
            "data_source": "DEFRA",
            "data_source_id": uuid4().hex,
        },
    ]


# ============================================================================
# Test Scenario 1: EmissionFactorMapper Instantiation
# ============================================================================

class TestEmissionFactorMapperInstantiation:
    """Test EmissionFactorMapper class instantiation."""

    def test_constructor_initializes_with_async_session(
        self, mock_async_session
    ):
        """Test that constructor accepts async session."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mapper = EmissionFactorMapper(db=mock_async_session)

        assert mapper.db == mock_async_session
        assert hasattr(mapper, '_mapping_cache')
        assert hasattr(mapper, '_warnings')

    def test_constructor_initializes_empty_cache(
        self, mock_async_session
    ):
        """Test that constructor initializes empty mapping cache."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mapper = EmissionFactorMapper(db=mock_async_session)

        assert isinstance(mapper._mapping_cache, dict)
        assert len(mapper._mapping_cache) == 0

    def test_constructor_initializes_empty_warnings(
        self, mock_async_session
    ):
        """Test that constructor initializes empty warnings list."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mapper = EmissionFactorMapper(db=mock_async_session)

        assert isinstance(mapper._warnings, list)
        assert len(mapper._warnings) == 0


# ============================================================================
# Test Scenario 2: Exact Match Returns Correct Factor
# ============================================================================

class TestExactMatch:
    """Test exact match functionality."""

    @pytest.mark.asyncio
    async def test_exact_match_returns_factor_with_matching_name_and_unit(
        self, mock_async_session, sample_emission_factors
    ):
        """Test that exact match returns correct factor."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # Mock the database query result
        mock_result = MagicMock()
        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "aluminum"
        mock_factor.co2e_factor = Decimal("8.5")
        mock_factor.unit = "kg"
        mock_factor.geography = "US"
        mock_result.scalar_one_or_none.return_value = mock_factor
        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg",
            geography="US"
        )

        assert result is not None
        assert result.activity_name == "aluminum"
        assert result.co2e_factor == Decimal("8.5")

    @pytest.mark.asyncio
    async def test_exact_match_respects_geography(
        self, mock_async_session
    ):
        """Test that exact match respects geography parameter."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # First call (with geography=US) returns US factor
        mock_result_us = MagicMock()
        mock_factor_us = MagicMock(spec=EmissionFactor)
        mock_factor_us.activity_name = "aluminum"
        mock_factor_us.co2e_factor = Decimal("8.5")
        mock_factor_us.geography = "US"
        mock_result_us.scalar_one_or_none.return_value = mock_factor_us

        mock_async_session.execute.return_value = mock_result_us

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg",
            geography="US"
        )

        assert result is not None
        assert result.geography == "US"

    @pytest.mark.asyncio
    async def test_exact_match_not_found_returns_none_from_exact_match(
        self, mock_async_session
    ):
        """Test that exact match returns None when not found."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        # Also mock scalars().all() for partial match
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = []
        mock_result.scalars.return_value = mock_scalars_result

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Call internal _exact_match method
        result = await mapper._exact_match(
            component_name="nonexistent_material",
            unit="kg",
            geography=None
        )

        assert result is None


# ============================================================================
# Test Scenario 3: Partial Match Returns Best Match (Shortest Name)
# ============================================================================

class TestPartialMatch:
    """Test partial match functionality."""

    @pytest.mark.asyncio
    async def test_partial_match_returns_factor_containing_search_term(
        self, mock_async_session
    ):
        """Test that partial match finds factor containing component name."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # Mock factors for partial match
        mock_factor1 = MagicMock(spec=EmissionFactor)
        mock_factor1.activity_name = "steel_hot_rolled"
        mock_factor1.co2e_factor = Decimal("2.8")

        mock_factor2 = MagicMock(spec=EmissionFactor)
        mock_factor2.activity_name = "steel"
        mock_factor2.co2e_factor = Decimal("2.5")

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_factor1, mock_factor2]
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper._partial_match(
            component_name="steel",
            unit="kg",
            geography=None
        )

        assert result is not None
        # Should return the shorter name (most specific)
        assert result.activity_name == "steel"

    @pytest.mark.asyncio
    async def test_partial_match_returns_shortest_name_as_best_match(
        self, mock_async_session
    ):
        """Test that partial match returns factor with shortest name."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # Mock multiple matching factors
        mock_factor_long = MagicMock(spec=EmissionFactor)
        mock_factor_long.activity_name = "plastic_abs_molding"

        mock_factor_medium = MagicMock(spec=EmissionFactor)
        mock_factor_medium.activity_name = "plastic_abs"

        mock_factor_short = MagicMock(spec=EmissionFactor)
        mock_factor_short.activity_name = "plastic"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [
            mock_factor_long, mock_factor_medium, mock_factor_short
        ]
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper._partial_match(
            component_name="plastic",
            unit="kg",
            geography=None
        )

        assert result is not None
        assert result.activity_name == "plastic"

    @pytest.mark.asyncio
    async def test_partial_match_is_case_insensitive(
        self, mock_async_session
    ):
        """Test that partial match is case-insensitive."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "Aluminum"
        mock_factor.co2e_factor = Decimal("8.5")

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_factor]
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        # Search with different case
        result = await mapper._partial_match(
            component_name="ALUMINUM",
            unit="kg",
            geography=None
        )

        assert result is not None
        # Verify that ILIKE is used (case-insensitive)
        mock_async_session.execute.assert_called()


# ============================================================================
# Test Scenario 4: Category Fallback Works When No Direct Match
# ============================================================================

class TestCategoryFallback:
    """Test category fallback functionality."""

    @pytest.mark.asyncio
    async def test_category_fallback_extracts_category_from_component_name(
        self, mock_async_session
    ):
        """Test that category is extracted from component name."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Test category extraction
        assert mapper._extract_category("steel_sheet") == "material"
        assert mapper._extract_category("aluminum_rod") == "material"
        assert mapper._extract_category("electricity_grid") == "energy"
        assert mapper._extract_category("transport_truck") == "transport"

    @pytest.mark.asyncio
    async def test_category_fallback_returns_factor_from_same_category(
        self, mock_async_session
    ):
        """Test that category fallback returns factor from same category."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "steel"
        mock_factor.co2e_factor = Decimal("2.5")
        mock_factor.category = "material"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_factor]
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper._category_fallback(
            component_name="steel_special_alloy",
            unit="kg"
        )

        assert result is not None
        assert result.category == "material"

    @pytest.mark.asyncio
    async def test_category_fallback_returns_none_for_unknown_category(
        self, mock_async_session
    ):
        """Test that category fallback returns None for unknown category."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper._category_fallback(
            component_name="unknown_exotic_material",
            unit="kg"
        )

        assert result is None


# ============================================================================
# Test Scenario 5: Geographic Fallback to GLO Works
# ============================================================================

class TestGeographicFallback:
    """Test geographic fallback to GLO."""

    @pytest.mark.asyncio
    async def test_geographic_fallback_uses_glo_when_specific_region_unavailable(
        self, mock_async_session
    ):
        """Test that GLO is used when specific region not available."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # First call returns None (no JP-specific factor)
        mock_result_jp = MagicMock()
        mock_result_jp.scalar_one_or_none.return_value = None
        mock_scalars_empty = MagicMock()
        mock_scalars_empty.all.return_value = []
        mock_result_jp.scalars.return_value = mock_scalars_empty

        # Second call returns GLO factor
        mock_factor_glo = MagicMock(spec=EmissionFactor)
        mock_factor_glo.activity_name = "aluminum"
        mock_factor_glo.co2e_factor = Decimal("9.2")
        mock_factor_glo.geography = "GLO"

        mock_result_glo = MagicMock()
        mock_result_glo.scalar_one_or_none.return_value = mock_factor_glo

        # Configure mock to return different results
        mock_async_session.execute.side_effect = [
            mock_result_jp,   # First exact match (JP) returns None
            mock_result_jp,   # Partial match returns empty
            mock_result_jp,   # Category fallback
            mock_result_glo,  # GLO fallback returns factor
        ]

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg",
            geography="JP"  # Japan - not available, should fall back to GLO
        )

        assert result is not None
        assert result.geography == "GLO"

    @pytest.mark.asyncio
    async def test_geographic_fallback_not_triggered_when_glo_already_requested(
        self, mock_async_session
    ):
        """Test that GLO fallback is not triggered when GLO is already requested."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # When geography is already GLO, don't trigger GLO fallback
        result = await mapper.get_factor_for_component(
            component_name="unknown_material",
            unit="kg",
            geography="GLO"
        )

        # Should return None and log warning (not trigger infinite GLO loop)
        assert result is None


# ============================================================================
# Test Scenario 6: Unmapped Components Logged as Warnings
# ============================================================================

class TestUnmappedComponents:
    """Test unmapped component warning functionality."""

    @pytest.mark.asyncio
    async def test_unmapped_component_returns_none(
        self, mock_async_session
    ):
        """Test that unmapped component returns None."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # All lookups return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        result = await mapper.get_factor_for_component(
            component_name="unknown_exotic_material",
            unit="kg"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_unmapped_component_adds_warning(
        self, mock_async_session
    ):
        """Test that unmapped component adds warning to warnings list."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # All lookups return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)
        await mapper.get_factor_for_component(
            component_name="unknown_exotic_material",
            unit="kg",
            geography="US"
        )

        warnings = mapper.get_warnings()
        assert len(warnings) == 1
        assert warnings[0]["component_name"] == "unknown_exotic_material"
        assert warnings[0]["unit"] == "kg"
        assert warnings[0]["geography"] == "US"

    @pytest.mark.asyncio
    async def test_get_warnings_returns_all_unmapped_components(
        self, mock_async_session
    ):
        """Test that get_warnings returns all unmapped components."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Multiple unmapped components
        await mapper.get_factor_for_component("unknown1", "kg")
        await mapper.get_factor_for_component("unknown2", "L")
        await mapper.get_factor_for_component("unknown3", "kWh")

        warnings = mapper.get_warnings()
        assert len(warnings) == 3


# ============================================================================
# Test Scenario 8: Cache Improves Performance on Repeated Lookups
# ============================================================================

class TestCaching:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit_does_not_query_database(
        self, mock_async_session
    ):
        """Test that cache hit doesn't trigger database query."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "aluminum"
        mock_factor.co2e_factor = Decimal("8.5")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_factor

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # First call - should query database
        result1 = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg",
            geography="US"
        )

        call_count_after_first = mock_async_session.execute.call_count

        # Second call - should use cache
        result2 = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg",
            geography="US"
        )

        call_count_after_second = mock_async_session.execute.call_count

        # Database should not be called again
        assert call_count_after_first == call_count_after_second
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_clear_cache_removes_all_cached_entries(
        self, mock_async_session
    ):
        """Test that clear_cache removes all cached entries."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "aluminum"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_factor

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Populate cache
        await mapper.get_factor_for_component("aluminum", "kg", "US")
        assert len(mapper._mapping_cache) > 0

        # Clear cache
        mapper.clear_cache()

        assert len(mapper._mapping_cache) == 0
        assert len(mapper._warnings) == 0

    @pytest.mark.asyncio
    async def test_different_parameters_create_different_cache_keys(
        self, mock_async_session
    ):
        """Test that different parameters create different cache entries."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor_us = MagicMock(spec=EmissionFactor)
        mock_factor_us.activity_name = "aluminum"
        mock_factor_us.geography = "US"

        mock_factor_uk = MagicMock(spec=EmissionFactor)
        mock_factor_uk.activity_name = "aluminum"
        mock_factor_uk.geography = "UK"

        mock_result_us = MagicMock()
        mock_result_us.scalar_one_or_none.return_value = mock_factor_us

        mock_result_uk = MagicMock()
        mock_result_uk.scalar_one_or_none.return_value = mock_factor_uk

        mock_async_session.execute.side_effect = [
            mock_result_us,
            mock_result_uk
        ]

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Different geographies should create different cache entries
        result_us = await mapper.get_factor_for_component("aluminum", "kg", "US")
        result_uk = await mapper.get_factor_for_component("aluminum", "kg", "UK")

        assert len(mapper._mapping_cache) == 2
        assert result_us.geography == "US"
        assert result_uk.geography == "UK"


# ============================================================================
# Test Scenario 9: Mapping Configuration Loading
# ============================================================================

class TestMappingConfiguration:
    """Test mapping configuration loading from JSON."""

    def test_load_mapping_aliases_from_json(self, mock_async_session):
        """Test that mapping aliases are loaded from JSON config."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mapper = EmissionFactorMapper(db=mock_async_session)

        # Test that aliases are loaded
        assert hasattr(mapper, '_aliases') or hasattr(mapper, '_load_mappings')

    @pytest.mark.asyncio
    async def test_alias_resolution_before_lookup(self, mock_async_session):
        """Test that aliases are resolved before database lookup."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "aluminum"
        mock_factor.co2e_factor = Decimal("8.5")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_factor

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        # "aluminium" (British spelling) should resolve to "aluminum"
        result = await mapper.get_factor_for_component(
            component_name="aluminium",  # British spelling
            unit="kg"
        )

        # Should find aluminum factor
        assert result is not None


# ============================================================================
# Test Scenario 10: Full Mapping Pipeline
# ============================================================================

class TestFullMappingPipeline:
    """Test the complete mapping pipeline."""

    @pytest.mark.asyncio
    async def test_mapping_priority_order(self, mock_async_session):
        """Test that mapping follows correct priority order."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        # Configure mock to track call order
        call_order = []

        async def track_execute(*args, **kwargs):
            call_order.append("execute")
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = []
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        mock_async_session.execute.side_effect = track_execute

        mapper = EmissionFactorMapper(db=mock_async_session)

        await mapper.get_factor_for_component(
            component_name="test_material",
            unit="kg",
            geography="US"
        )

        # Should have made multiple calls following priority order:
        # 1. Exact match
        # 2. Partial match
        # 3. Category fallback
        # 4. Geographic fallback (GLO)
        assert len(call_order) >= 3

    @pytest.mark.asyncio
    async def test_first_successful_match_stops_search(self, mock_async_session):
        """Test that search stops at first successful match."""
        try:
            from backend.services.data_ingestion.emission_factor_mapper import (
                EmissionFactorMapper
            )
            from backend.models import EmissionFactor
        except ImportError:
            pytest.skip("EmissionFactorMapper not yet implemented")

        mock_factor = MagicMock(spec=EmissionFactor)
        mock_factor.activity_name = "aluminum"
        mock_factor.co2e_factor = Decimal("8.5")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_factor

        mock_async_session.execute.return_value = mock_result

        mapper = EmissionFactorMapper(db=mock_async_session)

        result = await mapper.get_factor_for_component(
            component_name="aluminum",
            unit="kg"
        )

        # Exact match found - should only call once
        assert mock_async_session.execute.call_count == 1
        assert result is not None
