"""
FastAPI Dependency Injection for PCF Calculator.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache
TASK-BE-P7-050: Wire Domain Layer to API Routes

This module provides FastAPI dependencies for injecting the calculator,
domain services, and repositories into API route handlers.
"""

from typing import Generator, Optional, List, Tuple

from fastapi import Depends
from sqlalchemy.orm import Session, joinedload

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
from backend.domain.entities.product import Product, BOMItem, ProductWithBOM
from backend.domain.entities.calculation import Calculation
from backend.domain.entities.errors import ProductNotFoundError, CalculationNotFoundError

# Infrastructure layer imports
from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
    SQLAlchemyCalculationRepository,
)

# ORM Models for sync access
from backend.models import Product as ProductModel
from backend.models import BillOfMaterials as BOMModel
from backend.models import PCFCalculation as CalculationModel


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


# ============================================================================
# Sync Service Layer (TASK-BE-P7-050)
# ============================================================================


class SyncProductService:
    def __init__(self, session: Session):
        self._session = session

    def get_product(self, product_id: str) -> Optional[Product]:
        orm_product = (
            self._session.query(ProductModel)
            .filter(ProductModel.id == product_id)
            .first()
        )
        if orm_product is None:
            return None
        return Product(
            id=orm_product.id,
            code=orm_product.code,
            name=orm_product.name,
            unit=orm_product.unit,
            category=orm_product.category,
            description=orm_product.description,
        )

    def list_products(
        self,
        limit: int = 100,
        offset: int = 0,
        is_finished: Optional[bool] = None
    ) -> Tuple[List[Product], int]:
        query = self._session.query(ProductModel)
        if is_finished is not None:
            query = query.filter(ProductModel.is_finished_product == is_finished)
        total = query.count()
        orm_products = query.offset(offset).limit(limit).all()
        products = [
            Product(
                id=p.id,
                code=p.code,
                name=p.name,
                unit=p.unit,
                category=p.category,
                description=p.description,
            )
            for p in orm_products
        ]
        return products, total

    def get_product_with_bom(self, product_id: str) -> Optional[dict]:
        orm_product = (
            self._session.query(ProductModel)
            .options(
                joinedload(ProductModel.bom_items)
                .joinedload(BOMModel.child_product)
            )
            .filter(ProductModel.id == product_id)
            .first()
        )
        if orm_product is None:
            return None
        bom_details = []
        for bom in orm_product.bom_items:
            child_name = bom.child_product.name if bom.child_product else "Unknown"
            bom_details.append({
                "id": bom.id,
                "child_product_id": bom.child_product_id,
                "child_product_name": child_name,
                "quantity": float(bom.quantity),
                "unit": bom.unit,
                "notes": bom.notes,
            })
        return {
            "product": orm_product,
            "bom_items": bom_details,
        }


class SyncCalculationService:
    def __init__(self, session: Session):
        self._session = session

    def get_calculation(self, calculation_id: str) -> Optional[Calculation]:
        orm_calc = (
            self._session.query(CalculationModel)
            .filter(CalculationModel.id == calculation_id)
            .first()
        )
        if orm_calc is None:
            return None
        return Calculation(
            id=orm_calc.id,
            product_id=orm_calc.product_id,
            total_co2e_kg=float(orm_calc.total_co2e_kg) if orm_calc.total_co2e_kg else 0.0,
            status=orm_calc.status,
            calculation_type=orm_calc.calculation_type,
            materials_co2e=float(orm_calc.materials_co2e) if orm_calc.materials_co2e is not None else None,
            energy_co2e=float(orm_calc.energy_co2e) if orm_calc.energy_co2e is not None else None,
            transport_co2e=float(orm_calc.transport_co2e) if orm_calc.transport_co2e is not None else None,
            waste_co2e=float(orm_calc.waste_co2e) if orm_calc.waste_co2e is not None else None,
        )

    def get_calculation_raw(self, calculation_id: str) -> Optional[CalculationModel]:
        return (
            self._session.query(CalculationModel)
            .filter(CalculationModel.id == calculation_id)
            .first()
        )

    def list_calculations_for_product(self, product_id: str) -> List[Calculation]:
        orm_calcs = (
            self._session.query(CalculationModel)
            .filter(CalculationModel.product_id == product_id)
            .all()
        )
        return [
            Calculation(
                id=c.id,
                product_id=c.product_id,
                total_co2e_kg=float(c.total_co2e_kg) if c.total_co2e_kg else 0.0,
                status=c.status,
                calculation_type=c.calculation_type,
                materials_co2e=float(c.materials_co2e) if c.materials_co2e is not None else None,
                energy_co2e=float(c.energy_co2e) if c.energy_co2e is not None else None,
                transport_co2e=float(c.transport_co2e) if c.transport_co2e is not None else None,
                waste_co2e=float(c.waste_co2e) if c.waste_co2e is not None else None,
            )
            for c in orm_calcs
        ]


# ============================================================================
# Sync Service Dependencies (TASK-BE-P7-050)
# ============================================================================


def get_sync_product_service(
    session: Session = Depends(get_db),
) -> SyncProductService:
    return SyncProductService(session)


def get_sync_calculation_service(
    session: Session = Depends(get_db),
) -> SyncCalculationService:
    return SyncCalculationService(session)
