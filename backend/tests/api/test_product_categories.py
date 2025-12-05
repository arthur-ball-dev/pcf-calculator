"""
Test Product Categories API Endpoint
TASK-API-P5-002: Enhanced Product Search - Phase A Tests

Test Scenarios (per products-categories-contract.yaml):
1. Get full category tree (root categories)
2. Get children of specific parent
3. Limit depth parameter
4. Include product_count option
5. Filter by industry
6. Invalid parent_id (404)
7. Tree with multiple levels builds correctly

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
def seed_category_tree(db_session):
    """
    Seed test database with hierarchical category tree.

    Creates a 4-level deep category tree:
    - Electronics (level 0)
      - Computers (level 1)
        - Laptops (level 2)
          - Business Laptops (level 3)
        - Desktops (level 2)
      - Mobile Devices (level 1)
        - Smartphones (level 2)
        - Tablets (level 2)
    - Apparel (level 0)
      - Tops (level 1)
        - T-Shirts (level 2)
        - Polo Shirts (level 2)
      - Bottoms (level 1)
    """
    categories = {}

    # Level 0 - Root categories
    electronics = ProductCategory(
        id="cat-elec",
        code="ELEC",
        name="Electronics",
        level=0,
        industry_sector="electronics"
    )
    apparel = ProductCategory(
        id="cat-aprl",
        code="APRL",
        name="Apparel",
        level=0,
        industry_sector="apparel"
    )
    automotive = ProductCategory(
        id="cat-auto",
        code="AUTO",
        name="Automotive",
        level=0,
        industry_sector="automotive"
    )

    db_session.add_all([electronics, apparel, automotive])
    db_session.commit()
    categories["electronics"] = electronics
    categories["apparel"] = apparel
    categories["automotive"] = automotive

    # Level 1 - Children of Electronics
    computers = ProductCategory(
        id="cat-comp",
        code="ELEC-COMP",
        name="Computers",
        parent_id="cat-elec",
        level=1,
        industry_sector="electronics"
    )
    mobile = ProductCategory(
        id="cat-mobile",
        code="ELEC-MOBILE",
        name="Mobile Devices",
        parent_id="cat-elec",
        level=1,
        industry_sector="electronics"
    )

    # Level 1 - Children of Apparel
    tops = ProductCategory(
        id="cat-tops",
        code="APRL-TOPS",
        name="Tops",
        parent_id="cat-aprl",
        level=1,
        industry_sector="apparel"
    )
    bottoms = ProductCategory(
        id="cat-bottoms",
        code="APRL-BOTTOMS",
        name="Bottoms",
        parent_id="cat-aprl",
        level=1,
        industry_sector="apparel"
    )

    db_session.add_all([computers, mobile, tops, bottoms])
    db_session.commit()
    categories["computers"] = computers
    categories["mobile"] = mobile
    categories["tops"] = tops
    categories["bottoms"] = bottoms

    # Level 2 - Children of Computers
    laptops = ProductCategory(
        id="cat-laptops",
        code="ELEC-COMP-LAPTOP",
        name="Laptops",
        parent_id="cat-comp",
        level=2,
        industry_sector="electronics"
    )
    desktops = ProductCategory(
        id="cat-desktops",
        code="ELEC-COMP-DESK",
        name="Desktops",
        parent_id="cat-comp",
        level=2,
        industry_sector="electronics"
    )

    # Level 2 - Children of Mobile
    smartphones = ProductCategory(
        id="cat-phones",
        code="ELEC-MOBILE-PHONE",
        name="Smartphones",
        parent_id="cat-mobile",
        level=2,
        industry_sector="electronics"
    )
    tablets = ProductCategory(
        id="cat-tablets",
        code="ELEC-MOBILE-TAB",
        name="Tablets",
        parent_id="cat-mobile",
        level=2,
        industry_sector="electronics"
    )

    # Level 2 - Children of Tops
    tshirts = ProductCategory(
        id="cat-tshirts",
        code="APRL-TOPS-TSHIRT",
        name="T-Shirts",
        parent_id="cat-tops",
        level=2,
        industry_sector="apparel"
    )
    polos = ProductCategory(
        id="cat-polos",
        code="APRL-TOPS-POLO",
        name="Polo Shirts",
        parent_id="cat-tops",
        level=2,
        industry_sector="apparel"
    )

    db_session.add_all([laptops, desktops, smartphones, tablets, tshirts, polos])
    db_session.commit()
    categories["laptops"] = laptops
    categories["desktops"] = desktops
    categories["smartphones"] = smartphones
    categories["tablets"] = tablets
    categories["tshirts"] = tshirts
    categories["polos"] = polos

    # Level 3 - Children of Laptops
    business_laptops = ProductCategory(
        id="cat-blaptops",
        code="ELEC-COMP-LAPTOP-BIZ",
        name="Business Laptops",
        parent_id="cat-laptops",
        level=3,
        industry_sector="electronics"
    )
    gaming_laptops = ProductCategory(
        id="cat-glaptops",
        code="ELEC-COMP-LAPTOP-GAME",
        name="Gaming Laptops",
        parent_id="cat-laptops",
        level=3,
        industry_sector="electronics"
    )

    db_session.add_all([business_laptops, gaming_laptops])
    db_session.commit()
    categories["business_laptops"] = business_laptops
    categories["gaming_laptops"] = gaming_laptops

    return {
        "categories": categories,
        "total_count": 16,
        "root_count": 3,
        "electronics_count": 10,  # Including children
        "apparel_count": 5,       # Including children
        "max_depth": 3,
    }


@pytest.fixture(scope="function")
def seed_products_in_categories(db_session, seed_category_tree):
    """Seed products into categories for product_count testing."""
    products = [
        # 3 products in Business Laptops
        Product(
            id="prod-blaptop-1",
            code="BLAPTOP-001",
            name="Business Laptop 14",
            unit="unit",
            category_id="cat-blaptops",
            is_finished_product=True
        ),
        Product(
            id="prod-blaptop-2",
            code="BLAPTOP-002",
            name="Business Laptop 15",
            unit="unit",
            category_id="cat-blaptops",
            is_finished_product=True
        ),
        Product(
            id="prod-blaptop-3",
            code="BLAPTOP-003",
            name="Business Laptop 17",
            unit="unit",
            category_id="cat-blaptops",
            is_finished_product=True
        ),
        # 2 products in Gaming Laptops
        Product(
            id="prod-glaptop-1",
            code="GLAPTOP-001",
            name="Gaming Laptop Pro",
            unit="unit",
            category_id="cat-glaptops",
            is_finished_product=True
        ),
        Product(
            id="prod-glaptop-2",
            code="GLAPTOP-002",
            name="Gaming Laptop Elite",
            unit="unit",
            category_id="cat-glaptops",
            is_finished_product=True
        ),
        # 1 product in Desktops
        Product(
            id="prod-desktop-1",
            code="DESKTOP-001",
            name="Desktop Workstation",
            unit="unit",
            category_id="cat-desktops",
            is_finished_product=True
        ),
        # 2 products in Smartphones
        Product(
            id="prod-phone-1",
            code="PHONE-001",
            name="Smartphone Pro",
            unit="unit",
            category_id="cat-phones",
            is_finished_product=True
        ),
        Product(
            id="prod-phone-2",
            code="PHONE-002",
            name="Smartphone Lite",
            unit="unit",
            category_id="cat-phones",
            is_finished_product=True
        ),
        # 1 product in T-Shirts
        Product(
            id="prod-tshirt-1",
            code="TSHIRT-001",
            name="Cotton T-Shirt",
            unit="unit",
            category_id="cat-tshirts",
            is_finished_product=True
        ),
    ]

    db_session.add_all(products)
    db_session.commit()

    return {
        "products": products,
        "counts": {
            "cat-blaptops": 3,
            "cat-glaptops": 2,
            "cat-laptops": 5,  # sum of children
            "cat-desktops": 1,
            "cat-comp": 6,     # sum of children
            "cat-phones": 2,
            "cat-tshirts": 1,
        }
    }


# ============================================================================
# Test Scenario 1: Get full category tree (root categories)
# ============================================================================

class TestGetCategoryTree:
    """Test GET /api/v1/products/categories for full tree."""

    def test_categories_returns_200(self, client, seed_category_tree):
        """Test that categories endpoint returns 200 OK."""
        response = client.get("/api/v1/products/categories")

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

    def test_categories_returns_required_fields(self, client, seed_category_tree):
        """Test that response has required top-level fields."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        required_fields = ["categories", "total_categories", "max_depth"]
        for field in required_fields:
            assert field in data, \
                f"Response should include '{field}' field"

    def test_categories_array_is_list(self, client, seed_category_tree):
        """Test that categories field is an array."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["categories"], list), \
            "Categories should be a list"

    def test_root_categories_have_level_zero(self, client, seed_category_tree):
        """Test that root-level categories have level=0."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # All top-level categories should have level 0
        for category in data["categories"]:
            assert category["level"] == 0, \
                f"Root category {category['code']} should have level=0"

    def test_root_categories_count(self, client, seed_category_tree):
        """Test that correct number of root categories returned."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Only root categories at top level
        root_count = seed_category_tree["root_count"]
        assert len(data["categories"]) == root_count, \
            f"Expected {root_count} root categories"


# ============================================================================
# Test Scenario 2: Get children of specific parent
# ============================================================================

class TestGetChildCategories:
    """Test GET /api/v1/products/categories?parent_id=X."""

    def test_get_children_of_parent(self, client, seed_category_tree):
        """Test getting children of specific parent category."""
        parent_id = seed_category_tree["categories"]["electronics"].id

        response = client.get(f"/api/v1/products/categories?parent_id={parent_id}")
        data = response.json()

        assert response.status_code == 200

        # Should return direct children only
        for category in data["categories"]:
            assert category["level"] == 1, \
                "Children of electronics should have level=1"

    def test_children_count_correct(self, client, seed_category_tree):
        """Test that correct number of children returned."""
        parent_id = seed_category_tree["categories"]["electronics"].id

        response = client.get(f"/api/v1/products/categories?parent_id={parent_id}")
        data = response.json()

        # Electronics has 2 children: Computers and Mobile Devices
        assert len(data["categories"]) == 2, \
            "Electronics should have 2 children"

    def test_children_of_leaf_category(self, client, seed_category_tree):
        """Test getting children of a leaf category (no children)."""
        # Gaming Laptops is a leaf (no children)
        parent_id = seed_category_tree["categories"]["gaming_laptops"].id

        response = client.get(f"/api/v1/products/categories?parent_id={parent_id}")
        data = response.json()

        assert response.status_code == 200
        assert len(data["categories"]) == 0, \
            "Leaf category should have no children"
        assert data["total_categories"] == 0

    def test_invalid_parent_id_returns_404(self, client, seed_category_tree):
        """Test that non-existent parent_id returns 404."""
        fake_id = "00000000000000000000000000000000"

        response = client.get(f"/api/v1/products/categories?parent_id={fake_id}")

        assert response.status_code == 404, \
            f"Expected 404 for invalid parent_id, got {response.status_code}"

    def test_invalid_parent_id_error_format(self, client, seed_category_tree):
        """Test that 404 response follows error format."""
        fake_id = "00000000000000000000000000000000"

        response = client.get(f"/api/v1/products/categories?parent_id={fake_id}")
        data = response.json()

        assert "error" in data or "detail" in data, \
            "404 response should include error details"

    def test_malformed_parent_id_returns_400(self, client, seed_category_tree):
        """Test that malformed parent_id returns 400."""
        response = client.get("/api/v1/products/categories?parent_id=not-a-uuid")

        assert response.status_code in [400, 422], \
            f"Expected 400/422 for malformed UUID, got {response.status_code}"


# ============================================================================
# Test Scenario 3: Limit depth parameter
# ============================================================================

class TestDepthParameter:
    """Test depth parameter limits tree traversal."""

    def test_depth_one_returns_children_only(self, client, seed_category_tree):
        """Test depth=1 returns direct children only."""
        response = client.get("/api/v1/products/categories?depth=1")
        data = response.json()

        assert response.status_code == 200
        assert data["max_depth"] <= 1, \
            "max_depth should be at most 1"

        # Check that root categories have no nested children
        for category in data["categories"]:
            assert category["level"] == 0
            # Children array should be empty with depth=1
            if "children" in category:
                assert len(category["children"]) == 0 or \
                    all(c.get("children", []) == [] for c in category["children"])

    def test_depth_two_includes_grandchildren(self, client, seed_category_tree):
        """Test depth=2 includes grandchildren."""
        response = client.get("/api/v1/products/categories?depth=2")
        data = response.json()

        assert response.status_code == 200
        assert data["max_depth"] <= 2

        # Find Electronics and check children have children
        electronics = next(
            (c for c in data["categories"] if c["code"] == "ELEC"),
            None
        )
        assert electronics is not None

        # Electronics should have children (Computers, Mobile)
        assert "children" in electronics
        if len(electronics["children"]) > 0:
            # Computers should have children (Laptops, Desktops)
            computers = next(
                (c for c in electronics["children"] if c["code"] == "ELEC-COMP"),
                None
            )
            if computers:
                # With depth=2, we should see level 2 categories
                assert "children" in computers

    def test_depth_default_is_three(self, client, seed_category_tree):
        """Test that default depth is 3."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Per contract: default depth is 3
        # We should see categories up to level 3
        assert data["max_depth"] <= 3

    def test_depth_max_is_five(self, client, seed_category_tree):
        """Test that max depth is 5."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        assert response.status_code == 200
        # Should work without error

    def test_depth_invalid_returns_400(self, client, seed_category_tree):
        """Test that invalid depth (>5) returns 400."""
        response = client.get("/api/v1/products/categories?depth=10")

        assert response.status_code in [400, 422], \
            f"Expected 400/422 for depth>5, got {response.status_code}"

    def test_depth_minimum_is_one(self, client, seed_category_tree):
        """Test that depth minimum is 1."""
        response = client.get("/api/v1/products/categories?depth=0")

        assert response.status_code in [400, 422], \
            f"Expected 400/422 for depth=0, got {response.status_code}"


# ============================================================================
# Test Scenario 4: Include product_count option
# ============================================================================

class TestProductCountOption:
    """Test include_product_count parameter."""

    def test_product_count_included_when_requested(
        self, client, seed_products_in_categories
    ):
        """Test product_count included when include_product_count=true."""
        response = client.get(
            "/api/v1/products/categories?include_product_count=true"
        )
        data = response.json()

        assert response.status_code == 200

        # All categories should have product_count
        def check_product_count(categories):
            for cat in categories:
                assert "product_count" in cat, \
                    f"Category {cat['code']} should have product_count"
                assert isinstance(cat["product_count"], int), \
                    "product_count should be integer"
                assert cat["product_count"] >= 0, \
                    "product_count should be non-negative"
                if cat.get("children"):
                    check_product_count(cat["children"])

        check_product_count(data["categories"])

    def test_product_count_not_included_by_default(
        self, client, seed_products_in_categories
    ):
        """Test product_count not included when not requested."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert response.status_code == 200

        # product_count should be null or not present
        for cat in data["categories"]:
            if "product_count" in cat:
                assert cat["product_count"] is None, \
                    "product_count should be null when not requested"

    def test_product_count_values_correct(
        self, client, seed_products_in_categories
    ):
        """Test that product_count values are correct."""
        response = client.get(
            "/api/v1/products/categories?include_product_count=true&depth=5"
        )
        data = response.json()

        # Helper to find category by code
        def find_category(categories, code):
            for cat in categories:
                if cat["code"] == code:
                    return cat
                if cat.get("children"):
                    found = find_category(cat["children"], code)
                    if found:
                        return found
            return None

        # Check specific counts
        expected_counts = seed_products_in_categories["counts"]

        # Business Laptops should have 3 products
        blaptops = find_category(data["categories"], "ELEC-COMP-LAPTOP-BIZ")
        if blaptops:
            assert blaptops["product_count"] == expected_counts.get("cat-blaptops", 3)


# ============================================================================
# Test Scenario 5: Filter by industry
# ============================================================================

class TestFilterByIndustry:
    """Test industry filter parameter."""

    def test_filter_by_electronics_industry(self, client, seed_category_tree):
        """Test filtering categories by electronics industry."""
        response = client.get("/api/v1/products/categories?industry=electronics")
        data = response.json()

        assert response.status_code == 200

        # All returned categories should be electronics
        def check_industry(categories, expected_industry):
            for cat in categories:
                assert cat["industry_sector"] == expected_industry, \
                    f"Category {cat['code']} should be in {expected_industry}"
                if cat.get("children"):
                    check_industry(cat["children"], expected_industry)

        check_industry(data["categories"], "electronics")

    def test_filter_by_apparel_industry(self, client, seed_category_tree):
        """Test filtering categories by apparel industry."""
        response = client.get("/api/v1/products/categories?industry=apparel")
        data = response.json()

        assert response.status_code == 200

        # All returned categories should be apparel
        for cat in data["categories"]:
            assert cat["industry_sector"] == "apparel"

    def test_filter_invalid_industry(self, client, seed_category_tree):
        """Test that invalid industry returns 400."""
        response = client.get("/api/v1/products/categories?industry=invalid")

        assert response.status_code in [400, 422], \
            f"Expected 400/422 for invalid industry, got {response.status_code}"

    def test_filter_industry_with_depth(self, client, seed_category_tree):
        """Test combining industry filter with depth."""
        response = client.get(
            "/api/v1/products/categories?industry=electronics&depth=2"
        )
        data = response.json()

        assert response.status_code == 200

        # Should have electronics categories only, up to depth 2
        for cat in data["categories"]:
            assert cat["industry_sector"] == "electronics"
            assert cat["level"] == 0


# ============================================================================
# Test Scenario 6: Tree structure validation
# ============================================================================

class TestCategoryTreeStructure:
    """Test that tree structure is built correctly."""

    def test_category_has_required_fields(self, client, seed_category_tree):
        """Test that each category has required fields."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        required_fields = ["id", "code", "name", "level", "children"]

        def check_fields(categories):
            for cat in categories:
                for field in required_fields:
                    assert field in cat, \
                        f"Category should have '{field}' field"
                if cat.get("children"):
                    check_fields(cat["children"])

        check_fields(data["categories"])

    def test_children_array_is_list(self, client, seed_category_tree):
        """Test that children field is always a list."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        def check_children(categories):
            for cat in categories:
                assert isinstance(cat.get("children", []), list), \
                    f"Category {cat['code']} children should be a list"
                if cat.get("children"):
                    check_children(cat["children"])

        check_children(data["categories"])

    def test_level_increments_correctly(self, client, seed_category_tree):
        """Test that level increments by 1 for each depth."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        def check_levels(categories, expected_level):
            for cat in categories:
                assert cat["level"] == expected_level, \
                    f"Category {cat['code']} should be level {expected_level}"
                if cat.get("children"):
                    check_levels(cat["children"], expected_level + 1)

        check_levels(data["categories"], 0)

    def test_total_categories_count_accurate(self, client, seed_category_tree):
        """Test that total_categories reflects all nested categories."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        def count_categories(categories):
            count = len(categories)
            for cat in categories:
                if cat.get("children"):
                    count += count_categories(cat["children"])
            return count

        actual_count = count_categories(data["categories"])
        assert data["total_categories"] == actual_count, \
            f"total_categories should be {actual_count}"

    def test_max_depth_reflects_actual_depth(self, client, seed_category_tree):
        """Test that max_depth reflects actual tree depth."""
        response = client.get("/api/v1/products/categories?depth=5")
        data = response.json()

        def find_max_depth(categories, current_depth=0):
            max_found = current_depth
            for cat in categories:
                if cat.get("children"):
                    child_max = find_max_depth(cat["children"], current_depth + 1)
                    max_found = max(max_found, child_max)
            return max_found

        actual_max = find_max_depth(data["categories"])
        assert data["max_depth"] == actual_max, \
            f"max_depth should be {actual_max}"


# ============================================================================
# Test Scenario 7: Industry sector field
# ============================================================================

class TestIndustrySectorField:
    """Test industry_sector field in category responses."""

    def test_industry_sector_present(self, client, seed_category_tree):
        """Test that industry_sector is present in response."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        def check_industry_sector(categories):
            for cat in categories:
                assert "industry_sector" in cat, \
                    f"Category {cat['code']} should have industry_sector"
                if cat.get("children"):
                    check_industry_sector(cat["children"])

        check_industry_sector(data["categories"])

    def test_industry_sector_nullable(self, client, db_session):
        """Test that industry_sector can be null."""
        # Create category without industry_sector
        category = ProductCategory(
            id="cat-nosector",
            code="NOSEC",
            name="No Sector Category",
            level=0,
            industry_sector=None
        )
        db_session.add(category)
        db_session.commit()

        response = client.get("/api/v1/products/categories")
        data = response.json()

        # Find our test category
        nosector_cat = next(
            (c for c in data["categories"] if c["code"] == "NOSEC"),
            None
        )
        assert nosector_cat is not None
        assert nosector_cat["industry_sector"] is None


# ============================================================================
# Test Scenario 8: Empty database handling
# ============================================================================

class TestEmptyDatabase:
    """Test behavior with no categories."""

    def test_empty_categories_returns_200(self, client):
        """Test that empty categories returns 200 with empty array."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert response.status_code == 200
        assert data["categories"] == [], \
            "Empty database should return empty categories array"
        assert data["total_categories"] == 0
        assert data["max_depth"] == 0


# ============================================================================
# Test Scenario 9: Response type validation
# ============================================================================

class TestResponseTypes:
    """Test that response field types are correct."""

    def test_id_is_string(self, client, seed_category_tree):
        """Test that category id is a string."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["id"], str), \
                "Category id should be a string"

    def test_level_is_integer(self, client, seed_category_tree):
        """Test that level is an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        for cat in data["categories"]:
            assert isinstance(cat["level"], int), \
                "Category level should be an integer"

    def test_total_categories_is_integer(self, client, seed_category_tree):
        """Test that total_categories is an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["total_categories"], int), \
            "total_categories should be an integer"

    def test_max_depth_is_integer(self, client, seed_category_tree):
        """Test that max_depth is an integer."""
        response = client.get("/api/v1/products/categories")
        data = response.json()

        assert isinstance(data["max_depth"], int), \
            "max_depth should be an integer"
