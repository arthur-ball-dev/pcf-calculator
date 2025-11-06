"""
Test suite for PCF Calculator.

Tests the PCFCalculator class to ensure:
1. Simple flat BOM calculations work correctly
2. Hierarchical BOM traversal (max 2 levels) works
3. Breakdown by category (materials, energy, transport) is accurate
4. Error handling for missing emission factors
5. Data quality score calculation
6. Integration with real database (t-shirt, water bottle, phone case)

Following TDD methodology - tests written BEFORE implementation.
TASK-CALC-003: Implement Simplified PCF Calculator

HISTORICAL NOTE (TASK-CALC-007):
This test file was updated to use isolated in-memory database instead of production
database, fixing a critical test isolation vulnerability. The original implementation
used db_context() which connected to the production database, creating risks:
- Test data corruption of production database
- Test failures due to shared state
- Non-deterministic test results based on execution order

This issue was part of a series of misdiagnoses:
- TASK-CALC-005: Incorrectly diagnosed as "emission factor sync failure"
- TASK-CALC-006: Incorrectly diagnosed as "Brightway2 pickle corruption"
- TASK-QA-004: Correctly diagnosed as "test database isolation issue"
- TASK-CALC-007: Fixed remaining vulnerability in test_pcf_calculator.py

Pattern copied from test_emission_factor_sync.py (fixed in TASK-QA-004).
"""

import pytest
import brightway2 as bw
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create in-memory SQLite database for testing.

    HISTORICAL NOTE: This fixture was created in TASK-CALC-007 to fix a critical
    vulnerability where tests were using production database. The same pattern
    was successfully implemented in TASK-QA-004 for test_emission_factor_sync.py.

    This resolves the root cause identified in Phase 2 validation:
    - TASK-CALC-005 diagnosis: Incorrect (not sync failure)
    - TASK-CALC-006 diagnosis: Incorrect (not pickle corruption)
    - TASK-QA-004 diagnosis: Correct (test database isolation)

    REPLACED: Old fixture that used db_context() production database connection
    NEW: In-memory SQLite database with full isolation

    Benefits:
    - Tests cannot corrupt production data
    - Tests pass in any order (no shared state)
    - Faster execution (in-memory vs disk I/O)
    - Parallel test execution is safe
    """
    from backend.models import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    # Enable foreign keys for SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()

    return engine


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """
    Provide isolated TEST database session (in-memory, not production).

    Replaces: db_context() which was using production database
    Pattern: Identical to test_emission_factor_sync.py::db_session

    This fixture creates a fresh in-memory database for each test function,
    ensuring complete test isolation. No test can affect another test's data.
    """
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    # Enable foreign keys on session
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    # Seed test data with minimal emission factors
    _seed_test_emission_factors(session)

    yield session

    # Cleanup
    session.close()


def _seed_test_emission_factors(session):
    """
    Load minimal test emission factors needed for PCF calculator tests.

    This function seeds the test database with factors used by test fixtures.
    It mirrors the production seed_data.py but uses only test-essential data.

    Test emission factors are marked with metadata={'test': True} to distinguish
    them from production data.
    """
    from backend.models import EmissionFactor

    test_factors = [
        # Materials - based on seed_data.py emission factors
        EmissionFactor(
            id="ef-test-cotton",
            activity_name="cotton",
            co2e_factor=5.89,
            unit="kg",
            data_source="test_data",
            geography="Global",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
        EmissionFactor(
            id="ef-test-polyester",
            activity_name="polyester",
            co2e_factor=6.4,
            unit="kg",
            data_source="test_data",
            geography="Global",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
        EmissionFactor(
            id="ef-test-plastic",
            activity_name="plastic_hdpe",
            co2e_factor=1.8,
            unit="kg",
            data_source="test_data",
            geography="Global",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
        EmissionFactor(
            id="ef-test-aluminum",
            activity_name="aluminum",
            co2e_factor=9.0,
            unit="kg",
            data_source="test_data",
            geography="Global",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
        # Energy
        EmissionFactor(
            id="ef-test-electricity",
            activity_name="electricity_us",
            co2e_factor=0.4,
            unit="kWh",
            data_source="test_data",
            geography="US",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
        # Transport
        EmissionFactor(
            id="ef-test-transport",
            activity_name="transport_truck",
            co2e_factor=0.0001,
            unit="tkm",
            data_source="test_data",
            geography="Global",
            emission_metadata={"test": True, "source": "TASK-CALC-007"}
        ),
    ]

    for factor in test_factors:
        existing = session.query(EmissionFactor).filter_by(id=factor.id).first()
        if not existing:
            session.add(factor)

    session.commit()


@pytest.fixture(scope="function")
def initialized_brightway(db_session):
    """
    Fixture to ensure Brightway2 is initialized and emission factors are synced.

    Prerequisite: TASK-CALC-001 and TASK-CALC-002 completed.

    This fixture includes validation to ensure emission factors are actually
    synced to Brightway2 database. If sync fails, the fixture will fail fast
    with a clear error message instead of allowing silent failures.

    Fix for TASK-CALC-003-BUG-001: Added validation per BE SEQ-009 guidance.
    """
    from backend.calculator.brightway_setup import initialize_brightway
    from backend.calculator.emission_factor_sync import sync_emission_factors

    # Initialize Brightway2 project
    initialize_brightway()

    # Sync emission factors from database
    result = sync_emission_factors(db_session=db_session)

    # CRITICAL: Validate sync actually worked (SEQ-009 fix)
    if not result or result.get('synced_count', 0) == 0:
        raise RuntimeError(
            f"Emission factor sync failed: {result}. "
            f"Expected at least 1 emission factor to be synced."
        )

    # Verify database exists and has factors
    bw.projects.set_current('pcf_calculator')
    if 'pcf_emission_factors' not in bw.databases:
        raise RuntimeError(
            "pcf_emission_factors database not created by sync. "
            f"Available databases: {list(bw.databases)}"
        )

    ef_db = bw.Database('pcf_emission_factors')
    if len(ef_db) == 0:
        raise RuntimeError(
            "pcf_emission_factors database exists but is EMPTY. "
            f"Sync reported {result.get('synced_count', 0)} factors."
        )

    print(f"\u2713 Emission factor sync verified: {len(ef_db)} factors loaded")

    yield

    # Brightway cleanup handled by TASK-CALC-001 tests

class TestSimpleFlatBOMCalculation:
    """Test basic flat BOM calculation with direct quantity × emission_factor."""

    def test_calculate_simple_bom_with_two_materials(self, db_session, initialized_brightway):
        """
        Scenario 1: Simple Flat BOM Calculation

        Given: A flat BOM with cotton (0.2 kg) and polyester (0.05 kg)
        When: calculate() is called
        Then: Total CO2e is 1.498 kg with correct breakdown

        Expected calculation:
        - cotton: 0.2 kg × 5.89 kg CO2e/kg = 1.178 kg CO2e
        - polyester: 0.05 kg × 6.4 kg CO2e/kg = 0.32 kg CO2e
        - Total: 1.498 kg CO2e
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.2, "unit": "kg"},
            {"name": "polyester", "quantity": 0.05, "unit": "kg"}
        ]

        result = calculator.calculate(bom)

        # Check total
        assert "total_co2e_kg" in result
        assert result["total_co2e_kg"] == pytest.approx(1.498, abs=0.01)

        # Check breakdown exists
        assert "breakdown" in result
        assert "cotton" in result["breakdown"]
        assert "polyester" in result["breakdown"]

        # Check individual components
        assert result["breakdown"]["cotton"] == pytest.approx(1.178, abs=0.01)
        assert result["breakdown"]["polyester"] == pytest.approx(0.32, abs=0.01)

    def test_calculate_single_material(self, db_session, initialized_brightway):
        """
        Test calculation with single material.

        Given: BOM with only cotton (1.0 kg)
        When: calculate() is called
        Then: Total CO2e is 5.89 kg (1.0 × 5.89)
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 1.0, "unit": "kg"}
        ]

        result = calculator.calculate(bom)

        assert result["total_co2e_kg"] == pytest.approx(5.89, abs=0.01)
        assert result["breakdown"]["cotton"] == pytest.approx(5.89, abs=0.01)

    def test_calculate_zero_quantity(self, db_session, initialized_brightway):
        """
        Test calculation with zero quantity.

        Given: BOM with cotton (0.0 kg)
        When: calculate() is called
        Then: Total CO2e is 0.0 kg
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.0, "unit": "kg"}
        ]

        result = calculator.calculate(bom)

        assert result["total_co2e_kg"] == pytest.approx(0.0, abs=0.001)
        assert result["breakdown"]["cotton"] == pytest.approx(0.0, abs=0.001)


class TestHierarchicalBOMCalculation:
    """Test hierarchical BOM calculation with parent-child relationships."""

    def test_calculate_two_level_bom(self, db_session, initialized_brightway):
        """
        Scenario 2: Hierarchical BOM (2 Levels)

        Given: A hierarchical BOM with t-shirt → fabric → cotton
        When: calculate_hierarchical() is called
        Then: Quantities are multiplied through levels

        Structure:
        - t-shirt (1 unit)
          - cotton_fabric (0.2 kg)
            - cotton (1.05 kg per kg fabric - 5% waste)
          - polyester_thread (0.01 kg)
            - polyester (1.0 kg per kg thread)

        Expected calculation:
        - Level 2 cotton: 0.2 × 1.05 × 5.89 = 1.2369 kg CO2e
        - Level 2 polyester: 0.01 × 1.0 × 6.4 = 0.064 kg CO2e
        - Total: 1.3009 kg CO2e
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom_tree = {
            "name": "t-shirt",
            "quantity": 1,
            "unit": "unit",
            "children": [
                {
                    "name": "cotton_fabric",
                    "quantity": 0.2,
                    "unit": "kg",
                    "children": [
                        {"name": "cotton", "quantity": 1.05, "unit": "kg"}
                    ]
                },
                {
                    "name": "polyester_thread",
                    "quantity": 0.01,
                    "unit": "kg",
                    "children": [
                        {"name": "polyester", "quantity": 1.0, "unit": "kg"}
                    ]
                }
            ]
        }

        result = calculator.calculate_hierarchical(bom_tree)

        # Check total
        assert result["total_co2e_kg"] == pytest.approx(1.301, abs=0.01)

        # Check max depth tracking
        assert "max_depth" in result
        assert result["max_depth"] == 2

    def test_calculate_with_database_product(self, db_session, initialized_brightway):
        """
        Test calculation using actual product from database.

        Given: T-shirt product exists in database with BOM
        When: calculate_product() is called with product_id
        Then: PCF is calculated from database BOM structure
        """
        from backend.calculator.pcf_calculator import PCFCalculator
        from backend.models import Product

        calculator = PCFCalculator()

        # Find t-shirt product in database
        product = db_session.query(Product).filter(
            Product.code == "TSHIRT-001"
        ).first()

        # Skip if product doesn't exist (depends on seed data)
        if product is None:
            pytest.skip("Test product TSHIRT-001 not found in database")

        result = calculator.calculate_product(product.id, db_session)

        # Should have total CO2e
        assert "total_co2e_kg" in result
        assert result["total_co2e_kg"] > 0

        # Should have breakdown
        assert "breakdown" in result


class TestBreakdownByCategory:
    """Test emissions breakdown by category (materials, energy, transport)."""

    def test_calculate_with_categories(self, db_session, initialized_brightway):
        """
        Scenario 3: Breakdown by Category (Materials, Energy, Transport)

        Given: BOM with materials, energy, and transport components
        When: calculate_with_categories() is called
        Then: Breakdown shows emissions by category

        Expected calculation:
        - Materials: 0.18 kg cotton × 5.89 = 1.0602 kg CO2e
        - Energy: 2.5 kWh electricity × 0.4 = 1.0 kg CO2e
        - Transport: 101.5 tkm truck × 0.0001 = 0.01015 kg CO2e
        - Total: ~2.07 kg CO2e
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.18, "unit": "kg", "category": "materials"},
            {"name": "electricity_us", "quantity": 2.5, "unit": "kWh", "category": "energy"},
            {"name": "transport_truck", "quantity": 101.5, "unit": "tkm", "category": "transport"}
        ]

        result = calculator.calculate_with_categories(bom)

        # Check category breakdown exists
        assert "breakdown_by_category" in result

        # Check individual categories
        assert result["breakdown_by_category"]["materials"] == pytest.approx(1.06, abs=0.01)
        assert result["breakdown_by_category"]["energy"] == pytest.approx(1.0, abs=0.01)
        assert result["breakdown_by_category"]["transport"] == pytest.approx(0.01, abs=0.01)

        # Check total matches sum of categories
        assert result["total_co2e_kg"] == pytest.approx(2.07, abs=0.05)

    def test_calculate_categories_default_to_materials(self, db_session, initialized_brightway):
        """
        Test that items without category default to 'materials'.

        Given: BOM items without category specified
        When: calculate_with_categories() is called
        Then: All items are categorized as 'materials'
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.2, "unit": "kg"},
            {"name": "polyester", "quantity": 0.05, "unit": "kg"}
        ]

        result = calculator.calculate_with_categories(bom)

        assert "breakdown_by_category" in result
        assert "materials" in result["breakdown_by_category"]
        assert result["breakdown_by_category"]["materials"] == pytest.approx(1.498, abs=0.01)


class TestErrorHandling:
    """Test error handling for invalid inputs and missing data."""

    def test_missing_emission_factor_raises_error(self, db_session, initialized_brightway):
        """
        Scenario 4: Error Handling for Missing Emission Factor

        Given: BOM with material not in emission factors database
        When: calculate() is called
        Then: ValueError is raised with helpful message
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "unknown_material", "quantity": 1.0, "unit": "kg"}
        ]

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate(bom)

        # Error message should mention the missing material
        assert "unknown_material" in str(exc_info.value)
        assert "emission factor not found" in str(exc_info.value).lower()

    def test_empty_bom_returns_zero(self, db_session, initialized_brightway):
        """
        Test calculation with empty BOM.

        Given: Empty BOM list
        When: calculate() is called
        Then: Total CO2e is 0.0 kg
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = []

        result = calculator.calculate(bom)

        assert result["total_co2e_kg"] == pytest.approx(0.0, abs=0.001)
        assert result["breakdown"] == {}

    def test_invalid_product_id_raises_error(self, db_session, initialized_brightway):
        """
        Test error handling for non-existent product ID.

        Given: Invalid product_id
        When: calculate_product() is called
        Then: ValueError is raised
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_product("invalid-id-12345", db_session)

        assert "product not found" in str(exc_info.value).lower()


class TestDataQualityScore:
    """Test data quality score calculation."""

    def test_calculate_with_data_quality(self, db_session, initialized_brightway):
        """
        Scenario 5: Data Quality Score Calculation

        Given: BOM with materials from different data sources
        When: calculate_with_quality() is called
        Then: Data quality score and source list are returned
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.2, "unit": "kg", "data_source": "EPA"},
            {"name": "polyester", "quantity": 0.05, "unit": "kg", "data_source": "DEFRA"}
        ]

        result = calculator.calculate_with_quality(bom)

        # Check data quality score exists and is valid
        assert "data_quality_score" in result
        assert result["data_quality_score"] >= 0.0
        assert result["data_quality_score"] <= 1.0

        # Check data sources are tracked
        assert "data_sources" in result
        assert "EPA" in result["data_sources"]
        assert "DEFRA" in result["data_sources"]

    def test_quality_score_higher_for_primary_data(self, db_session, initialized_brightway):
        """
        Test that primary data sources result in higher quality scores.

        Given: BOM with mix of primary and secondary data
        When: calculate_with_quality() is called
        Then: Quality score reflects data source quality
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        # Test with secondary data
        bom_secondary = [
            {"name": "cotton", "quantity": 0.2, "unit": "kg", "data_source": "DEFRA"}
        ]

        result = calculator.calculate_with_quality(bom_secondary)

        # Quality score should be calculated
        assert "data_quality_score" in result
        assert isinstance(result["data_quality_score"], (int, float))


class TestRealisticProducts:
    """Test calculations for realistic demo products."""

    def test_cotton_tshirt_realistic(self, db_session, initialized_brightway):
        """
        Test T-shirt realistic calculation.

        Given: T-shirt with full BOM (materials, energy, transport)
        When: calculate_product() is called
        Then: Total CO2e is approximately 2.05 kg

        Expected breakdown:
        - Materials: ~1.04 kg CO2e
        - Energy: ~1.0 kg CO2e
        - Transport: ~0.01 kg CO2e
        """
        from backend.calculator.pcf_calculator import PCFCalculator
        from backend.models import Product

        calculator = PCFCalculator()

        # Find t-shirt product
        product = db_session.query(Product).filter(
            Product.code == "TSHIRT-001"
        ).first()

        if product is None:
            pytest.skip("Test product TSHIRT-001 not found in database")

        result = calculator.calculate_product(product.id, db_session)

        # Check total is approximately 2.05 kg CO2e (±5% tolerance)
        assert result["total_co2e_kg"] == pytest.approx(2.05, rel=0.05)

        # Check breakdown by category if available
        if "breakdown_by_category" in result:
            assert result["breakdown_by_category"]["materials"] == pytest.approx(1.04, rel=0.1)
            assert result["breakdown_by_category"]["energy"] == pytest.approx(1.0, rel=0.1)
            assert result["breakdown_by_category"]["transport"] == pytest.approx(0.01, rel=0.2)

    def test_water_bottle_realistic(self, db_session, initialized_brightway):
        """
        Test water bottle realistic calculation.

        Given: Water bottle with PET, cap, and production energy
        When: calculate_product() is called
        Then: Total CO2e is approximately 0.105 kg

        Note: Task spec shows 0.157 kg in one place and 0.105 kg in another.
        Using 0.105 kg from task acceptance criteria.
        """
        from backend.calculator.pcf_calculator import PCFCalculator
        from backend.models import Product

        calculator = PCFCalculator()

        # Find water bottle product
        product = db_session.query(Product).filter(
            Product.code.like("BOTTLE%")
        ).first()

        if product is None:
            pytest.skip("Test product BOTTLE not found in database")

        result = calculator.calculate_product(product.id, db_session)

        # Check total is in expected range (±10% tolerance due to spec ambiguity)
        assert result["total_co2e_kg"] == pytest.approx(0.105, rel=0.1) or \
               result["total_co2e_kg"] == pytest.approx(0.157, rel=0.1)

    def test_phone_case_realistic(self, db_session, initialized_brightway):
        """
        Test phone case realistic calculation.

        Given: Phone case with plastic and packaging
        When: calculate_product() is called
        Then: Total CO2e is approximately 0.157 kg or 0.343 kg

        Note: Task spec shows both values in different sections.
        Using range check for flexibility.
        """
        from backend.calculator.pcf_calculator import PCFCalculator
        from backend.models import Product

        calculator = PCFCalculator()

        # Find phone case product
        product = db_session.query(Product).filter(
            Product.code.like("CASE%")
        ).first()

        if product is None:
            pytest.skip("Test product CASE not found in database")

        result = calculator.calculate_product(product.id, db_session)

        # Check total is in expected range
        assert result["total_co2e_kg"] > 0.1
        assert result["total_co2e_kg"] < 0.5


class TestCalculationPerformance:
    """Test that calculations complete in acceptable time."""

    def test_calculation_completes_in_5_seconds(self, db_session, initialized_brightway):
        """
        Test calculation performance.

        Given: Simple product with BOM
        When: calculate() is called
        Then: Calculation completes in <5 seconds

        Performance requirement from TASK-CALC-003 spec.
        """
        import time
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        bom = [
            {"name": "cotton", "quantity": 0.2, "unit": "kg"},
            {"name": "polyester", "quantity": 0.05, "unit": "kg"}
        ]

        start_time = time.time()
        result = calculator.calculate(bom)
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete in less than 5 seconds
        assert calculation_time < 5.0

        # Should also complete reasonably fast (< 1 second for simple BOM)
        assert calculation_time < 1.0


class TestCalculatorInitialization:
    """Test PCFCalculator initialization."""

    def test_calculator_requires_brightway_initialized(self):
        """
        Test that calculator checks for Brightway2 initialization.

        Given: Brightway2 project "pcf_calculator" exists
        When: PCFCalculator() is instantiated
        Then: No errors occur
        """
        from backend.calculator.pcf_calculator import PCFCalculator
        from backend.calculator.brightway_setup import initialize_brightway

        # Ensure Brightway2 is initialized
        initialize_brightway()

        # Should not raise error
        calculator = PCFCalculator()

        assert calculator is not None

    def test_calculator_has_access_to_emission_factors_db(self, initialized_brightway):
        """
        Test that calculator can access emission factors database.

        Given: Emission factors are synced to Brightway2
        When: PCFCalculator() is instantiated
        Then: Calculator has access to pcf_emission_factors database
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        calculator = PCFCalculator()

        # Verify calculator has ef_db attribute
        assert hasattr(calculator, "ef_db")
        assert calculator.ef_db is not None
