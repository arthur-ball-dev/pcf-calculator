"""
Test Product Search API - has_bom Filter Parameter
TASK-FE-P8-001: Add has_bom filter to products search endpoint

Test Scenarios:
1. has_bom=true returns only products with BOM entries
2. has_bom=false returns all products (existing behavior)
3. Omitting has_bom returns all products (existing behavior)
4. has_bom combined with other filters (query, industry, is_finished_product)
5. has_bom with pagination

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (parameter does not exist yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from decimal import Decimal

from backend.models import (
    Base,
    Product,
    ProductCategory,
    BillOfMaterials,
)
from backend.main import app
from backend.database.connection import get_db


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing with threading support."""
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

    # Enable foreign key constraints for SQLite
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
def seed_categories(db_session):
    """Seed test database with product categories."""
    electronics = ProductCategory(
        id="cat-electronics",
        code="ELEC",
        name="Electronics",
        level=0,
        industry_sector="electronics"
    )

    apparel = ProductCategory(
        id="cat-apparel",
        code="APRL",
        name="Apparel",
        level=0,
        industry_sector="apparel"
    )

    db_session.add_all([electronics, apparel])
    db_session.commit()

    laptops = ProductCategory(
        id="cat-laptops",
        code="ELEC-LAPTOP",
        name="Laptops",
        parent_id="cat-electronics",
        level=1,
        industry_sector="electronics"
    )

    mobile = ProductCategory(
        id="cat-mobile",
        code="ELEC-MOBILE",
        name="Mobile Devices",
        parent_id="cat-electronics",
        level=1,
        industry_sector="electronics"
    )

    db_session.add_all([laptops, mobile])
    db_session.commit()

    return {
        "electronics": electronics,
        "apparel": apparel,
        "laptops": laptops,
        "mobile": mobile,
    }


@pytest.fixture(scope="function")
def seed_products(db_session, seed_categories):
    """
    Seed test database with products for has_bom filter testing.

    Creates 10 products:
    - 7 finished products
    - 3 components (not finished)
    """
    products = [
        # Finished products - Laptops
        Product(
            id="prod-laptop-1",
            code="LAPTOP-001",
            name="Business Laptop 14-inch",
            description="14-inch business laptop",
            unit="unit",
            category_id="cat-laptops",
            is_finished_product=True,
        ),
        Product(
            id="prod-laptop-2",
            code="LAPTOP-002",
            name="Gaming Laptop 17-inch",
            description="High-performance gaming laptop",
            unit="unit",
            category_id="cat-laptops",
            is_finished_product=True,
        ),
        Product(
            id="prod-laptop-3",
            code="LAPTOP-003",
            name="Ultrabook Pro",
            description="Ultralight laptop for professionals",
            unit="unit",
            category_id="cat-laptops",
            is_finished_product=True,
        ),
        # Finished products - Mobile
        Product(
            id="prod-phone-1",
            code="PHONE-001",
            name="Smartphone Pro Max",
            description="Flagship smartphone",
            unit="unit",
            category_id="cat-mobile",
            is_finished_product=True,
        ),
        Product(
            id="prod-tablet-1",
            code="TABLET-001",
            name="Tablet Air",
            description="Lightweight tablet",
            unit="unit",
            category_id="cat-mobile",
            is_finished_product=True,
        ),
        # Finished products - Apparel
        Product(
            id="prod-tshirt-1",
            code="TSHIRT-001",
            name="Cotton T-Shirt Basic",
            description="Simple cotton t-shirt",
            unit="unit",
            category_id="cat-apparel",
            is_finished_product=True,
        ),
        Product(
            id="prod-polo-1",
            code="POLO-001",
            name="Polo Shirt Classic",
            description="Classic polo shirt",
            unit="unit",
            category_id="cat-apparel",
            is_finished_product=True,
        ),
        # Components (not finished products)
        Product(
            id="prod-cpu-1",
            code="CPU-001",
            name="Laptop CPU i7",
            description="High-performance laptop processor",
            unit="unit",
            category_id="cat-electronics",
            is_finished_product=False,
        ),
        Product(
            id="prod-battery-1",
            code="BATTERY-001",
            name="Laptop Battery Pack",
            description="Lithium-ion battery for laptops",
            unit="unit",
            category_id="cat-electronics",
            is_finished_product=False,
        ),
        Product(
            id="prod-misc-1",
            code="MISC-001",
            name="Miscellaneous Component",
            description="Generic component",
            unit="kg",
            category_id=None,
            is_finished_product=False,
        ),
    ]

    db_session.add_all(products)
    db_session.commit()

    return {
        "laptop_1": products[0],
        "laptop_2": products[1],
        "laptop_3": products[2],
        "phone_1": products[3],
        "tablet_1": products[4],
        "tshirt_1": products[5],
        "polo_1": products[6],
        "cpu_1": products[7],
        "battery_1": products[8],
        "misc_1": products[9],
        "total_count": 10,
        "finished_count": 7,
        "component_count": 3,
    }


@pytest.fixture(scope="function")
def seed_bom_entries(db_session, seed_products):
    """
    Seed test database with BOM entries for has_bom filter testing.

    Creates BOM relationships:
    - laptop_1 has components: cpu_1, battery_1 (2 BOM entries)
    - laptop_2 has components: cpu_1 (1 BOM entry)
    - phone_1 has components: battery_1 (1 BOM entry)

    Products WITH BOM: laptop_1, laptop_2, phone_1 (3 products)
    Products WITHOUT BOM: laptop_3, tablet_1, tshirt_1, polo_1, cpu_1, battery_1, misc_1 (7 products)
    """
    bom_entries = [
        # laptop_1 has cpu and battery
        BillOfMaterials(
            id="bom-laptop1-cpu",
            parent_product_id="prod-laptop-1",
            child_product_id="prod-cpu-1",
            quantity=Decimal("1.0"),
            unit="unit",
            notes="Main processor"
        ),
        BillOfMaterials(
            id="bom-laptop1-battery",
            parent_product_id="prod-laptop-1",
            child_product_id="prod-battery-1",
            quantity=Decimal("1.0"),
            unit="unit",
            notes="Main battery"
        ),
        # laptop_2 has cpu
        BillOfMaterials(
            id="bom-laptop2-cpu",
            parent_product_id="prod-laptop-2",
            child_product_id="prod-cpu-1",
            quantity=Decimal("1.0"),
            unit="unit",
            notes="Gaming processor"
        ),
        # phone_1 has battery
        BillOfMaterials(
            id="bom-phone1-battery",
            parent_product_id="prod-phone-1",
            child_product_id="prod-battery-1",
            quantity=Decimal("1.0"),
            unit="unit",
            notes="Phone battery"
        ),
    ]

    db_session.add_all(bom_entries)
    db_session.commit()

    return {
        "entries": bom_entries,
        "products_with_bom_count": 3,
        "products_without_bom_count": 7,
        "products_with_bom_ids": ["prod-laptop-1", "prod-laptop-2", "prod-phone-1"],
    }


# ============================================================================
# Test Scenario: Filter by has_bom (TASK-FE-P8-001)
# ============================================================================

class TestFilterByHasBom:
    """
    Test filtering by has_bom parameter.

    TASK-FE-P8-001: Add has_bom filter to only return products
    that have at least one entry in bill_of_materials table
    where they are the parent_product_id.
    """

    def test_has_bom_true_returns_only_products_with_bom(
        self, client, seed_products, seed_bom_entries
    ):
        """Test that has_bom=true returns only products with BOM entries."""
        response = client.get("/api/v1/products/search?has_bom=true")
        data = response.json()

        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}"
        assert data["total"] == seed_bom_entries["products_with_bom_count"], \
            f"Expected {seed_bom_entries['products_with_bom_count']} products with BOM, got {data['total']}"

        # Verify all returned products are in the expected list
        returned_ids = [item["id"] for item in data["items"]]
        for product_id in returned_ids:
            assert product_id in seed_bom_entries["products_with_bom_ids"], \
                f"Product {product_id} should have BOM entries"

    def test_has_bom_false_returns_all_products(
        self, client, seed_products, seed_bom_entries
    ):
        """Test that has_bom=false returns all products (existing behavior)."""
        response = client.get("/api/v1/products/search?has_bom=false")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["total_count"], \
            f"Expected {seed_products['total_count']} products, got {data['total']}"

    def test_has_bom_not_provided_returns_all_products(
        self, client, seed_products, seed_bom_entries
    ):
        """Test that omitting has_bom returns all products (existing behavior)."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["total_count"], \
            f"Expected {seed_products['total_count']} products, got {data['total']}"

    def test_has_bom_with_query_filter(
        self, client, seed_products, seed_bom_entries
    ):
        """Test combining has_bom=true with search query."""
        # Search for 'laptop' with has_bom=true
        # Should return laptop_1 and laptop_2 (both have BOM and match 'laptop')
        response = client.get("/api/v1/products/search?query=laptop&has_bom=true")
        data = response.json()

        assert response.status_code == 200

        # All returned products should:
        # 1. Match 'laptop' in name or description
        # 2. Have BOM entries
        for item in data["items"]:
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower, \
                f"Product {item['code']} should match 'laptop'"
            assert item["id"] in seed_bom_entries["products_with_bom_ids"], \
                f"Product {item['id']} should have BOM entries"

    def test_has_bom_with_is_finished_product_filter(
        self, client, seed_products, seed_bom_entries
    ):
        """Test combining has_bom=true with is_finished_product filter."""
        response = client.get(
            "/api/v1/products/search?has_bom=true&is_finished_product=true"
        )
        data = response.json()

        assert response.status_code == 200

        # All products with BOM in test data are finished products
        for item in data["items"]:
            assert item["is_finished_product"] is True
            assert item["id"] in seed_bom_entries["products_with_bom_ids"]

    def test_has_bom_with_industry_filter(
        self, client, seed_products, seed_bom_entries, seed_categories
    ):
        """Test combining has_bom=true with industry filter."""
        response = client.get(
            "/api/v1/products/search?has_bom=true&industry=electronics"
        )
        data = response.json()

        assert response.status_code == 200

        # All products with BOM in test data are in electronics
        for item in data["items"]:
            assert item["id"] in seed_bom_entries["products_with_bom_ids"]
            if item.get("category"):
                assert item["category"]["industry_sector"] == "electronics"

    def test_has_bom_with_pagination(
        self, client, seed_products, seed_bom_entries
    ):
        """Test has_bom=true respects pagination."""
        response = client.get("/api/v1/products/search?has_bom=true&limit=2&offset=0")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) <= 2, "Should respect limit"
        assert data["total"] == seed_bom_entries["products_with_bom_count"], \
            "Total should reflect all products with BOM"

        # Test offset
        response2 = client.get("/api/v1/products/search?has_bom=true&limit=2&offset=2")
        data2 = response2.json()

        # IDs should not overlap between pages
        first_ids = {item["id"] for item in data["items"]}
        second_ids = {item["id"] for item in data2["items"]}
        assert first_ids.isdisjoint(second_ids), \
            "Pagination should not return duplicate items"

    def test_has_bom_true_empty_when_no_bom_exists(self, client, seed_products):
        """Test has_bom=true returns empty when no BOM entries exist."""
        # This test uses seed_products without seed_bom_entries
        response = client.get("/api/v1/products/search?has_bom=true")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 0, "Should return 0 when no products have BOM"
        assert data["items"] == [], "Items should be empty array"

    def test_has_bom_combined_with_all_filters(
        self, client, seed_products, seed_bom_entries, seed_categories
    ):
        """Test has_bom with multiple other filters combined."""
        response = client.get(
            "/api/v1/products/search?"
            "has_bom=true&"
            "query=laptop&"
            "industry=electronics&"
            "is_finished_product=true&"
            "limit=10"
        )
        data = response.json()

        assert response.status_code == 200

        # All results should satisfy all criteria
        for item in data["items"]:
            assert item["id"] in seed_bom_entries["products_with_bom_ids"]
            assert item["is_finished_product"] is True
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower
