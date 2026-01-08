"""
Domain Entity Tests for PCF Calculator.

TASK-BE-P7-019: Domain Layer Separation - Phase A (Tests Only)

This module tests domain entities to verify:
1. Entities are pure Python (no SQLAlchemy imports)
2. Entities are immutable (frozen dataclasses)
3. Entities validate on construction
4. Domain errors are distinct from infrastructure errors

Following TDD methodology - these tests are written BEFORE implementation.
"""

import pytest
import inspect
import ast
from dataclasses import FrozenInstanceError
from typing import Optional


class TestProductEntityPurity:
    """Test that Product domain entity is pure Python (no ORM dependencies)."""

    def test_product_entity_exists(self):
        """Product domain entity should exist in domain.entities module."""
        from backend.domain.entities.product import Product
        assert Product is not None

    def test_product_entity_no_sqlalchemy_imports(self):
        """Product entity module should not import SQLAlchemy."""
        from backend.domain.entities import product as product_module

        # Get the module source file
        source_file = inspect.getfile(product_module)

        with open(source_file, 'r') as f:
            source_code = f.read()

        # Parse the AST and check for SQLAlchemy imports
        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith('sqlalchemy'), \
                        f"Product entity should not import SQLAlchemy: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith('sqlalchemy'), \
                        f"Product entity should not import from SQLAlchemy: {node.module}"

    def test_product_entity_is_frozen_dataclass(self):
        """Product entity should be immutable (frozen dataclass)."""
        from backend.domain.entities.product import Product

        product = Product(
            id="prod-123",
            code="WIDGET-001",
            name="Steel Widget",
            unit="kg"
        )

        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            product.name = "Modified Name"


class TestProductEntityValidation:
    """Test Product domain entity validation rules."""

    def test_product_creation_with_valid_data(self):
        """Product should be created successfully with valid data."""
        from backend.domain.entities.product import Product

        product = Product(
            id="prod-123",
            code="WIDGET-001",
            name="Steel Widget",
            unit="kg",
            category="components",
            description="A steel widget for assembly"
        )

        assert product.id == "prod-123"
        assert product.code == "WIDGET-001"
        assert product.name == "Steel Widget"
        assert product.unit == "kg"
        assert product.category == "components"
        assert product.description == "A steel widget for assembly"

    def test_product_creation_minimal_fields(self):
        """Product should be created with only required fields."""
        from backend.domain.entities.product import Product

        product = Product(
            id="prod-456",
            code="P1",
            name="Test Product",
            unit="unit"
        )

        assert product.id == "prod-456"
        assert product.code == "P1"
        assert product.name == "Test Product"
        assert product.unit == "unit"
        assert product.category is None
        assert product.description is None

    def test_product_validation_empty_id_raises_error(self):
        """Product with empty ID should raise DomainValidationError."""
        from backend.domain.entities.product import Product
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            Product(
                id="",
                code="P1",
                name="Test",
                unit="kg"
            )

        assert "Product ID cannot be empty" in str(exc_info.value)

    def test_product_validation_empty_code_raises_error(self):
        """Product with empty code should raise DomainValidationError."""
        from backend.domain.entities.product import Product
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            Product(
                id="prod-123",
                code="",
                name="Test",
                unit="kg"
            )

        assert "Product code cannot be empty" in str(exc_info.value)

    def test_product_validation_empty_name_raises_error(self):
        """Product with empty name should raise DomainValidationError."""
        from backend.domain.entities.product import Product
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            Product(
                id="prod-123",
                code="P1",
                name="",
                unit="kg"
            )

        assert "Product name cannot be empty" in str(exc_info.value)


class TestCalculationEntityPurity:
    """Test that Calculation domain entity is pure Python."""

    def test_calculation_entity_exists(self):
        """Calculation domain entity should exist in domain.entities module."""
        from backend.domain.entities.calculation import Calculation
        assert Calculation is not None

    def test_calculation_entity_no_sqlalchemy_imports(self):
        """Calculation entity module should not import SQLAlchemy."""
        from backend.domain.entities import calculation as calculation_module

        source_file = inspect.getfile(calculation_module)

        with open(source_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith('sqlalchemy'), \
                        f"Calculation entity should not import SQLAlchemy: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith('sqlalchemy'), \
                        f"Calculation entity should not import from SQLAlchemy: {node.module}"

    def test_calculation_entity_is_frozen_dataclass(self):
        """Calculation entity should be immutable (frozen dataclass)."""
        from backend.domain.entities.calculation import Calculation

        calculation = Calculation(
            id="calc-123",
            product_id="prod-123",
            total_co2e_kg=100.5,
            status="completed"
        )

        with pytest.raises(FrozenInstanceError):
            calculation.status = "failed"


class TestCalculationEntityValidation:
    """Test Calculation domain entity validation rules."""

    def test_calculation_creation_with_valid_data(self):
        """Calculation should be created successfully with valid data."""
        from backend.domain.entities.calculation import Calculation

        calculation = Calculation(
            id="calc-123",
            product_id="prod-123",
            total_co2e_kg=100.5,
            status="completed",
            calculation_type="cradle_to_gate",
            materials_co2e=70.0,
            energy_co2e=20.5,
            transport_co2e=10.0
        )

        assert calculation.id == "calc-123"
        assert calculation.product_id == "prod-123"
        assert calculation.total_co2e_kg == 100.5
        assert calculation.status == "completed"
        assert calculation.calculation_type == "cradle_to_gate"

    def test_calculation_result_creation(self):
        """CalculationResult should be created for pending calculations."""
        from backend.domain.entities.calculation import CalculationResult

        result = CalculationResult(
            id="calc-456",
            status="pending",
            product_id="prod-123"
        )

        assert result.id == "calc-456"
        assert result.status == "pending"
        assert result.product_id == "prod-123"

    def test_calculation_validation_empty_id_raises_error(self):
        """Calculation with empty ID should raise DomainValidationError."""
        from backend.domain.entities.calculation import Calculation
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            Calculation(
                id="",
                product_id="prod-123",
                total_co2e_kg=100.0,
                status="completed"
            )

        assert "Calculation ID cannot be empty" in str(exc_info.value)

    def test_calculation_validation_negative_co2e_raises_error(self):
        """Calculation with negative CO2e should raise DomainValidationError."""
        from backend.domain.entities.calculation import Calculation
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            Calculation(
                id="calc-123",
                product_id="prod-123",
                total_co2e_kg=-10.0,
                status="completed"
            )

        assert "CO2e value cannot be negative" in str(exc_info.value)


class TestBOMItemEntity:
    """Test BOMItem domain entity."""

    def test_bom_item_creation(self):
        """BOMItem should be created successfully."""
        from backend.domain.entities.product import BOMItem

        bom_item = BOMItem(
            component_id="comp-1",
            quantity=2.5,
            unit="kg"
        )

        assert bom_item.component_id == "comp-1"
        assert bom_item.quantity == 2.5
        assert bom_item.unit == "kg"

    def test_bom_item_is_frozen(self):
        """BOMItem should be immutable."""
        from backend.domain.entities.product import BOMItem

        bom_item = BOMItem(
            component_id="comp-1",
            quantity=2.5,
            unit="kg"
        )

        with pytest.raises(FrozenInstanceError):
            bom_item.quantity = 5.0

    def test_bom_item_validation_positive_quantity(self):
        """BOMItem with zero or negative quantity should raise error."""
        from backend.domain.entities.product import BOMItem
        from backend.domain.entities.errors import DomainValidationError

        with pytest.raises(DomainValidationError) as exc_info:
            BOMItem(
                component_id="comp-1",
                quantity=0,
                unit="kg"
            )

        assert "quantity" in str(exc_info.value).lower()


class TestProductWithBOMEntity:
    """Test ProductWithBOM composite entity."""

    def test_product_with_bom_creation(self):
        """ProductWithBOM should contain product and BOM items."""
        from backend.domain.entities.product import Product, BOMItem, ProductWithBOM

        product = Product(
            id="prod-123",
            code="WIDGET-001",
            name="Steel Widget",
            unit="kg"
        )

        bom_items = [
            BOMItem(component_id="comp-1", quantity=2.5, unit="kg"),
            BOMItem(component_id="comp-2", quantity=1.0, unit="pieces")
        ]

        product_with_bom = ProductWithBOM(
            product=product,
            bom_items=bom_items
        )

        assert product_with_bom.product.id == "prod-123"
        assert len(product_with_bom.bom_items) == 2
        assert product_with_bom.bom_items[0].component_id == "comp-1"
        assert product_with_bom.bom_items[1].component_id == "comp-2"


class TestDomainErrors:
    """Test domain-specific error classes."""

    def test_domain_validation_error_exists(self):
        """DomainValidationError should be defined."""
        from backend.domain.entities.errors import DomainValidationError
        assert DomainValidationError is not None

    def test_domain_validation_error_is_exception(self):
        """DomainValidationError should be a proper exception."""
        from backend.domain.entities.errors import DomainValidationError

        error = DomainValidationError("Test error message")
        assert isinstance(error, Exception)
        assert str(error) == "Test error message"

    def test_product_not_found_error_exists(self):
        """ProductNotFoundError should be defined."""
        from backend.domain.entities.errors import ProductNotFoundError
        assert ProductNotFoundError is not None

    def test_product_not_found_error_contains_id(self):
        """ProductNotFoundError should contain the product ID."""
        from backend.domain.entities.errors import ProductNotFoundError

        error = ProductNotFoundError(product_id="prod-999")
        assert "prod-999" in str(error)
        assert hasattr(error, 'product_id')
        assert error.product_id == "prod-999"

    def test_duplicate_product_error_exists(self):
        """DuplicateProductError should be defined."""
        from backend.domain.entities.errors import DuplicateProductError
        assert DuplicateProductError is not None

    def test_duplicate_product_error_contains_code(self):
        """DuplicateProductError should contain the product code."""
        from backend.domain.entities.errors import DuplicateProductError

        error = DuplicateProductError(code="DUPLICATE-001")
        assert "DUPLICATE-001" in str(error)


class TestCreateCalculationRequest:
    """Test CreateCalculationRequest domain object."""

    def test_create_calculation_request_exists(self):
        """CreateCalculationRequest should be defined."""
        from backend.domain.entities.calculation import CreateCalculationRequest
        assert CreateCalculationRequest is not None

    def test_create_calculation_request_creation(self):
        """CreateCalculationRequest should be created with valid data."""
        from backend.domain.entities.calculation import CreateCalculationRequest

        request = CreateCalculationRequest(
            product_id="prod-123",
            calculation_method="attributional",
            include_transport=True
        )

        assert request.product_id == "prod-123"
        assert request.calculation_method == "attributional"
        assert request.include_transport is True
