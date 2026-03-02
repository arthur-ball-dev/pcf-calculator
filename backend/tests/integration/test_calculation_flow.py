"""
Integration test for POST /calculate -> 202 -> poll flow.
TEST-003: Calculation integration test.
"""

import time
import pytest
from backend.models import Product, BillOfMaterials, EmissionFactor


@pytest.fixture
def seed_products(db_session):
    """Seed minimal product + BOM + emission factor for calculation tests."""
    ef = EmissionFactor(
        id="ef-steel-test",
        name="Steel Production",
        category="materials",
        factor_value=1.85,
        unit="kg CO2e/kg",
        source="test",
    )
    product = Product(
        id="prod-laptop-1",
        code="LAPTOP-001",
        name="Business Laptop 14-inch",
        unit="unit",
        category="electronics",
        is_finished_product=True,
    )
    component = Product(
        id="comp-steel-1",
        code="STEEL-001",
        name="Steel Chassis",
        unit="kg",
        category="material",
        is_finished_product=False,
    )
    db_session.add_all([ef, product, component])
    db_session.commit()

    bom = BillOfMaterials(
        parent_product_id="prod-laptop-1",
        child_product_id="comp-steel-1",
        quantity=2.0,
        unit="kg",
        emission_factor_id="ef-steel-test",
    )
    db_session.add(bom)
    db_session.commit()

    return {"product": product, "component": component, "bom": bom, "ef": ef}


@pytest.mark.integration
class TestCalculationFlow:
    """Test the full async calculation flow: POST -> 202 -> poll until done."""

    def test_calculate_and_poll_flow(self, authenticated_client, seed_products):
        """POST /calculate returns 202, polling yields completed result."""
        # Step 1: POST /calculate with a known product
        response = authenticated_client.post(
            "/api/v1/calculate",
            json={
                "product_id": "prod-laptop-1",
                "calculation_type": "cradle_to_gate"
            }
        )

        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"
        data = response.json()
        assert "calculation_id" in data
        assert data["status"] in ("pending", "in_progress")

        calc_id = data["calculation_id"]

        # Step 2: Poll until completed or failed (max 30 seconds)
        max_polls = 60
        poll_interval = 0.5
        final_status = None

        for _ in range(max_polls):
            poll_response = authenticated_client.get(f"/api/v1/calculations/{calc_id}")
            assert poll_response.status_code == 200

            poll_data = poll_response.json()
            final_status = poll_data.get("status")

            if final_status in ("completed", "failed"):
                break

            time.sleep(poll_interval)

        assert final_status is not None, (
            f"Calculation did not finish within {max_polls * poll_interval}s, status: {final_status}"
        )
        assert final_status == "completed", (
            f"Expected completed, got {final_status}. "
            f"Response: {poll_data}"
        )

    def test_calculate_nonexistent_product_returns_404(self, authenticated_client):
        """POST /calculate with nonexistent product returns 404."""
        response = authenticated_client.post(
            "/api/v1/calculate",
            json={
                "product_id": "nonexistent-product-id",
                "calculation_type": "cradle_to_gate"
            }
        )

        assert response.status_code == 404

    def test_calculate_invalid_type_returns_422(self, authenticated_client, seed_products):
        """POST /calculate with invalid calculation_type returns 422."""
        response = authenticated_client.post(
            "/api/v1/calculate",
            json={
                "product_id": "prod-laptop-1",
                "calculation_type": "invalid_type"
            }
        )

        assert response.status_code == 422
