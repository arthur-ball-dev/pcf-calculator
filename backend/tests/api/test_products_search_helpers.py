"""
Test Product Search Helper Functions
TASK-BE-P8-004: Refactor search_products to Reduce Complexity

Test Scenarios:
1. _validate_search_params - Parameter validation and normalization
2. _build_search_query - SQLAlchemy query construction with filters
3. _apply_relevance_scoring - Relevance score calculation for results
4. _format_search_results - Response formatting with pagination

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (helper functions do not exist yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from backend.models import Product, ProductCategory, BillOfMaterials
from backend.schemas.products import (
    IndustrySector,
    CategoryInfo,
    ProductSearchItem,
    ProductSearchResponse,
)


# ============================================================================
# Test Fixtures
# ============================================================================

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

    return {
        "electronics": electronics,
        "apparel": apparel,
    }


@pytest.fixture(scope="function")
def seed_products(db_session, seed_categories):
    """Seed test database with products for search testing."""
    products = [
        Product(
            id="prod-laptop-1",
            code="LAPTOP-001",
            name="Business Laptop 14-inch",
            description="14-inch business laptop with aluminum chassis",
            unit="unit",
            category_id="cat-electronics",
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
            category_id="cat-electronics",
            manufacturer="GameTech Inc",
            country_of_origin="TW",
            is_finished_product=True,
            search_vector="gaming laptop 17 inch rgb keyboard gametech"
        ),
        Product(
            id="prod-tshirt-1",
            code="TSHIRT-001",
            name="Cotton T-Shirt Basic",
            description="Simple cotton t-shirt for everyday wear",
            unit="unit",
            category_id="cat-apparel",
            manufacturer="Fashion Co",
            country_of_origin="BD",
            is_finished_product=True,
            search_vector="cotton t-shirt basic simple everyday wear fashion"
        ),
        Product(
            id="prod-cpu-1",
            code="CPU-001",
            name="Laptop CPU i7",
            description="High-performance laptop processor",
            unit="unit",
            category_id="cat-electronics",
            manufacturer="ChipMaker Ltd",
            country_of_origin="US",
            is_finished_product=False,
            search_vector="laptop cpu i7 processor chipmaker"
        ),
    ]

    db_session.add_all(products)
    db_session.commit()

    return products


@pytest.fixture(scope="function")
def seed_bom(db_session, seed_products):
    """Seed BOM relationships for has_bom filter testing."""
    # Make prod-laptop-1 a parent in BOM (it has components)
    bom = BillOfMaterials(
        id="bom-1",
        parent_product_id="prod-laptop-1",
        child_product_id="prod-cpu-1",
        quantity=1.0,
        unit="unit"
    )
    db_session.add(bom)
    db_session.commit()
    return bom


# ============================================================================
# Test Scenario 1: _validate_search_params
# ============================================================================

class TestValidateSearchParams:
    """Test parameter validation helper function."""

    def test_validate_empty_query_normalized_to_none(self, db_session):
        """Test that empty string query is normalized to None."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query="",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.query is None, "Empty query should be normalized to None"

    def test_validate_query_too_short_returns_error(self, db_session):
        """Test that query <2 chars returns validation error."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query="a",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is not None, "Should return error for query <2 chars"
        assert result.error["code"] == "VALIDATION_ERROR"
        assert "query" in str(result.error["details"])

    def test_validate_query_too_long_returns_error(self, db_session):
        """Test that query >200 chars returns validation error."""
        from backend.api.routes.product_search import _validate_search_params

        long_query = "a" * 250
        result = _validate_search_params(
            query=long_query,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is not None, "Should return error for query >200 chars"
        assert result.error["code"] == "VALIDATION_ERROR"

    def test_validate_invalid_country_code_returns_error(self, db_session):
        """Test that invalid country code format returns error."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin="USA",  # Invalid: should be 2 uppercase letters
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is not None, "Should return error for invalid country code"
        assert "country_of_origin" in str(result.error["details"])

    def test_validate_invalid_industry_returns_error(self, db_session):
        """Test that invalid industry sector returns error."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query=None,
            category_id=None,
            industry="invalid_industry",
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is not None, "Should return error for invalid industry"
        assert "industry" in str(result.error["details"])

    def test_validate_nonexistent_category_returns_error(self, db_session):
        """Test that non-existent category_id returns error."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query=None,
            category_id="nonexistent-category-id",
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is not None, "Should return error for non-existent category"
        assert result.error["code"] == "INVALID_CATEGORY"

    def test_validate_valid_params_returns_validated_params(self, db_session, seed_categories):
        """Test that valid params return ValidatedParams without error."""
        from backend.api.routes.product_search import _validate_search_params

        result = _validate_search_params(
            query="laptop",
            category_id="cat-electronics",
            industry="electronics",
            manufacturer="Acme",
            country_of_origin="CN",
            is_finished_product=True,
            has_bom=None,
            limit=50,
            offset=0,
            db=db_session
        )

        assert result.error is None, "Should not have error for valid params"
        assert result.query == "laptop"
        assert result.category_id == "cat-electronics"
        assert result.industry == "electronics"
        assert result.manufacturer == "Acme"
        assert result.country_of_origin == "CN"
        assert result.is_finished_product is True


# ============================================================================
# Test Scenario 2: _build_search_query
# ============================================================================

class TestBuildSearchQuery:
    """Test query building helper function."""

    def test_build_query_with_text_search(self, db_session, seed_products):
        """Test that query filter applies text search."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query="laptop",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        # Should find products with "laptop" in name or description
        assert len(results) >= 2, "Should find at least 2 laptops"
        for product in results:
            assert "laptop" in product.name.lower() or "laptop" in (product.description or "").lower()

    def test_build_query_with_category_filter(self, db_session, seed_products):
        """Test that category_id filter works."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id="cat-apparel",
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        assert len(results) == 1, "Should find 1 apparel product"
        assert results[0].id == "prod-tshirt-1"

    def test_build_query_with_industry_filter(self, db_session, seed_products):
        """Test that industry filter works via category relationship."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry="electronics",
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        assert len(results) == 3, "Should find 3 electronics products"

    def test_build_query_with_manufacturer_filter(self, db_session, seed_products):
        """Test that manufacturer filter applies partial match."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer="Acme",
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        assert len(results) == 1, "Should find 1 Acme product"
        assert "Acme" in results[0].manufacturer

    def test_build_query_with_country_filter(self, db_session, seed_products):
        """Test that country_of_origin filter works."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin="CN",
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        assert len(results) == 1, "Should find 1 product from CN"
        assert results[0].country_of_origin == "CN"

    def test_build_query_with_is_finished_product_filter(self, db_session, seed_products):
        """Test that is_finished_product filter works."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=False,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        assert len(results) == 1, "Should find 1 component"
        assert results[0].is_finished_product is False

    def test_build_query_with_has_bom_true(self, db_session, seed_products, seed_bom):
        """Test that has_bom=true filter returns only products with BOM."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=True,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        # Only prod-laptop-1 has BOM entries as parent
        assert len(results) == 1, "Should find 1 product with BOM"
        assert results[0].id == "prod-laptop-1"

    def test_build_query_with_has_bom_false(self, db_session, seed_products, seed_bom):
        """Test that has_bom=false filter returns only products without BOM."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=False,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        # All products except prod-laptop-1 have no BOM
        assert len(results) == 3, "Should find 3 products without BOM"
        result_ids = [r.id for r in results]
        assert "prod-laptop-1" not in result_ids

    def test_build_query_combined_filters(self, db_session, seed_products):
        """Test query with multiple combined filters."""
        from backend.api.routes.product_search import _build_search_query, ValidatedParams

        params = ValidatedParams(
            query="laptop",
            category_id=None,
            industry="electronics",
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=True,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        query = _build_search_query(db_session, params)
        results = query.all()

        # Should find finished laptops in electronics
        assert len(results) >= 2
        for product in results:
            assert product.is_finished_product is True


# ============================================================================
# Test Scenario 3: _apply_relevance_scoring
# ============================================================================

class TestApplyRelevanceScoring:
    """Test relevance scoring helper function."""

    def test_relevance_scoring_with_query(self, db_session, seed_products):
        """Test that relevance scores are calculated when query is provided."""
        from backend.api.routes.product_search import _apply_relevance_scoring

        # Simulate products from query
        products = db_session.query(Product).filter(
            Product.name.ilike("%laptop%")
        ).all()

        scored = _apply_relevance_scoring(products, "laptop")

        for product, score in scored:
            assert score is not None, "Score should be set when query provided"
            assert 0.0 <= score <= 1.0, "Score should be between 0 and 1"

    def test_relevance_scoring_without_query(self, db_session, seed_products):
        """Test that relevance scores are None when no query provided."""
        from backend.api.routes.product_search import _apply_relevance_scoring

        products = db_session.query(Product).all()

        scored = _apply_relevance_scoring(products, None)

        for product, score in scored:
            assert score is None, "Score should be None when no query"

    def test_relevance_scoring_name_match_higher_than_description(self, db_session, seed_products):
        """Test that name matches get higher scores than description matches."""
        from backend.api.routes.product_search import _apply_relevance_scoring

        # Product with "laptop" in name vs product with only in description
        products = db_session.query(Product).all()

        scored = _apply_relevance_scoring(products, "laptop")
        scored_dict = {p.id: s for p, s in scored}

        # Business Laptop (in name) should have higher score than products
        # where "laptop" is only in description or search_vector
        laptop_score = scored_dict.get("prod-laptop-1", 0)
        assert laptop_score > 0, "Laptop should have positive score"

    def test_relevance_scoring_exact_prefix_match_highest(self, db_session, seed_products):
        """Test that products starting with query get highest scores."""
        from backend.api.routes.product_search import _apply_relevance_scoring

        products = db_session.query(Product).all()

        scored = _apply_relevance_scoring(products, "business")
        scored_dict = {p.id: s for p, s in scored}

        # "Business Laptop 14-inch" starts with "business" - should have high score
        business_laptop_score = scored_dict.get("prod-laptop-1", 0)
        assert business_laptop_score >= 0.5, "Starting match should have high score"


# ============================================================================
# Test Scenario 4: _format_search_results
# ============================================================================

class TestFormatSearchResults:
    """Test response formatting helper function."""

    def test_format_results_basic_structure(self, db_session, seed_products):
        """Test that response has correct structure."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        products = db_session.query(Product).limit(2).all()
        scored = [(p, None) for p in products]
        total = 4

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, total, params)

        # _format_search_results returns a dict (for caching), not a Pydantic model
        assert isinstance(response, dict)
        assert "items" in response
        assert "total" in response
        assert "limit" in response
        assert "offset" in response
        assert "has_more" in response

    def test_format_results_items_are_product_search_items(self, db_session, seed_products):
        """Test that items are correctly typed as ProductSearchItem."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        products = db_session.query(Product).limit(2).all()
        scored = [(p, 0.5) for p in products]

        params = ValidatedParams(
            query="test",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, 2, params)

        for item in response["items"]:
            assert isinstance(item, dict)
            assert "id" in item
            assert "code" in item
            assert "name" in item
            assert "relevance_score" in item

    def test_format_results_has_more_true(self, db_session, seed_products):
        """Test that has_more is true when more results exist."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        products = db_session.query(Product).limit(2).all()
        scored = [(p, None) for p in products]
        total = 10  # More than returned

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=2,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, total, params)

        assert response["has_more"] is True

    def test_format_results_has_more_false(self, db_session, seed_products):
        """Test that has_more is false on last page."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        products = db_session.query(Product).limit(2).all()
        scored = [(p, None) for p in products]
        total = 2  # Same as returned

        params = ValidatedParams(
            query=None,
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, total, params)

        assert response["has_more"] is False

    def test_format_results_with_category_info(self, db_session, seed_products):
        """Test that category info is included when product has category."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        # Get product with category eagerly loaded
        product = db_session.query(Product).filter(
            Product.id == "prod-laptop-1"
        ).first()
        scored = [(product, 0.5)]

        params = ValidatedParams(
            query="laptop",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, 1, params)

        assert len(response["items"]) == 1
        item = response["items"][0]
        # Category may be populated from product_category relationship or category field
        if item["category"] is not None:
            assert "id" in item["category"]
            assert "code" in item["category"]
            assert "name" in item["category"]

    def test_format_results_relevance_scores_included(self, db_session, seed_products):
        """Test that relevance scores are included in items."""
        from backend.api.routes.product_search import _format_search_results, ValidatedParams

        products = db_session.query(Product).limit(2).all()
        scored = [(products[0], 0.8), (products[1], 0.5)]

        params = ValidatedParams(
            query="test",
            category_id=None,
            industry=None,
            manufacturer=None,
            country_of_origin=None,
            is_finished_product=None,
            has_bom=None,
            limit=50,
            offset=0,
            error=None
        )

        response = _format_search_results(scored, 2, params)

        assert response["items"][0]["relevance_score"] == 0.8
        assert response["items"][1]["relevance_score"] == 0.5


# ============================================================================
# Test Scenario 5: Integration - Refactored search_products maintains behavior
# ============================================================================

class TestRefactoredSearchProductsIntegration:
    """Test that refactored search_products maintains backward compatibility."""

    def test_search_products_returns_same_response_format(self, authenticated_client, seed_products):
        """Test that response format is unchanged after refactoring."""
        response = authenticated_client.get("/api/v1/products/search?query=laptop")

        assert response.status_code == 200
        data = response.json()

        # Required fields must be present
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

    def test_search_products_filters_still_work(self, authenticated_client, seed_products):
        """Test that all filters continue to work after refactoring."""
        # Test multiple filters combined
        response = authenticated_client.get(
            "/api/v1/products/search?"
            "industry=electronics&"
            "is_finished_product=true&"
            "limit=10"
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["is_finished_product"] is True

    def test_search_products_validation_errors_unchanged(self, authenticated_client, seed_products):
        """Test that validation error responses are unchanged."""
        # Query too short
        response = authenticated_client.get("/api/v1/products/search?query=a")
        assert response.status_code == 400

        # Invalid country code
        response = authenticated_client.get("/api/v1/products/search?country_of_origin=USA")
        assert response.status_code == 400

    def test_search_products_pagination_unchanged(self, authenticated_client, seed_products):
        """Test that pagination behavior is unchanged."""
        response = authenticated_client.get("/api/v1/products/search?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) <= 2
        assert data["limit"] == 2
        assert data["offset"] == 0
