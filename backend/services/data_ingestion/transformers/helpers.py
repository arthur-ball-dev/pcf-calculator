"""
Helper Functions for Data Transformation.

TASK-DATA-P7-025: Refactor High-Complexity Transform Function

This module provides low-complexity helper functions for transforming
emission factor records. Each function has a single responsibility
and cyclomatic complexity < 8.

Functions:
- parse_emission_factor: Parse string/number to float
- validate_required_fields: Validate required fields are present
- convert_unit: Normalize unit and convert value
- parse_uncertainty: Parse uncertainty percentage to decimal
- normalize_fuel_type: Normalize fuel type string

Exceptions:
- TransformationError: Raised for transformation failures
"""

from typing import Optional, List, Tuple, Union, Callable
import re


class TransformationError(Exception):
    """
    Exception raised for errors during data transformation.

    Used when:
    - Required fields are missing
    - Values cannot be parsed
    - Invalid data formats encountered
    """

    pass


# Constants for unit conversion
LITERS_PER_GALLON = 3.785411784


# Unit conversion patterns: (pattern, unit_name, conversion_fn)
# Order matters - more specific patterns should come first
_UNIT_PATTERNS: List[Tuple[str, str, Callable[[float], float]]] = [
    (r"/gal(?:lon)?(?:\s|$)", "L", lambda v: v / LITERS_PER_GALLON),  # gallon -> L
    (r"/m3(?:\s|$)", "m3", lambda v: v),  # cubic meters
    (r"/l(?:iter|itre)?(?:\s|$)", "L", lambda v: v),  # liters
    (r"/kwh(?:\s|$)", "kWh", lambda v: v),  # kilowatt-hours
    (r"/kg(?:\s|$)", "kg", lambda v: v),  # kilograms
    (r"/tonne(?:\s|$)", "tonne", lambda v: v),  # tonnes
]


def parse_emission_factor(value: Union[str, int, float]) -> float:
    """
    Parse emission factor string or number to float.

    Handles string representations, integers, floats, and scientific notation.
    Empty strings are treated as invalid.

    Args:
        value: The emission factor value (string, int, or float)

    Returns:
        float: The parsed emission factor

    Raises:
        TransformationError: If value cannot be parsed as a number

    Examples:
        >>> parse_emission_factor("2.68")
        2.68
        >>> parse_emission_factor(5)
        5.0
        >>> parse_emission_factor("1.5e-3")
        0.0015
    """
    try:
        # Handle empty strings explicitly
        if isinstance(value, str) and value.strip() == "":
            raise ValueError("Empty string")
        return float(value)
    except (ValueError, TypeError):
        raise TransformationError(f"Invalid emission factor format: {value}")


def validate_required_fields(record: dict, required: List[str]) -> None:
    """
    Validate all required fields are present and not None.

    Args:
        record: The record dictionary to validate
        required: List of required field names

    Raises:
        TransformationError: If any required field is missing or None

    Examples:
        >>> record = {"fuel_type": "diesel", "emission_factor": "2.68"}
        >>> validate_required_fields(record, ["fuel_type", "emission_factor"])
        # No error raised

        >>> validate_required_fields(record, ["fuel_type", "unit"])
        TransformationError: Missing required field: unit
    """
    for field in required:
        if field not in record or record[field] is None:
            raise TransformationError(f"Missing required field: {field}")


def convert_unit(unit_string: str, value: float) -> Tuple[str, float]:
    """
    Convert unit to standard format and adjust value if needed.

    Extracts the base unit from "kg CO2e/X" format and converts
    non-standard units (gallon) to standard units (L).

    Args:
        unit_string: The unit string (e.g., "kg CO2e/L", "kg CO2e/gallon")
        value: The emission factor value

    Returns:
        Tuple of (normalized_unit, converted_value)

    Examples:
        >>> convert_unit("kg CO2e/L", 2.68)
        ('L', 2.68)
        >>> convert_unit("kg CO2e/gallon", 2.68)
        ('L', 0.708...)  # Divided by 3.785
        >>> convert_unit("kg CO2e/kWh", 0.42)
        ('kWh', 0.42)
    """
    unit_lower = unit_string.lower()

    # Try each pattern in order
    for pattern, unit_name, converter in _UNIT_PATTERNS:
        if re.search(pattern, unit_lower, re.IGNORECASE):
            return unit_name, converter(value)

    # Default: extract unit after last "/"
    return _extract_default_unit(unit_string, value)


def _extract_default_unit(unit_string: str, value: float) -> Tuple[str, float]:
    """
    Extract default unit from unit string when no pattern matches.

    Args:
        unit_string: The original unit string
        value: The emission factor value

    Returns:
        Tuple of (extracted_unit, value)
    """
    if "/" in unit_string:
        extracted = unit_string.split("/")[-1].strip()
        return extracted, value
    return unit_string, value


def parse_uncertainty(value: Optional[str]) -> Optional[float]:
    """
    Parse uncertainty percentage to decimal.

    Handles values with or without '%' sign, and strips whitespace.
    Returns None for invalid or None values.

    Args:
        value: The uncertainty string (e.g., "5%", "10", None)

    Returns:
        float or None: The uncertainty as decimal (0.05 for 5%) or None

    Examples:
        >>> parse_uncertainty("5%")
        0.05
        >>> parse_uncertainty("10")
        0.10
        >>> parse_uncertainty(None)
        None
        >>> parse_uncertainty("unknown")
        None
    """
    if value is None:
        return None

    try:
        cleaned = str(value).strip().rstrip("%").strip()
        return float(cleaned) / 100
    except (ValueError, TypeError):
        return None


def normalize_fuel_type(fuel_type: str) -> str:
    """
    Normalize fuel type string to consistent format.

    Converts to lowercase and replaces spaces/hyphens with underscores.

    Args:
        fuel_type: The raw fuel type string

    Returns:
        str: Normalized fuel type string

    Examples:
        >>> normalize_fuel_type("DIESEL")
        'diesel'
        >>> normalize_fuel_type("Natural Gas")
        'natural_gas'
        >>> normalize_fuel_type("bio-diesel")
        'bio_diesel'
    """
    return fuel_type.lower().replace(" ", "_").replace("-", "_")
