"""
Unit Normalizer Module

Normalizes emission factor units to standard base units (kg, kWh, L, tkm)
to prevent calculation errors from unit mismatches.

Key conversions:
- Mass: tonnes/tonne/t -> kg (÷1000)
- Volume: gallon -> L (÷3.785)
- Energy: mmBtu -> kWh (÷293.07), MJ -> kWh (÷3.6)

The normalization preserves original values for audit trail:
- original_unit: The unit as provided by the data source
- original_co2e_factor: The factor value before conversion
- conversion_factor: The multiplier applied (e.g., 0.001 for tonnes->kg)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple


@dataclass
class NormalizationResult:
    """Result of unit normalization operation."""
    normalized_factor: float
    normalized_unit: str
    original_factor: float
    original_unit: str
    conversion_factor: float
    was_normalized: bool
    normalized_at: Optional[datetime] = None


# Mapping from source units to (target_unit, conversion_factor)
# conversion_factor is multiplied with the original factor
# For per-unit factors: tonnes means "kg CO2e per tonne", so we multiply by 0.001
# to get "kg CO2e per kg"
UNIT_CONVERSIONS: Dict[str, Tuple[str, float]] = {
    # Mass units - normalize to kg
    "tonnes": ("kg", 0.001),
    "tonne": ("kg", 0.001),
    "t": ("kg", 0.001),
    "metric ton": ("kg", 0.001),
    "metric tons": ("kg", 0.001),
    # Volume units - normalize to L
    "gallon": ("L", 1 / 3.785411784),
    "gallons": ("L", 1 / 3.785411784),
    "gal": ("L", 1 / 3.785411784),
    # Energy units - normalize to kWh
    "mmbtu": ("kWh", 1 / 293.07107),
    "btu": ("kWh", 1 / 3412.14),  # 1 kWh = 3412.14 BTU
    "mj": ("kWh", 1 / 3.6),
    "gj": ("kWh", 1000 / 3.6),  # 1 GJ = 1000 MJ
    # Already standard units - no conversion needed
    "kg": ("kg", 1.0),
    "kwh": ("kWh", 1.0),
    "l": ("L", 1.0),
    "tkm": ("tkm", 1.0),
    "tonne-km": ("tkm", 1.0),
    "tonne-kilometer": ("tkm", 1.0),
    "unit": ("unit", 1.0),
    "units": ("unit", 1.0),
    "each": ("unit", 1.0),
}


def normalize_unit(co2e_factor: float, unit: str) -> NormalizationResult:
    """
    Normalize an emission factor to standard units.

    Args:
        co2e_factor: The CO2e emission factor value (kg CO2e per unit)
        unit: The unit of the emission factor

    Returns:
        NormalizationResult containing normalized values and audit trail

    Example:
        >>> result = normalize_unit(1800.0, "tonnes")
        >>> result.normalized_factor
        1.8
        >>> result.normalized_unit
        'kg'
        >>> result.conversion_factor
        0.001
    """
    unit_lower = unit.lower().strip()

    if unit_lower in UNIT_CONVERSIONS:
        target_unit, conv_factor = UNIT_CONVERSIONS[unit_lower]
        was_normalized = abs(conv_factor - 1.0) > 1e-9

        return NormalizationResult(
            normalized_factor=co2e_factor * conv_factor,
            normalized_unit=target_unit,
            original_factor=co2e_factor,
            original_unit=unit,
            conversion_factor=conv_factor,
            was_normalized=was_normalized,
            normalized_at=datetime.now() if was_normalized else None,
        )

    # Unknown unit - passthrough without conversion
    return NormalizationResult(
        normalized_factor=co2e_factor,
        normalized_unit=unit,
        original_factor=co2e_factor,
        original_unit=unit,
        conversion_factor=1.0,
        was_normalized=False,
        normalized_at=None,
    )


def get_supported_units() -> list[str]:
    """Return list of all supported units for normalization."""
    return list(UNIT_CONVERSIONS.keys())


def is_unit_supported(unit: str) -> bool:
    """Check if a unit is supported for normalization."""
    return unit.lower().strip() in UNIT_CONVERSIONS
