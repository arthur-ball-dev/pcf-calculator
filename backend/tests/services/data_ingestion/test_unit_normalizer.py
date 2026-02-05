"""
Tests for Unit Normalizer Module

Tests the normalization of emission factor units to standard base units.
"""

import pytest
from backend.services.data_ingestion.transformers.unit_normalizer import (
    NormalizationResult,
    normalize_unit,
    get_supported_units,
    is_unit_supported,
    UNIT_CONVERSIONS,
)


class TestNormalizeUnit:
    """Tests for normalize_unit function."""

    @pytest.mark.parametrize(
        "factor,unit,expected_factor,expected_unit",
        [
            # Mass conversions: tonnes -> kg
            (1000.0, "tonnes", 1.0, "kg"),
            (1800.0, "tonne", 1.8, "kg"),
            (2500.0, "t", 2.5, "kg"),
            (1000.0, "metric ton", 1.0, "kg"),
            (1000.0, "metric tons", 1.0, "kg"),
            # Volume conversions: gallon -> L
            (3.785411784, "gallon", 1.0, "L"),
            (7.570823568, "gallons", 2.0, "L"),
            (3.785411784, "gal", 1.0, "L"),
            # Energy conversions: mmBtu -> kWh
            (293.07107, "mmBtu", 1.0, "kWh"),
            # Energy conversions: MJ -> kWh
            (3.6, "MJ", 1.0, "kWh"),
            (36.0, "mj", 10.0, "kWh"),
            # GJ -> kWh
            (3.6, "GJ", 1000.0, "kWh"),
            # BTU -> kWh
            (3412.14, "btu", 1.0, "kWh"),
            # No change - already standard units
            (2.5, "kg", 2.5, "kg"),
            (1.5, "kWh", 1.5, "kWh"),
            (0.5, "L", 0.5, "L"),
            (0.1, "tkm", 0.1, "tkm"),
            (10.0, "unit", 10.0, "unit"),
        ],
    )
    def test_normalize_unit_conversions(
        self, factor: float, unit: str, expected_factor: float, expected_unit: str
    ):
        """Test that various units are correctly normalized."""
        result = normalize_unit(factor, unit)

        assert result.normalized_unit == expected_unit
        assert abs(result.normalized_factor - expected_factor) < 0.01
        assert result.original_factor == factor
        assert result.original_unit == unit

    def test_normalize_tonnes_preserves_audit_trail(self):
        """Test that normalization preserves original values for audit."""
        result = normalize_unit(1800.0, "tonnes")

        assert result.normalized_factor == 1.8
        assert result.normalized_unit == "kg"
        assert result.original_factor == 1800.0
        assert result.original_unit == "tonnes"
        assert result.conversion_factor == 0.001
        assert result.was_normalized is True
        assert result.normalized_at is not None

    def test_no_normalization_for_standard_units(self):
        """Test that standard units are not normalized."""
        result = normalize_unit(2.5, "kg")

        assert result.normalized_factor == 2.5
        assert result.normalized_unit == "kg"
        assert result.original_factor == 2.5
        assert result.original_unit == "kg"
        assert result.conversion_factor == 1.0
        assert result.was_normalized is False
        assert result.normalized_at is None

    def test_unknown_unit_passthrough(self):
        """Test that unknown units pass through without conversion."""
        result = normalize_unit(5.0, "unknownUnit")

        assert result.normalized_factor == 5.0
        assert result.normalized_unit == "unknownUnit"
        assert result.original_factor == 5.0
        assert result.original_unit == "unknownUnit"
        assert result.conversion_factor == 1.0
        assert result.was_normalized is False

    def test_case_insensitive_units(self):
        """Test that unit matching is case-insensitive."""
        result_lower = normalize_unit(1000.0, "tonnes")
        result_upper = normalize_unit(1000.0, "TONNES")
        result_mixed = normalize_unit(1000.0, "Tonnes")

        assert result_lower.normalized_factor == result_upper.normalized_factor
        assert result_lower.normalized_factor == result_mixed.normalized_factor

    def test_whitespace_handling(self):
        """Test that whitespace in units is handled."""
        result = normalize_unit(1000.0, "  tonnes  ")

        assert result.normalized_factor == 1.0
        assert result.normalized_unit == "kg"

    def test_zero_factor(self):
        """Test normalization of zero factor."""
        result = normalize_unit(0.0, "tonnes")

        assert result.normalized_factor == 0.0
        assert result.normalized_unit == "kg"
        assert result.conversion_factor == 0.001

    def test_negative_factor(self):
        """Test normalization handles negative factors (edge case)."""
        result = normalize_unit(-1000.0, "tonnes")

        assert result.normalized_factor == -1.0
        assert result.normalized_unit == "kg"


class TestNormalizationResult:
    """Tests for NormalizationResult dataclass."""

    def test_dataclass_fields(self):
        """Test that NormalizationResult has expected fields."""
        result = NormalizationResult(
            normalized_factor=1.8,
            normalized_unit="kg",
            original_factor=1800.0,
            original_unit="tonnes",
            conversion_factor=0.001,
            was_normalized=True,
        )

        assert result.normalized_factor == 1.8
        assert result.normalized_unit == "kg"
        assert result.original_factor == 1800.0
        assert result.original_unit == "tonnes"
        assert result.conversion_factor == 0.001
        assert result.was_normalized is True


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_supported_units(self):
        """Test that get_supported_units returns all known units."""
        units = get_supported_units()

        assert "tonnes" in units
        assert "kg" in units
        assert "kwh" in units  # Units are stored lowercase
        assert len(units) > 10

    def test_is_unit_supported(self):
        """Test is_unit_supported function."""
        assert is_unit_supported("tonnes") is True
        assert is_unit_supported("kg") is True
        assert is_unit_supported("unknownUnit") is False
        assert is_unit_supported("TONNES") is True  # Case-insensitive


class TestRealWorldScenarios:
    """Tests using real-world emission factor examples."""

    def test_defra_steel_normalization(self):
        """Test DEFRA steel factor (typically in kg CO2e/tonne)."""
        # DEFRA steel: ~2800 kg CO2e/tonne
        result = normalize_unit(2800.0, "tonne")

        assert abs(result.normalized_factor - 2.8) < 0.0001
        assert result.normalized_unit == "kg"
        # Now 5kg of steel: 5 * 2.8 = 14 kg CO2e (correct!)
        bom_quantity_kg = 5.0
        emissions = bom_quantity_kg * result.normalized_factor
        assert abs(emissions - 14.0) < 0.01

    def test_defra_aluminium_normalization(self):
        """Test DEFRA aluminium factor."""
        # DEFRA aluminium: ~9000 kg CO2e/tonne
        result = normalize_unit(9000.0, "tonnes")

        assert result.normalized_factor == 9.0
        assert result.normalized_unit == "kg"

    def test_epa_fuel_normalization(self):
        """Test EPA fuel factor (in mmBtu)."""
        # EPA natural gas: ~53 kg CO2e/mmBtu
        result = normalize_unit(53.0, "mmBtu")

        # Should convert to kg CO2e/kWh
        assert result.normalized_unit == "kWh"
        assert result.was_normalized is True

    def test_calculation_without_1000x_error(self):
        """Verify that normalized factors don't cause 1000x errors."""
        # Scenario: Gaming laptop with 5kg of components
        bom_quantity_kg = 5.0

        # Wrong (unnormalized): 5 * 2800 = 14,000 kg CO2e
        unnormalized_factor = 2800.0  # kg CO2e/tonne
        wrong_result = bom_quantity_kg * unnormalized_factor
        assert wrong_result == 14000.0  # This is wrong!

        # Correct (normalized): 5 * 2.8 = 14 kg CO2e
        result = normalize_unit(2800.0, "tonne")
        correct_result = bom_quantity_kg * result.normalized_factor
        assert abs(correct_result - 14.0) < 0.01  # This is correct!
