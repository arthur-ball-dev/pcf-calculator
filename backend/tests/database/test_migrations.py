"""
Test module for Alembic database migrations
Tests migration up/down, idempotency, and version tracking

TASK: TASK-DB-004
Following TDD methodology - tests written FIRST before implementation

Ported from temporary SQLite files to throwaway PostgreSQL databases
(alembic/env.py only accepts PostgreSQL URLs).
"""

import pytest
import os
import uuid
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test"
)


@pytest.fixture
def migration_db_url():
    """Create an empty throwaway PostgreSQL database for one test, then drop it"""
    db_name = f"pcf_migration_test_{uuid.uuid4().hex[:12]}"
    admin_engine = create_engine(
        make_url(TEST_DATABASE_URL).set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))

    yield make_url(TEST_DATABASE_URL).set(database=db_name).render_as_string(hide_password=False)

    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    admin_engine.dispose()


@pytest.fixture
def alembic_config(migration_db_url, monkeypatch):
    """
    Create Alembic configuration pointing to temporary database

    This fixture assumes Alembic is initialized in backend/alembic/
    """
    backend_dir = Path(__file__).parent.parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"

    # Create Alembic config
    config = Config(str(alembic_ini_path))

    # Override database URL to use temp database. env.py prefers DATABASE_URL from
    # the environment, so pin it too; otherwise migrations hit the developer's DB.
    monkeypatch.setenv("DATABASE_URL", migration_db_url)
    config.set_main_option("sqlalchemy.url", migration_db_url)

    return config


@pytest.fixture
def db_engine(migration_db_url):
    """Create SQLAlchemy engine for the temporary database"""
    engine = create_engine(migration_db_url, echo=False)
    yield engine
    engine.dispose()


def get_table_names(engine) -> list:
    """Get list of all tables in database"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_view_names(engine) -> list:
    """Get list of all views in database"""
    inspector = inspect(engine)
    return inspector.get_view_names()


def get_current_revision(engine) -> str:
    """Get current Alembic revision from database"""
    with engine.begin() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_head_revision(alembic_config) -> str:
    """Get head revision from Alembic scripts"""
    script_dir = ScriptDirectory.from_config(alembic_config)
    return script_dir.get_current_head()


class TestMigrationUp:
    """Test Scenario 1: Happy Path - Migration Up"""

    def test_initial_migration_creates_all_tables(self, alembic_config, db_engine):
        """
        Test that running 'alembic upgrade head' creates all 5 tables

        Expected tables:
        - products
        - emission_factors
        - bill_of_materials
        - pcf_calculations
        - calculation_details
        """
        # Run migration to head
        command.upgrade(alembic_config, "head")

        # Get all tables
        tables = get_table_names(db_engine)

        # Verify all 5 core tables exist
        assert "products" in tables, "products table should be created"
        assert "emission_factors" in tables, "emission_factors table should be created"
        assert "bill_of_materials" in tables, "bill_of_materials table should be created"
        assert "pcf_calculations" in tables, "pcf_calculations table should be created"
        assert "calculation_details" in tables, "calculation_details table should be created"

        # Verify alembic_version table exists
        assert "alembic_version" in tables, "alembic_version table should be created"

    def test_migration_creates_view(self, alembic_config, db_engine):
        """
        Test that migration creates v_bom_explosion view
        """
        # Run migration to head
        command.upgrade(alembic_config, "head")

        # Get all views
        views = get_view_names(db_engine)

        # Verify BOM explosion view exists
        assert "v_bom_explosion" in views, "v_bom_explosion view should be created"

    def test_migration_creates_indexes(self, alembic_config, db_engine):
        """
        Test that migration creates required indexes
        """
        # Run migration to head
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Check products table indexes
        products_indexes = inspector.get_indexes("products")
        index_names = [idx['name'] for idx in products_indexes]

        assert "idx_products_code" in index_names, "products.code index should exist"
        assert "idx_products_category" in index_names, "products.category index should exist"
        assert "idx_products_finished" in index_names, "products.is_finished_product index should exist"

        # Check emission_factors indexes
        ef_indexes = inspector.get_indexes("emission_factors")
        ef_index_names = [idx['name'] for idx in ef_indexes]

        assert "idx_ef_activity" in ef_index_names, "emission_factors.activity_name index should exist"
        assert "idx_ef_geography" in ef_index_names, "emission_factors.geography index should exist"
        assert "idx_ef_source" in ef_index_names, "emission_factors.data_source index should exist"

    def test_migration_tracks_version(self, alembic_config, db_engine):
        """
        Test that alembic_version table tracks the current migration
        """
        # Run migration to head
        command.upgrade(alembic_config, "head")

        # Get current revision from database
        current_rev = get_current_revision(db_engine)

        # Get head revision from scripts
        head_rev = get_head_revision(alembic_config)

        # Verify they match
        assert current_rev is not None, "Current revision should be set"
        assert current_rev == head_rev, "Current revision should match head revision"

    def test_migration_creates_foreign_keys(self, alembic_config, db_engine):
        """
        Test that foreign key constraints are created
        """
        # Run migration to head
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Check bill_of_materials foreign keys
        bom_fks = inspector.get_foreign_keys("bill_of_materials")
        assert len(bom_fks) >= 2, "bill_of_materials should have at least 2 foreign keys"

        fk_columns = [fk['constrained_columns'][0] for fk in bom_fks]
        assert "parent_product_id" in fk_columns, "parent_product_id FK should exist"
        assert "child_product_id" in fk_columns, "child_product_id FK should exist"

        # Check pcf_calculations foreign keys
        calc_fks = inspector.get_foreign_keys("pcf_calculations")
        assert len(calc_fks) >= 1, "pcf_calculations should have at least 1 foreign key"

        calc_fk_columns = [fk['constrained_columns'][0] for fk in calc_fks]
        assert "product_id" in calc_fk_columns, "product_id FK should exist"


class TestMigrationDown:
    """Test Scenario 2: Migration Down (Rollback)"""

    def test_migration_downgrade_drops_tables(self, alembic_config, db_engine):
        """
        Test that downgrading migration drops all tables
        """
        # First upgrade to head
        command.upgrade(alembic_config, "head")

        # Verify tables exist
        tables_before = get_table_names(db_engine)
        assert len(tables_before) >= 6, "Tables should exist after upgrade"

        # Get the current revision (head)
        head_rev = get_head_revision(alembic_config)

        # Downgrade to base
        command.downgrade(alembic_config, "base")

        # Get tables after downgrade
        tables_after = get_table_names(db_engine)

        # Only alembic_version should remain (or it might be dropped too)
        # In some Alembic configs, alembic_version persists
        assert len(tables_after) <= 1, "Most or all tables should be dropped after downgrade"

        # Verify core tables are dropped
        assert "products" not in tables_after, "products should be dropped"
        assert "emission_factors" not in tables_after, "emission_factors should be dropped"
        assert "bill_of_materials" not in tables_after, "bill_of_materials should be dropped"

    def test_migration_downgrade_drops_views(self, alembic_config, db_engine):
        """
        Test that downgrading drops views
        """
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Verify view exists
        views_before = get_view_names(db_engine)
        assert "v_bom_explosion" in views_before, "View should exist after upgrade"

        # Downgrade
        command.downgrade(alembic_config, "base")

        # Verify view is dropped
        views_after = get_view_names(db_engine)
        assert "v_bom_explosion" not in views_after, "View should be dropped after downgrade"

    def test_migration_downgrade_updates_version(self, alembic_config, db_engine):
        """
        Test that downgrade updates alembic_version correctly
        """
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Get revision before downgrade
        rev_before = get_current_revision(db_engine)
        assert rev_before is not None, "Should have revision after upgrade"

        # Downgrade
        command.downgrade(alembic_config, "base")

        # Get revision after downgrade
        rev_after = get_current_revision(db_engine)

        # Should be None (base state)
        assert rev_after is None, "Should have no revision after downgrade to base"


class TestMigrationIdempotency:
    """Test Scenario 3: Idempotent Migration"""

    def test_migration_upgrade_is_idempotent(self, alembic_config, db_engine):
        """
        Test that running upgrade multiple times is safe (no-op on subsequent runs)
        """
        # Run migration first time
        command.upgrade(alembic_config, "head")

        # Get state after first run
        tables_first = sorted(get_table_names(db_engine))
        rev_first = get_current_revision(db_engine)

        # Run migration second time (should be no-op)
        command.upgrade(alembic_config, "head")

        # Get state after second run
        tables_second = sorted(get_table_names(db_engine))
        rev_second = get_current_revision(db_engine)

        # State should be identical
        assert tables_first == tables_second, "Tables should be the same after second upgrade"
        assert rev_first == rev_second, "Revision should be the same after second upgrade"

    def test_migration_multiple_upgrades_no_errors(self, alembic_config, db_engine):
        """
        Test that multiple upgrade commands don't raise errors
        """
        # Run upgrade 3 times - should not raise any exceptions
        try:
            command.upgrade(alembic_config, "head")
            command.upgrade(alembic_config, "head")
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.fail(f"Multiple upgrades should not raise errors: {e}")

        # Verify database is in valid state
        tables = get_table_names(db_engine)
        assert len(tables) >= 6, "All tables should still exist"


class TestMigrationVersionTracking:
    """Test Scenario 4: Migration Version Tracking"""

    def test_current_revision_matches_head(self, alembic_config, db_engine):
        """
        Test that current database revision matches head revision
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        # Get revisions
        current_rev = get_current_revision(db_engine)
        head_rev = get_head_revision(alembic_config)

        # Should match
        assert current_rev == head_rev, "Current revision should match head"

    def test_fresh_database_has_no_revision(self, alembic_config, db_engine):
        """
        Test that fresh database has no revision before migration
        """
        # Get revision from fresh database
        current_rev = get_current_revision(db_engine)

        # Should be None
        assert current_rev is None, "Fresh database should have no revision"

    def test_alembic_version_table_has_single_row(self, alembic_config, db_engine):
        """
        Test that alembic_version table has exactly one row after migration
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        # Query alembic_version table
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM alembic_version"))
            row = result.fetchone()
            count = row[0]

        # Should have exactly 1 row
        assert count == 1, "alembic_version should have exactly 1 row"


class TestMigrationConstraints:
    """Test that migrations include all constraints from schema"""

    def test_unique_constraints_exist(self, alembic_config, db_engine):
        """
        Test that unique constraints are created by migration
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Check products unique constraint on code
        products_constraints = inspector.get_unique_constraints("products")
        products_constraint_columns = [set(uc['column_names']) for uc in products_constraints]

        # code should have unique constraint
        assert {'code'} in products_constraint_columns or any(
            'code' in cols for cols in products_constraint_columns
        ), "products.code should have unique constraint"

        # Check bill_of_materials composite unique constraint
        bom_constraints = inspector.get_unique_constraints("bill_of_materials")
        bom_constraint_columns = [set(uc['column_names']) for uc in bom_constraints]

        # Should have unique constraint on (parent_product_id, child_product_id)
        assert {'parent_product_id', 'child_product_id'} in bom_constraint_columns, \
            "bill_of_materials should have unique constraint on (parent_product_id, child_product_id)"

    def test_check_constraints_exist(self, alembic_config, db_engine):
        """
        Test that check constraints are created
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Check products table has check constraint on unit
        products_checks = inspector.get_check_constraints("products")

        # Should have at least one check constraint
        assert len(products_checks) >= 1, "products should have check constraints"

        # Check bill_of_materials has check constraint preventing self-reference
        bom_checks = inspector.get_check_constraints("bill_of_materials")

        # Should have check constraints
        assert len(bom_checks) >= 1, "bill_of_materials should have check constraints"


class TestMigrationStructure:
    """Test the structure of Alembic configuration"""

    def test_alembic_ini_exists(self):
        """
        Test that alembic.ini configuration file exists
        """
        backend_dir = Path(__file__).parent.parent.parent
        alembic_ini = backend_dir / "alembic.ini"

        assert alembic_ini.exists(), "alembic.ini should exist in backend directory"

    def test_alembic_directory_exists(self):
        """
        Test that alembic/ directory exists with proper structure
        """
        backend_dir = Path(__file__).parent.parent.parent
        alembic_dir = backend_dir / "alembic"

        assert alembic_dir.exists(), "alembic/ directory should exist"
        assert alembic_dir.is_dir(), "alembic should be a directory"

        # Check for env.py
        env_py = alembic_dir / "env.py"
        assert env_py.exists(), "alembic/env.py should exist"

        # Check for versions directory
        versions_dir = alembic_dir / "versions"
        assert versions_dir.exists(), "alembic/versions/ directory should exist"
        assert versions_dir.is_dir(), "versions should be a directory"

    def test_initial_migration_exists(self):
        """
        Test that initial migration script exists in versions/
        """
        backend_dir = Path(__file__).parent.parent.parent
        versions_dir = backend_dir / "alembic" / "versions"

        # Get all Python files in versions directory
        migration_files = list(versions_dir.glob("*.py"))

        # Filter out __init__.py and __pycache__
        migration_files = [
            f for f in migration_files
            if f.name != "__init__.py" and not f.name.startswith(".")
        ]

        # Should have at least one migration
        assert len(migration_files) >= 1, "Should have at least one migration script"

        # Check that migration contains "initial" or "001" in name
        migration_names = [f.name for f in migration_files]
        has_initial = any(
            "initial" in name.lower() or "001" in name
            for name in migration_names
        )

        assert has_initial, "Should have initial migration script"


class TestMigrationDataIntegrity:
    """Test that migrations preserve data integrity"""

    def test_migration_enables_foreign_keys(self, alembic_config, db_engine):
        """
        Test that foreign keys are enforced after migration
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        # PostgreSQL always enforces FKs (there is no PRAGMA), so check that
        # a BOM row pointing at non-existent products is rejected
        with pytest.raises(IntegrityError):
            with db_engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO bill_of_materials (id, parent_product_id, child_product_id, quantity)
                    VALUES ('orphan-bom', 'no-such-parent', 'no-such-child', 1.0)
                """))

    def test_cascade_delete_works(self, alembic_config, db_engine):
        """
        Test that cascade delete is properly configured
        """
        # Run migration
        command.upgrade(alembic_config, "head")

        # Create session
        Session = sessionmaker(bind=db_engine)
        session = Session()

        try:
            # Insert test product
            session.execute(text("""
                INSERT INTO products (id, code, name, unit)
                VALUES ('test-product-1', 'TEST-001', 'Test Product', 'unit')
            """))

            # Insert child product
            session.execute(text("""
                INSERT INTO products (id, code, name, unit)
                VALUES ('test-product-2', 'TEST-002', 'Test Child', 'unit')
            """))

            # Insert BOM relationship
            session.execute(text("""
                INSERT INTO bill_of_materials (id, parent_product_id, child_product_id, quantity)
                VALUES ('test-bom-1', 'test-product-1', 'test-product-2', 1.0)
            """))

            session.commit()

            # Verify BOM exists
            result = session.execute(text("SELECT COUNT(*) FROM bill_of_materials"))
            assert result.fetchone()[0] == 1, "BOM should exist"

            # Delete parent product (should cascade to BOM)
            session.execute(text("DELETE FROM products WHERE id = 'test-product-1'"))
            session.commit()

            # Verify BOM was deleted via cascade
            result = session.execute(text("SELECT COUNT(*) FROM bill_of_materials"))
            bom_count = result.fetchone()[0]

            assert bom_count == 0, "BOM should be deleted via cascade delete"

        finally:
            session.close()
