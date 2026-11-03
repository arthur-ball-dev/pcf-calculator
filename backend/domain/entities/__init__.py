"""
Domain Entities - Pure Python Objects

TASK-BE-P7-019: Domain Layer Separation

Contains immutable domain entities that represent core business concepts.
These entities are free from any infrastructure dependencies (no SQLAlchemy).
"""

from backend.domain.entities.product import Product, BOMItem, ProductWithBOM
from backend.domain.entities.category import Category, CategoryNode, CategoryTree
from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import (
    DomainValidationError,
    ProductNotFoundError,
    CategoryNotFoundError,
    EmissionFactorNotFoundError,
    DuplicateEmissionFactorError,
    CalculationNotFoundError,
)

__all__ = [
    "Product",
    "BOMItem",
    "ProductWithBOM",
    "Category",
    "CategoryNode",
    "CategoryTree",
    "Calculation",
    "CalculationResult",
    "CreateCalculationRequest",
    "DomainValidationError",
    "ProductNotFoundError",
    "CategoryNotFoundError",
    "EmissionFactorNotFoundError",
    "DuplicateEmissionFactorError",
    "CalculationNotFoundError",
]
