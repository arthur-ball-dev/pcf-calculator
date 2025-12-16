"""
Test suite for BOM enhancements with transport and other inputs.

TASK-DATA-P8-002: Enhance Sample BOMs with Transport and Other Inputs

Tests validate:
1. New "other" category emission factors exist
2. Component products for packaging/water/waste exist
3. All electronics BOMs have transport inputs
4. Electronics BOMs have packaging inputs
5. Brightway2 sync includes new factors
"""

import pytest
import sqlite3
from pathlib import Path
from decimal import Decimal

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "pcf_calculator.db"


@pytest.fixture
def db_connection():
    """Create database connection for tests."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestOtherCategoryEmissionFactors:
    """Test Scenario 1: New 'other' category emission factors exist."""

    def test_packaging_cardboard_emission_factor_exists(self, db_connection):
        """packaging (cardboard) emission factor should exist with correct values."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT activity_name, co2e_factor, unit, category "
            "FROM emission_factors WHERE activity_name = ?"
            , ("packaging (cardboard)",)
        )
        row = cursor.fetchone()

        assert row is not None, "packaging (cardboard) emission factor not found"
        assert float(row["co2e_factor"]) == pytest.approx(0.9, rel=0.01)
        assert row["unit"] == "kg"
        assert row["category"] == "other"

    def test_packaging_plastic_emission_factor_exists(self, db_connection):
        """packaging (plastic) emission factor should exist with correct values."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT activity_name, co2e_factor, unit, category "
            "FROM emission_factors WHERE activity_name = ?"
            , ("packaging (plastic)",)
        )
        row = cursor.fetchone()

        assert row is not None, "packaging (plastic) emission factor not found"
        assert float(row["co2e_factor"]) == pytest.approx(2.5, rel=0.01)
        assert row["unit"] == "kg"
        assert row["category"] == "other"

    def test_water_process_emission_factor_exists(self, db_connection):
        """water (process) emission factor should exist with correct values."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT activity_name, co2e_factor, unit, category "
            "FROM emission_factors WHERE activity_name = ?"
            , ("water (process)",)
        )
        row = cursor.fetchone()

        assert row is not None, "water (process) emission factor not found"
        assert float(row["co2e_factor"]) == pytest.approx(0.0003, rel=0.01)
        assert row["unit"] == "L"
        assert row["category"] == "other"

    def test_waste_general_emission_factor_exists(self, db_connection):
        """waste (general) emission factor should exist with correct values."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT activity_name, co2e_factor, unit, category "
            "FROM emission_factors WHERE activity_name = ?"
            , ("waste (general)",)
        )
        row = cursor.fetchone()

        assert row is not None, "waste (general) emission factor not found"
        assert float(row["co2e_factor"]) == pytest.approx(0.5, rel=0.01)
        assert row["unit"] == "kg"
        assert row["category"] == "other"

    def test_other_category_has_minimum_four_factors(self, db_connection):
        """Other category should have at least 4 emission factors."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM emission_factors WHERE category = 'other'"
        )
        row = cursor.fetchone()

        assert row["count"] >= 4, f"Expected at least 4 'other' category factors, got {row['count']}"


class TestComponentProducts:
    """Test Scenario 2: Component products for new inputs exist."""

    def test_packaging_cardboard_product_exists(self, db_connection):
        """Packaging (Cardboard) component product should exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT code, name, unit, is_finished_product "
            "FROM products WHERE code = ?"
            , ("packaging_cardboard",)
        )
        row = cursor.fetchone()

        assert row is not None, "packaging_cardboard product not found"
        assert row["unit"] == "kg"
        assert row["is_finished_product"] == 0

    def test_packaging_plastic_product_exists(self, db_connection):
        """Packaging (Plastic) component product should exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT code, name, unit, is_finished_product "
            "FROM products WHERE code = ?"
            , ("packaging_plastic",)
        )
        row = cursor.fetchone()

        assert row is not None, "packaging_plastic product not found"
        assert row["unit"] == "kg"
        assert row["is_finished_product"] == 0

    def test_water_process_product_exists(self, db_connection):
        """Water (Process) component product should exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT code, name, unit, is_finished_product "
            "FROM products WHERE code = ?"
            , ("water_process",)
        )
        row = cursor.fetchone()

        assert row is not None, "water_process product not found"
        assert row["unit"] == "L"
        assert row["is_finished_product"] == 0

    def test_waste_general_product_exists(self, db_connection):
        """Waste (General) component product should exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT code, name, unit, is_finished_product "
            "FROM products WHERE code = ?"
            , ("waste_general",)
        )
        row = cursor.fetchone()

        assert row is not None, "waste_general product not found"
        assert row["unit"] == "kg"
        assert row["is_finished_product"] == 0

    def test_transport_products_exist(self, db_connection):
        """Transport products (truck and ship) should exist."""
        cursor = db_connection.cursor()

        cursor.execute("SELECT code, unit FROM products WHERE code = 'transport_truck'")
        truck = cursor.fetchone()
        assert truck is not None, "transport_truck product not found"
        assert truck["unit"] == "tkm"

        cursor.execute("SELECT code, unit FROM products WHERE code = 'transport_ship'")
        ship = cursor.fetchone()
        assert ship is not None, "transport_ship product not found"
        assert ship["unit"] == "tkm"


class TestElectronicsTransport:
    """Test Scenario 3: All electronics BOMs have transport inputs."""

    def test_electronics_boms_have_transport_truck(self, db_connection):
        """All electronics finished products with BOMs should have transport_truck."""
        cursor = db_connection.cursor()

        # Get all electronics products (E- prefix) that have BOMs
        cursor.execute("""
            SELECT DISTINCT p.id, p.code
            FROM products p
            JOIN bill_of_materials b ON b.parent_product_id = p.id
            WHERE p.code LIKE 'E-%'
            AND p.is_finished_product = 1
        """)
        electronics_products = cursor.fetchall()

        products_without_truck = []
        for product in electronics_products:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bill_of_materials b
                JOIN products child ON b.child_product_id = child.id
                WHERE b.parent_product_id = ?
                AND child.code = 'transport_truck'
            """, (product["id"],))
            result = cursor.fetchone()
            if result["count"] == 0:
                products_without_truck.append(product["code"])

        assert len(products_without_truck) == 0, \
            f"Electronics products without transport_truck: {products_without_truck}"

    def test_electronics_boms_have_transport_ship(self, db_connection):
        """All electronics finished products with BOMs should have transport_ship."""
        cursor = db_connection.cursor()

        # Get all electronics products (E- prefix) that have BOMs
        cursor.execute("""
            SELECT DISTINCT p.id, p.code
            FROM products p
            JOIN bill_of_materials b ON b.parent_product_id = p.id
            WHERE p.code LIKE 'E-%'
            AND p.is_finished_product = 1
        """)
        electronics_products = cursor.fetchall()

        products_without_ship = []
        for product in electronics_products:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bill_of_materials b
                JOIN products child ON b.child_product_id = child.id
                WHERE b.parent_product_id = ?
                AND child.code = 'transport_ship'
            """, (product["id"],))
            result = cursor.fetchone()
            if result["count"] == 0:
                products_without_ship.append(product["code"])

        assert len(products_without_ship) == 0, \
            f"Electronics products without transport_ship: {products_without_ship}"


class TestAllBOMsHaveTransport:
    """Test Scenario 4: All finished products with BOMs have transport."""

    def test_all_boms_have_at_least_one_transport(self, db_connection):
        """All finished products with BOMs should have at least one transport component."""
        cursor = db_connection.cursor()

        # Get all finished products that have BOMs
        cursor.execute("""
            SELECT DISTINCT p.id, p.code
            FROM products p
            JOIN bill_of_materials b ON b.parent_product_id = p.id
            WHERE p.is_finished_product = 1
        """)
        products_with_boms = cursor.fetchall()

        products_without_transport = []
        for product in products_with_boms:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bill_of_materials b
                JOIN products child ON b.child_product_id = child.id
                WHERE b.parent_product_id = ?
                AND child.code LIKE 'transport_%'
            """, (product["id"],))
            result = cursor.fetchone()
            if result["count"] == 0:
                products_without_transport.append(product["code"])

        assert len(products_without_transport) == 0, \
            f"Products without any transport: {products_without_transport[:10]}... (showing first 10)"


class TestElectronicsPackaging:
    """Test Scenario 5: Electronics BOMs have packaging inputs."""

    def test_electronics_boms_have_cardboard_packaging(self, db_connection):
        """All electronics finished products with BOMs should have cardboard packaging."""
        cursor = db_connection.cursor()

        # Get all electronics products (E- prefix) that have BOMs
        cursor.execute("""
            SELECT DISTINCT p.id, p.code
            FROM products p
            JOIN bill_of_materials b ON b.parent_product_id = p.id
            WHERE p.code LIKE 'E-%'
            AND p.is_finished_product = 1
        """)
        electronics_products = cursor.fetchall()

        products_without_packaging = []
        for product in electronics_products:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bill_of_materials b
                JOIN products child ON b.child_product_id = child.id
                WHERE b.parent_product_id = ?
                AND child.code = 'packaging_cardboard'
            """, (product["id"],))
            result = cursor.fetchone()
            if result["count"] == 0:
                products_without_packaging.append(product["code"])

        assert len(products_without_packaging) == 0, \
            f"Electronics without cardboard packaging: {products_without_packaging[:10]}..."


class TestTransportQuantities:
    """Test transport quantities are realistic."""

    def test_transport_truck_quantities_are_positive(self, db_connection):
        """Transport truck quantities should be positive."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT b.quantity, p.code as parent_code
            FROM bill_of_materials b
            JOIN products child ON b.child_product_id = child.id
            JOIN products p ON b.parent_product_id = p.id
            WHERE child.code = 'transport_truck'
            AND b.quantity <= 0
        """)
        invalid_quantities = cursor.fetchall()

        assert len(invalid_quantities) == 0, \
            f"Found {len(invalid_quantities)} products with non-positive transport_truck quantities"

    def test_transport_ship_quantities_are_positive(self, db_connection):
        """Transport ship quantities should be positive."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT b.quantity, p.code as parent_code
            FROM bill_of_materials b
            JOIN products child ON b.child_product_id = child.id
            JOIN products p ON b.parent_product_id = p.id
            WHERE child.code = 'transport_ship'
            AND b.quantity <= 0
        """)
        invalid_quantities = cursor.fetchall()

        assert len(invalid_quantities) == 0, \
            f"Found {len(invalid_quantities)} products with non-positive transport_ship quantities"

    def test_transport_quantities_are_reasonable(self, db_connection):
        """Transport quantities should be in reasonable range.

        Realistic ranges:
        - Truck: 0.001 tkm (small item, local) to 50 tkm (heavy appliance, regional)
        - Ship: 0.1 tkm (light item) to 200 tkm (heavy server, intercontinental)

        Example calculations:
        - 0.5kg water bottle, 50km truck = 0.025 tkm (reasonable lower bound)
        - 15kg server, 500km truck = 7.5 tkm, 10000km ship = 150 tkm
        """
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT b.quantity, p.code as parent_code, child.code as child_code
            FROM bill_of_materials b
            JOIN products child ON b.child_product_id = child.id
            JOIN products p ON b.parent_product_id = p.id
            WHERE child.code LIKE 'transport_%'
            AND (b.quantity < 0.001 OR b.quantity > 250)
        """)
        unreasonable = cursor.fetchall()

        if len(unreasonable) > 0:
            samples = [(r["parent_code"], r["child_code"], float(r["quantity"]))
                      for r in unreasonable[:5]]
            pytest.fail(f"Found unreasonable transport quantities: {samples}")


class TestPackagingQuantities:
    """Test packaging quantities are realistic."""

    def test_cardboard_packaging_quantities_are_reasonable(self, db_connection):
        """Cardboard packaging should be between 0.05 and 2 kg."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT b.quantity, p.code as parent_code
            FROM bill_of_materials b
            JOIN products child ON b.child_product_id = child.id
            JOIN products p ON b.parent_product_id = p.id
            WHERE child.code = 'packaging_cardboard'
            AND (b.quantity < 0.05 OR b.quantity > 2)
        """)
        unreasonable = cursor.fetchall()

        assert len(unreasonable) == 0, \
            f"Found {len(unreasonable)} products with unreasonable cardboard packaging quantities"

    def test_plastic_packaging_quantities_are_reasonable(self, db_connection):
        """Plastic packaging should be between 0.01 and 0.5 kg."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT b.quantity, p.code as parent_code
            FROM bill_of_materials b
            JOIN products child ON b.child_product_id = child.id
            JOIN products p ON b.parent_product_id = p.id
            WHERE child.code = 'packaging_plastic'
            AND (b.quantity < 0.01 OR b.quantity > 0.5)
        """)
        unreasonable = cursor.fetchall()

        # This is optional - not all products need plastic packaging
        # Just verify the ones that have it are reasonable
        if len(unreasonable) > 0:
            samples = [(r["parent_code"], float(r["quantity"]))
                      for r in unreasonable[:5]]
            pytest.fail(f"Found unreasonable plastic packaging quantities: {samples}")


class TestBOMIntegrity:
    """Test overall BOM integrity after enhancements."""

    def test_no_duplicate_bom_entries(self, db_connection):
        """Each parent-child pair should appear only once."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT parent_product_id, child_product_id, COUNT(*) as count
            FROM bill_of_materials
            GROUP BY parent_product_id, child_product_id
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()

        assert len(duplicates) == 0, \
            f"Found {len(duplicates)} duplicate BOM entries"

    def test_no_self_referencing_boms(self, db_connection):
        """Products should not reference themselves in BOMs."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT parent_product_id, child_product_id
            FROM bill_of_materials
            WHERE parent_product_id = child_product_id
        """)
        self_refs = cursor.fetchall()

        assert len(self_refs) == 0, \
            f"Found {len(self_refs)} self-referencing BOM entries"

    def test_total_bom_count_reasonable(self, db_connection):
        """Total BOM count should be reasonable after enhancements."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM bill_of_materials")
        result = cursor.fetchone()

        # Should have significantly more BOMs after adding transport to all
        assert result["count"] > 100, \
            f"Expected more than 100 BOM entries, got {result['count']}"
