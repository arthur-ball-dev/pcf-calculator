"""
Test suite for emission factor sync to Brightway2.

Tests the sync_emission_factors() function to ensure:
1. All emission factors from SQLite are synced to Brightway2
2. Each factor has correct CO2e exchange with biosphere
3. Sync is idempotent (no duplicates on re-run)
4. Updates to database factors are reflected in Brightway2
5. Error handling for missing biosphere database

Following TDD methodology - tests written BEFORE implementation.

TASK-CALC-002: Sync Emission Factors to Brightway2
"""

import pytest
import brightway2 as bw
from sqlalchemy import text
from decimal import Decimal


@pytest.fixture(scope="function")
def clean_brightway_project():
    """
    Fixture to ensure clean Brightway2 state for each test.

    Assumes pcf_calculator project exists (from TASK-CALC-001).
    Cleans the pcf_emission_factors database before each test.
    """
    import time

    # Set current project
    if "pcf_calculator" not in bw.projects:
        # Initialize if not exists (dependency on CALC-001)
        from backend.calculator.brightway_setup import initialize_brightway
        initialize_brightway()

    bw.projects.set_current("pcf_calculator")

    # Clean pcf_emission_factors database if it exists
    if "pcf_emission_factors" in bw.databases:
        ef_db = bw.Database("pcf_emission_factors")
        ef_db.delete()
        time.sleep(0.1)  # Allow filesystem to sync

    # Recreate empty database
    ef_db = bw.Database("pcf_emission_factors")
    ef_db.write({})

    yield

    # Cleanup after test
    if "pcf_emission_factors" in bw.databases:
        ef_db = bw.Database("pcf_emission_factors")
        ef_db.delete()


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to provide database session for tests.
    """
    from backend.database.connection import db_context

    with db_context() as session:
        yield session


@pytest.fixture(scope="function")
def seed_emission_factors(db_session):
    """
    Fixture to ensure emission factors are loaded in SQLite database.

    Assumes seed_data.py has been run (TASK-DATA-003).
    Verifies 20+ emission factors exist.
    """
    # Verify emission factors exist
    count = db_session.execute(text("SELECT COUNT(*) FROM emission_factors")).scalar()

    if count == 0:
        pytest.skip("Emission factors not loaded. Run: python backend/scripts/seed_data.py")

    return count


class TestSyncAllEmissionFactors:
    """Test that all emission factors from database are synced to Brightway2."""

    def test_sync_all_factors_from_database(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Scenario 1: Sync All Emission Factors from Database

        Given: Database has 20+ emission factors loaded
        When: sync_emission_factors() is called
        Then: All factors are synced to Brightway2 "pcf_emission_factors" database
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get count from database
        count_before = db_session.execute(
            text("SELECT COUNT(*) FROM emission_factors")
        ).scalar()
        assert count_before >= 20, f"Expected >=20 emission factors, got {count_before}"

        # Sync emission factors
        result = sync_emission_factors(db_session=db_session)

        # Verify sync result
        assert "synced_count" in result, "Result should contain 'synced_count' key"
        assert result["synced_count"] == count_before

        # Verify Brightway2 database
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")

        assert len(ef_db) == count_before, f"Expected {count_before} activities in Brightway2, got {len(ef_db)}"

    def test_all_factors_accessible_by_name(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that all synced factors are accessible by activity name.

        Given: Emission factors synced to Brightway2
        When: Accessing activities by name
        Then: All activities are findable and have correct names
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get expected names from database
        rows = db_session.execute(
            text("SELECT activity_name FROM emission_factors ORDER BY activity_name")
        ).fetchall()
        expected_names = [row[0] for row in rows]

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify all activities exist in Brightway2
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")

        for name in expected_names:
            # Should be able to get activity by code (using name as code)
            activity = ef_db.get(name)
            assert activity is not None, f"Activity '{name}' not found in Brightway2"
            assert activity["name"] == name


class TestEmissionFactorCO2eExchange:
    """Test that each emission factor has correct CO2e exchange."""

    def test_cotton_factor_has_correct_exchange(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Scenario 2: Emission Factor Has Correct CO2e Exchange

        Given: Cotton emission factor exists in database
        When: sync_emission_factors() is called
        Then: Cotton activity has biosphere exchange with correct CO2e amount
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get cotton emission factor from database
        cotton_row = db_session.execute(
            text("""
                SELECT activity_name, co2e_factor, unit
                FROM emission_factors
                WHERE activity_name = 'cotton'
            """)
        ).fetchone()

        if cotton_row is None:
            pytest.skip("Cotton emission factor not in database")

        expected_co2e = float(cotton_row[1])
        expected_unit = cotton_row[2]

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify cotton activity in Brightway2
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        cotton = ef_db.get("cotton")

        assert cotton is not None, "Cotton activity not found"
        assert cotton["name"] == "cotton"
        assert cotton["unit"] == expected_unit

        # Check biosphere exchange
        exchanges = list(cotton.exchanges())
        assert len(exchanges) >= 1, "Expected at least one exchange (biosphere)"

        # Find CO2e exchange (should be first/only biosphere exchange)
        co2_exchange = None
        for ex in exchanges:
            if ex["type"] == "biosphere":
                co2_exchange = ex
                break

        assert co2_exchange is not None, "No biosphere exchange found"
        assert co2_exchange["amount"] == expected_co2e, \
            f"Expected CO2e amount {expected_co2e}, got {co2_exchange['amount']}"

    def test_all_factors_have_biosphere_exchanges(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that ALL emission factors have biosphere exchanges.

        Given: Multiple emission factors synced
        When: Checking each activity
        Then: Each activity has exactly one biosphere exchange
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get all factors from database
        rows = db_session.execute(
            text("SELECT activity_name, co2e_factor FROM emission_factors")
        ).fetchall()

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify each factor has biosphere exchange
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")

        for name, expected_amount in rows:
            activity = ef_db.get(name)
            assert activity is not None, f"Activity '{name}' not found"

            exchanges = [ex for ex in activity.exchanges() if ex["type"] == "biosphere"]
            assert len(exchanges) >= 1, f"Activity '{name}' has no biosphere exchange"

            # Check amount matches database
            assert exchanges[0]["amount"] == float(expected_amount), \
                f"Activity '{name}' CO2e mismatch"


class TestIdempotentSync:
    """Test that sync is idempotent (no duplicates on re-run)."""

    def test_running_sync_twice_no_duplicates(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Scenario 3: Idempotent Sync (No Duplicates)

        Given: Emission factors already synced
        When: sync_emission_factors() is called again
        Then: No duplicate activities created, same count returned
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # First sync
        result1 = sync_emission_factors(db_session=db_session)
        synced_count = result1["synced_count"]

        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        count_after_first = len(ef_db)

        # Second sync
        result2 = sync_emission_factors(db_session=db_session)

        # Verify counts
        assert result2["synced_count"] == synced_count, \
            "Second sync should return same count"

        ef_db = bw.Database("pcf_emission_factors")
        count_after_second = len(ef_db)

        assert count_after_second == count_after_first, \
            f"Expected {count_after_first} activities, got {count_after_second} (duplicates created)"

    def test_multiple_syncs_preserve_data(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that multiple syncs preserve data integrity.

        Given: Emission factors synced multiple times
        When: Checking activity data
        Then: Data remains consistent across syncs
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get reference data
        cotton_row = db_session.execute(
            text("SELECT co2e_factor FROM emission_factors WHERE activity_name = 'cotton'")
        ).fetchone()

        if cotton_row is None:
            pytest.skip("Cotton not in database")

        expected_co2e = float(cotton_row[0])

        # Sync three times
        for i in range(3):
            sync_emission_factors(db_session=db_session)

            # Verify cotton data after each sync
            bw.projects.set_current("pcf_calculator")
            ef_db = bw.Database("pcf_emission_factors")
            cotton = ef_db.get("cotton")

            exchanges = [ex for ex in cotton.exchanges() if ex["type"] == "biosphere"]
            assert exchanges[0]["amount"] == expected_co2e, \
                f"Cotton CO2e changed on sync {i+1}"


class TestSyncUpdatesModifiedFactors:
    """Test that sync updates emission factors modified in database."""

    def test_sync_reflects_database_updates(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Scenario 4: Sync Updates Modified Emission Factors

        Given: Emission factors synced, then cotton factor updated in database
        When: sync_emission_factors() is called again
        Then: Brightway2 cotton activity reflects new CO2e value
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Initial sync
        sync_emission_factors(db_session=db_session)

        # Get original cotton value
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        cotton = ef_db.get("cotton")
        exchanges = [ex for ex in cotton.exchanges() if ex["type"] == "biosphere"]
        original_amount = exchanges[0]["amount"]

        # Update cotton emission factor in database
        new_co2e_value = original_amount + 1.0  # Increase by 1.0
        db_session.execute(
            text("""
                UPDATE emission_factors
                SET co2e_factor = :new_value
                WHERE activity_name = 'cotton'
            """),
            {"new_value": new_co2e_value}
        )
        db_session.commit()

        # Sync again
        sync_emission_factors(db_session=db_session)

        # Verify updated value in Brightway2
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        cotton = ef_db.get("cotton")

        exchanges = [ex for ex in cotton.exchanges() if ex["type"] == "biosphere"]
        updated_amount = exchanges[0]["amount"]

        assert updated_amount == new_co2e_value, \
            f"Expected updated CO2e {new_co2e_value}, got {updated_amount}"
        assert updated_amount != original_amount, \
            "Cotton CO2e should have changed"


class TestErrorHandling:
    """Test error handling for missing dependencies."""

    def test_error_if_biosphere_missing(self, clean_brightway_project, db_session):
        """
        Scenario 5: Error Handling for Missing Biosphere Flows

        Given: Biosphere3 database potentially missing
        When: sync_emission_factors(validate_biosphere=True) is called
        Then: Appropriate error raised if biosphere not available
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Check if biosphere3 exists
        bw.projects.set_current("pcf_calculator")

        if "biosphere3" not in bw.databases:
            # Should raise error when validate_biosphere=True
            with pytest.raises(Exception) as exc_info:
                sync_emission_factors(db_session=db_session, validate_biosphere=True)

            assert "biosphere" in str(exc_info.value).lower(), \
                "Error message should mention biosphere"
        else:
            # If biosphere exists, validation should pass
            result = sync_emission_factors(db_session=db_session, validate_biosphere=True)
            assert result["synced_count"] > 0

    def test_error_if_no_emission_factors_in_db(self, clean_brightway_project, db_session):
        """
        Test appropriate handling when no emission factors in database.

        Given: Empty emission_factors table
        When: sync_emission_factors() is called
        Then: Returns synced_count=0, no errors
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Clear all emission factors
        db_session.execute(text("DELETE FROM emission_factors"))
        db_session.commit()

        # Sync should handle gracefully
        result = sync_emission_factors(db_session=db_session)

        assert result["synced_count"] == 0, "Should sync 0 factors"

        # Brightway2 database should be empty
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        assert len(ef_db) == 0, "Brightway2 database should be empty"


class TestSyncMetadata:
    """Test that metadata and attributes are synced correctly."""

    def test_activity_attributes_synced(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that activity attributes (unit, location, type) are synced.

        Given: Emission factors with various attributes
        When: Syncing to Brightway2
        Then: All attributes are correctly set
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get sample factor with metadata
        row = db_session.execute(
            text("""
                SELECT activity_name, unit, data_source
                FROM emission_factors
                WHERE activity_name = 'cotton'
            """)
        ).fetchone()

        if row is None:
            pytest.skip("Cotton not in database")

        expected_name, expected_unit, expected_source = row

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify attributes
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        cotton = ef_db.get("cotton")

        assert cotton["name"] == expected_name
        assert cotton["unit"] == expected_unit
        assert cotton["type"] == "process", "Should be process type"
        assert "location" in cotton, "Should have location attribute"

    def test_sync_result_includes_statistics(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that sync result includes useful statistics.

        Given: Emission factors synced
        When: Checking return value
        Then: Contains synced_count and other metadata
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        result = sync_emission_factors(db_session=db_session)

        # Verify result structure
        assert isinstance(result, dict), "Result should be dictionary"
        assert "synced_count" in result, "Should contain synced_count"
        assert isinstance(result["synced_count"], int), "synced_count should be integer"
        assert result["synced_count"] > 0, "Should have synced some factors"


class TestSyncLogging:
    """Test that sync operations log appropriately."""

    def test_sync_logs_operations(self, clean_brightway_project, db_session, seed_emission_factors, caplog):
        """
        Test that sync_emission_factors() logs appropriate messages.

        Given: Fresh Brightway2 state
        When: sync_emission_factors() is called
        Then: INFO level log messages are generated
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors
        import logging

        # Set logging level
        caplog.set_level(logging.INFO)

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify logging occurred
        assert len(caplog.records) > 0, "Expected log messages during sync"

        # Check log content
        log_text = " ".join([record.message for record in caplog.records]).lower()
        assert "sync" in log_text or "emission" in log_text, \
            "Log should mention sync or emission factors"


class TestSyncCoverage:
    """Test edge cases and coverage requirements."""

    def test_sync_handles_all_units(self, clean_brightway_project, db_session, seed_emission_factors):
        """
        Test that sync handles different unit types correctly.

        Given: Emission factors with various units (kg, kWh, tkm, L)
        When: Syncing to Brightway2
        Then: All units are preserved correctly
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Get factors with different units
        rows = db_session.execute(
            text("SELECT activity_name, unit FROM emission_factors")
        ).fetchall()

        unit_map = {name: unit for name, unit in rows}

        # Sync
        sync_emission_factors(db_session=db_session)

        # Verify all units preserved
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")

        for name, expected_unit in unit_map.items():
            activity = ef_db.get(name)
            assert activity["unit"] == expected_unit, \
                f"Unit mismatch for {name}: expected {expected_unit}, got {activity['unit']}"

    def test_sync_without_session_parameter(self, clean_brightway_project, seed_emission_factors):
        """
        Test that sync works when db_session parameter is None.

        Given: No db_session provided
        When: sync_emission_factors() is called
        Then: Creates own session and syncs successfully
        """
        from backend.calculator.emission_factor_sync import sync_emission_factors

        # Call without session parameter
        result = sync_emission_factors(db_session=None)

        assert "synced_count" in result
        assert result["synced_count"] > 0, "Should sync factors even without session parameter"
