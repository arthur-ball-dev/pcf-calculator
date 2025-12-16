"""
Contract Validation Tests for Product Categories API
TASK-API-P5-002: Enhanced Product Search - Phase A Tests

Contract tests validate that the /api/v1/products/categories endpoint
adheres to the products-categories-contract.yaml specification.

Contract tests verify:
- Response structure matches contract exactly
- Field types are correct
- Required fields are present
- Tree structure follows recursive definition
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
def seed_contract_categories(db_session):
    """
    Seed database with minimal category tree for contract testing.

    Creates simple hierarchy:
    - Root Category (level 0)
      - Child Category (level 1)
    """
    # Root category
    root = ProductCategory(
        id="contract-root",
        code="ROOT",
        name="Contract Root Category",
        level=0,
        industry_sector="electronics"
    )
    db_session.add(root)
    db_session.commit()

    # Child category
    child = ProductCategory(
        id="contract-child",
        code="CHILD",
        name="Contract Child Category",
        parent_id="contract-root",
        level=1,
        industry_sector="electronics"
    )
    db_session.add(child)
    db_session.commit()

    # Category without industry_sector
    no_sector = ProductCategory(
        id="contract-nosec",
        code="NOSEC",
        name="No Sector Category",
        level=0,
        industry_sector=None
    )
    db_session.add(no_sector)
    db_session.commit()

    return {
        "root": root,
        "child": child,
        "no_sector": no_sector,
    }


@pytest.fixture(scope="function")
def seed_products_for_count(db_session, seed_contract_categories):
    """Seed products for product_count testing."""
    products = [
        Product(
            id="count-prod-1",
            code="COUNT-001",
            name="Count Product 1",
            unit="unit",
            category_id="contract-root",
            is_finished_product=True
        ),
        Product(
            id="count-prod-2",
            code="COUNT-002",
            name="Count Product 2",
            unit="unit",
            category_id="contract-root",
            is_finished_product=True
        ),
        Product(
            id="count-prod-3",
            code="COUNT-003",
            name="Count Product 3",
            unit="unit",
            category_id="contract-child",
            is_finished_product=True
        ),
    ]
    db_session.add_all(products)
    db_session.commit()

    return products


# ============================================================================
# Contract: Response Structure
# ============================================================================

class TestCategoriesResponseStructureContract:
    """
    Contract: Response MUST contain required top-level fields.

    Per products-categories-contract.yaml:
    - categories: array of category objects
    - total_categories: integer count
    - max_depth: integer maximum depth
    """

    def test_response_has_categories_field(self, client, seed_contract_categories):
        """Contract: Response MUST have 'categories' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert "categories" in data, \
            "Contract violation: 'categories' field is required"

    def test_response_has_total_categories_field(self, client, seed_contract_categories):
        """Contract: Response MUST have 'total_categories' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert "total_categories" in data, \
            "Contract violation: 'total_categories' field is required"

    def test_response_has_max_depth_field(self, client, seed_contract_categories):
        """Contract: Response MUST have 'max_depth' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert "max_depth" in data, \
            "Contract violation: 'max_depth' field is required"


# ============================================================================
# Contract: Field Types
# ============================================================================

class TestCategoriesFieldTypesContract:
    """
    Contract: Response fields MUST have correct types.

    Per products-categories-contract.yaml:
    - categories: array
    - total_categories: integer
    - max_depth: integer
    """

    def test_categories_is_array(self, client, seed_contract_categories):
        """Contract: 'categories' MUST be an array."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["categories"], list), \
            "Contract violation: 'categories' must be an array"

    def test_total_categories_is_integer(self, client, seed_contract_categories):
        """Contract: 'total_categories' MUST be an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["total_categories"], int), \
            "Contract violation: 'total_categories' must be an integer"

    def test_max_depth_is_integer(self, client, seed_contract_categories):
        """Contract: 'max_depth' MUST be an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["max_depth"], int), \
            "Contract violation: 'max_depth' must be an integer"


# ============================================================================
# Contract: Category Object Structure
# ============================================================================

class TestCategoryObjectStructureContract:
    """
    Contract: Each category MUST have required fields.

    Per products-categories-contract.yaml, each category MUST have:
    - id: UUID string
    - code: string
    - name: string
    - level: integer
    - children: array (recursive)

    Optional/nullable:
    - industry_sector: string or null
    - product_count: integer or null
    """

    def test_category_has_id(self, client, seed_contract_categories):
        """Contract: Category MUST have 'id' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert len(data["categories"]) > 0, "Need categories to test"
        for cat in data["categories"]:
            assert "id" in cat, \
                "Contract violation: 'id' required in category"

    def test_category_has_code(self, client, seed_contract_categories):
        """Contract: Category MUST have 'code' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert "code" in cat, \
                "Contract violation: 'code' required in category"

    def test_category_has_name(self, client, seed_contract_categories):
        """Contract: Category MUST have 'name' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert "name" in cat, \
                "Contract violation: 'name' required in category"

    def test_category_has_level(self, client, seed_contract_categories):
        """Contract: Category MUST have 'level' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert "level" in cat, \
                "Contract violation: 'level' required in category"

    def test_category_has_children(self, client, seed_contract_categories):
        """Contract: Category MUST have 'children' field."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert "children" in cat, \
                "Contract violation: 'children' required in category"

    def test_category_has_industry_sector(self, client, seed_contract_categories):
        """Contract: Category MUST have 'industry_sector' field (nullable)."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert "industry_sector" in cat, \
                "Contract violation: 'industry_sector' field must be present"


# ============================================================================
# Contract: Category Field Types
# ============================================================================

class TestCategoryFieldTypesContract:
    """Contract: Category fields MUST have correct types."""

    def test_category_id_is_string(self, client, seed_contract_categories):
        """Contract: 'id' MUST be a string (UUID)."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["id"], str), \
                "Contract violation: 'id' must be a string"

    def test_category_code_is_string(self, client, seed_contract_categories):
        """Contract: 'code' MUST be a string."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["code"], str), \
                "Contract violation: 'code' must be a string"

    def test_category_name_is_string(self, client, seed_contract_categories):
        """Contract: 'name' MUST be a string."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["name"], str), \
                "Contract violation: 'name' must be a string"

    def test_category_level_is_integer(self, client, seed_contract_categories):
        """Contract: 'level' MUST be an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["level"], int), \
                "Contract violation: 'level' must be an integer"

    def test_category_children_is_array(self, client, seed_contract_categories):
        """Contract: 'children' MUST be an array."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["children"], list), \
                "Contract violation: 'children' must be an array"


# ============================================================================
# Contract: Nullable Fields
# ============================================================================

class TestNullableCategoryFieldsContract:
    """Contract: Optional fields MAY be null."""

    def test_industry_sector_can_be_null(self, client, seed_contract_categories):
        """Contract: 'industry_sector' MAY be null."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Find category without industry sector
        nosec = next(
            (c for c in data["categories"] if c["code"] == "NOSEC"),
            None
        )
        if nosec:
            assert nosec["industry_sector"] is None, \
                "Contract violation: industry_sector can be null"

    def test_product_count_null_when_not_requested(
        self, client, seed_products_for_count
    ):
        """Contract: 'product_count' null when not requested."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            if "product_count" in cat:
                assert cat["product_count"] is None, \
                    "Contract violation: product_count null when not requested"


# ============================================================================
# Contract: Product Count Field
# ============================================================================

class TestProductCountContract:
    """Contract: product_count behavior when include_product_count=true."""

    def test_product_count_present_when_requested(
        self, client, seed_products_for_count
    ):
        """Contract: 'product_count' present when include_product_count=true."""
        response = client.get(
            "/api/v1/products/categories?include_product_count=true"
        )
        data = response.json()

        def check_count_present(categories):
            for cat in categories:
                assert "product_count" in cat, \
                    f"Contract violation: product_count required when requested"
                if cat.get("children"):
                    check_count_present(cat["children"])

        check_count_present(data["categories"])

    def test_product_count_is_integer(self, client, seed_products_for_count):
        """Contract: 'product_count' MUST be integer when present."""
        response = client.get(
            "/api/v1/products/categories?include_product_count=true"
        )
        data = response.json()

        def check_count_type(categories):
            for cat in categories:
                assert isinstance(cat["product_count"], int), \
                    "Contract violation: product_count must be integer"
                if cat.get("children"):
                    check_count_type(cat["children"])

        check_count_type(data["categories"])

    def test_product_count_non_negative(self, client, seed_products_for_count):
        """Contract: 'product_count' MUST be >= 0."""
        response = client.get(
            "/api/v1/products/categories?include_product_count=true"
        )
        data = response.json()

        def check_count_value(categories):
            for cat in categories:
                assert cat["product_count"] >= 0, \
                    "Contract violation: product_count must be non-negative"
                if cat.get("children"):
                    check_count_value(cat["children"])

        check_count_value(data["categories"])


# ============================================================================
# Contract: Recursive Structure
# ============================================================================

class TestRecursiveStructureContract:
    """Contract: Children follow same structure as parent."""

    def test_children_have_same_structure(self, client, seed_contract_categories):
        """Contract: Child categories have same structure as parents."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        required_fields = ["id", "code", "name", "level", "children", "industry_sector"]

        def check_structure(categories):
            for cat in categories:
                for field in required_fields:
                    assert field in cat, \
                        f"Contract violation: child missing '{field}'"
                if cat.get("children"):
                    check_structure(cat["children"])

        check_structure(data["categories"])


# ============================================================================
# Contract: Error Responses
# ============================================================================

class TestCategoriesErrorResponseContract:
    """
    Contract: Error responses follow standard format.

    Per products-categories-contract.yaml:
    - 400: Validation error
    - 404: Parent category not found
    """

    def test_400_for_invalid_depth(self, client, seed_contract_categories):
        """Contract: Invalid depth MUST return 400."""
        response = client.get("/api/v1/products/categories?depth=10")

        assert response.status_code in [400, 422], \
            f"Contract violation: invalid depth should return 400/422"

    def test_404_for_invalid_parent_id(self, client, seed_contract_categories):
        """Contract: Non-existent parent_id MUST return 404."""
        fake_id = "00000000000000000000000000000000"
        response = client.get(f"/api/v1/products/categories?parent_id={fake_id}")

        assert response.status_code == 404, \
            f"Contract violation: invalid parent_id should return 404"

    def test_error_response_has_error_details(self, client, seed_contract_categories):
        """Contract: Error response MUST have error details."""
        fake_id = "00000000000000000000000000000000"
        response = client.get(f"/api/v1/products/categories?parent_id={fake_id}")
        data = response.json()

        assert "error" in data or "detail" in data, \
            "Contract violation: error response must have 'error' or 'detail'"


# ============================================================================
# Contract: Query Parameter Defaults
# ============================================================================

class TestQueryParameterDefaultsContract:
    """Contract: Query parameters have specific defaults."""

    def test_default_depth_is_3(self, client, seed_contract_categories):
        """Contract: Default depth MUST be 3."""
        # This is implicit - we verify by checking max_depth <= 3
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Per contract, default depth is 3
        assert data["max_depth"] <= 3, \
            "Contract violation: default depth should limit to 3"

    def test_include_product_count_default_false(
        self, client, seed_products_for_count
    ):
        """Contract: Default include_product_count is false."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Product count should be null when not explicitly requested
        for cat in data["categories"]:
            if "product_count" in cat:
                assert cat["product_count"] is None, \
                    "Contract violation: default product_count should be null"


# ============================================================================
# Contract: HTTP Status Codes
# ============================================================================

class TestCategoriesHttpStatusCodesContract:
    """Contract: Endpoints return correct HTTP status codes."""

    def test_success_returns_200(self, client, seed_contract_categories):
        """Contract: Successful request MUST return 200."""
        response = client.get("/api/v1/products/categories")

        assert response.status_code == 200, \
            f"Contract violation: success should return 200"

    def test_empty_result_returns_200(self, client):
        """Contract: Empty categories MUST return 200, not 404."""
        response = client.get("/api/v1/products/categories")

        assert response.status_code == 200, \
            "Contract violation: empty result should return 200"

    def test_not_found_parent_returns_404(self, client, seed_contract_categories):
        """Contract: Non-existent parent MUST return 404."""
        fake_id = "00000000000000000000000000000000"
        response = client.get(f"/api/v1/products/categories?parent_id={fake_id}")

        assert response.status_code == 404, \
            "Contract violation: non-existent parent should return 404"


# ============================================================================
# Contract: Level Field Semantics
# ============================================================================

class TestLevelFieldContract:
    """Contract: Level field follows hierarchical semantics."""

    def test_root_level_is_zero(self, client, seed_contract_categories):
        """Contract: Root categories MUST have level=0."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Top-level categories should have level=0
        for cat in data["categories"]:
            assert cat["level"] == 0, \
                f"Contract violation: root category should have level=0"

    def test_child_level_increments(self, client, seed_contract_categories):
        """Contract: Child level = parent level + 1."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        def check_levels(categories, expected_level):
            for cat in categories:
                assert cat["level"] == expected_level, \
                    f"Contract violation: expected level {expected_level}"
                if cat.get("children"):
                    check_levels(cat["children"], expected_level + 1)

        check_levels(data["categories"], 0)


# ============================================================================
# Contract: Empty Arrays
# ============================================================================

class TestEmptyArraysContract:
    """Contract: Empty arrays are valid responses."""

    def test_empty_categories_array_valid(self, client):
        """Contract: Empty categories array is valid."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert response.status_code == 200
        assert isinstance(data["categories"], list)
        # Empty list is acceptable

    def test_empty_children_array_valid(self, client, seed_contract_categories):
        """Contract: Empty children array is valid for leaf categories."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Find a leaf category (no children)
        def find_leaf(categories):
            for cat in categories:
                if len(cat["children"]) == 0:
                    return cat
                leaf = find_leaf(cat["children"])
                if leaf:
                    return leaf
            return None

        leaf = find_leaf(data["categories"])
        if leaf:
            assert leaf["children"] == [], \
                "Contract violation: leaf should have empty children array"
