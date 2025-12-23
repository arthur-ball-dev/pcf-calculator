"""
SQLAlchemy Calculation Repository Implementation

TASK-BE-P7-019: Domain Layer Separation

Implements CalculationRepository interface using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select

from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.repositories.interfaces import CalculationRepository
from backend.models import PCFCalculation as CalculationModel


class SQLAlchemyCalculationRepository(CalculationRepository):
    """
    SQLAlchemy implementation of CalculationRepository.

    Maps ORM models to domain entities and handles database operations.
    """

    def __init__(self, session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy AsyncSession or Session.
        """
        self._session = session

    async def get_by_id(self, calculation_id: str) -> Optional[Calculation]:
        """
        Get calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity if found, None otherwise.
        """
        result = await self._session.execute(
            select(CalculationModel).where(CalculationModel.id == calculation_id)
        )
        orm_calc = result.scalar_one_or_none()

        if orm_calc is None:
            return None

        return self._to_domain(orm_calc)

    async def create(self, request: CreateCalculationRequest) -> CalculationResult:
        """
        Create a new calculation request.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.
        """
        calculation_id = uuid.uuid4().hex

        orm_calc = CalculationModel(
            id=calculation_id,
            product_id=request.product_id,
            calculation_method=request.calculation_method,
            status="pending",
            total_co2e_kg=0.0,  # Will be updated when calculation completes
        )

        self._session.add(orm_calc)
        await self._session.commit()
        await self._session.refresh(orm_calc)

        return CalculationResult(
            id=calculation_id,
            status="pending",
            product_id=request.product_id,
        )

    async def list_for_product(self, product_id: str) -> List[Calculation]:
        """
        List all calculations for a specific product.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            List of Calculation domain entities.
        """
        result = await self._session.execute(
            select(CalculationModel).where(
                CalculationModel.product_id == product_id
            )
        )
        orm_calcs = result.scalars().all()

        return [self._to_domain(c) for c in orm_calcs]

    def _to_domain(self, orm_calc: CalculationModel) -> Calculation:
        """
        Convert ORM model to domain entity.

        Args:
            orm_calc: SQLAlchemy ORM PCFCalculation model.

        Returns:
            Calculation domain entity.
        """
        return Calculation(
            id=orm_calc.id,
            product_id=orm_calc.product_id,
            total_co2e_kg=float(orm_calc.total_co2e_kg),
            status=orm_calc.status,
            calculation_type=orm_calc.calculation_type,
            materials_co2e=(
                float(orm_calc.materials_co2e)
                if orm_calc.materials_co2e is not None
                else None
            ),
            energy_co2e=(
                float(orm_calc.energy_co2e)
                if orm_calc.energy_co2e is not None
                else None
            ),
            transport_co2e=(
                float(orm_calc.transport_co2e)
                if orm_calc.transport_co2e is not None
                else None
            ),
            waste_co2e=(
                float(orm_calc.waste_co2e)
                if orm_calc.waste_co2e is not None
                else None
            ),
        )
