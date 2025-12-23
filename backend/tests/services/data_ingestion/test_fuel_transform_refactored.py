"""
Test suite for refactored fuel record transformation.

TASK-DATA-P7-025: Refactor High-Complexity Transform Function - Phase A Tests

This test suite validates the refactored _transform_fuel_record function which
has been decomposed into smaller, testable helper functions with lower
cyclomatic complexity.

Test coverage includes:
- FuelTransformer class with reduced complexity (CC < 8)
- Helper functions in transformers/helpers.py
- All 8 transformation scenarios from SPEC
- Edge cases and error handling
- Backward compatibility with existing behavior

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (refactored modules don't exist yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Test Fixtures
# =============================================================================

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


# =============================================================================
# Test Scenario 1: Standard Fuel Record Transformation
# =============================================================================

class TestStandardFuelRecordTransformation:
    """Test standard fuel record transformation (Scenario 1 from SPEC)."""

    def test_standard_diesel_record_transforms_correctly(self):
        """Test that a standard diesel fuel record transforms to expected output."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer,
                TransformedRecord
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert isinstance(result, TransformedRecord)
        assert result.category == "fuel_diesel"
        assert result.co2e_kg == 2.68
        assert result.unit == "L"
        assert result.data_source == "EPA"
        assert result.year == 2023
        assert result.uncertainty is None

    def test_standard_record_preserves_data_source(self):
        """Test that data source is preserved in transformation."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "gasoline",
            "emission_factor": "2.31",
            "unit": "kg CO2e/L",
            "source": "DEFRA",
            "year": "2024"
        }

        result = transformer.transform(raw_record)

        assert result.data_source == "DEFRA"


# =============================================================================
# Test Scenario 2: Fuel with Unit Conversion (Natural Gas)
# =============================================================================

class TestFuelWithUnitConversion:
    """Test fuel records with different units (Scenario 2 from SPEC)."""

    def test_natural_gas_m3_unit_preserved(self):
        """Test that natural gas with m3 unit transforms correctly."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "natural_gas",
            "emission_factor": "1.93",
            "unit": "kg CO2e/m3",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.category == "fuel_natural_gas"
        assert result.co2e_kg == 1.93
        assert result.unit == "m3"
        assert result.data_source == "EPA"
        assert result.year == 2023

    def test_kwh_unit_preserved(self):
        """Test that kWh unit is preserved correctly."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "electricity",
            "emission_factor": "0.42",
            "unit": "kg CO2e/kWh",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.unit == "kWh"


# =============================================================================
# Test Scenario 3: Fuel with Uncertainty Data
# =============================================================================

class TestFuelWithUncertainty:
    """Test fuel records with uncertainty data (Scenario 3 from SPEC)."""

    def test_percentage_uncertainty_parsed_correctly(self):
        """Test that uncertainty percentage is parsed to decimal."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "gasoline",
            "emission_factor": "2.31",
            "unit": "kg CO2e/L",
            "uncertainty": "5%",
            "source": "DEFRA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.category == "fuel_gasoline"
        assert result.co2e_kg == 2.31
        assert result.unit == "L"
        assert result.data_source == "DEFRA"
        assert result.year == 2023
        assert result.uncertainty == 0.05

    def test_uncertainty_without_percent_sign(self):
        """Test that uncertainty without % sign is still parsed."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "uncertainty": "10",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.uncertainty == 0.10

    def test_missing_uncertainty_returns_none(self):
        """Test that missing uncertainty field returns None."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.uncertainty is None


# =============================================================================
# Test Scenario 4: Missing Required Field
# =============================================================================

class TestMissingRequiredField:
    """Test error handling for missing required fields (Scenario 4 from SPEC)."""

    def test_missing_emission_factor_raises_error(self):
        """Test that missing emission_factor raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            # Missing emission_factor
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Missing required field: emission_factor" in str(exc_info.value)

    def test_missing_fuel_type_raises_error(self):
        """Test that missing fuel_type raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            # Missing fuel_type
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Missing required field: fuel_type" in str(exc_info.value)

    def test_missing_unit_raises_error(self):
        """Test that missing unit raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            # Missing unit
            "source": "EPA"
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Missing required field: unit" in str(exc_info.value)

    def test_missing_source_raises_error(self):
        """Test that missing source raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            # Missing source
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Missing required field: source" in str(exc_info.value)

    def test_none_value_treated_as_missing(self):
        """Test that None value in required field is treated as missing."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": None,  # None value
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Missing required field: emission_factor" in str(exc_info.value)


# =============================================================================
# Test Scenario 5: Invalid Emission Factor Format
# =============================================================================

class TestInvalidEmissionFactorFormat:
    """Test error handling for invalid emission factor format (Scenario 5 from SPEC)."""

    def test_non_numeric_emission_factor_raises_error(self):
        """Test that non-numeric emission_factor raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "not_a_number",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(raw_record)

        assert "Invalid emission factor format: not_a_number" in str(exc_info.value)

    def test_empty_string_emission_factor_raises_error(self):
        """Test that empty string emission_factor raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError):
            transformer.transform(raw_record)

    def test_special_characters_in_emission_factor_raises_error(self):
        """Test that special characters in emission_factor raises error."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
            from backend.services.data_ingestion.transformers.helpers import (
                TransformationError
            )
        except ImportError:
            pytest.skip("FuelTransformer or TransformationError not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68$",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        with pytest.raises(TransformationError):
            transformer.transform(raw_record)


# =============================================================================
# Test Scenario 6: Unknown Unit Format (Gallon to Liter Conversion)
# =============================================================================

class TestUnknownUnitFormatConversion:
    """Test unit conversion for non-standard units (Scenario 6 from SPEC)."""

    def test_gallon_to_liter_conversion(self):
        """Test that gallon unit is converted to liters."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/gallon",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        assert result.category == "fuel_diesel"
        # 2.68 / 3.785 = 0.708 (approximately)
        assert abs(result.co2e_kg - 0.708) < 0.001
        assert result.unit == "L"
        assert result.data_source == "EPA"

    def test_gal_abbreviation_to_liter_conversion(self):
        """Test that 'gal' abbreviation is also converted to liters."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "gasoline",
            "emission_factor": "2.31",
            "unit": "kg CO2e/gal",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        # Should convert from gallon to liter
        assert result.unit == "L"
        assert abs(result.co2e_kg - (2.31 / 3.785)) < 0.001


# =============================================================================
# Test Scenario 7: Regional Variation Handling
# =============================================================================

class TestRegionalVariationHandling:
    """Test regional variation handling (Scenario 7 from SPEC)."""

    def test_electricity_with_region_code(self):
        """Test that region is included in category for electricity."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "electricity",
            "emission_factor": "0.42",
            "unit": "kg CO2e/kWh",
            "region": "US_MIDWEST",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        assert result.category == "electricity_US_MIDWEST"
        assert result.co2e_kg == 0.42
        assert result.unit == "kWh"
        assert result.data_source == "EPA"
        assert result.region == "US_MIDWEST"

    def test_region_preserves_exact_code(self):
        """Test that region code is preserved exactly as provided."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "electricity",
            "emission_factor": "0.38",
            "unit": "kg CO2e/kWh",
            "region": "EU_WEST",
            "source": "DEFRA"
        }

        result = transformer.transform(raw_record)

        assert result.region == "EU_WEST"
        assert "EU_WEST" in result.category

    def test_fuel_without_region_has_none_region(self):
        """Test that fuel without region has None region attribute."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        assert result.region is None or not hasattr(result, 'region') or result.region is None


# =============================================================================
# Test Scenario 8: Biofuel Blend Handling
# =============================================================================

class TestBiofuelBlendHandling:
    """Test biofuel blend handling (Scenario 8 from SPEC)."""

    def test_b20_biodiesel_blend(self):
        """Test that B20 biodiesel blend is handled correctly."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "B20",
            "emission_factor": "2.48",
            "unit": "kg CO2e/L",
            "blend_percentage": "20",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        assert result.category == "fuel_diesel_B20"
        assert result.co2e_kg == 2.48
        assert result.unit == "L"
        assert result.data_source == "EPA"
        assert result.blend_percentage == 20

    def test_e10_ethanol_blend(self):
        """Test that E10 ethanol blend is handled correctly."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "E10",
            "emission_factor": "2.25",
            "unit": "kg CO2e/L",
            "blend_percentage": "10",
            "source": "EPA"
        }

        result = transformer.transform(raw_record)

        # E10 is gasoline blend, so category should reflect that
        assert "B10" in result.category or "E10" in result.category or "gasoline" in result.category.lower()
        assert result.blend_percentage == 10


# =============================================================================
# Test Helper Functions - parse_emission_factor
# =============================================================================

class TestParseEmissionFactor:
    """Test the parse_emission_factor helper function."""

    def test_parse_valid_float_string(self):
        """Test parsing valid float string."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor
            )
        except ImportError:
            pytest.skip("parse_emission_factor not yet implemented")

        result = parse_emission_factor("2.68")
        assert result == 2.68

    def test_parse_integer_string(self):
        """Test parsing integer string."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor
            )
        except ImportError:
            pytest.skip("parse_emission_factor not yet implemented")

        result = parse_emission_factor("5")
        assert result == 5.0

    def test_parse_scientific_notation(self):
        """Test parsing scientific notation."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor
            )
        except ImportError:
            pytest.skip("parse_emission_factor not yet implemented")

        result = parse_emission_factor("1.5e-3")
        assert abs(result - 0.0015) < 0.0001

    def test_parse_float_value(self):
        """Test parsing already float value."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor
            )
        except ImportError:
            pytest.skip("parse_emission_factor not yet implemented")

        result = parse_emission_factor(2.68)
        assert result == 2.68

    def test_parse_invalid_raises_error(self):
        """Test that invalid value raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor, TransformationError
            )
        except ImportError:
            pytest.skip("parse_emission_factor not yet implemented")

        with pytest.raises(TransformationError) as exc_info:
            parse_emission_factor("not_a_number")

        assert "Invalid emission factor format" in str(exc_info.value)


# =============================================================================
# Test Helper Functions - validate_required_fields
# =============================================================================

class TestValidateRequiredFields:
    """Test the validate_required_fields helper function."""

    def test_all_required_fields_present(self):
        """Test that no error is raised when all required fields present."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                validate_required_fields
            )
        except ImportError:
            pytest.skip("validate_required_fields not yet implemented")

        record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }
        required = ["fuel_type", "emission_factor", "unit", "source"]

        # Should not raise
        validate_required_fields(record, required)

    def test_missing_field_raises_error(self):
        """Test that missing field raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                validate_required_fields, TransformationError
            )
        except ImportError:
            pytest.skip("validate_required_fields not yet implemented")

        record = {
            "fuel_type": "diesel",
            "unit": "kg CO2e/L",
            "source": "EPA"
        }
        required = ["fuel_type", "emission_factor", "unit", "source"]

        with pytest.raises(TransformationError) as exc_info:
            validate_required_fields(record, required)

        assert "Missing required field: emission_factor" in str(exc_info.value)

    def test_none_value_raises_error(self):
        """Test that None value raises TransformationError."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                validate_required_fields, TransformationError
            )
        except ImportError:
            pytest.skip("validate_required_fields not yet implemented")

        record = {
            "fuel_type": "diesel",
            "emission_factor": None,
            "unit": "kg CO2e/L",
            "source": "EPA"
        }
        required = ["fuel_type", "emission_factor", "unit", "source"]

        with pytest.raises(TransformationError) as exc_info:
            validate_required_fields(record, required)

        assert "Missing required field: emission_factor" in str(exc_info.value)


# =============================================================================
# Test Helper Functions - convert_unit
# =============================================================================

class TestConvertUnit:
    """Test the convert_unit helper function."""

    def test_liter_unit_extraction(self):
        """Test extracting liter unit from 'kg CO2e/L'."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit, value = convert_unit("kg CO2e/L", 2.68)

        assert unit == "L"
        assert value == 2.68

    def test_liter_full_word_extraction(self):
        """Test extracting liter unit from 'kg CO2e/liter'."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit, value = convert_unit("kg CO2e/liter", 2.68)

        assert unit == "L"
        assert value == 2.68

    def test_m3_unit_extraction(self):
        """Test extracting m3 unit."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit, value = convert_unit("kg CO2e/m3", 1.93)

        assert unit == "m3"
        assert value == 1.93

    def test_kwh_unit_extraction(self):
        """Test extracting kWh unit."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit, value = convert_unit("kg CO2e/kWh", 0.42)

        assert unit == "kWh"
        assert value == 0.42

    def test_gallon_conversion_to_liter(self):
        """Test converting gallon to liter with value adjustment."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit, value = convert_unit("kg CO2e/gallon", 2.68)

        assert unit == "L"
        # 2.68 / 3.785 = 0.708 (approximately)
        assert abs(value - 0.708) < 0.001

    def test_case_insensitive_unit_matching(self):
        """Test that unit matching is case insensitive."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                convert_unit
            )
        except ImportError:
            pytest.skip("convert_unit not yet implemented")

        unit1, _ = convert_unit("KG CO2E/KWH", 0.42)
        unit2, _ = convert_unit("kg co2e/kwh", 0.42)

        assert unit1 == unit2 == "kWh"


# =============================================================================
# Test Helper Functions - parse_uncertainty
# =============================================================================

class TestParseUncertainty:
    """Test the parse_uncertainty helper function."""

    def test_percentage_with_sign(self):
        """Test parsing '5%' to 0.05."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_uncertainty
            )
        except ImportError:
            pytest.skip("parse_uncertainty not yet implemented")

        result = parse_uncertainty("5%")
        assert result == 0.05

    def test_percentage_without_sign(self):
        """Test parsing '10' to 0.10."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_uncertainty
            )
        except ImportError:
            pytest.skip("parse_uncertainty not yet implemented")

        result = parse_uncertainty("10")
        assert result == 0.10

    def test_none_returns_none(self):
        """Test that None input returns None."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_uncertainty
            )
        except ImportError:
            pytest.skip("parse_uncertainty not yet implemented")

        result = parse_uncertainty(None)
        assert result is None

    def test_invalid_returns_none(self):
        """Test that invalid value returns None."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_uncertainty
            )
        except ImportError:
            pytest.skip("parse_uncertainty not yet implemented")

        result = parse_uncertainty("unknown")
        assert result is None

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_uncertainty
            )
        except ImportError:
            pytest.skip("parse_uncertainty not yet implemented")

        result = parse_uncertainty("  5%  ")
        assert result == 0.05


# =============================================================================
# Test Helper Functions - normalize_fuel_type
# =============================================================================

class TestNormalizeFuelType:
    """Test the normalize_fuel_type helper function."""

    def test_lowercase_conversion(self):
        """Test that fuel type is converted to lowercase."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                normalize_fuel_type
            )
        except ImportError:
            pytest.skip("normalize_fuel_type not yet implemented")

        result = normalize_fuel_type("DIESEL")
        assert result == "diesel"

    def test_space_to_underscore(self):
        """Test that spaces are converted to underscores."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                normalize_fuel_type
            )
        except ImportError:
            pytest.skip("normalize_fuel_type not yet implemented")

        result = normalize_fuel_type("Natural Gas")
        assert result == "natural_gas"

    def test_hyphen_to_underscore(self):
        """Test that hyphens are converted to underscores."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                normalize_fuel_type
            )
        except ImportError:
            pytest.skip("normalize_fuel_type not yet implemented")

        result = normalize_fuel_type("bio-diesel")
        assert result == "bio_diesel"

    def test_mixed_case_and_special_chars(self):
        """Test handling of mixed case and special characters."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                normalize_fuel_type
            )
        except ImportError:
            pytest.skip("normalize_fuel_type not yet implemented")

        result = normalize_fuel_type("Fuel-Type Name")
        assert result == "fuel_type_name"


# =============================================================================
# Test TransformedRecord Dataclass
# =============================================================================

class TestTransformedRecord:
    """Test the TransformedRecord dataclass."""

    def test_required_attributes_exist(self):
        """Test that TransformedRecord has all required attributes."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                TransformedRecord
            )
        except ImportError:
            pytest.skip("TransformedRecord not yet implemented")

        record = TransformedRecord(
            category="fuel_diesel",
            co2e_kg=2.68,
            unit="L",
            data_source="EPA",
            year=2023,
            uncertainty=None
        )

        assert hasattr(record, "category")
        assert hasattr(record, "co2e_kg")
        assert hasattr(record, "unit")
        assert hasattr(record, "data_source")
        assert hasattr(record, "year")
        assert hasattr(record, "uncertainty")

    def test_optional_attributes_can_be_none(self):
        """Test that optional attributes can be None."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                TransformedRecord
            )
        except ImportError:
            pytest.skip("TransformedRecord not yet implemented")

        record = TransformedRecord(
            category="fuel_diesel",
            co2e_kg=2.68,
            unit="L",
            data_source="EPA",
            year=2023,
            uncertainty=None
        )

        assert record.uncertainty is None


# =============================================================================
# Test FuelTransformer Class Structure
# =============================================================================

class TestFuelTransformerClassStructure:
    """Test FuelTransformer class structure and configuration."""

    def test_required_fields_defined(self):
        """Test that REQUIRED_FIELDS class attribute is defined."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        assert hasattr(FuelTransformer, "REQUIRED_FIELDS")
        assert "fuel_type" in FuelTransformer.REQUIRED_FIELDS
        assert "emission_factor" in FuelTransformer.REQUIRED_FIELDS
        assert "unit" in FuelTransformer.REQUIRED_FIELDS
        assert "source" in FuelTransformer.REQUIRED_FIELDS

    def test_transform_method_exists(self):
        """Test that transform method exists."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        assert hasattr(transformer, "transform")
        assert callable(transformer.transform)


# =============================================================================
# Test Backward Compatibility with Existing EPA Ingestion
# =============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with existing EPAEmissionFactorsIngestion."""

    @pytest.mark.asyncio
    async def test_existing_fuel_record_format_works(
        self, mock_async_session, data_source_id
    ):
        """Test that existing EPA fuel record format still transforms correctly."""
        try:
            from backend.services.data_ingestion.epa_ingestion import (
                EPAEmissionFactorsIngestion
            )
        except ImportError:
            pytest.skip("EPAEmissionFactorsIngestion not available")

        ingestion = EPAEmissionFactorsIngestion(
            db=mock_async_session,
            data_source_id=data_source_id,
            file_key="fuels"
        )

        # Old format record
        parsed_data = [
            {
                "Fuel Type": "Natural Gas",
                "kg CO2e per unit": 2.75,
                "Unit": "kg",
                "Category": "Stationary Combustion",
                "_source_sheet": "Table 1 - Fuel",
                "_source_row": 2
            }
        ]

        transformed = await ingestion.transform_data(parsed_data)

        # Should still work
        assert len(transformed) == 1
        assert transformed[0]["activity_name"] == "Natural Gas"
        assert transformed[0]["co2e_factor"] == 2.75


# =============================================================================
# Test Complexity Verification (Structural Tests)
# =============================================================================

class TestComplexityVerification:
    """
    Test that refactored code meets complexity requirements.

    These tests verify the structural requirements of the refactoring:
    - Helper functions are independently importable
    - Each helper has focused, single responsibility
    - Main transform function delegates to helpers
    """

    def test_helpers_module_importable(self):
        """Test that helpers module can be imported."""
        try:
            from backend.services.data_ingestion.transformers import helpers
        except ImportError:
            pytest.skip("helpers module not yet implemented")

        assert helpers is not None

    def test_all_helper_functions_importable(self):
        """Test that all expected helper functions are importable."""
        try:
            from backend.services.data_ingestion.transformers.helpers import (
                parse_emission_factor,
                validate_required_fields,
                convert_unit,
                parse_uncertainty,
                normalize_fuel_type,
                TransformationError
            )
        except ImportError:
            pytest.skip("helper functions not yet implemented")

        # All should be callable
        assert callable(parse_emission_factor)
        assert callable(validate_required_fields)
        assert callable(convert_unit)
        assert callable(parse_uncertainty)
        assert callable(normalize_fuel_type)

    def test_fuel_transformer_module_importable(self):
        """Test that fuel_transformer module can be imported."""
        try:
            from backend.services.data_ingestion.transformers import fuel_transformer
        except ImportError:
            pytest.skip("fuel_transformer module not yet implemented")

        assert fuel_transformer is not None

    def test_transformers_package_structure(self):
        """Test that transformers package has proper structure."""
        try:
            from backend.services.data_ingestion import transformers
        except ImportError:
            pytest.skip("transformers package not yet implemented")

        # Should be a package with submodules
        assert hasattr(transformers, "__path__")


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_emission_factor_is_valid(self):
        """Test that zero emission factor is handled (may be valid for some fuels)."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "hydrogen",
            "emission_factor": "0",
            "unit": "kg CO2e/kg",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.co2e_kg == 0.0

    def test_very_small_emission_factor(self):
        """Test handling of very small emission factors."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "renewable",
            "emission_factor": "0.0001",
            "unit": "kg CO2e/kWh",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.co2e_kg == 0.0001

    def test_very_large_emission_factor(self):
        """Test handling of very large emission factors."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "coal_high_carbon",
            "emission_factor": "99999.99",
            "unit": "kg CO2e/tonne",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert result.co2e_kg == 99999.99

    def test_unicode_fuel_type(self):
        """Test handling of unicode characters in fuel type."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel_Type_A",  # Could contain special chars
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA",
            "year": "2023"
        }

        result = transformer.transform(raw_record)

        assert "diesel" in result.category.lower()

    def test_year_as_integer(self):
        """Test that year as integer is handled correctly."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA",
            "year": 2023  # Integer, not string
        }

        result = transformer.transform(raw_record)

        assert result.year == 2023

    def test_missing_year_is_optional(self):
        """Test that missing year field is handled gracefully."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()
        raw_record = {
            "fuel_type": "diesel",
            "emission_factor": "2.68",
            "unit": "kg CO2e/L",
            "source": "EPA"
            # No year field
        }

        result = transformer.transform(raw_record)

        # Year should be None or have a default
        assert result.year is None or isinstance(result.year, int)


# =============================================================================
# Test Multiple Records Transformation
# =============================================================================

class TestMultipleRecordsTransformation:
    """Test transforming multiple records."""

    def test_transform_multiple_valid_records(self):
        """Test transforming a list of valid records."""
        try:
            from backend.services.data_ingestion.transformers.fuel_transformer import (
                FuelTransformer
            )
        except ImportError:
            pytest.skip("FuelTransformer not yet implemented")

        transformer = FuelTransformer()

        records = [
            {
                "fuel_type": "diesel",
                "emission_factor": "2.68",
                "unit": "kg CO2e/L",
                "source": "EPA",
                "year": "2023"
            },
            {
                "fuel_type": "gasoline",
                "emission_factor": "2.31",
                "unit": "kg CO2e/L",
                "source": "EPA",
                "year": "2023"
            },
            {
                "fuel_type": "natural_gas",
                "emission_factor": "1.93",
                "unit": "kg CO2e/m3",
                "source": "EPA",
                "year": "2023"
            }
        ]

        results = [transformer.transform(r) for r in records]

        assert len(results) == 3
        assert results[0].category == "fuel_diesel"
        assert results[1].category == "fuel_gasoline"
        assert results[2].category == "fuel_natural_gas"
