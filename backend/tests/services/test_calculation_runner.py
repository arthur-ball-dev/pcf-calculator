"""
Tests for the production calculation path (issue #33).

execute_calculation is what POST /api/v1/calculate runs. These tests seed their
own products, so they cannot skip for want of seed data, and they replace the
database-backed tests that exercised the removed legacy calculator instead.
"""

import uuid
from decimal import Decimal

import pytest

from backend.models import BillOfMaterials, EmissionFactor, PCFCalculation, Product
from backend.services.calculation_runner import classify_component, execute_calculation


class _KeepOpen:
    """execute_calculation closes its session; the test session must survive that."""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        pass


def _uid():
    return uuid.uuid4().hex


@pytest.fixture
def add_product(db_session):
    def _add(name):
        product = Product(id=_uid(), code=f"T-{_uid()[:12]}", name=name, unit="kg")
        db_session.add(product)
        db_session.commit()
        return product

    return _add


@pytest.fixture
def add_factor(db_session):
    def _add(activity_name, value):
        factor = EmissionFactor(
            id=_uid(),
            activity_name=activity_name,
            co2e_factor=Decimal(value),
            unit="kg",
            data_source="test_calculation_runner",
            geography="GLO",
        )
        db_session.add(factor)
        db_session.commit()
        return factor

    return _add


@pytest.fixture
def add_bom_line(db_session):
    def _add(parent, child, quantity, factor=None):
        line = BillOfMaterials(
            id=_uid(),
            parent_product_id=parent.id,
            child_product_id=child.id,
            quantity=Decimal(quantity),
            unit="kg",
            emission_factor_id=factor.id if factor else None,
        )
        db_session.add(line)
        db_session.commit()
        return line

    return _add


@pytest.fixture
def run(db_session):
    def _run(product_id, row_product_id=None):
        calculation = PCFCalculation(
            id=_uid(),
            product_id=row_product_id or product_id,
            calculation_type="cradle_to_gate",
            status="pending",
            total_co2e_kg=0,
        )
        db_session.add(calculation)
        db_session.commit()
        execute_calculation(
            calculation.id,
            product_id,
            "cradle_to_gate",
            session_factory=lambda: _KeepOpen(db_session),
        )
        db_session.refresh(calculation)
        return calculation

    return _run


class TestCompletedCalculation:
    def test_total_categories_and_breakdown(self, add_product, add_factor, add_bom_line, run):
        shirt = add_product("Runner Test Shirt")
        add_bom_line(shirt, add_product("Cotton Fabric"), "2", add_factor("rt cotton", "5"))
        add_bom_line(shirt, add_product("Grid Electricity"), "1.5", add_factor("rt grid", "0.4"))
        add_bom_line(shirt, add_product("Truck Transport"), "0.2", add_factor("rt truck", "0.1"))

        calculation = run(shirt.id)

        assert calculation.status == "completed"
        assert calculation.total_co2e_kg == Decimal("10.62")
        assert calculation.materials_co2e == Decimal("10")
        assert calculation.energy_co2e == Decimal("0.6")
        assert calculation.transport_co2e == Decimal("0.02")
        assert calculation.breakdown == {
            "Cotton Fabric": 10.0,
            "Grid Electricity": 0.6,
            "Truck Transport": 0.02,
        }

    def test_tiny_values_keep_six_decimal_places(self, add_product, add_factor, add_bom_line, run):
        parent = add_product("Runner Test Tiny")
        factor = add_factor("rt tiny", "0.000123")
        add_bom_line(parent, add_product("Tiny A"), "1", factor)
        add_bom_line(parent, add_product("Tiny B"), "2", factor)

        assert run(parent.id).total_co2e_kg == Decimal("0.000369")

    def test_empty_bom_completes_at_zero(self, add_product, run):
        calculation = run(add_product("Runner Test Empty").id)

        assert calculation.status == "completed"
        assert calculation.total_co2e_kg == Decimal("0")
        assert calculation.breakdown == {}


class TestEmissionFactorLookup:
    def test_line_without_factor_id_falls_back_to_activity_name(
        self, add_product, add_factor, add_bom_line, run
    ):
        parent = add_product("Runner Test Fallback")
        add_factor("rt fallback steel", "3")
        add_bom_line(parent, add_product("RT Fallback Steel"), "2")

        assert run(parent.id).total_co2e_kg == Decimal("6")

    def test_line_with_no_matching_factor_counts_as_zero(self, add_product, add_bom_line, run):
        parent = add_product("Runner Test Unmatched")
        add_bom_line(parent, add_product("Nothing Matches This"), "2")

        calculation = run(parent.id)

        assert calculation.status == "completed"
        assert calculation.breakdown == {"Nothing Matches This": 0.0}


class TestFailure:
    def test_missing_product_marks_the_row_failed(self, add_product, run):
        row_owner = add_product("Runner Test Row Owner")

        calculation = run(_uid(), row_product_id=row_owner.id)

        assert calculation.status == "failed"
        assert "not found" in calculation.calculation_metadata["error_message"]


@pytest.mark.parametrize(
    "name, category",
    [
        ("Grid Electricity", "energy"),
        ("Renewable Energy", "energy"),
        ("Truck Transport", "transport"),
        ("Container Ship", "transport"),
        ("Cotton Fabric", "materials"),
    ],
)
def test_classify_component(name, category):
    assert classify_component(name) == category
