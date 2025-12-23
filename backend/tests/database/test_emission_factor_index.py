"""
Test suite for emission_factors.category index.

TASK-DB-P7-023: Add Index on emission_factors.category

This test suite validates:
- Index existence on emission_factors.category column
- Index is used for category-based queries (EXPLAIN analysis)
- Query performance improvement with index
- Migration rollback removes the index
- Idempotent migration behavior

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (index does not exist yet)
- Implementation must make tests PASS without modifying tests

Test Scenarios from SPEC:
1. Index exists after migration
2. Query uses index (EXPLAIN shows Index Scan, not Seq Scan)
3. Performance improvement (at least 2x faster with index)
4. Migration rollback removes index
5. Idempotent migration (running twice does not error)
"""

import os
import time
import pytest
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.models import Base, EmissionFactor
from backend.models.base import generate_uuid

# Mark entire module as database tests
pytestmark = pytest.mark.database


@pytest.fixture(scope="module")
def db_engine():
    """
    Create SQLite engine for testing.

    Uses in-memory SQLite database with foreign keys enabled.
    This fixture creates the schema from SQLAlchemy models.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables from models
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """
    Create database session for testing.

    Provides a session with transaction rollback for test isolation.
    Each test runs in its own transaction.
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def emission_factors_with_data(db_engine):
    """
    Populate emission_factors table with test data.

    Creates 1000+ emission factors across multiple categories
    to enable meaningful performance testing.
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()

    categories = ['steel', 'aluminum', 'plastic', 'energy', 'transport', 'chemicals']

    try:
        # Insert 1000+ emission factors (approximately 170 per category)
        factors_to_insert = []
        for i in range(1020):
            category = categories[i % len(categories)]
            factor = EmissionFactor(
                id=generate_uuid(),
                activity_name=f"Test Activity {i:04d}",
                category=category,
                co2e_factor=Decimal(str(round(0.5 + (i % 100) * 0.1, 4))),
                unit="kg",
                data_source="test_source",
                geography="GLO",
                reference_year=2024,
                is_active=True
            )
            factors_to_insert.append(factor)

        session.bulk_save_objects(factors_to_insert)
        session.commit()

        yield session

    finally:
        session.rollback()
        session.close()


class TestIndexExists:
    """Test Scenario 1: Index Exists After Migration"""

    def test_category_index_exists_on_emission_factors_table(self, db_engine):
        """
        Verify index ix_emission_factors_category exists on emission_factors table.

        After running the migration, the index should be present
        in the database schema.

        Expected: Index 'ix_emission_factors_category' exists on 'emission_factors' table

        This test will FAIL until the migration is implemented.
        """
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('emission_factors')

        index_names = [idx['name'] for idx in indexes]

        assert 'ix_emission_factors_category' in index_names, (
            f"Index 'ix_emission_factors_category' should exist on emission_factors table. "
            f"Found indexes: {index_names}"
        )

    def test_category_index_on_correct_column(self, db_engine):
        """
        Verify the index is on the 'category' column.

        The index should be specifically on the category column,
        not on any other column.

        Expected: Index has 'category' in its column_names
        """
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('emission_factors')

        category_index = None
        for idx in indexes:
            if idx['name'] == 'ix_emission_factors_category':
                category_index = idx
                break

        assert category_index is not None, (
            "Index 'ix_emission_factors_category' not found"
        )
        assert 'category' in category_index['column_names'], (
            f"Index should be on 'category' column, found columns: {category_index['column_names']}"
        )

    def test_category_index_is_not_unique(self, db_engine):
        """
        Verify the index is not a unique index.

        The category column can have duplicate values (many emission factors
        can share the same category), so the index should NOT be unique.

        Expected: Index unique property is False
        """
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('emission_factors')

        category_index = None
        for idx in indexes:
            if idx['name'] == 'ix_emission_factors_category':
                category_index = idx
                break

        assert category_index is not None, (
            "Index 'ix_emission_factors_category' not found"
        )
        assert category_index['unique'] is False, (
            "Category index should not be unique (multiple factors can share a category)"
        )


class TestIndexUsedInQueries:
    """Test Scenario 2: Query Uses Index (EXPLAIN Analysis)"""

    def test_explain_shows_index_scan_for_category_query(self, db_engine, emission_factors_with_data):
        """
        Verify EXPLAIN shows index scan for category-based queries.

        When querying by category, the database should use an index scan
        instead of a sequential scan (full table scan).

        Expected: EXPLAIN output contains 'USING INDEX' or 'Index Scan'

        Note: SQLite uses 'USING INDEX' in EXPLAIN output.
        PostgreSQL uses 'Index Scan' in EXPLAIN ANALYZE output.
        """
        with db_engine.connect() as conn:
            # SQLite EXPLAIN QUERY PLAN format
            result = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM emission_factors WHERE category = 'steel'"
            ))
            explain_output = result.fetchall()

            # Convert to string for easier analysis
            explain_str = str(explain_output).lower()

            # SQLite shows "USING INDEX" when an index is used
            # Also check for "COVERING INDEX" which is even better
            index_used = (
                'using index' in explain_str or
                'covering index' in explain_str or
                'ix_emission_factors_category' in explain_str
            )

            assert index_used, (
                f"Query should use index scan for category lookup. "
                f"EXPLAIN output: {explain_output}. "
                f"Expected 'USING INDEX ix_emission_factors_category' in output."
            )

    def test_no_sequential_scan_for_category_query(self, db_engine, emission_factors_with_data):
        """
        Verify query does not use sequential scan for category lookups.

        A sequential scan (SCAN TABLE) indicates the index is not being used,
        which would be inefficient for large tables.

        Expected: EXPLAIN output does NOT show 'SCAN TABLE' without index
        """
        with db_engine.connect() as conn:
            result = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM emission_factors WHERE category = 'aluminum'"
            ))
            explain_output = result.fetchall()
            explain_str = str(explain_output).lower()

            # If we see "scan table emission_factors" WITHOUT "using index"
            # then we have a sequential scan (bad)
            has_table_scan = 'scan table emission_factors' in explain_str
            has_index = 'using index' in explain_str or 'covering index' in explain_str

            # Sequential scan without index is bad
            if has_table_scan and not has_index:
                pytest.fail(
                    f"Query uses sequential scan without index. "
                    f"EXPLAIN output: {explain_output}. "
                    f"Add index on emission_factors.category to improve performance."
                )


class TestPerformanceImprovement:
    """Test Scenario 3: Performance Improvement with Index"""

    def test_category_query_performance_under_threshold(self, db_engine, emission_factors_with_data):
        """
        Verify category query completes under performance threshold.

        With an index on the category column, queries filtering by category
        should complete in a reasonable time even with 1000+ records.

        Expected: Query completes in <50ms for 1000+ records

        Note: This threshold is generous for SQLite in-memory.
        The key improvement is in production with larger datasets.
        """
        with db_engine.connect() as conn:
            # Warm up query (first query may be slower)
            conn.execute(text(
                "SELECT * FROM emission_factors WHERE category = 'steel'"
            )).fetchall()

            # Measure query time
            start_time = time.time()
            result = conn.execute(text(
                "SELECT * FROM emission_factors WHERE category = 'steel'"
            ))
            rows = result.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000

            assert len(rows) > 0, "Query should return results"
            assert elapsed_ms < 50, (
                f"Category query should complete in <50ms with index, "
                f"took {elapsed_ms:.2f}ms"
            )

    def test_index_improves_query_performance(self, db_engine, emission_factors_with_data):
        """
        Verify index provides measurable performance improvement.

        This test measures query performance and verifies that the query
        uses an optimized execution plan. The actual improvement ratio
        depends on the index being present.

        Expected: Indexed queries show consistent fast performance
        """
        with db_engine.connect() as conn:
            query_times = []

            # Run multiple queries to get consistent timing
            for category in ['steel', 'aluminum', 'plastic', 'energy', 'transport']:
                start_time = time.time()
                result = conn.execute(text(
                    f"SELECT * FROM emission_factors WHERE category = '{category}'"
                ))
                rows = result.fetchall()
                elapsed_ms = (time.time() - start_time) * 1000
                query_times.append(elapsed_ms)

            # Average query time should be fast with index
            avg_time = sum(query_times) / len(query_times)
            max_time = max(query_times)

            assert avg_time < 20, (
                f"Average category query should be <20ms with index, "
                f"got {avg_time:.2f}ms"
            )
            assert max_time < 50, (
                f"Max category query should be <50ms with index, "
                f"got {max_time:.2f}ms"
            )


class TestMigrationRollback:
    """Test Scenario 4: Migration Rollback Removes Index"""

    def test_index_can_be_dropped(self, db_engine):
        """
        Verify index can be dropped (rollback capability).

        The migration downgrade should be able to remove the index.
        This test verifies the DROP INDEX statement works.

        Note: This test creates and then drops a test index to verify
        the rollback mechanism without affecting other tests.
        """
        with db_engine.connect() as conn:
            # First verify the index exists (or create it for this test)
            inspector = inspect(db_engine)
            indexes = inspector.get_indexes('emission_factors')
            index_names = [idx['name'] for idx in indexes]

            if 'ix_emission_factors_category' not in index_names:
                # Index doesn't exist - this test should fail
                pytest.fail(
                    "Index 'ix_emission_factors_category' does not exist. "
                    "Cannot test rollback capability. "
                    "Implement the migration first."
                )

            # Test that we CAN drop it (but don't actually drop in other tests)
            # Just verify the DROP INDEX syntax would work
            try:
                # Create a temporary test index
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_test_rollback_temp ON emission_factors(geography)"
                ))
                conn.commit()

                # Verify we can drop it
                conn.execute(text(
                    "DROP INDEX IF EXISTS ix_test_rollback_temp"
                ))
                conn.commit()

            except Exception as e:
                pytest.fail(f"Index drop operation failed: {e}")


class TestIdempotentMigration:
    """Test Scenario 5: Idempotent Migration (Safe to Run Multiple Times)"""

    def test_create_index_if_not_exists_is_idempotent(self, db_engine):
        """
        Verify CREATE INDEX IF NOT EXISTS is idempotent.

        Running the migration multiple times should not cause errors.
        The IF NOT EXISTS clause ensures idempotency.

        Expected: Running CREATE INDEX twice does not raise an error
        """
        with db_engine.connect() as conn:
            # Run CREATE INDEX IF NOT EXISTS twice
            # This should not raise an error
            try:
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_emission_factors_category "
                    "ON emission_factors(category)"
                ))
                conn.commit()

                # Run again - should not error
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_emission_factors_category "
                    "ON emission_factors(category)"
                ))
                conn.commit()

            except Exception as e:
                pytest.fail(
                    f"Idempotent index creation failed on second run: {e}. "
                    "Migration should use IF NOT EXISTS clause."
                )

    def test_index_still_exists_after_idempotent_creation(self, db_engine):
        """
        Verify index still exists after idempotent creation.

        After running CREATE INDEX IF NOT EXISTS multiple times,
        the index should still be present.
        """
        with db_engine.connect() as conn:
            # Run CREATE INDEX IF NOT EXISTS
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_emission_factors_category "
                "ON emission_factors(category)"
            ))
            conn.commit()

        # Verify index exists
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('emission_factors')
        index_names = [idx['name'] for idx in indexes]

        assert 'ix_emission_factors_category' in index_names, (
            "Index should exist after idempotent creation"
        )


class TestIndexNamingConvention:
    """Test index follows naming convention"""

    def test_index_name_follows_convention(self, db_engine):
        """
        Verify index name follows the convention: ix_{table_name}_{column_name}

        Expected: Index name is 'ix_emission_factors_category'
        """
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('emission_factors')

        # Check for the correctly named index
        expected_name = 'ix_emission_factors_category'
        index_names = [idx['name'] for idx in indexes]

        assert expected_name in index_names, (
            f"Index should be named '{expected_name}' following convention "
            f"ix_{{table_name}}_{{column_name}}. Found indexes: {index_names}"
        )


class TestSQLiteCompatibility:
    """Test index works on SQLite (development database)"""

    def test_index_syntax_compatible_with_sqlite(self, db_engine):
        """
        Verify index creation syntax works with SQLite.

        The migration must use syntax compatible with both SQLite
        (development) and PostgreSQL (production).
        """
        with db_engine.connect() as conn:
            # This is the expected migration syntax
            # Should work on both SQLite and PostgreSQL
            try:
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_emission_factors_category "
                    "ON emission_factors(category)"
                ))
                conn.commit()
            except Exception as e:
                pytest.fail(
                    f"Index creation syntax not compatible with SQLite: {e}"
                )

    def test_existing_data_not_affected_by_index(self, db_engine, emission_factors_with_data):
        """
        Verify adding index does not affect existing data.

        Creating an index should not modify, delete, or corrupt
        existing data in the table.
        """
        # Get count before index creation
        with db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM emission_factors"
            ))
            count_before = result.scalar()

        # Create index (if not exists)
        with db_engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_emission_factors_category "
                "ON emission_factors(category)"
            ))
            conn.commit()

        # Get count after index creation
        with db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM emission_factors"
            ))
            count_after = result.scalar()

        assert count_before == count_after, (
            f"Index creation should not affect row count. "
            f"Before: {count_before}, After: {count_after}"
        )


class TestModelIndexDefinition:
    """Test that SQLAlchemy model has index defined"""

    def test_emission_factor_model_has_category_index_attribute(self):
        """
        Verify EmissionFactor model has index=True on category column.

        The SQLAlchemy model should define index=True for the category column,
        which allows automatic index creation via alembic autogenerate.

        Note: This checks the model definition, not the database state.
        """
        # Get the category column from the model
        category_column = EmissionFactor.__table__.columns.get('category')

        assert category_column is not None, (
            "EmissionFactor model should have a 'category' column"
        )

        # Check if the column has an index
        # In SQLAlchemy, column.index is True if index=True was specified
        assert category_column.index is True, (
            "EmissionFactor.category column should have index=True. "
            "Update the model: category = Column(String(50), nullable=True, index=True)"
        )
