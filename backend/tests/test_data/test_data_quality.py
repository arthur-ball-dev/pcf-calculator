"""
Test Data Quality Validation - TASK-DATA-004 (REVISED)

Tests for data quality validation using CORRECT schema:
- NO Product.emission_factor_id (uses implicit matching via activity_name)
- NO BillOfMaterials.level (only in v_bom_explosion view)
- Component-to-factor matching via: Product.code == EmissionFactor.activity_name

These tests MUST be written BEFORE implementing validate_data_quality.py
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from backend.models import (
    Base,
    Product,
    EmissionFactor,
    BillOfMaterials,
)


# Fixtures
@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create tables
    Base.metadata.create_all(engine)

    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()

    # Enable foreign keys for this session
    session.execute("PRAGMA foreign_keys=ON")

    yield session

    session.close()


@pytest.fixture
def sample_emission_factors(db_session):
    """Create sample emission factors for testing"""
    factors = [
        EmissionFactor(
            activity_name="cotton",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            data_quality_rating=Decimal("4.5")
        ),
        EmissionFactor(
            activity_name="polyester",
            co2e_factor=Decimal("6.0"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            data_quality_rating=Decimal("4.0")
        ),
        EmissionFactor(
            activity_name="plastic_abs",
            co2e_factor=Decimal("3.8"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            data_quality_rating=Decimal("4.2")
        ),
        EmissionFactor(
            activity_name="electricity_us",
            co2e_factor=Decimal("0.4"),
            unit="kWh",
            data_source="EPA",
            geography="US",
            data_quality_rating=Decimal("3.8")
        ),
        EmissionFactor(
            activity_name="transport_truck",
            co2e_factor=Decimal("0.1"),
            unit="tkm",
            data_source="EPA",
            geography="GLO",
            data_quality_rating=Decimal("3.5")
        ),
    ]

    for ef in factors:
        db_session.add(ef)

    db_session.commit()

    return factors


@pytest.fixture
def sample_product_with_bom(db_session, sample_emission_factors):
    """Create sample product with BOM for testing"""
    # Create finished product
    product = Product(
        code="TSHIRT-001",
        name="Cotton T-Shirt",
        unit="unit",
        is_finished_product=True
    )
    db_session.add(product)
    db_session.flush()

    # Create components (matching emission factor activity_names)
    components = [
        Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False),
        Product(code="polyester", name="Polyester", unit="kg", is_finished_product=False),
        Product(code="plastic_abs", name="Plastic ABS", unit="kg", is_finished_product=False),
        Product(code="electricity_us", name="Electricity US", unit="kWh", is_finished_product=False),
        Product(code="transport_truck", name="Transport Truck", unit="tkm", is_finished_product=False),
    ]

    for comp in components:
        db_session.add(comp)

    db_session.flush()

    # Create BOM relationships
    bom_items = [
        BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=components[0].id,
            quantity=Decimal("0.18"),
            unit="kg"
        ),
        BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=components[1].id,
            quantity=Decimal("0.015"),
            unit="kg"
        ),
        BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=components[2].id,
            quantity=Decimal("0.002"),
            unit="kg"
        ),
        BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=components[3].id,
            quantity=Decimal("2.5"),
            unit="kWh"
        ),
        BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=components[4].id,
            quantity=Decimal("0.1015"),
            unit="tkm"
        ),
    ]

    for bom in bom_items:
        db_session.add(bom)

    db_session.commit()

    return product


# Test Scenario 1: Happy Path - All Data Quality Checks Pass
class TestHappyPath:
    """Test validation when all data is complete and valid"""

    def test_validate_all_checks_pass(self, db_session, sample_product_with_bom):
        """Test that validation passes when all data is valid"""
        # Import validate function (will be implemented later)
        from backend.scripts.validate_data_quality import validate_data_quality

        # Run validation
        quality_report = validate_data_quality(db_session)

        # Verify report structure
        assert "validation_timestamp" in quality_report
        assert "emission_factors" in quality_report
        assert "products" in quality_report
        assert "bom_completeness" in quality_report
        assert "overall_quality_score" in quality_report
        assert "validation_errors" in quality_report

        # Verify emission factors metrics
        ef_metrics = quality_report["emission_factors"]
        assert ef_metrics["count"] == 5
        assert ef_metrics["completeness_percent"] == 100.0
        assert ef_metrics["valid_ranges"] is True
        assert "average_co2e_factor" in ef_metrics

        # Verify products metrics
        products = quality_report["products"]
        assert products["finished_products"] == 1
        assert products["with_bom"] == 1
        assert products["bom_coverage_percent"] == 100.0

        # Verify BOM completeness
        bom = quality_report["bom_completeness"]
        assert bom["total_components"] == 5
        assert bom["components_with_factors"] == 5
        assert bom["coverage_percent"] == 100.0
        assert bom["missing_factors"] == []

        # Verify no validation errors
        assert quality_report["validation_errors"] == 0

    def test_data_sources_breakdown(self, db_session, sample_product_with_bom):
        """Test that data sources are correctly counted"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        # All sample factors are from EPA
        data_sources = quality_report["emission_factors"]["data_sources"]
        assert "EPA" in data_sources
        assert data_sources["EPA"] == 5


# Test Scenario 2: Detect Missing Emission Factors
class TestMissingEmissionFactors:
    """Test detection of components without matching emission factors"""

    def test_detect_missing_emission_factor(self, db_session, sample_emission_factors):
        """Test that missing emission factors are detected"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create product with component that has NO matching emission factor
        product = Product(
            code="TEST-001",
            name="Test Product",
            unit="item",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.flush()

        # Create component with code that doesn't match any emission factor
        unknown_component = Product(
            code="UNKNOWN-MATERIAL",  # No emission factor with this activity_name
            name="Unknown Material",
            unit="kg",
            is_finished_product=False
        )
        db_session.add(unknown_component)
        db_session.flush()

        # Create BOM relationship
        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=unknown_component.id,
            quantity=Decimal("1.0")
        )
        db_session.add(bom)
        db_session.commit()

        # Run validation
        quality_report = validate_data_quality(db_session)

        # Verify missing factor is detected
        assert quality_report["bom_completeness"]["coverage_percent"] < 100.0
        assert "UNKNOWN-MATERIAL" in quality_report["bom_completeness"]["missing_factors"]
        assert quality_report["bom_completeness"]["components_with_factors"] == 0
        assert quality_report["bom_completeness"]["total_components"] == 1

    def test_partial_coverage(self, db_session, sample_emission_factors):
        """Test BOM coverage calculation with partial matches"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create product
        product = Product(
            code="PARTIAL-001",
            name="Partial Coverage Product",
            unit="item",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.flush()

        # Create components: 2 with factors, 1 without
        comp1 = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)
        comp2 = Product(code="polyester", name="Polyester", unit="kg", is_finished_product=False)
        comp3 = Product(code="unobtainium", name="Unobtainium", unit="kg", is_finished_product=False)

        db_session.add_all([comp1, comp2, comp3])
        db_session.flush()

        # Create BOM relationships
        for comp in [comp1, comp2, comp3]:
            bom = BillOfMaterials(
                parent_product_id=product.id,
                child_product_id=comp.id,
                quantity=Decimal("1.0")
            )
            db_session.add(bom)

        db_session.commit()

        # Run validation
        quality_report = validate_data_quality(db_session)

        # Verify partial coverage
        bom = quality_report["bom_completeness"]
        assert bom["total_components"] == 3
        assert bom["components_with_factors"] == 2
        assert abs(bom["coverage_percent"] - 66.67) < 0.1
        assert "unobtainium" in bom["missing_factors"]


# Test Scenario 3: Calculate Data Quality Scores
class TestDataQualityScores:
    """Test data quality score calculations"""

    def test_average_quality_rating(self, db_session):
        """Test calculation of average data quality rating"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factors with known quality ratings
        ef1 = EmissionFactor(
            activity_name="material1",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            data_quality_rating=Decimal("4.5")
        )
        ef2 = EmissionFactor(
            activity_name="material2",
            co2e_factor=Decimal("3.0"),
            unit="kg",
            data_source="DEFRA",
            geography="GLO",
            data_quality_rating=Decimal("3.5")
        )

        db_session.add_all([ef1, ef2])
        db_session.commit()

        # Run validation
        quality_report = validate_data_quality(db_session)

        # Average quality: (4.5 + 3.5) / 2 = 4.0
        assert quality_report["average_data_quality"] == 4.0

    def test_overall_quality_score(self, db_session, sample_product_with_bom):
        """Test overall quality score calculation"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        # Overall score should be between 1.0 and 5.0
        assert 1.0 <= quality_report["overall_quality_score"] <= 5.0

        # With 100% coverage and good quality ratings, score should be high
        assert quality_report["overall_quality_score"] >= 4.0


# Test Scenario 4: Validate Positive CO2e Factors
class TestValidRanges:
    """Test validation of CO2e factor ranges"""

    def test_all_factors_positive(self, db_session, sample_emission_factors):
        """Test that all emission factors have positive CO2e values"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        # All factors should be valid (>= 0)
        assert quality_report["emission_factors"]["valid_ranges"] is True
        assert quality_report["validation_errors"] == 0

    def test_zero_factor_allowed(self, db_session):
        """Test that zero CO2e factor is allowed"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factor with zero CO2e
        ef = EmissionFactor(
            activity_name="zero_emission",
            co2e_factor=Decimal("0.0"),
            unit="kg",
            data_source="TEST",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        quality_report = validate_data_quality(db_session)

        # Zero is valid (>= 0 constraint)
        assert quality_report["emission_factors"]["valid_ranges"] is True


# Test Scenario 5: BOM Coverage Report Per Product
class TestProductDetails:
    """Test per-product BOM coverage reporting"""

    def test_product_details_structure(self, db_session, sample_product_with_bom):
        """Test that product details have correct structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        # Verify product details exist
        assert "product_details" in quality_report["products"]
        product_details = quality_report["products"]["product_details"]

        assert len(product_details) == 1

        product = product_details[0]
        assert "code" in product
        assert "name" in product
        assert "bom_component_count" in product
        assert "components_with_factors" in product
        assert "coverage_percent" in product

    def test_product_coverage_calculation(self, db_session, sample_product_with_bom):
        """Test BOM coverage calculation for individual products"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        product = quality_report["products"]["product_details"][0]

        # Verify product details
        assert product["code"] == "TSHIRT-001"
        assert product["name"] == "Cotton T-Shirt"
        assert product["bom_component_count"] == 5
        assert product["components_with_factors"] == 5
        assert product["coverage_percent"] == 100.0

    def test_multiple_products(self, db_session, sample_emission_factors):
        """Test validation with multiple products"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create two products
        for i in range(2):
            product = Product(
                code=f"PROD-{i:03d}",
                name=f"Product {i}",
                unit="item",
                is_finished_product=True
            )
            db_session.add(product)
            db_session.flush()

            # Add cotton component to each
            cotton = db_session.query(Product).filter_by(code="cotton").first()
            if not cotton:
                cotton = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)
                db_session.add(cotton)
                db_session.flush()

            bom = BillOfMaterials(
                parent_product_id=product.id,
                child_product_id=cotton.id,
                quantity=Decimal("1.0")
            )
            db_session.add(bom)

        db_session.commit()

        quality_report = validate_data_quality(db_session)

        # Verify multiple products reported
        assert quality_report["products"]["finished_products"] == 2
        assert len(quality_report["products"]["product_details"]) == 2


# Test Scenario 6: Edge Cases
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_no_emission_factors(self, db_session):
        """Test validation with no emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        assert quality_report["emission_factors"]["count"] == 0
        assert quality_report["emission_factors"]["completeness_percent"] == 0.0

    def test_no_products(self, db_session, sample_emission_factors):
        """Test validation with no products"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(db_session)

        assert quality_report["products"]["finished_products"] == 0
        assert quality_report["products"]["with_bom"] == 0

    def test_product_without_bom(self, db_session, sample_emission_factors):
        """Test product with no BOM items"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create product without BOM
        product = Product(
            code="NO-BOM",
            name="Product Without BOM",
            unit="item",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        quality_report = validate_data_quality(db_session)

        assert quality_report["products"]["finished_products"] == 1
        assert quality_report["products"]["with_bom"] == 0
        assert quality_report["products"]["bom_coverage_percent"] == 0.0


# Test Scenario 7: Completeness Validation
class TestCompletenessValidation:
    """Test data completeness checks"""

    def test_completeness_percent_calculation(self, db_session):
        """Test completeness percentage for emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factors with all required fields
        ef = EmissionFactor(
            activity_name="complete_factor",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        quality_report = validate_data_quality(db_session)

        # All required fields present
        assert quality_report["emission_factors"]["completeness_percent"] == 100.0

    def test_null_optional_fields(self, db_session):
        """Test that null optional fields don't affect completeness"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factor with null optional fields
        ef = EmissionFactor(
            activity_name="minimal_factor",
            co2e_factor=Decimal("3.0"),
            unit="kg",
            data_source="TEST",
            geography="GLO",
            data_quality_rating=None,  # Optional
            uncertainty_min=None,  # Optional
            uncertainty_max=None   # Optional
        )
        db_session.add(ef)
        db_session.commit()

        quality_report = validate_data_quality(db_session)

        # Completeness should still be 100% for required fields
        assert quality_report["emission_factors"]["completeness_percent"] == 100.0


# Test Scenario 8: Matching Logic Verification
class TestMatchingLogic:
    """Test component-to-emission-factor matching using correct schema"""

    def test_matching_by_activity_name(self, db_session):
        """Test that matching works via Product.code == EmissionFactor.activity_name"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factor with specific activity_name
        ef = EmissionFactor(
            activity_name="test_material",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="TEST",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.flush()

        # Create product with matching code
        product = Product(
            code="FINISHED-001",
            name="Finished Product",
            unit="item",
            is_finished_product=True
        )
        component = Product(
            code="test_material",  # Matches emission_factor.activity_name
            name="Test Material",
            unit="kg",
            is_finished_product=False
        )
        db_session.add_all([product, component])
        db_session.flush()

        # Create BOM
        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=component.id,
            quantity=Decimal("1.0")
        )
        db_session.add(bom)
        db_session.commit()

        # Run validation
        quality_report = validate_data_quality(db_session)

        # Component should be matched
        assert quality_report["bom_completeness"]["coverage_percent"] == 100.0
        assert quality_report["bom_completeness"]["components_with_factors"] == 1

    def test_case_sensitive_matching(self, db_session):
        """Test that matching is case-sensitive"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factor with lowercase activity_name
        ef = EmissionFactor(
            activity_name="material",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="TEST",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.flush()

        # Create components with different cases
        product = Product(code="PROD-001", name="Product", unit="item", is_finished_product=True)
        comp1 = Product(code="material", name="Material", unit="kg", is_finished_product=False)
        comp2 = Product(code="MATERIAL", name="Material Upper", unit="kg", is_finished_product=False)

        db_session.add_all([product, comp1, comp2])
        db_session.flush()

        # Create BOMs
        for comp in [comp1, comp2]:
            bom = BillOfMaterials(
                parent_product_id=product.id,
                child_product_id=comp.id,
                quantity=Decimal("1.0")
            )
            db_session.add(bom)

        db_session.commit()

        quality_report = validate_data_quality(db_session)

        # Only lowercase "material" should match
        assert quality_report["bom_completeness"]["total_components"] == 2
        assert quality_report["bom_completeness"]["components_with_factors"] == 1
        assert "MATERIAL" in quality_report["bom_completeness"]["missing_factors"]
