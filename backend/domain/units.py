"""
Unit kinds and quantity conversion.

TASK-BE-P9-013 (#195): a submitted BOM row's quantity is converted to its emission factor's
unit before quantity x factor. Units convert only within a kind. A unit outside this table
(for example a raw EPA string such as "vehicle-mile") is compatible only with itself.

Mirrored in frontend/src/utils/units.ts, which limits the BOM editor's unit picklist to units
of the selected factor's kind; keep the two tables in step.
"""

from decimal import Decimal
from typing import Dict, Optional

# 1 short ton-mile = 0.90718474 t x 1.609344 km
TKM_PER_SHORT_TON_MILE = Decimal("0.90718474") * Decimal("1.609344")

# kind -> {unit (lower case): size in the kind's base unit}. Besides the units the BOM editor
# offers, the table carries the units catalog emission factors use (EPA "short ton-mile", DEFRA
# "cubic metres" and "kWh (Gross CV)"), so catalog rows convert to them (#195).
# "vehicle-mile" (distance driven) is deliberately absent: freight in tkm doesn't convert to it.
_UNIT_TABLE: Dict[str, Dict[str, Decimal]] = {
    "mass": {"kg": Decimal(1), "g": Decimal("0.001"), "t": Decimal(1000)},
    "volume": {
        "l": Decimal(1),
        "ml": Decimal("0.001"),
        "cubic metres": Decimal(1000),
        "cubic meters": Decimal(1000),
        "m3": Decimal(1000),
    },
    "energy": {
        "kwh": Decimal(1),
        "mj": Decimal(1) / Decimal("3.6"),
        "kwh (gross cv)": Decimal(1),
        "kwh (net cv)": Decimal(1),
    },
    "freight": {"tkm": Decimal(1), "short ton-mile": TKM_PER_SHORT_TON_MILE},
    "count": {"unit": Decimal(1)},
    "length": {"m": Decimal(1), "cm": Decimal("0.01")},
}

_KIND_OF: Dict[str, str] = {
    unit: kind for kind, units in _UNIT_TABLE.items() for unit in units
}


def _key(unit: str) -> str:
    return unit.strip().lower()


def unit_kind(unit: str) -> Optional[str]:
    """The kind of a unit (mass, volume, energy, freight, count, length), or None if unknown."""
    return _KIND_OF.get(_key(unit))


def are_compatible(from_unit: str, to_unit: str) -> bool:
    """Whether a quantity in from_unit can be converted to to_unit."""
    kind = unit_kind(from_unit)
    if kind is None or unit_kind(to_unit) is None:
        return _key(from_unit) == _key(to_unit)
    return kind == unit_kind(to_unit)


def convert(quantity: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """Convert a quantity between compatible units; raises ValueError otherwise."""
    if not are_compatible(from_unit, to_unit):
        raise ValueError(f"Cannot convert {from_unit!r} to {to_unit!r}")
    kind = unit_kind(from_unit)
    if kind is None:
        return quantity
    sizes = _UNIT_TABLE[kind]
    return quantity * sizes[_key(from_unit)] / sizes[_key(to_unit)]
