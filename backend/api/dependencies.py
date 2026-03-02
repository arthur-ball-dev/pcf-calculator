"""
FastAPI Dependency Injection for PCF Calculator.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache
TASK-BE-P7-050: Wire Domain Layer to API Routes

This module provides FastAPI dependencies for injecting the calculator,
domain services, and repositories into API route handlers.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.connection import get_db
from backend.calculator.cache import CachedEmissionFactorProvider
from backend.calculator.pcf_calculator import PCFCalculator
from backend.calculator.providers import EmissionFactorProvider
from backend.calculator.sqlalchemy_provider import SQLAlchemyEmissionFactorProvider

# Domain layer imports
from backend.domain.services.product_service import ProductService
from backend.domain.services.calculation_service import CalculationService
from backend.domain.repositories.interfaces import (
    ProductRepository,
    CalculationRepository,
)
# Infrastructure layer imports
from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
    SQLAlchemyCalculationRepository,
)

# ============================================================================
# Calculator Dependencies (existing)
# ============================================================================


async def get_ef_provider(
    session=Depends(get_db),
) -> EmissionFactorProvider:
    sql_provider = SQLAlchemyEmissionFactorProvider(session)
    ttl = getattr(settings, "emission_factor_cache_ttl", 300)
    return CachedEmissionFactorProvider(sql_provider, ttl_seconds=ttl)


async def get_calculator(
    ef_provider: EmissionFactorProvider = Depends(get_ef_provider),
) -> PCFCalculator:
    return PCFCalculator(ef_provider=ef_provider)


# ============================================================================
# Repository Dependencies (TASK-BE-P7-050 - Async)
# ============================================================================


def get_product_repository(
    session: Session = Depends(get_db),
) -> ProductRepository:
    return SQLAlchemyProductRepository(session)


def get_calculation_repository(
    session: Session = Depends(get_db),
) -> CalculationRepository:
    return SQLAlchemyCalculationRepository(session)


# ============================================================================
# Domain Service Dependencies (TASK-BE-P7-050 - Async)
# ============================================================================


def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(product_repo)


def get_calculation_service(
    calculation_repo: CalculationRepository = Depends(get_calculation_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
) -> CalculationService:
    return CalculationService(calculation_repo, product_repo)
