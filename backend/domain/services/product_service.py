"""
Product Service - Domain Business Logic

TASK-BE-P7-019: Domain Layer Separation

Contains business logic for product-related operations.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

import uuid
from typing import List, Optional

from backend.domain.entities.product import Product, ProductWithBOM
from backend.domain.entities.errors import ProductNotFoundError
from backend.domain.repositories.interfaces import ProductRepository


class ProductService:
    """
    Domain service for product operations.

    Encapsulates business logic and coordinates with repository.
    Uses dependency injection for the repository.
    """

    def __init__(self, product_repo: ProductRepository):
        """
        Initialize the service with a repository.

        Args:
            product_repo: Repository implementing ProductRepository interface.
        """
        self._product_repo = product_repo

    async def get_product(self, product_id: str) -> Product:
        """
        Get a product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        product = await self._product_repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id=product_id)
        return product

    async def get_product_with_bom(self, product_id: str) -> ProductWithBOM:
        """
        Get a product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        result = await self._product_repo.get_with_bom(product_id)
        if result is None:
            raise ProductNotFoundError(product_id=product_id)
        return result

    async def list_products(
        self, limit: int = 100, offset: int = 0
    ) -> List[Product]:
        """
        List products with pagination.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of Product domain entities.
        """
        return await self._product_repo.list_all(limit=limit, offset=offset)

    async def create_product(
        self,
        code: str,
        name: str,
        unit: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Product:
        """
        Create a new product.

        Generates a UUID for the product and delegates to repository.

        Args:
            code: Unique product code.
            name: Display name of the product.
            unit: Unit of measure.
            category: Optional product category.
            description: Optional description.

        Returns:
            Created Product domain entity.

        Raises:
            DuplicateProductError: If a product with the same code exists.
        """
        # Generate UUID for new product
        product_id = uuid.uuid4().hex

        product = Product(
            id=product_id,
            code=code,
            name=name,
            unit=unit,
            category=category,
            description=description,
        )

        return await self._product_repo.create(product)
