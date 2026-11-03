"""
Repository Interface and Implementation Tests for PCF Calculator.

TASK-BE-P7-019: Domain Layer Separation - Phase A (Tests Only)

This module tests repository interfaces and implementations to verify:
1. Repository interfaces are abstract (ABC)
2. Interfaces stay free of infrastructure imports

Implementations are tested on a real session in test_domain_layer_wiring.py.

Following TDD methodology - these tests are written BEFORE implementation.
"""

import pytest
from abc import ABC
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
        assert hasattr(method, '__isabstractmethod__')

    def test_product_repository_has_list_all_method(self):
        """ProductRepository should define list_all abstract method."""
        from backend.domain.repositories.interfaces import ProductRepository

        assert hasattr(ProductRepository, 'list_all')

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
