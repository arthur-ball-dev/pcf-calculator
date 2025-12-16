"""
Test suite for data_sources seeding functionality.

TASK-DATA-P7-001: Seed Data Sources Table

This test suite validates:
- Fresh database seeding creates all 3 data sources (EPA, DEFRA, Exiobase)
- Idempotency: calling seed multiple times doesn't create duplicates
- Partial seeding: adds missing sources without duplicating existing ones
- Data source fields are populated correctly with expected values
- Verification function correctly validates seeded state

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (data_sources table is empty)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.models import Base, DataSource


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="function")
def empty_db_session(db_engine):
    """
    Create database session with empty data_sources table.

    This fixture represents a fresh database with no data sources seeded.
    Used for testing initial seeding behavior.
    """
    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def seeded_db_session(db_engine):
    """
    Create database session with data_sources already seeded.

    This fixture represents a database where seed_data_sources has
    already been called. Used for testing idempotency.
    """
    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    # Pre-seed with all 3 data sources
    from backend.database.seeds.data_sources import seed_data_sources
    seed_data_sources(session, skip_existing=False)

    yield session

    session.close()


@pytest.fixture(scope="function")
def partial_db_session(db_engine):
    """
    Create database session with only EPA data source seeded.

    This fixture represents a partial seeding state where only
    one of the three expected data sources exists. Used for testing
    incremental seeding behavior.
    """
    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    # Pre-seed with only EPA
    epa_source = DataSource(
        name="EPA GHG Emission Factors Hub",
        source_type="file",
        base_url="https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        api_key_env_var=None,
        sync_frequency="biweekly",
        is_active=True,
    )
    session.add(epa_source)
    session.commit()

    yield session

    session.close()


# ============================================================================
# Test Scenario 1: Happy Path - Fresh Database
# ============================================================================

class TestSeedDataSourcesFreshDatabase:
    """Test seeding data sources into an empty database."""

    def test_seed_data_sources_creates_all_sources(self, empty_db_session: Session):
        """
        Input: Empty data_sources table
        Action: Call seed_data_sources(session)
        Expected:
            - Returns 3 (number created)
            - data_sources table has 3 records
            - Records match SEED_DATA_SOURCES names
        """
        from backend.database.seeds.data_sources import seed_data_sources

        count = seed_data_sources(empty_db_session)

        assert count == 3, f"Expected 3 data sources created, got {count}"
        sources = empty_db_session.query(DataSource).all()
        assert len(sources) == 3, f"Expected 3 sources in DB, got {len(sources)}"

        names = {s.name for s in sources}
        assert "EPA GHG Emission Factors Hub" in names
        assert "DEFRA Conversion Factors" in names
        assert "Exiobase" in names

    def test_seed_data_sources_returns_count(self, empty_db_session: Session):
        """Test that seed_data_sources returns the count of created records."""
        from backend.database.seeds.data_sources import seed_data_sources

        count = seed_data_sources(empty_db_session)

        assert isinstance(count, int)
        assert count == 3


# ============================================================================
# Test Scenario 2: Idempotency - Already Seeded
# ============================================================================

class TestSeedDataSourcesIdempotency:
    """Test that seeding is idempotent and doesn't create duplicates."""

    def test_seed_data_sources_skips_existing(self, seeded_db_session: Session):
        """
        Input: data_sources table already has 3 records
        Action: Call seed_data_sources(session, skip_existing=True)
        Expected:
            - Returns 0 (no new records created)
            - Table still has exactly 3 records
            - No duplicate entries
        """
        from backend.database.seeds.data_sources import seed_data_sources

        count = seed_data_sources(seeded_db_session, skip_existing=True)

        assert count == 0, f"Expected 0 new records, got {count}"
        sources = seeded_db_session.query(DataSource).all()
        assert len(sources) == 3, f"Expected 3 sources, got {len(sources)}"

    def test_seed_data_sources_no_duplicates_after_multiple_calls(
        self, empty_db_session: Session
    ):
        """Test that calling seed multiple times doesn't create duplicates."""
        from backend.database.seeds.data_sources import seed_data_sources

        # First call
        count1 = seed_data_sources(empty_db_session, skip_existing=True)
        assert count1 == 3

        # Second call
        count2 = seed_data_sources(empty_db_session, skip_existing=True)
        assert count2 == 0

        # Third call
        count3 = seed_data_sources(empty_db_session, skip_existing=True)
        assert count3 == 0

        # Total should still be 3
        total = empty_db_session.query(DataSource).count()
        assert total == 3


# ============================================================================
# Test Scenario 3: Partial Seeding
# ============================================================================

class TestSeedDataSourcesPartialSeeding:
    """Test incremental seeding when some sources already exist."""

    def test_seed_data_sources_handles_partial(self, partial_db_session: Session):
        """
        Input: data_sources table has 1 record (EPA only)
        Action: Call seed_data_sources(session, skip_existing=True)
        Expected:
            - Returns 2 (DEFRA and Exiobase created)
            - Table now has 3 records total
        """
        from backend.database.seeds.data_sources import seed_data_sources

        # Pre-condition: EPA already exists
        existing = partial_db_session.query(DataSource).filter(
            DataSource.name == "EPA GHG Emission Factors Hub"
        ).first()
        assert existing is not None, "Pre-condition: EPA should exist"

        count = seed_data_sources(partial_db_session, skip_existing=True)

        assert count == 2, f"Expected 2 new sources created, got {count}"
        sources = partial_db_session.query(DataSource).all()
        assert len(sources) == 3, f"Expected 3 total sources, got {len(sources)}"

        # Verify all three exist
        names = {s.name for s in sources}
        assert "EPA GHG Emission Factors Hub" in names
        assert "DEFRA Conversion Factors" in names
        assert "Exiobase" in names


# ============================================================================
# Test Scenario 4: Data Source Record Validation
# ============================================================================

class TestSeedDataSourceRecordValidation:
    """Test that seeded records have correct field values."""

    def test_seeded_epa_data_source_has_correct_fields(
        self, seeded_db_session: Session
    ):
        """
        Input: Seeded database
        Action: Query EPA data source
        Expected:
            - id is valid UUID hex string (32 chars)
            - name matches exactly
            - source_type is "file"
            - base_url matches EPA URL
            - sync_frequency is "biweekly"
            - is_active is True
            - created_at is not None
        """
        epa = seeded_db_session.query(DataSource).filter(
            DataSource.name == "EPA GHG Emission Factors Hub"
        ).first()

        assert epa is not None, "EPA data source should exist"
        assert len(epa.id) == 32, f"Expected 32-char UUID hex, got {len(epa.id)}"
        assert epa.name == "EPA GHG Emission Factors Hub"
        assert epa.source_type == "file"
        assert "epa.gov" in epa.base_url
        assert epa.sync_frequency == "biweekly"
        assert epa.is_active is True
        assert epa.created_at is not None

    def test_seeded_defra_data_source_has_correct_fields(
        self, seeded_db_session: Session
    ):
        """Test DEFRA data source has correct field values."""
        defra = seeded_db_session.query(DataSource).filter(
            DataSource.name == "DEFRA Conversion Factors"
        ).first()

        assert defra is not None, "DEFRA data source should exist"
        assert len(defra.id) == 32
        assert defra.name == "DEFRA Conversion Factors"
        assert defra.source_type == "file"
        assert "gov.uk" in defra.base_url
        assert defra.sync_frequency == "biweekly"
        assert defra.is_active is True
        assert defra.created_at is not None

    def test_seeded_exiobase_data_source_has_correct_fields(
        self, seeded_db_session: Session
    ):
        """Test Exiobase data source has correct field values."""
        exiobase = seeded_db_session.query(DataSource).filter(
            DataSource.name == "Exiobase"
        ).first()

        assert exiobase is not None, "Exiobase data source should exist"
        assert len(exiobase.id) == 32
        assert exiobase.name == "Exiobase"
        assert exiobase.source_type == "file"
        assert "zenodo.org" in exiobase.base_url
        assert exiobase.sync_frequency == "monthly"  # Different from others
        assert exiobase.is_active is True
        assert exiobase.created_at is not None

    def test_all_data_sources_have_unique_ids(self, seeded_db_session: Session):
        """Test that all seeded data sources have unique UUIDs."""
        sources = seeded_db_session.query(DataSource).all()
        ids = [s.id for s in sources]

        assert len(ids) == len(set(ids)), "All data source IDs should be unique"


# ============================================================================
# Test Scenario 5: Verification Function
# ============================================================================

class TestVerifyDataSources:
    """Test the verification function for seeded data sources."""

    def test_verify_data_sources_returns_true_when_seeded(
        self, seeded_db_session: Session
    ):
        """Test verification passes when all sources are seeded."""
        from backend.database.seeds.data_sources import verify_data_sources

        result = verify_data_sources(seeded_db_session)

        assert result is True, "Verification should pass for seeded database"

    def test_verify_data_sources_returns_false_when_empty(
        self, empty_db_session: Session
    ):
        """Test verification fails when database is empty."""
        from backend.database.seeds.data_sources import verify_data_sources

        result = verify_data_sources(empty_db_session)

        assert result is False, "Verification should fail for empty database"

    def test_verify_data_sources_returns_false_when_partial(
        self, partial_db_session: Session
    ):
        """Test verification fails when only some sources exist."""
        from backend.database.seeds.data_sources import verify_data_sources

        result = verify_data_sources(partial_db_session)

        assert result is False, "Verification should fail for partial seeding"


# ============================================================================
# Test Scenario 6: Startup Integration
# ============================================================================

class TestStartupSeeding:
    """Test that seeding works correctly in startup context."""

    def test_seed_on_fresh_database_via_context(self, db_engine):
        """
        Test seeding via db_context-like pattern for startup integration.

        This mimics how seeding would be called in the startup event.
        """
        from backend.database.seeds.data_sources import seed_data_sources

        Base.metadata.create_all(db_engine)
        SessionLocal = sessionmaker(bind=db_engine)

        # Simulate startup seeding
        session = SessionLocal()
        try:
            count = seed_data_sources(session, skip_existing=True)
            session.commit()
        finally:
            session.close()

        # Verify in new session
        verify_session = SessionLocal()
        try:
            sources = verify_session.query(DataSource).all()
            assert len(sources) == 3
            assert count == 3
        finally:
            verify_session.close()

    def test_seed_multiple_startups_remain_idempotent(self, db_engine):
        """
        Test that multiple simulated startups don't create duplicates.

        This ensures the skip_existing=True parameter works correctly
        across multiple application restarts.
        """
        from backend.database.seeds.data_sources import seed_data_sources

        Base.metadata.create_all(db_engine)
        SessionLocal = sessionmaker(bind=db_engine)

        # First startup
        session1 = SessionLocal()
        count1 = seed_data_sources(session1, skip_existing=True)
        session1.close()

        # Second startup
        session2 = SessionLocal()
        count2 = seed_data_sources(session2, skip_existing=True)
        session2.close()

        # Third startup
        session3 = SessionLocal()
        count3 = seed_data_sources(session3, skip_existing=True)
        sources = session3.query(DataSource).all()
        session3.close()

        assert count1 == 3
        assert count2 == 0
        assert count3 == 0
        assert len(sources) == 3
