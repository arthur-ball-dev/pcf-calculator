"""
FastAPI Dependency Injection for PCF Calculator.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module provides FastAPI dependencies for injecting the calculator
and its dependencies into API route handlers.

Usage in route handlers:
    @router.post("/calculate")
    async def calculate(
        calculator: PCFCalculator = Depends(get_calculator)
    ):
        result = await calculator.calculate(...)
"""

from typing import Generator

from fastapi import Depends

from backend.config import settings
from backend.database.connection import get_db
from backend.calculator.cache import CachedEmissionFactorProvider
from backend.calculator.pcf_calculator import PCFCalculator
from backend.calculator.providers import EmissionFactorProvider
from backend.calculator.sqlalchemy_provider import SQLAlchemyEmissionFactorProvider


async def get_ef_provider(
    session=Depends(get_db),
) -> EmissionFactorProvider:
    """
    Get emission factor provider with caching.

    Creates a SQLAlchemy-backed provider wrapped with caching layer.
    Uses TTL from application settings.

    Args:
        session: SQLAlchemy session from get_db dependency

    Returns:
        CachedEmissionFactorProvider wrapping SQLAlchemyEmissionFactorProvider

    Example usage in route:
        @router.get("/emission-factors/{category}")
        async def get_ef(
            category: str,
            provider: EmissionFactorProvider = Depends(get_ef_provider)
        ):
            ef = await provider.get_by_category(category)
            return ef
    """
    sql_provider = SQLAlchemyEmissionFactorProvider(session)

    # Get TTL from settings (default 300 seconds = 5 minutes)
    ttl = getattr(settings, "emission_factor_cache_ttl", 300)

    return CachedEmissionFactorProvider(sql_provider, ttl_seconds=ttl)


async def get_calculator(
    ef_provider: EmissionFactorProvider = Depends(get_ef_provider),
) -> PCFCalculator:
    """
    Get PCF calculator with injected dependencies.

    Creates a calculator instance with the cached emission factor provider.
    This is the recommended way to get a calculator instance in API routes.

    Args:
        ef_provider: Emission factor provider from get_ef_provider dependency

    Returns:
        PCFCalculator configured with the injected provider

    Example usage in route:
        @router.post("/calculate")
        async def calculate_pcf(
            request: CalculationRequest,
            calculator: PCFCalculator = Depends(get_calculator)
        ):
            result = await calculator.calculate(
                product_id=request.product_id,
                bom_items=request.bom_items
            )
            return result
    """
    return PCFCalculator(ef_provider=ef_provider)
