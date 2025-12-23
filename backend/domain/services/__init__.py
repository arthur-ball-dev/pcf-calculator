"""
Domain Services - Business Logic Layer

TASK-BE-P7-019: Domain Layer Separation

Contains domain services that encapsulate business logic.
Services depend only on repository interfaces, not implementations.

No infrastructure dependencies (SQLAlchemy, FastAPI) allowed here.
"""

from backend.domain.services.product_service import ProductService
from backend.domain.services.calculation_service import CalculationService

__all__ = [
    "ProductService",
    "CalculationService",
]
