"""
SQLAlchemy Category Repository Implementation

Implements CategoryRepository using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.domain.entities.category import Category
from backend.domain.repositories.interfaces import CategoryRepository
from backend.models import Product as ProductModel
from backend.models import ProductCategory as CategoryModel


class SQLAlchemyCategoryRepository(CategoryRepository):
    """SQLAlchemy implementation of CategoryRepository."""

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session.
        """
        self._session = session

    def get_by_id(self, category_id: str) -> Optional[Category]:
        orm_category = (
            self._session.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        )
        return None if orm_category is None else self._to_domain(orm_category)

    def list_all(self, industry: Optional[str] = None) -> List[Category]:
        query = self._session.query(CategoryModel)
        if industry is not None:
            query = query.filter(CategoryModel.industry_sector == industry)
        return [self._to_domain(c) for c in query.all()]

    def count_products(self, category_id: str) -> int:
        return (
            self._session.query(func.count(ProductModel.id))
            .filter(ProductModel.category_id == category_id)
            .scalar()
            or 0
        )

    @staticmethod
    def _to_domain(orm_category: CategoryModel) -> Category:
        return Category(
            id=orm_category.id,
            code=orm_category.code,
            name=orm_category.name,
            level=orm_category.level,
            parent_id=orm_category.parent_id,
            industry_sector=orm_category.industry_sector,
        )
