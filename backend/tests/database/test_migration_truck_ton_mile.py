"""
Data migration: catalog truck rows in tkm use EPA's per-ton-mile truck factor
(TASK-BE-P9-014, #195 follow-up).

Rows measured in tkm pointed at "Transport - Medium- and Heavy-Duty Truck" per vehicle-mile,
which tkm can't be converted to. The migration points them at the per-short-ton-mile truck
factor. Other rows are untouched, and nothing happens when that factor isn't loaded.
"""

import importlib.util
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from backend.models import BillOfMaterials, EmissionFactor, Product

MIGRATION = next(
    (Path(__file__).resolve().parents[2] / "alembic" / "versions").glob("*_truck_rows_per_ton_mile.py")
)
spec = importlib.util.spec_from_file_location("truck_rows_per_ton_mile", MIGRATION)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def _uid():
    return uuid.uuid4().hex


@pytest.fixture
def add_factor(db_session):
    def _add(name, unit, value="1"):
        ef = EmissionFactor(id=_uid(), activity_name=name, co2e_factor=Decimal(value), unit=unit,
                            data_source="test_migration_truck_ton_mile", geography="GLO")
        db_session.add(ef)
        db_session.commit()
        return ef
    return _add


@pytest.fixture
def add_row(db_session):
    parent = Product(id=_uid(), code=f"MIG-{_uid()[:10]}", name="Migration Laptop", unit="unit",
                     is_finished_product=True)
    db_session.add(parent)
    db_session.commit()

    def _add(child_name, unit, factor):
        child = Product(id=_uid(), code=f"MIGC-{_uid()[:10]}", name=child_name, unit="unit")
        db_session.add(child)
        db_session.commit()
        row = BillOfMaterials(id=_uid(), parent_product_id=parent.id, child_product_id=child.id,
                              quantity=Decimal("10"), unit=unit, emission_factor_id=factor.id)
        db_session.add(row)
        db_session.commit()
        return row
    return _add


def _factor_of(db_session, row):
    db_session.expire_all()
    return db_session.get(BillOfMaterials, row.id).emission_factor_id


def test_tkm_truck_rows_move_to_the_ton_mile_factor(db_session, add_factor, add_row):
    per_vehicle_mile = add_factor("Transport - Medium- and Heavy-Duty Truck", "vehicle-mile", "1.36")
    per_ton_mile = add_factor("Transport - Medium- and Heavy-Duty TruckC", "short ton-mile", "0.168")
    truck = add_row("Transport - Truck", "tkm", per_vehicle_mile)

    moved = migration.move_truck_rows_to_ton_mile(db_session.connection())

    assert moved == 1
    assert _factor_of(db_session, truck) == per_ton_mile.id


def test_other_rows_are_untouched(db_session, add_factor, add_row):
    per_vehicle_mile = add_factor("Transport - Medium- and Heavy-Duty Truck", "vehicle-mile")
    add_factor("Transport - Medium- and Heavy-Duty TruckC", "short ton-mile")
    steel = add_factor("Steel", "kg")
    by_the_mile = add_row("Courier van", "vehicle-mile", per_vehicle_mile)
    metal = add_row("Steel Frame", "kg", steel)

    migration.move_truck_rows_to_ton_mile(db_session.connection())

    assert _factor_of(db_session, by_the_mile) == per_vehicle_mile.id
    assert _factor_of(db_session, metal) == steel.id


def test_nothing_happens_without_the_ton_mile_factor(db_session, add_factor, add_row):
    per_vehicle_mile = add_factor("Transport - Medium- and Heavy-Duty Truck", "vehicle-mile")
    truck = add_row("Transport - Truck", "tkm", per_vehicle_mile)

    assert migration.move_truck_rows_to_ton_mile(db_session.connection()) == 0
    assert _factor_of(db_session, truck) == per_vehicle_mile.id


def test_downgrade_moves_them_back(db_session, add_factor, add_row):
    per_vehicle_mile = add_factor("Transport - Medium- and Heavy-Duty Truck", "vehicle-mile")
    add_factor("Transport - Medium- and Heavy-Duty TruckC", "short ton-mile")
    truck = add_row("Transport - Truck", "tkm", per_vehicle_mile)

    migration.move_truck_rows_to_ton_mile(db_session.connection())
    migration.move_truck_rows_to_vehicle_mile(db_session.connection())

    assert _factor_of(db_session, truck) == per_vehicle_mile.id
