"""
Domain Service Tests for PCF Calculator.

TASK-BE-P7-019: Domain Layer Separation - Phase A (Tests Only)

This module tests domain services to verify:
1. Services depend on repository interfaces, not implementations
2. Business logic is properly encapsulated
3. Services use dependency injection
4. Error handling follows domain patterns
5. Services are testable with mocked repositories

Following TDD methodology - these tests are written BEFORE implementation.
"""

import pytest
from unittest.mock import MagicMock


class TestProductService:
    """Test ProductService domain service."""

    def test_product_service_exists(self):
        """ProductService should exist in domain.services module."""
        from backend.domain.services.product_service import ProductService
        assert ProductService is not None

    def test_product_service_constructor_accepts_repository(self):
        """ProductService should accept repository interface in constructor."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository

        # Create a mock repository that implements the interface
        mock_repo = MagicMock(spec=ProductRepository)

        service = ProductService(product_repo=mock_repo)

        assert service is not None

    def test_get_product_returns_product(self):
        """get_product should return Product domain entity."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository
        from backend.domain.entities.product import Product

        mock_repo = MagicMock(spec=ProductRepository)
        mock_repo.get_by_id.return_value = Product(
            id="prod-123",
            code="WIDGET-001",
            name="Steel Widget",
            unit="kg"
        )

        service = ProductService(product_repo=mock_repo)
        product = service.get_product("prod-123")

        assert isinstance(product, Product)
        assert product.id == "prod-123"
        mock_repo.get_by_id.assert_called_once_with("prod-123")

    def test_get_product_raises_not_found_error(self):
        """get_product should raise ProductNotFoundError when not found."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository
        from backend.domain.entities.errors import ProductNotFoundError

        mock_repo = MagicMock(spec=ProductRepository)
        mock_repo.get_by_id.return_value = None

        service = ProductService(product_repo=mock_repo)

        with pytest.raises(ProductNotFoundError) as exc_info:
            service.get_product("nonexistent-id")

        assert exc_info.value.product_id == "nonexistent-id"

    def test_get_product_with_bom(self):
        """get_product_with_bom should return ProductWithBOM."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository
        from backend.domain.entities.product import Product, BOMItem, ProductWithBOM

        mock_repo = MagicMock(spec=ProductRepository)
        mock_repo.get_with_bom.return_value = ProductWithBOM(
            product=Product(
                id="prod-123",
                code="WIDGET-001",
                name="Steel Widget",
                unit="kg"
            ),
            bom_items=[
                BOMItem(component_id="comp-1", quantity=2.5, unit="kg"),
                BOMItem(component_id="comp-2", quantity=1.0, unit="pieces")
            ]
        )

        service = ProductService(product_repo=mock_repo)
        result = service.get_product_with_bom("prod-123")

        assert isinstance(result, ProductWithBOM)
        assert result.product.id == "prod-123"
        assert len(result.bom_items) == 2
        mock_repo.get_with_bom.assert_called_once_with("prod-123")

    def test_get_product_with_bom_raises_not_found(self):
        """get_product_with_bom should raise error when product not found."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository
        from backend.domain.entities.errors import ProductNotFoundError

        mock_repo = MagicMock(spec=ProductRepository)
        mock_repo.get_with_bom.return_value = None

        service = ProductService(product_repo=mock_repo)

        with pytest.raises(ProductNotFoundError):
            service.get_product_with_bom("nonexistent-id")

    def test_list_products(self):
        """list_products should return list of products with pagination."""
        from backend.domain.services.product_service import ProductService
        from backend.domain.repositories.interfaces import ProductRepository
        from backend.domain.entities.product import Product, ProductPage

        mock_repo = MagicMock(spec=ProductRepository)
        mock_repo.list_all.return_value = ProductPage(items=[
            Product(id="prod-1", code="P1", name="Product 1", unit="kg"),
            Product(id="prod-2", code="P2", name="Product 2", unit="unit"),
        ], total=2)

        service = ProductService(product_repo=mock_repo)
        page = service.list_products(limit=10, offset=0)

        assert page.total == 2
        assert all(isinstance(p, Product) for p in page.items)
        mock_repo.list_all.assert_called_once_with(limit=10, offset=0, is_finished_product=None)

class TestCalculationService:
    """Test CalculationService domain service."""

    def test_calculation_service_exists(self):
        """CalculationService should exist in domain.services module."""
        from backend.domain.services.calculation_service import CalculationService
        assert CalculationService is not None

    def test_calculation_service_constructor_accepts_repositories(self):
        """CalculationService should accept repository interfaces in constructor."""
        from backend.domain.services.calculation_service import CalculationService
        from backend.domain.repositories.interfaces import (
            CalculationRepository,
            ProductRepository
        )

        mock_calc_repo = MagicMock(spec=CalculationRepository)
        mock_product_repo = MagicMock(spec=ProductRepository)

        service = CalculationService(
            calculation_repo=mock_calc_repo,
            product_repo=mock_product_repo
        )

        assert service is not None

    def test_create_calculation_validates_product_exists(self):
        """create_calculation should verify product exists before creating."""
        from backend.domain.services.calculation_service import CalculationService
        from backend.domain.repositories.interfaces import (
            CalculationRepository,
            ProductRepository
        )
        from backend.domain.entities.calculation import (
            CreateCalculationRequest,
            CalculationResult
        )
        from backend.domain.entities.product import Product

        mock_calc_repo = MagicMock(spec=CalculationRepository)
        mock_product_repo = MagicMock(spec=ProductRepository)

        # Product exists
        mock_product_repo.get_by_id.return_value = Product(
            id="prod-123",
            code="WIDGET-001",
            name="Steel Widget",
            unit="kg"
        )

        mock_calc_repo.create.return_value = CalculationResult(
            id="calc-456",
            status="pending",
            product_id="prod-123"
        )

        service = CalculationService(
            calculation_repo=mock_calc_repo,
            product_repo=mock_product_repo
        )

        request = CreateCalculationRequest(
            product_id="prod-123",
            calculation_type="cradle_to_gate"
        )

        result = service.create_calculation(request)

        assert isinstance(result, CalculationResult)
        assert result.id == "calc-456"
        assert result.status == "pending"
        assert result.product_id == "prod-123"

        # Verify product was checked
        mock_product_repo.get_by_id.assert_called_once_with("prod-123")
        # Verify calculation was created
        mock_calc_repo.create.assert_called_once()

    def test_create_calculation_raises_for_nonexistent_product(self):
        """create_calculation should raise error if product does not exist."""
        from backend.domain.services.calculation_service import CalculationService
        from backend.domain.repositories.interfaces import (
            CalculationRepository,
            ProductRepository
        )
        from backend.domain.entities.calculation import CreateCalculationRequest
        from backend.domain.entities.errors import ProductNotFoundError

        mock_calc_repo = MagicMock(spec=CalculationRepository)
        mock_product_repo = MagicMock(spec=ProductRepository)

        # Product does not exist
        mock_product_repo.get_by_id.return_value = None

        service = CalculationService(
            calculation_repo=mock_calc_repo,
            product_repo=mock_product_repo
        )

        request = CreateCalculationRequest(
            product_id="nonexistent",
            calculation_type="cradle_to_gate"
        )

        with pytest.raises(ProductNotFoundError):
            service.create_calculation(request)

        # Verify create was NOT called
        mock_calc_repo.create.assert_not_called()

    def test_get_calculation(self):
        """get_calculation should return Calculation domain entity."""
        from backend.domain.services.calculation_service import CalculationService
        from backend.domain.repositories.interfaces import (
            CalculationRepository,
            ProductRepository
        )
        from backend.domain.entities.calculation import Calculation

        mock_calc_repo = MagicMock(spec=CalculationRepository)
        mock_product_repo = MagicMock(spec=ProductRepository)

        mock_calc_repo.get_by_id.return_value = Calculation(
            id="calc-123",
            product_id="prod-123",
            total_co2e_kg=100.5,
            status="completed"
        )

        service = CalculationService(
            calculation_repo=mock_calc_repo,
            product_repo=mock_product_repo
        )

        result = service.get_calculation("calc-123")

        assert isinstance(result, Calculation)
        assert result.id == "calc-123"
        mock_calc_repo.get_by_id.assert_called_once_with("calc-123")

    def test_get_calculation_raises_not_found(self):
        """get_calculation should raise error when calculation not found."""
        from backend.domain.services.calculation_service import CalculationService
        from backend.domain.repositories.interfaces import (
            CalculationRepository,
            ProductRepository
        )
        from backend.domain.entities.errors import CalculationNotFoundError

        mock_calc_repo = MagicMock(spec=CalculationRepository)
        mock_product_repo = MagicMock(spec=ProductRepository)

        mock_calc_repo.get_by_id.return_value = None

        service = CalculationService(
            calculation_repo=mock_calc_repo,
            product_repo=mock_product_repo
        )

        with pytest.raises(CalculationNotFoundError):
            service.get_calculation("nonexistent")

class TestServiceDependencyInjection:
    """Test that services use proper dependency injection."""

    def test_product_service_only_depends_on_interfaces(self):
        """ProductService should only depend on repository interfaces."""
        from backend.domain.services.product_service import ProductService
        import inspect

        # Get constructor signature
        sig = inspect.signature(ProductService.__init__)
        params = sig.parameters

        # Should have product_repo parameter
        assert 'product_repo' in params or any(
            'repo' in name.lower() for name in params
        ), "ProductService should accept repository in constructor"

    def test_calculation_service_only_depends_on_interfaces(self):
        """CalculationService should only depend on repository interfaces."""
        from backend.domain.services.calculation_service import CalculationService
        import inspect

        sig = inspect.signature(CalculationService.__init__)
        params = sig.parameters

        # Should have repository parameters
        param_names = [name.lower() for name in params]
        assert any('repo' in name for name in param_names), \
            "CalculationService should accept repositories in constructor"


class TestServiceModulePurity:
    """Test that service modules don't have infrastructure imports."""

    def test_product_service_no_sqlalchemy_imports(self):
        """ProductService module should not import SQLAlchemy."""
        from backend.domain.services import product_service
        import inspect
        import ast

        source_file = inspect.getfile(product_service)

        with open(source_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith('sqlalchemy'), \
                        f"ProductService should not import SQLAlchemy: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith('sqlalchemy'), \
                        f"ProductService should not import from SQLAlchemy: {node.module}"

    def test_calculation_service_no_sqlalchemy_imports(self):
        """CalculationService module should not import SQLAlchemy."""
        from backend.domain.services import calculation_service
        import inspect
        import ast

        source_file = inspect.getfile(calculation_service)

        with open(source_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith('sqlalchemy'), \
                        f"CalculationService should not import SQLAlchemy: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith('sqlalchemy'), \
                        f"CalculationService should not import from SQLAlchemy: {node.module}"
