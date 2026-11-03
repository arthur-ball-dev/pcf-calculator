"""
SQLAlchemy Product Repository Implementation

TASK-BE-P7-019: Domain Layer Separation

Implements ProductRepository interface using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

from typing import Optional

from sqlalchemy import exists, func, not_, or_, select
from sqlalchemy.orm import Query, Session, joinedload

from backend.domain.entities.product import (
    BOMItem,
    CategorySummary,
    Product,
    ProductPage,
    ProductSearchCriteria,
    ProductWithBOM,
)
from backend.domain.repositories.interfaces import ProductRepository
from backend.models import BillOfMaterials as BOMModel
from backend.models import Product as ProductModel
from backend.models import ProductCategory as CategoryModel


def build_search_query(session: Session, criteria: ProductSearchCriteria) -> Query:
    """Build the product search query, ordered by name, from the criteria."""
    base_query = session.query(ProductModel).options(joinedload(ProductModel.product_category))

    if criteria.query:
        query_lower = f"%{criteria.query.lower()}%"
        base_query = base_query.filter(
            or_(
                func.lower(ProductModel.name).like(query_lower),
                func.lower(ProductModel.description).like(query_lower),
                func.lower(ProductModel.code).like(query_lower),
                func.lower(ProductModel.search_vector).like(query_lower),
            )
        )

    if criteria.category_id is not None:
        base_query = base_query.filter(ProductModel.category_id == criteria.category_id)

    if criteria.industry is not None:
        base_query = base_query.filter(
            or_(
                exists(
                    select(CategoryModel.id).where(
                        CategoryModel.id == ProductModel.category_id,
                        CategoryModel.industry_sector == criteria.industry,
                    )
                ),
                func.lower(ProductModel.category) == criteria.industry.lower(),
            )
        )

    if criteria.manufacturer is not None:
        manufacturer_pattern = f"%{criteria.manufacturer}%"
        base_query = base_query.filter(
            func.lower(ProductModel.manufacturer).like(func.lower(manufacturer_pattern))
        )

    if criteria.country_of_origin is not None:
        base_query = base_query.filter(ProductModel.country_of_origin == criteria.country_of_origin)

    if criteria.is_finished_product is not None:
        base_query = base_query.filter(
            ProductModel.is_finished_product == criteria.is_finished_product
        )

    has_bom_subquery = exists(
        select(BOMModel.id).where(BOMModel.parent_product_id == ProductModel.id)
    )
    if criteria.has_bom is True:
        base_query = base_query.filter(has_bom_subquery)
    elif criteria.has_bom is False:
        base_query = base_query.filter(not_(has_bom_subquery))

    return base_query.order_by(ProductModel.name)


class SQLAlchemyProductRepository(ProductRepository):
    """
    SQLAlchemy implementation of ProductRepository.

    Maps ORM models to domain entities and handles database operations.
    """

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session.
        """
        self._session = session

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity if found, None otherwise.
        """
        orm_product = self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        ).scalar_one_or_none()

        return None if orm_product is None else self._to_domain(orm_product)

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
        query = self._session.query(ProductModel)
        if is_finished_product is not None:
            query = query.filter(ProductModel.is_finished_product == is_finished_product)

        total = query.count()
        products = query.order_by(ProductModel.name).offset(offset).limit(limit).all()

        return ProductPage(items=[self._to_domain(p) for p in products], total=total)

    def search(self, criteria: ProductSearchCriteria) -> ProductPage:
        """
        Search products.

        Args:
            criteria: Filters and pagination.

        Returns:
            One page of products, with their categories, and the total matching count.
        """
        query = build_search_query(self._session, criteria)
        total = query.count()
        products = query.offset(criteria.offset).limit(criteria.limit).all()

        return ProductPage(
            items=[self._to_domain(p, with_category=True) for p in products],
            total=total,
        )

    def get_with_bom(self, product_id: str) -> Optional[ProductWithBOM]:
        """
        Get product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items, or None if not found.
        """
        orm_product = (
            self._session.query(ProductModel)
            .options(joinedload(ProductModel.bom_items).joinedload(BOMModel.child_product))
            .filter(ProductModel.id == product_id)
            .first()
        )

        if orm_product is None:
            return None

        return ProductWithBOM(
            product=self._to_domain(orm_product),
            bom_items=[self._bom_to_domain(bom) for bom in orm_product.bom_items],
        )

    def _to_domain(self, orm_product: ProductModel, with_category: bool = False) -> Product:
        """
        Convert ORM model to domain entity.

        Args:
            orm_product: SQLAlchemy ORM Product model.
            with_category: Map the linked category. Only for queries that load it,
                because reading it otherwise costs one query per product.

        Returns:
            Product domain entity.
        """
        category_info = None
        if with_category and orm_product.product_category:
            linked = orm_product.product_category
            category_info = CategorySummary(
                id=linked.id,
                code=linked.code,
                name=linked.name,
                industry_sector=linked.industry_sector,
            )

        return Product(
            id=orm_product.id,
            code=orm_product.code,
            name=orm_product.name,
            unit=orm_product.unit,
            category=orm_product.category,
            description=orm_product.description,
            is_finished_product=orm_product.is_finished_product,
            created_at=orm_product.created_at,
            manufacturer=orm_product.manufacturer,
            country_of_origin=orm_product.country_of_origin,
            category_info=category_info,
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
            unit=orm_bom.unit,
            id=orm_bom.id,
            component_name=orm_bom.child_product.name if orm_bom.child_product else "Unknown",
            notes=orm_bom.notes,
            emission_factor_id=orm_bom.emission_factor_id,
        )
