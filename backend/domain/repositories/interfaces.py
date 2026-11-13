"""
Repository Interfaces - Abstract Base Classes

TASK-BE-P7-019: Domain Layer Separation

Defines abstract repository interfaces for data access.
Implementations are in the infrastructure layer.

No SQLAlchemy or other infrastructure imports allowed here.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, Iterable, Optional, List

from backend.domain.entities.category import Category
from backend.domain.entities.emission_factor import (
    DataSourceLicense,
    EmissionFactor,
    EmissionFactorFilters,
    EmissionFactorPage,
    NewEmissionFactor,
)
from backend.domain.entities.product import (
    Product,
    ProductPage,
    ProductSearchCriteria,
    ProductWithBOM,
)
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
    def get_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        is_finished_product: Optional[bool] = None,
    ) -> ProductPage:
        """
        List products by name, with pagination.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.
            is_finished_product: Only finished products, or only components.

        Returns:
            One page of products and the total matching count.
        """
        pass

    @abstractmethod
    def search(self, criteria: ProductSearchCriteria) -> ProductPage:
        """
        Search products.

        Args:
            criteria: Filters and pagination.

        Returns:
            One page of products, with their categories, and the total matching count.
        """
        pass

    @abstractmethod
    def get_with_bom(self, product_id: str) -> Optional[ProductWithBOM]:
        """
        Get product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items, or None if not found.
        """
        pass


class CategoryRepository(ABC):
    """
    Abstract interface for product category data access.

    Implementations must handle ORM-to-domain entity mapping.
    """

    @abstractmethod
    def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get a category by ID, or None if not found."""
        pass

    @abstractmethod
    def list_all(self, industry: Optional[str] = None) -> List[Category]:
        """List categories, optionally only those in one industry sector."""
        pass

    @abstractmethod
    def count_products(self, category_id: str) -> int:
        """Count the products directly in a category."""
        pass


class EmissionFactorRepository(ABC):
    """
    Abstract interface for emission factor data access.

    Implementations must handle ORM-to-domain entity mapping.
    """

    @abstractmethod
    def list_all(
        self, filters: EmissionFactorFilters, limit: int = 100, offset: int = 0
    ) -> EmissionFactorPage:
        """List emission factors, with the total matching count."""
        pass

    @abstractmethod
    def exists(
        self,
        activity_name: str,
        data_source: str,
        geography: str,
        reference_year: Optional[int],
    ) -> bool:
        """Check whether an emission factor with this composite key exists."""
        pass

    @abstractmethod
    def get_by_ids(self, factor_ids: Iterable[str]) -> Dict[str, EmissionFactor]:
        """The emission factors with these ids, keyed by id; unknown ids are absent."""
        pass

    @abstractmethod
    def create(self, factor: NewEmissionFactor) -> EmissionFactor:
        """Create an emission factor."""
        pass

    @abstractmethod
    def update(self, factor_id: str, changes: Dict[str, Any]) -> Optional[EmissionFactor]:
        """Update the given fields, skipping None values. Returns None if not found."""
        pass

    @abstractmethod
    def delete(self, factor_id: str) -> bool:
        """Delete an emission factor. Returns False if not found."""
        pass

    @abstractmethod
    def list_active_licenses(self) -> List[DataSourceLicense]:
        """List licence and attribution details of the active data sources."""
        pass


class CalculationRepository(ABC):
    """
    Abstract interface for calculation data access.

    Implementations must handle ORM-to-domain entity mapping.
    """

    @abstractmethod
    def get_by_id(self, calculation_id: str) -> Optional[Calculation]:
        """
        Get calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def create(self, request: CreateCalculationRequest) -> CalculationResult:
        """
        Create a new calculation request.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.
        """
        pass

    @abstractmethod
    def delete_older_than(self, age: timedelta) -> int:
        """Delete calculations created more than `age` ago (by the database clock); returns the count."""
        pass
