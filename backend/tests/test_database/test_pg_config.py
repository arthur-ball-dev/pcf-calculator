"""
Test suite for PostgreSQL configuration validation.

TASK-DB-P7-004: PostgreSQL Production Configuration

Following TDD methodology - tests written first per task specification.
Tests validate database type detection, async URL conversion, and
environment template requirements.
"""

import pytest
import os
from pathlib import Path


# Test availability check - module imports
try:
    from backend.config import Settings
    from backend.database.connection import (
        get_engine,
        SessionLocal,
        create_test_engine,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestDatabaseTypeDetection:
    """Test database type detection from settings"""

    def test_sqlite_config_detected(self):
        """
        Test Scenario 1: SQLite configuration detection
        Input: DATABASE_URL=sqlite:///./test.db
        Expected:
            - is_sqlite returns True
            - is_postgresql returns False
        """
        settings = Settings(database_url="sqlite:///./test.db")

        assert settings.is_sqlite is True
        assert settings.is_postgresql is False

    def test_postgresql_config_detected(self):
        """
        Test Scenario 2: PostgreSQL configuration detection
        Input: DATABASE_URL=postgresql://user:pass@localhost/db
        Expected:
            - is_postgresql returns True
            - is_sqlite returns False
        """
        settings = Settings(database_url="postgresql://user:pass@localhost/db")

        assert settings.is_postgresql is True
        assert settings.is_sqlite is False

    def test_postgresql_with_port_detected(self):
        """
        Test PostgreSQL with explicit port is detected
        Input: DATABASE_URL=postgresql://user:pass@localhost:5432/db
        Expected: is_postgresql returns True
        """
        settings = Settings(database_url="postgresql://user:pass@localhost:5432/db")

        assert settings.is_postgresql is True
        assert settings.is_sqlite is False

    def test_supabase_url_detected_as_postgresql(self):
        """
        Test that Supabase connection string is detected as PostgreSQL
        Input: DATABASE_URL=postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
        Expected: is_postgresql returns True
        """
        settings = Settings(
            database_url="postgresql://postgres:password@db.project.supabase.co:5432/postgres?sslmode=require"
        )

        assert settings.is_postgresql is True
        assert settings.is_sqlite is False

    def test_postgresql_with_sslmode_detected(self):
        """
        Test PostgreSQL with SSL parameters is detected correctly
        Input: DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
        Expected: is_postgresql returns True
        """
        settings = Settings(
            database_url="postgresql://user:pass@host/db?sslmode=require"
        )

        assert settings.is_postgresql is True


class TestAsyncUrlConversion:
    """Test async database URL conversion for SQLAlchemy async operations"""

    def test_async_url_conversion_postgresql(self):
        """
        Test Scenario 3: Async URL conversion for PostgreSQL
        Input: DATABASE_URL=postgresql://user:pass@localhost/db
        Expected: async_database_url returns postgresql+asyncpg://...
        """
        settings = Settings(database_url="postgresql://user:pass@localhost/db")

        result = settings.async_database_url

        assert result.startswith("postgresql+asyncpg://")
        assert "user:pass@localhost/db" in result

    def test_async_url_conversion_sqlite(self):
        """
        Test Scenario 4: Async URL conversion for SQLite
        Input: DATABASE_URL=sqlite:///./test.db
        Expected: async_database_url returns sqlite+aiosqlite://...
        """
        settings = Settings(database_url="sqlite:///./test.db")

        result = settings.async_database_url

        assert result.startswith("sqlite+aiosqlite:///")
        assert "test.db" in result

    def test_async_url_preserves_query_params(self):
        """
        Test that async URL conversion preserves query parameters
        Input: DATABASE_URL=postgresql://user:pass@localhost/db?sslmode=require
        Expected: sslmode=require preserved in async URL
        """
        settings = Settings(
            database_url="postgresql://user:pass@localhost/db?sslmode=require"
        )

        result = settings.async_database_url

        assert "sslmode=require" in result

    def test_async_url_preserves_port(self):
        """
        Test that async URL conversion preserves port number
        Input: DATABASE_URL=postgresql://user:pass@localhost:5432/db
        Expected: Port 5432 preserved in async URL
        """
        settings = Settings(
            database_url="postgresql://user:pass@localhost:5432/db"
        )

        result = settings.async_database_url

        assert ":5432" in result


class TestEnvExampleFile:
    """Test .env.example file contains required configuration variables"""

    @pytest.fixture
    def env_example_path(self):
        """Path to .env.example file"""
        # Navigate from tests to project root
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / ".env.example"

    @pytest.fixture
    def env_sample_path(self):
        """Path to .env.sample file (current naming)"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / ".env.sample"

    def test_env_file_exists(self, env_example_path, env_sample_path):
        """
        Test Scenario 5: Environment template file exists
        Expected: Either .env.example or .env.sample exists
        """
        env_exists = env_example_path.exists() or env_sample_path.exists()
        assert env_exists, (
            "Environment template file must exist. "
            f"Checked: {env_example_path} and {env_sample_path}"
        )

    def test_env_file_has_database_url(self, env_example_path, env_sample_path):
        """
        Test that environment template contains DATABASE_URL variable
        """
        env_file = env_sample_path if env_sample_path.exists() else env_example_path

        with open(env_file, "r") as f:
            content = f.read()

        assert "DATABASE_URL" in content, "DATABASE_URL must be defined in env template"

    def test_env_file_has_postgresql_example(self, env_example_path, env_sample_path):
        """
        Test that environment template includes PostgreSQL connection example
        """
        env_file = env_sample_path if env_sample_path.exists() else env_example_path

        with open(env_file, "r") as f:
            content = f.read()

        assert "postgresql://" in content, (
            "Environment template must include PostgreSQL connection example"
        )

    def test_env_file_has_sqlite_example(self, env_example_path, env_sample_path):
        """
        Test that environment template includes SQLite connection example
        """
        env_file = env_sample_path if env_sample_path.exists() else env_example_path

        with open(env_file, "r") as f:
            content = f.read()

        assert "sqlite:///" in content, (
            "Environment template must include SQLite connection example"
        )

    def test_env_file_has_supabase_example(self, env_example_path, env_sample_path):
        """
        Test that environment template includes Supabase connection example
        """
        env_file = env_sample_path if env_sample_path.exists() else env_example_path

        with open(env_file, "r") as f:
            content = f.read()

        assert "supabase" in content.lower(), (
            "Environment template must include Supabase connection example"
        )

    def test_env_file_has_pool_settings(self, env_example_path, env_sample_path):
        """
        Test that environment template includes database pool settings
        """
        env_file = env_sample_path if env_sample_path.exists() else env_example_path

        with open(env_file, "r") as f:
            content = f.read()

        assert "DB_POOL_SIZE" in content, (
            "Environment template must include DB_POOL_SIZE setting"
        )
        assert "DB_MAX_OVERFLOW" in content, (
            "Environment template must include DB_MAX_OVERFLOW setting"
        )


class TestPoolingConfiguration:
    """Test database connection pool settings"""

    def test_pool_size_configurable(self):
        """
        Test that pool size is configurable via settings
        """
        settings = Settings(
            database_url="postgresql://user:pass@localhost/db",
            db_pool_size=10
        )

        assert settings.db_pool_size == 10

    def test_max_overflow_configurable(self):
        """
        Test that max overflow is configurable via settings
        """
        settings = Settings(
            database_url="postgresql://user:pass@localhost/db",
            db_max_overflow=20
        )

        assert settings.db_max_overflow == 20

    def test_default_pool_settings(self):
        """
        Test default pool settings are reasonable
        """
        settings = Settings(database_url="postgresql://user:pass@localhost/db")

        # Defaults should be reasonable for production
        assert settings.db_pool_size >= 3, "Default pool size should be at least 3"
        assert settings.db_pool_size <= 20, "Default pool size should not exceed 20"
        assert settings.db_max_overflow >= 5, "Default max overflow should be at least 5"


class TestProductionDatabaseDocumentation:
    """Test that production database documentation exists and is complete"""

    @pytest.fixture
    def docs_path(self):
        """Path to docs directory"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / "docs"

    def test_production_database_doc_exists(self, docs_path):
        """
        Test that PRODUCTION_DATABASE.md documentation exists
        """
        doc_file = docs_path / "PRODUCTION_DATABASE.md"
        assert doc_file.exists(), (
            f"Production database documentation must exist at {doc_file}"
        )

    def test_doc_has_postgresql_setup(self, docs_path):
        """
        Test that documentation includes PostgreSQL setup instructions
        """
        doc_file = docs_path / "PRODUCTION_DATABASE.md"
        if not doc_file.exists():
            pytest.skip("Documentation file not yet created")

        with open(doc_file, "r") as f:
            content = f.read()

        assert "PostgreSQL" in content, "Documentation must cover PostgreSQL setup"
        assert "CREATE DATABASE" in content or "createdb" in content.lower(), (
            "Documentation must include database creation instructions"
        )

    def test_doc_has_supabase_setup(self, docs_path):
        """
        Test that documentation includes Supabase setup instructions
        """
        doc_file = docs_path / "PRODUCTION_DATABASE.md"
        if not doc_file.exists():
            pytest.skip("Documentation file not yet created")

        with open(doc_file, "r") as f:
            content = f.read()

        assert "Supabase" in content, "Documentation must cover Supabase setup"

    def test_doc_has_migration_instructions(self, docs_path):
        """
        Test that documentation includes migration instructions
        """
        doc_file = docs_path / "PRODUCTION_DATABASE.md"
        if not doc_file.exists():
            pytest.skip("Documentation file not yet created")

        with open(doc_file, "r") as f:
            content = f.read()

        assert "alembic" in content.lower(), (
            "Documentation must include Alembic migration instructions"
        )

    def test_doc_has_troubleshooting(self, docs_path):
        """
        Test that documentation includes troubleshooting section
        """
        doc_file = docs_path / "PRODUCTION_DATABASE.md"
        if not doc_file.exists():
            pytest.skip("Documentation file not yet created")

        with open(doc_file, "r") as f:
            content = f.read()

        assert "troubleshoot" in content.lower() or "SSL" in content, (
            "Documentation must include troubleshooting guidance"
        )


class TestValidationScript:
    """Test that database validation script exists"""

    @pytest.fixture
    def scripts_path(self):
        """Path to scripts directory"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / "scripts"

    def test_validation_script_exists(self, scripts_path):
        """
        Test that validate_database.py script exists
        """
        script_file = scripts_path / "validate_database.py"
        assert script_file.exists(), (
            f"Database validation script must exist at {script_file}"
        )

    def test_validation_script_is_executable(self, scripts_path):
        """
        Test that validation script has proper shebang for execution
        """
        script_file = scripts_path / "validate_database.py"
        if not script_file.exists():
            pytest.skip("Validation script not yet created")

        with open(script_file, "r") as f:
            first_line = f.readline()

        assert first_line.startswith("#!"), (
            "Validation script should have a shebang line"
        )
        assert "python" in first_line, (
            "Validation script shebang should reference python"
        )


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Implementation not yet available")
class TestDualDatabaseEngineCreation:
    """Test that engine creation works for both database types"""

    def test_sqlite_engine_creation(self):
        """
        Test SQLite engine can be created via test helper
        """
        engine = create_test_engine("sqlite:///:memory:")

        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_postgresql_engine_config_validation(self):
        """
        Test that PostgreSQL engine config is validated
        Note: Does not require actual PostgreSQL connection
        """
        # Test that the settings properly format PostgreSQL URL
        settings = Settings(
            database_url="postgresql://user:pass@localhost:5432/testdb"
        )

        assert "5432" in settings.database_url
        assert "localhost" in settings.database_url


# Test markers for pytest organization
pytestmark = [
    pytest.mark.database,
    pytest.mark.unit,
    pytest.mark.configuration,
]
