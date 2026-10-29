"""
Fuel Record Transformer.

TASK-DATA-P7-025: Refactor High-Complexity Transform Function

This module provides the FuelTransformer class for transforming raw fuel
emission factor records into a normalized format. The original function
had cyclomatic complexity >10; this refactored version targets CC < 8.

Complexity Reduction Strategy:
- Extract validation to validate_required_fields helper
- Extract parsing to parse_emission_factor helper
- Extract unit handling to convert_unit helper
- Extract category building to _build_category method
- Use dataclass for structured output

Classes:
- TransformedRecord: Dataclass for transformed record output
- FuelTransformer: Main transformer class with reduced complexity
"""

from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

from backend.services.data_ingestion.transformers.helpers import (
    parse_emission_factor,
    validate_required_fields,
    convert_unit,
    parse_uncertainty,
    normalize_fuel_type,
)


@dataclass
class TransformedRecord:
    """
    Data class representing a transformed fuel emission factor record.

    Attributes:
        category: Normalized category string (e.g., "fuel_diesel")
        co2e_kg: CO2 equivalent in kg per unit
        unit: Normalized unit (e.g., "L", "m3", "kWh")
        data_source: Source of the data (e.g., "EPA", "DEFRA")
        year: Year of the emission factor data (optional)
        uncertainty: Uncertainty as decimal (0.05 for 5%) (optional)
        region: Geographic region code (optional)
        blend_percentage: Biofuel blend percentage (optional)
    """

    category: str
    co2e_kg: float
    unit: str
    data_source: str
    year: Optional[int] = None
    uncertainty: Optional[float] = None
    region: Optional[str] = None
    blend_percentage: Optional[int] = None


class FuelTransformer:
    """
    Transformer for fuel emission factor records.

    Transforms raw fuel records from various sources (EPA, DEFRA, etc.)
    into a normalized TransformedRecord format.

    Target Cyclomatic Complexity: < 8
    Original Complexity: > 10

    Attributes:
        REQUIRED_FIELDS: List of fields that must be present in input records

    Example:
        >>> transformer = FuelTransformer()
        >>> raw_record = {
        ...     "fuel_type": "diesel",
        ...     "emission_factor": "2.68",
        ...     "unit": "kg CO2e/L",
        ...     "source": "EPA",
        ...     "year": "2023"
        ... }
        >>> result = transformer.transform(raw_record)
        >>> result.category
        'fuel_diesel'
        >>> result.co2e_kg
        2.68
    """

    REQUIRED_FIELDS = ["fuel_type", "emission_factor", "unit", "source"]

    def transform(self, raw_record: Dict[str, Any]) -> TransformedRecord:
        """
        Transform raw fuel record to normalized format.

        Cyclomatic Complexity: ~4 (reduced from >10)

        Args:
            raw_record: Dictionary containing raw fuel emission data

        Returns:
            TransformedRecord: Normalized emission factor record

        Raises:
            TransformationError: If required fields missing or invalid format
        """
        # Validate required fields (extracted helper)
        validate_required_fields(raw_record, self.REQUIRED_FIELDS)

        # Parse emission factor (extracted helper)
        co2e_kg = parse_emission_factor(raw_record["emission_factor"])

        # Normalize unit and convert value (extracted helper)
        unit, co2e_kg = convert_unit(raw_record["unit"], co2e_kg)

        # Build category (extracted method)
        category = self._build_category(raw_record)

        # Parse optional fields
        uncertainty = parse_uncertainty(raw_record.get("uncertainty"))
        year = self._parse_year(raw_record.get("year"))
        region = raw_record.get("region")
        blend_percentage = self._parse_blend_percentage(
            raw_record.get("blend_percentage")
        )

        return TransformedRecord(
            category=category,
            co2e_kg=co2e_kg,
            unit=unit,
            data_source=raw_record["source"],
            year=year,
            uncertainty=uncertainty,
            region=region,
            blend_percentage=blend_percentage,
        )

    def _build_category(self, record: Dict[str, Any]) -> str:
        """
        Build category string from fuel type and variants.

        Handles special cases:
        - Biofuel blends: fuel_diesel_B20
        - Regional electricity: electricity_US_MIDWEST
        - Standard fuels: fuel_diesel

        Args:
            record: The raw record dictionary

        Returns:
            str: The constructed category string
        """
        fuel_type = record["fuel_type"]
        base = normalize_fuel_type(fuel_type)

        # Handle biofuel blends (B20, E10, etc.)
        blend_pct = record.get("blend_percentage")
        if blend_pct:
            # Determine blend type from fuel type code
            blend_code = self._get_blend_code(fuel_type, blend_pct)
            return f"fuel_diesel_{blend_code}"

        # Handle regional variations (mainly for electricity)
        region = record.get("region")
        if region:
            return f"{base}_{region}"

        # Standard fuel category
        return f"fuel_{base}"

    def _get_blend_code(self, fuel_type: str, blend_percentage: str) -> str:
        """
        Get blend code for biofuel blends.

        Args:
            fuel_type: The raw fuel type (e.g., "B20", "E10")
            blend_percentage: The blend percentage string

        Returns:
            str: Blend code (e.g., "B20", "E10")
        """
        fuel_upper = fuel_type.upper()
        # If fuel type already contains blend code, use it
        if fuel_upper.startswith("B") or fuel_upper.startswith("E"):
            return fuel_upper
        # Otherwise construct from percentage
        try:
            pct = int(blend_percentage)
            return f"B{pct}"
        except (ValueError, TypeError):
            return f"B{blend_percentage}"

    def _parse_year(self, value: Optional[Union[str, int]]) -> Optional[int]:
        """
        Parse year from string or integer.

        Args:
            value: Year value as string or integer

        Returns:
            int or None: Parsed year or None if invalid/missing
        """
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_blend_percentage(
        self, value: Optional[Union[str, int]]
    ) -> Optional[int]:
        """
        Parse blend percentage from string or integer.

        Args:
            value: Blend percentage as string or integer

        Returns:
            int or None: Parsed percentage or None if invalid/missing
        """
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
