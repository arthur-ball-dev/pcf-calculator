"""
Test Seed Data Loading Script
TASK-DATA-003: Comprehensive tests for seed_data.py

Test Scenarios:
1. Happy Path - Load All Data (emission factors, products, BOMs)
2. Idempotent Execution - No duplicates on re-run
3. Validation - Missing Emission Factor Detection
4. CSV to Database Mapping - Verify correct data transfer
5. BOM JSON to Database - Verify relationships created
6. Energy and Transport Data - Verify auxiliary components created
"""

import pytest
import os
import json
from pathlib import Path
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
def project_root():
    """Get project root directory"""
    # Assumes tests are in backend/tests/test_data/
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent


# ============================================================================
# Test Scenario 1: Happy Path - Load All Data
# ============================================================================

class TestLoadEmissionFactors:
    """Test loading emission factors from CSV"""

    def test_load_emission_factors_from_csv(self, test_db_session: Session, project_root: Path):
        """Test that all 20 emission factors are loaded from CSV"""
        # Import the function we'll create
        from backend.scripts.seed_data import load_emission_factors

        # Load emission factors
        loaded_count = load_emission_factors(test_db_session)

        # Should load exactly 20 emission factors
        assert loaded_count == 20

        # Verify they're in the database
        ef_count = test_db_session.query(EmissionFactor).count()
        assert ef_count == 20

    def test_emission_factors_data_integrity(self, test_db_session: Session, project_root: Path):
        """Test that emission factors have correct data"""
        from backend.scripts.seed_data import load_emission_factors

        load_emission_factors(test_db_session)

        # Check specific emission factors
        cotton = test_db_session.query(EmissionFactor).filter_by(
            activity_name="cotton"
        ).first()

        assert cotton is not None
        assert float(cotton.co2e_factor) == 5.0
        assert cotton.unit == "kg"
        assert cotton.data_source == "EPA"
        assert cotton.geography == "GLO"

        # Check electricity_us
        electricity = test_db_session.query(EmissionFactor).filter_by(
            activity_name="electricity_us"
        ).first()

        assert electricity is not None
        assert float(electricity.co2e_factor) == 0.4
        assert electricity.unit == "kWh"

        # Check transport_truck
        truck = test_db_session.query(EmissionFactor).filter_by(
            activity_name="transport_truck"
        ).first()

        assert truck is not None
        assert float(truck.co2e_factor) == 0.1
        assert truck.unit == "tkm"


class TestLoadProducts:
    """Test loading products from JSON BOMs"""

    def test_load_all_products(self, test_db_session: Session, project_root: Path):
        """Test that all 3 finished products are loaded"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        # Load emission factors first (required for validation)
        load_emission_factors(test_db_session)

        # Load products
        loaded_count = load_products_and_boms(test_db_session)

        # Should load 3 finished products
        finished_products = test_db_session.query(Product).filter_by(
            is_finished_product=True
        ).all()

        assert len(finished_products) == 3

        # Verify product codes
        product_codes = [p.code for p in finished_products]
        assert "TSHIRT-001" in product_codes
        assert "BOTTLE-001" in product_codes
        assert "CASE-001" in product_codes

    def test_product_details(self, test_db_session: Session, project_root: Path):
        """Test that products have correct attributes"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Check T-Shirt
        tshirt = test_db_session.query(Product).filter_by(code="TSHIRT-001").first()
        assert tshirt is not None
        assert tshirt.name == "Cotton T-Shirt - Realistic"
        assert tshirt.unit == "unit"
        assert tshirt.is_finished_product is True

        # Check Water Bottle
        bottle = test_db_session.query(Product).filter_by(code="BOTTLE-001").first()
        assert bottle is not None
        assert bottle.name == "Water Bottle - Realistic"
        assert bottle.unit == "unit"
        assert bottle.is_finished_product is True

        # Check Phone Case
        case = test_db_session.query(Product).filter_by(code="CASE-001").first()
        assert case is not None
        assert case.name == "Phone Case - Realistic"
        assert case.unit == "unit"
        assert case.is_finished_product is True


class TestLoadBillOfMaterials:
    """Test loading BOM relationships from JSON"""

    def test_load_bom_relationships(self, test_db_session: Session, project_root: Path):
        """Test that BOM relationships are created"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Check that BOMs exist
        bom_count = test_db_session.query(BillOfMaterials).count()
        assert bom_count >= 10  # At least 10 BOM relationships

    def test_tshirt_bom_structure(self, test_db_session: Session, project_root: Path):
        """Test T-Shirt BOM has correct components"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        tshirt = test_db_session.query(Product).filter_by(code="TSHIRT-001").first()
        assert tshirt is not None

        # T-Shirt should have BOM items
        assert len(tshirt.bom_items) >= 5

        # Check for cotton component
        cotton_bom = [bom for bom in tshirt.bom_items
                      if bom.child_product.code == "cotton"][0]
        assert float(cotton_bom.quantity) == 0.18
        assert cotton_bom.unit == "kg"

    def test_water_bottle_bom_structure(self, test_db_session: Session, project_root: Path):
        """Test Water Bottle BOM has correct components"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        bottle = test_db_session.query(Product).filter_by(code="BOTTLE-001").first()
        assert bottle is not None

        # Water bottle should have BOM items
        assert len(bottle.bom_items) >= 4

        # Check for plastic_pet component
        pet_bom = [bom for bom in bottle.bom_items
                   if bom.child_product.code == "plastic_pet"][0]
        assert float(pet_bom.quantity) == 0.023
        assert pet_bom.unit == "kg"

    def test_phone_case_bom_structure(self, test_db_session: Session, project_root: Path):
        """Test Phone Case BOM has correct components"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        case = test_db_session.query(Product).filter_by(code="CASE-001").first()
        assert case is not None

        # Phone case should have BOM items
        assert len(case.bom_items) >= 5

        # Check for plastic_abs component
        abs_bom = [bom for bom in case.bom_items
                   if bom.child_product.code == "plastic_abs"][0]
        assert float(abs_bom.quantity) == 0.025
        assert abs_bom.unit == "kg"


class TestLoadEnergyAndTransport:
    """Test loading energy and transport data as components"""

    def test_energy_components_created(self, test_db_session: Session, project_root: Path):
        """Test that energy consumption is stored as BOM components"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        tshirt = test_db_session.query(Product).filter_by(code="TSHIRT-001").first()

        # Should have electricity component
        electricity_bom = [bom for bom in tshirt.bom_items
                          if bom.child_product.code == "electricity_us"]

        assert len(electricity_bom) == 1
        assert float(electricity_bom[0].quantity) == 2.5
        assert electricity_bom[0].unit == "kWh"

    def test_transport_components_created(self, test_db_session: Session, project_root: Path):
        """Test that transport is stored as BOM components (tkm = tonne-km)"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        tshirt = test_db_session.query(Product).filter_by(code="TSHIRT-001").first()

        # Should have transport_truck component
        truck_bom = [bom for bom in tshirt.bom_items
                     if bom.child_product.code == "transport_truck"]

        assert len(truck_bom) == 1
        # Transport should be in tkm (tonne-km) = mass_kg * distance_km / 1000
        # 0.203 kg * 500 km / 1000 = 0.1015 tkm
        expected_tkm = (0.203 * 500) / 1000
        assert abs(float(truck_bom[0].quantity) - expected_tkm) < 0.001
        assert truck_bom[0].unit == "tkm"


# ============================================================================
# Test Scenario 2: Idempotent Execution
# ============================================================================

class TestIdempotency:
    """Test that seed script can be run multiple times safely"""

    def test_emission_factors_idempotent(self, test_db_session: Session, project_root: Path):
        """Test that loading emission factors twice doesn't create duplicates"""
        from backend.scripts.seed_data import load_emission_factors

        # Load once
        count1 = load_emission_factors(test_db_session)
        ef_count_1 = test_db_session.query(EmissionFactor).count()

        # Load again
        count2 = load_emission_factors(test_db_session)
        ef_count_2 = test_db_session.query(EmissionFactor).count()

        # Should still have exactly 20 emission factors
        assert ef_count_1 == 20
        assert ef_count_2 == 20
        assert count2 == 0  # Second run should load 0 new records

    def test_products_idempotent(self, test_db_session: Session, project_root: Path):
        """Test that loading products twice doesn't create duplicates"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)

        # Load once
        load_products_and_boms(test_db_session)
        product_count_1 = test_db_session.query(Product).count()
        bom_count_1 = test_db_session.query(BillOfMaterials).count()

        # Load again
        load_products_and_boms(test_db_session)
        product_count_2 = test_db_session.query(Product).count()
        bom_count_2 = test_db_session.query(BillOfMaterials).count()

        # Should have same counts
        assert product_count_1 == product_count_2
        assert bom_count_1 == bom_count_2

    def test_full_seed_idempotent(self, test_db_session: Session, project_root: Path):
        """Test that running entire seed process twice is safe"""
        from backend.scripts.seed_data import seed_all_data

        # Run seed twice
        seed_all_data(test_db_session)

        ef_count_1 = test_db_session.query(EmissionFactor).count()
        product_count_1 = test_db_session.query(Product).count()
        bom_count_1 = test_db_session.query(BillOfMaterials).count()

        seed_all_data(test_db_session)

        ef_count_2 = test_db_session.query(EmissionFactor).count()
        product_count_2 = test_db_session.query(Product).count()
        bom_count_2 = test_db_session.query(BillOfMaterials).count()

        # All counts should remain the same
        assert ef_count_1 == ef_count_2
        assert product_count_1 == product_count_2
        assert bom_count_1 == bom_count_2


# ============================================================================
# Test Scenario 3: Validation - Missing Emission Factor
# ============================================================================

class TestValidation:
    """Test validation of data before loading"""

    def test_missing_emission_factor_detection(self, test_db_session: Session, project_root: Path):
        """Test that missing emission factors are detected"""
        from backend.scripts.seed_data import validate_bom_emission_factors

        # Load only emission factors
        from backend.scripts.seed_data import load_emission_factors
        load_emission_factors(test_db_session)

        # Create test BOM data with invalid component
        invalid_bom = {
            "bill_of_materials": [
                {"component_name": "nonexistent_material", "quantity": 1.0, "unit": "kg"}
            ]
        }

        # Should detect missing emission factor
        is_valid, missing = validate_bom_emission_factors(
            test_db_session,
            invalid_bom["bill_of_materials"]
        )

        assert is_valid is False
        assert "nonexistent_material" in missing

    def test_valid_emission_factors(self, test_db_session: Session, project_root: Path):
        """Test that valid BOMs pass validation"""
        from backend.scripts.seed_data import load_emission_factors, validate_bom_emission_factors

        load_emission_factors(test_db_session)

        # Valid BOM data
        valid_bom = {
            "bill_of_materials": [
                {"component_name": "cotton", "quantity": 0.2, "unit": "kg"},
                {"component_name": "polyester", "quantity": 0.01, "unit": "kg"}
            ]
        }

        # Should pass validation
        is_valid, missing = validate_bom_emission_factors(
            test_db_session,
            valid_bom["bill_of_materials"]
        )

        assert is_valid is True
        assert len(missing) == 0


# ============================================================================
# Test Scenario 4: CSV to Database Mapping
# ============================================================================

class TestCSVMapping:
    """Test that CSV data maps correctly to database"""

    def test_csv_columns_mapped_correctly(self, test_db_session: Session, project_root: Path):
        """Test all CSV columns are mapped to database fields"""
        from backend.scripts.seed_data import load_emission_factors
        import pandas as pd

        # Load emission factors
        load_emission_factors(test_db_session)

        # Read CSV
        csv_path = project_root / "data" / "emission_factors_simple.csv"
        df = pd.read_csv(csv_path)

        # Check each row is in database
        for _, row in df.iterrows():
            ef = test_db_session.query(EmissionFactor).filter_by(
                activity_name=row['activity_name']
            ).first()

            assert ef is not None
            assert float(ef.co2e_factor) == float(row['co2e_factor'])
            assert ef.unit == row['unit']
            assert ef.data_source == row['data_source']
            assert ef.geography == row['geography']

    def test_csv_row_count_matches(self, test_db_session: Session, project_root: Path):
        """Test that number of rows in CSV matches database"""
        from backend.scripts.seed_data import load_emission_factors
        import pandas as pd

        load_emission_factors(test_db_session)

        # Read CSV
        csv_path = project_root / "data" / "emission_factors_simple.csv"
        df = pd.read_csv(csv_path)

        # Count in database
        ef_count = test_db_session.query(EmissionFactor).count()

        # Should match
        assert ef_count == len(df)


# ============================================================================
# Test Scenario 5: BOM JSON to Database
# ============================================================================

class TestJSONMapping:
    """Test that JSON BOM data maps correctly to database"""

    def test_json_product_fields_mapped(self, test_db_session: Session, project_root: Path):
        """Test that product fields from JSON are mapped correctly"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Read original JSON
        json_path = project_root / "data" / "bom_tshirt_realistic.json"
        with open(json_path, 'r') as f:
            bom_data = json.load(f)

        # Find product in database
        tshirt = test_db_session.query(Product).filter_by(
            code=bom_data['product']['code']
        ).first()

        assert tshirt is not None
        assert tshirt.code == bom_data['product']['code']
        assert tshirt.name == bom_data['product']['name']
        assert tshirt.unit == bom_data['product']['unit']
        assert tshirt.is_finished_product == bom_data['product']['is_finished_product']

    def test_json_bom_quantities_preserved(self, test_db_session: Session, project_root: Path):
        """Test that BOM quantities from JSON are preserved"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Read original JSON
        json_path = project_root / "data" / "bom_tshirt_realistic.json"
        with open(json_path, 'r') as f:
            bom_data = json.load(f)

        tshirt = test_db_session.query(Product).filter_by(code="TSHIRT-001").first()

        # Check each BOM item from JSON
        for json_item in bom_data['bill_of_materials']:
            # Find matching BOM in database
            db_bom = [bom for bom in tshirt.bom_items
                      if bom.child_product.code == json_item['component_name']][0]

            assert float(db_bom.quantity) == json_item['quantity']
            assert db_bom.unit == json_item['unit']


# ============================================================================
# Test CLI and Main Function
# ============================================================================

class TestMainFunction:
    """Test main seed script execution"""

    def test_seed_all_data_function(self, test_db_session: Session, project_root: Path):
        """Test that seed_all_data() loads everything"""
        from backend.scripts.seed_data import seed_all_data

        # Run seed
        result = seed_all_data(test_db_session)

        # Check result summary
        assert result['emission_factors_loaded'] == 20
        assert result['products_loaded'] >= 3
        assert result['bom_relationships_created'] >= 10

        # Verify database state
        ef_count = test_db_session.query(EmissionFactor).count()
        product_count = test_db_session.query(Product).count()
        bom_count = test_db_session.query(BillOfMaterials).count()

        assert ef_count == 20
        assert product_count >= 3
        assert bom_count >= 10

    def test_seed_summary_output(self, test_db_session: Session, project_root: Path):
        """Test that seed function returns summary"""
        from backend.scripts.seed_data import seed_all_data

        result = seed_all_data(test_db_session)

        # Should have summary keys
        assert 'emission_factors_loaded' in result
        assert 'products_loaded' in result
        assert 'bom_relationships_created' in result
        assert 'status' in result

        assert result['status'] == 'success'


# ============================================================================
# Test Component Creation
# ============================================================================

class TestComponentCreation:
    """Test that components are created as products"""

    def test_material_components_created(self, test_db_session: Session, project_root: Path):
        """Test that material components are created as products"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Check that cotton exists as a product
        cotton = test_db_session.query(Product).filter_by(code="cotton").first()
        assert cotton is not None
        assert cotton.is_finished_product is False
        assert cotton.unit == "kg"

        # Check that polyester exists
        polyester = test_db_session.query(Product).filter_by(code="polyester").first()
        assert polyester is not None
        assert polyester.is_finished_product is False

    def test_energy_component_created(self, test_db_session: Session, project_root: Path):
        """Test that energy component is created as a product"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Check that electricity_us exists as a product
        electricity = test_db_session.query(Product).filter_by(
            code="electricity_us"
        ).first()
        assert electricity is not None
        assert electricity.is_finished_product is False
        assert electricity.unit == "kWh"

    def test_transport_component_created(self, test_db_session: Session, project_root: Path):
        """Test that transport component is created as a product"""
        from backend.scripts.seed_data import load_emission_factors, load_products_and_boms

        load_emission_factors(test_db_session)
        load_products_and_boms(test_db_session)

        # Check that transport_truck exists as a product
        truck = test_db_session.query(Product).filter_by(
            code="transport_truck"
        ).first()
        assert truck is not None
        assert truck.is_finished_product is False
        assert truck.unit == "tkm"
