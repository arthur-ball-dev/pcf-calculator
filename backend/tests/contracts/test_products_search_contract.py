"""
Contract Validation Tests for Product Search API
TASK-API-P5-002: Enhanced Product Search - Phase A Tests

Contract tests validate that the /api/v1/products/search endpoint
adheres to the products-search-contract.yaml specification.

Contract tests verify:
- Response structure matches contract exactly
- Field types are correct
- Required fields are present
- Optional fields behave correctly
- Error responses follow standard format

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests validate contract compliance, not business logic
- Implementation must make tests PASS without modifying tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from backend.models import (
    Base,
    Product,
    ProductCategory,
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
    Seed database with minimal data for contract testing.

    Creates just enough data to validate all response fields.
    """
    # Create category
    category = ProductCategory(
        id="contract-cat-001",
        code="CONTRACT-CAT",
        name="Contract Test Category",
        level=0,
        industry_sector="electronics"
    )
    db_session.add(category)
    db_session.commit()

    # Create product with all fields
    product = Product(
        id="contract-prod-001",
        code="CONTRACT-001",
        name="Contract Test Product",
        description="Product for contract testing with full description",
        unit="unit",
        category_id="contract-cat-001",
        manufacturer="Contract Manufacturer",
        country_of_origin="US",
        is_finished_product=True,
        search_vector="contract test product"
    )
    db_session.add(product)
    db_session.commit()

    # Create product without optional fields
    product_minimal = Product(
        id="contract-prod-002",
        code="CONTRACT-002",
        name="Minimal Product",
        unit="kg",
        is_finished_product=False,
        description=None,
        category_id=None,
        manufacturer=None,
        country_of_origin=None
    )
    db_session.add(product_minimal)
    db_session.commit()

    return {
        "category": category,
        "product": product,
        "product_minimal": product_minimal,
    }


# ============================================================================
# Contract: Response Structure
# ============================================================================

class TestSearchResponseStructureContract:
    """
    Contract: Response MUST contain required top-level fields.

    Per products-search-contract.yaml:
    - items: array of products
    - total: integer count
    - limit: integer limit applied
    - offset: integer offset applied
    - has_more: boolean
    """

    def test_response_has_items_field(self, client, seed_contract_data):
        """Contract: Response MUST have 'items' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "items" in data, \
            "Contract violation: 'items' field is required"

    def test_response_has_total_field(self, client, seed_contract_data):
        """Contract: Response MUST have 'total' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "total" in data, \
            "Contract violation: 'total' field is required"

    def test_response_has_limit_field(self, client, seed_contract_data):
        """Contract: Response MUST have 'limit' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "limit" in data, \
            "Contract violation: 'limit' field is required"

    def test_response_has_offset_field(self, client, seed_contract_data):
        """Contract: Response MUST have 'offset' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "offset" in data, \
            "Contract violation: 'offset' field is required"

    def test_response_has_has_more_field(self, client, seed_contract_data):
        """Contract: Response MUST have 'has_more' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "has_more" in data, \
            "Contract violation: 'has_more' field is required"


# ============================================================================
# Contract: Field Types
# ============================================================================

class TestSearchFieldTypesContract:
    """
    Contract: Response fields MUST have correct types.

    Per products-search-contract.yaml:
    - items: array
    - total: integer
    - limit: integer
    - offset: integer
    - has_more: boolean
    """

    def test_items_is_array(self, client, seed_contract_data):
        """Contract: 'items' MUST be an array."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert isinstance(data["items"], list), \
            "Contract violation: 'items' must be an array"

    def test_total_is_integer(self, client, seed_contract_data):
        """Contract: 'total' MUST be an integer."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert isinstance(data["total"], int), \
            "Contract violation: 'total' must be an integer"

    def test_limit_is_integer(self, client, seed_contract_data):
        """Contract: 'limit' MUST be an integer."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert isinstance(data["limit"], int), \
            "Contract violation: 'limit' must be an integer"

    def test_offset_is_integer(self, client, seed_contract_data):
        """Contract: 'offset' MUST be an integer."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert isinstance(data["offset"], int), \
            "Contract violation: 'offset' must be an integer"

    def test_has_more_is_boolean(self, client, seed_contract_data):
        """Contract: 'has_more' MUST be a boolean."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert isinstance(data["has_more"], bool), \
            "Contract violation: 'has_more' must be a boolean"


# ============================================================================
# Contract: Product Item Structure
# ============================================================================

class TestProductItemStructureContract:
    """
    Contract: Each product item MUST have required fields.

    Per products-search-contract.yaml, each item MUST have:
    - id: UUID string
    - code: string
    - name: string
    - unit: string
    - is_finished_product: boolean
    - created_at: ISO 8601 datetime string

    Optional/nullable fields:
    - description: string or null
    - category: object or null
    - manufacturer: string or null
    - country_of_origin: string or null
    - relevance_score: number or null
    """

    def test_item_has_id(self, client, seed_contract_data):
        """Contract: Product item MUST have 'id' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert len(data["items"]) > 0, "Need items to test"
        for item in data["items"]:
            assert "id" in item, \
                "Contract violation: 'id' required in product item"

    def test_item_has_code(self, client, seed_contract_data):
        """Contract: Product item MUST have 'code' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert "code" in item, \
                "Contract violation: 'code' required in product item"

    def test_item_has_name(self, client, seed_contract_data):
        """Contract: Product item MUST have 'name' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert "name" in item, \
                "Contract violation: 'name' required in product item"

    def test_item_has_unit(self, client, seed_contract_data):
        """Contract: Product item MUST have 'unit' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert "unit" in item, \
                "Contract violation: 'unit' required in product item"

    def test_item_has_is_finished_product(self, client, seed_contract_data):
        """Contract: Product item MUST have 'is_finished_product' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert "is_finished_product" in item, \
                "Contract violation: 'is_finished_product' required"

    def test_item_has_created_at(self, client, seed_contract_data):
        """Contract: Product item MUST have 'created_at' field."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert "created_at" in item, \
                "Contract violation: 'created_at' required"


# ============================================================================
# Contract: Product Item Field Types
# ============================================================================

class TestProductItemFieldTypesContract:
    """Contract: Product item fields MUST have correct types."""

    def test_item_id_is_string(self, client, seed_contract_data):
        """Contract: 'id' MUST be a string (UUID)."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["id"], str), \
                "Contract violation: 'id' must be a string"

    def test_item_code_is_string(self, client, seed_contract_data):
        """Contract: 'code' MUST be a string."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["code"], str), \
                "Contract violation: 'code' must be a string"

    def test_item_name_is_string(self, client, seed_contract_data):
        """Contract: 'name' MUST be a string."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["name"], str), \
                "Contract violation: 'name' must be a string"

    def test_item_unit_is_string(self, client, seed_contract_data):
        """Contract: 'unit' MUST be a string."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["unit"], str), \
                "Contract violation: 'unit' must be a string"

    def test_item_is_finished_product_is_boolean(self, client, seed_contract_data):
        """Contract: 'is_finished_product' MUST be a boolean."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["is_finished_product"], bool), \
                "Contract violation: 'is_finished_product' must be boolean"

    def test_item_created_at_is_iso8601(self, client, seed_contract_data):
        """Contract: 'created_at' MUST be ISO 8601 datetime string."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            created_at = item["created_at"]
            assert isinstance(created_at, str), \
                "Contract violation: 'created_at' must be a string"
            try:
                datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(
                    f"Contract violation: 'created_at' not ISO 8601: {created_at}"
                )


# ============================================================================
# Contract: Nullable Fields
# ============================================================================

class TestNullableFieldsContract:
    """Contract: Optional fields MAY be null."""

    def test_description_can_be_null(self, client, seed_contract_data):
        """Contract: 'description' MAY be null."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        # Find minimal product (has null description)
        minimal = next(
            (p for p in data["items"] if p["code"] == "CONTRACT-002"),
            None
        )
        if minimal:
            # description should be present as key but can be null
            assert "description" in minimal, \
                "Contract violation: 'description' field must be present"
            # Value can be null
            assert minimal["description"] is None or isinstance(minimal["description"], str)

    def test_category_can_be_null(self, client, seed_contract_data):
        """Contract: 'category' MAY be null."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        # Find minimal product (has null category)
        minimal = next(
            (p for p in data["items"] if p["code"] == "CONTRACT-002"),
            None
        )
        if minimal:
            assert "category" in minimal, \
                "Contract violation: 'category' field must be present"
            # Can be null for products without category
            assert minimal["category"] is None or isinstance(minimal["category"], dict)

    def test_manufacturer_can_be_null(self, client, seed_contract_data):
        """Contract: 'manufacturer' MAY be null."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        minimal = next(
            (p for p in data["items"] if p["code"] == "CONTRACT-002"),
            None
        )
        if minimal:
            assert "manufacturer" in minimal, \
                "Contract violation: 'manufacturer' field must be present"

    def test_country_of_origin_can_be_null(self, client, seed_contract_data):
        """Contract: 'country_of_origin' MAY be null."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        minimal = next(
            (p for p in data["items"] if p["code"] == "CONTRACT-002"),
            None
        )
        if minimal:
            assert "country_of_origin" in minimal, \
                "Contract violation: 'country_of_origin' field must be present"

    def test_relevance_score_null_without_query(self, client, seed_contract_data):
        """Contract: 'relevance_score' MUST be null when no query provided."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        for item in data["items"]:
            if "relevance_score" in item:
                assert item["relevance_score"] is None, \
                    "Contract violation: relevance_score null when no query"


# ============================================================================
# Contract: Category Object Structure
# ============================================================================

class TestCategoryObjectContract:
    """
    Contract: When category is not null, it MUST have specific structure.

    Per products-search-contract.yaml, category object MUST have:
    - id: UUID string
    - code: string
    - name: string
    - industry_sector: string
    """

    def test_category_has_id(self, client, seed_contract_data):
        """Contract: Category object MUST have 'id'."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        # Find product with category
        with_cat = next(
            (p for p in data["items"] if p.get("category")),
            None
        )
        if with_cat:
            assert "id" in with_cat["category"], \
                "Contract violation: category 'id' required"

    def test_category_has_code(self, client, seed_contract_data):
        """Contract: Category object MUST have 'code'."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        with_cat = next(
            (p for p in data["items"] if p.get("category")),
            None
        )
        if with_cat:
            assert "code" in with_cat["category"], \
                "Contract violation: category 'code' required"

    def test_category_has_name(self, client, seed_contract_data):
        """Contract: Category object MUST have 'name'."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        with_cat = next(
            (p for p in data["items"] if p.get("category")),
            None
        )
        if with_cat:
            assert "name" in with_cat["category"], \
                "Contract violation: category 'name' required"

    def test_category_has_industry_sector(self, client, seed_contract_data):
        """Contract: Category object MUST have 'industry_sector'."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        with_cat = next(
            (p for p in data["items"] if p.get("category")),
            None
        )
        if with_cat:
            assert "industry_sector" in with_cat["category"], \
                "Contract violation: category 'industry_sector' required"


# ============================================================================
# Contract: Error Responses
# ============================================================================

class TestErrorResponseContract:
    """
    Contract: Error responses MUST follow standard format.

    Per products-search-contract.yaml:
    - 400: Validation error (query too short)
    - 422: Invalid category
    - 500: Internal error
    """

    def test_400_for_query_too_short(self, client, seed_contract_data):
        """Contract: Query <2 chars MUST return 400."""
        response = client.get("/api/v1/products/search?query=a")

        assert response.status_code == 400, \
            f"Contract violation: query<2 chars should return 400"

    def test_422_for_invalid_category(self, client, seed_contract_data):
        """Contract: Invalid category_id MUST return 422."""
        fake_id = "00000000000000000000000000000000"
        response = client.get(f"/api/v1/products/search?category_id={fake_id}")

        assert response.status_code == 422, \
            f"Contract violation: invalid category should return 422"

    def test_error_response_has_error_field(self, client, seed_contract_data):
        """Contract: Error response MUST have 'error' or 'detail' field."""
        response = client.get("/api/v1/products/search?query=a")
        data = response.json()

        assert "error" in data or "detail" in data, \
            "Contract violation: error response must have 'error' or 'detail'"


# ============================================================================
# Contract: Pagination Defaults
# ============================================================================

class TestPaginationDefaultsContract:
    """Contract: Pagination parameters have specific defaults."""

    def test_default_limit_is_50(self, client, seed_contract_data):
        """Contract: Default limit MUST be 50."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert data["limit"] == 50, \
            f"Contract violation: default limit should be 50, got {data['limit']}"

    def test_default_offset_is_0(self, client, seed_contract_data):
        """Contract: Default offset MUST be 0."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert data["offset"] == 0, \
            f"Contract violation: default offset should be 0, got {data['offset']}"


# ============================================================================
# Contract: HTTP Status Codes
# ============================================================================

class TestHttpStatusCodesContract:
    """Contract: Endpoints return correct HTTP status codes."""

    def test_success_returns_200(self, client, seed_contract_data):
        """Contract: Successful search MUST return 200."""
        response = client.get("/api/v1/products/search")

        assert response.status_code == 200, \
            f"Contract violation: success should return 200, got {response.status_code}"

    def test_validation_error_returns_400_or_422(self, client, seed_contract_data):
        """Contract: Validation errors return 400 or 422."""
        response = client.get("/api/v1/products/search?limit=0")

        assert response.status_code in [400, 422], \
            f"Contract violation: validation error should return 400/422"

    def test_empty_results_still_returns_200(self, client, seed_contract_data):
        """Contract: Empty results MUST return 200, not 404."""
        response = client.get("/api/v1/products/search?query=xyz123nonexistent")

        assert response.status_code == 200, \
            "Contract violation: empty results should return 200"
