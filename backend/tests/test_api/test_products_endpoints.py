"""
Test Products API Endpoints
TASK-API-001: Comprehensive tests for products REST endpoints

Test Scenarios (per specification):
1. GET /api/v1/products - List all products
2. GET /api/v1/products - Pagination (limit, offset)
3. GET /api/v1/products/{id} - Product with BOM
4. GET /api/v1/products/{id} - 404 for missing product
5. GET /api/v1/products - Filter by is_finished_product
6. Response format validation with Pydantic
7. HTTP status codes (200, 404, 422)
8. Response structure matches API specification
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

# Import models and base
from backend.models import (
    Base,
    Product,
    BillOfMaterials,
    EmissionFactor
)
from backend.main import app
from backend.database.connection import get_db


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing with threading support"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},  # Allow cross-thread access
        poolclass=StaticPool,  # Use static pool for thread safety
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create FastAPI TestClient with database dependency override

    This fixture overrides the get_db dependency to use the test database
    instead of the production database
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)

    yield test_client

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_test_products(db_session):
    """
    Seed test database with known products for endpoint testing

    Creates:
    - 3 finished products (T-Shirt, Water Bottle, Phone Case)
    - 5 components (Cotton, Polyester, PET, ABS, Aluminum)
    - BOM relationships for T-Shirt
    """
    # Create finished products
    tshirt = Product(
        id="tshirt-001",
        code="TSHIRT-001",
        name="Cotton T-Shirt",
        unit="unit",
        category="apparel",
        is_finished_product=True,
        description="Simple cotton t-shirt"
    )

    bottle = Product(
        id="bottle-001",
        code="BOTTLE-001",
        name="Water Bottle",
        unit="unit",
        category="beverage",
        is_finished_product=True,
        description="Reusable water bottle"
    )

    phone_case = Product(
        id="case-001",
        code="CASE-001",
        name="Phone Case",
        unit="unit",
        category="electronics",
        is_finished_product=True,
        description="Protective phone case"
    )

    # Create component products
    cotton = Product(
        id="cotton-001",
        code="COTTON-001",
        name="Cotton Fabric",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    polyester = Product(
        id="polyester-001",
        code="POLYESTER-001",
        name="Polyester Thread",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    pet_plastic = Product(
        id="pet-001",
        code="PET-001",
        name="PET Plastic",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    abs_plastic = Product(
        id="abs-001",
        code="ABS-001",
        name="ABS Plastic",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    aluminum = Product(
        id="aluminum-001",
        code="ALUMINUM-001",
        name="Aluminum Cap",
        unit="kg",
        category="material",
        is_finished_product=False
    )

    # Add all products
    db_session.add_all([
        tshirt, bottle, phone_case,
        cotton, polyester, pet_plastic, abs_plastic, aluminum
    ])
    db_session.commit()

    # Create BOM for T-Shirt
    tshirt_bom = [
        BillOfMaterials(
            parent_product_id="tshirt-001",
            child_product_id="cotton-001",
            quantity=0.18,
            unit="kg",
            notes="Main fabric"
        ),
        BillOfMaterials(
            parent_product_id="tshirt-001",
            child_product_id="polyester-001",
            quantity=0.02,
            unit="kg",
            notes="Thread"
        )
    ]

    # Create BOM for Water Bottle
    bottle_bom = [
        BillOfMaterials(
            parent_product_id="bottle-001",
            child_product_id="pet-001",
            quantity=0.03,
            unit="kg",
            notes="Bottle body"
        ),
        BillOfMaterials(
            parent_product_id="bottle-001",
            child_product_id="aluminum-001",
            quantity=0.005,
            unit="kg",
            notes="Cap"
        )
    ]

    db_session.add_all(tshirt_bom + bottle_bom)
    db_session.commit()

    return {
        "products": {
            "tshirt": tshirt,
            "bottle": bottle,
            "phone_case": phone_case,
            "cotton": cotton,
            "polyester": polyester,
            "pet": pet_plastic,
            "abs": abs_plastic,
            "aluminum": aluminum
        },
        "finished_count": 3,
        "component_count": 5,
        "total_count": 8
    }


# ============================================================================
# Test Scenario 1: GET /api/v1/products - List all products
# ============================================================================

class TestListProducts:
    """Test GET /api/v1/products endpoint"""

    def test_list_products_returns_200(self, client, seed_test_products):
        """Test that listing products returns 200 OK"""
        response = client.get("/api/v1/products")

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

    def test_list_products_returns_items(self, client, seed_test_products):
        """Test that response includes items array"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert "items" in data, \
            "Response should include 'items' field"
        assert isinstance(data["items"], list), \
            "Items should be a list"

    def test_list_products_returns_total(self, client, seed_test_products):
        """Test that response includes total count"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert "total" in data, \
            "Response should include 'total' field"
        assert isinstance(data["total"], int), \
            "Total should be an integer"
        assert data["total"] == seed_test_products["total_count"], \
            f"Expected total={seed_test_products['total_count']}, got {data['total']}"

    def test_list_products_includes_expected_products(self, client, seed_test_products):
        """Test that response includes known test products"""
        response = client.get("/api/v1/products")
        data = response.json()

        # Extract product codes
        codes = [item["code"] for item in data["items"]]

        assert "TSHIRT-001" in codes, \
            "Response should include TSHIRT-001"
        assert "BOTTLE-001" in codes, \
            "Response should include BOTTLE-001"
        assert "CASE-001" in codes, \
            "Response should include CASE-001"

    def test_list_products_item_structure(self, client, seed_test_products):
        """Test that each item has required fields"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert len(data["items"]) > 0, \
            "Should have at least one product"

        first_item = data["items"][0]

        # Required fields per API specification
        assert "id" in first_item, "Item should have 'id'"
        assert "code" in first_item, "Item should have 'code'"
        assert "name" in first_item, "Item should have 'name'"
        assert "unit" in first_item, "Item should have 'unit'"
        assert "is_finished_product" in first_item, "Item should have 'is_finished_product'"
        assert "category" in first_item, "Item should have 'category'"


# ============================================================================
# Test Scenario 2: GET /api/v1/products - Pagination
# ============================================================================

class TestProductsPagination:
    """Test pagination parameters (limit, offset)"""

    def test_pagination_with_limit(self, client, seed_test_products):
        """Test that limit parameter restricts results"""
        response = client.get("/api/v1/products?limit=2")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 2, \
            f"Expected 2 items with limit=2, got {len(data['items'])}"
        assert data["limit"] == 2, \
            f"Response should include limit=2, got {data.get('limit')}"

    def test_pagination_with_offset(self, client, seed_test_products):
        """Test that offset parameter skips results"""
        # Get first 2 products
        response1 = client.get("/api/v1/products?limit=2&offset=0")
        data1 = response1.json()
        first_two_ids = [item["id"] for item in data1["items"]]

        # Get next 2 products
        response2 = client.get("/api/v1/products?limit=2&offset=2")
        data2 = response2.json()
        next_two_ids = [item["id"] for item in data2["items"]]

        # IDs should be different (no overlap)
        assert len(set(first_two_ids) & set(next_two_ids)) == 0, \
            "Offset should skip previous results"
        assert data2["offset"] == 2, \
            f"Response should include offset=2, got {data2.get('offset')}"

    def test_pagination_default_values(self, client, seed_test_products):
        """Test default pagination values"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert "limit" in data, "Response should include limit"
        assert "offset" in data, "Response should include offset"
        assert data["offset"] == 0, \
            f"Default offset should be 0, got {data['offset']}"

    def test_pagination_limit_validation(self, client, seed_test_products):
        """Test that limit has minimum value of 1"""
        response = client.get("/api/v1/products?limit=0")

        # Should return 422 for invalid parameter
        assert response.status_code == 422, \
            f"Expected 422 for limit=0, got {response.status_code}"

    def test_pagination_offset_validation(self, client, seed_test_products):
        """Test that offset cannot be negative"""
        response = client.get("/api/v1/products?offset=-1")

        # Should return 422 for invalid parameter
        assert response.status_code == 422, \
            f"Expected 422 for offset=-1, got {response.status_code}"

    def test_pagination_limit_max_value(self, client, seed_test_products):
        """Test that limit has maximum value of 1000"""
        response = client.get("/api/v1/products?limit=2000")

        # Should return 422 for limit > 1000
        assert response.status_code == 422, \
            f"Expected 422 for limit=2000, got {response.status_code}"


# ============================================================================
# Test Scenario 3: GET /api/v1/products/{id} - Product with BOM
# ============================================================================

class TestGetProductById:
    """Test GET /api/v1/products/{id} endpoint"""

    def test_get_product_by_id_returns_200(self, client, seed_test_products):
        """Test that getting product by ID returns 200 OK"""
        response = client.get("/api/v1/products/tshirt-001")

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

    def test_get_product_by_id_returns_correct_product(self, client, seed_test_products):
        """Test that response contains correct product data"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        assert data["id"] == "tshirt-001", \
            f"Expected id='tshirt-001', got '{data['id']}'"
        assert data["code"] == "TSHIRT-001", \
            f"Expected code='TSHIRT-001', got '{data['code']}'"
        assert data["name"] == "Cotton T-Shirt", \
            f"Expected name='Cotton T-Shirt', got '{data['name']}'"

    def test_get_product_includes_bom(self, client, seed_test_products):
        """Test that response includes bill_of_materials"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        assert "bill_of_materials" in data, \
            "Response should include 'bill_of_materials' field"
        assert isinstance(data["bill_of_materials"], list), \
            "bill_of_materials should be a list"

    def test_get_product_bom_has_items(self, client, seed_test_products):
        """Test that BOM contains expected items for T-Shirt"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        bom = data["bill_of_materials"]
        assert len(bom) > 0, \
            "T-Shirt should have BOM items"

        # Check BOM item structure
        first_bom_item = bom[0]
        assert "child_product_id" in first_bom_item, \
            "BOM item should have child_product_id"
        assert "quantity" in first_bom_item, \
            "BOM item should have quantity"
        assert "unit" in first_bom_item, \
            "BOM item should have unit"

    def test_get_product_bom_includes_child_details(self, client, seed_test_products):
        """Test that BOM items include child product name"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        bom = data["bill_of_materials"]
        first_bom_item = bom[0]

        # Should include child product name for convenience
        assert "child_product_name" in first_bom_item, \
            "BOM item should include child_product_name"

    def test_get_product_without_bom(self, client, seed_test_products):
        """Test getting product without BOM (Phone Case has no BOM in seed)"""
        response = client.get("/api/v1/products/case-001")
        data = response.json()

        assert response.status_code == 200
        assert "bill_of_materials" in data
        assert len(data["bill_of_materials"]) == 0, \
            "Phone Case should have empty BOM"


# ============================================================================
# Test Scenario 4: GET /api/v1/products/{id} - 404 for missing product
# ============================================================================

class TestProductNotFound:
    """Test 404 error handling"""

    def test_get_nonexistent_product_returns_404(self, client, seed_test_products):
        """Test that requesting nonexistent product returns 404"""
        response = client.get("/api/v1/products/nonexistent-id")

        assert response.status_code == 404, \
            f"Expected status 404 for nonexistent product, got {response.status_code}"

    def test_get_nonexistent_product_error_format(self, client, seed_test_products):
        """Test that 404 response follows error format"""
        response = client.get("/api/v1/products/nonexistent-id")
        data = response.json()

        assert "detail" in data, \
            "404 response should include 'detail' field"
        assert isinstance(data["detail"], str), \
            "Detail should be a string"
        assert "not found" in data["detail"].lower(), \
            "Error message should indicate product not found"


# ============================================================================
# Test Scenario 5: GET /api/v1/products - Filter by is_finished_product
# ============================================================================

class TestProductsFiltering:
    """Test filtering by is_finished_product parameter"""

    def test_filter_finished_products_only(self, client, seed_test_products):
        """Test filtering for finished products only"""
        response = client.get("/api/v1/products?is_finished=true")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be finished products
        for item in data["items"]:
            assert item["is_finished_product"] is True, \
                f"Product {item['code']} should be finished product"

        # Should return exactly 3 finished products from seed
        assert len(data["items"]) == seed_test_products["finished_count"], \
            f"Expected {seed_test_products['finished_count']} finished products, got {len(data['items'])}"

    def test_filter_components_only(self, client, seed_test_products):
        """Test filtering for components only (not finished products)"""
        response = client.get("/api/v1/products?is_finished=false")
        data = response.json()

        assert response.status_code == 200

        # All returned items should NOT be finished products
        for item in data["items"]:
            assert item["is_finished_product"] is False, \
                f"Product {item['code']} should be component (not finished)"

        # Should return exactly 5 components from seed
        assert len(data["items"]) == seed_test_products["component_count"], \
            f"Expected {seed_test_products['component_count']} components, got {len(data['items'])}"

    def test_filter_without_parameter_returns_all(self, client, seed_test_products):
        """Test that omitting is_finished returns all products"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_test_products["total_count"], \
            f"Without filter, should return all {seed_test_products['total_count']} products"


# ============================================================================
# Test Scenario 6: Response format validation
# ============================================================================

class TestResponseFormat:
    """Test that responses match API specification format"""

    def test_list_response_has_all_required_fields(self, client, seed_test_products):
        """Test list response structure"""
        response = client.get("/api/v1/products")
        data = response.json()

        # Per API spec: items, total, limit, offset
        required_fields = ["items", "total", "limit", "offset"]
        for field in required_fields:
            assert field in data, \
                f"List response should include '{field}'"

    def test_product_item_has_all_required_fields(self, client, seed_test_products):
        """Test individual product structure in list"""
        response = client.get("/api/v1/products")
        data = response.json()

        item = data["items"][0]

        # Per API spec (knowledge/api-specifications.md lines 38-46)
        required_fields = [
            "id", "code", "name", "unit", "category",
            "is_finished_product", "created_at"
        ]
        for field in required_fields:
            assert field in item, \
                f"Product item should include '{field}'"

    def test_product_detail_has_all_required_fields(self, client, seed_test_products):
        """Test product detail response structure"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        # Per API spec (knowledge/api-specifications.md lines 58-76)
        required_fields = [
            "id", "code", "name", "unit", "category",
            "is_finished_product", "bill_of_materials", "created_at"
        ]
        for field in required_fields:
            assert field in data, \
                f"Product detail should include '{field}'"

    def test_bom_item_structure(self, client, seed_test_products):
        """Test BOM item structure in product detail"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        bom_item = data["bill_of_materials"][0]

        # Per API spec (knowledge/api-specifications.md lines 67-71)
        required_fields = [
            "child_product_id", "child_product_name", "quantity", "unit"
        ]
        for field in required_fields:
            assert field in bom_item, \
                f"BOM item should include '{field}'"


# ============================================================================
# Test Scenario 7: Data types validation
# ============================================================================

class TestDataTypes:
    """Test that response data types are correct"""

    def test_product_id_is_string(self, client, seed_test_products):
        """Test that product ID is a string"""
        response = client.get("/api/v1/products")
        data = response.json()

        item = data["items"][0]
        assert isinstance(item["id"], str), \
            f"Product ID should be string, got {type(item['id'])}"

    def test_is_finished_product_is_boolean(self, client, seed_test_products):
        """Test that is_finished_product is a boolean"""
        response = client.get("/api/v1/products")
        data = response.json()

        item = data["items"][0]
        assert isinstance(item["is_finished_product"], bool), \
            f"is_finished_product should be boolean, got {type(item['is_finished_product'])}"

    def test_total_is_integer(self, client, seed_test_products):
        """Test that total count is an integer"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert isinstance(data["total"], int), \
            f"Total should be integer, got {type(data['total'])}"

    def test_bom_quantity_is_numeric(self, client, seed_test_products):
        """Test that BOM quantity is numeric"""
        response = client.get("/api/v1/products/tshirt-001")
        data = response.json()

        bom_item = data["bill_of_materials"][0]
        quantity = bom_item["quantity"]

        # Should be float or int
        assert isinstance(quantity, (int, float)), \
            f"Quantity should be numeric, got {type(quantity)}"
        assert quantity > 0, \
            f"Quantity should be positive, got {quantity}"


# ============================================================================
# Test Scenario 8: Edge cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_list_products_with_no_data(self, client):
        """Test listing products when database is empty"""
        response = client.get("/api/v1/products")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 0, \
            "Empty database should return total=0"
        assert len(data["items"]) == 0, \
            "Empty database should return empty items list"

    def test_pagination_offset_beyond_total(self, client, seed_test_products):
        """Test offset beyond total count"""
        total_count = seed_test_products["total_count"]
        response = client.get(f"/api/v1/products?offset={total_count + 10}")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 0, \
            "Offset beyond total should return empty list"

    def test_product_with_special_characters_in_id(self, client, db_session):
        """Test product ID can be retrieved correctly"""
        # Create product with hyphenated ID
        special_product = Product(
            id="test-product-123",
            code="TEST-SPECIAL",
            name="Test Product",
            unit="unit",
            is_finished_product=True
        )
        db_session.add(special_product)
        db_session.commit()

        response = client.get("/api/v1/products/test-product-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-product-123"
