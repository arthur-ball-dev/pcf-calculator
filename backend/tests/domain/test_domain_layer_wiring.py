"""
The domain layer running for real (issue #19).

Earlier tests used mocked sessions, which hid that the async repositories were handed
a sync session, and tests named "uses_service" only called the route. These use a real
session, or replace the service and check the route returned the replacement's data.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.api.dependencies import get_calculation_service, get_product_service
from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import CalculationNotFoundError, ProductNotFoundError
from backend.domain.entities.product import Product as DomainProduct
from backend.domain.services.calculation_service import CalculationService
from backend.domain.services.product_service import ProductService
from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
    SQLAlchemyCalculationRepository,
)
from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from backend.models import BillOfMaterials, PCFCalculation, Product

START = "/api/v1/calculate"
STATUS = "/api/v1/calculations/{}"


@pytest.fixture
def product(db_session):
    parent = Product(id="wire-parent", code="WIRE-P", name="Parent", unit="unit", is_finished_product=True)
    child = Product(id="wire-child", code="WIRE-C", name="Child", unit="kg", is_finished_product=False)
    db_session.add_all([parent, child])
    db_session.commit()
    db_session.add(
        BillOfMaterials(parent_product_id=parent.id, child_product_id=child.id, quantity=0.25, unit="kg")
    )
    db_session.commit()
    return parent


def _store_calculation(db_session, product, **fields):
    defaults = {
        "id": "wire-calc",
        "product_id": product.id,
        "calculation_type": "cradle_to_gate",
        "status": "completed",
        "total_co2e_kg": 1.5,
    }
    calculation = PCFCalculation(**{**defaults, **fields})
    db_session.add(calculation)
    db_session.commit()
    return calculation


class TestRepositoriesOnARealSession:
    def test_product_get_by_id(self, db_session, product):
        found = SQLAlchemyProductRepository(db_session).get_by_id(product.id)

        assert isinstance(found, DomainProduct)
        assert found.code == "WIRE-P"

    def test_product_get_by_id_missing(self, db_session):
        assert SQLAlchemyProductRepository(db_session).get_by_id("wire-none") is None

    def test_product_list_all(self, db_session, product):
        found = SQLAlchemyProductRepository(db_session).list_all(limit=1000)

        assert {"wire-parent", "wire-child"} <= {p.id for p in found.items}

    def test_product_get_with_bom(self, db_session, product):
        found = SQLAlchemyProductRepository(db_session).get_with_bom(product.id)

        assert [item.component_id for item in found.bom_items] == ["wire-child"]
        assert found.bom_items[0].quantity == 0.25

    def test_calculation_create_stores_a_pending_row(self, db_session, product):
        result = SQLAlchemyCalculationRepository(db_session).create(
            CreateCalculationRequest(product_id=product.id, calculation_type="gate_to_gate")
        )

        row = db_session.get(PCFCalculation, result.id)
        assert result.status == "pending"
        assert row.status == "pending"
        assert row.calculation_type == "gate_to_gate"
        assert row.created_at is not None

    def test_calculation_get_by_id_maps_results(self, db_session, product):
        _store_calculation(
            db_session, product, materials_co2e=0, energy_co2e=0.5,
            breakdown={"steel": 1.5}, calculation_time_ms=12,
        )

        found = SQLAlchemyCalculationRepository(db_session).get_by_id("wire-calc")

        assert found.total_co2e_kg == 1.5
        assert found.materials_co2e == 0.0
        assert found.transport_co2e is None
        assert found.breakdown == {"steel": 1.5}
        assert found.calculation_time_ms == 12

    def test_calculation_get_by_id_missing(self, db_session):
        assert SQLAlchemyCalculationRepository(db_session).get_by_id("wire-none") is None

    @pytest.mark.parametrize(
        "stored, expected",
        [
            ({"calculation_metadata": {"error_message": "meta"}}, "meta"),
            ({"input_data": {"error_message": "input"}}, "input"),
            (
                {
                    "calculation_metadata": {"error_message": "meta"},
                    "input_data": {"error_message": "input"},
                },
                "meta",
            ),
            ({"calculation_metadata": {"other": 1}, "input_data": {"error_message": "input"}}, "input"),
            ({}, None),
        ],
    )
    def test_calculation_error_message(self, db_session, product, stored, expected):
        _store_calculation(db_session, product, status="failed", **stored)

        found = SQLAlchemyCalculationRepository(db_session).get_by_id("wire-calc")

        assert found.error_message == expected


class TestProvidersBuildWorkingServices:
    """The defect behind #19: these providers built services that failed on first use."""

    def _calculation_service(self, db_session):
        return get_calculation_service(
            SQLAlchemyCalculationRepository(db_session), SQLAlchemyProductRepository(db_session)
        )

    def test_product_service(self, db_session, product):
        service = get_product_service(SQLAlchemyProductRepository(db_session))

        assert isinstance(service, ProductService)
        assert service.get_product(product.id).id == product.id

    def test_calculation_service_round_trip(self, db_session, product):
        service = self._calculation_service(db_session)
        assert isinstance(service, CalculationService)

        created = service.create_calculation(
            CreateCalculationRequest(product_id=product.id, calculation_type="cradle_to_gate")
        )

        assert service.get_calculation(created.id).status == "pending"

    def test_calculation_service_rejects_a_missing_product(self, db_session):
        with pytest.raises(ProductNotFoundError):
            self._calculation_service(db_session).create_calculation(
                CreateCalculationRequest(product_id="wire-none", calculation_type="cradle_to_gate")
            )


class TestCalculationRoutesUseTheService:
    @pytest.fixture
    def service(self, client):
        from backend.main import app

        fake = MagicMock(spec=CalculationService)
        app.dependency_overrides[get_calculation_service] = lambda: fake
        return fake

    def test_status_comes_from_the_service(self, client, service):
        service.get_calculation.return_value = Calculation(
            id="only-in-fake",
            product_id="fake-product",
            total_co2e_kg=7.5,
            status="completed",
            materials_co2e=0.0,
            breakdown={"steel": 7.5},
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        response = client.get(STATUS.format("only-in-fake"))

        assert response.status_code == 200
        body = response.json()
        assert body["calculation_id"] == "only-in-fake"
        assert body["total_co2e_kg"] == 7.5
        assert body["materials_co2e"] == 0.0
        assert body["breakdown"] == {"steel": 7.5}
        service.get_calculation.assert_called_once_with("only-in-fake")

    @pytest.mark.parametrize("stored", ["running", "processing"])
    def test_working_states_are_reported_as_in_progress(self, client, service, stored):
        service.get_calculation.return_value = Calculation(
            id="c", product_id="p", total_co2e_kg=0.0, status=stored
        )

        body = client.get(STATUS.format("c")).json()

        assert body["status"] == "in_progress"
        assert "total_co2e_kg" not in body or body["total_co2e_kg"] is None

    def test_failed_without_a_stored_message(self, client, service):
        service.get_calculation.return_value = Calculation(
            id="c", product_id="p", total_co2e_kg=0.0, status="failed"
        )

        assert client.get(STATUS.format("c")).json()["error_message"] == "Calculation failed"

    def test_missing_calculation_is_404(self, client, service):
        service.get_calculation.side_effect = CalculationNotFoundError(calculation_id="c")

        response = client.get(STATUS.format("c"))

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CALCULATION_NOT_FOUND"

    def test_start_returns_the_service_id_and_queues_the_run(self, client, service):
        service.create_calculation.return_value = CalculationResult(
            id="fake-id", status="pending", product_id="fake-product"
        )

        with patch("backend.api.routes.calculations.execute_calculation") as run:
            response = client.post(
                START, json={"product_id": "fake-product", "calculation_type": "gate_to_gate"}
            )

        assert response.status_code == 202
        assert response.json() == {"calculation_id": "fake-id", "status": "in_progress"}
        request = service.create_calculation.call_args.args[0]
        assert request == CreateCalculationRequest(
            product_id="fake-product", calculation_type="gate_to_gate"
        )
        assert run.call_args.args[:3] == ("fake-id", "fake-product", "gate_to_gate")

    def test_start_for_a_missing_product_is_404(self, client, service):
        service.create_calculation.side_effect = ProductNotFoundError(product_id="p")

        response = client.post(START, json={"product_id": "p"})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    def test_start_failure_is_500_and_queues_nothing(self, client, service):
        service.create_calculation.side_effect = RuntimeError("database down")

        with patch("backend.api.routes.calculations.execute_calculation") as run:
            response = client.post(START, json={"product_id": "p"})

        assert response.status_code == 500
        assert response.json()["error"]["message"] == "Failed to start calculation"
        run.assert_not_called()


class TestPublicStatus:
    @pytest.mark.parametrize(
        "stored, shown",
        [
            ("pending", "pending"),
            ("running", "in_progress"),
            ("processing", "in_progress"),
            ("completed", "completed"),
            ("failed", "failed"),
        ],
    )
    def test_mapping(self, stored, shown):
        calculation = Calculation(id="c", product_id="p", total_co2e_kg=0.0, status=stored)

        assert calculation.public_status == shown
