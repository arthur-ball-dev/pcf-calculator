"""
POST /api/v1/calculate with the BOM the user edited in the wizard.

TASK-BE-P9-013 (#195): the request may carry `bom`, the edited rows (name, quantity, unit,
category, emission_factor_id). With it, the calculation uses those rows instead of the catalog
BOM: each quantity is converted to its factor's unit, and the stored materials/energy/transport
totals follow each row's category (material/other -> materials, energy/combustion -> energy,
transport -> transport). Without it, the catalog BOM is used as before. The submitted rows are
never stored; only the result is.
"""

import json
import uuid
from decimal import Decimal

import pytest

from backend.models import BillOfMaterials, EmissionFactor, PCFCalculation, Product

CALCULATE = "/api/v1/calculate"


def _uid() -> str:
    return uuid.uuid4().hex


@pytest.fixture
def factor(db_session):
    def _add(value: str, unit: str) -> EmissionFactor:
        ef = EmissionFactor(
            id=_uid(),
            activity_name=f"submitted bom test {_uid()[:8]}",
            co2e_factor=Decimal(value),
            unit=unit,
            data_source="test_calculate_submitted_bom",
            geography="GLO",
        )
        db_session.add(ef)
        db_session.commit()
        return ef

    return _add


@pytest.fixture
def product(db_session, factor):
    """A finished product whose catalog BOM is 1 kg of a material at 5 kg CO2e/kg."""
    parent = Product(id=_uid(), code=f"SB-{_uid()[:10]}", name="Submitted BOM Shirt", unit="unit",
                     is_finished_product=True)
    child = Product(id=_uid(), code=f"SBC-{_uid()[:10]}", name="Catalog Cotton", unit="kg")
    db_session.add_all([parent, child])
    db_session.commit()
    catalog_factor = factor("5", "kg")
    db_session.add(BillOfMaterials(id=_uid(), parent_product_id=parent.id, child_product_id=child.id,
                                   quantity=Decimal("1"), unit="kg",
                                   emission_factor_id=catalog_factor.id))
    db_session.commit()
    return parent


def _row(name, quantity, unit, category, ef_id):
    return {"name": name, "quantity": quantity, "unit": unit, "category": category,
            "emission_factor_id": ef_id}


def _calculate(client, product_id, bom=None):
    body = {"product_id": product_id}
    if bom is not None:
        body["bom"] = bom
    return client.post(CALCULATE, json=body)


def _result(client, response):
    assert response.status_code == 202, response.text
    calc_id = response.json()["calculation_id"]
    result = client.get(f"/api/v1/calculations/{calc_id}")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["status"] == "completed", data
    return data


def _fields(response):
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    return [d["field"] for d in body["error"]["details"]]


class TestSubmittedBOMIsCalculated:
    def test_submitted_rows_replace_the_catalog_bom(self, client, product, factor):
        cotton, grid, truck = factor("5", "kg"), factor("0.4", "kWh"), factor("0.1", "tkm")
        data = _result(client, _calculate(client, product.id, [
            _row("Organic Cotton", 2, "kg", "material", cotton.id),
            _row("Grid Power", 3, "kWh", "energy", grid.id),
            _row("Truck Freight", 10, "tkm", "transport", truck.id),
        ]))

        assert data["total_co2e_kg"] == pytest.approx(12.2)
        assert data["materials_co2e"] == pytest.approx(10)
        assert data["energy_co2e"] == pytest.approx(1.2)
        assert data["transport_co2e"] == pytest.approx(1)
        assert data["breakdown"] == pytest.approx(
            {"Organic Cotton": 10, "Grid Power": 1.2, "Truck Freight": 1})
        assert "Catalog Cotton" not in data["breakdown"]

    def test_quantity_is_converted_to_the_factor_unit(self, client, product, factor):
        per_kg, per_kwh = factor("5", "kg"), factor("0.5", "kWh")
        data = _result(client, _calculate(client, product.id, [
            _row("Cotton in grams", 500, "g", "material", per_kg.id),
            _row("Heat in megajoules", 36, "MJ", "energy", per_kwh.id),
        ]))

        assert data["breakdown"] == pytest.approx({"Cotton in grams": 2.5, "Heat in megajoules": 5})
        assert data["total_co2e_kg"] == pytest.approx(7.5)

    def test_totals_follow_the_row_category_not_the_name(self, client, product, factor):
        ef = factor("1", "kg")
        data = _result(client, _calculate(client, product.id, [
            _row("Electricity Cable", 1, "kg", "material", ef.id),
            _row("Diesel", 2, "kg", "combustion", ef.id),
            _row("Packaging", 4, "kg", "other", ef.id),
            _row("Courier", 8, "kg", "transport", ef.id),
        ]))

        assert data["materials_co2e"] == pytest.approx(5)    # material + other
        assert data["energy_co2e"] == pytest.approx(2)       # combustion
        assert data["transport_co2e"] == pytest.approx(8)
        assert data["total_co2e_kg"] == pytest.approx(15)

    def test_without_bom_the_catalog_bom_is_used(self, client, product):
        data = _result(client, _calculate(client, product.id))

        assert data["total_co2e_kg"] == pytest.approx(5)
        assert data["breakdown"] == pytest.approx({"Catalog Cotton": 5})

    def test_submitted_rows_are_not_stored(self, client, db_session, product, factor):
        ef = factor("5", "kg")
        response = _calculate(client, product.id, [_row("Private Name", 1, "kg", "material", ef.id)])
        _result(client, response)

        row = db_session.query(PCFCalculation).filter_by(id=response.json()["calculation_id"]).one()
        db_session.refresh(row)
        stored = json.dumps([row.input_data, row.calculation_metadata], default=str)
        assert "Private Name" not in stored
        assert ef.id not in stored


class TestSubmittedBOMIsValidated:
    def test_unknown_emission_factor(self, client, product, factor):
        ok = factor("1", "kg")
        response = _calculate(client, product.id, [
            _row("Known", 1, "kg", "material", ok.id),
            _row("Unknown", 1, "kg", "material", _uid()),
        ])
        assert _fields(response) == ["body.bom.1.emission_factor_id"]

    def test_unit_of_another_kind_than_the_factor(self, client, product, factor):
        per_kg = factor("1", "kg")
        response = _calculate(client, product.id, [_row("Steel", 1, "kWh", "material", per_kg.id)])
        assert _fields(response) == ["body.bom.0.unit"]

    def test_duplicate_names_ignoring_case_and_spaces(self, client, product, factor):
        ef = factor("1", "kg")
        response = _calculate(client, product.id, [
            _row("Steel", 1, "kg", "material", ef.id),
            _row(" steel ", 2, "kg", "material", ef.id),
        ])
        assert _fields(response) == ["body.bom.1.name"]

    @pytest.mark.parametrize("ef_id", ["", None])
    def test_missing_emission_factor(self, client, product, ef_id):
        response = _calculate(client, product.id, [_row("No factor", 1, "kg", "material", ef_id)])
        assert _fields(response) == ["body.bom.0.emission_factor_id"]

    @pytest.mark.parametrize("quantity", [0, -1])
    def test_quantity_must_be_positive(self, client, product, factor, quantity):
        ef = factor("1", "kg")
        response = _calculate(client, product.id, [_row("Steel", quantity, "kg", "material", ef.id)])
        assert _fields(response) == ["body.bom.0.quantity"]

    def test_quantity_must_be_finite(self, client, product, factor):
        ef = factor("1", "kg")
        body = json.dumps({"product_id": product.id,
                           "bom": [_row("Steel", 1, "kg", "material", ef.id)]})
        body = body.replace('"quantity": 1', '"quantity": 1e400')  # parses as infinity
        response = client.post(CALCULATE, content=body, headers={"Content-Type": "application/json"})
        assert _fields(response) == ["body.bom.0.quantity"]

    def test_unknown_category(self, client, product, factor):
        ef = factor("1", "kg")
        response = _calculate(client, product.id, [_row("Steel", 1, "kg", "metal", ef.id)])
        assert _fields(response) == ["body.bom.0.category"]

    def test_blank_name(self, client, product, factor):
        ef = factor("1", "kg")
        response = _calculate(client, product.id, [_row("   ", 1, "kg", "material", ef.id)])
        assert _fields(response) == ["body.bom.0.name"]

    def test_empty_bom(self, client, product):
        response = _calculate(client, product.id, [])
        assert _fields(response) == ["body.bom"]

    def test_more_than_100_rows(self, client, product, factor):
        ef = factor("1", "kg")
        rows = [_row(f"Part {i}", 1, "kg", "material", ef.id) for i in range(101)]
        assert _fields(_calculate(client, product.id, rows)) == ["body.bom"]

    def test_100_rows_are_accepted(self, client, product, factor):
        ef = factor("1", "kg")
        rows = [_row(f"Part {i}", 1, "kg", "material", ef.id) for i in range(100)]
        data = _result(client, _calculate(client, product.id, rows))
        assert data["total_co2e_kg"] == pytest.approx(100)

    def test_an_invalid_bom_creates_no_calculation(self, client, db_session, product):
        before = db_session.query(PCFCalculation).count()
        _calculate(client, product.id, [_row("Unknown", 1, "kg", "material", _uid())])
        assert db_session.query(PCFCalculation).count() == before

    def test_unknown_product_is_still_404(self, client, factor):
        ef = factor("1", "kg")
        response = _calculate(client, _uid(), [_row("Steel", 1, "kg", "material", ef.id)])
        assert response.status_code == 404
