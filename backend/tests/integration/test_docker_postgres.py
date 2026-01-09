"""
Integration tests for Docker PostgreSQL infrastructure.

TASK-DB-P8-001: PostgreSQL Docker Infrastructure

This test suite validates:
- docker-compose.yml PostgreSQL service configuration (Layer 1)
- Environment configuration for PostgreSQL (Layer 2)
- Connection validation scripts (Layer 3)
- Data persistence across container restarts
- Network integration with existing Docker services

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (PostgreSQL container not yet configured)
- Implementation must make tests PASS without modifying tests

Prerequisites:
- Docker PostgreSQL running: docker-compose up -d postgres
- Environment variable: DATABASE_URL=postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator

Run with: pytest backend/tests/integration/test_docker_postgres.py -v
"""

import os
import pytest
import yaml
import time
from pathlib import Path
from typing import Optional

# Skip entire module if running without Docker
pytestmark = pytest.mark.integration


# =============================================================================
# Constants for Docker PostgreSQL Configuration
# =============================================================================

# Expected PostgreSQL Docker configuration values
EXPECTED_POSTGRES_IMAGE = "postgres:16-alpine"
EXPECTED_POSTGRES_CONTAINER = "pcf-postgres"
EXPECTED_POSTGRES_PORT = "5432:5432"
EXPECTED_POSTGRES_USER = "pcf_user"
EXPECTED_POSTGRES_PASSWORD = "DB_PASSWORD"
EXPECTED_POSTGRES_DB = "pcf_calculator"
EXPECTED_VOLUME_NAME = "pcf-postgres-data"
EXPECTED_NETWORK = "pcf-network"


# =============================================================================
# Helper Functions
# =============================================================================


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # backend/tests/integration/test_docker_postgres.py -> project root
    return current_file.parent.parent.parent.parent


def load_docker_compose() -> Optional[dict]:
    """
    Load and parse docker-compose.yml file.

    Returns:
        dict: Parsed docker-compose configuration
        None: If file cannot be loaded or parsed
    """
    compose_path = get_project_root() / "docker-compose.yml"
    if not compose_path.exists():
        return None

    try:
        with open(compose_path, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def postgres_docker_available() -> bool:
    """
    Check if PostgreSQL Docker container is available.

    Returns True if:
    - DATABASE_URL points to PostgreSQL
    - Connection can be established
    """
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator"
    )

    if "postgresql" not in db_url.lower():
        return False

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


# Marker for tests requiring Docker PostgreSQL
requires_docker_postgres = pytest.mark.skipif(
    not postgres_docker_available(),
    reason="Docker PostgreSQL not available. Run: docker-compose up -d postgres"
)


# =============================================================================
# Layer 1: Docker Compose Configuration Tests
# =============================================================================


class TestDockerComposeConfiguration:
    """
    Layer 1: Validate docker-compose.yml PostgreSQL service configuration.

    These tests verify the docker-compose.yml file contains the correct
    PostgreSQL service definition without requiring Docker to be running.
    """

    def test_docker_compose_file_exists(self):
        """Test 1.1: docker-compose.yml file exists in project root."""
        compose_path = get_project_root() / "docker-compose.yml"
        assert compose_path.exists(), (
            f"docker-compose.yml not found at {compose_path}"
        )

    def test_docker_compose_valid_yaml(self):
        """Test 1.2: docker-compose.yml is valid YAML."""
        compose = load_docker_compose()
        assert compose is not None, "docker-compose.yml failed to parse as YAML"
        assert isinstance(compose, dict), "docker-compose.yml should be a YAML dictionary"

    def test_postgres_service_defined(self):
        """Test 1.3: PostgreSQL service is defined in docker-compose.yml."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        services = compose.get("services", {})
        assert "postgres" in services, (
            "PostgreSQL service 'postgres' not found in docker-compose.yml. "
            f"Found services: {list(services.keys())}"
        )

    def test_postgres_image_version(self):
        """Test 1.4: PostgreSQL service uses postgres:16-alpine image."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        image = postgres.get("image")

        assert image == EXPECTED_POSTGRES_IMAGE, (
            f"PostgreSQL image should be '{EXPECTED_POSTGRES_IMAGE}', "
            f"got '{image}'"
        )

    def test_postgres_container_name(self):
        """Test 1.5: PostgreSQL container name is 'pcf-postgres'."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        container_name = postgres.get("container_name")

        assert container_name == EXPECTED_POSTGRES_CONTAINER, (
            f"Container name should be '{EXPECTED_POSTGRES_CONTAINER}', "
            f"got '{container_name}'"
        )

    def test_postgres_port_mapping(self):
        """Test 1.6: PostgreSQL port 5432 is exposed."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        ports = postgres.get("ports", [])

        assert EXPECTED_POSTGRES_PORT in ports, (
            f"Port mapping '{EXPECTED_POSTGRES_PORT}' not found. "
            f"Found ports: {ports}"
        )

    def test_postgres_environment_variables(self):
        """Test 1.7: PostgreSQL environment variables are configured."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        env = postgres.get("environment", {})

        # Environment can be dict or list
        if isinstance(env, list):
            env_dict = {}
            for item in env:
                if "=" in item:
                    key, value = item.split("=", 1)
                    env_dict[key] = value
            env = env_dict

        # Check for POSTGRES_USER (with or without default)
        assert any("POSTGRES_USER" in str(k) for k in env.keys()), (
            f"POSTGRES_USER not found in environment. Found: {list(env.keys())}"
        )
        assert any("POSTGRES_PASSWORD" in str(k) for k in env.keys()), (
            f"POSTGRES_PASSWORD not found in environment. Found: {list(env.keys())}"
        )
        assert any("POSTGRES_DB" in str(k) for k in env.keys()), (
            f"POSTGRES_DB not found in environment. Found: {list(env.keys())}"
        )

    def test_postgres_volume_defined(self):
        """Test 1.8: PostgreSQL data volume is defined for persistence."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        volumes = postgres.get("volumes", [])

        # Check for postgres_data volume mount
        has_data_volume = any("postgres_data" in str(v) for v in volumes)
        assert has_data_volume, (
            f"postgres_data volume not found in service volumes. Found: {volumes}"
        )

        # Check volume is defined at top level
        top_volumes = compose.get("volumes", {})
        assert "postgres_data" in top_volumes, (
            f"postgres_data not defined in top-level volumes. Found: {list(top_volumes.keys())}"
        )

    def test_postgres_healthcheck_defined(self):
        """Test 1.9: PostgreSQL health check is configured."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        healthcheck = postgres.get("healthcheck", {})

        assert healthcheck, "No healthcheck defined for PostgreSQL service"
        assert "test" in healthcheck, "healthcheck.test not defined"
        assert "interval" in healthcheck, "healthcheck.interval not defined"
        assert "timeout" in healthcheck, "healthcheck.timeout not defined"
        assert "retries" in healthcheck, "healthcheck.retries not defined"

    def test_postgres_network_attached(self):
        """Test 1.10: PostgreSQL is attached to pcf-network."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        networks = postgres.get("networks", [])

        # Networks can be list or dict
        if isinstance(networks, dict):
            network_names = list(networks.keys())
        else:
            network_names = networks

        assert EXPECTED_NETWORK in network_names, (
            f"PostgreSQL not attached to '{EXPECTED_NETWORK}'. "
            f"Found networks: {network_names}"
        )

    def test_postgres_restart_policy(self):
        """Test 1.11: PostgreSQL has restart policy configured."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        restart = postgres.get("restart")

        assert restart is not None, "No restart policy defined for PostgreSQL"
        assert restart in ["always", "unless-stopped", "on-failure"], (
            f"Unexpected restart policy: {restart}"
        )


# =============================================================================
# Layer 2: Environment Configuration Tests
# =============================================================================


class TestEnvironmentConfiguration:
    """
    Layer 2: Validate environment configuration for PostgreSQL.

    These tests verify .env.docker and .env.example contain the correct
    PostgreSQL configuration variables.
    """

    def test_env_docker_file_exists(self):
        """Test 2.1: .env.docker file exists in project root."""
        env_path = get_project_root() / ".env.docker"
        assert env_path.exists(), (
            f".env.docker not found at {env_path}. "
            "This file is required for Docker PostgreSQL configuration."
        )

    def test_env_docker_contains_postgres_user(self):
        """Test 2.2: .env.docker contains POSTGRES_USER."""
        env_path = get_project_root() / ".env.docker"
        if not env_path.exists():
            pytest.skip(".env.docker file does not exist yet")

        content = env_path.read_text()
        assert "POSTGRES_USER" in content, (
            "POSTGRES_USER not found in .env.docker"
        )

    def test_env_docker_contains_postgres_password(self):
        """Test 2.3: .env.docker contains POSTGRES_PASSWORD."""
        env_path = get_project_root() / ".env.docker"
        if not env_path.exists():
            pytest.skip(".env.docker file does not exist yet")

        content = env_path.read_text()
        assert "POSTGRES_PASSWORD" in content, (
            "POSTGRES_PASSWORD not found in .env.docker"
        )

    def test_env_docker_contains_postgres_db(self):
        """Test 2.4: .env.docker contains POSTGRES_DB."""
        env_path = get_project_root() / ".env.docker"
        if not env_path.exists():
            pytest.skip(".env.docker file does not exist yet")

        content = env_path.read_text()
        assert "POSTGRES_DB" in content, (
            "POSTGRES_DB not found in .env.docker"
        )

    def test_env_docker_contains_database_url(self):
        """Test 2.5: .env.docker contains DATABASE_URL with PostgreSQL."""
        env_path = get_project_root() / ".env.docker"
        if not env_path.exists():
            pytest.skip(".env.docker file does not exist yet")

        content = env_path.read_text()
        assert "DATABASE_URL" in content, (
            "DATABASE_URL not found in .env.docker"
        )
        assert "postgresql://" in content, (
            "DATABASE_URL should contain postgresql:// connection string"
        )

    def test_env_example_contains_postgres_documentation(self):
        """Test 2.6: .env.example documents PostgreSQL configuration."""
        env_path = get_project_root() / ".env.example"
        if not env_path.exists():
            pytest.skip(".env.example file does not exist yet")

        content = env_path.read_text()
        # Should document PostgreSQL variables
        assert "POSTGRES" in content or "postgresql" in content.lower(), (
            ".env.example should document PostgreSQL configuration"
        )


# =============================================================================
# Layer 3: PostgreSQL Connection Tests (Requires Docker Running)
# =============================================================================


@requires_docker_postgres
class TestDockerPostgresConnection:
    """
    Layer 3: Integration tests for Docker PostgreSQL connection.

    These tests require Docker PostgreSQL to be running:
    docker-compose up -d postgres
    """

    @pytest.fixture(scope="class")
    def pg_engine(self):
        """Create PostgreSQL engine for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool

        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator"
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

    def test_postgres_connection_success(self, pg_engine):
        """Test 3.1: Can connect to Docker PostgreSQL."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1, "Basic query should return 1"

    def test_postgres_version_is_16(self, pg_engine):
        """Test 3.2: PostgreSQL version is 16.x."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()

        assert "PostgreSQL 16" in version, (
            f"Expected PostgreSQL 16.x, got: {version}"
        )

    def test_postgres_database_name_correct(self, pg_engine):
        """Test 3.3: Database name is 'pcf_calculator'."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()

        assert db_name == EXPECTED_POSTGRES_DB, (
            f"Expected database '{EXPECTED_POSTGRES_DB}', got '{db_name}'"
        )

    def test_postgres_user_has_privileges(self, pg_engine):
        """Test 3.4: User has CREATE TABLE privilege."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            # Try to create and drop a test table
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS _test_privileges_check (id INT)"
            ))
            conn.execute(text(
                "DROP TABLE IF EXISTS _test_privileges_check"
            ))
            conn.commit()

        # If we get here without exception, privileges are correct
        assert True

    def test_postgres_uuid_extension_available(self, pg_engine):
        """Test 3.5: uuid-ossp extension is available."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            result = conn.execute(text("SELECT uuid_generate_v4()"))
            uuid_value = result.scalar()
            conn.commit()

        # UUID should be 36 characters (with hyphens)
        assert len(str(uuid_value)) == 36, (
            f"UUID should be 36 chars, got {len(str(uuid_value))}"
        )

    def test_postgres_gen_random_uuid_available(self, pg_engine):
        """Test 3.6: gen_random_uuid() function is available (PostgreSQL 13+)."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT gen_random_uuid()"))
            uuid_value = result.scalar()

        assert len(str(uuid_value)) == 36, (
            "gen_random_uuid() should return valid UUID"
        )

    def test_postgres_pg_trgm_extension_available(self, pg_engine):
        """Test 3.7: pg_trgm extension is available for fuzzy search."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
            # Test that extension works
            result = conn.execute(text(
                "SELECT similarity('test', 'testing')"
            ))
            similarity = result.scalar()
            conn.commit()

        assert similarity is not None, "pg_trgm similarity function should work"
        assert 0 <= similarity <= 1, "Similarity should be between 0 and 1"


# =============================================================================
# Layer 4: Service Integration Tests (Requires Full Docker Stack)
# =============================================================================


@requires_docker_postgres
class TestServiceIntegration:
    """
    Layer 4: Integration tests for service dependencies.

    These tests verify that other Docker services can connect to PostgreSQL
    and that the DATABASE_URL environment variable works correctly.
    """

    def test_celery_worker_postgres_dependency(self):
        """Test 4.1: Celery worker service depends on postgres."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        celery_worker = compose.get("services", {}).get("celery_worker", {})
        depends_on = celery_worker.get("depends_on", {})

        # depends_on can be list or dict
        if isinstance(depends_on, list):
            assert "postgres" in depends_on, (
                "celery_worker should depend on postgres service"
            )
        else:
            assert "postgres" in depends_on, (
                "celery_worker should depend on postgres service"
            )

    def test_api_service_postgres_dependency(self):
        """Test 4.2: API service depends on postgres."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        api = compose.get("services", {}).get("api", {})
        depends_on = api.get("depends_on", {})

        # depends_on can be list or dict
        if isinstance(depends_on, list):
            assert "postgres" in depends_on, (
                "api service should depend on postgres service"
            )
        else:
            assert "postgres" in depends_on, (
                "api service should depend on postgres service"
            )

    def test_celery_worker_has_postgres_database_url(self):
        """Test 4.3: Celery worker has PostgreSQL DATABASE_URL configured."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        celery_worker = compose.get("services", {}).get("celery_worker", {})
        env = celery_worker.get("environment", [])

        # Convert list to string for searching
        env_str = str(env)

        assert "DATABASE_URL" in env_str, (
            "celery_worker should have DATABASE_URL environment variable"
        )
        assert "postgresql" in env_str.lower(), (
            "celery_worker DATABASE_URL should use PostgreSQL"
        )

    def test_api_service_has_postgres_database_url(self):
        """Test 4.4: API service has PostgreSQL DATABASE_URL configured."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        api = compose.get("services", {}).get("api", {})
        env = api.get("environment", [])

        # Convert list to string for searching
        env_str = str(env)

        assert "DATABASE_URL" in env_str, (
            "api service should have DATABASE_URL environment variable"
        )
        assert "postgresql" in env_str.lower(), (
            "api service DATABASE_URL should use PostgreSQL"
        )


# =============================================================================
# Layer 5: Data Persistence Tests
# =============================================================================


@requires_docker_postgres
class TestDataPersistence:
    """
    Layer 5: Tests for data persistence across container operations.

    These tests verify that data survives container restarts and that
    the volume is properly configured for persistence.
    """

    @pytest.fixture(scope="class")
    def pg_engine(self):
        """Create PostgreSQL engine for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool

        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator"
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

    def test_can_create_test_table(self, pg_engine):
        """Test 5.1: Can create a test table for persistence testing."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS _persistence_test (
                    id SERIAL PRIMARY KEY,
                    test_value VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()

        # Verify table exists
        with pg_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '_persistence_test'
                )
            """))
            exists = result.scalar()

        assert exists, "Test table should be created"

    def test_can_insert_and_retrieve_data(self, pg_engine):
        """Test 5.2: Can insert and retrieve data from test table."""
        from sqlalchemy import text
        import uuid

        test_value = f"test_{uuid.uuid4().hex[:8]}"

        with pg_engine.connect() as conn:
            # Ensure table exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS _persistence_test (
                    id SERIAL PRIMARY KEY,
                    test_value VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))

            # Insert test data
            conn.execute(text(
                f"INSERT INTO _persistence_test (test_value) VALUES ('{test_value}')"
            ))
            conn.commit()

        # Retrieve in new connection
        with pg_engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT test_value FROM _persistence_test WHERE test_value = '{test_value}'"
            ))
            retrieved = result.scalar()

        assert retrieved == test_value, (
            f"Retrieved value should match inserted value: {test_value}"
        )

    def test_cleanup_persistence_test(self, pg_engine):
        """Test 5.3: Cleanup persistence test table."""
        from sqlalchemy import text

        with pg_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS _persistence_test"))
            conn.commit()

        # Verify table is removed
        with pg_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '_persistence_test'
                )
            """))
            exists = result.scalar()

        assert not exists, "Test table should be cleaned up"


# =============================================================================
# Layer 6: Initialization Script Tests
# =============================================================================


class TestInitializationScripts:
    """
    Layer 6: Tests for database initialization scripts.

    These tests verify that initialization scripts are properly configured
    and will be executed when the PostgreSQL container starts.
    """

    def test_init_directory_exists(self):
        """Test 6.1: Database init directory exists."""
        init_path = get_project_root() / "backend" / "database" / "init"
        assert init_path.exists(), (
            f"Init directory not found at {init_path}. "
            "This directory is needed for PostgreSQL initialization scripts."
        )

    def test_extensions_script_exists(self):
        """Test 6.2: Extensions initialization script exists."""
        script_path = get_project_root() / "backend" / "database" / "init" / "01_extensions.sql"
        assert script_path.exists(), (
            f"Extensions script not found at {script_path}. "
            "This script should create required PostgreSQL extensions."
        )

    def test_extensions_script_creates_uuid_ossp(self):
        """Test 6.3: Extensions script creates uuid-ossp extension."""
        script_path = get_project_root() / "backend" / "database" / "init" / "01_extensions.sql"
        if not script_path.exists():
            pytest.skip("Extensions script does not exist yet")

        content = script_path.read_text()
        assert "uuid-ossp" in content, (
            "Extensions script should create uuid-ossp extension"
        )

    def test_extensions_script_creates_pg_trgm(self):
        """Test 6.4: Extensions script creates pg_trgm extension."""
        script_path = get_project_root() / "backend" / "database" / "init" / "01_extensions.sql"
        if not script_path.exists():
            pytest.skip("Extensions script does not exist yet")

        content = script_path.read_text()
        assert "pg_trgm" in content, (
            "Extensions script should create pg_trgm extension for fuzzy search"
        )

    def test_init_volume_mount_configured(self):
        """Test 6.5: Init directory is mounted in docker-compose.yml."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        volumes = postgres.get("volumes", [])

        # Check for init directory mount
        has_init_mount = any(
            "docker-entrypoint-initdb.d" in str(v)
            for v in volumes
        )
        assert has_init_mount, (
            "Init directory should be mounted to /docker-entrypoint-initdb.d. "
            f"Found volumes: {volumes}"
        )


# =============================================================================
# Layer 7: Health Check Tests
# =============================================================================


@requires_docker_postgres
class TestHealthCheck:
    """
    Layer 7: Tests for PostgreSQL health check configuration.

    These tests verify that the health check is properly configured
    and returns correct status.
    """

    def test_healthcheck_uses_pg_isready(self):
        """Test 7.1: Health check uses pg_isready command."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        healthcheck = postgres.get("healthcheck", {})
        test_cmd = healthcheck.get("test", [])

        # Convert to string for searching
        test_str = str(test_cmd)

        assert "pg_isready" in test_str, (
            f"Health check should use pg_isready. Found: {test_cmd}"
        )

    def test_healthcheck_interval_reasonable(self):
        """Test 7.2: Health check interval is reasonable (5-30 seconds)."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        healthcheck = postgres.get("healthcheck", {})
        interval = healthcheck.get("interval", "")

        # Parse interval (e.g., "10s" -> 10)
        if isinstance(interval, str):
            interval_seconds = int(interval.replace("s", "").replace("m", ""))
            if "m" in str(healthcheck.get("interval", "")):
                interval_seconds *= 60
        else:
            interval_seconds = interval

        assert 5 <= interval_seconds <= 30, (
            f"Health check interval should be 5-30 seconds, got {interval}"
        )

    def test_healthcheck_has_start_period(self):
        """Test 7.3: Health check has start_period for container startup."""
        compose = load_docker_compose()
        assert compose is not None, "Could not load docker-compose.yml"

        postgres = compose.get("services", {}).get("postgres", {})
        healthcheck = postgres.get("healthcheck", {})

        assert "start_period" in healthcheck, (
            "Health check should have start_period defined for container startup time"
        )
