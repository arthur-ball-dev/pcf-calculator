"""
Test suite for v_bom_explosion recursive CTE view.

This test suite validates:
- Happy Path: 2-level BOM explosion
- Cumulative quantity calculation
- Cycle detection and prevention
- Multiple finished products support
- Edge cases (products with no BOM)
- Path tracking for cycle prevention
- Level limit enforcement

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE view implementation
- Tests should FAIL initially (view not implemented yet)
- Implementation must make tests PASS without modifying tests

Ported from in-memory SQLite + schema.sql (deleted in 65784c0) to the
PostgreSQL test database, where the view is created by the Alembic migrations.
Each test runs in a transaction that is rolled back, so nothing persists.

Reference: TASK-DB-002_SEQ-001_FROM-TL_TO-DB_2025-10-23-12-17-58_SPEC.md
"""

import os

import psycopg
import pytest
from psycopg.types.numeric import FloatLoader

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test"
)


@pytest.fixture
def db_connection():
    """Open a PostgreSQL test DB connection whose work is rolled back afterwards."""
    conn = psycopg.connect(TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://"))
    # Compare quantities as floats, as the original SQLite tests did
    conn.adapters.register_loader("numeric", FloatLoader)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def db_with_schema(db_connection):
    """Start each test from empty products/BOM tables (inside the rolled-back transaction)."""
    cursor = db_connection.cursor()
    cursor.execute("SET LOCAL lock_timeout = '10s'")
    cursor.execute("TRUNCATE TABLE products CASCADE")
    # The ORM generates bill_of_materials.id; give raw INSERTs a default for this transaction only
    cursor.execute("ALTER TABLE bill_of_materials ALTER COLUMN id SET DEFAULT md5(random()::text)")
    return db_connection


class TestBOMExplosionViewExists:
    """Test Scenario 0: View Creation and Structure"""

    def test_view_exists(self, db_with_schema):
        """Verify v_bom_explosion view is created."""
        cursor = db_with_schema.cursor()
        cursor.execute("""
            SELECT viewname FROM pg_views
            WHERE viewname = 'v_bom_explosion'
        """)
        result = cursor.fetchone()
        assert result is not None, "View 'v_bom_explosion' not found"

    def test_view_has_required_columns(self, db_with_schema):
        """Verify v_bom_explosion view has all required columns."""
        cursor = db_with_schema.cursor()

        # Insert minimal test data to query view structure
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('test-prod', 'TEST-001', 'Test Product', TRUE)
        """)

        # Query view to check columns
        cursor.execute("SELECT * FROM v_bom_explosion LIMIT 1")
        column_names = [description[0] for description in cursor.description]

        required_columns = [
            'root_id',
            'root_name',
            'component_id',
            'component_name',
            'level',
            'cumulative_quantity',
            'unit',
            'path'
        ]

        for col in required_columns:
            assert col in column_names, f"Column '{col}' missing from v_bom_explosion view"


class TestHappyPath:
    """Test Scenario 1: Happy Path - 2-Level BOM Explosion"""

    def test_tshirt_realistic_bom_explosion(self, db_with_schema):
        """Test BOM explosion for realistic t-shirt with 5 components."""
        cursor = db_with_schema.cursor()

        # Insert t-shirt finished product
        cursor.execute("""
            INSERT INTO products (id, code, name, unit, is_finished_product)
            VALUES ('tshirt-001', 'TSHIRT-001', 'Cotton T-Shirt', 'unit', TRUE)
        """)

        # Insert component materials
        components = [
            ('cotton-001', 'COTTON-001', 'cotton', 'kg', False),
            ('polyester-001', 'POLYESTER-001', 'polyester', 'kg', False),
            ('nylon-001', 'NYLON-001', 'nylon', 'kg', False),
            ('abs-001', 'ABS-001', 'plastic_abs', 'kg', False),
            ('paper-001', 'PAPER-001', 'paper', 'kg', False)
        ]

        for comp_id, code, name, unit, is_finished in components:
            cursor.execute("""
                INSERT INTO products (id, code, name, unit, is_finished_product)
                VALUES (%s, %s, %s, %s, %s)
            """, (comp_id, code, name, unit, is_finished))

        # Insert BOM relationships (from bom_tshirt_realistic.json)
        bom_entries = [
            ('tshirt-001', 'cotton-001', 0.18, 'kg'),
            ('tshirt-001', 'polyester-001', 0.015, 'kg'),
            ('tshirt-001', 'nylon-001', 0.005, 'kg'),
            ('tshirt-001', 'abs-001', 0.002, 'kg'),
            ('tshirt-001', 'paper-001', 0.001, 'kg')
        ]

        for parent_id, child_id, quantity, unit in bom_entries:
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity, unit)
                VALUES (%s, %s, %s, %s)
            """, (parent_id, child_id, quantity, unit))

        # Query v_bom_explosion
        cursor.execute("""
            SELECT root_id, component_name, level, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'tshirt-001'
            ORDER BY level, component_name
        """)
        results = cursor.fetchall()

        # Expected: 6 rows (1 root + 5 components)
        assert len(results) == 6, f"Expected 6 rows, got {len(results)}"

        # Verify root product (level 0)
        root = [r for r in results if r[2] == 0]
        assert len(root) == 1, "Expected exactly 1 root product"
        assert root[0][1] == 'Cotton T-Shirt'
        assert root[0][3] == 1.0

        # Verify level 1 components
        components_result = [r for r in results if r[2] == 1]
        assert len(components_result) == 5, "Expected 5 level-1 components"

        # Verify quantities
        component_quantities = {r[1]: r[3] for r in components_result}
        assert component_quantities['cotton'] == 0.18
        assert component_quantities['polyester'] == 0.015
        assert component_quantities['nylon'] == 0.005
        assert component_quantities['plastic_abs'] == 0.002
        assert component_quantities['paper'] == 0.001

    def test_simple_parent_child_relationship(self, db_with_schema):
        """Test simple 1-level BOM explosion."""
        cursor = db_with_schema.cursor()

        # Insert parent product
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('parent-001', 'PARENT-001', 'Parent Product', TRUE)
        """)

        # Insert child component
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('child-001', 'CHILD-001', 'Child Component', FALSE)
        """)

        # Insert BOM relationship
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('parent-001', 'child-001', 3.5)
        """)

        # Query view
        cursor.execute("""
            SELECT component_name, level, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'parent-001'
            ORDER BY level
        """)
        results = cursor.fetchall()

        assert len(results) == 2, "Expected 2 rows (1 parent + 1 child)"
        assert results[0][0] == 'Parent Product'
        assert results[0][1] == 0
        assert results[0][2] == 1.0
        assert results[1][0] == 'Child Component'
        assert results[1][1] == 1
        assert results[1][2] == 3.5


class TestCumulativeQuantityCalculation:
    """Test Scenario 2: Cumulative Quantity Calculation"""

    def test_two_level_cumulative_quantity(self, db_with_schema):
        """Test cumulative quantity calculation through 2 levels."""
        cursor = db_with_schema.cursor()

        # Create 2-level BOM: Product A (1) -> Product B (2) -> Material C (0.5kg)
        # Expected: Material C cumulative_quantity = 1 * 2 * 0.5 = 1.0kg
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('prod-a', 'PROD-A', 'Product A', TRUE),
                ('prod-b', 'PROD-B', 'Product B', FALSE),
                ('mat-c', 'MAT-C', 'Material C', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('prod-a', 'prod-b', 2.0),
                ('prod-b', 'mat-c', 0.5)
        """)

        # Query BOM explosion
        cursor.execute("""
            SELECT component_name, level, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'prod-a'
            ORDER BY level
        """)
        results = cursor.fetchall()

        # Verify 3 rows: Product A (level 0), Product B (level 1), Material C (level 2)
        assert len(results) == 3, f"Expected 3 rows, got {len(results)}"

        # Verify cumulative quantities
        assert results[0][0] == 'Product A'
        assert results[0][1] == 0
        assert results[0][2] == 1.0

        assert results[1][0] == 'Product B'
        assert results[1][1] == 1
        assert results[1][2] == 2.0

        assert results[2][0] == 'Material C'
        assert results[2][1] == 2
        assert results[2][2] == 1.0, f"Expected 1.0, got {results[2][2]}"

    def test_multiple_children_quantity_calculation(self, db_with_schema):
        """Test cumulative quantities with multiple children at same level."""
        cursor = db_with_schema.cursor()

        # Product with 3 components at different quantities
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('assembly', 'ASSEMBLY-001', 'Assembly', TRUE),
                ('part-a', 'PART-A', 'Part A', FALSE),
                ('part-b', 'PART-B', 'Part B', FALSE),
                ('part-c', 'PART-C', 'Part C', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('assembly', 'part-a', 10.0),
                ('assembly', 'part-b', 5.0),
                ('assembly', 'part-c', 2.5)
        """)

        # Query view
        cursor.execute("""
            SELECT component_name, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'assembly' AND level = 1
            ORDER BY component_name
        """)
        results = cursor.fetchall()

        assert len(results) == 3
        assert results[0][0] == 'Part A'
        assert results[0][1] == 10.0
        assert results[1][0] == 'Part B'
        assert results[1][1] == 5.0
        assert results[2][0] == 'Part C'
        assert results[2][1] == 2.5


class TestCycleDetection:
    """Test Scenario 3: Cycle Detection"""

    def test_no_infinite_loop_with_complex_hierarchy(self, db_with_schema):
        """Test that view terminates with reasonable depth limit."""
        cursor = db_with_schema.cursor()

        # Create a long chain (but not circular)
        # A -> B -> C -> D -> E
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('prod-a', 'PROD-A', 'Product A', TRUE),
                ('prod-b', 'PROD-B', 'Product B', FALSE),
                ('prod-c', 'PROD-C', 'Product C', FALSE),
                ('prod-d', 'PROD-D', 'Product D', FALSE),
                ('prod-e', 'PROD-E', 'Product E', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('prod-a', 'prod-b', 1.0),
                ('prod-b', 'prod-c', 1.0),
                ('prod-c', 'prod-d', 1.0),
                ('prod-d', 'prod-e', 1.0)
        """)

        # Query should complete without infinite loop
        cursor.execute("""
            SELECT COUNT(*) FROM v_bom_explosion WHERE root_id = 'prod-a'
        """)
        count = cursor.fetchone()[0]

        # Should return 5 rows (levels 0-4)
        assert count == 5, f"Expected 5 rows, got {count}"

        # Verify max level is 4
        cursor.execute("""
            SELECT MAX(level) FROM v_bom_explosion WHERE root_id = 'prod-a'
        """)
        max_level = cursor.fetchone()[0]
        assert max_level == 4

    def test_level_limit_enforcement(self, db_with_schema):
        """Test that level limit of 10 is enforced."""
        cursor = db_with_schema.cursor()

        # Create a chain longer than 10 levels
        products = []
        for i in range(12):
            is_finished = i == 0
            cursor.execute("""
                INSERT INTO products (id, code, name, is_finished_product)
                VALUES (%s, %s, %s, %s)
            """, (f'prod-{i}', f'PROD-{i:03d}', f'Product {i}', is_finished))
            products.append(f'prod-{i}')

        # Create chain: 0 -> 1 -> 2 -> ... -> 11
        for i in range(11):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES (%s, %s, 1.0)
            """, (products[i], products[i + 1]))

        # Query view
        cursor.execute("""
            SELECT MAX(level) FROM v_bom_explosion WHERE root_id = 'prod-0'
        """)
        max_level = cursor.fetchone()[0]

        # Should stop at level 9 (0-9 = 10 levels total, due to level < 10 check)
        assert max_level < 10, f"Expected max level < 10, got {max_level}"

    def test_path_tracking_format(self, db_with_schema):
        """Test that path column correctly tracks component IDs."""
        cursor = db_with_schema.cursor()

        # Create simple hierarchy: A -> B -> C
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('a', 'A', 'Product A', TRUE),
                ('b', 'B', 'Product B', FALSE),
                ('c', 'C', 'Product C', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('a', 'b', 1.0),
                ('b', 'c', 1.0)
        """)

        # Query paths
        cursor.execute("""
            SELECT component_name, level, path
            FROM v_bom_explosion
            WHERE root_id = 'a'
            ORDER BY level
        """)
        results = cursor.fetchall()

        # Verify path format: starts with root ID, uses / separator
        assert results[0][2] == 'a', f"Root path should be 'a', got {results[0][2]}"
        assert results[1][2] == 'a/b', f"Level 1 path should be 'a/b', got {results[1][2]}"
        assert results[2][2] == 'a/b/c', f"Level 2 path should be 'a/b/c', got {results[2][2]}"


class TestMultipleFinishedProducts:
    """Test Scenario 4: Multiple Finished Products"""

    def test_three_finished_products_explosion(self, db_with_schema):
        """Test BOM explosion returns separate hierarchies for 3 finished products."""
        cursor = db_with_schema.cursor()

        # Create 3 finished products with their components
        # T-Shirt with cotton
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('tshirt', 'TSHIRT-001', 'T-Shirt', TRUE),
                ('cotton', 'COTTON-001', 'Cotton', FALSE),
                ('bottle', 'BOTTLE-001', 'Water Bottle', TRUE),
                ('plastic', 'PLASTIC-001', 'PET Plastic', FALSE),
                ('phone-case', 'CASE-001', 'Phone Case', TRUE),
                ('abs', 'ABS-001', 'ABS Plastic', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('tshirt', 'cotton', 0.2),
                ('bottle', 'plastic', 0.025),
                ('phone-case', 'abs', 0.03)
        """)

        # Query all finished products
        cursor.execute("""
            SELECT DISTINCT root_id, root_name
            FROM v_bom_explosion
            ORDER BY root_name
        """)
        roots = cursor.fetchall()

        assert len(roots) == 3, f"Expected 3 finished products, got {len(roots)}"

        # Verify each product has correct root_id
        cursor.execute("""
            SELECT root_id, COUNT(*) as component_count
            FROM v_bom_explosion
            GROUP BY root_id
            ORDER BY root_id
        """)
        counts = cursor.fetchall()

        # Each should have 2 rows (1 root + 1 component)
        assert all(count[1] == 2 for count in counts), "Each product should have 2 rows"

    def test_root_id_matches_finished_product(self, db_with_schema):
        """Test that root_id correctly identifies the finished product."""
        cursor = db_with_schema.cursor()

        # Create finished product and component
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('finished-123', 'FIN-123', 'Finished Product', TRUE),
                ('comp-456', 'COMP-456', 'Component', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('finished-123', 'comp-456', 1.0)
        """)

        # Query view
        cursor.execute("""
            SELECT root_id, component_id, level
            FROM v_bom_explosion
            WHERE root_id = 'finished-123'
        """)
        results = cursor.fetchall()

        # All rows should have same root_id
        assert all(r[0] == 'finished-123' for r in results)

        # Level 0 should have component_id == root_id
        level_0 = [r for r in results if r[2] == 0]
        assert len(level_0) == 1
        assert level_0[0][1] == 'finished-123'


class TestEdgeCases:
    """Test Scenario 5: Edge Cases"""

    def test_product_with_no_bom(self, db_with_schema):
        """Test finished product with no BOM entries."""
        cursor = db_with_schema.cursor()

        # Create finished product WITHOUT any BOM entries
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('simple-001', 'SIMPLE-001', 'Simple Product', TRUE)
        """)

        # Query view
        cursor.execute("""
            SELECT root_id, component_name, level, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'simple-001'
        """)
        results = cursor.fetchall()

        # Should return only root level
        assert len(results) == 1, f"Expected 1 row, got {len(results)}"
        assert results[0][0] == 'simple-001'
        assert results[0][1] == 'Simple Product'
        assert results[0][2] == 0
        assert results[0][3] == 1.0

    def test_component_not_finished_product_excluded(self, db_with_schema):
        """Test that components (is_finished_product=0) don't appear as roots."""
        cursor = db_with_schema.cursor()

        # Create component (NOT finished product)
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('component-001', 'COMP-001', 'Just a Component', FALSE)
        """)

        # Query view for this component as root
        cursor.execute("""
            SELECT COUNT(*)
            FROM v_bom_explosion
            WHERE root_id = 'component-001'
        """)
        count = cursor.fetchone()[0]

        # Should return 0 rows (not a finished product)
        assert count == 0, "Component should not appear as root in BOM explosion"

    def test_zero_quantity_not_allowed(self, db_with_schema):
        """Test that BOM entries with zero quantity are rejected by CHECK constraint."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('parent', 'PARENT-001', 'Parent', TRUE),
                ('child', 'CHILD-001', 'Child', FALSE)
        """)

        # Try to insert BOM with quantity = 0
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent', 'child', 0.0)
            """)

    def test_negative_quantity_not_allowed(self, db_with_schema):
        """Test that BOM entries with negative quantity are rejected."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('parent', 'PARENT-001', 'Parent', TRUE),
                ('child', 'CHILD-001', 'Child', FALSE)
        """)

        # Try to insert BOM with negative quantity
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent', 'child', -1.5)
            """)

    def test_fractional_quantities_supported(self, db_with_schema):
        """Test that fractional quantities are correctly calculated."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('prod', 'PROD-001', 'Product', TRUE),
                ('comp', 'COMP-001', 'Component', FALSE)
        """)

        # Insert BOM with fractional quantity
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('prod', 'comp', 0.00123)
        """)

        # Query view
        cursor.execute("""
            SELECT cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'prod' AND level = 1
        """)
        result = cursor.fetchone()

        # Verify fractional quantity is preserved
        assert result[0] == 0.00123


class TestViewPerformance:
    """Test performance characteristics of the view."""

    def test_realistic_tshirt_query_performance(self, db_with_schema):
        """Test query completes reasonably fast for realistic BOM."""
        import time

        cursor = db_with_schema.cursor()

        # Insert realistic t-shirt BOM (6 rows)
        cursor.execute("""
            INSERT INTO products (id, code, name, unit, is_finished_product)
            VALUES ('tshirt-001', 'TSHIRT-001', 'Cotton T-Shirt', 'unit', TRUE)
        """)

        components = [
            ('cotton-001', 'COTTON-001', 'cotton', 'kg', False),
            ('polyester-001', 'POLYESTER-001', 'polyester', 'kg', False),
            ('nylon-001', 'NYLON-001', 'nylon', 'kg', False),
            ('abs-001', 'ABS-001', 'plastic_abs', 'kg', False),
            ('paper-001', 'PAPER-001', 'paper', 'kg', False)
        ]

        for comp_id, code, name, unit, is_finished in components:
            cursor.execute("""
                INSERT INTO products (id, code, name, unit, is_finished_product)
                VALUES (%s, %s, %s, %s, %s)
            """, (comp_id, code, name, unit, is_finished))

        bom_entries = [
            ('tshirt-001', 'cotton-001', 0.18, 'kg'),
            ('tshirt-001', 'polyester-001', 0.015, 'kg'),
            ('tshirt-001', 'nylon-001', 0.005, 'kg'),
            ('tshirt-001', 'abs-001', 0.002, 'kg'),
            ('tshirt-001', 'paper-001', 0.001, 'kg')
        ]

        for parent_id, child_id, quantity, unit in bom_entries:
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity, unit)
                VALUES (%s, %s, %s, %s)
            """, (parent_id, child_id, quantity, unit))

        # Measure query time
        start_time = time.time()
        cursor.execute("SELECT * FROM v_bom_explosion WHERE root_id = 'tshirt-001'")
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in under 100ms for 2-level BOM
        assert elapsed_ms < 100, f"Query took {elapsed_ms:.2f}ms, expected < 100ms"
        assert len(results) == 6

    def test_multiple_products_query(self, db_with_schema):
        """Test querying all finished products at once."""
        cursor = db_with_schema.cursor()

        # Create 10 finished products each with 3 components
        for i in range(10):
            cursor.execute("""
                INSERT INTO products (id, code, name, is_finished_product)
                VALUES (%s, %s, %s, TRUE)
            """, (f'prod-{i}', f'PROD-{i:03d}', f'Product {i}'))

            for j in range(3):
                cursor.execute("""
                    INSERT INTO products (id, code, name, is_finished_product)
                    VALUES (%s, %s, %s, FALSE)
                """, (f'comp-{i}-{j}', f'COMP-{i:03d}-{j}', f'Component {i}-{j}'))

                cursor.execute("""
                    INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                    VALUES (%s, %s, 1.0)
                """, (f'prod-{i}', f'comp-{i}-{j}'))

        # Query all products
        cursor.execute("SELECT COUNT(*) FROM v_bom_explosion")
        count = cursor.fetchone()[0]

        # Should return 10 * 4 = 40 rows (10 roots + 30 components)
        assert count == 40, f"Expected 40 rows, got {count}"


class TestDataIntegrity:
    """Test data integrity and constraint validation."""

    def test_self_reference_prevented_by_check_constraint(self, db_with_schema):
        """Test that self-referencing BOM entries are rejected."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('prod-self', 'PROD-SELF', 'Self Product', TRUE)
        """)

        # Try to create self-referencing BOM
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('prod-self', 'prod-self', 1.0)
            """)

    def test_duplicate_parent_child_prevented(self, db_with_schema):
        """Test that duplicate BOM entries are prevented by UNIQUE constraint."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('parent', 'PARENT-001', 'Parent', TRUE),
                ('child', 'CHILD-001', 'Child', FALSE)
        """)

        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('parent', 'child', 1.0)
        """)

        # Try to insert duplicate
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent', 'child', 2.0)
            """)

    def test_foreign_key_constraint_on_parent(self, db_with_schema):
        """Test foreign key constraint on parent_product_id."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('child', 'CHILD-001', 'Child', FALSE)
        """)

        # Try to reference non-existent parent
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('nonexistent-parent', 'child', 1.0)
            """)

    def test_foreign_key_constraint_on_child(self, db_with_schema):
        """Test foreign key constraint on child_product_id."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('parent', 'PARENT-001', 'Parent', TRUE)
        """)

        # Try to reference non-existent child
        with pytest.raises(psycopg.IntegrityError):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent', 'nonexistent-child', 1.0)
            """)
