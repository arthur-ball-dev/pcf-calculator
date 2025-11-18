"""
Test suite for Brightway2 initialization.

Tests the initialize_brightway() function to ensure:
1. Brightway2 project "pcf_calculator" is created
2. Biosphere3 database is installed
3. IPCC 2021 GWP100 method is available
4. Custom "pcf_emission_factors" database is created
5. Initialization is idempotent (safe to run multiple times)

Following TDD methodology - tests written BEFORE implementation.
"""

import pytest
import brightway2 as bw
import shutil
import os
from pathlib import Path


@pytest.fixture(scope="function")
def clean_brightway_projects():
    """
    Fixture to clean up Brightway2 projects before and after each test.

    Uses retry logic and filesystem sync delays to prevent race conditions
    with Brightway2's asynchronous file operations (whoosh indexing, pickle writes).
    """
    import time

    # Clean before test with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if "pcf_calculator" in bw.projects:
                bw.projects.delete_project("pcf_calculator", delete_dir=True)
            break
        except (FileNotFoundError, PermissionError):
            if attempt < max_retries - 1:
                time.sleep(1.0)  # Wait for file handles to release

    # Wait for filesystem sync before starting test
    time.sleep(0.5)

    yield

    # Clean after test with retry logic
    for attempt in range(max_retries):
        try:
            if "pcf_calculator" in bw.projects:
                bw.projects.delete_project("pcf_calculator", delete_dir=True)
            break
        except (FileNotFoundError, PermissionError):
            if attempt < max_retries - 1:
                time.sleep(1.0)
            else:
                # Last attempt - force cleanup with shutil
                import shutil
                for path in Path(bw.projects.dir).glob("pcf_calculator.*"):
                    shutil.rmtree(path, ignore_errors=True)



class TestBrightwayProjectCreation:
    """Test that Brightway2 project is created correctly."""

    def test_project_created(self, clean_brightway_projects):
        """
        Scenario 1: Brightway2 Project Created

        Given: No existing "pcf_calculator" project
        When: initialize_brightway() is called
        Then: Project "pcf_calculator" exists and is set as current
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # Verify project doesn't exist yet
        assert "pcf_calculator" not in bw.projects

        # Initialize
        result = initialize_brightway()

        # Verify project was created
        assert "pcf_calculator" in bw.projects

        # Verify project is set as current
        bw.projects.set_current("pcf_calculator")
        assert bw.projects.current == "pcf_calculator"

        # Verify function returns True
        assert result is True


class TestBiosphere3Installation:
    """Test that biosphere3 database is installed."""

    def test_biosphere3_installed(self, clean_brightway_projects):
        """
        Scenario 2: Biosphere3 Database Installed

        Given: Fresh Brightway2 project
        When: initialize_brightway() is called
        Then: "biosphere3" database exists and contains biosphere flows
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # Initialize
        initialize_brightway()

        # Set current project
        bw.projects.set_current("pcf_calculator")

        # Verify biosphere3 database exists
        assert "biosphere3" in bw.databases

        # Verify database contains flows
        bio_db = bw.Database("biosphere3")
        assert len(bio_db) > 0, "biosphere3 database should contain flows"

        # Verify it contains a substantial number of flows (typically >1000)
        assert len(bio_db) > 1000, f"Expected >1000 biosphere flows, got {len(bio_db)}"


class TestIPCCMethodAvailability:
    """Test that IPCC 2021 GWP100 method is available."""

    def test_ipcc_2021_method_available(self, clean_brightway_projects):
        """
        Scenario 3: IPCC 2021 Method Available

        Given: Fresh Brightway2 project with bw2setup complete
        When: initialize_brightway() is called
        Then: IPCC 2021 GWP100 impact assessment method is available
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # Initialize
        initialize_brightway()

        # Set current project
        bw.projects.set_current("pcf_calculator")

        # Get all methods containing "IPCC 2021"
        methods = [m for m in bw.methods if "IPCC 2021" in str(m)]

        # Verify at least one IPCC 2021 method exists
        assert len(methods) > 0, "No IPCC 2021 methods found"

        # Verify at least one method contains "GWP100"
        gwp100_methods = [m for m in methods if "GWP100" in str(m)]
        assert len(gwp100_methods) > 0, f"No IPCC 2021 GWP100 methods found. Available: {methods}"


class TestCustomEmissionFactorsDatabase:
    """Test that custom emission factors database is created."""

    def test_custom_database_created(self, clean_brightway_projects):
        """
        Scenario 4: Custom Emission Factors Database Created

        Given: Fresh Brightway2 project
        When: initialize_brightway() is called
        Then: "pcf_emission_factors" database exists but is initially empty
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # Initialize
        initialize_brightway()

        # Set current project
        bw.projects.set_current("pcf_calculator")

        # Verify custom database exists
        assert "pcf_emission_factors" in bw.databases

        # Verify database is initially empty
        ef_db = bw.Database("pcf_emission_factors")
        assert len(ef_db) == 0, "pcf_emission_factors should be initially empty"


class TestIdempotentInitialization:
    """Test that initialization is idempotent (safe to run multiple times)."""

    def test_idempotent_initialization(self, clean_brightway_projects):
        """
        Scenario 5: Idempotent Initialization

        Given: Existing "pcf_calculator" project
        When: initialize_brightway() is called multiple times
        Then: No errors raised, project remains functional, databases unchanged
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # First initialization
        result1 = initialize_brightway()
        assert result1 is True

        bw.projects.set_current("pcf_calculator")
        project_name_1 = bw.projects.current

        # Count databases after first init
        db_count_1 = len(bw.databases)
        bio_count_1 = len(bw.Database("biosphere3"))
        ef_count_1 = len(bw.Database("pcf_emission_factors"))

        # Second initialization
        result2 = initialize_brightway()
        assert result2 is True

        bw.projects.set_current("pcf_calculator")
        project_name_2 = bw.projects.current

        # Count databases after second init
        db_count_2 = len(bw.databases)
        bio_count_2 = len(bw.Database("biosphere3"))
        ef_count_2 = len(bw.Database("pcf_emission_factors"))

        # Verify project name unchanged
        assert project_name_1 == project_name_2 == "pcf_calculator"

        # Verify database counts unchanged
        assert db_count_1 == db_count_2, "Database count should not change on re-initialization"
        assert bio_count_1 == bio_count_2, "Biosphere3 count should not change"
        assert ef_count_1 == ef_count_2, "Custom DB count should not change"

        # Verify third run also works without errors
        result3 = initialize_brightway()
        assert result3 is True


class TestInitializationLogging:
    """Test that appropriate logging occurs during initialization."""

    def test_logging_output(self, clean_brightway_projects, caplog):
        """
        Test that initialize_brightway() logs appropriate messages.

        Given: Fresh system
        When: initialize_brightway() is called
        Then: Appropriate INFO level log messages are generated
        """
        from backend.calculator.brightway_setup import initialize_brightway
        import logging

        # Set logging level to capture INFO messages
        caplog.set_level(logging.INFO)

        # Initialize
        initialize_brightway()

        # Verify logging occurred (at least one log message)
        assert len(caplog.records) > 0, "Expected log messages during initialization"

        # Verify log messages contain relevant content
        log_text = " ".join([record.message for record in caplog.records])
        assert "pcf_calculator" in log_text.lower() or "brightway" in log_text.lower()


class TestInitializationCoverage:
    """Test edge cases and coverage requirements."""

    def test_existing_project_reuse(self, clean_brightway_projects):
        """
        Test that existing project is reused correctly.

        Given: "pcf_calculator" project already exists
        When: initialize_brightway() is called
        Then: Existing project is used, not recreated
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # First initialization
        initialize_brightway()
        bw.projects.set_current("pcf_calculator")

        # Add a marker to verify project persistence
        # (The database count should remain the same)
        initial_db_count = len(bw.databases)

        # Second initialization
        initialize_brightway()
        bw.projects.set_current("pcf_calculator")

        # Verify same project was reused
        assert len(bw.databases) == initial_db_count

    def test_custom_database_not_recreated(self, clean_brightway_projects):
        """
        Test that custom database is not recreated if it exists.

        Given: "pcf_emission_factors" database already exists
        When: initialize_brightway() is called again
        Then: Database is reused, not recreated
        """
        from backend.calculator.brightway_setup import initialize_brightway

        # First initialization
        initialize_brightway()
        bw.projects.set_current("pcf_calculator")

        # Verify empty database
        ef_db = bw.Database("pcf_emission_factors")
        assert len(ef_db) == 0

        # Second initialization
        initialize_brightway()
        bw.projects.set_current("pcf_calculator")

        # Verify database still exists and is still empty
        ef_db = bw.Database("pcf_emission_factors")
        assert len(ef_db) == 0
        assert "pcf_emission_factors" in bw.databases
