"""
Test SQLAlchemy ORM Models
TASK-DB-003: Comprehensive tests for all 5 models

Test Scenarios:
1. Happy Path - Create Product with Type Hints
2. Relationship - Product with BOM
3. EmissionFactor with Unique Constraint
4. PCFCalculation with JSON Fields
5. Cascade Delete
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

# Import models (will be created in implementation step)
from backend.models import (
    Base,
    Product,
    EmissionFactor,
    BillOfMaterials,
    PCFCalculation,
    CalculationDetail
)


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute("PRAGMA foreign_keys = ON")
    session.commit()

    yield session

    session.close()


# ============================================================================
# Test Scenario 1: Happy Path - Create Product with Type Hints
# ============================================================================

class TestProductModel:
    """Test Product model CRUD operations and type hints"""

    def test_create_product_with_type_hints(self, db_session: Session):
        """Test creating a product with all type hints validated"""
        product = Product(
            code="TEST-001",
            name="Test Product",
            unit="kg",
            category="material",
            is_finished_product=False
        )
        db_session.add(product)
        db_session.commit()

        # Product created with auto-generated UUID id
        assert product.id is not None
        assert isinstance(product.id, str)
        assert len(product.id) == 32  # UUID hex string length

        # Type hints validated
        assert product.code == "TEST-001"
        assert isinstance(product.code, str)
        assert product.name == "Test Product"
        assert isinstance(product.name, str)
        assert product.unit == "kg"
        assert isinstance(product.unit, str)

        # Default values
        assert product.is_finished_product is False
        assert product.created_at is not None
        assert product.updated_at is not None

    def test_product_unique_code_constraint(self, db_session: Session):
        """Test that product code must be unique"""
        product1 = Product(code="DUP-001", name="Product 1")
        product2 = Product(code="DUP-001", name="Product 2")

        db_session.add(product1)
        db_session.commit()

        # Second product with same code should fail
        db_session.add(product2)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "UNIQUE constraint failed" in str(exc_info.value)
        assert "products.code" in str(exc_info.value)

    def test_product_unit_check_constraint(self, db_session: Session):
        """Test that product unit must be from allowed list"""
        product = Product(
            code="INVALID-001",
            name="Invalid Unit Product",
            unit="invalid_unit"  # Not in allowed list
        )

        db_session.add(product)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "CHECK constraint failed" in str(exc_info.value)

    def test_product_json_metadata_field(self, db_session: Session):
        """Test JSON metadata field serialization"""
        metadata = {
            "supplier": "ACME Corp",
            "certification": "ISO 14001",
            "custom_field": 123
        }

        product = Product(
            code="JSON-001",
            name="Product with Metadata",
            metadata=metadata
        )

        db_session.add(product)
        db_session.commit()

        # Refresh from database
        db_session.refresh(product)

        assert product.metadata is not None
        assert product.metadata["supplier"] == "ACME Corp"
        assert product.metadata["certification"] == "ISO 14001"
        assert product.metadata["custom_field"] == 123

    def test_product_soft_delete(self, db_session: Session):
        """Test soft delete timestamp"""
        product = Product(code="DEL-001", name="To be deleted")
        db_session.add(product)
        db_session.commit()

        # Soft delete - set deleted_at timestamp
        product.deleted_at = datetime.utcnow()
        db_session.commit()

        assert product.deleted_at is not None


# ============================================================================
# Test Scenario 2: Relationship - Product with BOM
# ============================================================================

class TestBillOfMaterialsModel:
    """Test BillOfMaterials model and relationships"""

    def test_create_bom_relationship(self, db_session: Session):
        """Test creating BOM relationship between parent and child products"""
        parent = Product(
            code="PARENT-001",
            name="Parent Product",
            is_finished_product=True
        )
        child = Product(
            code="CHILD-001",
            name="Child Component"
        )

        bom = BillOfMaterials(
            parent_product=parent,
            child_product=child,
            quantity=2.5,
            unit="kg"
        )

        db_session.add_all([parent, child, bom])
        db_session.commit()

        # Relationship working via SQLAlchemy
        assert len(parent.bom_items) == 1
        assert parent.bom_items[0].child_product.code == "CHILD-001"
        assert parent.bom_items[0].quantity == 2.5
        assert parent.bom_items[0].unit == "kg"

        # Reverse relationship
        assert len(child.used_in_boms) == 1
        assert child.used_in_boms[0].parent_product.code == "PARENT-001"

    def test_bom_prevent_self_reference(self, db_session: Session):
        """Test that BOM cannot have parent_product_id == child_product_id"""
        product = Product(code="SELF-001", name="Self Product")
        db_session.add(product)
        db_session.commit()

        # Try to create self-referencing BOM
        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=product.id,
            quantity=1.0
        )

        db_session.add(bom)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "CHECK constraint failed" in str(exc_info.value)

    def test_bom_quantity_must_be_positive(self, db_session: Session):
        """Test that BOM quantity must be > 0"""
        parent = Product(code="P-002", name="Parent")
        child = Product(code="C-002", name="Child")

        db_session.add_all([parent, child])
        db_session.commit()

        # Zero quantity should fail
        bom = BillOfMaterials(
            parent_product_id=parent.id,
            child_product_id=child.id,
            quantity=0.0
        )

        db_session.add(bom)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "CHECK constraint failed" in str(exc_info.value)

    def test_bom_unique_parent_child_pair(self, db_session: Session):
        """Test that parent-child pair must be unique"""
        parent = Product(code="P-003", name="Parent")
        child = Product(code="C-003", name="Child")

        bom1 = BillOfMaterials(
            parent_product=parent,
            child_product=child,
            quantity=1.0
        )

        bom2 = BillOfMaterials(
            parent_product=parent,
            child_product=child,
            quantity=2.0
        )

        db_session.add_all([parent, child, bom1])
        db_session.commit()

        # Second BOM with same parent-child should fail
        db_session.add(bom2)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "UNIQUE constraint failed" in str(exc_info.value)


# ============================================================================
# Test Scenario 3: EmissionFactor with Unique Constraint
# ============================================================================

class TestEmissionFactorModel:
    """Test EmissionFactor model and constraints"""

    def test_create_emission_factor(self, db_session: Session):
        """Test creating emission factor with all required fields"""
        ef = EmissionFactor(
            activity_name="cotton",
            co2e_factor=5.0,
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=0.85
        )

        db_session.add(ef)
        db_session.commit()

        assert ef.id is not None
        assert ef.activity_name == "cotton"
        assert ef.co2e_factor == 5.0
        assert ef.unit == "kg"
        assert ef.data_source == "EPA"
        assert ef.geography == "GLO"
        assert ef.reference_year == 2023
        assert ef.data_quality_rating == 0.85

    def test_emission_factor_unique_constraint(self, db_session: Session):
        """Test unique constraint on (activity_name, data_source, geography, reference_year)"""
        ef1 = EmissionFactor(
            activity_name="cotton",
            co2e_factor=5.0,
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023
        )

        ef2 = EmissionFactor(
            activity_name="cotton",
            co2e_factor=5.5,  # Different factor
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023
        )

        db_session.add(ef1)
        db_session.commit()

        # Second emission factor with same composite key should fail
        db_session.add(ef2)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "UNIQUE constraint failed" in str(exc_info.value)
        assert "emission_factors" in str(exc_info.value)

    def test_emission_factor_non_negative_constraint(self, db_session: Session):
        """Test that co2e_factor must be non-negative"""
        ef = EmissionFactor(
            activity_name="invalid",
            co2e_factor=-1.0,  # Negative value
            unit="kg",
            data_source="TEST",
            geography="GLO"
        )

        db_session.add(ef)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "CHECK constraint failed" in str(exc_info.value)

    def test_emission_factor_with_uncertainty(self, db_session: Session):
        """Test emission factor with uncertainty range"""
        ef = EmissionFactor(
            activity_name="polyester",
            co2e_factor=6.0,
            unit="kg",
            data_source="EPA",
            geography="US",
            reference_year=2023,
            uncertainty_min=5.5,
            uncertainty_max=6.5
        )

        db_session.add(ef)
        db_session.commit()

        assert ef.uncertainty_min == 5.5
        assert ef.uncertainty_max == 6.5


# ============================================================================
# Test Scenario 4: PCFCalculation with JSON Fields
# ============================================================================

class TestPCFCalculationModel:
    """Test PCFCalculation model with JSON fields"""

    def test_create_calculation_with_json_breakdown(self, db_session: Session):
        """Test creating PCF calculation with JSON breakdown field"""
        product = Product(code="CALC-001", name="Calculated Product")
        db_session.add(product)
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=8.43,
            materials_co2e=6.8,
            energy_co2e=0.95,
            transport_co2e=0.68,
            status="completed",
            breakdown={
                "materials": 6.8,
                "energy": 0.95,
                "transport": 0.68
            }
        )

        db_session.add(calc)
        db_session.commit()

        # JSON field stored correctly
        assert calc.breakdown is not None
        assert calc.breakdown["materials"] == 6.8
        assert calc.breakdown["energy"] == 0.95
        assert calc.breakdown["transport"] == 0.68
        assert calc.status == "completed"

    def test_calculation_default_values(self, db_session: Session):
        """Test calculation default values"""
        product = Product(code="CALC-002", name="Product 2")
        db_session.add(product)
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=10.0
        )

        db_session.add(calc)
        db_session.commit()

        # Default values should be set
        assert calc.calculation_type == "cradle_to_gate"
        assert calc.status == "completed"
        assert calc.created_at is not None

    def test_calculation_type_check_constraint(self, db_session: Session):
        """Test that calculation_type must be from allowed values"""
        product = Product(code="CALC-003", name="Product 3")
        db_session.add(product)
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=5.0,
            calculation_type="invalid_type"
        )

        db_session.add(calc)
        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "CHECK constraint failed" in str(exc_info.value)

    def test_calculation_with_input_data_json(self, db_session: Session):
        """Test calculation with complex input_data JSON"""
        product = Product(code="CALC-004", name="Product 4")
        db_session.add(product)
        db_session.commit()

        input_data = {
            "bom": [
                {"component": "cotton", "quantity": 0.18},
                {"component": "polyester", "quantity": 0.015}
            ],
            "energy": {"electricity_kwh": 2.5},
            "transport": {"distance_km": 500}
        }

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=7.5,
            input_data=input_data
        )

        db_session.add(calc)
        db_session.commit()

        db_session.refresh(calc)

        assert calc.input_data is not None
        assert len(calc.input_data["bom"]) == 2
        assert calc.input_data["energy"]["electricity_kwh"] == 2.5


# ============================================================================
# Test Scenario 5: Cascade Delete
# ============================================================================

class TestCascadeDelete:
    """Test cascade delete behavior"""

    def test_delete_product_cascades_to_bom(self, db_session: Session):
        """Test that deleting parent product also deletes BOM entries"""
        parent = Product(code="PARENT-002", name="Parent")
        child = Product(code="CHILD-002", name="Child")

        bom = BillOfMaterials(
            parent_product=parent,
            child_product=child,
            quantity=1.0
        )

        db_session.add_all([parent, child, bom])
        db_session.commit()

        parent_id = parent.id

        # Delete parent product
        db_session.delete(parent)
        db_session.commit()

        # BOM entry should also be deleted (CASCADE)
        bom_count = db_session.query(BillOfMaterials).filter_by(
            parent_product_id=parent_id
        ).count()

        assert bom_count == 0

    def test_delete_calculation_cascades_to_details(self, db_session: Session):
        """Test that deleting calculation also deletes calculation details"""
        product = Product(code="CASCADE-001", name="Product")
        db_session.add(product)
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=10.0
        )
        db_session.add(calc)
        db_session.commit()

        detail1 = CalculationDetail(
            calculation_id=calc.id,
            component_name="Component 1",
            emissions_kg_co2e=5.0
        )
        detail2 = CalculationDetail(
            calculation_id=calc.id,
            component_name="Component 2",
            emissions_kg_co2e=5.0
        )

        db_session.add_all([detail1, detail2])
        db_session.commit()

        calc_id = calc.id

        # Delete calculation
        db_session.delete(calc)
        db_session.commit()

        # Details should also be deleted (CASCADE)
        detail_count = db_session.query(CalculationDetail).filter_by(
            calculation_id=calc_id
        ).count()

        assert detail_count == 0


# ============================================================================
# Test CalculationDetail Model
# ============================================================================

class TestCalculationDetailModel:
    """Test CalculationDetail model"""

    def test_create_calculation_detail(self, db_session: Session):
        """Test creating calculation detail"""
        product = Product(code="DETAIL-001", name="Product")
        component = Product(code="COMP-001", name="Component")
        db_session.add_all([product, component])
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=5.0
        )
        db_session.add(calc)
        db_session.commit()

        detail = CalculationDetail(
            calculation_id=calc.id,
            component_id=component.id,
            component_name="Component",
            component_level=1,
            quantity=2.5,
            unit="kg",
            emissions_kg_co2e=3.5
        )

        db_session.add(detail)
        db_session.commit()

        assert detail.id is not None
        assert detail.calculation_id == calc.id
        assert detail.component_id == component.id
        assert detail.component_name == "Component"
        assert detail.component_level == 1
        assert detail.quantity == 2.5
        assert detail.unit == "kg"
        assert detail.emissions_kg_co2e == 3.5

    def test_calculation_detail_relationship(self, db_session: Session):
        """Test relationship between calculation and details"""
        product = Product(code="REL-001", name="Product")
        db_session.add(product)
        db_session.commit()

        calc = PCFCalculation(
            product_id=product.id,
            total_co2e_kg=10.0
        )
        db_session.add(calc)
        db_session.commit()

        detail1 = CalculationDetail(
            calculation_id=calc.id,
            component_name="Component 1",
            emissions_kg_co2e=4.0
        )
        detail2 = CalculationDetail(
            calculation_id=calc.id,
            component_name="Component 2",
            emissions_kg_co2e=6.0
        )

        db_session.add_all([detail1, detail2])
        db_session.commit()

        # Refresh to load relationship
        db_session.refresh(calc)

        # Check relationship
        assert len(calc.details) == 2
        component_names = [d.component_name for d in calc.details]
        assert "Component 1" in component_names
        assert "Component 2" in component_names


# ============================================================================
# Integration Tests - All Models Together
# ============================================================================

class TestModelsIntegration:
    """Test integration of all models together"""

    def test_complete_product_lifecycle(self, db_session: Session):
        """Test creating product, BOM, emission factors, and calculation"""
        # Create products
        tshirt = Product(
            code="TSHIRT-001",
            name="Cotton T-Shirt",
            unit="unit",
            category="apparel",
            is_finished_product=True
        )
        cotton = Product(
            code="COTTON-001",
            name="Cotton Fabric",
            unit="kg",
            category="material"
        )

        # Create BOM
        bom = BillOfMaterials(
            parent_product=tshirt,
            child_product=cotton,
            quantity=0.18,
            unit="kg"
        )

        # Create emission factor
        ef = EmissionFactor(
            activity_name="Cotton Fabric",
            co2e_factor=5.0,
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023
        )

        db_session.add_all([tshirt, cotton, bom, ef])
        db_session.commit()

        # Create calculation
        calc = PCFCalculation(
            product_id=tshirt.id,
            total_co2e_kg=0.9,
            materials_co2e=0.9,
            breakdown={"cotton": 0.9}
        )

        db_session.add(calc)
        db_session.commit()

        # Create calculation detail
        detail = CalculationDetail(
            calculation_id=calc.id,
            component_id=cotton.id,
            component_name="Cotton Fabric",
            component_level=1,
            quantity=0.18,
            unit="kg",
            emission_factor_id=ef.id,
            emissions_kg_co2e=0.9
        )

        db_session.add(detail)
        db_session.commit()

        # Verify all relationships
        assert len(tshirt.bom_items) == 1
        assert tshirt.bom_items[0].child_product.code == "COTTON-001"
        assert len(calc.details) == 1
        assert calc.details[0].component_name == "Cotton Fabric"

    def test_query_performance_with_relationships(self, db_session: Session):
        """Test that relationships can be queried efficiently"""
        # Create parent product with multiple children
        parent = Product(code="COMPLEX-001", name="Complex Product", is_finished_product=True)
        db_session.add(parent)
        db_session.commit()

        # Create 5 child components
        for i in range(5):
            child = Product(code=f"COMP-{i:03d}", name=f"Component {i}")
            bom = BillOfMaterials(
                parent_product=parent,
                child_product=child,
                quantity=float(i + 1)
            )
            db_session.add_all([child, bom])

        db_session.commit()

        # Query parent and access BOM items
        db_session.refresh(parent)
        assert len(parent.bom_items) == 5

        # Verify quantities
        quantities = sorted([bom.quantity for bom in parent.bom_items])
        assert quantities == [1.0, 2.0, 3.0, 4.0, 5.0]
