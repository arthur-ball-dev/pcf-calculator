"""
Test suite for API contract validation.

TASK-DB-P5-001: PostgreSQL Migration - Contract Tests

This test suite validates that API response structures remain unchanged
after the PostgreSQL migration, ensuring 100% backward compatibility
with existing MVP functionality.

Contract Tests Validate:
- GET /api/v1/products response structure unchanged
- GET /api/v1/emission-factors response structure unchanged
- POST /api/v1/calculate response structure unchanged
- All existing API responses backward compatible

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests define the expected response contracts
- Implementation must preserve these contracts exactly
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from decimal import Decimal

from backend.models import (
    Base,
    Product,
    BillOfMaterials,
    EmissionFactor,
    PCFCalculation,
)
from backend.main import app
from backend.database.connection import get_db


# Mark all tests in this module as contract tests
pytestmark = pytest.mark.contracts


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for contract testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for contract testing."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create FastAPI TestClient with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_contract_data(db_session):
    """
    Seed database with known data for contract testing.

    Creates a representative set of data that exercises all response fields.
    """
    # Create products
    finished_product = Product(
        id="contract-prod-001",
        code="CONTRACT-FP-001",
        name="Contract Test Finished Product",
        description="A finished product for contract testing",
        unit="unit",
        category="contract-test",
        is_finished_product=True,
    )

    component = Product(
        id="contract-comp-001",
        code="CONTRACT-COMP-001",
        name="Contract Test Component",
        description="A component for contract testing",
        unit="kg",
        category="material",
        is_finished_product=False,
    )

    db_session.add_all([finished_product, component])
    db_session.commit()

    # Create BOM relationship
    bom = BillOfMaterials(
        id="contract-bom-001",
        parent_product_id="contract-prod-001",
        child_product_id="contract-comp-001",
        quantity=Decimal("2.5"),
        unit="kg",
        notes="Contract test BOM entry",
    )
    db_session.add(bom)
    db_session.commit()

    # Create emission factor
    emission_factor = EmissionFactor(
        id="contract-ef-001",
        activity_name="Contract Test Material",
        category="material",
        co2e_factor=Decimal("5.25"),
        unit="kg",
        data_source="CONTRACT",
        geography="GLO",
        reference_year=2024,
        data_quality_rating=Decimal("0.85"),
    )
    db_session.add(emission_factor)
    db_session.commit()

    # Create completed calculation
    calculation = PCFCalculation(
        id="contract-calc-001",
        product_id="contract-prod-001",
        calculation_type="cradle_to_gate",
        status="completed",
        total_co2e_kg=Decimal("12.50"),
        materials_co2e=Decimal("10.00"),
        energy_co2e=Decimal("1.50"),
        transport_co2e=Decimal("1.00"),
        calculation_time_ms=150,
        calculation_method="contract_test",
    )
    db_session.add(calculation)
    db_session.commit()

    return {
        "finished_product": finished_product,
        "component": component,
        "bom": bom,
        "emission_factor": emission_factor,
        "calculation": calculation,
    }


class TestProductsListContract:
    """
    Contract tests for GET /api/v1/products response structure.

    These tests validate that the response structure matches the
    documented API specification and MVP behavior.
    """

    def test_products_list_response_has_required_top_level_fields(
        self, client, seed_contract_data
    ):
        """
        Verify products list response has all required top-level fields.

        Contract: Response MUST contain 'items', 'total', 'limit', 'offset'
        """
        response = client.get("/api/v1/products")
        data = response.json()

        required_fields = ["items", "total", "limit", "offset"]
        for field in required_fields:
            assert field in data, \
                f"Contract violation: '{field}' missing from products list response"

    def test_products_list_items_type_is_array(self, client, seed_contract_data):
        """
        Verify 'items' field is an array.

        Contract: 'items' MUST be an array, even if empty
        """
        response = client.get("/api/v1/products")
        data = response.json()

        assert isinstance(data["items"], list), \
            "Contract violation: 'items' must be an array"

    def test_products_list_pagination_fields_are_integers(
        self, client, seed_contract_data
    ):
        """
        Verify pagination fields are integers.

        Contract: 'total', 'limit', 'offset' MUST be integers
        """
        response = client.get("/api/v1/products")
        data = response.json()

        assert isinstance(data["total"], int), \
            "Contract violation: 'total' must be an integer"
        assert isinstance(data["limit"], int), \
            "Contract violation: 'limit' must be an integer"
        assert isinstance(data["offset"], int), \
            "Contract violation: 'offset' must be an integer"

    def test_products_list_item_has_required_fields(
        self, client, seed_contract_data
    ):
        """
        Verify each product item has all required fields.

        Contract: Each item MUST have:
        - id (string)
        - code (string)
        - name (string)
        - unit (string)
        - category (string or null)
        - is_finished_product (boolean)
        - created_at (string, ISO 8601 datetime)
        """
        response = client.get("/api/v1/products")
        data = response.json()

        assert len(data["items"]) > 0, "Need at least one product to test"

        for item in data["items"]:
            # Required fields
            assert "id" in item, "Contract violation: 'id' required in product item"
            assert "code" in item, "Contract violation: 'code' required in product item"
            assert "name" in item, "Contract violation: 'name' required in product item"
            assert "unit" in item, "Contract violation: 'unit' required in product item"
            assert "is_finished_product" in item, \
                "Contract violation: 'is_finished_product' required in product item"
            assert "created_at" in item, \
                "Contract violation: 'created_at' required in product item"

            # Type validation
            assert isinstance(item["id"], str), \
                "Contract violation: 'id' must be a string"
            assert isinstance(item["code"], str), \
                "Contract violation: 'code' must be a string"
            assert isinstance(item["name"], str), \
                "Contract violation: 'name' must be a string"
            assert isinstance(item["unit"], str), \
                "Contract violation: 'unit' must be a string"
            assert isinstance(item["is_finished_product"], bool), \
                "Contract violation: 'is_finished_product' must be a boolean"
            assert isinstance(item["created_at"], str), \
                "Contract violation: 'created_at' must be a string"

    def test_products_list_category_can_be_null(self, client, db_session):
        """
        Verify category field can be null.

        Contract: 'category' MAY be null for products without category
        """
        # Create product without category
        product = Product(
            id="no-category-001",
            code="NO-CAT-001",
            name="No Category Product",
            unit="unit",
            category=None,
            is_finished_product=True,
        )
        db_session.add(product)
        db_session.commit()

        response = client.get("/api/v1/products")
        data = response.json()

        # Find our test product
        test_product = next(
            (p for p in data["items"] if p["id"] == "no-category-001"),
            None
        )
        assert test_product is not None, "Test product should exist"
        # Category should be present (as key) but value can be null
        assert "category" in test_product, \
            "Contract violation: 'category' field must be present"


class TestProductDetailContract:
    """
    Contract tests for GET /api/v1/products/{id} response structure.
    """

    def test_product_detail_has_required_fields(self, client, seed_contract_data):
        """
        Verify product detail response has all required fields.

        Contract: Response MUST contain all product list fields plus:
        - description (string or null)
        - bill_of_materials (array)
        """
        response = client.get("/api/v1/products/contract-prod-001")
        data = response.json()

        required_fields = [
            "id", "code", "name", "unit", "category",
            "is_finished_product", "created_at",
            "description", "bill_of_materials"
        ]

        for field in required_fields:
            assert field in data, \
                f"Contract violation: '{field}' missing from product detail response"

    def test_product_detail_bom_is_array(self, client, seed_contract_data):
        """
        Verify bill_of_materials is an array.

        Contract: 'bill_of_materials' MUST be an array, even if empty
        """
        response = client.get("/api/v1/products/contract-prod-001")
        data = response.json()

        assert isinstance(data["bill_of_materials"], list), \
            "Contract violation: 'bill_of_materials' must be an array"

    def test_product_detail_bom_item_structure(self, client, seed_contract_data):
        """
        Verify BOM item has required structure.

        Contract: Each BOM item MUST have:
        - id (string)
        - child_product_id (string)
        - child_product_name (string)
        - quantity (number)
        - unit (string or null)
        """
        response = client.get("/api/v1/products/contract-prod-001")
        data = response.json()

        bom = data["bill_of_materials"]
        assert len(bom) > 0, "Need BOM items to test"

        for item in bom:
            assert "id" in item, \
                "Contract violation: 'id' required in BOM item"
            assert "child_product_id" in item, \
                "Contract violation: 'child_product_id' required in BOM item"
            assert "child_product_name" in item, \
                "Contract violation: 'child_product_name' required in BOM item"
            assert "quantity" in item, \
                "Contract violation: 'quantity' required in BOM item"

            # Type validation
            assert isinstance(item["id"], str), \
                "Contract violation: BOM 'id' must be a string"
            assert isinstance(item["child_product_id"], str), \
                "Contract violation: 'child_product_id' must be a string"
            assert isinstance(item["child_product_name"], str), \
                "Contract violation: 'child_product_name' must be a string"
            assert isinstance(item["quantity"], (int, float)), \
                "Contract violation: 'quantity' must be numeric"

    def test_product_detail_not_found_returns_404(self, client, seed_contract_data):
        """
        Verify 404 response for non-existent product.

        Contract: Non-existent product MUST return 404 with 'detail' field
        """
        response = client.get("/api/v1/products/non-existent-id")

        assert response.status_code == 404, \
            "Contract violation: Non-existent product must return 404"

        data = response.json()
        assert "detail" in data, \
            "Contract violation: 404 response must contain 'detail' field"
        assert isinstance(data["detail"], str), \
            "Contract violation: 'detail' must be a string"


class TestEmissionFactorsListContract:
    """
    Contract tests for GET /api/v1/emission-factors response structure.
    """

    def test_emission_factors_list_response_structure(
        self, client, seed_contract_data
    ):
        """
        Verify emission factors list response has required structure.

        Contract: Response MUST contain 'items', 'total', 'limit', 'offset'
        """
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        required_fields = ["items", "total", "limit", "offset"]
        for field in required_fields:
            assert field in data, \
                f"Contract violation: '{field}' missing from emission factors response"

        assert isinstance(data["items"], list), \
            "Contract violation: 'items' must be an array"
        assert isinstance(data["total"], int), \
            "Contract violation: 'total' must be an integer"
        assert isinstance(data["limit"], int), \
            "Contract violation: 'limit' must be an integer"
        assert isinstance(data["offset"], int), \
            "Contract violation: 'offset' must be an integer"

    def test_emission_factor_item_has_required_fields(
        self, client, seed_contract_data
    ):
        """
        Verify emission factor item has all required fields.

        Contract: Each item MUST have:
        - id (string)
        - activity_name (string)
        - co2e_factor (number)
        - unit (string)
        - data_source (string)
        - geography (string)
        - created_at (string)
        """
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert len(data["items"]) > 0, "Need at least one emission factor to test"

        for item in data["items"]:
            # Required fields
            required_fields = [
                "id", "activity_name", "co2e_factor", "unit",
                "data_source", "geography", "created_at"
            ]
            for field in required_fields:
                assert field in item, \
                    f"Contract violation: '{field}' required in emission factor item"

            # Type validation
            assert isinstance(item["id"], str), \
                "Contract violation: 'id' must be a string"
            assert isinstance(item["activity_name"], str), \
                "Contract violation: 'activity_name' must be a string"
            assert isinstance(item["co2e_factor"], (int, float)), \
                "Contract violation: 'co2e_factor' must be numeric"
            assert isinstance(item["unit"], str), \
                "Contract violation: 'unit' must be a string"
            assert isinstance(item["data_source"], str), \
                "Contract violation: 'data_source' must be a string"
            assert isinstance(item["geography"], str), \
                "Contract violation: 'geography' must be a string"
            assert isinstance(item["created_at"], str), \
                "Contract violation: 'created_at' must be a string"

    def test_emission_factor_optional_fields(self, client, seed_contract_data):
        """
        Verify emission factor optional fields can be null.

        Contract: These fields MAY be null:
        - category
        - reference_year
        - data_quality_rating
        """
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        # These fields should be present (as keys) but may be null
        optional_fields = ["category", "reference_year", "data_quality_rating"]

        for item in data["items"]:
            for field in optional_fields:
                assert field in item, \
                    f"Contract violation: '{field}' field must be present (even if null)"


class TestCalculateContract:
    """
    Contract tests for POST /api/v1/calculate response structure.
    """

    def test_calculate_start_response_structure(self, client, seed_contract_data):
        """
        Verify calculation start response has required structure.

        Contract: Response MUST contain:
        - calculation_id (string)
        - status (string, value="processing")
        Response status code MUST be 202 Accepted
        """
        response = client.post(
            "/api/v1/calculate",
            json={
                "product_id": "contract-prod-001",
                "calculation_type": "cradle_to_gate"
            }
        )

        assert response.status_code == 202, \
            "Contract violation: POST /calculate must return 202 Accepted"

        data = response.json()

        assert "calculation_id" in data, \
            "Contract violation: 'calculation_id' required in calculate response"
        assert "status" in data, \
            "Contract violation: 'status' required in calculate response"

        assert isinstance(data["calculation_id"], str), \
            "Contract violation: 'calculation_id' must be a string"
        assert isinstance(data["status"], str), \
            "Contract violation: 'status' must be a string"
        assert data["status"] == "processing", \
            "Contract violation: Initial status must be 'processing'"

    def test_calculate_invalid_request_returns_422(self, client, seed_contract_data):
        """
        Verify invalid request returns 422.

        Contract: Missing required fields MUST return 422 with error details
        """
        response = client.post(
            "/api/v1/calculate",
            json={}  # Missing required product_id
        )

        assert response.status_code == 422, \
            "Contract violation: Invalid request must return 422"

        data = response.json()
        assert "detail" in data, \
            "Contract violation: 422 response must contain 'detail' field"


class TestCalculationStatusContract:
    """
    Contract tests for GET /api/v1/calculations/{id} response structure.
    """

    def test_calculation_status_completed_structure(
        self, client, seed_contract_data
    ):
        """
        Verify completed calculation response has required structure.

        Contract: Completed response MUST contain:
        - calculation_id (string)
        - status (string, value="completed")
        - product_id (string)
        - created_at (string or null)
        - total_co2e_kg (number)
        - calculation_time_ms (number or null)

        Optional when completed:
        - materials_co2e (number or null)
        - energy_co2e (number or null)
        - transport_co2e (number or null)
        """
        response = client.get("/api/v1/calculations/contract-calc-001")

        assert response.status_code == 200, \
            "Contract violation: Existing calculation must return 200"

        data = response.json()

        # Required fields
        assert "calculation_id" in data, \
            "Contract violation: 'calculation_id' required"
        assert "status" in data, \
            "Contract violation: 'status' required"
        assert "product_id" in data, \
            "Contract violation: 'product_id' required"

        # Type validation
        assert isinstance(data["calculation_id"], str), \
            "Contract violation: 'calculation_id' must be a string"
        assert isinstance(data["status"], str), \
            "Contract violation: 'status' must be a string"
        assert isinstance(data["product_id"], str), \
            "Contract violation: 'product_id' must be a string"

        # Completed-specific fields
        if data["status"] == "completed":
            assert "total_co2e_kg" in data, \
                "Contract violation: 'total_co2e_kg' required when completed"
            assert isinstance(data["total_co2e_kg"], (int, float)), \
                "Contract violation: 'total_co2e_kg' must be numeric"

    def test_calculation_status_not_found_returns_404(
        self, client, seed_contract_data
    ):
        """
        Verify 404 response for non-existent calculation.

        Contract: Non-existent calculation MUST return 404 with 'detail' field
        """
        response = client.get("/api/v1/calculations/non-existent-calc-id")

        assert response.status_code == 404, \
            "Contract violation: Non-existent calculation must return 404"

        data = response.json()
        assert "detail" in data, \
            "Contract violation: 404 response must contain 'detail' field"

    def test_calculation_status_valid_status_values(
        self, client, seed_contract_data
    ):
        """
        Verify status field has valid value.

        Contract: 'status' MUST be one of:
        - "pending"
        - "processing"
        - "running"
        - "completed"
        - "failed"
        """
        response = client.get("/api/v1/calculations/contract-calc-001")
        data = response.json()

        valid_statuses = ["pending", "processing", "running", "completed", "failed"]
        assert data["status"] in valid_statuses, \
            f"Contract violation: 'status' must be one of {valid_statuses}, " \
            f"got '{data['status']}'"


class TestAPIResponseConsistency:
    """
    Contract tests for consistent API response behavior.
    """

    def test_all_list_endpoints_use_pagination_format(self, client, seed_contract_data):
        """
        Verify all list endpoints use consistent pagination format.

        Contract: All list endpoints MUST use the same pagination structure:
        {items: [], total: int, limit: int, offset: int}
        """
        list_endpoints = [
            "/api/v1/products",
            "/api/v1/emission-factors",
        ]

        for endpoint in list_endpoints:
            response = client.get(endpoint)
            data = response.json()

            assert "items" in data, \
                f"Contract violation: {endpoint} missing 'items'"
            assert "total" in data, \
                f"Contract violation: {endpoint} missing 'total'"
            assert "limit" in data, \
                f"Contract violation: {endpoint} missing 'limit'"
            assert "offset" in data, \
                f"Contract violation: {endpoint} missing 'offset'"

    def test_all_404_responses_have_detail_field(self, client, seed_contract_data):
        """
        Verify all 404 responses use consistent format.

        Contract: All 404 responses MUST contain 'detail' field with string value
        """
        not_found_endpoints = [
            "/api/v1/products/non-existent",
            "/api/v1/calculations/non-existent",
        ]

        for endpoint in not_found_endpoints:
            response = client.get(endpoint)

            assert response.status_code == 404, \
                f"Expected 404 for {endpoint}"

            data = response.json()
            assert "detail" in data, \
                f"Contract violation: {endpoint} 404 response missing 'detail'"
            assert isinstance(data["detail"], str), \
                f"Contract violation: {endpoint} 'detail' must be string"

    def test_datetime_fields_are_iso8601_format(self, client, seed_contract_data):
        """
        Verify datetime fields use ISO 8601 format.

        Contract: All datetime fields MUST be ISO 8601 formatted strings
        """
        # Test products
        response = client.get("/api/v1/products")
        data = response.json()

        for item in data["items"]:
            created_at = item.get("created_at")
            if created_at:
                # Should be parseable as ISO 8601
                try:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    pytest.fail(
                        f"Contract violation: 'created_at' not ISO 8601: {created_at}"
                    )

        # Test emission factors
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        for item in data["items"]:
            created_at = item.get("created_at")
            if created_at:
                try:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    pytest.fail(
                        f"Contract violation: 'created_at' not ISO 8601: {created_at}"
                    )

    def test_numeric_fields_are_not_strings(self, client, seed_contract_data):
        """
        Verify numeric fields are actual numbers, not strings.

        Contract: Numeric fields MUST be JSON numbers, not quoted strings
        """
        # Test emission factors
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        for item in data["items"]:
            co2e_factor = item.get("co2e_factor")
            assert not isinstance(co2e_factor, str), \
                f"Contract violation: 'co2e_factor' must be number, not string"

        # Test products (BOM quantities)
        response = client.get("/api/v1/products/contract-prod-001")
        data = response.json()

        for bom_item in data.get("bill_of_materials", []):
            quantity = bom_item.get("quantity")
            assert not isinstance(quantity, str), \
                f"Contract violation: BOM 'quantity' must be number, not string"


class TestPaginationContract:
    """
    Contract tests for pagination behavior.
    """

    def test_pagination_limit_parameter_respected(self, client, db_session):
        """
        Verify limit parameter is respected.

        Contract: 'limit' parameter MUST limit the number of items returned
        """
        # Create multiple products
        for i in range(5):
            product = Product(
                id=f"page-test-{i}",
                code=f"PAGE-{i:03d}",
                name=f"Pagination Test {i}",
                unit="unit",
                is_finished_product=True,
            )
            db_session.add(product)
        db_session.commit()

        response = client.get("/api/v1/products?limit=2")
        data = response.json()

        assert len(data["items"]) <= 2, \
            "Contract violation: 'limit' must restrict item count"
        assert data["limit"] == 2, \
            "Contract violation: Response 'limit' must match request"

    def test_pagination_offset_parameter_respected(self, client, db_session):
        """
        Verify offset parameter is respected.

        Contract: 'offset' parameter MUST skip the specified number of items
        """
        # Create products with predictable order
        for i in range(5):
            product = Product(
                id=f"offset-test-{i}",
                code=f"OFFSET-{i:03d}",
                name=f"Offset Test {i}",
                unit="unit",
                is_finished_product=True,
            )
            db_session.add(product)
        db_session.commit()

        response = client.get("/api/v1/products?offset=2")
        data = response.json()

        assert data["offset"] == 2, \
            "Contract violation: Response 'offset' must match request"

    def test_pagination_total_reflects_full_count(self, client, db_session):
        """
        Verify total reflects full count regardless of pagination.

        Contract: 'total' MUST reflect total matching items, not paginated count
        """
        # Create multiple products
        for i in range(10):
            product = Product(
                id=f"total-test-{i}",
                code=f"TOTAL-{i:03d}",
                name=f"Total Test {i}",
                unit="unit",
                is_finished_product=True,
            )
            db_session.add(product)
        db_session.commit()

        response = client.get("/api/v1/products?limit=3")
        data = response.json()

        assert data["total"] >= 10, \
            "Contract violation: 'total' must reflect full count"
        assert len(data["items"]) == 3, \
            "Contract violation: Items should be limited to 3"
