"""
SQLAlchemy Repository Implementations

TASK-BE-P7-019: Domain Layer Separation

Contains SQLAlchemy implementations of domain repository interfaces.
"""

from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from backend.infrastructure.repositories.sqlalchemy_category_repository import (
    SQLAlchemyCategoryRepository,
)
from backend.infrastructure.repositories.sqlalchemy_emission_factor_repository import (
    SQLAlchemyEmissionFactorRepository,
)
from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
    SQLAlchemyCalculationRepository,
)

__all__ = [
    "SQLAlchemyProductRepository",
    "SQLAlchemyCalculationRepository",
    "SQLAlchemyCategoryRepository",
    "SQLAlchemyEmissionFactorRepository",
]
