"""
SQLAlchemy Calculation Repository Implementation

TASK-BE-P7-019: Domain Layer Separation

Implements CalculationRepository interface using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.repositories.interfaces import CalculationRepository
from backend.models import PCFCalculation as CalculationModel
from backend.models import generate_uuid


def _optional_float(value) -> Optional[float]:
    return float(value) if value is not None else None


class SQLAlchemyCalculationRepository(CalculationRepository):
    """
    SQLAlchemy implementation of CalculationRepository.

    Maps ORM models to domain entities and handles database operations.
    """

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session.
        """
        self._session = session

    def get_by_id(self, calculation_id: str) -> Optional[Calculation]:
        """
        Get calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity if found, None otherwise.
        """
        orm_calc = self._session.execute(
            select(CalculationModel).where(CalculationModel.id == calculation_id)
        ).scalar_one_or_none()

        if orm_calc is None:
            return None

        return self._to_domain(orm_calc)

    def create(self, request: CreateCalculationRequest) -> CalculationResult:
        """
        Create a new calculation request.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.
        """
        calculation_id = generate_uuid()

        self._session.add(
            CalculationModel(
                id=calculation_id,
                product_id=request.product_id,
                calculation_type=request.calculation_type,
                status="pending",
                total_co2e_kg=0.0,  # Will be updated when calculation completes
                created_at=datetime.now(UTC),
            )
        )
        self._session.commit()

        return CalculationResult(
            id=calculation_id,
            status="pending",
            product_id=request.product_id,
        )

    def delete_older_than(self, age: timedelta) -> int:
        """
        Delete calculations created more than `age` ago, measured on the database clock (#196).

        Their calculation_details rows go with them (ON DELETE CASCADE).
        """
        result = self._session.execute(
            delete(CalculationModel).where(CalculationModel.created_at < func.now() - age)
        )
        self._session.commit()
        return result.rowcount or 0

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
            materials_co2e=_optional_float(orm_calc.materials_co2e),
            energy_co2e=_optional_float(orm_calc.energy_co2e),
            transport_co2e=_optional_float(orm_calc.transport_co2e),
            waste_co2e=_optional_float(orm_calc.waste_co2e),
            created_at=orm_calc.created_at,
            calculation_time_ms=orm_calc.calculation_time_ms,
            breakdown=orm_calc.breakdown,
            error_message=self._error_message(orm_calc),
        )

    @staticmethod
    def _error_message(orm_calc: CalculationModel) -> Optional[str]:
        """Failed runs record their error in metadata; older rows used input_data."""
        for stored in (orm_calc.calculation_metadata, orm_calc.input_data):
            if stored and stored.get("error_message"):
                return stored["error_message"]
        return None
