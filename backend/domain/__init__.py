"""
Domain Layer - Pure Business Logic

TASK-BE-P7-019: Domain Layer Separation

This package contains the domain layer of the application:
- entities/: Pure Python domain entities (no ORM)
- repositories/: Abstract repository interfaces
- services/: Domain services containing business logic

The domain layer has NO dependencies on infrastructure (SQLAlchemy, FastAPI, etc.)
"""

from backend.domain.entities.product import Product, BOMItem, ProductWithBOM
from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import (
    DomainValidationError,
    ProductNotFoundError,
    DuplicateProductError,
    CalculationNotFoundError,
)
from backend.domain.repositories.interfaces import (
    ProductRepository,
    CalculationRepository,
    BOMRepository,
)
from backend.domain.services.product_service import ProductService
from backend.domain.services.calculation_service import CalculationService

__all__ = [
    # Entities
    "Product",
    "BOMItem",
    "ProductWithBOM",
    "Calculation",
    "CalculationResult",
    "CreateCalculationRequest",
    # Errors
    "DomainValidationError",
    "ProductNotFoundError",
    "DuplicateProductError",
    "CalculationNotFoundError",
    # Repository Interfaces
    "ProductRepository",
    "CalculationRepository",
    "BOMRepository",
    # Services
    "ProductService",
    "CalculationService",
]
