"""
Tests for E2E Test Database Setup Script

TASK-DB-P9-007: Setup Dedicated PostgreSQL Test Database

This module tests the setup_test_db.py script functions:
- get_test_database_url: Get test database URL from environment
- create_test_database: Create test database if not exists
- run_migrations: Execute Alembic migrations on test database
- seed_data: Seed required data (sources, factors, user, products)
- verify_database: Verify test database state
- seed_sample_products: Seed E2E sample products

TDD Protocol:
    These tests are written BEFORE implementation per TDD methodology.
    Test file becomes read-only after implementation commit.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure test JWT secret is set before any backend imports
os.environ.setdefault(
    "PCF_CALC_JWT_SECRET_KEY",
    "test-secret-key-for-pytest-only-32-chars-minimum"
)

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestGetTestDatabaseUrl:
    """Tests for get_test_database_url function."""

    def test_returns_default_when_env_not_set(self, monkeypatch):
        """Returns default URL when TEST_DATABASE_URL not set."""
        # Clear environment variable
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        # Import fresh to ensure default is used
        from backend.scripts.setup_test_db import (
            get_test_database_url,
            DEFAULT_TEST_DB_URL,
        )

        result = get_test_database_url()

        assert result == DEFAULT_TEST_DB_URL
        assert "pcf_calculator_test" in result
        assert "postgresql" in result.lower()

    def test_returns_env_when_set(self, monkeypatch):
        """Returns environment URL when TEST_DATABASE_URL is set."""
        custom_url = "postgresql://custom:password@testhost:5432/custom_test_db"
        monkeypatch.setenv("TEST_DATABASE_URL", custom_url)

        from backend.scripts.setup_test_db import get_test_database_url

        result = get_test_database_url()

        assert result == custom_url

    def test_default_url_has_correct_format(self, monkeypatch):
        """Default URL has correct PostgreSQL connection format."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        from backend.scripts.setup_test_db import DEFAULT_TEST_DB_URL

        # Check URL format: postgresql://user:password@host:port/database
        assert DEFAULT_TEST_DB_URL.startswith("postgresql://")
        assert "@localhost:5432" in DEFAULT_TEST_DB_URL
        assert "pcf_calculator_test" in DEFAULT_TEST_DB_URL


class TestCreateTestDatabase:
    """Tests for create_test_database function."""

    @pytest.fixture
    def mock_psycopg_setup(self):
        """Setup mock psycopg (version 3) connection and cursor."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_psycopg = MagicMock()
        mock_psycopg.connect.return_value = mock_conn

        # psycopg3 uses OperationalError directly from the module
        mock_psycopg.OperationalError = Exception

        return mock_psycopg, mock_conn, mock_cursor

    def test_creates_database_when_not_exists(self, monkeypatch, mock_psycopg_setup):
        """Creates database when it doesn't exist."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        mock_psycopg, mock_conn, mock_cursor = mock_psycopg_setup
        mock_cursor.fetchone.return_value = None  # Database doesn't exist

        # Patch psycopg module
        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            # Need to reimport the module to pick up the mocks
            import importlib
            import backend.scripts.setup_test_db as setup_module
            importlib.reload(setup_module)

            result = setup_module.create_test_database()

        # Verify database was created
        assert result is True
        # Check CREATE DATABASE was called
        create_calls = [
            c for c in mock_cursor.execute.call_args_list
            if "CREATE DATABASE" in str(c)
        ]
        assert len(create_calls) == 1

    def test_skips_creation_when_exists(self, monkeypatch, mock_psycopg_setup):
        """Skips creation when database already exists."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        mock_psycopg, mock_conn, mock_cursor = mock_psycopg_setup
        mock_cursor.fetchone.return_value = (1,)  # Database exists

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            import importlib
            import backend.scripts.setup_test_db as setup_module
            importlib.reload(setup_module)

            result = setup_module.create_test_database()

        assert result is True
        # Check CREATE DATABASE was NOT called
        create_calls = [
            c for c in mock_cursor.execute.call_args_list
            if "CREATE DATABASE" in str(c)
        ]
        assert len(create_calls) == 0

    def test_returns_false_on_connection_error(self, monkeypatch):
        """Returns False when PostgreSQL connection fails."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        # Create proper mock for psycopg
        mock_psycopg = MagicMock()
        mock_psycopg.OperationalError = Exception

        # Simulate connection error
        mock_psycopg.connect.side_effect = mock_psycopg.OperationalError("Connection refused")

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            import importlib
            import backend.scripts.setup_test_db as setup_module
            importlib.reload(setup_module)

            result = setup_module.create_test_database()

        assert result is False

    def test_connects_to_postgres_database_for_creation(self, monkeypatch, mock_psycopg_setup):
        """Connects to 'postgres' database to create test database."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        mock_psycopg, mock_conn, mock_cursor = mock_psycopg_setup
        mock_cursor.fetchone.return_value = None

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            import importlib
            import backend.scripts.setup_test_db as setup_module
            importlib.reload(setup_module)

            setup_module.create_test_database()

        # Verify connection was to 'postgres' database
        connect_call = mock_psycopg.connect.call_args
        assert connect_call.kwargs.get("dbname") == "postgres"


class TestRunMigrations:
    """Tests for run_migrations function."""

    @patch("subprocess.run")
    def test_runs_alembic_upgrade(self, mock_run, monkeypatch):
        """Runs Alembic upgrade head command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Running migration...\nDone.",
            stderr=""
        )
        monkeypatch.delenv("SKIP_MIGRATIONS", raising=False)
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        from backend.scripts.setup_test_db import run_migrations

        result = run_migrations()

        assert result is True
        # Check alembic command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "alembic" in call_args[0][0]
        assert "upgrade" in call_args[0][0]
        assert "head" in call_args[0][0]

    def test_skips_when_env_set(self, monkeypatch):
        """Skips migrations when SKIP_MIGRATIONS=1."""
        monkeypatch.setenv("SKIP_MIGRATIONS", "1")

        from backend.scripts.setup_test_db import run_migrations

        result = run_migrations()

        assert result is True

    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run, monkeypatch):
        """Returns False when migration fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Migration error: table already exists"
        )
        monkeypatch.delenv("SKIP_MIGRATIONS", raising=False)
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        from backend.scripts.setup_test_db import run_migrations

        result = run_migrations()

        assert result is False

    @patch("subprocess.run")
    def test_sets_database_url_for_alembic(self, mock_run, monkeypatch):
        """Sets DATABASE_URL environment variable for Alembic."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        monkeypatch.delenv("SKIP_MIGRATIONS", raising=False)

        test_url = "postgresql://test:test@localhost:5432/test_db"
        monkeypatch.setenv("TEST_DATABASE_URL", test_url)

        from backend.scripts.setup_test_db import run_migrations

        run_migrations()

        # Check DATABASE_URL was set in environment passed to subprocess
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["env"]["DATABASE_URL"] == test_url


class TestSeedData:
    """Tests for seed_data function."""

    def test_skips_when_env_set(self, monkeypatch):
        """Skips seeding when SKIP_SEED=1."""
        monkeypatch.setenv("SKIP_SEED", "1")

        from backend.scripts.setup_test_db import seed_data

        result = seed_data()

        assert result is True


class TestSeedSampleProducts:
    """Tests for seed_sample_products function."""

    def test_creates_e2e_test_products(self, db_session):
        """Creates expected E2E test products."""
        from backend.models import Product
        from backend.scripts.setup_test_db import seed_sample_products

        # Ensure no products exist
        assert db_session.query(Product).count() == 0

        seed_sample_products(db_session)
        db_session.commit()  # Commit to persist

        # Verify products were created
        products = db_session.query(Product).all()
        assert len(products) >= 3  # At least 3 sample products

        # Verify E2E products have expected prefix
        e2e_products = [p for p in products if p.code.startswith("E2E-")]
        assert len(e2e_products) >= 3

    def test_skips_when_products_exist(self, db_session):
        """Skips seeding if products already exist."""
        from backend.models import Product
        from backend.scripts.setup_test_db import seed_sample_products

        # Create an existing product
        existing = Product(
            code="EXISTING-001",
            name="Existing Product",
            unit="kg"
        )
        db_session.add(existing)
        db_session.commit()

        initial_count = db_session.query(Product).count()

        seed_sample_products(db_session)

        # Count should be unchanged
        assert db_session.query(Product).count() == initial_count

    def test_products_have_correct_attributes(self, db_session):
        """Created products have expected attributes."""
        from backend.models import Product
        from backend.scripts.setup_test_db import seed_sample_products

        seed_sample_products(db_session)
        db_session.commit()

        products = db_session.query(Product).filter(
            Product.code.like("E2E-%")
        ).all()

        for product in products:
            # All products should have required fields
            assert product.code is not None
            assert product.name is not None
            assert product.unit is not None
            assert "E2E" in product.description or "E2E" in product.name


class TestResetTestDatabase:
    """Tests for reset_test_database function."""

    @patch("subprocess.run")
    def test_runs_alembic_downgrade(self, mock_run, monkeypatch):
        """Runs Alembic downgrade base command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Downgrading...\nDone.",
            stderr=""
        )
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

        from backend.scripts.setup_test_db import reset_test_database

        result = reset_test_database()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "alembic" in call_args[0][0]
        assert "downgrade" in call_args[0][0]
        assert "base" in call_args[0][0]


class TestURLParsing:
    """Tests for database URL parsing utilities."""

    def test_parse_standard_postgresql_url(self):
        """Parses standard PostgreSQL connection URL."""
        from backend.scripts.setup_test_db import parse_database_url

        url = "postgresql://myuser:mypassword@myhost:5433/mydb"
        result = parse_database_url(url)

        assert result["user"] == "myuser"
        assert result["password"] == "mypassword"
        assert result["host"] == "myhost"
        assert result["port"] == 5433
        assert result["database"] == "mydb"

    def test_parse_url_with_default_port(self):
        """Parses URL with default PostgreSQL port."""
        from backend.scripts.setup_test_db import parse_database_url

        url = "postgresql://user:pass@localhost/testdb"
        result = parse_database_url(url)

        assert result["host"] == "localhost"
        assert result["port"] == 5432  # Default PostgreSQL port

    def test_parse_url_with_special_characters(self):
        """Handles special characters in password."""
        from backend.scripts.setup_test_db import parse_database_url

        # URL-encoded password with special chars
        url = "postgresql://user:p%40ssw%23rd@localhost:5432/db"
        result = parse_database_url(url)

        assert result["user"] == "user"
        assert result["password"] == "p@ssw#rd"  # URL-decoded


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestIntegrationWithPostgreSQL:
    """Integration tests requiring real PostgreSQL connection."""

    @pytest.fixture
    def require_postgres(self):
        """Skip if PostgreSQL is not available."""
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests not enabled (set RUN_INTEGRATION_TESTS=1)")

        try:
            import psycopg
            conn = psycopg.connect(
                host="localhost",
                port=5432,
                user="pcf_user",
                password="DB_PASSWORD",
                dbname="postgres"
            )
            conn.close()
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    def test_full_setup_workflow(self, require_postgres):
        """Test complete database setup workflow."""
        from backend.scripts.setup_test_db import (
            create_test_database,
            run_migrations,
            verify_database,
        )

        # Step 1: Create database
        assert create_test_database() is True

        # Step 2: Run migrations (if not skipped)
        if os.getenv("SKIP_MIGRATIONS") != "1":
            assert run_migrations() is True

        # Step 3: Verify database
        # Note: verify_database may need seeding first

    def test_database_isolation(self, require_postgres):
        """Test that test database is isolated from dev database."""
        import psycopg

        # Connect to both databases
        dev_conn = psycopg.connect(
            host="localhost",
            port=5432,
            user="pcf_user",
            password="DB_PASSWORD",
            dbname="pcf_calculator"
        )
        test_conn = psycopg.connect(
            host="localhost",
            port=5432,
            user="pcf_user",
            password="DB_PASSWORD",
            dbname="pcf_calculator_test"
        )

        # They should be separate databases
        assert dev_conn.info.dbname == "pcf_calculator"
        assert test_conn.info.dbname == "pcf_calculator_test"

        dev_conn.close()
        test_conn.close()
