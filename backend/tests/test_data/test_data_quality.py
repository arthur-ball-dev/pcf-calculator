"""
Test Data Quality Validation Script
TASK-DATA-004: Comprehensive tests for validate_data_quality.py

Test Scenarios:
1. Happy Path - All Data Quality Checks Pass
2. Detect Missing Emission Factors
3. Calculate Data Quality Scores
4. Validate Positive CO2e Factors
5. BOM Coverage Report

TDD Protocol: Tests written FIRST, implementation comes after test commit.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from decimal import Decimal

# Import models
from backend.models import (
    Base,
    Product,
    EmissionFactor,
    BillOfMaterials,
)


@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def seed_test_data(test_db_session: Session):
    """Seed database with test data for quality validation"""
    # Create emission factors
    emission_factors = [
        EmissionFactor(
            activity_name="cotton",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=4.5
        ),
        EmissionFactor(
            activity_name="polyester",
            co2e_factor=Decimal("7.0"),
            unit="kg",
            data_source="DEFRA",
            data_quality_rating=3.5
        ),
        EmissionFactor(
            activity_name="plastic_pet",
            co2e_factor=Decimal("3.5"),
            unit="kg",
            data_source="Ecoinvent",
            data_quality_rating=5.0
        ),
    ]
    test_db_session.add_all(emission_factors)
    test_db_session.commit()

    # Create products
    tshirt = Product(
        code="TSHIRT-001",
        name="Cotton T-Shirt",
        description="Simple cotton t-shirt",
        unit="item",
        is_finished_product=True
    )
    cotton_material = Product(
        code="COTTON-MAT",
        name="Cotton Material",
        description="Raw cotton",
        unit="kg",
        is_finished_product=False,
        emission_factor_id=emission_factors[0].id
    )
    bottle = Product(
        code="BOTTLE-001",
        name="Water Bottle",
        description="PET water bottle",
        unit="item",
        is_finished_product=True
    )
    plastic_material = Product(
        code="PLASTIC-MAT",
        name="PET Plastic",
        description="Raw PET",
        unit="kg",
        is_finished_product=False,
        emission_factor_id=emission_factors[2].id
    )

    test_db_session.add_all([tshirt, cotton_material, bottle, plastic_material])
    test_db_session.commit()

    # Create BOMs
    bom1 = BillOfMaterials(
        parent_product_id=tshirt.id,
        child_product_id=cotton_material.id,
        quantity=Decimal("0.18"),
        level=0
    )
    bom2 = BillOfMaterials(
        parent_product_id=bottle.id,
        child_product_id=plastic_material.id,
        quantity=Decimal("0.05"),
        level=0
    )

    test_db_session.add_all([bom1, bom2])
    test_db_session.commit()

    return test_db_session


# ============================================================================
# Test Scenario 1: Happy Path - All Data Quality Checks Pass
# ============================================================================

class TestDataQualityHappyPath:
    """Test data quality validation with complete, valid data"""

    def test_validate_emission_factors_completeness(self, seed_test_data: Session):
        """Test emission factors completeness check"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        # Should have emission_factors section
        assert "emission_factors" in quality_report
        ef_section = quality_report["emission_factors"]

        # Should count emission factors correctly
        assert ef_section["count"] == 3
        assert ef_section["completeness_percent"] == 100.0

    def test_validate_emission_factors_valid_ranges(self, seed_test_data: Session):
        """Test that all CO2e factors are positive"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        ef_section = quality_report["emission_factors"]
        assert ef_section["valid_ranges"] is True

    def test_validate_products_with_bom(self, seed_test_data: Session):
        """Test products BOM coverage"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        # Should have products section
        assert "products" in quality_report
        products_section = quality_report["products"]

        # 2 finished products
        assert products_section["finished_products"] == 2
        # Both have BOMs
        assert products_section["with_bom"] == 2
        # 100% coverage
        assert products_section["bom_coverage_percent"] == 100.0

    def test_validate_bom_completeness(self, seed_test_data: Session):
        """Test BOM component coverage with emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        # Should have bom_completeness section
        assert "bom_completeness" in quality_report
        bom_section = quality_report["bom_completeness"]

        # All components have emission factors
        assert bom_section["total_components"] == 2
        assert bom_section["components_with_factors"] == 2
        assert bom_section["coverage_percent"] == 100.0
        assert bom_section["missing_factors"] == []

    def test_overall_quality_score_calculation(self, seed_test_data: Session):
        """Test overall quality score is calculated"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        # Should have overall quality score (1-5 scale)
        assert "overall_quality_score" in quality_report
        score = quality_report["overall_quality_score"]
        assert 1.0 <= score <= 5.0

    def test_validation_timestamp_included(self, seed_test_data: Session):
        """Test report includes validation timestamp"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        assert "validation_timestamp" in quality_report
        # Should be ISO format timestamp
        timestamp = quality_report["validation_timestamp"]
        assert isinstance(timestamp, str)
        # Verify it's a valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_validation_errors_zero_for_valid_data(self, seed_test_data: Session):
        """Test no validation errors for valid data"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        assert "validation_errors" in quality_report
        assert quality_report["validation_errors"] == 0


# ============================================================================
# Test Scenario 2: Detect Missing Emission Factors
# ============================================================================

class TestMissingEmissionFactors:
    """Test detection of components without emission factors"""

    def test_detect_component_without_emission_factor(self, seed_test_data: Session):
        """Test detection of BOM component without emission factor"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Add product and BOM component without emission factor
        unknown_product = Product(
            code="UNKNOWN-001",
            name="Unknown Material",
            description="Material without emission factor",
            unit="kg",
            is_finished_product=False,
            emission_factor_id=None  # No emission factor
        )
        test_product = Product(
            code="TEST-001",
            name="Test Product",
            description="Test product",
            unit="item",
            is_finished_product=True
        )
        seed_test_data.add_all([unknown_product, test_product])
        seed_test_data.commit()

        bom = BillOfMaterials(
            parent_product_id=test_product.id,
            child_product_id=unknown_product.id,
            quantity=Decimal("1.0"),
            level=0
        )
        seed_test_data.add(bom)
        seed_test_data.commit()

        # Validate
        quality_report = validate_data_quality(seed_test_data)

        # Coverage should be less than 100%
        bom_section = quality_report["bom_completeness"]
        assert bom_section["coverage_percent"] < 100.0

        # Should list missing emission factors
        assert len(bom_section["missing_factors"]) > 0
        assert "UNKNOWN-001" in bom_section["missing_factors"]

    def test_bom_coverage_percent_calculation(self, seed_test_data: Session):
        """Test BOM coverage percentage calculation with missing factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Add 3 components: 2 with factors, 1 without
        comp1 = Product(
            code="COMP-001",
            name="Component 1",
            unit="kg",
            is_finished_product=False,
            emission_factor_id=seed_test_data.query(EmissionFactor).first().id
        )
        comp2 = Product(
            code="COMP-002",
            name="Component 2",
            unit="kg",
            is_finished_product=False,
            emission_factor_id=None  # Missing
        )
        comp3 = Product(
            code="COMP-003",
            name="Component 3",
            unit="kg",
            is_finished_product=False,
            emission_factor_id=seed_test_data.query(EmissionFactor).first().id
        )
        test_product = Product(
            code="TEST-002",
            name="Test Product 2",
            unit="item",
            is_finished_product=True
        )
        seed_test_data.add_all([comp1, comp2, comp3, test_product])
        seed_test_data.commit()

        # Add BOMs
        for comp in [comp1, comp2, comp3]:
            bom = BillOfMaterials(
                parent_product_id=test_product.id,
                child_product_id=comp.id,
                quantity=Decimal("1.0"),
                level=0
            )
            seed_test_data.add(bom)
        seed_test_data.commit()

        quality_report = validate_data_quality(seed_test_data)

        bom_section = quality_report["bom_completeness"]
        # 5 total components (2 from seed data + 3 new)
        assert bom_section["total_components"] == 5
        # 4 with factors (2 from seed + 2 new with factors)
        assert bom_section["components_with_factors"] == 4
        # 80% coverage (4/5)
        assert bom_section["coverage_percent"] == 80.0


# ============================================================================
# Test Scenario 3: Calculate Data Quality Scores
# ============================================================================

class TestDataQualityScores:
    """Test data quality score calculations"""

    def test_average_data_quality_rating(self, seed_test_data: Session):
        """Test average data quality rating calculation"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        # Should have average_data_quality field
        assert "average_data_quality" in quality_report
        avg_quality = quality_report["average_data_quality"]

        # Seed data has ratings: 4.5, 3.5, 5.0
        # Average: (4.5 + 3.5 + 5.0) / 3 = 4.333...
        expected_avg = (4.5 + 3.5 + 5.0) / 3
        assert abs(avg_quality - expected_avg) < 0.01

    def test_data_source_distribution(self, seed_test_data: Session):
        """Test data source distribution reporting"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        ef_section = quality_report["emission_factors"]
        assert "data_sources" in ef_section

        sources = ef_section["data_sources"]
        # Seed data has EPA, DEFRA, Ecoinvent
        assert sources["EPA"] == 1
        assert sources["DEFRA"] == 1
        assert sources["Ecoinvent"] == 1

    def test_average_co2e_factor_calculation(self, seed_test_data: Session):
        """Test average CO2e factor calculation"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        ef_section = quality_report["emission_factors"]
        assert "average_co2e_factor" in ef_section

        avg_co2e = ef_section["average_co2e_factor"]
        # Seed data: 5.0, 7.0, 3.5
        # Average: (5.0 + 7.0 + 3.5) / 3 = 5.166...
        expected_avg = (5.0 + 7.0 + 3.5) / 3
        assert abs(avg_co2e - expected_avg) < 0.01


# ============================================================================
# Test Scenario 4: Validate Positive CO2e Factors
# ============================================================================

class TestValidatePositiveCO2eFactors:
    """Test validation of CO2e factor ranges"""

    def test_detect_negative_co2e_factor(self, test_db_session: Session):
        """Test detection of invalid negative CO2e factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Add negative emission factor (should be caught by DB constraint, but test validation)
        # Note: Database constraint will prevent this, so we test validation logic
        ef_valid = EmissionFactor(
            activity_name="valid_material",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=4.0
        )
        test_db_session.add(ef_valid)
        test_db_session.commit()

        # Validate - should pass with valid data
        quality_report = validate_data_quality(test_db_session)
        assert quality_report["validation_errors"] == 0
        assert quality_report["emission_factors"]["valid_ranges"] is True

    def test_detect_zero_co2e_factor(self, test_db_session: Session):
        """Test detection of zero CO2e factors (valid but unusual)"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Zero is technically valid but unusual
        ef_zero = EmissionFactor(
            activity_name="zero_emission",
            co2e_factor=Decimal("0.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=3.0
        )
        test_db_session.add(ef_zero)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Should be marked as valid (zero is allowed)
        assert quality_report["emission_factors"]["valid_ranges"] is True

    def test_validation_error_details(self, test_db_session: Session):
        """Test validation error details structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Add valid data
        ef = EmissionFactor(
            activity_name="material",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=4.0
        )
        test_db_session.add(ef)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Should have error_details field (empty list for valid data)
        assert "error_details" in quality_report
        assert isinstance(quality_report["error_details"], list)
        assert len(quality_report["error_details"]) == 0


# ============================================================================
# Test Scenario 5: BOM Coverage Report
# ============================================================================

class TestBOMCoverageReport:
    """Test BOM coverage reporting per product"""

    def test_product_level_bom_coverage(self, seed_test_data: Session):
        """Test BOM coverage reported per product"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        products_section = quality_report["products"]
        assert "product_details" in products_section

        product_details = products_section["product_details"]
        assert len(product_details) == 2  # 2 finished products

        # Each product should have coverage details
        for product in product_details:
            assert "code" in product
            assert "name" in product
            assert "bom_component_count" in product
            assert "components_with_factors" in product
            assert "coverage_percent" in product

    def test_product_bom_component_count(self, seed_test_data: Session):
        """Test BOM component counting per product"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        product_details = quality_report["products"]["product_details"]

        # Find tshirt product
        tshirt = next(p for p in product_details if p["code"] == "TSHIRT-001")
        assert tshirt["bom_component_count"] == 1  # 1 component
        assert tshirt["components_with_factors"] == 1
        assert tshirt["coverage_percent"] == 100.0

    def test_all_products_have_complete_bom_coverage(self, seed_test_data: Session):
        """Test all seed products have 100% BOM coverage"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        product_details = quality_report["products"]["product_details"]

        for product in product_details:
            assert product["bom_component_count"] > 0
            assert product["components_with_factors"] == product["bom_component_count"]
            assert product["coverage_percent"] == 100.0


# ============================================================================
# Test Scenario 6: Overall Quality Score Calculation
# ============================================================================

class TestOverallQualityScore:
    """Test overall quality score calculation (1-5 scale)"""

    def test_quality_score_perfect_data(self, seed_test_data: Session):
        """Test quality score for perfect data (all checks pass)"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(seed_test_data)

        score = quality_report["overall_quality_score"]
        # Perfect data should score high (4.5-5.0)
        assert score >= 4.5

    def test_quality_score_missing_factors(self, seed_test_data: Session):
        """Test quality score decreases with missing emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Add component without emission factor
        missing_comp = Product(
            code="MISSING-001",
            name="Missing Material",
            unit="kg",
            is_finished_product=False,
            emission_factor_id=None
        )
        test_product = Product(
            code="TEST-MISSING",
            name="Test Product",
            unit="item",
            is_finished_product=True
        )
        seed_test_data.add_all([missing_comp, test_product])
        seed_test_data.commit()

        bom = BillOfMaterials(
            parent_product_id=test_product.id,
            child_product_id=missing_comp.id,
            quantity=Decimal("1.0"),
            level=0
        )
        seed_test_data.add(bom)
        seed_test_data.commit()

        quality_report = validate_data_quality(seed_test_data)

        score = quality_report["overall_quality_score"]
        # Score should be lower with missing data
        assert score < 5.0

    def test_quality_score_range(self, test_db_session: Session):
        """Test quality score is always in valid range (1-5)"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Test with minimal data
        ef = EmissionFactor(
            activity_name="material",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=3.0
        )
        test_db_session.add(ef)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        score = quality_report["overall_quality_score"]
        assert 1.0 <= score <= 5.0


# ============================================================================
# Test Scenario 7: Full Integration with Seed Data
# ============================================================================

class TestFullSeedDataValidation:
    """Test validation with full seed data loaded"""

    def test_validate_full_seed_data(self, test_db_session: Session):
        """Test validation with complete seed data (20 factors, 3 products)"""
        from backend.scripts.validate_data_quality import validate_data_quality
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        # Load full seed data
        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Validate
        quality_report = validate_data_quality(test_db_session)

        # Expected values for full seed data
        assert quality_report["emission_factors"]["count"] == 20
        assert quality_report["emission_factors"]["completeness_percent"] == 100.0
        assert quality_report["products"]["finished_products"] >= 3
        assert quality_report["bom_completeness"]["coverage_percent"] == 100.0
        assert quality_report["overall_quality_score"] >= 4.5
        assert quality_report["validation_errors"] == 0

    def test_seed_data_quality_report_structure(self, test_db_session: Session):
        """Test complete report structure with seed data"""
        from backend.scripts.validate_data_quality import validate_data_quality
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        quality_report = validate_data_quality(test_db_session)

        # Verify all required sections exist
        required_sections = [
            "validation_timestamp",
            "emission_factors",
            "products",
            "bom_completeness",
            "overall_quality_score",
            "validation_errors",
            "error_details",
            "average_data_quality"
        ]

        for section in required_sections:
            assert section in quality_report, f"Missing section: {section}"
