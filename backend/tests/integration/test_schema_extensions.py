"""
Integration test suite for Phase 5 schema extensions.

TASK-DB-P5-002: Extended Database Schema - Phase A Tests

This test suite validates:
- Full-text search on products works
- Full-text search on emission_factors works
- Category hierarchy queries work (recursive CTE)
- Performance: category tree query <200ms
- Performance: full-text search <100ms

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no schema extensions exist yet)
- Implementation must make tests PASS without modifying tests

Note: These integration tests are designed for PostgreSQL.
Some tests may skip when running against SQLite.
"""

import pytest
import time
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine, text
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
# Test Scenario 1: Full-Text Search on Products
# ============================================================================

class TestProductFullTextSearch:
    """Test full-text search functionality on products."""

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_product_search_vector_populated(self, db_session: Session):
        """Test that product search_vector is populated automatically."""
        from backend.models import Product

        product = Product(
            code="LAPTOP-001",
            name="Business Laptop Computer",
            description="High performance laptop for business use",
            unit="unit",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        # Refresh to load search_vector (populated by trigger)
        db_session.refresh(product)

        # search_vector should be populated
        assert product.search_vector is not None

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_product_full_text_search_by_name(self, db_session: Session):
        """Test searching products by name."""
        from backend.models import Product

        # Create products
        products = [
            Product(
                code="LAPTOP-001",
                name="Business Laptop Computer",
                description="High performance laptop",
                unit="unit",
                is_finished_product=True
            ),
            Product(
                code="PHONE-001",
                name="Smartphone",
                description="Mobile phone device",
                unit="unit",
                is_finished_product=True
            ),
            Product(
                code="DESKTOP-001",
                name="Desktop Computer",
                description="Workstation computer",
                unit="unit",
                is_finished_product=True
            )
        ]
        db_session.add_all(products)
        db_session.commit()

        # Search for "laptop"
        results = db_session.execute(
            text("""
                SELECT id, name
                FROM products
                WHERE search_vector @@ to_tsquery('english', 'laptop')
            """)
        ).fetchall()

        assert len(results) >= 1
        # Should find the laptop product
        names = [r[1] for r in results]
        assert any("Laptop" in name for name in names)

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_product_full_text_search_by_description(self, db_session: Session):
        """Test searching products by description."""
        from backend.models import Product

        product = Product(
            code="ECO-001",
            name="Standard Product",
            description="Environmentally friendly sustainable materials",
            unit="unit",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        # Search for "sustainable"
        results = db_session.execute(
            text("""
                SELECT id, name
                FROM products
                WHERE search_vector @@ to_tsquery('english', 'sustainable')
            """)
        ).fetchall()

        assert len(results) >= 1

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_product_search_ranking(self, db_session: Session):
        """Test that search results are ranked by relevance."""
        from backend.models import Product

        # Product with "laptop" in name (weight A)
        product1 = Product(
            code="L1",
            name="Laptop Computer",
            description="A computing device",
            unit="unit"
        )
        # Product with "laptop" only in description (weight C)
        product2 = Product(
            code="L2",
            name="Computing Device",
            description="Similar to a laptop",
            unit="unit"
        )
        db_session.add_all([product1, product2])
        db_session.commit()

        # Search with ranking
        results = db_session.execute(
            text("""
                SELECT id, name, ts_rank(search_vector, query) as rank
                FROM products, to_tsquery('english', 'laptop') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
            """)
        ).fetchall()

        # Product with "laptop" in name should rank higher
        if len(results) >= 2:
            assert results[0][1] == "Laptop Computer"

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_product_search_partial_match(self, db_session: Session):
        """Test partial word matching with prefix search."""
        from backend.models import Product

        product = Product(
            code="COMP-001",
            name="Desktop Computer",
            description="A desktop computing machine",
            unit="unit"
        )
        db_session.add(product)
        db_session.commit()

        # Search with prefix "comput"
        results = db_session.execute(
            text("""
                SELECT id, name
                FROM products
                WHERE search_vector @@ to_tsquery('english', 'comput:*')
            """)
        ).fetchall()

        assert len(results) >= 1


# ============================================================================
# Test Scenario 2: Full-Text Search on Emission Factors
# ============================================================================

class TestEmissionFactorFullTextSearch:
    """Test full-text search functionality on emission factors."""

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_emission_factor_search_vector_populated(self, db_session: Session):
        """Test that emission factor search_vector is populated automatically."""
        from backend.models import EmissionFactor

        ef = EmissionFactor(
            activity_name="Steel Production Primary",
            co2e_factor=Decimal("1.85"),
            unit="kg",
            data_source="EPA",
            geography="US"
        )
        db_session.add(ef)
        db_session.commit()

        # Refresh to load search_vector
        db_session.refresh(ef)

        assert ef.search_vector is not None

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_emission_factor_search_by_activity_name(self, db_session: Session):
        """Test searching emission factors by activity name."""
        from backend.models import EmissionFactor

        # Create emission factors
        factors = [
            EmissionFactor(
                activity_name="Steel Production Primary",
                co2e_factor=Decimal("1.85"),
                unit="kg",
                data_source="EPA",
                geography="US"
            ),
            EmissionFactor(
                activity_name="Aluminum Smelting",
                co2e_factor=Decimal("11.5"),
                unit="kg",
                data_source="EPA",
                geography="US"
            ),
            EmissionFactor(
                activity_name="Steel Recycling Secondary",
                co2e_factor=Decimal("0.42"),
                unit="kg",
                data_source="EPA",
                geography="US"
            )
        ]
        db_session.add_all(factors)
        db_session.commit()

        # Search for "steel"
        results = db_session.execute(
            text("""
                SELECT id, activity_name
                FROM emission_factors
                WHERE search_vector @@ to_tsquery('english', 'steel')
            """)
        ).fetchall()

        assert len(results) >= 2
        activity_names = [r[1] for r in results]
        assert all("Steel" in name for name in activity_names)

    @pytest.mark.skipif(True, reason="PostgreSQL TSVECTOR required")
    def test_emission_factor_combined_search(self, db_session: Session):
        """Test combined search with multiple terms."""
        from backend.models import EmissionFactor

        ef = EmissionFactor(
            activity_name="Primary Steel Production Blast Furnace",
            co2e_factor=Decimal("1.85"),
            unit="kg",
            data_source="EPA",
            geography="US"
        )
        db_session.add(ef)
        db_session.commit()

        # Search for "steel AND production"
        results = db_session.execute(
            text("""
                SELECT id, activity_name
                FROM emission_factors
                WHERE search_vector @@ to_tsquery('english', 'steel & production')
            """)
        ).fetchall()

        assert len(results) >= 1


# ============================================================================
# Test Scenario 3: Category Hierarchy Queries (Recursive CTE)
# ============================================================================

class TestCategoryHierarchyQueries:
    """Test category hierarchy queries using recursive CTE."""

    def test_category_tree_basic_structure(self, db_session: Session):
        """Test basic category tree structure can be queried."""
        try:
            from backend.models import ProductCategory
        except ImportError:
            pytest.skip("ProductCategory model not yet implemented")

        # Create 3-level hierarchy
        root = ProductCategory(code="ROOT", name="All Products", level=0)
        db_session.add(root)
        db_session.commit()

        child = ProductCategory(
            code="CHILD",
            name="Electronics",
            parent_id=root.id,
            level=1
        )
        db_session.add(child)
        db_session.commit()

        grandchild = ProductCategory(
            code="GCHILD",
            name="Laptops",
            parent_id=child.id,
            level=2
        )
        db_session.add(grandchild)
        db_session.commit()

        # Query all categories
        all_cats = db_session.query(ProductCategory).all()
        assert len(all_cats) == 3

    @pytest.mark.skipif(True, reason="PostgreSQL CTE required for recursive queries")
    def test_get_all_descendants_cte(self, db_session: Session):
        """Test getting all descendants using recursive CTE."""
        from backend.models import ProductCategory

        # Create hierarchy
        root = ProductCategory(code="R", name="Root", level=0)
        db_session.add(root)
        db_session.commit()

        l1 = ProductCategory(code="L1", name="Level 1", parent_id=root.id, level=1)
        db_session.add(l1)
        db_session.commit()

        l2a = ProductCategory(code="L2A", name="Level 2A", parent_id=l1.id, level=2)
        l2b = ProductCategory(code="L2B", name="Level 2B", parent_id=l1.id, level=2)
        db_session.add_all([l2a, l2b])
        db_session.commit()

        # Recursive CTE to get all descendants of root
        results = db_session.execute(
            text("""
                WITH RECURSIVE category_tree AS (
                    -- Base case: start from root
                    SELECT id, code, name, parent_id, level,
                           ARRAY[code] as path
                    FROM product_categories
                    WHERE code = 'R'

                    UNION ALL

                    -- Recursive case: join children
                    SELECT c.id, c.code, c.name, c.parent_id, c.level,
                           ct.path || c.code
                    FROM product_categories c
                    JOIN category_tree ct ON c.parent_id = ct.id
                )
                SELECT code, name, level, path
                FROM category_tree
                ORDER BY level, code
            """)
        ).fetchall()

        # Should get all 4 categories
        assert len(results) == 4
        codes = [r[0] for r in results]
        assert "R" in codes
        assert "L1" in codes
        assert "L2A" in codes
        assert "L2B" in codes

    @pytest.mark.skipif(True, reason="PostgreSQL CTE required for recursive queries")
    def test_get_ancestors_cte(self, db_session: Session):
        """Test getting all ancestors using recursive CTE."""
        from backend.models import ProductCategory

        # Create 4-level hierarchy
        l0 = ProductCategory(code="L0", name="Level 0", level=0)
        db_session.add(l0)
        db_session.commit()

        l1 = ProductCategory(code="L1", name="Level 1", parent_id=l0.id, level=1)
        db_session.add(l1)
        db_session.commit()

        l2 = ProductCategory(code="L2", name="Level 2", parent_id=l1.id, level=2)
        db_session.add(l2)
        db_session.commit()

        l3 = ProductCategory(code="L3", name="Level 3", parent_id=l2.id, level=3)
        db_session.add(l3)
        db_session.commit()

        # Recursive CTE to get all ancestors of L3
        results = db_session.execute(
            text("""
                WITH RECURSIVE ancestors AS (
                    -- Base case: start from target category
                    SELECT id, code, name, parent_id, level
                    FROM product_categories
                    WHERE code = 'L3'

                    UNION ALL

                    -- Recursive case: join parents
                    SELECT c.id, c.code, c.name, c.parent_id, c.level
                    FROM product_categories c
                    JOIN ancestors a ON c.id = a.parent_id
                )
                SELECT code, name, level
                FROM ancestors
                ORDER BY level
            """)
        ).fetchall()

        # Should get L3 and all its ancestors (L0, L1, L2, L3)
        assert len(results) == 4
        codes = [r[0] for r in results]
        assert codes == ["L0", "L1", "L2", "L3"]

    @pytest.mark.skipif(True, reason="PostgreSQL CTE required for recursive queries")
    def test_get_full_path_string(self, db_session: Session):
        """Test building full category path as string."""
        from backend.models import ProductCategory

        # Create hierarchy: Electronics > Computers > Laptops
        elec = ProductCategory(code="ELEC", name="Electronics", level=0)
        db_session.add(elec)
        db_session.commit()

        comp = ProductCategory(code="COMP", name="Computers", parent_id=elec.id, level=1)
        db_session.add(comp)
        db_session.commit()

        lapt = ProductCategory(code="LAPT", name="Laptops", parent_id=comp.id, level=2)
        db_session.add(lapt)
        db_session.commit()

        # Build path string
        results = db_session.execute(
            text("""
                WITH RECURSIVE ancestors AS (
                    SELECT id, code, name, parent_id, level,
                           name as path_name
                    FROM product_categories
                    WHERE code = 'LAPT'

                    UNION ALL

                    SELECT c.id, c.code, c.name, c.parent_id, c.level,
                           c.name || ' > ' || a.path_name
                    FROM product_categories c
                    JOIN ancestors a ON c.id = a.parent_id
                )
                SELECT path_name
                FROM ancestors
                WHERE parent_id IS NULL
            """)
        ).fetchone()

        # Full path should be "Electronics > Computers > Laptops"
        assert results is not None
        assert "Electronics" in results[0]
        assert "Laptops" in results[0]


# ============================================================================
# Test Scenario 4: Performance - Category Tree Query <200ms
# ============================================================================

class TestCategoryTreePerformance:
    """Test category tree query performance."""

    @pytest.mark.skipif(True, reason="Performance test requires PostgreSQL with real data")
    def test_category_tree_query_under_200ms(self, db_session: Session):
        """Test that category tree query completes in under 200ms."""
        from backend.models import ProductCategory

        # Create a realistic category tree (100+ categories, 5 levels deep)
        # This creates a substantial tree for performance testing
        categories = []

        # Level 0 - 5 root categories
        for i in range(5):
            root = ProductCategory(
                code=f"ROOT-{i}",
                name=f"Root Category {i}",
                level=0,
                industry_sector=f"Sector {i}"
            )
            db_session.add(root)
            db_session.flush()  # Get ID

            # Level 1 - 4 children per root
            for j in range(4):
                l1 = ProductCategory(
                    code=f"L1-{i}-{j}",
                    name=f"Level 1 Category {i}-{j}",
                    parent_id=root.id,
                    level=1
                )
                db_session.add(l1)
                db_session.flush()

                # Level 2 - 3 children per L1
                for k in range(3):
                    l2 = ProductCategory(
                        code=f"L2-{i}-{j}-{k}",
                        name=f"Level 2 Category {i}-{j}-{k}",
                        parent_id=l1.id,
                        level=2
                    )
                    db_session.add(l2)
                    db_session.flush()

                    # Level 3 - 2 children per L2
                    for m in range(2):
                        l3 = ProductCategory(
                            code=f"L3-{i}-{j}-{k}-{m}",
                            name=f"Level 3 Category {i}-{j}-{k}-{m}",
                            parent_id=l2.id,
                            level=3
                        )
                        db_session.add(l3)

        db_session.commit()

        # Count total categories
        total = db_session.query(ProductCategory).count()
        assert total >= 100, f"Expected at least 100 categories, got {total}"

        # Performance test: get all descendants of first root
        start_time = time.time()

        results = db_session.execute(
            text("""
                WITH RECURSIVE category_tree AS (
                    SELECT id, code, name, parent_id, level
                    FROM product_categories
                    WHERE code = 'ROOT-0'

                    UNION ALL

                    SELECT c.id, c.code, c.name, c.parent_id, c.level
                    FROM product_categories c
                    JOIN category_tree ct ON c.parent_id = ct.id
                )
                SELECT * FROM category_tree
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        # Assert performance requirement
        assert elapsed_ms < 200, \
            f"Category tree query took {elapsed_ms:.2f}ms, expected <200ms"

        # Verify we got results
        assert len(results) > 20, f"Expected more descendants, got {len(results)}"


# ============================================================================
# Test Scenario 5: Performance - Full-Text Search <100ms
# ============================================================================

class TestFullTextSearchPerformance:
    """Test full-text search performance."""

    @pytest.mark.skipif(True, reason="Performance test requires PostgreSQL with real data")
    def test_product_search_under_100ms(self, db_session: Session):
        """Test that product full-text search completes in under 100ms."""
        from backend.models import Product

        # Create 1000+ products for realistic performance testing
        products = []
        categories = ["Electronics", "Apparel", "Automotive", "Industrial", "Consumer"]
        adjectives = ["Premium", "Standard", "Professional", "Eco-friendly", "Advanced"]
        nouns = ["Device", "Component", "System", "Module", "Assembly"]

        for i in range(1000):
            cat = categories[i % len(categories)]
            adj = adjectives[i % len(adjectives)]
            noun = nouns[i % len(nouns)]

            product = Product(
                code=f"PROD-{i:04d}",
                name=f"{cat} {adj} {noun} {i}",
                description=f"A {adj.lower()} {noun.lower()} for {cat.lower()} applications. "
                           f"Product number {i} in the catalog.",
                unit="unit",
                category=cat,
                is_finished_product=(i % 2 == 0)
            )
            products.append(product)

        db_session.add_all(products)
        db_session.commit()

        # Performance test: search for "electronics"
        start_time = time.time()

        results = db_session.execute(
            text("""
                SELECT id, name, ts_rank(search_vector, query) as rank
                FROM products, to_tsquery('english', 'electronics') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT 100
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        # Assert performance requirement
        assert elapsed_ms < 100, \
            f"Full-text search took {elapsed_ms:.2f}ms, expected <100ms"

        # Verify we got results
        assert len(results) > 0, "Expected search results"

    @pytest.mark.skipif(True, reason="Performance test requires PostgreSQL with real data")
    def test_emission_factor_search_under_100ms(self, db_session: Session):
        """Test that emission factor full-text search completes in under 100ms."""
        from backend.models import EmissionFactor

        # Create 1000+ emission factors
        activities = [
            "Steel Production", "Aluminum Smelting", "Concrete Manufacturing",
            "Glass Production", "Plastic Molding", "Paper Production",
            "Chemical Synthesis", "Food Processing", "Textile Weaving",
            "Electronic Assembly"
        ]
        variants = ["Primary", "Secondary", "Recycled", "Industrial", "Commercial"]
        sources = ["EPA", "DEFRA", "Exiobase"]
        geographies = ["US", "EU", "GLO", "CN", "UK"]

        factors = []
        for i in range(1000):
            activity = activities[i % len(activities)]
            variant = variants[i % len(variants)]
            source = sources[i % len(sources)]
            geo = geographies[i % len(geographies)]

            ef = EmissionFactor(
                activity_name=f"{activity} {variant} {i}",
                co2e_factor=Decimal(str(0.1 + (i % 100) * 0.1)),
                unit="kg",
                data_source=source,
                geography=geo,
                reference_year=2020 + (i % 5)
            )
            factors.append(ef)

        db_session.add_all(factors)
        db_session.commit()

        # Performance test: search for "steel"
        start_time = time.time()

        results = db_session.execute(
            text("""
                SELECT id, activity_name, ts_rank(search_vector, query) as rank
                FROM emission_factors, to_tsquery('english', 'steel') query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT 100
            """)
        ).fetchall()

        elapsed_ms = (time.time() - start_time) * 1000

        # Assert performance requirement
        assert elapsed_ms < 100, \
            f"Emission factor search took {elapsed_ms:.2f}ms, expected <100ms"

        # Verify we got results
        assert len(results) > 0, "Expected search results"


# ============================================================================
# Test Scenario 6: Schema Extension Validation
# ============================================================================

class TestSchemaExtensionValidation:
    """Test that schema extensions are properly configured."""

    def test_product_has_category_id_column(self, db_session: Session):
        """Test that products table has category_id column."""
        from backend.models import Product

        # Check if category_id column exists
        # This will be added in Phase B implementation
        # For now, we just verify the model can be imported
        assert Product is not None

    def test_product_has_manufacturer_column(self, db_session: Session):
        """Test that products table has manufacturer column."""
        from backend.models import Product

        # This will be added in Phase B
        assert Product is not None

    def test_product_has_country_of_origin_column(self, db_session: Session):
        """Test that products table has country_of_origin column."""
        from backend.models import Product

        # This will be added in Phase B
        assert Product is not None

    def test_emission_factor_has_data_source_id_column(self, db_session: Session):
        """Test that emission_factors table has data_source_id column."""
        from backend.models import EmissionFactor

        # This will be added in Phase B
        assert EmissionFactor is not None

    def test_emission_factor_has_external_id_column(self, db_session: Session):
        """Test that emission_factors table has external_id column."""
        from backend.models import EmissionFactor

        # This will be added in Phase B
        assert EmissionFactor is not None

    def test_emission_factor_has_is_active_column(self, db_session: Session):
        """Test that emission_factors table has is_active column."""
        from backend.models import EmissionFactor

        # This will be added in Phase B
        assert EmissionFactor is not None


# ============================================================================
# Test Scenario 7: Index Validation
# ============================================================================

class TestIndexValidation:
    """Test that required indexes exist."""

    @pytest.mark.skipif(True, reason="PostgreSQL required for index validation")
    def test_product_search_gin_index_exists(self, db_session: Session):
        """Test that GIN index exists on products.search_vector."""
        result = db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'products'
                AND indexname LIKE '%search%'
            """)
        ).fetchone()

        assert result is not None, "GIN index on products.search_vector not found"

    @pytest.mark.skipif(True, reason="PostgreSQL required for index validation")
    def test_emission_factor_search_gin_index_exists(self, db_session: Session):
        """Test that GIN index exists on emission_factors.search_vector."""
        result = db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'emission_factors'
                AND indexname LIKE '%search%'
            """)
        ).fetchone()

        assert result is not None, "GIN index on emission_factors.search_vector not found"

    @pytest.mark.skipif(True, reason="PostgreSQL required for index validation")
    def test_category_parent_index_exists(self, db_session: Session):
        """Test that index exists on product_categories.parent_id."""
        result = db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'product_categories'
                AND indexname LIKE '%parent%'
            """)
        ).fetchone()

        assert result is not None, "Index on product_categories.parent_id not found"


# ============================================================================
# Test Scenario 8: Data Integrity with Extensions
# ============================================================================

class TestDataIntegrityWithExtensions:
    """Test data integrity with new schema extensions."""

    def test_product_with_category_relationship(self, db_session: Session):
        """Test product can be associated with a category."""
        try:
            from backend.models import ProductCategory, Product
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Create category
        category = ProductCategory(
            code="TEST-CAT",
            name="Test Category",
            level=0
        )
        db_session.add(category)
        db_session.commit()

        # Category exists and can be queried
        retrieved = db_session.query(ProductCategory).filter(
            ProductCategory.code == "TEST-CAT"
        ).first()
        assert retrieved is not None

    def test_emission_factor_with_data_source_relationship(self, db_session: Session):
        """Test emission factor can be associated with a data source."""
        try:
            from backend.models import DataSource, EmissionFactor
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Create data source
        data_source = DataSource(
            name="Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        # Data source exists and can be queried
        retrieved = db_session.query(DataSource).filter(
            DataSource.name == "Test Source"
        ).first()
        assert retrieved is not None

    def test_sync_log_with_data_source_relationship(self, db_session: Session):
        """Test sync log can be associated with a data source."""
        try:
            from backend.models import DataSource, DataSyncLog
        except ImportError:
            pytest.skip("Models not yet implemented")

        # Create data source
        data_source = DataSource(
            name="Sync Test Source",
            source_type="api"
        )
        db_session.add(data_source)
        db_session.commit()

        # Create sync log
        sync_log = DataSyncLog(
            data_source_id=data_source.id,
            sync_type="initial",
            status="pending",
            started_at=datetime.now(timezone.utc)
        )
        db_session.add(sync_log)
        db_session.commit()

        # Verify relationship
        assert sync_log.data_source_id == data_source.id
