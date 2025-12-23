"""
API Contract Alignment Tests

TASK-API-P7-027: Tests to verify API response contracts align between backend and frontend.

These tests specifically check for the contract mismatches identified in code review:
- P1 #18: Calculation status values ("running"/"processing" vs "in_progress")
- P1 #19: ProductSearchItem.category type (object vs string)

These tests are written FIRST per TDD methodology and MUST FAIL initially,
confirming the contract mismatches exist before fixes are implemented.

Contract Requirements (from frontend types):
- CalculationStatus: 'pending' | 'in_progress' | 'completed' | 'failed'
- ProductSearchItem.category: string (not object)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from decimal import Decimal

from backend.models import Base, Product, PCFCalculation
from backend.main import app
from backend.database.connection import get_db
from backend.schemas import CalculationStartResponse, CalculationStatusResponse
from backend.schemas.products import ProductSearchItem


# Mark all tests in this module as contract alignment tests
pytestmark = [pytest.mark.contracts, pytest.mark.api_alignment]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
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
    """Create database session for testing."""
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
def seed_test_data(db_session):
    """Seed database with test data for contract alignment tests."""
    # Create a finished product for calculation tests
    product = Product(
        id="alignment-test-prod-001",
        code="ALIGN-FP-001",
        name="Contract Alignment Test Product",
        description="A product for contract alignment testing",
        unit="unit",
        category="electronics",
        is_finished_product=True,
    )
    db_session.add(product)
    db_session.commit()

    # Create calculations with different statuses for status contract testing
    # Note: PCFCalculation.total_co2e_kg is required, so we provide default values
    pending_calc = PCFCalculation(
        id="alignment-calc-pending",
        product_id="alignment-test-prod-001",
        calculation_type="cradle_to_gate",
        status="pending",
        total_co2e_kg=Decimal("0.00"),  # Required field
    )

    # Note: Backend may use "processing" or "running" which differs from frontend's "in_progress"
    processing_calc = PCFCalculation(
        id="alignment-calc-processing",
        product_id="alignment-test-prod-001",
        calculation_type="cradle_to_gate",
        status="processing",  # Backend uses "processing", frontend expects "in_progress"
        total_co2e_kg=Decimal("0.00"),  # Required field
    )

    completed_calc = PCFCalculation(
        id="alignment-calc-completed",
        product_id="alignment-test-prod-001",
        calculation_type="cradle_to_gate",
        status="completed",
        total_co2e_kg=Decimal("5.50"),
        materials_co2e=Decimal("4.00"),
        energy_co2e=Decimal("1.00"),
        transport_co2e=Decimal("0.50"),
        calculation_time_ms=200,
    )

    # Note: PCFCalculation model doesn't have error_message field - status alone indicates failure
    failed_calc = PCFCalculation(
        id="alignment-calc-failed",
        product_id="alignment-test-prod-001",
        calculation_type="cradle_to_gate",
        status="failed",
        total_co2e_kg=Decimal("0.00"),  # Required field
    )

    db_session.add_all([pending_calc, processing_calc, completed_calc, failed_calc])
    db_session.commit()

    return {
        "product": product,
        "pending_calc": pending_calc,
        "processing_calc": processing_calc,
        "completed_calc": completed_calc,
        "failed_calc": failed_calc,
    }


# =============================================================================
# Calculation Status Contract Alignment Tests
# =============================================================================

class TestCalculationStatusContractAlignment:
    """
    Tests ensuring calculation status values match frontend expectations.

    Frontend expects: 'pending' | 'in_progress' | 'completed' | 'failed'

    These tests verify the backend returns EXACTLY these values, not alternatives
    like 'running' or 'processing'.
    """

    # The exact status values expected by the frontend
    VALID_FRONTEND_STATUSES = ["pending", "in_progress", "completed", "failed"]

    def test_calculation_start_status_matches_frontend_contract(
        self, client, seed_test_data
    ):
        """
        Verify POST /calculate returns status that matches frontend contract.

        Contract Requirement:
        - Initial status MUST be one of: 'pending', 'in_progress', 'completed', 'failed'
        - NOT 'processing' or 'running'

        This test MUST FAIL if backend returns 'processing' (the current behavior).
        """
        response = client.post(
            "/api/v1/calculate",
            json={
                "product_id": "alignment-test-prod-001",
                "calculation_type": "cradle_to_gate"
            }
        )

        assert response.status_code in [200, 202], \
            f"Expected 200 or 202, got {response.status_code}"

        data = response.json()
        status = data.get("status")

        # This assertion will FAIL if backend returns "processing" instead of
        # a frontend-compatible status
        assert status in self.VALID_FRONTEND_STATUSES, \
            f"Contract Violation: Status '{status}' not in valid frontend values: " \
            f"{self.VALID_FRONTEND_STATUSES}. " \
            f"Backend is returning '{status}' but frontend expects one of " \
            f"'pending', 'in_progress', 'completed', or 'failed'."

    def test_calculation_status_response_matches_frontend_contract(
        self, client, seed_test_data
    ):
        """
        Verify GET /calculations/{id} returns status matching frontend contract.

        Contract Requirement:
        - status MUST be one of: 'pending', 'in_progress', 'completed', 'failed'
        - NOT 'processing' or 'running'

        Tests all seeded calculation statuses to ensure alignment.
        """
        calc_ids = [
            "alignment-calc-pending",
            "alignment-calc-processing",
            "alignment-calc-completed",
            "alignment-calc-failed",
        ]

        for calc_id in calc_ids:
            response = client.get(f"/api/v1/calculations/{calc_id}")

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                # This assertion will FAIL for "alignment-calc-processing" because
                # backend stores "processing" but frontend expects "in_progress"
                assert status in self.VALID_FRONTEND_STATUSES, \
                    f"Contract Violation: Calculation {calc_id} has status '{status}' " \
                    f"which is not in valid frontend values: {self.VALID_FRONTEND_STATUSES}. " \
                    f"Backend must return 'in_progress' instead of 'processing' or 'running'."

    def test_backend_schema_uses_frontend_compatible_status_enum(self):
        """
        Verify CalculationStartResponse schema uses frontend-compatible status values.

        Contract Requirement:
        - Backend Pydantic schema should use an enum with exactly the frontend values.

        This test checks the schema directly, not via API, to catch definition issues.
        """
        # Get the schema's JSON representation
        schema = CalculationStartResponse.model_json_schema()

        # Check if status field has proper enum definition
        # Note: This will vary based on how the schema is defined
        # If status is just 'str', we expect the API to use proper values
        status_schema = schema.get("properties", {}).get("status", {})

        # The description or example should indicate proper values
        # This test documents the expectation that status should be constrained
        example = schema.get("examples", [{}])[0] if "examples" in schema else {}
        if not example:
            example = schema.get("json_schema_extra", {}).get("example", {})

        if example and "status" in example:
            example_status = example["status"]
            # The example should use a frontend-compatible value
            assert example_status in self.VALID_FRONTEND_STATUSES, \
                f"Contract Violation: Schema example uses status '{example_status}' " \
                f"which is not frontend-compatible. Expected one of: {self.VALID_FRONTEND_STATUSES}"

    def test_no_running_status_returned_by_api(self, client, seed_test_data):
        """
        Verify the API never returns 'running' status.

        The frontend does not recognize 'running' - it expects 'in_progress'.
        """
        # Create a new calculation
        response = client.post(
            "/api/v1/calculate",
            json={
                "product_id": "alignment-test-prod-001",
                "calculation_type": "cradle_to_gate"
            }
        )

        data = response.json()
        calc_id = data.get("calculation_id")

        # Check the initial response
        assert data.get("status") != "running", \
            "Contract Violation: API returned 'running' status. " \
            "Frontend expects 'in_progress' for calculations that are executing."

        # Also check the status endpoint if we got a calc_id
        if calc_id:
            status_response = client.get(f"/api/v1/calculations/{calc_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                assert status_data.get("status") != "running", \
                    "Contract Violation: Calculation status endpoint returned 'running'. " \
                    "Frontend expects 'in_progress'."

    def test_no_processing_status_returned_by_api(self, client, seed_test_data):
        """
        Verify the API never returns 'processing' status.

        The frontend does not recognize 'processing' - it expects 'in_progress'.
        """
        # Create a new calculation
        response = client.post(
            "/api/v1/calculate",
            json={
                "product_id": "alignment-test-prod-001",
                "calculation_type": "cradle_to_gate"
            }
        )

        data = response.json()
        calc_id = data.get("calculation_id")

        # Check the initial response - this WILL FAIL because backend uses "processing"
        assert data.get("status") != "processing", \
            "Contract Violation: API returned 'processing' status. " \
            "Frontend expects 'in_progress' for calculations that are executing."

        # Also check the status endpoint
        if calc_id:
            status_response = client.get(f"/api/v1/calculations/{calc_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                assert status_data.get("status") != "processing", \
                    "Contract Violation: Calculation status endpoint returned 'processing'. " \
                    "Frontend expects 'in_progress'."


# =============================================================================
# ProductSearchItem.category Type Contract Alignment Tests
# =============================================================================

class TestProductSearchCategoryContractAlignment:
    """
    Tests ensuring ProductSearchItem.category is a string, not an object.

    Frontend expects: category: string (e.g., "Materials")
    Backend currently returns: category: {id: string, code: string, name: string, ...}

    These tests verify the category field type matches frontend expectations.
    """

    def test_product_search_category_is_string_type(self, client, seed_test_data):
        """
        Verify product search returns category as string, not object.

        Contract Requirement:
        - ProductSearchItem.category MUST be a string
        - NOT an object like {id: "1", name: "Materials", ...}

        This test MUST FAIL if backend returns category as CategoryInfo object.
        """
        response = client.get("/api/v1/products/search?q=Contract")

        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}"

        data = response.json()
        items = data.get("items", [])

        if len(items) > 0:
            item = items[0]
            category = item.get("category")

            # Category should be a string or null, NOT an object
            if category is not None:
                assert isinstance(category, str), \
                    f"Contract Violation: ProductSearchItem.category should be a string, " \
                    f"but got {type(category).__name__}: {category}. " \
                    f"Frontend expects 'category: string', not 'category: CategoryInfo'."

    def test_product_search_category_not_object_with_id(self, client, seed_test_data):
        """
        Verify category does not have 'id' property (would indicate it's an object).

        If category has nested properties, it's returning an object instead of string.
        """
        response = client.get("/api/v1/products/search?q=Contract")

        assert response.status_code == 200

        data = response.json()
        items = data.get("items", [])

        for item in items:
            category = item.get("category")

            # If category is an object with 'id', it's wrong
            if category is not None and isinstance(category, dict):
                assert "id" not in category, \
                    f"Contract Violation: ProductSearchItem.category is an object with 'id': {category}. " \
                    f"Frontend expects a simple string like 'Materials', not an object."

    def test_product_search_category_not_object_with_name(self, client, seed_test_data):
        """
        Verify category does not have 'name' property (would indicate it's an object).

        Backend may be returning CategoryInfo object {id, code, name, industry_sector}.
        """
        response = client.get("/api/v1/products/search?q=Contract")

        assert response.status_code == 200

        data = response.json()
        items = data.get("items", [])

        for item in items:
            category = item.get("category")

            # If category is an object with 'name', it's wrong
            if category is not None and isinstance(category, dict):
                assert "name" not in category, \
                    f"Contract Violation: ProductSearchItem.category is an object with 'name': {category}. " \
                    f"Frontend expects a simple string like 'Materials', not a CategoryInfo object."

    def test_pydantic_schema_category_type_is_string(self):
        """
        Verify ProductSearchItem Pydantic schema defines category as string.

        Contract Requirement:
        - ProductSearchItem.category should be Optional[str], not Optional[CategoryInfo]

        This test checks the schema definition directly.
        """
        schema = ProductSearchItem.model_json_schema()
        properties = schema.get("properties", {})
        category_schema = properties.get("category", {})

        # Check if category is defined as string type
        # If it references another schema (CategoryInfo), this will fail
        category_type = category_schema.get("type")
        category_ref = category_schema.get("$ref")
        category_anyof = category_schema.get("anyOf", [])

        # If there's a $ref, it's referencing another schema (object)
        if category_ref:
            pytest.fail(
                f"Contract Violation: ProductSearchItem.category uses $ref: {category_ref}. "
                f"Should be 'type: string' to match frontend contract."
            )

        # If anyOf contains a $ref, it's also wrong
        for option in category_anyof:
            if "$ref" in option:
                pytest.fail(
                    f"Contract Violation: ProductSearchItem.category uses anyOf with $ref: {option}. "
                    f"Should be a simple string type to match frontend contract."
                )

        # If type is present, verify it's string (or includes string for Optional)
        if category_type:
            valid_types = ["string", "null"]
            if category_type not in valid_types:
                pytest.fail(
                    f"Contract Violation: ProductSearchItem.category has type '{category_type}'. "
                    f"Expected 'string' to match frontend contract."
                )


# =============================================================================
# OpenAPI Schema Contract Alignment Tests
# =============================================================================

class TestOpenAPISchemaAlignment:
    """
    Tests verifying OpenAPI schema matches frontend type definitions.

    These tests ensure the auto-generated OpenAPI documentation reflects
    the correct contract types that the frontend expects.
    """

    def test_openapi_calculation_status_enum_values(self, client):
        """
        Verify OpenAPI schema defines CalculationStatus with frontend-compatible values.

        Contract Requirement:
        - CalculationStatus enum should be: ["pending", "in_progress", "completed", "failed"]
        - NOT ["pending", "processing", "running", "completed", "failed"]
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        schemas = openapi.get("components", {}).get("schemas", {})

        # Look for status-related schemas or enums
        # The calculation response should have status field documentation
        calc_status_schema = schemas.get("CalculationStatusResponse", {})
        if calc_status_schema:
            properties = calc_status_schema.get("properties", {})
            status_prop = properties.get("status", {})

            # If status has enum values, check them
            status_enum = status_prop.get("enum")
            if status_enum:
                expected_enum = ["pending", "in_progress", "completed", "failed"]
                assert set(status_enum) == set(expected_enum), \
                    f"Contract Violation: OpenAPI status enum {status_enum} " \
                    f"does not match frontend expected values {expected_enum}."

    def test_openapi_product_search_category_type(self, client):
        """
        Verify OpenAPI schema defines ProductSearchItem.category as string type.

        Contract Requirement:
        - category should be defined as 'type: string' or nullable string
        - NOT as a $ref to CategoryInfo
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        schemas = openapi.get("components", {}).get("schemas", {})

        # Find ProductSearchItem schema
        search_item_schema = schemas.get("ProductSearchItem", {})
        if search_item_schema:
            properties = search_item_schema.get("properties", {})
            category_prop = properties.get("category", {})

            # Check if category references another schema
            if "$ref" in category_prop:
                ref = category_prop["$ref"]
                pytest.fail(
                    f"Contract Violation: OpenAPI ProductSearchItem.category has $ref: {ref}. "
                    f"Frontend expects simple string type, not a complex object."
                )

            # Check anyOf for $ref
            anyof = category_prop.get("anyOf", [])
            for option in anyof:
                if "$ref" in option:
                    ref = option["$ref"]
                    pytest.fail(
                        f"Contract Violation: OpenAPI ProductSearchItem.category anyOf contains $ref: {ref}. "
                        f"Frontend expects simple string type."
                    )


# =============================================================================
# Integration Alignment Tests
# =============================================================================

class TestIntegrationContractAlignment:
    """
    Integration tests verifying end-to-end contract alignment.

    These tests simulate actual frontend usage patterns and verify
    the responses match what the frontend components expect.
    """

    def test_calculation_workflow_status_alignment(self, client, seed_test_data):
        """
        Verify complete calculation workflow uses aligned status values.

        Simulates: Create calculation -> Poll status -> Complete

        All status values throughout must be frontend-compatible.
        """
        valid_statuses = ["pending", "in_progress", "completed", "failed"]

        # Step 1: Create calculation
        create_response = client.post(
            "/api/v1/calculate",
            json={
                "product_id": "alignment-test-prod-001",
                "calculation_type": "cradle_to_gate"
            }
        )

        assert create_response.status_code in [200, 202]
        create_data = create_response.json()

        initial_status = create_data.get("status")
        assert initial_status in valid_statuses, \
            f"Contract Violation: Initial calculation status '{initial_status}' " \
            f"not in frontend-compatible values: {valid_statuses}"

        # Step 2: Check calculation status endpoint
        calc_id = create_data.get("calculation_id")
        if calc_id:
            status_response = client.get(f"/api/v1/calculations/{calc_id}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                polled_status = status_data.get("status")

                assert polled_status in valid_statuses, \
                    f"Contract Violation: Polled calculation status '{polled_status}' " \
                    f"not in frontend-compatible values: {valid_statuses}"

    def test_product_search_response_format_alignment(self, client, seed_test_data):
        """
        Verify product search response format matches frontend ProductSearchResponse.

        Frontend expects:
        - items: ProductSearchItem[] with category: string
        - total: number
        - limit: number
        - offset: number
        - has_more: boolean
        """
        response = client.get("/api/v1/products/search?q=test")

        assert response.status_code == 200

        data = response.json()

        # Verify top-level structure
        assert "items" in data, "Missing 'items' field"
        assert "total" in data, "Missing 'total' field"
        assert "limit" in data, "Missing 'limit' field"
        assert "offset" in data, "Missing 'offset' field"
        assert "has_more" in data, "Missing 'has_more' field (frontend expects this)"

        # Verify items structure
        for item in data.get("items", []):
            # Check category is string, not object
            category = item.get("category")
            if category is not None:
                assert isinstance(category, str), \
                    f"Contract Violation: item.category is {type(category).__name__}, " \
                    f"expected string. Value: {category}"
