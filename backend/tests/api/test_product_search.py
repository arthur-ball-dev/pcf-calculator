"""
Test Product Search API Endpoint
TASK-API-P5-002: Enhanced Product Search - Phase A Tests

Test Scenarios (per products-search-contract.yaml):
1. Search with query string (relevance ranking)
2. Search without query (returns all products)
3. Filter by category_id
4. Filter by industry
5. Filter by manufacturer (partial match)
6. Filter by country_of_origin
7. Filter by is_finished_product
8. Combined filters + search
9. Pagination (limit, offset, has_more)
10. Empty results handling
11. Invalid category_id (422)
12. Query too short (400 if <2 chars)

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (endpoint does not exist yet)
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
    """
    Seed test database with product categories.

    Creates hierarchy:
    - Electronics (level 0)
      - Computers (level 1)
        - Laptops (level 2)
      - Mobile Devices (level 1)
    - Apparel (level 0)
      - Tops (level 1)
    """
    # Root categories
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

    # Level 1 categories
    computers = ProductCategory(
        id="cat-computers",
        code="ELEC-COMP",
        name="Computers",
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

    tops = ProductCategory(
        id="cat-tops",
        code="APRL-TOPS",
        name="Tops",
        parent_id="cat-apparel",
        level=1,
        industry_sector="apparel"
    )

    db_session.add_all([computers, mobile, tops])
    db_session.commit()

    # Level 2 categories
    laptops = ProductCategory(
        id="cat-laptops",
        code="ELEC-COMP-LAPTOP",
        name="Laptops",
        parent_id="cat-computers",
        level=2,
        industry_sector="electronics"
    )

    db_session.add(laptops)
    db_session.commit()

    return {
        "electronics": electronics,
        "apparel": apparel,
        "computers": computers,
        "mobile": mobile,
        "tops": tops,
        "laptops": laptops,
    }


@pytest.fixture(scope="function")
def seed_products(db_session, seed_categories):
    """
    Seed test database with products for search testing.

    Creates products across different categories, manufacturers,
    and countries to test filtering capabilities.
    """
    products = [
        # Laptops (electronics)
        Product(
            id="prod-laptop-1",
            code="LAPTOP-001",
            name="Business Laptop 14-inch",
            description="14-inch business laptop with aluminum chassis",
            unit="unit",
            category_id="cat-laptops",
            manufacturer="Acme Tech",
            country_of_origin="CN",
            is_finished_product=True,
            search_vector="business laptop 14 inch aluminum chassis acme tech"
        ),
        Product(
            id="prod-laptop-2",
            code="LAPTOP-002",
            name="Gaming Laptop 17-inch",
            description="High-performance gaming laptop with RGB keyboard",
            unit="unit",
            category_id="cat-laptops",
            manufacturer="GameTech Inc",
            country_of_origin="TW",
            is_finished_product=True,
            search_vector="gaming laptop 17 inch rgb keyboard gametech"
        ),
        Product(
            id="prod-laptop-3",
            code="LAPTOP-003",
            name="Ultrabook Pro",
            description="Ultralight laptop for professionals",
            unit="unit",
            category_id="cat-laptops",
            manufacturer="Acme Tech",
            country_of_origin="US",
            is_finished_product=True,
            search_vector="ultrabook pro ultralight laptop professionals acme tech"
        ),
        # Mobile devices (electronics)
        Product(
            id="prod-phone-1",
            code="PHONE-001",
            name="Smartphone Pro Max",
            description="Flagship smartphone with advanced camera",
            unit="unit",
            category_id="cat-mobile",
            manufacturer="TechGiant Corp",
            country_of_origin="CN",
            is_finished_product=True,
            search_vector="smartphone pro max flagship camera techgiant"
        ),
        Product(
            id="prod-tablet-1",
            code="TABLET-001",
            name="Tablet Air",
            description="Lightweight tablet for productivity",
            unit="unit",
            category_id="cat-mobile",
            manufacturer="TechGiant Corp",
            country_of_origin="CN",
            is_finished_product=True,
            search_vector="tablet air lightweight productivity techgiant"
        ),
        # Apparel
        Product(
            id="prod-tshirt-1",
            code="TSHIRT-001",
            name="Cotton T-Shirt Basic",
            description="Simple cotton t-shirt for everyday wear",
            unit="unit",
            category_id="cat-tops",
            manufacturer="Fashion Co",
            country_of_origin="BD",
            is_finished_product=True,
            search_vector="cotton t-shirt basic simple everyday wear fashion"
        ),
        Product(
            id="prod-polo-1",
            code="POLO-001",
            name="Polo Shirt Classic",
            description="Classic polo shirt in cotton blend",
            unit="unit",
            category_id="cat-tops",
            manufacturer="Fashion Co",
            country_of_origin="VN",
            is_finished_product=True,
            search_vector="polo shirt classic cotton blend fashion"
        ),
        # Components (not finished products)
        Product(
            id="prod-cpu-1",
            code="CPU-001",
            name="Laptop CPU i7",
            description="High-performance laptop processor",
            unit="unit",
            category_id="cat-computers",
            manufacturer="ChipMaker Ltd",
            country_of_origin="US",
            is_finished_product=False,
            search_vector="laptop cpu i7 processor chipmaker"
        ),
        Product(
            id="prod-battery-1",
            code="BATTERY-001",
            name="Laptop Battery Pack",
            description="Lithium-ion battery for laptops",
            unit="unit",
            category_id="cat-computers",
            manufacturer="PowerCell Inc",
            country_of_origin="JP",
            is_finished_product=False,
            search_vector="laptop battery pack lithium ion powercell"
        ),
        # Product without category
        Product(
            id="prod-misc-1",
            code="MISC-001",
            name="Miscellaneous Component",
            description="Generic component without category",
            unit="kg",
            category_id=None,
            manufacturer="Generic Mfg",
            country_of_origin="DE",
            is_finished_product=False,
            search_vector="miscellaneous component generic"
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
        "electronics_count": 7,
        "apparel_count": 2,
    }


# ============================================================================
# Test Scenario 1: Search with query string (relevance ranking)
# ============================================================================

class TestSearchWithQuery:
    """Test full-text search with query string."""

    def test_search_returns_200(self, client, seed_products):
        """Test that search endpoint returns 200 OK."""
        response = client.get("/api/v1/products/search?query=laptop")

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

    def test_search_returns_matching_products(self, client, seed_products):
        """Test that search returns products matching query."""
        response = client.get("/api/v1/products/search?query=laptop")
        data = response.json()

        assert "items" in data, "Response should include 'items' field"
        assert len(data["items"]) > 0, "Should find products matching 'laptop'"

        # All results should contain 'laptop' in name or description
        for item in data["items"]:
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower, \
                f"Product {item['code']} should match 'laptop'"

    def test_search_returns_relevance_score(self, client, seed_products):
        """Test that search results include relevance_score when query provided."""
        response = client.get("/api/v1/products/search?query=laptop")
        data = response.json()

        assert len(data["items"]) > 0, "Should have results"

        for item in data["items"]:
            assert "relevance_score" in item, \
                "Each item should have relevance_score when query provided"
            assert isinstance(item["relevance_score"], (int, float, type(None))), \
                "relevance_score should be numeric or null"

    def test_search_case_insensitive(self, client, seed_products):
        """Test that search is case-insensitive."""
        response_lower = client.get("/api/v1/products/search?query=laptop")
        response_upper = client.get("/api/v1/products/search?query=LAPTOP")
        response_mixed = client.get("/api/v1/products/search?query=LaPtOp")

        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()

        # All should return same number of results
        assert data_lower["total"] == data_upper["total"] == data_mixed["total"], \
            "Search should be case-insensitive"

    def test_search_partial_match(self, client, seed_products):
        """Test that search matches partial words."""
        response = client.get("/api/v1/products/search?query=ultra")
        data = response.json()

        # Should match "Ultrabook Pro"
        assert data["total"] >= 1, "Should find 'ultra' in Ultrabook"

        codes = [item["code"] for item in data["items"]]
        assert "LAPTOP-003" in codes, "Should find Ultrabook Pro"

    def test_search_multiple_terms(self, client, seed_products):
        """Test search with multiple terms."""
        response = client.get("/api/v1/products/search?query=business%20laptop")
        data = response.json()

        assert data["total"] >= 1, "Should find products matching 'business laptop'"

    def test_search_description_match(self, client, seed_products):
        """Test that search matches content in description."""
        response = client.get("/api/v1/products/search?query=aluminum")
        data = response.json()

        # Should match Business Laptop (has "aluminum chassis" in description)
        assert data["total"] >= 1, "Should find 'aluminum' in description"


# ============================================================================
# Test Scenario 2: Search without query (returns all products)
# ============================================================================

class TestSearchWithoutQuery:
    """Test search endpoint without query parameter."""

    def test_search_without_query_returns_all(self, client, seed_products):
        """Test that omitting query returns all products."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["total_count"], \
            f"Expected {seed_products['total_count']} products, got {data['total']}"

    def test_search_without_query_no_relevance_score(self, client, seed_products):
        """Test that relevance_score is null when no query provided."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert len(data["items"]) > 0, "Should have results"

        for item in data["items"]:
            # relevance_score should be null or not present when no query
            if "relevance_score" in item:
                assert item["relevance_score"] is None, \
                    "relevance_score should be null when no query provided"


# ============================================================================
# Test Scenario 3: Filter by category_id
# ============================================================================

class TestFilterByCategory:
    """Test filtering by category_id."""

    def test_filter_by_category_id(self, client, seed_products, seed_categories):
        """Test filtering products by category_id."""
        laptops_cat_id = seed_categories["laptops"].id

        response = client.get(f"/api/v1/products/search?category_id={laptops_cat_id}")
        data = response.json()

        assert response.status_code == 200

        # All results should be in laptops category
        for item in data["items"]:
            if item.get("category"):
                assert item["category"]["id"] == laptops_cat_id, \
                    f"Product should be in laptops category"

    def test_filter_category_with_search(self, client, seed_products, seed_categories):
        """Test combining category filter with search query."""
        computers_cat_id = seed_categories["computers"].id

        response = client.get(
            f"/api/v1/products/search?query=laptop&category_id={computers_cat_id}"
        )
        data = response.json()

        assert response.status_code == 200

        # Results should match both query and category
        for item in data["items"]:
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower

    def test_filter_invalid_category_id(self, client, seed_products):
        """Test that invalid category_id returns 422."""
        # Non-existent UUID
        fake_uuid = "00000000000000000000000000000000"

        response = client.get(f"/api/v1/products/search?category_id={fake_uuid}")

        # Per contract: Invalid category returns 422 with INVALID_CATEGORY code
        assert response.status_code == 422, \
            f"Expected 422 for invalid category_id, got {response.status_code}"

    def test_filter_malformed_category_id(self, client, seed_products):
        """Test that malformed category_id returns 400/422."""
        response = client.get("/api/v1/products/search?category_id=not-a-uuid")

        # Should return validation error (400 or 422)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for malformed category_id, got {response.status_code}"


# ============================================================================
# Test Scenario 4: Filter by industry
# ============================================================================

class TestFilterByIndustry:
    """Test filtering by industry sector."""

    def test_filter_by_industry_electronics(self, client, seed_products):
        """Test filtering by industry=electronics."""
        response = client.get("/api/v1/products/search?industry=electronics")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["electronics_count"], \
            f"Expected {seed_products['electronics_count']} electronics products"

        # All results should be in electronics industry
        for item in data["items"]:
            if item.get("category"):
                assert item["category"]["industry_sector"] == "electronics"

    def test_filter_by_industry_apparel(self, client, seed_products):
        """Test filtering by industry=apparel."""
        response = client.get("/api/v1/products/search?industry=apparel")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["apparel_count"], \
            f"Expected {seed_products['apparel_count']} apparel products"

    def test_filter_by_industry_with_query(self, client, seed_products):
        """Test combining industry filter with search query."""
        response = client.get("/api/v1/products/search?query=cotton&industry=apparel")
        data = response.json()

        assert response.status_code == 200

        # Should find cotton t-shirt in apparel
        for item in data["items"]:
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "cotton" in name_lower or "cotton" in desc_lower

    def test_filter_invalid_industry(self, client, seed_products):
        """Test that invalid industry returns 400."""
        response = client.get("/api/v1/products/search?industry=invalid_industry")

        # Should return validation error (industry not in enum)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for invalid industry, got {response.status_code}"


# ============================================================================
# Test Scenario 5: Filter by manufacturer (partial match)
# ============================================================================

class TestFilterByManufacturer:
    """Test filtering by manufacturer name."""

    def test_filter_by_manufacturer_exact(self, client, seed_products):
        """Test filtering by exact manufacturer name."""
        response = client.get("/api/v1/products/search?manufacturer=Acme%20Tech")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] >= 2, "Should find at least 2 Acme Tech products"

        for item in data["items"]:
            assert item["manufacturer"] == "Acme Tech"

    def test_filter_by_manufacturer_partial(self, client, seed_products):
        """Test filtering by partial manufacturer name."""
        response = client.get("/api/v1/products/search?manufacturer=Acme")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] >= 2, "Should find Acme Tech products with partial match"

        for item in data["items"]:
            assert "Acme" in item["manufacturer"]

    def test_filter_manufacturer_case_insensitive(self, client, seed_products):
        """Test that manufacturer filter is case-insensitive."""
        response_lower = client.get("/api/v1/products/search?manufacturer=acme")
        response_upper = client.get("/api/v1/products/search?manufacturer=ACME")

        data_lower = response_lower.json()
        data_upper = response_upper.json()

        assert data_lower["total"] == data_upper["total"], \
            "Manufacturer filter should be case-insensitive"

    def test_filter_manufacturer_with_query(self, client, seed_products):
        """Test combining manufacturer filter with search."""
        response = client.get(
            "/api/v1/products/search?query=laptop&manufacturer=Acme"
        )
        data = response.json()

        assert response.status_code == 200

        # Should find Acme laptops
        for item in data["items"]:
            assert "Acme" in item["manufacturer"]
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower


# ============================================================================
# Test Scenario 6: Filter by country_of_origin
# ============================================================================

class TestFilterByCountryOfOrigin:
    """Test filtering by country of origin."""

    def test_filter_by_country(self, client, seed_products):
        """Test filtering by country_of_origin."""
        response = client.get("/api/v1/products/search?country_of_origin=CN")
        data = response.json()

        assert response.status_code == 200

        # All results should be from China
        for item in data["items"]:
            assert item["country_of_origin"] == "CN"

    def test_filter_country_us(self, client, seed_products):
        """Test filtering products from US."""
        response = client.get("/api/v1/products/search?country_of_origin=US")
        data = response.json()

        assert response.status_code == 200

        for item in data["items"]:
            assert item["country_of_origin"] == "US"

    def test_filter_country_invalid_format(self, client, seed_products):
        """Test that invalid country code format returns 400."""
        # Country code should be 2 uppercase letters
        response = client.get("/api/v1/products/search?country_of_origin=USA")

        # Should fail validation (not ^[A-Z]{2}$)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for invalid country code, got {response.status_code}"


# ============================================================================
# Test Scenario 7: Filter by is_finished_product
# ============================================================================

class TestFilterByIsFinishedProduct:
    """Test filtering by is_finished_product flag."""

    def test_filter_finished_products_only(self, client, seed_products):
        """Test filtering for finished products only."""
        response = client.get("/api/v1/products/search?is_finished_product=true")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["finished_count"], \
            f"Expected {seed_products['finished_count']} finished products"

        for item in data["items"]:
            assert item["is_finished_product"] is True

    def test_filter_components_only(self, client, seed_products):
        """Test filtering for components (not finished)."""
        response = client.get("/api/v1/products/search?is_finished_product=false")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == seed_products["component_count"], \
            f"Expected {seed_products['component_count']} components"

        for item in data["items"]:
            assert item["is_finished_product"] is False


# ============================================================================
# Test Scenario 8: Combined filters + search
# ============================================================================

class TestCombinedFilters:
    """Test combining multiple filters with search."""

    def test_query_plus_category_plus_manufacturer(
        self, client, seed_products, seed_categories
    ):
        """Test search with query, category, and manufacturer filters."""
        response = client.get(
            "/api/v1/products/search?"
            "query=laptop&"
            f"category_id={seed_categories['laptops'].id}&"
            "manufacturer=Acme"
        )
        data = response.json()

        assert response.status_code == 200

        for item in data["items"]:
            # Should match all criteria
            assert "Acme" in item["manufacturer"]
            name_lower = item["name"].lower()
            desc_lower = (item.get("description") or "").lower()
            assert "laptop" in name_lower or "laptop" in desc_lower

    def test_industry_plus_country_plus_finished(self, client, seed_products):
        """Test filtering by industry, country, and is_finished_product."""
        response = client.get(
            "/api/v1/products/search?"
            "industry=electronics&"
            "country_of_origin=CN&"
            "is_finished_product=true"
        )
        data = response.json()

        assert response.status_code == 200

        for item in data["items"]:
            assert item["country_of_origin"] == "CN"
            assert item["is_finished_product"] is True

    def test_all_filters_combined(
        self, client, seed_products, seed_categories
    ):
        """Test using all filters together."""
        response = client.get(
            "/api/v1/products/search?"
            "query=laptop&"
            "industry=electronics&"
            "manufacturer=Acme&"
            "country_of_origin=CN&"
            "is_finished_product=true&"
            "limit=10"
        )
        data = response.json()

        assert response.status_code == 200

        # Results should satisfy all criteria
        for item in data["items"]:
            assert item["is_finished_product"] is True
            assert "Acme" in item["manufacturer"]
            assert item["country_of_origin"] == "CN"


# ============================================================================
# Test Scenario 9: Pagination (limit, offset, has_more)
# ============================================================================

class TestSearchPagination:
    """Test pagination parameters for search."""

    def test_pagination_limit(self, client, seed_products):
        """Test that limit parameter restricts results."""
        response = client.get("/api/v1/products/search?limit=3")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) <= 3, "Should return at most 3 items"
        assert data["limit"] == 3, "Response should include limit=3"

    def test_pagination_offset(self, client, seed_products):
        """Test that offset parameter skips results."""
        # Get first 3 products
        response1 = client.get("/api/v1/products/search?limit=3&offset=0")
        data1 = response1.json()
        first_ids = [item["id"] for item in data1["items"]]

        # Get next 3 products
        response2 = client.get("/api/v1/products/search?limit=3&offset=3")
        data2 = response2.json()
        next_ids = [item["id"] for item in data2["items"]]

        # IDs should not overlap
        assert len(set(first_ids) & set(next_ids)) == 0, \
            "Offset should skip previous results"
        assert data2["offset"] == 3, "Response should include offset=3"

    def test_pagination_has_more_true(self, client, seed_products):
        """Test has_more is true when more results exist."""
        response = client.get("/api/v1/products/search?limit=3&offset=0")
        data = response.json()

        assert response.status_code == 200

        # With 10 products and limit=3, has_more should be true
        if data["total"] > 3:
            assert data["has_more"] is True, \
                "has_more should be true when more results exist"

    def test_pagination_has_more_false(self, client, seed_products):
        """Test has_more is false on last page."""
        total = seed_products["total_count"]
        offset = total - 2 if total > 2 else 0

        response = client.get(f"/api/v1/products/search?limit=100&offset={offset}")
        data = response.json()

        assert response.status_code == 200

        # On last page, has_more should be false
        if data["offset"] + len(data["items"]) >= data["total"]:
            assert data["has_more"] is False, \
                "has_more should be false on last page"

    def test_pagination_default_values(self, client, seed_products):
        """Test default pagination values."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert "limit" in data, "Response should include limit"
        assert "offset" in data, "Response should include offset"
        assert data["offset"] == 0, "Default offset should be 0"
        # Per contract: default limit is 50
        assert data["limit"] == 50, "Default limit should be 50"

    def test_pagination_limit_max(self, client, seed_products):
        """Test that limit has maximum value of 100."""
        response = client.get("/api/v1/products/search?limit=200")

        # Per contract: max limit is 100
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for limit>100, got {response.status_code}"

    def test_pagination_limit_min(self, client, seed_products):
        """Test that limit has minimum value of 1."""
        response = client.get("/api/v1/products/search?limit=0")

        # Per contract: min limit is 1
        assert response.status_code == 422, \
            f"Expected 422 for limit=0, got {response.status_code}"

    def test_pagination_offset_min(self, client, seed_products):
        """Test that offset cannot be negative."""
        response = client.get("/api/v1/products/search?offset=-1")

        assert response.status_code == 422, \
            f"Expected 422 for negative offset, got {response.status_code}"


# ============================================================================
# Test Scenario 10: Empty results handling
# ============================================================================

class TestEmptyResults:
    """Test handling of empty search results."""

    def test_empty_results_for_no_match(self, client, seed_products):
        """Test empty results when no products match."""
        response = client.get("/api/v1/products/search?query=xyz123nonexistent")
        data = response.json()

        assert response.status_code == 200, \
            "Should return 200 even with no results"
        assert data["items"] == [], \
            "Items should be empty array"
        assert data["total"] == 0, \
            "Total should be 0"
        assert data["has_more"] is False, \
            "has_more should be false for empty results"

    def test_empty_results_for_filter_no_match(self, client, seed_products):
        """Test empty results when filters match nothing."""
        response = client.get(
            "/api/v1/products/search?"
            "industry=electronics&"
            "country_of_origin=XX"  # No products from XX
        )
        data = response.json()

        assert response.status_code == 200
        assert data["items"] == []
        assert data["total"] == 0


# ============================================================================
# Test Scenario 11: Query validation
# ============================================================================

class TestQueryValidation:
    """Test query parameter validation."""

    def test_query_too_short(self, client, seed_products):
        """Test that query <2 chars returns 400."""
        response = client.get("/api/v1/products/search?query=a")

        # Per contract: min_length is 2
        assert response.status_code == 400, \
            f"Expected 400 for query<2 chars, got {response.status_code}"

    def test_query_empty_string(self, client, seed_products):
        """Test that empty query string is treated as no query."""
        response = client.get("/api/v1/products/search?query=")
        data = response.json()

        # Empty string should either return all or validation error
        assert response.status_code in [200, 400], \
            f"Empty query should return 200 (all) or 400 (validation)"

    def test_query_max_length(self, client, seed_products):
        """Test that query respects max length (200 chars)."""
        long_query = "a" * 250

        response = client.get(f"/api/v1/products/search?query={long_query}")

        # Per contract: max_length is 200
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for query>200 chars, got {response.status_code}"


# ============================================================================
# Test Scenario 12: Response structure validation
# ============================================================================

class TestResponseStructure:
    """Test that response structure matches contract."""

    def test_response_has_required_fields(self, client, seed_products):
        """Test that response has all required top-level fields."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        required_fields = ["items", "total", "limit", "offset", "has_more"]
        for field in required_fields:
            assert field in data, \
                f"Response should include '{field}' field"

    def test_product_item_has_required_fields(self, client, seed_products):
        """Test that each product item has required fields."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        assert len(data["items"]) > 0, "Should have results to test"

        required_fields = [
            "id", "code", "name", "unit",
            "is_finished_product", "created_at"
        ]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, \
                    f"Product item should have '{field}'"

    def test_category_structure_in_response(self, client, seed_products):
        """Test that category object has correct structure."""
        response = client.get("/api/v1/products/search")
        data = response.json()

        # Find a product with category
        product_with_category = next(
            (p for p in data["items"] if p.get("category")), None
        )

        if product_with_category:
            category = product_with_category["category"]

            assert "id" in category, "Category should have 'id'"
            assert "code" in category, "Category should have 'code'"
            assert "name" in category, "Category should have 'name'"
            assert "industry_sector" in category, \
                "Category should have 'industry_sector'"

    def test_total_reflects_all_matches(self, client, seed_products):
        """Test that total reflects full count regardless of pagination."""
        response = client.get("/api/v1/products/search?limit=2")
        data = response.json()

        assert data["total"] == seed_products["total_count"], \
            "Total should reflect full count, not paginated count"
        assert len(data["items"]) <= 2, \
            "Items should be limited to 2"
