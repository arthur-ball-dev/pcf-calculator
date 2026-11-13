"""
EmissionFactorMapper prefers a factor whose unit the row's unit converts to
(TASK-BE-P9-014, #195 follow-up).

EPA lists "Medium- and Heavy-Duty Truck" twice: per vehicle-mile and per short ton-mile. The
mapper took the first name match, so freight rows in tkm got the per-vehicle-mile factor,
which no quantity in tkm can be converted to. Among a component's matching factors it now
takes the first one with a compatible unit, and only falls back to the first match when none is.
"""

from types import SimpleNamespace

from backend.services.data_ingestion.emission_factor_mapper import pick_factor_for_unit


def factor(name, unit):
    return SimpleNamespace(activity_name=name, unit=unit)


VEHICLE_MILE = factor("Transport - Medium- and Heavy-Duty Truck", "vehicle-mile")
TON_MILE = factor("Transport - Medium- and Heavy-Duty TruckC", "short ton-mile")


def test_takes_the_first_factor_with_a_compatible_unit():
    assert pick_factor_for_unit([VEHICLE_MILE, TON_MILE], "tkm") is TON_MILE


def test_keeps_the_order_among_compatible_factors():
    a, b = factor("Steel A", "kg"), factor("Steel B", "kg")
    assert pick_factor_for_unit([a, b], "g") is a


def test_falls_back_to_the_first_match_when_none_is_compatible():
    assert pick_factor_for_unit([VEHICLE_MILE], "tkm") is VEHICLE_MILE


def test_no_candidates():
    assert pick_factor_for_unit([], "kg") is None
