"""
SQLAlchemy Product Repository Implementation

TASK-BE-P7-019: Domain Layer Separation

Implements ProductRepository interface using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from backend.domain.entities.product import Product, BOMItem, ProductWithBOM
from backend.domain.entities.errors import DuplicateProductError
from backend.domain.repositories.interfaces import ProductRepository
from backend.models import Product as ProductModel
from backend.models import BillOfMaterials as BOMModel


class SQLAlchemyProductRepository(ProductRepository):
    """
    SQLAlchemy implementation of ProductRepository.

    Maps ORM models to domain entities and handles database operations.
    """

    def __init__(self, session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy AsyncSession or Session.
        """
        self._session = session

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity if found, None otherwise.
        """
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        orm_product = result.scalar_one_or_none()

        if orm_product is None:
            return None

        return self._to_domain(orm_product)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Product]:
        """
        List all products with pagination.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of Product domain entities.
        """
        result = await self._session.execute(
            select(ProductModel).limit(limit).offset(offset)
        )
        orm_products = result.scalars().all()

        return [self._to_domain(p) for p in orm_products]

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
        orm_product = ProductModel(
            id=product.id,
            code=product.code,
            name=product.name,
            unit=product.unit,
            category=product.category,
            description=product.description,
        )

        self._session.add(orm_product)

        try:
            await self._session.commit()
            await self._session.refresh(orm_product)
            return self._to_domain(orm_product)
        except IntegrityError:
            await self._session.rollback()
            raise DuplicateProductError(code=product.code)

    async def get_with_bom(self, product_id: str) -> Optional[ProductWithBOM]:
        """
        Get product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items, or None if not found.
        """
        result = await self._session.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.bom_items))
            .where(ProductModel.id == product_id)
        )
        orm_product = result.unique().scalar_one_or_none()

        if orm_product is None:
            return None

        product = self._to_domain(orm_product)
        bom_items = [
            self._bom_to_domain(bom) for bom in orm_product.bom_items
        ]

        return ProductWithBOM(product=product, bom_items=bom_items)

    def _to_domain(self, orm_product: ProductModel) -> Product:
        """
        Convert ORM model to domain entity.

        Args:
            orm_product: SQLAlchemy ORM Product model.

        Returns:
            Product domain entity.
        """
        return Product(
            id=orm_product.id,
            code=orm_product.code,
            name=orm_product.name,
            unit=orm_product.unit,
            category=orm_product.category,
            description=orm_product.description,
        )

    def _bom_to_domain(self, orm_bom: BOMModel) -> BOMItem:
        """
        Convert ORM BOM model to domain entity.

        Args:
            orm_bom: SQLAlchemy ORM BillOfMaterials model.

        Returns:
            BOMItem domain entity.
        """
        return BOMItem(
            component_id=orm_bom.child_product_id,
            quantity=float(orm_bom.quantity),
            unit=orm_bom.unit or "unit",
        )
