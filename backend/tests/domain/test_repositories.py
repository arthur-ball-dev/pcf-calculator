"""
Repository Interface and Implementation Tests for PCF Calculator.

TASK-BE-P7-019: Domain Layer Separation - Phase A (Tests Only)

This module tests repository interfaces and implementations to verify:
1. Repository interfaces are abstract (ABC)
2. Repository methods are async
3. SQLAlchemy implementations correctly map ORM to domain entities
4. Transaction rollback works correctly
5. Proper error handling and mapping

Following TDD methodology - these tests are written BEFORE implementation.
"""

import pytest
from abc import ABC
from typing import Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
import inspect


class TestProductRepositoryInterface:
    """Test ProductRepository abstract interface."""

    def test_product_repository_interface_exists(self):
        """ProductRepository interface should exist."""
        from backend.domain.repositories.interfaces import ProductRepository
        assert ProductRepository is not None

    def test_product_repository_is_abstract(self):
        """ProductRepository should be an abstract base class."""
        from backend.domain.repositories.interfaces import ProductRepository
        assert issubclass(ProductRepository, ABC)

    def test_product_repository_cannot_be_instantiated(self):
        """ProductRepository should not be directly instantiable."""
        from backend.domain.repositories.interfaces import ProductRepository

        with pytest.raises(TypeError):
            ProductRepository()

    def test_product_repository_has_get_by_id_method(self):
        """ProductRepository should define get_by_id abstract method."""
        from backend.domain.repositories.interfaces import ProductRepository

        assert hasattr(ProductRepository, 'get_by_id')
        method = getattr(ProductRepository, 'get_by_id')
        assert inspect.iscoroutinefunction(method) or hasattr(method, '__isabstractmethod__')

    def test_product_repository_has_list_all_method(self):
        """ProductRepository should define list_all abstract method."""
        from backend.domain.repositories.interfaces import ProductRepository

        assert hasattr(ProductRepository, 'list_all')

    def test_product_repository_has_create_method(self):
        """ProductRepository should define create abstract method."""
        from backend.domain.repositories.interfaces import ProductRepository

        assert hasattr(ProductRepository, 'create')

    def test_product_repository_has_get_with_bom_method(self):
        """ProductRepository should define get_with_bom abstract method."""
        from backend.domain.repositories.interfaces import ProductRepository

        assert hasattr(ProductRepository, 'get_with_bom')


class TestCalculationRepositoryInterface:
    """Test CalculationRepository abstract interface."""

    def test_calculation_repository_interface_exists(self):
        """CalculationRepository interface should exist."""
        from backend.domain.repositories.interfaces import CalculationRepository
        assert CalculationRepository is not None

    def test_calculation_repository_is_abstract(self):
        """CalculationRepository should be an abstract base class."""
        from backend.domain.repositories.interfaces import CalculationRepository
        assert issubclass(CalculationRepository, ABC)

    def test_calculation_repository_has_get_by_id_method(self):
        """CalculationRepository should define get_by_id abstract method."""
        from backend.domain.repositories.interfaces import CalculationRepository

        assert hasattr(CalculationRepository, 'get_by_id')

    def test_calculation_repository_has_create_method(self):
        """CalculationRepository should define create abstract method."""
        from backend.domain.repositories.interfaces import CalculationRepository

        assert hasattr(CalculationRepository, 'create')

    def test_calculation_repository_has_list_for_product_method(self):
        """CalculationRepository should define list_for_product abstract method."""
        from backend.domain.repositories.interfaces import CalculationRepository

        assert hasattr(CalculationRepository, 'list_for_product')


class TestBOMRepositoryInterface:
    """Test BOMRepository abstract interface."""

    def test_bom_repository_interface_exists(self):
        """BOMRepository interface should exist."""
        from backend.domain.repositories.interfaces import BOMRepository
        assert BOMRepository is not None

    def test_bom_repository_has_get_for_product_method(self):
        """BOMRepository should define get_for_product abstract method."""
        from backend.domain.repositories.interfaces import BOMRepository

        assert hasattr(BOMRepository, 'get_for_product')


@pytest.mark.asyncio
class TestSQLAlchemyProductRepository:
    """Test SQLAlchemy implementation of ProductRepository."""

    async def test_sqlalchemy_product_repository_exists(self):
        """SQLAlchemyProductRepository should exist."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        assert SQLAlchemyProductRepository is not None

    async def test_sqlalchemy_product_repository_implements_interface(self):
        """SQLAlchemyProductRepository should implement ProductRepository."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.repositories.interfaces import ProductRepository

        assert issubclass(SQLAlchemyProductRepository, ProductRepository)

    async def test_get_by_id_returns_domain_entity(self):
        """get_by_id should return a Product domain entity, not ORM model."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.entities.product import Product

        # Create a mock async session
        mock_session = AsyncMock()

        # Mock the execute result to return a fake ORM product
        mock_orm_product = MagicMock()
        mock_orm_product.id = "prod-123"
        mock_orm_product.code = "WIDGET-001"
        mock_orm_product.name = "Steel Widget"
        mock_orm_product.unit = "kg"
        mock_orm_product.category = "components"
        mock_orm_product.description = "A steel widget"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm_product
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProductRepository(mock_session)
        product = await repo.get_by_id("prod-123")

        # Should return domain entity, not ORM model
        assert isinstance(product, Product)
        assert product.id == "prod-123"
        assert product.code == "WIDGET-001"
        assert product.name == "Steel Widget"

    async def test_get_by_id_returns_none_when_not_found(self):
        """get_by_id should return None when product not found."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProductRepository(mock_session)
        product = await repo.get_by_id("nonexistent-id")

        assert product is None

    async def test_list_all_returns_domain_entities(self):
        """list_all should return list of Product domain entities."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.entities.product import Product

        mock_session = AsyncMock()

        # Mock ORM products
        mock_orm_product1 = MagicMock()
        mock_orm_product1.id = "prod-1"
        mock_orm_product1.code = "P1"
        mock_orm_product1.name = "Product 1"
        mock_orm_product1.unit = "kg"
        mock_orm_product1.category = None
        mock_orm_product1.description = None

        mock_orm_product2 = MagicMock()
        mock_orm_product2.id = "prod-2"
        mock_orm_product2.code = "P2"
        mock_orm_product2.name = "Product 2"
        mock_orm_product2.unit = "unit"
        mock_orm_product2.category = None
        mock_orm_product2.description = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_orm_product1, mock_orm_product2
        ]
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProductRepository(mock_session)
        products = await repo.list_all(limit=10, offset=0)

        assert len(products) == 2
        assert all(isinstance(p, Product) for p in products)
        assert products[0].id == "prod-1"
        assert products[1].id == "prod-2"

    async def test_create_returns_domain_entity(self):
        """create should return the created Product domain entity."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.entities.product import Product

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        product = Product(
            id="prod-new",
            code="NEW-001",
            name="New Product",
            unit="kg"
        )

        repo = SQLAlchemyProductRepository(mock_session)
        created = await repo.create(product)

        assert isinstance(created, Product)
        assert mock_session.add.called
        assert mock_session.commit.called


@pytest.mark.asyncio
class TestSQLAlchemyProductRepositoryTransactions:
    """Test transaction handling in SQLAlchemy repository."""

    async def test_create_duplicate_raises_domain_error(self):
        """Creating duplicate product should raise DuplicateProductError."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.entities.product import Product
        from backend.domain.entities.errors import DuplicateProductError
        from sqlalchemy.exc import IntegrityError

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock(
            side_effect=IntegrityError(
                statement="INSERT",
                params={},
                orig=Exception("UNIQUE constraint failed: products.code")
            )
        )
        mock_session.rollback = AsyncMock()

        product = Product(
            id="prod-dup",
            code="DUPLICATE",
            name="Duplicate Product",
            unit="kg"
        )

        repo = SQLAlchemyProductRepository(mock_session)

        with pytest.raises(DuplicateProductError):
            await repo.create(product)

        # Verify rollback was called
        assert mock_session.rollback.called

    async def test_get_with_bom_returns_product_with_bom(self):
        """get_with_bom should return ProductWithBOM containing BOM items."""
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository
        )
        from backend.domain.entities.product import ProductWithBOM, BOMItem

        mock_session = AsyncMock()

        # Mock ORM product with BOM items
        mock_bom_item1 = MagicMock()
        mock_bom_item1.child_product_id = "comp-1"
        mock_bom_item1.quantity = 2.5
        mock_bom_item1.unit = "kg"

        mock_bom_item2 = MagicMock()
        mock_bom_item2.child_product_id = "comp-2"
        mock_bom_item2.quantity = 1.0
        mock_bom_item2.unit = "pieces"

        mock_orm_product = MagicMock()
        mock_orm_product.id = "prod-123"
        mock_orm_product.code = "WIDGET-001"
        mock_orm_product.name = "Steel Widget"
        mock_orm_product.unit = "kg"
        mock_orm_product.category = None
        mock_orm_product.description = None
        mock_orm_product.bom_items = [mock_bom_item1, mock_bom_item2]

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_orm_product
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProductRepository(mock_session)
        result = await repo.get_with_bom("prod-123")

        assert isinstance(result, ProductWithBOM)
        assert result.product.id == "prod-123"
        assert len(result.bom_items) == 2
        assert all(isinstance(item, BOMItem) for item in result.bom_items)


@pytest.mark.asyncio
class TestSQLAlchemyCalculationRepository:
    """Test SQLAlchemy implementation of CalculationRepository."""

    async def test_sqlalchemy_calculation_repository_exists(self):
        """SQLAlchemyCalculationRepository should exist."""
        from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
            SQLAlchemyCalculationRepository
        )
        assert SQLAlchemyCalculationRepository is not None

    async def test_sqlalchemy_calculation_repository_implements_interface(self):
        """SQLAlchemyCalculationRepository should implement CalculationRepository."""
        from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
            SQLAlchemyCalculationRepository
        )
        from backend.domain.repositories.interfaces import CalculationRepository

        assert issubclass(SQLAlchemyCalculationRepository, CalculationRepository)

    async def test_get_by_id_returns_domain_entity(self):
        """get_by_id should return a Calculation domain entity."""
        from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
            SQLAlchemyCalculationRepository
        )
        from backend.domain.entities.calculation import Calculation

        mock_session = AsyncMock()

        mock_orm_calc = MagicMock()
        mock_orm_calc.id = "calc-123"
        mock_orm_calc.product_id = "prod-123"
        mock_orm_calc.total_co2e_kg = 100.5
        mock_orm_calc.status = "completed"
        mock_orm_calc.calculation_type = "cradle_to_gate"
        mock_orm_calc.materials_co2e = 70.0
        mock_orm_calc.energy_co2e = 20.5
        mock_orm_calc.transport_co2e = 10.0
        mock_orm_calc.waste_co2e = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm_calc
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyCalculationRepository(mock_session)
        calculation = await repo.get_by_id("calc-123")

        assert isinstance(calculation, Calculation)
        assert calculation.id == "calc-123"
        assert calculation.product_id == "prod-123"
        assert calculation.total_co2e_kg == 100.5

    async def test_create_returns_calculation_result(self):
        """create should return CalculationResult for pending calculation."""
        from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
            SQLAlchemyCalculationRepository
        )
        from backend.domain.entities.calculation import (
            CreateCalculationRequest,
            CalculationResult
        )

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        request = CreateCalculationRequest(
            product_id="prod-123",
            calculation_method="attributional",
            include_transport=True
        )

        repo = SQLAlchemyCalculationRepository(mock_session)
        result = await repo.create(request)

        assert isinstance(result, CalculationResult)
        assert result.product_id == "prod-123"
        assert result.status == "pending"


class TestRepositoryInterfaceModulePurity:
    """Test that repository interfaces module has no infrastructure imports."""

    def test_interfaces_module_no_sqlalchemy_imports(self):
        """Repository interfaces should not import SQLAlchemy."""
        from backend.domain.repositories import interfaces

        source_file = inspect.getfile(interfaces)

        with open(source_file, 'r') as f:
            source_code = f.read()

        import ast
        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith('sqlalchemy'), \
                        f"Repository interfaces should not import SQLAlchemy: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith('sqlalchemy'), \
                        f"Repository interfaces should not import from SQLAlchemy: {node.module}"
