"""
Repository Interfaces - Abstract Base Classes

TASK-BE-P7-019: Domain Layer Separation

Defines abstract repository interfaces for data access.
Implementations are in the infrastructure layer.

No SQLAlchemy or other infrastructure imports allowed here.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from backend.domain.entities.product import Product, ProductWithBOM, BOMItem
from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)


class ProductRepository(ABC):
    """
    Abstract interface for product data access.

    Implementations must handle ORM-to-domain entity mapping.
    """

    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Product]:
        """
        List all products with pagination.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of Product domain entities.
        """
        pass

    @abstractmethod
    async def create(self, product: Product) -> Product:
        """
        Create a new product.

        Args:
            product: Product domain entity to create.

        Returns:
            Created Product domain entity.

        Raises:
            DuplicateProductError: If a product with the same code exists.
        """
        pass

    @abstractmethod
    async def get_with_bom(self, product_id: str) -> Optional[ProductWithBOM]:
        """
        Get product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items, or None if not found.
        """
        pass


class CalculationRepository(ABC):
    """
    Abstract interface for calculation data access.

    Implementations must handle ORM-to-domain entity mapping.
    """

    @abstractmethod
    async def get_by_id(self, calculation_id: str) -> Optional[Calculation]:
        """
        Get calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def create(self, request: CreateCalculationRequest) -> CalculationResult:
        """
        Create a new calculation request.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.
        """
        pass

    @abstractmethod
    async def list_for_product(self, product_id: str) -> List[Calculation]:
        """
        List all calculations for a specific product.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            List of Calculation domain entities.
        """
        pass


class BOMRepository(ABC):
    """
    Abstract interface for Bill of Materials data access.
    """

    @abstractmethod
    async def get_for_product(self, product_id: str) -> List[BOMItem]:
        """
        Get BOM items for a product.

        Args:
            product_id: The unique identifier of the parent product.

        Returns:
            List of BOMItem domain entities.
        """
        pass
