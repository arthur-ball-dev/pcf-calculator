"""
Repository Interfaces - Abstract Data Access Layer

TASK-BE-P7-019: Domain Layer Separation

Contains abstract repository interfaces that define data access contracts.
No infrastructure dependencies (SQLAlchemy) allowed in this module.
"""

from backend.domain.repositories.interfaces import (
    ProductRepository,
    CategoryRepository,
    EmissionFactorRepository,
    CalculationRepository,
)

__all__ = [
    "ProductRepository",
    "CategoryRepository",
    "EmissionFactorRepository",
    "CalculationRepository",
]
