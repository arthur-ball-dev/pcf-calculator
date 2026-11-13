"""
Units used by catalog emission factors (TASK-BE-P9-014, #195 follow-up).

The live catalog's rows convert to factors in these units: ship freight in tkm against EPA's
"short ton-mile", process water in L against DEFRA's "cubic metres", and DEFRA fuels per
"kWh (Gross CV)". Each must convert within its kind. "vehicle-mile" (distance driven, not
freight carried) has no conversion from tkm.
"""

from decimal import Decimal

import pytest

from backend.domain.units import are_compatible, convert, unit_kind

TKM_PER_SHORT_TON_MILE = Decimal("0.90718474") * Decimal("1.609344")


class TestCatalogUnitKinds:
    @pytest.mark.parametrize(
        "unit, kind",
        [
            ("short ton-mile", "freight"),
            ("cubic metres", "volume"),
            ("m3", "volume"),
            ("kWh (Gross CV)", "energy"),
            ("kWh (Net CV)", "energy"),
        ],
    )
    def test_kind(self, unit, kind):
        assert unit_kind(unit) == kind

    def test_vehicle_mile_is_not_freight(self):
        assert not are_compatible("tkm", "vehicle-mile")


class TestCatalogUnitConversions:
    def test_tonne_km_to_short_ton_miles(self):
        assert convert(TKM_PER_SHORT_TON_MILE, "tkm", "short ton-mile") == Decimal(1)
        assert abs(convert(Decimal("100"), "tkm", "short ton-mile") - Decimal("68.4944")) < Decimal("0.0001")

    def test_litres_to_cubic_metres(self):
        assert convert(Decimal("250"), "L", "cubic metres") == Decimal("0.25")
        assert convert(Decimal("1"), "m3", "L") == Decimal("1000")

    def test_kwh_gross_cv_is_kwh(self):
        assert convert(Decimal("3"), "kWh", "kWh (Gross CV)") == Decimal("3")
        assert convert(Decimal("3.6"), "MJ", "kWh (Net CV)") == Decimal("1")
