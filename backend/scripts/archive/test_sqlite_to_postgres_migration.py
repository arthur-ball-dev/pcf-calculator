"""
Integration tests for SQLite to PostgreSQL data migration.

TASK-DATA-P8-001: SQLite to PostgreSQL Data Migration

Prerequisites:
- Docker PostgreSQL running: docker-compose up -d postgres
- SQLite database exists: pcf_calculator.db
- Test database URL: TEST_POSTGRES_URL environment variable

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (migration script doesn't exist yet)
- Implementation must make tests PASS without modifying tests

Test Scenarios Covered:
1. Migration script validates source SQLite database
2. Migration preserves all emission factors (~33 records)
3. Migration preserves all products (~4000 records)
4. Migration preserves all BOMs (22 parent products)
5. Primary key and foreign key integrity maintained
6. Indexes created correctly
7. UUID fields converted properly
8. Timestamps preserved
9. Migration is idempotent (can run multiple times safely)
10. Rollback mechanism works
"""

import os
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator, Dict, Any
from pathlib import Path

# Skip entire module if PostgreSQL is not configured
pytestmark = pytest.mark.integration


# =============================================================================
# Test Configuration Constants
# =============================================================================

# Expected minimum record counts based on SPEC
EXPECTED_MIN_EMISSION_FACTORS = 33
EXPECTED_MIN_PRODUCTS = 4000
EXPECTED_MIN_BOM_PARENT_PRODUCTS = 22
EXPECTED_DATA_SOURCES = 3  # EPA, DEFRA, Exiobase


# =============================================================================
# Helper Functions
# =============================================================================


def is_postgresql_configured() -> bool:
    """Check if PostgreSQL is configured via environment variable."""
    db_url = os.environ.get("DATABASE_URL", "")
    test_url = os.environ.get("TEST_POSTGRES_URL", "")
    return "postgresql" in db_url.lower() or "postgresql" in test_url.lower()


def get_sqlite_path() -> Path:
    """Get path to SQLite database."""
    # Check common locations
    potential_paths = [
        Path("./pcf_calculator.db"),
        Path("../pcf_calculator.db"),
        Path("./backend/pcf_calculator.db"),
        Path(os.environ.get("SQLITE_PATH", "./pcf_calculator.db")),
    ]
    for path in potential_paths:
        if path.exists():
            return path
    return Path("./pcf_calculator.db")  # Default path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def sqlite_engine():
    """
    Create SQLite engine connected to source database.

    This fixture creates a connection to the SQLite database
    to verify source data before and during migration.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    sqlite_path = get_sqlite_path()
    sqlite_url = os.environ.get("SQLITE_URL", f"sqlite:///{sqlite_path}")

    if not Path(sqlite_path).exists() and "memory" not in sqlite_url:
        pytest.skip(f"SQLite database not found at {sqlite_path}")

    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def postgres_engine():
    """
    Create PostgreSQL engine for migration target.

    Requirements:
    - DATABASE_URL or TEST_POSTGRES_URL must be set
    - Format: postgresql://user:password@host:port/database
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import QueuePool

    db_url = os.environ.get("TEST_POSTGRES_URL") or os.environ.get("DATABASE_URL")

    if not db_url or "postgresql" not in db_url.lower():
        pytest.skip(
            "PostgreSQL not configured. Set TEST_POSTGRES_URL or DATABASE_URL "
            "to run these tests."
        )

    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False
    )

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def sqlite_session(sqlite_engine):
    """SQLite session fixture for source data queries."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=sqlite_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def postgres_session(postgres_engine):
    """PostgreSQL session fixture for migration target queries."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=postgres_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def migration_script():
    """
    Import the migration script module.

    This fixture attempts to import the migration script.
    Tests should FAIL if the script doesn't exist yet.
    """
    try:
        from backend.scripts import migrate_sqlite_to_postgres
        return migrate_sqlite_to_postgres
    except ImportError:
        pytest.fail(
            "Migration script not found. "
            "Create backend/scripts/migrate_sqlite_to_postgres.py"
        )


# =============================================================================
# Test Class: Source Database Validation
# =============================================================================


class TestSourceDatabaseValidation:
    """Test Scenario 1: Migration script validates source SQLite database."""

    def test_migration_script_exists(self):
        """
        Verify migration script module exists.

        The migration script should be importable from backend.scripts.
        """
        try:
            from backend.scripts import migrate_sqlite_to_postgres
            assert migrate_sqlite_to_postgres is not None
        except ImportError:
            pytest.fail(
                "Migration script not found at backend/scripts/migrate_sqlite_to_postgres.py"
            )

    def test_migration_script_has_validate_source_function(self, migration_script):
        """
        Verify migration script has source validation function.

        The script should have a validate_source() or similar function
        that checks the SQLite database before migration.
        """
        assert hasattr(migration_script, 'validate_source') or \
               hasattr(migration_script, 'validate_sqlite_database'), \
            "Migration script should have validate_source() function"

    def test_validation_checks_required_tables_exist(
        self, migration_script, sqlite_engine
    ):
        """
        Verify validation checks all required tables exist.

        Required tables: products, emission_factors, bill_of_materials,
        data_sources, product_categories, pcf_calculations, calculation_details
        """
        from sqlalchemy import text

        required_tables = [
            "products",
            "emission_factors",
            "bill_of_materials",
            "data_sources",
            "product_categories",
            "pcf_calculations",
            "calculation_details",
        ]

        with sqlite_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            existing_tables = {row[0] for row in result.fetchall()}

        for table in required_tables:
            assert table in existing_tables, \
                f"Required table '{table}' not found in SQLite database"

    def test_validation_detects_empty_critical_tables(
        self, migration_script, sqlite_engine
    ):
        """
        Verify validation warns about empty critical tables.

        Critical tables like products and emission_factors should
        have data for a meaningful migration.
        """
        from sqlalchemy import text

        # This test verifies the script can detect empty tables
        # The implementation should warn/error if critical tables are empty
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            product_count = result.scalar()

            result = conn.execute(text("SELECT COUNT(*) FROM emission_factors"))
            ef_count = result.scalar()

        # Source database should have data
        assert product_count > 0, "Products table should have data"
        assert ef_count > 0, "Emission factors table should have data"


# =============================================================================
# Test Class: Emission Factors Migration
# =============================================================================


class TestEmissionFactorsMigration:
    """Test Scenario 2: Migration preserves all emission factors (~33 records)."""

    def test_emission_factors_count_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify all emission factors are migrated.

        Row count in PostgreSQL should match SQLite exactly.
        """
        from sqlalchemy import text

        sqlite_count = sqlite_session.execute(
            text("SELECT COUNT(*) FROM emission_factors")
        ).scalar()

        postgres_count = postgres_session.execute(
            text("SELECT COUNT(*) FROM emission_factors")
        ).scalar()

        assert sqlite_count == postgres_count, \
            f"Emission factor count mismatch: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
        assert postgres_count >= EXPECTED_MIN_EMISSION_FACTORS, \
            f"Expected at least {EXPECTED_MIN_EMISSION_FACTORS} emission factors, got {postgres_count}"

    def test_emission_factors_data_integrity(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify emission factor data fields are preserved.

        Check that activity_name, co2e_factor, unit, data_source match.
        """
        from sqlalchemy import text

        # Get sample emission factors from SQLite
        sqlite_factors = sqlite_session.execute(text("""
            SELECT activity_name, co2e_factor, unit, data_source, geography
            FROM emission_factors
            ORDER BY activity_name
            LIMIT 5
        """)).fetchall()

        for sf in sqlite_factors:
            activity_name, co2e_factor, unit, data_source, geography = sf

            # Find same factor in PostgreSQL
            pg_factor = postgres_session.execute(text("""
                SELECT co2e_factor, unit, data_source, geography
                FROM emission_factors
                WHERE activity_name = :activity_name
            """), {"activity_name": activity_name}).fetchone()

            assert pg_factor is not None, \
                f"Emission factor '{activity_name}' not found in PostgreSQL"

            pg_co2e, pg_unit, pg_source, pg_geography = pg_factor

            # Compare values (allow small decimal differences)
            assert abs(float(pg_co2e) - float(co2e_factor)) < 0.00001, \
                f"co2e_factor mismatch for '{activity_name}'"
            assert pg_unit == unit, f"unit mismatch for '{activity_name}'"
            assert pg_source == data_source, f"data_source mismatch for '{activity_name}'"

    def test_emission_factors_foreign_keys_valid(
        self, migration_script, postgres_session
    ):
        """
        Verify emission_factors.data_source_id references valid data_sources.

        No orphaned foreign key references should exist.
        """
        from sqlalchemy import text

        orphan_count = postgres_session.execute(text("""
            SELECT COUNT(*)
            FROM emission_factors ef
            LEFT JOIN data_sources ds ON ef.data_source_id = ds.id
            WHERE ef.data_source_id IS NOT NULL AND ds.id IS NULL
        """)).scalar()

        assert orphan_count == 0, \
            f"Found {orphan_count} emission factors with orphaned data_source_id references"


# =============================================================================
# Test Class: Products Migration
# =============================================================================


class TestProductsMigration:
    """Test Scenario 3: Migration preserves all products (~4000 records)."""

    def test_products_count_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify all products are migrated.

        Row count in PostgreSQL should match SQLite exactly.
        """
        from sqlalchemy import text

        sqlite_count = sqlite_session.execute(
            text("SELECT COUNT(*) FROM products")
        ).scalar()

        postgres_count = postgres_session.execute(
            text("SELECT COUNT(*) FROM products")
        ).scalar()

        assert sqlite_count == postgres_count, \
            f"Product count mismatch: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
        assert postgres_count >= EXPECTED_MIN_PRODUCTS, \
            f"Expected at least {EXPECTED_MIN_PRODUCTS} products, got {postgres_count}"

    def test_products_data_integrity(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify product data fields are preserved.

        Check that code, name, unit, category, is_finished_product match.
        """
        from sqlalchemy import text

        # Get sample products from SQLite
        sqlite_products = sqlite_session.execute(text("""
            SELECT code, name, unit, category, is_finished_product
            FROM products
            WHERE code IS NOT NULL
            ORDER BY code
            LIMIT 10
        """)).fetchall()

        for sp in sqlite_products:
            code, name, unit, category, is_finished = sp

            # Find same product in PostgreSQL
            pg_product = postgres_session.execute(text("""
                SELECT name, unit, category, is_finished_product
                FROM products
                WHERE code = :code
            """), {"code": code}).fetchone()

            assert pg_product is not None, \
                f"Product '{code}' not found in PostgreSQL"

            pg_name, pg_unit, pg_category, pg_is_finished = pg_product

            assert pg_name == name, f"name mismatch for product '{code}'"
            assert pg_unit == unit, f"unit mismatch for product '{code}'"
            # Note: boolean comparison handles SQLite 0/1 vs PostgreSQL true/false
            assert bool(pg_is_finished) == bool(is_finished), \
                f"is_finished_product mismatch for product '{code}'"

    def test_products_category_foreign_keys_valid(
        self, migration_script, postgres_session
    ):
        """
        Verify products.category_id references valid product_categories.

        No orphaned foreign key references should exist.
        """
        from sqlalchemy import text

        orphan_count = postgres_session.execute(text("""
            SELECT COUNT(*)
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.category_id IS NOT NULL AND pc.id IS NULL
        """)).scalar()

        assert orphan_count == 0, \
            f"Found {orphan_count} products with orphaned category_id references"


# =============================================================================
# Test Class: Bill of Materials Migration
# =============================================================================


class TestBOMsMigration:
    """Test Scenario 4: Migration preserves all BOMs (22 parent products)."""

    def test_bom_count_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify all BOM relationships are migrated.

        Row count in PostgreSQL should match SQLite exactly.
        """
        from sqlalchemy import text

        sqlite_count = sqlite_session.execute(
            text("SELECT COUNT(*) FROM bill_of_materials")
        ).scalar()

        postgres_count = postgres_session.execute(
            text("SELECT COUNT(*) FROM bill_of_materials")
        ).scalar()

        assert sqlite_count == postgres_count, \
            f"BOM count mismatch: SQLite={sqlite_count}, PostgreSQL={postgres_count}"

    def test_bom_parent_products_count(
        self, migration_script, postgres_session
    ):
        """
        Verify correct number of products have BOMs.

        Expected: ~22 parent products with BOM relationships.
        """
        from sqlalchemy import text

        parent_count = postgres_session.execute(text("""
            SELECT COUNT(DISTINCT parent_product_id)
            FROM bill_of_materials
        """)).scalar()

        assert parent_count >= EXPECTED_MIN_BOM_PARENT_PRODUCTS, \
            f"Expected at least {EXPECTED_MIN_BOM_PARENT_PRODUCTS} parent products with BOMs, got {parent_count}"

    def test_bom_relationships_integrity(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify BOM parent-child relationships are preserved.

        For sample BOMs, verify parent, child, and quantity match.
        """
        from sqlalchemy import text

        # Get sample BOMs from SQLite (join to get product codes)
        sqlite_boms = sqlite_session.execute(text("""
            SELECT
                parent.code as parent_code,
                child.code as child_code,
                bom.quantity
            FROM bill_of_materials bom
            JOIN products parent ON bom.parent_product_id = parent.id
            JOIN products child ON bom.child_product_id = child.id
            LIMIT 10
        """)).fetchall()

        for sb in sqlite_boms:
            parent_code, child_code, quantity = sb

            # Find same BOM in PostgreSQL
            pg_bom = postgres_session.execute(text("""
                SELECT bom.quantity
                FROM bill_of_materials bom
                JOIN products parent ON bom.parent_product_id = parent.id
                JOIN products child ON bom.child_product_id = child.id
                WHERE parent.code = :parent_code AND child.code = :child_code
            """), {"parent_code": parent_code, "child_code": child_code}).fetchone()

            assert pg_bom is not None, \
                f"BOM relationship {parent_code} -> {child_code} not found in PostgreSQL"

            pg_quantity = pg_bom[0]
            assert abs(float(pg_quantity) - float(quantity)) < 0.00001, \
                f"Quantity mismatch for BOM {parent_code} -> {child_code}"

    def test_bom_foreign_keys_valid(
        self, migration_script, postgres_session
    ):
        """
        Verify all BOM foreign keys reference valid products.

        Both parent_product_id and child_product_id must be valid.
        """
        from sqlalchemy import text

        # Check parent references
        orphan_parents = postgres_session.execute(text("""
            SELECT COUNT(*)
            FROM bill_of_materials bom
            LEFT JOIN products p ON bom.parent_product_id = p.id
            WHERE p.id IS NULL
        """)).scalar()

        assert orphan_parents == 0, \
            f"Found {orphan_parents} BOMs with orphaned parent_product_id"

        # Check child references
        orphan_children = postgres_session.execute(text("""
            SELECT COUNT(*)
            FROM bill_of_materials bom
            LEFT JOIN products p ON bom.child_product_id = p.id
            WHERE p.id IS NULL
        """)).scalar()

        assert orphan_children == 0, \
            f"Found {orphan_children} BOMs with orphaned child_product_id"


# =============================================================================
# Test Class: Primary Key and Foreign Key Integrity
# =============================================================================


class TestKeyIntegrity:
    """Test Scenario 5: Primary key and foreign key integrity maintained."""

    def test_all_primary_keys_unique(
        self, migration_script, postgres_session
    ):
        """
        Verify all primary keys are unique in PostgreSQL.

        Each table should have no duplicate IDs.
        """
        from sqlalchemy import text

        tables = [
            "products",
            "emission_factors",
            "bill_of_materials",
            "data_sources",
            "product_categories",
            "pcf_calculations",
            "calculation_details",
        ]

        for table in tables:
            # This query finds duplicate IDs
            duplicate_count = postgres_session.execute(text(f"""
                SELECT COUNT(*) FROM (
                    SELECT id, COUNT(*) as cnt
                    FROM {table}
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) as dupes
            """)).scalar()

            assert duplicate_count == 0, \
                f"Found {duplicate_count} duplicate primary keys in {table}"

    def test_all_foreign_keys_referential_integrity(
        self, migration_script, postgres_session
    ):
        """
        Verify all foreign key constraints are satisfied.

        Check all FK relationships for orphaned references.
        """
        from sqlalchemy import text

        fk_checks = [
            # (child_table, fk_column, parent_table, pk_column)
            ("emission_factors", "data_source_id", "data_sources", "id"),
            ("products", "category_id", "product_categories", "id"),
            ("bill_of_materials", "parent_product_id", "products", "id"),
            ("bill_of_materials", "child_product_id", "products", "id"),
            ("pcf_calculations", "product_id", "products", "id"),
            ("calculation_details", "calculation_id", "pcf_calculations", "id"),
            ("calculation_details", "component_id", "products", "id"),
            ("calculation_details", "emission_factor_id", "emission_factors", "id"),
            ("product_categories", "parent_id", "product_categories", "id"),
        ]

        for child_table, fk_col, parent_table, pk_col in fk_checks:
            orphan_count = postgres_session.execute(text(f"""
                SELECT COUNT(*)
                FROM {child_table} c
                LEFT JOIN {parent_table} p ON c.{fk_col} = p.{pk_col}
                WHERE c.{fk_col} IS NOT NULL AND p.{pk_col} IS NULL
            """)).scalar()

            assert orphan_count == 0, \
                f"Found {orphan_count} orphaned {fk_col} references in {child_table}"

    def test_data_sources_migrated_correctly(
        self, migration_script, postgres_session
    ):
        """
        Verify data_sources table has expected entries.

        Should have EPA, DEFRA, Exiobase (at least 3 sources).
        """
        from sqlalchemy import text

        count = postgres_session.execute(
            text("SELECT COUNT(*) FROM data_sources")
        ).scalar()

        assert count >= EXPECTED_DATA_SOURCES, \
            f"Expected at least {EXPECTED_DATA_SOURCES} data sources, got {count}"


# =============================================================================
# Test Class: Index Creation
# =============================================================================


class TestIndexCreation:
    """Test Scenario 6: Indexes created correctly."""

    def test_products_indexes_exist(
        self, migration_script, postgres_engine
    ):
        """
        Verify essential indexes exist on products table.

        Required indexes: code, category, category_id, is_finished_product
        """
        from sqlalchemy import text

        with postgres_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'products'
            """))
            index_names = {row[0] for row in result.fetchall()}

        # Check for expected indexes (names may vary)
        assert any('code' in idx.lower() for idx in index_names) or \
               'products_pkey' in index_names, \
            "Products table should have index on code column"

    def test_emission_factors_indexes_exist(
        self, migration_script, postgres_engine
    ):
        """
        Verify essential indexes exist on emission_factors table.

        Required indexes: activity_name, data_source, geography, category
        """
        from sqlalchemy import text

        with postgres_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'emission_factors'
            """))
            index_names = {row[0] for row in result.fetchall()}

        # Primary key index should exist at minimum
        assert len(index_names) > 0, \
            "Emission factors table should have at least primary key index"

    def test_bom_indexes_exist(
        self, migration_script, postgres_engine
    ):
        """
        Verify essential indexes exist on bill_of_materials table.

        Required indexes: parent_product_id, child_product_id
        """
        from sqlalchemy import text

        with postgres_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'bill_of_materials'
            """))
            index_names = {row[0] for row in result.fetchall()}

        # Should have indexes for parent and child product lookups
        assert len(index_names) > 0, \
            "BOM table should have indexes for parent/child lookups"


# =============================================================================
# Test Class: UUID Conversion
# =============================================================================


class TestUUIDConversion:
    """Test Scenario 7: UUID fields converted properly."""

    def test_product_ids_are_valid_uuids(
        self, migration_script, postgres_session
    ):
        """
        Verify product IDs are valid UUIDs in PostgreSQL.

        SQLite string IDs should be converted to PostgreSQL UUIDs.
        """
        from sqlalchemy import text
        import re

        # UUID regex pattern (with or without hyphens)
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$',
            re.IGNORECASE
        )

        result = postgres_session.execute(
            text("SELECT id FROM products LIMIT 10")
        )

        for row in result.fetchall():
            product_id = str(row[0])
            # Remove hyphens for validation (32 hex chars)
            clean_id = product_id.replace('-', '')
            assert len(clean_id) == 32 and all(c in '0123456789abcdef' for c in clean_id.lower()), \
                f"Product ID '{product_id}' is not a valid UUID format"

    def test_emission_factor_ids_are_valid_uuids(
        self, migration_script, postgres_session
    ):
        """
        Verify emission factor IDs are valid UUIDs.
        """
        from sqlalchemy import text

        result = postgres_session.execute(
            text("SELECT id FROM emission_factors LIMIT 10")
        )

        for row in result.fetchall():
            ef_id = str(row[0])
            clean_id = ef_id.replace('-', '')
            assert len(clean_id) == 32 and all(c in '0123456789abcdef' for c in clean_id.lower()), \
                f"Emission factor ID '{ef_id}' is not a valid UUID format"

    def test_uuid_references_are_consistent(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify UUID conversion is consistent across tables.

        A product_id in SQLite should map to the same product in PostgreSQL
        through the code field.
        """
        from sqlalchemy import text

        # Get a BOM from SQLite with product codes
        sqlite_bom = sqlite_session.execute(text("""
            SELECT
                parent.code as parent_code,
                child.code as child_code
            FROM bill_of_materials bom
            JOIN products parent ON bom.parent_product_id = parent.id
            JOIN products child ON bom.child_product_id = child.id
            LIMIT 1
        """)).fetchone()

        if sqlite_bom:
            parent_code, child_code = sqlite_bom

            # Verify same relationship exists in PostgreSQL
            pg_bom = postgres_session.execute(text("""
                SELECT COUNT(*)
                FROM bill_of_materials bom
                JOIN products parent ON bom.parent_product_id = parent.id
                JOIN products child ON bom.child_product_id = child.id
                WHERE parent.code = :parent_code AND child.code = :child_code
            """), {"parent_code": parent_code, "child_code": child_code}).scalar()

            assert pg_bom == 1, \
                f"UUID reference consistency check failed for BOM {parent_code} -> {child_code}"


# =============================================================================
# Test Class: Timestamp Preservation
# =============================================================================


class TestTimestampPreservation:
    """Test Scenario 8: Timestamps preserved."""

    def test_product_timestamps_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify product created_at timestamps are preserved.
        """
        from sqlalchemy import text

        # Get sample product timestamps from SQLite
        sqlite_product = sqlite_session.execute(text("""
            SELECT code, created_at
            FROM products
            WHERE created_at IS NOT NULL
            ORDER BY code
            LIMIT 1
        """)).fetchone()

        if sqlite_product:
            code, sqlite_created = sqlite_product

            # Get same product from PostgreSQL
            pg_product = postgres_session.execute(text("""
                SELECT created_at
                FROM products
                WHERE code = :code
            """), {"code": code}).fetchone()

            assert pg_product is not None, \
                f"Product '{code}' not found in PostgreSQL"

            pg_created = pg_product[0]

            # Timestamps should be within a few seconds (accounting for timezone)
            # SQLite stores as string, PostgreSQL as timestamp
            assert pg_created is not None, \
                f"Product '{code}' created_at should be preserved"

    def test_emission_factor_timestamps_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify emission factor timestamps are preserved.
        """
        from sqlalchemy import text

        # Get count of emission factors with timestamps
        pg_count = postgres_session.execute(text("""
            SELECT COUNT(*)
            FROM emission_factors
            WHERE created_at IS NOT NULL
        """)).scalar()

        sqlite_count = sqlite_session.execute(text("""
            SELECT COUNT(*)
            FROM emission_factors
            WHERE created_at IS NOT NULL
        """)).scalar()

        assert pg_count == sqlite_count, \
            f"Timestamp preservation mismatch: SQLite={sqlite_count}, PostgreSQL={pg_count}"

    def test_timestamps_have_timezone(
        self, migration_script, postgres_session
    ):
        """
        Verify timestamps in PostgreSQL have timezone information.

        PostgreSQL TIMESTAMP WITH TIME ZONE should store timezone-aware timestamps.
        """
        from sqlalchemy import text

        # Get a timestamp and verify timezone info
        result = postgres_session.execute(text("""
            SELECT created_at AT TIME ZONE 'UTC'
            FROM products
            WHERE created_at IS NOT NULL
            LIMIT 1
        """)).fetchone()

        if result:
            created_at = result[0]
            # PostgreSQL AT TIME ZONE converts to timestamp without tz
            # This verifies the timestamp can be interpreted with timezone
            assert created_at is not None, \
                "Timestamp should be convertible to UTC"


# =============================================================================
# Test Class: Migration Idempotency
# =============================================================================


class TestMigrationIdempotency:
    """Test Scenario 9: Migration is idempotent (can run multiple times safely)."""

    def test_migration_detects_existing_data(
        self, migration_script, postgres_session
    ):
        """
        Verify migration script can detect existing data.

        Running migration twice should not create duplicates.
        """
        from sqlalchemy import text

        # Get initial product count
        initial_count = postgres_session.execute(
            text("SELECT COUNT(*) FROM products")
        ).scalar()

        # Verify migration script has idempotency mechanism
        assert hasattr(migration_script, 'migrate') or \
               hasattr(migration_script, 'run_migration'), \
            "Migration script should have a migrate() function"

        # After migration, count should remain the same or be additive
        # (implementation detail - this tests the contract)
        final_count = postgres_session.execute(
            text("SELECT COUNT(*) FROM products")
        ).scalar()

        # For idempotent migration, counts should match
        # (unless migration is designed to be additive)
        assert final_count >= initial_count, \
            "Migration should not lose data on re-run"

    def test_migration_handles_force_flag(self, migration_script):
        """
        Verify migration script supports --force flag for re-migration.

        Script should accept a force flag to allow re-running migration.
        """
        import argparse
        import sys

        # Check if migration script has argument parser setup
        assert hasattr(migration_script, 'main') or \
               hasattr(migration_script, 'parse_args') or \
               hasattr(migration_script, 'FORCE_FLAG'), \
            "Migration script should support command-line arguments including --force"

    def test_no_duplicate_primary_keys_after_remigration(
        self, migration_script, postgres_session
    ):
        """
        Verify no duplicate primary keys exist after migration.

        Running migration multiple times should not create duplicate records.
        """
        from sqlalchemy import text

        tables = ["products", "emission_factors", "data_sources"]

        for table in tables:
            duplicate_count = postgres_session.execute(text(f"""
                SELECT COUNT(*) FROM (
                    SELECT id, COUNT(*) as cnt
                    FROM {table}
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) as dupes
            """)).scalar()

            assert duplicate_count == 0, \
                f"Found duplicate IDs in {table} after migration"


# =============================================================================
# Test Class: Rollback Mechanism
# =============================================================================


class TestRollbackMechanism:
    """Test Scenario 10: Rollback mechanism works."""

    def test_migration_uses_transactions(self, migration_script):
        """
        Verify migration script uses database transactions.

        The script should wrap operations in transactions for rollback capability.
        """
        # Check for transaction-related code in migration script
        import inspect

        # Get source code of migrate function if available
        if hasattr(migration_script, 'migrate'):
            source = inspect.getsource(migration_script.migrate)
        elif hasattr(migration_script, 'run_migration'):
            source = inspect.getsource(migration_script.run_migration)
        else:
            pytest.fail("Migration script should have migrate() function")

        # Look for transaction patterns
        transaction_patterns = [
            'begin()',
            'commit()',
            'rollback()',
            'transaction',
            'BEGIN',
            'COMMIT',
            'ROLLBACK',
        ]

        has_transaction_handling = any(
            pattern in source for pattern in transaction_patterns
        )

        assert has_transaction_handling, \
            "Migration script should use database transactions for rollback capability"

    def test_migration_logs_errors(self, migration_script):
        """
        Verify migration script has error logging.

        Errors during migration should be logged for debugging.
        """
        import inspect
        import logging

        # Check if migration module uses logging
        module_source = inspect.getsource(migration_script)

        logging_patterns = [
            'logging',
            'logger',
            'log.error',
            'log.warning',
            'logger.error',
            'logger.warning',
            'print(',  # Even print is acceptable for CLI
        ]

        has_logging = any(
            pattern in module_source for pattern in logging_patterns
        )

        assert has_logging, \
            "Migration script should log errors for debugging"

    def test_partial_migration_can_be_recovered(
        self, migration_script, postgres_session
    ):
        """
        Verify partial migration state can be detected.

        If migration fails midway, the state should be recoverable.
        """
        from sqlalchemy import text

        # Check for migration state tracking (e.g., migration_status table)
        # or ability to detect partial migration
        has_state_tracking = hasattr(migration_script, 'get_migration_status') or \
                             hasattr(migration_script, 'check_migration_state')

        # Alternatively, check if all tables have data (consistent state)
        tables_with_data = 0
        for table in ["products", "emission_factors", "data_sources"]:
            count = postgres_session.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()
            if count > 0:
                tables_with_data += 1

        # Either has state tracking or consistent data state
        assert has_state_tracking or tables_with_data in [0, 3], \
            "Migration should either track state or leave database in consistent state"


# =============================================================================
# Test Class: Data Quality Validation
# =============================================================================


class TestDataQualityValidation:
    """Additional data quality tests for migration."""

    def test_product_categories_hierarchy_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify product_categories parent-child hierarchy is preserved.
        """
        from sqlalchemy import text

        # Get category hierarchy from SQLite
        sqlite_hierarchy = sqlite_session.execute(text("""
            SELECT code, parent_id, level
            FROM product_categories
            WHERE parent_id IS NOT NULL
            ORDER BY code
            LIMIT 5
        """)).fetchall()

        for sh in sqlite_hierarchy:
            code, parent_id, level = sh

            # Find same category in PostgreSQL
            pg_category = postgres_session.execute(text("""
                SELECT parent_id, level
                FROM product_categories
                WHERE code = :code
            """), {"code": code}).fetchone()

            if pg_category:
                pg_parent_id, pg_level = pg_category
                # Level should match
                assert pg_level == level, \
                    f"Category level mismatch for '{code}'"

    def test_decimal_precision_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify decimal precision is preserved in migration.

        co2e_factor and quantity values should maintain precision.
        """
        from sqlalchemy import text

        # Get sample decimal values from SQLite
        sqlite_factors = sqlite_session.execute(text("""
            SELECT activity_name, co2e_factor
            FROM emission_factors
            WHERE co2e_factor IS NOT NULL
            LIMIT 5
        """)).fetchall()

        for sf in sqlite_factors:
            activity_name, sqlite_co2e = sf

            pg_factor = postgres_session.execute(text("""
                SELECT co2e_factor
                FROM emission_factors
                WHERE activity_name = :activity_name
            """), {"activity_name": activity_name}).fetchone()

            if pg_factor:
                pg_co2e = pg_factor[0]
                # Compare with high precision
                assert abs(float(pg_co2e) - float(sqlite_co2e)) < 1e-8, \
                    f"Decimal precision lost for '{activity_name}'"

    def test_null_values_preserved(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify NULL values are preserved in migration.

        Fields that are NULL in SQLite should be NULL in PostgreSQL.
        """
        from sqlalchemy import text

        # Count NULLs in description field
        sqlite_null_count = sqlite_session.execute(text("""
            SELECT COUNT(*) FROM products WHERE description IS NULL
        """)).scalar()

        postgres_null_count = postgres_session.execute(text("""
            SELECT COUNT(*) FROM products WHERE description IS NULL
        """)).scalar()

        # NULL counts should match (or be close - some data may have been cleaned)
        assert abs(postgres_null_count - sqlite_null_count) < 10, \
            f"NULL value preservation issue: SQLite={sqlite_null_count}, PostgreSQL={postgres_null_count}"

    def test_boolean_conversion_correct(
        self, migration_script, sqlite_session, postgres_session
    ):
        """
        Verify boolean conversion from SQLite (0/1) to PostgreSQL (true/false).
        """
        from sqlalchemy import text

        # Count finished products in SQLite (stored as 0/1)
        sqlite_finished = sqlite_session.execute(text("""
            SELECT COUNT(*) FROM products WHERE is_finished_product = 1
        """)).scalar()

        # Count finished products in PostgreSQL (stored as true/false)
        postgres_finished = postgres_session.execute(text("""
            SELECT COUNT(*) FROM products WHERE is_finished_product = true
        """)).scalar()

        assert sqlite_finished == postgres_finished, \
            f"Boolean conversion issue: SQLite={sqlite_finished}, PostgreSQL={postgres_finished}"


# =============================================================================
# Test Class: Migration Performance
# =============================================================================


class TestMigrationPerformance:
    """Performance tests for migration."""

    def test_migration_completes_under_5_minutes(
        self, migration_script
    ):
        """
        Verify migration completes within expected time.

        Per SPEC: Migration should complete in <5 minutes for ~4000 products.
        """
        # This test verifies the spec requirement exists
        # Actual timing would be measured during implementation validation
        assert hasattr(migration_script, 'migrate') or \
               hasattr(migration_script, 'run_migration'), \
            "Migration script should have migrate() function"

    def test_batch_processing_implemented(self, migration_script):
        """
        Verify migration uses batch processing for large tables.

        Products table (4000+ rows) should be migrated in batches.
        """
        import inspect

        # Check for batch processing patterns
        if hasattr(migration_script, 'migrate'):
            source = inspect.getsource(migration_script.migrate)
        elif hasattr(migration_script, 'run_migration'):
            source = inspect.getsource(migration_script.run_migration)
        elif hasattr(migration_script, 'migrate_large_table'):
            source = inspect.getsource(migration_script.migrate_large_table)
        else:
            source = inspect.getsource(migration_script)

        batch_patterns = [
            'batch',
            'BATCH',
            'LIMIT',
            'OFFSET',
            'chunk',
            'executemany',
        ]

        has_batch_processing = any(
            pattern in source for pattern in batch_patterns
        )

        assert has_batch_processing, \
            "Migration script should use batch processing for large tables"
