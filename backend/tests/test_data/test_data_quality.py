"""
Test Data Quality Validation Script
TASK-DATA-004 (REVISED): Comprehensive tests for validate_data_quality.py

Test Scenarios:
1. Happy Path - All Data Quality Checks Pass
2. Detect Missing Emission Factors (implicit matching via activity_name)
3. Calculate Data Quality Scores
4. Validate Positive CO2e Factors
5. BOM Coverage Report Per Product

CRITICAL: Uses actual schema:
- NO Product.emission_factor_id (implicit matching: Product.code == EmissionFactor.activity_name)
- NO BillOfMaterials.level (only in v_bom_explosion view)
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
def sample_emission_factors(test_db_session):
    """Create sample emission factors for testing"""
    factors = [
        EmissionFactor(
            activity_name="cotton",
            co2e_factor=Decimal("5.5"),
            unit="kg",
            data_source="EPA",
            geography="US",
            data_quality_rating=Decimal("4.5")
        ),
        EmissionFactor(
            activity_name="polyester",
            co2e_factor=Decimal("6.2"),
            unit="kg",
            data_source="DEFRA",
            geography="UK",
            data_quality_rating=Decimal("4.0")
        ),
        EmissionFactor(
            activity_name="plastic_pet",
            co2e_factor=Decimal("2.7"),
            unit="kg",
            data_source="EPA",
            geography="US",
            data_quality_rating=Decimal("4.3")
        ),
        EmissionFactor(
            activity_name="electricity_us",
            co2e_factor=Decimal("0.45"),
            unit="kWh",
            data_source="EPA",
            geography="US",
            data_quality_rating=Decimal("4.8")
        ),
        EmissionFactor(
            activity_name="transport_truck",
            co2e_factor=Decimal("0.12"),
            unit="tkm",
            data_source="DEFRA",
            geography="GLO",
            data_quality_rating=Decimal("3.5")
        ),
    ]

    for factor in factors:
        test_db_session.add(factor)
    test_db_session.commit()

    return factors


@pytest.fixture(scope="function")
def sample_products_with_bom(test_db_session, sample_emission_factors):
    """Create sample products with complete BOM (all components have emission factors)"""
    # Create components (matching emission factor activity_names)
    cotton = Product(
        code="cotton",  # Matches EmissionFactor.activity_name
        name="Cotton Fiber",
        unit="kg",
        is_finished_product=False
    )
    polyester = Product(
        code="polyester",  # Matches EmissionFactor.activity_name
        name="Polyester Fiber",
        unit="kg",
        is_finished_product=False
    )

    # Create finished product
    tshirt = Product(
        code="TSHIRT-001",
        name="Cotton T-Shirt",
        unit="unit",
        is_finished_product=True
    )

    test_db_session.add_all([cotton, polyester, tshirt])
    test_db_session.commit()

    # Create BOM (no level field in base table)
    bom1 = BillOfMaterials(
        parent_product_id=tshirt.id,
        child_product_id=cotton.id,
        quantity=Decimal("0.18")
    )
    bom2 = BillOfMaterials(
        parent_product_id=tshirt.id,
        child_product_id=polyester.id,
        quantity=Decimal("0.02")
    )

    test_db_session.add_all([bom1, bom2])
    test_db_session.commit()

    return {
        'tshirt': tshirt,
        'cotton': cotton,
        'polyester': polyester
    }


class TestValidateDataQualityHappyPath:
    """Scenario 1: Happy Path - All Data Quality Checks Pass"""

    def test_emission_factors_count(self, test_db_session, sample_emission_factors):
        """Test that emission factors count is correct"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        assert quality_report['emission_factors']['count'] == 5

    def test_emission_factors_completeness(self, test_db_session, sample_emission_factors):
        """Test that emission factors have 100% completeness (no nulls)"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        # All required fields should be present
        assert quality_report['emission_factors']['completeness_percent'] == 100.0

    def test_emission_factors_valid_ranges(self, test_db_session, sample_emission_factors):
        """Test that all CO2e factors are non-negative"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        assert quality_report['emission_factors']['valid_ranges'] is True

    def test_emission_factors_average_co2e(self, test_db_session, sample_emission_factors):
        """Test average CO2e factor calculation"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        # Average of: 5.5, 6.2, 2.7, 0.45, 0.12 = 14.97 / 5 = 2.994
        expected_avg = (5.5 + 6.2 + 2.7 + 0.45 + 0.12) / 5
        assert abs(quality_report['emission_factors']['average_co2e_factor'] - expected_avg) < 0.01

    def test_emission_factors_data_sources(self, test_db_session, sample_emission_factors):
        """Test data source breakdown"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        sources = quality_report['emission_factors']['data_sources']
        assert sources['EPA'] == 3  # cotton, plastic_pet, electricity_us
        assert sources['DEFRA'] == 2  # polyester, transport_truck

    def test_products_with_bom_coverage(self, test_db_session, sample_products_with_bom):
        """Test that products with BOM show 100% coverage"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        assert quality_report['products']['finished_products'] == 1
        assert quality_report['products']['with_bom'] == 1
        assert quality_report['products']['bom_coverage_percent'] == 100.0

    def test_bom_completeness_all_components_have_factors(self, test_db_session, sample_products_with_bom):
        """Test BOM completeness when all components have matching emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        # T-shirt has 2 components: cotton and polyester
        assert quality_report['bom_completeness']['total_components'] == 2
        assert quality_report['bom_completeness']['components_with_factors'] == 2
        assert quality_report['bom_completeness']['coverage_percent'] == 100.0
        assert len(quality_report['bom_completeness']['missing_factors']) == 0

    def test_overall_quality_score_perfect(self, test_db_session, sample_products_with_bom):
        """Test overall quality score when everything is perfect"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        # With 100% coverage and high data quality, score should be high (4.0+)
        assert quality_report['overall_quality_score'] >= 4.0
        assert quality_report['overall_quality_score'] <= 5.0

    def test_validation_errors_zero(self, test_db_session, sample_products_with_bom):
        """Test that validation errors are zero in happy path"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        assert quality_report['validation_errors'] == 0

    def test_report_has_timestamp(self, test_db_session, sample_emission_factors):
        """Test that report includes validation timestamp"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        assert 'validation_timestamp' in quality_report
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(quality_report['validation_timestamp'].replace('Z', '+00:00'))


class TestDetectMissingEmissionFactors:
    """Scenario 2: Detect Missing Emission Factors (implicit matching)"""

    def test_component_without_emission_factor(self, test_db_session, sample_emission_factors):
        """Test detection of component without matching emission factor"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create component with code that doesn't match any emission factor
        unknown_material = Product(
            code="UNKNOWN-MATERIAL",  # No EmissionFactor with this activity_name
            name="Unknown Material",
            unit="kg",
            is_finished_product=False
        )

        # Create finished product
        test_product = Product(
            code="TEST-001",
            name="Test Product",
            unit="unit",
            is_finished_product=True
        )

        test_db_session.add_all([unknown_material, test_product])
        test_db_session.commit()

        # Create BOM entry
        bom = BillOfMaterials(
            parent_product_id=test_product.id,
            child_product_id=unknown_material.id,
            quantity=Decimal("1.0")
        )
        test_db_session.add(bom)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Coverage should be less than 100%
        assert quality_report['bom_completeness']['coverage_percent'] < 100.0

        # Missing factor should be identified
        assert 'UNKNOWN-MATERIAL' in quality_report['bom_completeness']['missing_factors']

    def test_multiple_missing_emission_factors(self, test_db_session, sample_emission_factors):
        """Test detection of multiple missing emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create components without emission factors
        unknown1 = Product(code="UNKNOWN-1", name="Unknown Material 1", unit="kg", is_finished_product=False)
        unknown2 = Product(code="UNKNOWN-2", name="Unknown Material 2", unit="kg", is_finished_product=False)
        known = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)

        product = Product(code="TEST-002", name="Test Product 2", unit="unit", is_finished_product=True)

        test_db_session.add_all([unknown1, unknown2, known, product])
        test_db_session.commit()

        # Create BOM with 2 unknown and 1 known
        bom1 = BillOfMaterials(parent_product_id=product.id, child_product_id=unknown1.id, quantity=Decimal("1.0"))
        bom2 = BillOfMaterials(parent_product_id=product.id, child_product_id=unknown2.id, quantity=Decimal("1.0"))
        bom3 = BillOfMaterials(parent_product_id=product.id, child_product_id=known.id, quantity=Decimal("1.0"))

        test_db_session.add_all([bom1, bom2, bom3])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # 1 out of 3 has factor = 33.33%
        assert quality_report['bom_completeness']['total_components'] == 3
        assert quality_report['bom_completeness']['components_with_factors'] == 1
        assert abs(quality_report['bom_completeness']['coverage_percent'] - 33.33) < 0.1

        # Both unknowns should be in missing list
        missing = quality_report['bom_completeness']['missing_factors']
        assert 'UNKNOWN-1' in missing
        assert 'UNKNOWN-2' in missing

    def test_bom_coverage_with_partial_factors(self, test_db_session, sample_emission_factors):
        """Test BOM coverage calculation with partial emission factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create 3 components: 2 with factors, 1 without
        cotton = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)
        polyester = Product(code="polyester", name="Polyester", unit="kg", is_finished_product=False)
        mystery = Product(code="mystery_material", name="Mystery Material", unit="kg", is_finished_product=False)

        product = Product(code="PARTIAL-001", name="Partial Coverage Product", unit="unit", is_finished_product=True)

        test_db_session.add_all([cotton, polyester, mystery, product])
        test_db_session.commit()

        bom1 = BillOfMaterials(parent_product_id=product.id, child_product_id=cotton.id, quantity=Decimal("1.0"))
        bom2 = BillOfMaterials(parent_product_id=product.id, child_product_id=polyester.id, quantity=Decimal("1.0"))
        bom3 = BillOfMaterials(parent_product_id=product.id, child_product_id=mystery.id, quantity=Decimal("1.0"))

        test_db_session.add_all([bom1, bom2, bom3])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # 2 out of 3 = 66.67%
        assert quality_report['bom_completeness']['total_components'] == 3
        assert quality_report['bom_completeness']['components_with_factors'] == 2
        assert abs(quality_report['bom_completeness']['coverage_percent'] - 66.67) < 0.1


class TestDataQualityScores:
    """Scenario 3: Calculate Data Quality Scores"""

    def test_average_data_quality_rating(self, test_db_session):
        """Test average data quality rating calculation"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create emission factors with specific quality ratings
        ef1 = EmissionFactor(
            activity_name="material1",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=Decimal("4.5")
        )
        ef2 = EmissionFactor(
            activity_name="material2",
            co2e_factor=Decimal("3.0"),
            unit="kg",
            data_source="DEFRA",
            data_quality_rating=Decimal("3.5")
        )

        test_db_session.add_all([ef1, ef2])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Average: (4.5 + 3.5) / 2 = 4.0
        assert quality_report['average_data_quality'] == 4.0

    def test_average_data_quality_with_nulls(self, test_db_session):
        """Test average data quality when some factors don't have ratings"""
        from backend.scripts.validate_data_quality import validate_data_quality

        ef1 = EmissionFactor(
            activity_name="material1",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            data_quality_rating=Decimal("4.0")
        )
        ef2 = EmissionFactor(
            activity_name="material2",
            co2e_factor=Decimal("3.0"),
            unit="kg",
            data_source="DEFRA",
            data_quality_rating=None  # No rating
        )

        test_db_session.add_all([ef1, ef2])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Should only average non-null ratings: 4.0
        assert quality_report['average_data_quality'] == 4.0

    def test_overall_quality_score_calculation(self, test_db_session, sample_emission_factors):
        """Test overall quality score includes multiple factors"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create product with full BOM coverage
        cotton = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)
        product = Product(code="TEST-SCORE", name="Test Score Product", unit="unit", is_finished_product=True)

        test_db_session.add_all([cotton, product])
        test_db_session.commit()

        bom = BillOfMaterials(parent_product_id=product.id, child_product_id=cotton.id, quantity=Decimal("1.0"))
        test_db_session.add(bom)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Overall score should be between 1 and 5
        assert 1.0 <= quality_report['overall_quality_score'] <= 5.0

        # With 100% coverage and good data quality, should be > 4.0
        assert quality_report['overall_quality_score'] > 4.0


class TestValidatePositiveCO2eFactors:
    """Scenario 4: Validate Positive CO2e Factors"""

    def test_all_factors_non_negative(self, test_db_session, sample_emission_factors):
        """Test that all emission factors are non-negative"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        # Database constraint enforces this, validation confirms
        assert quality_report['emission_factors']['valid_ranges'] is True

    def test_validation_confirms_constraint(self, test_db_session):
        """Test validation detects if all factors pass range checks"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create factors with valid (positive) values
        ef1 = EmissionFactor(
            activity_name="valid1",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="EPA"
        )
        ef2 = EmissionFactor(
            activity_name="valid2",
            co2e_factor=Decimal("0.0"),  # Zero is valid
            unit="kg",
            data_source="EPA"
        )

        test_db_session.add_all([ef1, ef2])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        assert quality_report['emission_factors']['valid_ranges'] is True
        assert quality_report['validation_errors'] == 0


class TestBOMCoveragePerProduct:
    """Scenario 5: BOM Coverage Report Per Product"""

    def test_product_details_structure(self, test_db_session, sample_products_with_bom):
        """Test that product details have correct structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        product_details = quality_report['products']['product_details']
        assert len(product_details) == 1  # One finished product

        product = product_details[0]
        assert 'code' in product
        assert 'name' in product
        assert 'bom_component_count' in product
        assert 'components_with_factors' in product
        assert 'coverage_percent' in product

    def test_product_bom_component_count(self, test_db_session, sample_products_with_bom):
        """Test BOM component count per product"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        product = quality_report['products']['product_details'][0]

        # T-shirt has 2 components
        assert product['bom_component_count'] == 2
        assert product['components_with_factors'] == 2

    def test_product_coverage_percent(self, test_db_session, sample_products_with_bom):
        """Test coverage percentage per product"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        product = quality_report['products']['product_details'][0]

        # All components have factors
        assert product['coverage_percent'] == 100.0

    def test_multiple_products_with_different_coverage(self, test_db_session, sample_emission_factors):
        """Test report for multiple products with varying coverage"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Product 1: 100% coverage (2 components with factors)
        cotton = Product(code="cotton", name="Cotton", unit="kg", is_finished_product=False)
        polyester = Product(code="polyester", name="Polyester", unit="kg", is_finished_product=False)
        product1 = Product(code="PROD-001", name="Product 1", unit="unit", is_finished_product=True)

        # Product 2: 50% coverage (1 with factor, 1 without)
        plastic = Product(code="plastic_pet", name="Plastic PET", unit="kg", is_finished_product=False)
        unknown = Product(code="unknown_mat", name="Unknown", unit="kg", is_finished_product=False)
        product2 = Product(code="PROD-002", name="Product 2", unit="unit", is_finished_product=True)

        test_db_session.add_all([cotton, polyester, product1, plastic, unknown, product2])
        test_db_session.commit()

        # Product 1 BOM
        bom1_1 = BillOfMaterials(parent_product_id=product1.id, child_product_id=cotton.id, quantity=Decimal("1.0"))
        bom1_2 = BillOfMaterials(parent_product_id=product1.id, child_product_id=polyester.id, quantity=Decimal("1.0"))

        # Product 2 BOM
        bom2_1 = BillOfMaterials(parent_product_id=product2.id, child_product_id=plastic.id, quantity=Decimal("1.0"))
        bom2_2 = BillOfMaterials(parent_product_id=product2.id, child_product_id=unknown.id, quantity=Decimal("1.0"))

        test_db_session.add_all([bom1_1, bom1_2, bom2_1, bom2_2])
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        product_details = quality_report['products']['product_details']
        assert len(product_details) == 2

        # Find products by code
        prod1_report = next(p for p in product_details if p['code'] == 'PROD-001')
        prod2_report = next(p for p in product_details if p['code'] == 'PROD-002')

        # Product 1: 100% coverage
        assert prod1_report['bom_component_count'] == 2
        assert prod1_report['components_with_factors'] == 2
        assert prod1_report['coverage_percent'] == 100.0

        # Product 2: 50% coverage
        assert prod2_report['bom_component_count'] == 2
        assert prod2_report['components_with_factors'] == 1
        assert prod2_report['coverage_percent'] == 50.0

    def test_product_without_bom(self, test_db_session, sample_emission_factors):
        """Test that products without BOM are handled correctly"""
        from backend.scripts.validate_data_quality import validate_data_quality

        # Create finished product with no BOM
        product = Product(
            code="NO-BOM",
            name="Product Without BOM",
            unit="unit",
            is_finished_product=True
        )
        test_db_session.add(product)
        test_db_session.commit()

        quality_report = validate_data_quality(test_db_session)

        # Should show 1 finished product, 0 with BOM
        assert quality_report['products']['finished_products'] == 1
        assert quality_report['products']['with_bom'] == 0
        assert quality_report['products']['bom_coverage_percent'] == 0.0


class TestReportSchema:
    """Test that report structure matches specification"""

    def test_report_top_level_keys(self, test_db_session, sample_emission_factors):
        """Test report contains all required top-level keys"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)

        required_keys = [
            'validation_timestamp',
            'emission_factors',
            'products',
            'bom_completeness',
            'average_data_quality',
            'overall_quality_score',
            'validation_errors',
            'error_details'
        ]

        for key in required_keys:
            assert key in quality_report, f"Missing required key: {key}"

    def test_emission_factors_section_keys(self, test_db_session, sample_emission_factors):
        """Test emission_factors section structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)
        ef_section = quality_report['emission_factors']

        required_keys = ['count', 'completeness_percent', 'average_co2e_factor', 'data_sources', 'valid_ranges']
        for key in required_keys:
            assert key in ef_section, f"Missing key in emission_factors: {key}"

    def test_products_section_keys(self, test_db_session, sample_emission_factors):
        """Test products section structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)
        products_section = quality_report['products']

        required_keys = ['finished_products', 'with_bom', 'bom_coverage_percent', 'product_details']
        for key in required_keys:
            assert key in products_section, f"Missing key in products: {key}"

    def test_bom_completeness_section_keys(self, test_db_session, sample_emission_factors):
        """Test bom_completeness section structure"""
        from backend.scripts.validate_data_quality import validate_data_quality

        quality_report = validate_data_quality(test_db_session)
        bom_section = quality_report['bom_completeness']

        required_keys = ['total_components', 'components_with_factors', 'coverage_percent', 'missing_factors']
        for key in required_keys:
            assert key in bom_section, f"Missing key in bom_completeness: {key}"
