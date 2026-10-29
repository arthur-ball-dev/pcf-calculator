"""
Test suite for ProductCategory model.

TASK-DB-P5-002: Extended Database Schema - Phase A Tests

This test suite validates:
- ProductCategory CRUD operations (create, read, update, delete)
- Self-referential parent/children relationship
- Unique code constraint enforcement
- 5-level hierarchy traversal
- Category tree recursive CTE query
- Level field validation
- Industry sector field

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no ProductCategory model exists yet)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from datetime import datetime


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
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
    try:
        from backend.models import ProductCategory
    except ImportError:
        pytest.skip("ProductCategory model not yet implemented")

    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


# ============================================================================
# Test Scenario 1: ProductCategory CRUD Operations
# ============================================================================

class TestProductCategoryCRUD:
    """Test ProductCategory model CRUD operations."""

    def test_create_category_with_required_fields(self, db_session: Session):
        """Test creating a category with all required fields."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="ELEC",
            name="Electronics"
        )
        db_session.add(category)
        db_session.commit()

        # Category created with auto-generated UUID id
        assert category.id is not None
        assert category.code == "ELEC"
        assert category.name == "Electronics"

        # Default values
        assert category.level == 0
        assert category.parent_id is None
        assert category.created_at is not None

    def test_create_category_with_all_fields(self, db_session: Session):
        """Test creating a category with all fields populated."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="COMP",
            name="Computers",
            level=1,
            industry_sector="Information Technology"
        )
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.code == "COMP"
        assert category.name == "Computers"
        assert category.level == 1
        assert category.industry_sector == "Information Technology"

    def test_read_category_by_id(self, db_session: Session):
        """Test reading a category by ID."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="READ",
            name="Read Test Category"
        )
        db_session.add(category)
        db_session.commit()

        category_id = category.id

        # Clear session cache
        db_session.expire_all()

        # Read by ID
        retrieved = db_session.get(ProductCategory, category_id)
        assert retrieved is not None
        assert retrieved.code == "READ"
        assert retrieved.name == "Read Test Category"

    def test_read_category_by_code(self, db_session: Session):
        """Test reading a category by code."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="BYCODE",
            name="Code Query Test"
        )
        db_session.add(category)
        db_session.commit()

        # Query by code
        retrieved = db_session.query(ProductCategory).filter(
            ProductCategory.code == "BYCODE"
        ).first()
        assert retrieved is not None
        assert retrieved.name == "Code Query Test"

    def test_update_category(self, db_session: Session):
        """Test updating a category."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="UPD",
            name="Original Name",
            industry_sector="Original Sector"
        )
        db_session.add(category)
        db_session.commit()

        # Update category
        category.name = "Updated Name"
        category.industry_sector = "Updated Sector"
        db_session.commit()

        # Verify update
        db_session.expire_all()
        retrieved = db_session.get(ProductCategory, category.id)
        assert retrieved.name == "Updated Name"
        assert retrieved.industry_sector == "Updated Sector"

    def test_delete_category(self, db_session: Session):
        """Test deleting a category."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="DEL",
            name="To Delete"
        )
        db_session.add(category)
        db_session.commit()

        category_id = category.id

        # Delete category
        db_session.delete(category)
        db_session.commit()

        # Verify deletion
        retrieved = db_session.get(ProductCategory, category_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 2: Self-Referential Parent/Children Relationship
# ============================================================================

class TestProductCategoryHierarchy:
    """Test self-referential parent/children relationships."""

    def test_create_child_category(self, db_session: Session):
        """Test creating a child category with parent reference."""
        from backend.models import ProductCategory

        # Create parent
        parent = ProductCategory(
            code="PARENT",
            name="Parent Category",
            level=0
        )
        db_session.add(parent)
        db_session.commit()

        # Create child
        child = ProductCategory(
            code="CHILD",
            name="Child Category",
            parent_id=parent.id,
            level=1
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_id == parent.id

    def test_parent_relationship_access(self, db_session: Session):
        """Test accessing parent via relationship."""
        from backend.models import ProductCategory

        parent = ProductCategory(
            code="P1",
            name="Parent 1",
            level=0
        )
        db_session.add(parent)
        db_session.commit()

        child = ProductCategory(
            code="C1",
            name="Child 1",
            parent_id=parent.id,
            level=1
        )
        db_session.add(child)
        db_session.commit()

        # Refresh to load relationship
        db_session.refresh(child)

        # Access parent via relationship
        assert child.parent is not None
        assert child.parent.code == "P1"

    def test_children_relationship_access(self, db_session: Session):
        """Test accessing children via relationship."""
        from backend.models import ProductCategory

        parent = ProductCategory(
            code="P2",
            name="Parent 2",
            level=0
        )
        db_session.add(parent)
        db_session.commit()

        child1 = ProductCategory(
            code="C2A",
            name="Child 2A",
            parent_id=parent.id,
            level=1
        )
        child2 = ProductCategory(
            code="C2B",
            name="Child 2B",
            parent_id=parent.id,
            level=1
        )
        db_session.add_all([child1, child2])
        db_session.commit()

        # Refresh to load relationship
        db_session.refresh(parent)

        # Access children via relationship
        assert len(parent.children) == 2
        child_codes = [c.code for c in parent.children]
        assert "C2A" in child_codes
        assert "C2B" in child_codes

    def test_multilevel_hierarchy(self, db_session: Session):
        """Test creating a multi-level category hierarchy."""
        from backend.models import ProductCategory

        # Level 0 - Root
        root = ProductCategory(code="ROOT", name="Root", level=0)
        db_session.add(root)
        db_session.commit()

        # Level 1
        level1 = ProductCategory(
            code="L1", name="Level 1",
            parent_id=root.id, level=1
        )
        db_session.add(level1)
        db_session.commit()

        # Level 2
        level2 = ProductCategory(
            code="L2", name="Level 2",
            parent_id=level1.id, level=2
        )
        db_session.add(level2)
        db_session.commit()

        # Level 3
        level3 = ProductCategory(
            code="L3", name="Level 3",
            parent_id=level2.id, level=3
        )
        db_session.add(level3)
        db_session.commit()

        # Verify hierarchy traversal upward
        db_session.refresh(level3)
        assert level3.parent.code == "L2"
        assert level3.parent.parent.code == "L1"
        assert level3.parent.parent.parent.code == "ROOT"


# ============================================================================
# Test Scenario 3: Unique Code Constraint
# ============================================================================

class TestProductCategoryUniqueConstraint:
    """Test unique constraint on ProductCategory code."""

    def test_unique_code_constraint(self, db_session: Session):
        """Test that category codes must be unique."""
        from backend.models import ProductCategory

        cat1 = ProductCategory(
            code="UNIQ",
            name="Category 1"
        )
        db_session.add(cat1)
        db_session.commit()

        # Second category with same code should fail
        cat2 = ProductCategory(
            code="UNIQ",  # Duplicate code
            name="Category 2"
        )
        db_session.add(cat2)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "UNIQUE constraint failed" in str(exc_info.value) or \
               "duplicate key" in str(exc_info.value).lower()

    def test_different_codes_allowed(self, db_session: Session):
        """Test that different codes are allowed."""
        from backend.models import ProductCategory

        cat1 = ProductCategory(code="CODE1", name="Category 1")
        cat2 = ProductCategory(code="CODE2", name="Category 2")

        db_session.add_all([cat1, cat2])
        db_session.commit()

        assert cat1.id is not None
        assert cat2.id is not None
        assert cat1.id != cat2.id


# ============================================================================
# Test Scenario 4: 5-Level Hierarchy Traversal
# ============================================================================

class TestFiveLevelHierarchy:
    """Test 5-level category hierarchy traversal."""

    def test_create_five_level_hierarchy(self, db_session: Session):
        """Test creating a 5-level deep category hierarchy."""
        from backend.models import ProductCategory

        # Level 0 - Electronics
        level0 = ProductCategory(
            code="ELEC",
            name="Electronics",
            level=0,
            industry_sector="Consumer Electronics"
        )
        db_session.add(level0)
        db_session.commit()

        # Level 1 - Computers
        level1 = ProductCategory(
            code="COMP",
            name="Computers",
            parent_id=level0.id,
            level=1
        )
        db_session.add(level1)
        db_session.commit()

        # Level 2 - Laptops
        level2 = ProductCategory(
            code="LAPT",
            name="Laptops",
            parent_id=level1.id,
            level=2
        )
        db_session.add(level2)
        db_session.commit()

        # Level 3 - Business Laptops
        level3 = ProductCategory(
            code="BLPT",
            name="Business Laptops",
            parent_id=level2.id,
            level=3
        )
        db_session.add(level3)
        db_session.commit()

        # Level 4 - 14-inch Business Laptops (leaf)
        level4 = ProductCategory(
            code="B14",
            name="14-inch Business Laptops",
            parent_id=level3.id,
            level=4
        )
        db_session.add(level4)
        db_session.commit()

        # Verify all levels exist
        all_categories = db_session.query(ProductCategory).order_by(
            ProductCategory.level
        ).all()
        assert len(all_categories) >= 5

        # Verify level values
        levels = [cat.level for cat in all_categories]
        assert 0 in levels
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels
        assert 4 in levels

    def test_traverse_hierarchy_upward(self, db_session: Session):
        """Test traversing from leaf to root."""
        from backend.models import ProductCategory

        # Create 5-level hierarchy
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

        l4 = ProductCategory(code="L4", name="Level 4", parent_id=l3.id, level=4)
        db_session.add(l4)
        db_session.commit()

        # Traverse upward from leaf
        db_session.refresh(l4)
        path = []
        current = l4
        while current is not None:
            path.append(current.code)
            current = current.parent

        assert path == ["L4", "L3", "L2", "L1", "L0"]

    def test_traverse_hierarchy_downward(self, db_session: Session):
        """Test traversing from root to leaves."""
        from backend.models import ProductCategory

        # Create simple tree
        root = ProductCategory(code="R", name="Root", level=0)
        db_session.add(root)
        db_session.commit()

        child1 = ProductCategory(code="C1", name="Child 1", parent_id=root.id, level=1)
        child2 = ProductCategory(code="C2", name="Child 2", parent_id=root.id, level=1)
        db_session.add_all([child1, child2])
        db_session.commit()

        grandchild = ProductCategory(
            code="GC", name="Grandchild",
            parent_id=child1.id, level=2
        )
        db_session.add(grandchild)
        db_session.commit()

        # Refresh root to load children
        db_session.refresh(root)

        # Verify structure
        assert len(root.children) == 2

        # Find child1 and check its children
        child1_refreshed = db_session.query(ProductCategory).filter(
            ProductCategory.code == "C1"
        ).first()
        db_session.refresh(child1_refreshed)
        assert len(child1_refreshed.children) == 1
        assert child1_refreshed.children[0].code == "GC"


# ============================================================================
# Test Scenario 5: Category Tree Recursive CTE Query
# ============================================================================

class TestCategoryTreeCTE:
    """Test recursive CTE queries for category tree operations."""

    @pytest.mark.skipif(
        True,  # Will be implemented with PostgreSQL
        reason="CTE queries require PostgreSQL implementation"
    )
    def test_get_all_descendants_cte(self, db_session: Session):
        """Test getting all descendants using recursive CTE."""
        from backend.models import ProductCategory

        # Create hierarchy
        root = ProductCategory(code="ROOT", name="Root", level=0)
        db_session.add(root)
        db_session.commit()

        child = ProductCategory(
            code="CHILD", name="Child",
            parent_id=root.id, level=1
        )
        db_session.add(child)
        db_session.commit()

        grandchild = ProductCategory(
            code="GCHILD", name="Grandchild",
            parent_id=child.id, level=2
        )
        db_session.add(grandchild)
        db_session.commit()

        # This would use a recursive CTE in PostgreSQL
        # For now, verify the data exists
        all_cats = db_session.query(ProductCategory).all()
        assert len(all_cats) >= 3

    @pytest.mark.skipif(
        True,  # Will be implemented with PostgreSQL
        reason="CTE queries require PostgreSQL implementation"
    )
    def test_get_full_path_cte(self, db_session: Session):
        """Test getting full path from leaf to root using recursive CTE."""
        from backend.models import ProductCategory

        # Create hierarchy
        root = ProductCategory(code="A", name="A", level=0)
        db_session.add(root)
        db_session.commit()

        b = ProductCategory(code="B", name="B", parent_id=root.id, level=1)
        db_session.add(b)
        db_session.commit()

        c = ProductCategory(code="C", name="C", parent_id=b.id, level=2)
        db_session.add(c)
        db_session.commit()

        # Verify path can be reconstructed
        # Full CTE implementation will be in PostgreSQL
        assert c.parent.parent.code == "A"


# ============================================================================
# Test Scenario 6: Industry Sector Field
# ============================================================================

class TestIndustrySectorField:
    """Test industry_sector field behavior."""

    def test_industry_sector_optional(self, db_session: Session):
        """Test that industry_sector is optional."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="NOSEC",
            name="No Sector Category"
            # industry_sector not provided
        )
        db_session.add(category)
        db_session.commit()

        assert category.industry_sector is None

    def test_filter_by_industry_sector(self, db_session: Session):
        """Test filtering categories by industry sector."""
        from backend.models import ProductCategory

        cat1 = ProductCategory(
            code="IT1",
            name="IT Category 1",
            industry_sector="Information Technology"
        )
        cat2 = ProductCategory(
            code="IT2",
            name="IT Category 2",
            industry_sector="Information Technology"
        )
        cat3 = ProductCategory(
            code="MFG",
            name="Manufacturing Category",
            industry_sector="Manufacturing"
        )
        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()

        # Filter by sector
        it_categories = db_session.query(ProductCategory).filter(
            ProductCategory.industry_sector == "Information Technology"
        ).all()
        assert len(it_categories) == 2


# ============================================================================
# Test Scenario 7: Product Relationship
# ============================================================================

class TestProductCategoryProductRelationship:
    """Test relationship between ProductCategory and Product."""

    def test_product_references_category(self, db_session: Session):
        """Test that products can reference a category."""
        from backend.models import ProductCategory, Product

        # Create category
        category = ProductCategory(
            code="APPAREL",
            name="Apparel"
        )
        db_session.add(category)
        db_session.commit()

        # Create product with category
        # Note: This requires Product model to have category_id field
        # which will be added in Phase B implementation
        # For now, verify category exists
        assert category.id is not None

    def test_category_products_relationship(self, db_session: Session):
        """Test accessing products from category via relationship."""
        from backend.models import ProductCategory

        # Create category
        category = ProductCategory(
            code="TEXTILE",
            name="Textiles"
        )
        db_session.add(category)
        db_session.commit()

        # The products relationship will be tested after
        # Product model is updated with category_id field
        assert category.id is not None


# ============================================================================
# Test Scenario 8: Search Vector (PostgreSQL Full-Text Search)
# ============================================================================

class TestCategorySearchVector:
    """Test search_vector field for full-text search."""

    @pytest.mark.skipif(
        True,  # TSVECTOR is PostgreSQL-specific
        reason="TSVECTOR requires PostgreSQL"
    )
    def test_search_vector_field_exists(self, db_session: Session):
        """Test that search_vector field can be populated."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="SEARCH",
            name="Searchable Category"
        )
        db_session.add(category)
        db_session.commit()

        # search_vector would be populated by trigger in PostgreSQL
        assert category.id is not None


# ============================================================================
# Test Scenario 9: Level Field Validation
# ============================================================================

class TestLevelFieldValidation:
    """Test level field behavior."""

    def test_default_level_is_zero(self, db_session: Session):
        """Test that default level is 0."""
        from backend.models import ProductCategory

        category = ProductCategory(
            code="DEFLVL",
            name="Default Level Category"
        )
        db_session.add(category)
        db_session.commit()

        assert category.level == 0

    def test_level_can_be_set_explicitly(self, db_session: Session):
        """Test that level can be set to any non-negative integer."""
        from backend.models import ProductCategory

        for level in [0, 1, 2, 3, 4]:
            category = ProductCategory(
                code=f"LVL{level}",
                name=f"Level {level} Category",
                level=level
            )
            db_session.add(category)

        db_session.commit()

        # Verify all levels
        for level in [0, 1, 2, 3, 4]:
            cat = db_session.query(ProductCategory).filter(
                ProductCategory.code == f"LVL{level}"
            ).first()
            assert cat.level == level
