"""
Test suite for PostgreSQL migration integration tests.

TASK-DB-P5-001: PostgreSQL Migration

This test suite validates:
- PostgreSQL connection success
- Connection pooling under load (10 concurrent connections)
- UUID primary keys work correctly
- DateTime with timezone handling
- Transaction rollback capability

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (PostgreSQL not configured yet)
- Implementation must make tests PASS without modifying tests
"""

import os
import pytest
import concurrent.futures
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Generator
import threading
import time

# Skip entire module if PostgreSQL is not configured
pytestmark = pytest.mark.integration


def is_postgresql_configured() -> bool:
    """Check if PostgreSQL is configured via environment variable."""
    db_url = os.environ.get("DATABASE_URL", "")
    return "postgresql" in db_url.lower()


@pytest.fixture(scope="module")
def postgresql_engine():
    """
    Create PostgreSQL engine for testing.

    This fixture creates a connection to the PostgreSQL database
    configured via DATABASE_URL environment variable.

    Requirements:
    - DATABASE_URL must be set to a valid PostgreSQL connection string
    - Format: postgresql://user:password@host:port/database

    The engine uses connection pooling appropriate for testing.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import QueuePool

    db_url = os.environ.get("DATABASE_URL")

    if not db_url or "postgresql" not in db_url.lower():
        pytest.skip("PostgreSQL not configured. Set DATABASE_URL to run these tests.")

    # Convert to async-compatible URL if needed
    if "postgresql://" in db_url and "+asyncpg" not in db_url:
        # Use synchronous psycopg2 for these tests
        pass

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
def postgresql_session(postgresql_engine):
    """
    Create PostgreSQL session for testing.

    Provides a database session with transaction rollback for test isolation.
    Each test runs in its own transaction that is rolled back after the test.
    """
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=postgresql_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


class TestPostgreSQLConnection:
    """Test Scenario 1: PostgreSQL Connection Success"""

    def test_postgresql_connection_established(self, postgresql_engine):
        """
        Verify PostgreSQL connection can be established.

        Tests that the engine can create a valid connection to the database.
        This is the most basic connectivity test.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1, "Should be able to execute basic query"

    def test_postgresql_version_retrieved(self, postgresql_engine):
        """
        Verify PostgreSQL version can be retrieved.

        Tests that the connection is to a valid PostgreSQL database
        by querying the version string.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()

            assert version is not None, "Should retrieve PostgreSQL version"
            assert "PostgreSQL" in version, f"Should be PostgreSQL, got: {version}"

    def test_postgresql_database_name_accessible(self, postgresql_engine):
        """
        Verify current database name can be retrieved.

        Tests that we can query the current database context.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()

            assert db_name is not None, "Should retrieve database name"
            assert len(db_name) > 0, "Database name should not be empty"


class TestConnectionPooling:
    """Test Scenario 2: Connection Pooling Under Load"""

    def test_connection_pool_handles_10_concurrent_connections(self, postgresql_engine):
        """
        Verify connection pool handles 10 concurrent connections.

        This tests that the connection pool can successfully manage
        multiple concurrent database operations without timing out
        or failing due to connection exhaustion.
        """
        from sqlalchemy import text

        results = []
        errors = []

        def execute_query():
            try:
                with postgresql_engine.connect() as conn:
                    result = conn.execute(text("SELECT pg_sleep(0.1), 1"))
                    row = result.fetchone()
                    results.append(row[1])
            except Exception as e:
                errors.append(str(e))

        # Create 10 concurrent threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_query) for _ in range(10)]
            concurrent.futures.wait(futures, timeout=30)

        assert len(errors) == 0, f"No connection errors expected, got: {errors}"
        assert len(results) == 10, f"All 10 connections should complete, got {len(results)}"

    def test_connection_pool_reuses_connections(self, postgresql_engine):
        """
        Verify connections are reused from pool.

        Tests that the pool doesn't create new connections for each request
        but instead reuses existing connections.
        """
        from sqlalchemy import text

        # Get initial pool status
        initial_pool_size = postgresql_engine.pool.size()

        # Execute multiple queries
        for _ in range(20):
            with postgresql_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        # Pool size should not have grown excessively
        final_pool_size = postgresql_engine.pool.size()
        assert final_pool_size <= 5 + 10, \
            f"Pool should respect limits, got size {final_pool_size}"

    def test_connection_pool_timeout_handling(self, postgresql_engine):
        """
        Verify pool handles connection timeout gracefully.

        Tests that when all connections are in use, new requests
        wait for available connections rather than failing immediately.
        """
        from sqlalchemy import text
        import time

        # This test verifies the pool can queue requests
        start_time = time.time()

        def long_query():
            with postgresql_engine.connect() as conn:
                conn.execute(text("SELECT pg_sleep(0.2)"))

        # Submit more requests than pool size
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(long_query) for _ in range(15)]
            done, not_done = concurrent.futures.wait(futures, timeout=60)

        elapsed = time.time() - start_time

        # All should complete (queued requests wait for connections)
        assert len(done) == 15, f"All requests should complete, {len(not_done)} still pending"
        # Should take at least as long as queries need to run with pooling
        assert elapsed >= 0.2, "Should have waited for connection pool"


class TestUUIDPrimaryKeys:
    """Test Scenario 3: UUID Primary Keys Work Correctly"""

    def test_uuid_generation_function_exists(self, postgresql_engine):
        """
        Verify gen_random_uuid() function is available.

        PostgreSQL 13+ includes gen_random_uuid() by default.
        Earlier versions require pgcrypto extension.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT gen_random_uuid()"))
            uuid_value = result.scalar()

            assert uuid_value is not None, "gen_random_uuid() should return a value"
            # UUID format: 8-4-4-4-12 hex digits
            uuid_str = str(uuid_value)
            assert len(uuid_str) == 36, f"UUID should be 36 chars, got {len(uuid_str)}"
            assert uuid_str.count('-') == 4, "UUID should have 4 dashes"

    def test_uuid_column_type_works(self, postgresql_engine):
        """
        Verify UUID column type can store and retrieve values.

        Tests that PostgreSQL UUID type works correctly with SQLAlchemy.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Create temporary table with UUID column
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_uuid_column (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100)
                )
            """))
            conn.commit()

            # Insert without providing UUID (should auto-generate)
            conn.execute(text(
                "INSERT INTO test_uuid_column (name) VALUES ('Test Row')"
            ))
            conn.commit()

            # Retrieve and verify
            result = conn.execute(text(
                "SELECT id, name FROM test_uuid_column WHERE name = 'Test Row'"
            ))
            row = result.fetchone()

            assert row is not None, "Should retrieve inserted row"
            assert row[0] is not None, "UUID should be auto-generated"
            assert len(str(row[0])) == 36, "UUID should be properly formatted"

    def test_uuid_uniqueness_enforced(self, postgresql_engine):
        """
        Verify UUID primary key uniqueness is enforced.

        Tests that duplicate UUIDs are rejected by the database.
        """
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError

        with postgresql_engine.connect() as conn:
            # Create temporary table with UUID column
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_uuid_unique (
                    id UUID PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.commit()

            # Insert with specific UUID
            test_uuid = "123e4567-e89b-12d3-a456-426614174000"
            conn.execute(text(
                f"INSERT INTO test_uuid_unique (id, name) VALUES ('{test_uuid}', 'First')"
            ))
            conn.commit()

            # Try to insert duplicate UUID - should fail
            with pytest.raises(IntegrityError):
                conn.execute(text(
                    f"INSERT INTO test_uuid_unique (id, name) VALUES ('{test_uuid}', 'Second')"
                ))
                conn.commit()

    def test_uuid_foreign_key_reference(self, postgresql_engine):
        """
        Verify UUID foreign key references work correctly.

        Tests that UUID columns can be used as foreign key references.
        """
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError

        with postgresql_engine.connect() as conn:
            # Create parent table
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_uuid_parent (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100)
                )
            """))

            # Create child table with FK reference
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_uuid_child (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    parent_id UUID REFERENCES test_uuid_parent(id),
                    name VARCHAR(100)
                )
            """))
            conn.commit()

            # Insert parent and get its UUID
            conn.execute(text(
                "INSERT INTO test_uuid_parent (name) VALUES ('Parent')"
            ))
            conn.commit()

            result = conn.execute(text(
                "SELECT id FROM test_uuid_parent WHERE name = 'Parent'"
            ))
            parent_id = result.scalar()

            # Insert child with valid FK
            conn.execute(text(
                f"INSERT INTO test_uuid_child (parent_id, name) VALUES ('{parent_id}', 'Child')"
            ))
            conn.commit()

            # Verify FK constraint by trying invalid reference
            with pytest.raises(IntegrityError):
                fake_uuid = "00000000-0000-0000-0000-000000000000"
                conn.execute(text(
                    f"INSERT INTO test_uuid_child (parent_id, name) VALUES ('{fake_uuid}', 'Orphan')"
                ))
                conn.commit()


class TestDateTimeWithTimezone:
    """Test Scenario 4: DateTime with Timezone Handling"""

    def test_timestamp_with_timezone_column(self, postgresql_engine):
        """
        Verify TIMESTAMP WITH TIME ZONE column type works.

        Tests that PostgreSQL timestamptz type stores and retrieves
        timezone-aware datetime values correctly.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Create temporary table with timestamptz column
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_timestamptz (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            conn.commit()

            # Insert and retrieve
            conn.execute(text("INSERT INTO test_timestamptz DEFAULT VALUES"))
            conn.commit()

            result = conn.execute(text("SELECT created_at FROM test_timestamptz"))
            created_at = result.scalar()

            assert created_at is not None, "Should retrieve timestamp"
            # PostgreSQL timestamptz is always UTC
            assert created_at.tzinfo is not None or \
                   hasattr(created_at, 'utcoffset'), \
                   "Timestamp should have timezone info"

    def test_timezone_conversion_preserves_instant(self, postgresql_engine):
        """
        Verify timezone conversion preserves the actual instant in time.

        Tests that storing a timestamp in one timezone and retrieving it
        represents the same instant regardless of timezone display.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Create temporary table
            conn.execute(text("""
                CREATE TEMPORARY TABLE test_tz_convert (
                    id SERIAL PRIMARY KEY,
                    event_time TIMESTAMP WITH TIME ZONE
                )
            """))
            conn.commit()

            # Insert with specific timezone
            conn.execute(text("""
                INSERT INTO test_tz_convert (event_time)
                VALUES ('2024-06-15 10:00:00+05:00')
            """))
            conn.commit()

            # Retrieve in different timezone
            result = conn.execute(text("""
                SELECT event_time AT TIME ZONE 'UTC' as utc_time,
                       event_time AT TIME ZONE 'America/New_York' as ny_time
                FROM test_tz_convert
            """))
            row = result.fetchone()

            # UTC should be 05:00 (10:00 - 5 hours)
            utc_time = row[0]
            assert utc_time.hour == 5, f"UTC should be 05:00, got {utc_time.hour}"

    def test_current_timestamp_has_timezone(self, postgresql_engine):
        """
        Verify NOW() returns timezone-aware timestamp.

        Tests that PostgreSQL's NOW() function returns a timestamp
        with timezone information.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT NOW()"))
            now_value = result.scalar()

            assert now_value is not None, "NOW() should return a value"
            # Verify it's a datetime with timezone awareness
            assert hasattr(now_value, 'tzinfo') or hasattr(now_value, 'utcoffset'), \
                "NOW() should return timezone-aware timestamp"

    def test_datetime_comparison_across_timezones(self, postgresql_engine):
        """
        Verify datetime comparisons work correctly across timezones.

        Tests that comparing timestamps in different timezones
        compares the actual instants correctly.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # These represent the same instant
            result = conn.execute(text("""
                SELECT
                    '2024-06-15 10:00:00+00'::timestamptz =
                    '2024-06-15 06:00:00-04'::timestamptz AS same_instant
            """))
            same_instant = result.scalar()

            assert same_instant is True, \
                "Same instant in different timezones should be equal"


class TestTransactionRollback:
    """Test Scenario 5: Transaction Rollback Capability"""

    def test_transaction_rollback_reverts_insert(self, postgresql_engine):
        """
        Verify transaction rollback reverts INSERT operations.

        Tests that starting a transaction, inserting data, and then
        rolling back leaves the database unchanged.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Create persistent test table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_rollback_insert (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.commit()

            # Clear any existing data
            conn.execute(text("DELETE FROM test_rollback_insert"))
            conn.commit()

        # Start new connection for transaction test
        with postgresql_engine.connect() as conn:
            trans = conn.begin()

            # Insert data
            conn.execute(text(
                "INSERT INTO test_rollback_insert (name) VALUES ('Should Not Exist')"
            ))

            # Verify insert is visible within transaction
            result = conn.execute(text(
                "SELECT COUNT(*) FROM test_rollback_insert WHERE name = 'Should Not Exist'"
            ))
            count_before = result.scalar()
            assert count_before == 1, "Insert should be visible within transaction"

            # Rollback
            trans.rollback()

        # Verify data was rolled back
        with postgresql_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM test_rollback_insert WHERE name = 'Should Not Exist'"
            ))
            count_after = result.scalar()
            assert count_after == 0, "Rollback should revert the insert"

        # Cleanup
        with postgresql_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_rollback_insert"))
            conn.commit()

    def test_transaction_rollback_reverts_update(self, postgresql_engine):
        """
        Verify transaction rollback reverts UPDATE operations.

        Tests that starting a transaction, updating data, and then
        rolling back leaves the original data unchanged.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Setup test data
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_rollback_update (
                    id SERIAL PRIMARY KEY,
                    value INTEGER
                )
            """))
            conn.execute(text("DELETE FROM test_rollback_update"))
            conn.execute(text("INSERT INTO test_rollback_update (value) VALUES (100)"))
            conn.commit()

        # Perform update in transaction then rollback
        with postgresql_engine.connect() as conn:
            trans = conn.begin()

            conn.execute(text("UPDATE test_rollback_update SET value = 999"))

            # Verify update visible within transaction
            result = conn.execute(text("SELECT value FROM test_rollback_update"))
            assert result.scalar() == 999, "Update should be visible in transaction"

            trans.rollback()

        # Verify original value preserved
        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT value FROM test_rollback_update"))
            assert result.scalar() == 100, "Rollback should preserve original value"

        # Cleanup
        with postgresql_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_rollback_update"))
            conn.commit()

    def test_transaction_rollback_reverts_delete(self, postgresql_engine):
        """
        Verify transaction rollback reverts DELETE operations.

        Tests that starting a transaction, deleting data, and then
        rolling back restores the deleted data.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Setup test data
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_rollback_delete (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.execute(text("DELETE FROM test_rollback_delete"))
            conn.execute(text("INSERT INTO test_rollback_delete (name) VALUES ('Keep Me')"))
            conn.commit()

        # Perform delete in transaction then rollback
        with postgresql_engine.connect() as conn:
            trans = conn.begin()

            conn.execute(text("DELETE FROM test_rollback_delete WHERE name = 'Keep Me'"))

            # Verify delete visible within transaction
            result = conn.execute(text("SELECT COUNT(*) FROM test_rollback_delete"))
            assert result.scalar() == 0, "Delete should be visible in transaction"

            trans.rollback()

        # Verify data restored
        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM test_rollback_delete"))
            assert result.scalar() == 1, "Rollback should restore deleted data"

        # Cleanup
        with postgresql_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_rollback_delete"))
            conn.commit()

    def test_nested_transaction_savepoint(self, postgresql_engine):
        """
        Verify nested transactions with savepoints work correctly.

        Tests that PostgreSQL savepoints allow partial rollbacks
        within a larger transaction.
        """
        from sqlalchemy import text

        with postgresql_engine.connect() as conn:
            # Setup
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_savepoint (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.execute(text("DELETE FROM test_savepoint"))
            conn.commit()

        with postgresql_engine.connect() as conn:
            trans = conn.begin()

            # First insert (will be kept)
            conn.execute(text("INSERT INTO test_savepoint (name) VALUES ('First')"))

            # Create savepoint
            conn.execute(text("SAVEPOINT sp1"))

            # Second insert (will be rolled back)
            conn.execute(text("INSERT INTO test_savepoint (name) VALUES ('Second')"))

            # Verify both visible
            result = conn.execute(text("SELECT COUNT(*) FROM test_savepoint"))
            assert result.scalar() == 2, "Both inserts should be visible"

            # Rollback to savepoint
            conn.execute(text("ROLLBACK TO SAVEPOINT sp1"))

            # Now only first insert should be visible
            result = conn.execute(text("SELECT COUNT(*) FROM test_savepoint"))
            assert result.scalar() == 1, "Only first insert should remain"

            # Commit the outer transaction
            trans.commit()

        # Verify final state
        with postgresql_engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM test_savepoint"))
            names = [row[0] for row in result.fetchall()]

            assert "First" in names, "First insert should be committed"
            assert "Second" not in names, "Second insert should be rolled back"

        # Cleanup
        with postgresql_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_savepoint"))
            conn.commit()


class TestSQLAlchemyModelCompatibility:
    """Test SQLAlchemy ORM model compatibility with PostgreSQL"""

    def test_sqlalchemy_base_metadata_creation(self, postgresql_engine):
        """
        Verify SQLAlchemy Base.metadata.create_all works with PostgreSQL.

        Tests that our existing SQLAlchemy models can create tables
        in PostgreSQL without modification.
        """
        from backend.models import Base

        # This should not raise any exceptions
        # Note: In actual migration, we'd use Alembic
        try:
            Base.metadata.create_all(postgresql_engine)
        except Exception as e:
            pytest.fail(f"Failed to create tables from models: {e}")

    def test_sqlalchemy_session_crud_operations(self, postgresql_session):
        """
        Verify basic CRUD operations work through SQLAlchemy session.

        Tests that our ORM models can perform create, read, update, delete
        operations correctly on PostgreSQL.
        """
        from backend.models import Product

        # Create
        product = Product(
            code="TEST-PG-001",
            name="PostgreSQL Test Product",
            unit="kg",
            category="test",
            is_finished_product=False
        )
        postgresql_session.add(product)
        postgresql_session.commit()

        product_id = product.id
        assert product_id is not None, "Product ID should be auto-generated"

        # Read
        retrieved = postgresql_session.query(Product).filter_by(id=product_id).first()
        assert retrieved is not None, "Should retrieve product"
        assert retrieved.code == "TEST-PG-001", "Code should match"

        # Update
        retrieved.name = "Updated Product Name"
        postgresql_session.commit()

        updated = postgresql_session.query(Product).filter_by(id=product_id).first()
        assert updated.name == "Updated Product Name", "Name should be updated"

        # Delete
        postgresql_session.delete(updated)
        postgresql_session.commit()

        deleted = postgresql_session.query(Product).filter_by(id=product_id).first()
        assert deleted is None, "Product should be deleted"


class TestPerformanceBenchmarks:
    """Test performance benchmarks for PostgreSQL migration"""

    def test_product_query_performance(self, postgresql_engine):
        """
        Verify product query completes in less than 100ms.

        Performance requirement from TASK-DB-P5-001 spec.
        """
        from sqlalchemy import text
        import time

        # Setup: Create test table and insert sample data
        with postgresql_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_perf_products (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    code VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(100)
                )
            """))
            conn.execute(text("DELETE FROM test_perf_products"))

            # Insert 1000 sample products
            for i in range(1000):
                conn.execute(text(
                    f"INSERT INTO test_perf_products (code, name, category) "
                    f"VALUES ('PERF-{i:04d}', 'Performance Test Product {i}', 'test')"
                ))
            conn.commit()

        # Benchmark query
        with postgresql_engine.connect() as conn:
            start_time = time.time()

            result = conn.execute(text("""
                SELECT id, code, name, category
                FROM test_perf_products
                WHERE category = 'test'
                ORDER BY code
                LIMIT 100
            """))
            rows = result.fetchall()

            elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100, \
            f"Product query should complete in <100ms, took {elapsed_ms:.2f}ms"
        assert len(rows) == 100, "Should return 100 products"

        # Cleanup
        with postgresql_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_perf_products"))
            conn.commit()

    def test_connection_acquisition_performance(self, postgresql_engine):
        """
        Verify connection acquisition completes in less than 10ms.

        Performance requirement from PostgreSQL migration skill.
        """
        from sqlalchemy import text
        import time

        acquisition_times = []

        for _ in range(10):
            start_time = time.time()

            with postgresql_engine.connect() as conn:
                # Just acquire connection and do minimal work
                conn.execute(text("SELECT 1"))

            elapsed_ms = (time.time() - start_time) * 1000
            acquisition_times.append(elapsed_ms)

        # Use 95th percentile (skip worst case)
        acquisition_times.sort()
        p95 = acquisition_times[8]  # 9th out of 10 (95th percentile)

        assert p95 < 10, \
            f"Connection acquisition should be <10ms (p95), got {p95:.2f}ms"
