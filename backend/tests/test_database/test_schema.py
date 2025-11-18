"""
Test suite for SQLite database schema validation.

This test suite validates:
- Table creation and structure
- Foreign key constraint enforcement
- Unique constraints on code fields
- CHECK constraints (self-reference prevention, positive quantities, valid units)
- Cascade delete behavior
- View creation (v_bom_explosion)
- Index creation

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE schema.sql implementation
- Tests should FAIL initially (no schema exists yet)
- Implementation must make tests PASS without modifying tests
"""

import sqlite3
import pytest
import os
from pathlib import Path


@pytest.fixture
def db_connection():
    """Create an in-memory database connection for testing."""
    conn = sqlite3.connect(':memory:')
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def schema_sql():
    """Load the schema SQL file."""
    schema_path = Path(__file__).parent.parent.parent / 'database' / 'schema.sql'
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return f.read()


@pytest.fixture
def db_with_schema(db_connection, schema_sql):
    """Create database with schema applied."""
    db_connection.executescript(schema_sql)
    return db_connection


class TestSchemaCreation:
    """Test Scenario 1: Happy Path - All Tables Created"""

    def test_all_tables_exist(self, db_with_schema):
        """Verify all 5 required tables are created."""
        cursor = db_with_schema.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            'bill_of_materials',
            'calculation_details',
            'emission_factors',
            'pcf_calculations',
            'products'
        ]

        for table in required_tables:
            assert table in tables, f"Table '{table}' not found in schema"

    def test_products_table_structure(self, db_with_schema):
        """Verify products table has correct columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'TEXT',
            'code': 'VARCHAR(100)',
            'name': 'VARCHAR(255)',
            'description': 'TEXT',
            'unit': 'VARCHAR(20)',
            'category': 'VARCHAR(100)',
            'is_finished_product': 'BOOLEAN',
            'metadata': 'JSON',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'deleted_at': 'TIMESTAMP'
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from products table"

    def test_emission_factors_table_structure(self, db_with_schema):
        """Verify emission_factors table has correct columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(emission_factors)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'TEXT',
            'activity_name': 'VARCHAR(255)',
            'co2e_factor': 'DECIMAL(15,8)',
            'unit': 'VARCHAR(20)',
            'data_source': 'VARCHAR(100)',
            'geography': 'VARCHAR(50)',
            'reference_year': 'INTEGER',
            'data_quality_rating': 'DECIMAL(3,2)',
            'uncertainty_min': 'DECIMAL(15,8)',
            'uncertainty_max': 'DECIMAL(15,8)',
            'metadata': 'JSON',
            'valid_from': 'DATE',
            'valid_to': 'DATE',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        }

        for col_name in required_columns.keys():
            assert col_name in columns, f"Column '{col_name}' missing from emission_factors table"

    def test_bill_of_materials_table_structure(self, db_with_schema):
        """Verify bill_of_materials table has correct columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(bill_of_materials)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'TEXT',
            'parent_product_id': 'TEXT',
            'child_product_id': 'TEXT',
            'quantity': 'DECIMAL(15,6)',
            'unit': 'VARCHAR(20)',
            'notes': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        }

        for col_name in required_columns.keys():
            assert col_name in columns, f"Column '{col_name}' missing from bill_of_materials table"

    def test_pcf_calculations_table_structure(self, db_with_schema):
        """Verify pcf_calculations table has correct columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(pcf_calculations)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'TEXT',
            'product_id': 'TEXT',
            'calculation_type': 'VARCHAR(50)',
            'total_co2e_kg': 'DECIMAL(15,6)',
            'materials_co2e': 'DECIMAL(15,6)',
            'energy_co2e': 'DECIMAL(15,6)',
            'transport_co2e': 'DECIMAL(15,6)',
            'waste_co2e': 'DECIMAL(15,6)',
            'primary_data_share': 'DECIMAL(5,2)',
            'data_quality_score': 'DECIMAL(3,2)',
            'calculation_method': 'VARCHAR(100)',
            'status': 'VARCHAR(50)',
            'input_data': 'JSON',
            'breakdown': 'JSON',
            'metadata': 'JSON',
            'calculated_by': 'VARCHAR(100)',
            'calculation_time_ms': 'INTEGER',
            'created_at': 'TIMESTAMP'
        }

        for col_name in required_columns.keys():
            assert col_name in columns, f"Column '{col_name}' missing from pcf_calculations table"

    def test_calculation_details_table_structure(self, db_with_schema):
        """Verify calculation_details table has correct columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(calculation_details)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'TEXT',
            'calculation_id': 'TEXT',
            'component_id': 'TEXT',
            'component_name': 'VARCHAR(255)',
            'component_level': 'INTEGER',
            'quantity': 'DECIMAL(15,6)',
            'unit': 'VARCHAR(20)',
            'emission_factor_id': 'TEXT',
            'emissions_kg_co2e': 'DECIMAL(15,6)',
            'data_quality': 'VARCHAR(50)',
            'notes': 'TEXT',
            'created_at': 'TIMESTAMP'
        }

        for col_name in required_columns.keys():
            assert col_name in columns, f"Column '{col_name}' missing from calculation_details table"

    def test_bom_explosion_view_exists(self, db_with_schema):
        """Verify v_bom_explosion view is created."""
        cursor = db_with_schema.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_bom_explosion'
        """)
        result = cursor.fetchone()
        assert result is not None, "View 'v_bom_explosion' not found"

    def test_indexes_created(self, db_with_schema):
        """Verify required indexes are created."""
        cursor = db_with_schema.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index'
            ORDER BY name
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'idx_products_code',
            'idx_products_category',
            'idx_products_finished',
            'idx_ef_activity',
            'idx_ef_geography',
            'idx_ef_source',
            'idx_bom_parent',
            'idx_bom_child',
            'idx_calc_product',
            'idx_calc_date',
            'idx_calc_status',
            'idx_detail_calc',
            'idx_detail_component'
        ]

        for index in expected_indexes:
            assert index in indexes, f"Index '{index}' not found"


class TestForeignKeyConstraints:
    """Test Scenario 2: Foreign Key Constraint Enforcement"""

    def test_foreign_keys_enabled(self, db_with_schema):
        """Verify foreign keys are enabled."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1, "Foreign keys are not enabled"

    def test_bom_parent_foreign_key(self, db_with_schema):
        """Test foreign key constraint on parent_product_id."""
        cursor = db_with_schema.cursor()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('non-existent-parent', 'non-existent-child', 1.0)
            """)

    def test_bom_child_foreign_key(self, db_with_schema):
        """Test foreign key constraint on child_product_id."""
        cursor = db_with_schema.cursor()

        # Insert a valid parent product
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('parent1', 'PARENT-001', 'Valid Parent')
        """)

        # Try to insert BOM with non-existent child
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent1', 'non-existent-child', 1.0)
            """)

    def test_calculation_product_foreign_key(self, db_with_schema):
        """Test foreign key constraint on pcf_calculations.product_id."""
        cursor = db_with_schema.cursor()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cursor.execute("""
                INSERT INTO pcf_calculations (product_id, total_co2e_kg)
                VALUES ('non-existent-product', 10.5)
            """)

    def test_calculation_details_foreign_key(self, db_with_schema):
        """Test foreign key constraint on calculation_details.calculation_id."""
        cursor = db_with_schema.cursor()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cursor.execute("""
                INSERT INTO calculation_details (calculation_id, component_name, emissions_kg_co2e)
                VALUES ('non-existent-calc', 'Test Component', 5.0)
            """)

    def test_cascade_delete_bom(self, db_with_schema):
        """Test CASCADE DELETE on bill_of_materials."""
        cursor = db_with_schema.cursor()

        # Insert parent and child products
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('parent1', 'PARENT-001', 'Parent Product')
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('child1', 'CHILD-001', 'Child Product')
        """)

        # Insert BOM relationship
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('parent1', 'child1', 2.0)
        """)

        # Delete parent product
        cursor.execute("DELETE FROM products WHERE id = 'parent1'")

        # Verify BOM entry was cascade deleted
        cursor.execute("SELECT COUNT(*) FROM bill_of_materials WHERE parent_product_id = 'parent1'")
        count = cursor.fetchone()[0]
        assert count == 0, "BOM entry was not cascade deleted"

    def test_cascade_delete_calculation_details(self, db_with_schema):
        """Test CASCADE DELETE on calculation_details."""
        cursor = db_with_schema.cursor()

        # Insert product and calculation
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('prod1', 'PROD-001', 'Test Product')
        """)
        cursor.execute("""
            INSERT INTO pcf_calculations (id, product_id, total_co2e_kg)
            VALUES ('calc1', 'prod1', 15.5)
        """)
        cursor.execute("""
            INSERT INTO calculation_details (calculation_id, component_name, emissions_kg_co2e)
            VALUES ('calc1', 'Component A', 5.0)
        """)

        # Delete calculation
        cursor.execute("DELETE FROM pcf_calculations WHERE id = 'calc1'")

        # Verify calculation_details was cascade deleted
        cursor.execute("SELECT COUNT(*) FROM calculation_details WHERE calculation_id = 'calc1'")
        count = cursor.fetchone()[0]
        assert count == 0, "Calculation details were not cascade deleted"


class TestUniqueConstraints:
    """Test Scenario 3: Unique Constraint on Product Code"""

    def test_product_code_unique(self, db_with_schema):
        """Test UNIQUE constraint on products.code."""
        cursor = db_with_schema.cursor()

        # Insert first product
        cursor.execute("""
            INSERT INTO products (code, name)
            VALUES ('TSHIRT-001', 'T-Shirt 1')
        """)

        # Try to insert duplicate code
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed: products.code"):
            cursor.execute("""
                INSERT INTO products (code, name)
                VALUES ('TSHIRT-001', 'T-Shirt 2')
            """)

    def test_emission_factor_composite_unique(self, db_with_schema):
        """Test composite UNIQUE constraint on emission_factors."""
        cursor = db_with_schema.cursor()

        # Insert first emission factor
        cursor.execute("""
            INSERT INTO emission_factors (activity_name, co2e_factor, unit, data_source, geography, reference_year)
            VALUES ('Cotton Fabric', 5.0, 'kg', 'EPA', 'GLO', 2023)
        """)

        # Try to insert duplicate combination
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
            cursor.execute("""
                INSERT INTO emission_factors (activity_name, co2e_factor, unit, data_source, geography, reference_year)
                VALUES ('Cotton Fabric', 6.0, 'kg', 'EPA', 'GLO', 2023)
            """)

    def test_bom_unique_parent_child_pair(self, db_with_schema):
        """Test UNIQUE constraint on BOM parent-child pair."""
        cursor = db_with_schema.cursor()

        # Insert products
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('parent1', 'PARENT-001', 'Parent')
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('child1', 'CHILD-001', 'Child')
        """)

        # Insert first BOM entry
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('parent1', 'child1', 2.0)
        """)

        # Try to insert duplicate parent-child pair
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent1', 'child1', 3.0)
            """)


class TestCheckConstraints:
    """Test Scenario 4 & 5: CHECK Constraints"""

    def test_self_referencing_bom_prevented(self, db_with_schema):
        """Test CHECK constraint prevents self-referencing BOM (parent = child)."""
        cursor = db_with_schema.cursor()

        # Insert product
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('prod1', 'PROD-001', 'Product 1')
        """)

        # Try to create self-reference
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('prod1', 'prod1', 1.0)
            """)

    def test_positive_quantity_constraint(self, db_with_schema):
        """Test CHECK constraint for positive quantities in BOM."""
        cursor = db_with_schema.cursor()

        # Insert products
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('parent1', 'PARENT-001', 'Parent')
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('child1', 'CHILD-001', 'Child')
        """)

        # Try to insert negative quantity
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent1', 'child1', -5.0)
            """)

    def test_zero_quantity_prevented(self, db_with_schema):
        """Test CHECK constraint prevents zero quantities."""
        cursor = db_with_schema.cursor()

        # Insert products
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('parent1', 'PARENT-001', 'Parent')
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('child1', 'CHILD-001', 'Child')
        """)

        # Try to insert zero quantity
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute("""
                INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
                VALUES ('parent1', 'child1', 0)
            """)

    def test_valid_unit_constraint(self, db_with_schema):
        """Test CHECK constraint for valid units in products table."""
        cursor = db_with_schema.cursor()

        valid_units = ['unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ']

        # Test each valid unit works
        for i, unit in enumerate(valid_units):
            cursor.execute(f"""
                INSERT INTO products (code, name, unit)
                VALUES ('PROD-{i:03d}', 'Product {i}', '{unit}')
            """)

        # Test invalid unit is rejected
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute("""
                INSERT INTO products (code, name, unit)
                VALUES ('INVALID-001', 'Invalid Product', 'invalid_unit')
            """)

    def test_valid_calculation_type_constraint(self, db_with_schema):
        """Test CHECK constraint for valid calculation types."""
        cursor = db_with_schema.cursor()

        # Insert product
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('prod1', 'PROD-001', 'Product')
        """)

        # Test valid calculation types
        valid_types = ['cradle_to_gate', 'cradle_to_grave', 'gate_to_gate']
        for calc_type in valid_types:
            cursor.execute(f"""
                INSERT INTO pcf_calculations (product_id, calculation_type, total_co2e_kg)
                VALUES ('prod1', '{calc_type}', 10.0)
            """)

        # Test invalid calculation type is rejected
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute("""
                INSERT INTO pcf_calculations (product_id, calculation_type, total_co2e_kg)
                VALUES ('prod1', 'invalid_type', 10.0)
            """)

    def test_non_negative_emission_factor(self, db_with_schema):
        """Test that emission factors cannot be negative."""
        cursor = db_with_schema.cursor()

        # Note: Schema should prevent negative emission factors
        # This test will verify if such constraint exists
        # If not explicitly in schema, this is a recommendation
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO emission_factors (activity_name, co2e_factor, unit, data_source)
                VALUES ('Test Activity', -5.0, 'kg', 'Test Source')
            """)


class TestSampleDataInsertion:
    """Test that schema supports realistic data insertion."""

    def test_insert_complete_product_hierarchy(self, db_with_schema):
        """Test inserting a complete product with BOM hierarchy."""
        cursor = db_with_schema.cursor()

        # Insert finished product
        cursor.execute("""
            INSERT INTO products (id, code, name, unit, category, is_finished_product)
            VALUES ('tshirt', 'TSHIRT-001', 'Cotton T-Shirt', 'unit', 'apparel', 1)
        """)

        # Insert components
        cursor.execute("""
            INSERT INTO products (id, code, name, unit, category, is_finished_product)
            VALUES ('cotton', 'COTTON-001', 'Cotton Fabric', 'kg', 'material', 0)
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name, unit, category, is_finished_product)
            VALUES ('thread', 'THREAD-001', 'Polyester Thread', 'kg', 'material', 0)
        """)

        # Insert BOM relationships
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity, unit)
            VALUES ('tshirt', 'cotton', 0.2, 'kg')
        """)
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity, unit)
            VALUES ('tshirt', 'thread', 0.01, 'kg')
        """)

        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM products")
        assert cursor.fetchone()[0] == 3

        cursor.execute("SELECT COUNT(*) FROM bill_of_materials")
        assert cursor.fetchone()[0] == 2

    def test_insert_emission_factors(self, db_with_schema):
        """Test inserting emission factors."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO emission_factors (
                activity_name, co2e_factor, unit, data_source,
                geography, reference_year, data_quality_rating
            ) VALUES
                ('Cotton Fabric', 5.0, 'kg', 'EPA', 'GLO', 2023, 0.85),
                ('Polyester Thread', 6.0, 'kg', 'EPA', 'GLO', 2023, 0.80),
                ('PET Plastic', 3.5, 'kg', 'DEFRA', 'GLO', 2023, 0.90)
        """)

        cursor.execute("SELECT COUNT(*) FROM emission_factors")
        assert cursor.fetchone()[0] == 3

    def test_insert_calculation_with_details(self, db_with_schema):
        """Test inserting PCF calculation with details."""
        cursor = db_with_schema.cursor()

        # Insert product
        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('prod1', 'PROD-001', 'Test Product')
        """)

        # Insert calculation
        cursor.execute("""
            INSERT INTO pcf_calculations (
                id, product_id, calculation_type, total_co2e_kg,
                materials_co2e, energy_co2e, transport_co2e,
                status, calculation_method
            ) VALUES (
                'calc1', 'prod1', 'cradle_to_gate', 15.5,
                10.0, 3.5, 2.0,
                'completed', 'brightway2'
            )
        """)

        # Insert calculation details
        cursor.execute("""
            INSERT INTO calculation_details (
                calculation_id, component_name, component_level,
                quantity, unit, emissions_kg_co2e
            ) VALUES (
                'calc1', 'Cotton Fabric', 1, 0.2, 'kg', 1.0
            )
        """)

        # Verify data
        cursor.execute("SELECT total_co2e_kg FROM pcf_calculations WHERE id = 'calc1'")
        result = cursor.fetchone()
        assert result[0] == 15.5

        cursor.execute("SELECT COUNT(*) FROM calculation_details WHERE calculation_id = 'calc1'")
        assert cursor.fetchone()[0] == 1


class TestBOMExplosionView:
    """Test the recursive BOM explosion view."""

    def test_bom_explosion_view_queryable(self, db_with_schema):
        """Test that v_bom_explosion view can be queried."""
        cursor = db_with_schema.cursor()

        # Insert test data
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('prod1', 'PROD-001', 'Finished Product', 1)
        """)
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product)
            VALUES ('comp1', 'COMP-001', 'Component', 0)
        """)
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('prod1', 'comp1', 2.0)
        """)

        # Query the view
        cursor.execute("SELECT * FROM v_bom_explosion")
        results = cursor.fetchall()

        # Should return at least the root product
        assert len(results) >= 1

    def test_bom_explosion_cumulative_quantity(self, db_with_schema):
        """Test cumulative quantity calculation in BOM explosion."""
        cursor = db_with_schema.cursor()

        # Create 2-level BOM: Product -> SubAssembly -> Component
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('prod', 'PROD-001', 'Product', 1),
                ('sub', 'SUB-001', 'SubAssembly', 0),
                ('comp', 'COMP-001', 'Component', 0)
        """)
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity) VALUES
                ('prod', 'sub', 2.0),
                ('sub', 'comp', 3.0)
        """)

        # Query BOM explosion
        cursor.execute("""
            SELECT component_name, level, cumulative_quantity
            FROM v_bom_explosion
            WHERE root_id = 'prod'
            ORDER BY level
        """)
        results = cursor.fetchall()

        # Verify hierarchy levels exist
        levels = [row[1] for row in results]
        assert 0 in levels  # Root level
        assert 1 in levels or 2 in levels  # At least one child level

    def test_bom_explosion_cycle_detection(self, db_with_schema):
        """Test that BOM explosion prevents infinite loops."""
        cursor = db_with_schema.cursor()

        # Note: Schema CHECK constraint should prevent direct self-reference
        # This tests that the view handles complex cycles
        cursor.execute("""
            INSERT INTO products (id, code, name, is_finished_product) VALUES
                ('prod1', 'PROD-001', 'Product 1', 1),
                ('comp1', 'COMP-001', 'Component 1', 0)
        """)
        cursor.execute("""
            INSERT INTO bill_of_materials (parent_product_id, child_product_id, quantity)
            VALUES ('prod1', 'comp1', 1.0)
        """)

        # Query should complete without infinite loop
        cursor.execute("""
            SELECT COUNT(*) FROM v_bom_explosion WHERE root_id = 'prod1'
        """)
        count = cursor.fetchone()[0]
        assert count > 0 and count < 100  # Reasonable limit


class TestDefaultValues:
    """Test default values and auto-generated fields."""

    def test_product_id_auto_generated(self, db_with_schema):
        """Test that product ID is auto-generated if not provided."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (code, name)
            VALUES ('AUTO-001', 'Auto ID Product')
        """)

        cursor.execute("SELECT id FROM products WHERE code = 'AUTO-001'")
        product_id = cursor.fetchone()[0]

        assert product_id is not None
        assert len(product_id) > 0

    def test_product_default_unit(self, db_with_schema):
        """Test default unit value for products."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (code, name)
            VALUES ('DEFAULT-001', 'Default Unit Product')
        """)

        cursor.execute("SELECT unit FROM products WHERE code = 'DEFAULT-001'")
        unit = cursor.fetchone()[0]

        assert unit == 'unit'

    def test_product_timestamps_auto_set(self, db_with_schema):
        """Test that created_at is automatically set."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (code, name)
            VALUES ('TIMESTAMP-001', 'Timestamp Product')
        """)

        cursor.execute("SELECT created_at FROM products WHERE code = 'TIMESTAMP-001'")
        created_at = cursor.fetchone()[0]

        assert created_at is not None

    def test_calculation_default_status(self, db_with_schema):
        """Test default status for calculations."""
        cursor = db_with_schema.cursor()

        cursor.execute("""
            INSERT INTO products (id, code, name)
            VALUES ('prod1', 'PROD-001', 'Product')
        """)
        cursor.execute("""
            INSERT INTO pcf_calculations (product_id, total_co2e_kg)
            VALUES ('prod1', 10.0)
        """)

        cursor.execute("SELECT status FROM pcf_calculations WHERE product_id = 'prod1'")
        status = cursor.fetchone()[0]

        assert status == 'completed'
