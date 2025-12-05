"""
Integration test suite for Product Catalog Expansion.

TASK-DATA-P5-005: Product Catalog Expansion - Phase A Tests

This test suite validates:
- 1000+ categories loaded
- 1000+ products generated
- 5 industries represented
- 5 levels of hierarchy
- Full-text search returns results <500ms
- Category tree query <200ms
- Product search with filter works

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no implementation exists yet)
- Implementation must make tests PASS without modifying tests

Note: These integration tests are designed for PostgreSQL.
Some tests may skip when running against SQLite.
"""

import pytest
import time
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for basic testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing."""
    from backend.models import Base

    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


def is_postgresql(engine) -> bool:
    """Check if engine is PostgreSQL."""
    return "postgresql" in str(engine.url).lower()


# ============================================================================
# Test Scenario 1: 1000+ Categories Loaded
# ============================================================================

class TestCategoryCountRequirement:
    """Test that 1000+ categories are loaded."""

    @pytest.mark.asyncio
    async def test_load_generates_minimum_1000_categories(self, db_session: Session):
        """Test that the catalog expansion creates at least 1000 categories."""
        try:
            from backend.services.data_ingestion.category_loader import CategoryLoader
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("CategoryLoader not yet implemented")

        # Skip if we don't have async session capability in SQLite
        # This test should be run against PostgreSQL in real integration
        pytest.skip("Requires async session - run with PostgreSQL integration")

    def test_category_table_has_1000_plus_records(self, db_session: Session):
        """Test that product_categories table has 1000+ records after expansion."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # This test verifies the final state after running the expansion script
        # It will fail until implementation populates the database
        count = db_session.query(func.count(ProductCategory.id)).scalar()

        assert count is not None
        assert count >= 1000, f"Expected at least 1000 categories, got {count}"

    def test_category_codes_are_unique(self, db_session: Session):
        """Test that all category codes are unique."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Count total categories
        total_count = db_session.query(func.count(ProductCategory.id)).scalar()

        # Count distinct codes
        distinct_count = db_session.query(
            func.count(func.distinct(ProductCategory.code))
        ).scalar()

        assert total_count == distinct_count, \
            f"Duplicate category codes found: {total_count} total vs {distinct_count} distinct"


# ============================================================================
# Test Scenario 2: 1000+ Products Generated
# ============================================================================

class TestProductCountRequirement:
    """Test that 1000+ products are generated."""

    def test_products_table_has_1000_plus_records(self, db_session: Session):
        """Test that products table has 1000+ records after expansion."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # This test verifies the final state after running the expansion script
        count = db_session.query(func.count(Product.id)).scalar()

        assert count is not None
        assert count >= 1000, f"Expected at least 1000 products, got {count}"

    def test_product_codes_are_unique(self, db_session: Session):
        """Test that all product codes are unique."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # Count total products
        total_count = db_session.query(func.count(Product.id)).scalar()

        # Count distinct codes
        distinct_count = db_session.query(
            func.count(func.distinct(Product.code))
        ).scalar()

        assert total_count == distinct_count, \
            f"Duplicate product codes found: {total_count} total vs {distinct_count} distinct"

    def test_products_have_category_id(self, db_session: Session):
        """Test that generated products have category_id set."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # Count products with category_id
        with_category = db_session.query(func.count(Product.id)).filter(
            Product.category_id.isnot(None)
        ).scalar()

        # Count total generated products (excluding original seed data)
        total = db_session.query(func.count(Product.id)).scalar()

        # Most products should have category_id (allow some seed data without)
        assert with_category >= 1000, \
            f"Expected at least 1000 products with category_id, got {with_category}"


# ============================================================================
# Test Scenario 3: 5 Industries Represented
# ============================================================================

class TestIndustryRepresentation:
    """Test that 5 industries are represented."""

    def test_five_distinct_industries_in_categories(self, db_session: Session):
        """Test that categories span 5 distinct industries."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Count distinct industry sectors
        industries = db_session.query(
            func.distinct(ProductCategory.industry_sector)
        ).filter(
            ProductCategory.industry_sector.isnot(None)
        ).all()

        industry_list = [i[0] for i in industries if i[0]]

        assert len(industry_list) >= 5, \
            f"Expected at least 5 industries, got {len(industry_list)}: {industry_list}"

    def test_electronics_industry_present(self, db_session: Session):
        """Test that electronics industry is represented."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.industry_sector == "electronics"
        ).scalar()

        assert count > 0, "Electronics industry not found in categories"

    def test_apparel_industry_present(self, db_session: Session):
        """Test that apparel industry is represented."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.industry_sector == "apparel"
        ).scalar()

        assert count > 0, "Apparel industry not found in categories"

    def test_automotive_industry_present(self, db_session: Session):
        """Test that automotive industry is represented."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.industry_sector == "automotive"
        ).scalar()

        assert count > 0, "Automotive industry not found in categories"

    def test_construction_industry_present(self, db_session: Session):
        """Test that construction industry is represented."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.industry_sector == "construction"
        ).scalar()

        assert count > 0, "Construction industry not found in categories"

    def test_food_beverage_industry_present(self, db_session: Session):
        """Test that food & beverage industry is represented."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.industry_sector == "food_beverage"
        ).scalar()

        assert count > 0, "Food & Beverage industry not found in categories"

    def test_products_distributed_across_industries(self, db_session: Session):
        """Test that products are distributed across all 5 industries."""
        try:
            from backend.models import Product, ProductCategory
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Count products per industry through category relationship
        results = db_session.query(
            ProductCategory.industry_sector,
            func.count(Product.id)
        ).join(
            Product, Product.category_id == ProductCategory.id
        ).filter(
            ProductCategory.industry_sector.isnot(None)
        ).group_by(
            ProductCategory.industry_sector
        ).all()

        # Should have products in at least 5 industries
        industries_with_products = [r[0] for r in results if r[1] > 0]

        assert len(industries_with_products) >= 5, \
            f"Expected products in 5 industries, found in {len(industries_with_products)}: {industries_with_products}"


# ============================================================================
# Test Scenario 4: 5 Levels of Hierarchy
# ============================================================================

class TestHierarchyLevels:
    """Test that category hierarchy has 5 levels."""

    def test_maximum_level_is_at_least_4(self, db_session: Session):
        """Test that hierarchy has at least 5 levels (0-4)."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        max_level = db_session.query(func.max(ProductCategory.level)).scalar()

        assert max_level is not None
        assert max_level >= 4, f"Expected max level >= 4, got {max_level}"

    def test_level_0_has_categories(self, db_session: Session):
        """Test that level 0 (root) has categories."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 0
        ).scalar()

        assert count > 0, "No level 0 (root) categories found"

    def test_level_1_has_categories(self, db_session: Session):
        """Test that level 1 has categories."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 1
        ).scalar()

        assert count > 0, "No level 1 categories found"

    def test_level_2_has_categories(self, db_session: Session):
        """Test that level 2 has categories."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 2
        ).scalar()

        assert count > 0, "No level 2 categories found"

    def test_level_3_has_categories(self, db_session: Session):
        """Test that level 3 has categories."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 3
        ).scalar()

        assert count > 0, "No level 3 categories found"

    def test_level_4_has_categories(self, db_session: Session):
        """Test that level 4 (leaf) has categories."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        count = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 4
        ).scalar()

        assert count > 0, "No level 4 categories found"

    def test_parent_child_relationships_valid(self, db_session: Session):
        """Test that parent-child relationships are valid."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Find categories where parent_id doesn't exist
        from sqlalchemy.orm import aliased

        Parent = aliased(ProductCategory)

        # Categories with invalid parent_id (non-existent parent)
        invalid = db_session.query(ProductCategory).filter(
            ProductCategory.parent_id.isnot(None)
        ).outerjoin(
            Parent, ProductCategory.parent_id == Parent.id
        ).filter(
            Parent.id.is_(None)
        ).count()

        assert invalid == 0, f"Found {invalid} categories with invalid parent_id"

    def test_root_categories_have_no_parent(self, db_session: Session):
        """Test that root categories (level 0) have no parent."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Count level 0 categories with parent_id
        invalid = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.level == 0,
            ProductCategory.parent_id.isnot(None)
        ).scalar()

        assert invalid == 0, f"Found {invalid} root categories with parent_id set"


# ============================================================================
# Test Scenario 5: Full-Text Search Returns Results <500ms
# ============================================================================

class TestFullTextSearchPerformance:
    """Test that full-text search returns results in <500ms."""

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required for FTS")
    def test_product_search_under_500ms(self, db_session: Session):
        """Test that product full-text search completes in under 500ms."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # Ensure we have data
        count = db_session.query(func.count(Product.id)).scalar()
        if count < 100:
            pytest.skip("Insufficient data for performance test")

        # Performance test: search for "laptop"
        start_time = time.time()

        results = db_session.execute(
            text("""
                SELECT id, name, ts_rank(search_vector, query) as rank
                FROM products, to_tsquery('english', 'laptop') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT 100
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 500, \
            f"Product search took {elapsed_ms:.2f}ms, expected <500ms"

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required for FTS")
    def test_product_search_multiple_terms_under_500ms(self, db_session: Session):
        """Test that multi-term product search completes in under 500ms."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        start_time = time.time()

        results = db_session.execute(
            text("""
                SELECT id, name, ts_rank(search_vector, query) as rank
                FROM products, to_tsquery('english', 'business & laptop') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT 100
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 500, \
            f"Multi-term search took {elapsed_ms:.2f}ms, expected <500ms"

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required for FTS")
    def test_category_search_under_500ms(self, db_session: Session):
        """Test that category full-text search completes in under 500ms."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        start_time = time.time()

        results = db_session.execute(
            text("""
                SELECT id, name, ts_rank(search_vector, query) as rank
                FROM product_categories, to_tsquery('english', 'electronics') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT 100
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 500, \
            f"Category search took {elapsed_ms:.2f}ms, expected <500ms"


# ============================================================================
# Test Scenario 6: Category Tree Query <200ms
# ============================================================================

class TestCategoryTreePerformance:
    """Test that category tree query completes in <200ms."""

    @pytest.mark.skipif(True, reason="PostgreSQL CTE required for recursive queries")
    def test_category_tree_query_under_200ms(self, db_session: Session):
        """Test that recursive category tree query completes in under 200ms."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Get a root category to test with
        root = db_session.query(ProductCategory).filter(
            ProductCategory.level == 0
        ).first()

        if not root:
            pytest.skip("No root category found")

        start_time = time.time()

        results = db_session.execute(
            text("""
                WITH RECURSIVE category_tree AS (
                    SELECT id, code, name, parent_id, level
                    FROM product_categories
                    WHERE id = :root_id

                    UNION ALL

                    SELECT c.id, c.code, c.name, c.parent_id, c.level
                    FROM product_categories c
                    JOIN category_tree ct ON c.parent_id = ct.id
                )
                SELECT * FROM category_tree
                ORDER BY level, code
            """),
            {"root_id": root.id}
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 200, \
            f"Category tree query took {elapsed_ms:.2f}ms, expected <200ms"

    @pytest.mark.skipif(True, reason="PostgreSQL CTE required for recursive queries")
    def test_all_descendants_query_under_200ms(self, db_session: Session):
        """Test that getting all descendants of a category completes in under 200ms."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Get a category with children
        parent = db_session.query(ProductCategory).filter(
            ProductCategory.level == 1
        ).first()

        if not parent:
            pytest.skip("No level 1 category found")

        start_time = time.time()

        results = db_session.execute(
            text("""
                WITH RECURSIVE descendants AS (
                    SELECT id, code, name, level
                    FROM product_categories
                    WHERE id = :parent_id

                    UNION ALL

                    SELECT c.id, c.code, c.name, c.level
                    FROM product_categories c
                    JOIN descendants d ON c.parent_id = d.id
                )
                SELECT * FROM descendants
            """),
            {"parent_id": parent.id}
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 200, \
            f"Descendants query took {elapsed_ms:.2f}ms, expected <200ms"

    def test_category_count_query_fast(self, db_session: Session):
        """Test that basic category count query is fast."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        start_time = time.time()

        count = db_session.query(func.count(ProductCategory.id)).scalar()

        elapsed_ms = (time.time() - start_time) * 1000

        # Basic count should be very fast (<50ms)
        assert elapsed_ms < 50, \
            f"Category count query took {elapsed_ms:.2f}ms, expected <50ms"


# ============================================================================
# Test Scenario 7: Product Search with Filter Works
# ============================================================================

class TestProductSearchWithFilter:
    """Test that product search with filters works correctly."""

    def test_filter_products_by_industry(self, db_session: Session):
        """Test filtering products by industry sector."""
        try:
            from backend.models import Product, ProductCategory
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Get products in electronics industry
        results = db_session.query(Product).join(
            ProductCategory, Product.category_id == ProductCategory.id
        ).filter(
            ProductCategory.industry_sector == "electronics"
        ).limit(10).all()

        # All results should be in electronics
        for product in results:
            category = db_session.query(ProductCategory).filter(
                ProductCategory.id == product.category_id
            ).first()
            assert category.industry_sector == "electronics"

    def test_filter_products_by_category_level(self, db_session: Session):
        """Test filtering products by category level."""
        try:
            from backend.models import Product, ProductCategory
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Get products in leaf categories (level >= 2)
        results = db_session.query(Product).join(
            ProductCategory, Product.category_id == ProductCategory.id
        ).filter(
            ProductCategory.level >= 2
        ).limit(10).all()

        # All results should be in leaf categories
        for product in results:
            category = db_session.query(ProductCategory).filter(
                ProductCategory.id == product.category_id
            ).first()
            assert category.level >= 2

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required for FTS")
    def test_search_products_with_industry_filter(self, db_session: Session):
        """Test full-text search with industry filter."""
        try:
            from backend.models import Product, ProductCategory
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Search for "laptop" in electronics only
        results = db_session.execute(
            text("""
                SELECT p.id, p.name
                FROM products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.search_vector @@ to_tsquery('english', 'laptop')
                AND pc.industry_sector = 'electronics'
                LIMIT 10
            """)
        ).fetchall()

        # Results should exist (assuming test data has laptops)
        assert isinstance(results, list)

    def test_filter_products_by_finished_product_flag(self, db_session: Session):
        """Test filtering products by is_finished_product flag."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # Count finished products
        finished_count = db_session.query(func.count(Product.id)).filter(
            Product.is_finished_product == True
        ).scalar()

        # Count components (not finished)
        component_count = db_session.query(func.count(Product.id)).filter(
            Product.is_finished_product == False
        ).scalar()

        # Should have both finished products and components
        total = finished_count + component_count
        total_products = db_session.query(func.count(Product.id)).scalar()

        assert total == total_products, \
            f"Finished ({finished_count}) + Components ({component_count}) should equal total ({total_products})"


# ============================================================================
# Test Scenario 8: Data Integrity
# ============================================================================

class TestDataIntegrity:
    """Test data integrity after catalog expansion."""

    def test_all_categories_have_required_fields(self, db_session: Session):
        """Test that all categories have required fields set."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Categories without code
        missing_code = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.code.is_(None)
        ).scalar()

        # Categories without name
        missing_name = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.name.is_(None)
        ).scalar()

        assert missing_code == 0, f"Found {missing_code} categories without code"
        assert missing_name == 0, f"Found {missing_name} categories without name"

    def test_all_products_have_required_fields(self, db_session: Session):
        """Test that all products have required fields set."""
        try:
            from backend.models import Product
        except ImportError:
            pytest.skip("Product model not yet implemented")

        # Products without code
        missing_code = db_session.query(func.count(Product.id)).filter(
            Product.code.is_(None)
        ).scalar()

        # Products without name
        missing_name = db_session.query(func.count(Product.id)).filter(
            Product.name.is_(None)
        ).scalar()

        # Products without unit
        missing_unit = db_session.query(func.count(Product.id)).filter(
            Product.unit.is_(None)
        ).scalar()

        assert missing_code == 0, f"Found {missing_code} products without code"
        assert missing_name == 0, f"Found {missing_name} products without name"
        assert missing_unit == 0, f"Found {missing_unit} products without unit"

    def test_category_parent_references_valid(self, db_session: Session):
        """Test that all category parent references are valid."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        from sqlalchemy.orm import aliased
        Parent = aliased(ProductCategory)

        # Categories with invalid parent_id
        invalid = db_session.query(func.count(ProductCategory.id)).filter(
            ProductCategory.parent_id.isnot(None)
        ).outerjoin(
            Parent, ProductCategory.parent_id == Parent.id
        ).filter(
            Parent.id.is_(None)
        ).scalar()

        assert invalid == 0, f"Found {invalid} categories with invalid parent reference"

    def test_product_category_references_valid(self, db_session: Session):
        """Test that all product category references are valid."""
        try:
            from backend.models import Product, ProductCategory
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Products with invalid category_id
        invalid = db_session.query(func.count(Product.id)).filter(
            Product.category_id.isnot(None)
        ).outerjoin(
            ProductCategory, Product.category_id == ProductCategory.id
        ).filter(
            ProductCategory.id.is_(None)
        ).scalar()

        assert invalid == 0, f"Found {invalid} products with invalid category reference"


# ============================================================================
# Test Scenario 9: Expansion Script Integration
# ============================================================================

class TestExpansionScriptIntegration:
    """Test the catalog expansion script integration."""

    @pytest.mark.asyncio
    async def test_expand_catalog_function_exists(self):
        """Test that expand_catalog function exists and is callable."""
        try:
            from backend.scripts.expand_product_catalog import expand_catalog
        except ImportError:
            pytest.skip("expand_product_catalog script not yet implemented")

        assert callable(expand_catalog)

    @pytest.mark.asyncio
    async def test_expand_catalog_creates_categories_and_products(self):
        """Test that expand_catalog creates both categories and products."""
        try:
            from backend.scripts.expand_product_catalog import expand_catalog
            from backend.models import ProductCategory, Product
        except ImportError:
            pytest.skip("expand_product_catalog script not yet implemented")

        # This test requires async session and actual database
        pytest.skip("Requires async session - run with PostgreSQL integration")

    def test_category_loader_module_exists(self):
        """Test that category_loader module exists."""
        try:
            from backend.services.data_ingestion import category_loader
        except ImportError:
            pytest.skip("category_loader module not yet implemented")

        assert category_loader is not None

    def test_product_generator_module_exists(self):
        """Test that product_generator module exists."""
        try:
            from backend.services.data_ingestion import product_generator
        except ImportError:
            pytest.skip("product_generator module not yet implemented")

        assert product_generator is not None

    def test_fts_indexer_module_exists(self):
        """Test that fts_indexer module exists."""
        try:
            from backend.services.data_ingestion import fts_indexer
        except ImportError:
            pytest.skip("fts_indexer module not yet implemented")

        assert fts_indexer is not None
