"""
Unit kinds and quantity conversion for submitted BOMs.

TASK-BE-P9-013 (#195): a BOM row's quantity is converted to its emission factor's unit before
quantity x factor. Units convert only within a kind; a unit outside the table matches only itself.
"""

from decimal import Decimal

import pytest

from backend.domain.units import are_compatible, convert, unit_kind


class TestUnitKind:
    @pytest.mark.parametrize(
        "unit, kind",
        [
            ("kg", "mass"),
            ("g", "mass"),
            ("t", "mass"),
            ("L", "volume"),
            ("mL", "volume"),
            ("kWh", "energy"),
            ("MJ", "energy"),
            ("tkm", "freight"),
            ("unit", "count"),
            ("m", "length"),
            ("cm", "length"),
        ],
    )
    def test_known_units(self, unit, kind):
        assert unit_kind(unit) == kind

    def test_lookup_ignores_case_and_surrounding_space(self):
        assert unit_kind(" KG ") == "mass"
        assert unit_kind("kwh") == "energy"
        assert unit_kind("ml") == "volume"

    def test_unknown_unit_has_no_kind(self):
        assert unit_kind("vehicle-mile") is None
        assert unit_kind("") is None


class TestCompatibility:
    def test_same_kind_is_compatible(self):
        assert are_compatible("g", "kg")
        assert are_compatible("MJ", "kWh")

    def test_different_kinds_are_not(self):
        assert not are_compatible("kg", "kWh")
        assert not are_compatible("L", "kg")
        assert not are_compatible("unit", "kg")

    def test_unknown_unit_matches_only_itself(self):
        assert are_compatible("vehicle-mile", "vehicle-mile")
        assert are_compatible("Vehicle-Mile", "vehicle-mile")
        assert not are_compatible("vehicle-mile", "km")
        assert not are_compatible("vehicle-mile", "kg")


class TestConvert:
    @pytest.mark.parametrize(
        "quantity, from_unit, to_unit, expected",
        [
            ("500", "g", "kg", "0.5"),
            ("2", "t", "kg", "2000"),
            ("0.25", "kg", "g", "250"),
            ("750", "mL", "L", "0.75"),
            ("90", "cm", "m", "0.9"),
            ("3", "kWh", "kWh", "3"),
            ("1.5", "tkm", "tkm", "1.5"),
            ("4", "unit", "unit", "4"),
        ],
    )
    def test_exact_conversions(self, quantity, from_unit, to_unit, expected):
        assert convert(Decimal(quantity), from_unit, to_unit) == Decimal(expected)

    def test_megajoules_to_kilowatt_hours(self):
        # 1 kWh = 3.6 MJ
        assert convert(Decimal("36"), "MJ", "kWh") == Decimal("10")
        assert abs(convert(Decimal("1"), "MJ", "kWh") - Decimal(1) / Decimal("3.6")) < Decimal("1e-20")

    def test_unknown_unit_to_itself_is_unchanged(self):
        assert convert(Decimal("7"), "vehicle-mile", "vehicle-mile") == Decimal("7")

    def test_incompatible_units_raise(self):
        with pytest.raises(ValueError):
            convert(Decimal("1"), "kg", "kWh")
        with pytest.raises(ValueError):
            convert(Decimal("1"), "vehicle-mile", "km")
