"""
SQLAlchemy Implementation of Emission Factor Provider.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module provides the concrete SQLAlchemy implementation of the
EmissionFactorProvider interface, allowing the PCF calculator to
access emission factors from the database.

Design Notes:
- This is the ONLY module in the calculator package that imports SQLAlchemy
- All database operations are async-compatible using SQLAlchemy sessions
- Converts ORM models to DTOs to maintain separation of concerns
"""

from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .providers import EmissionFactorDTO, EmissionFactorProvider


class SQLAlchemyEmissionFactorProvider(EmissionFactorProvider):
    """
    SQLAlchemy implementation of EmissionFactorProvider.

    This provider fetches emission factors from the database using
    SQLAlchemy ORM and converts them to EmissionFactorDTO objects.

    Note: This implementation uses synchronous SQLAlchemy sessions.
    The async interface methods are implemented synchronously but
    are compatible with async wrappers if needed.

    Example:
        >>> from backend.database.connection import db_context
        >>> with db_context() as session:
        ...     provider = SQLAlchemyEmissionFactorProvider(session)
        ...     ef = await provider.get_by_category("steel")

    Attributes:
        session: SQLAlchemy database session
    """

    def __init__(self, session: Session):
        """
        Initialize with SQLAlchemy session.

        Args:
            session: SQLAlchemy database session (sync or async)
        """
        self._session = session

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """
        Get emission factor by category name.

        Queries the emission_factors table for an active emission factor
        matching the given category. Returns the first match.

        Args:
            category: Material/process category name (e.g., "steel", "aluminum")

        Returns:
            EmissionFactorDTO if found, None otherwise

        Note:
            Uses case-insensitive matching for category lookup.
        """
        # Import here to avoid circular imports and keep SQLAlchemy imports isolated
        from backend.models import EmissionFactor

        # Query for matching category (case-insensitive, active only)
        # Try exact match first, then case-insensitive
        result = self._session.query(EmissionFactor).filter(
            EmissionFactor.category == category,
            EmissionFactor.is_active == True  # noqa: E712
        ).first()

        # If no exact match, try case-insensitive
        if result is None:
            result = self._session.query(EmissionFactor).filter(
                EmissionFactor.category.ilike(category),
                EmissionFactor.is_active == True  # noqa: E712
            ).first()

        # If still no match, try activity_name as fallback
        if result is None:
            result = self._session.query(EmissionFactor).filter(
                EmissionFactor.activity_name.ilike(category),
                EmissionFactor.is_active == True  # noqa: E712
            ).first()

        if result is None:
            return None

        return self._to_dto(result)

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """
        Get all active emission factors.

        Returns:
            Dictionary mapping category names to EmissionFactorDTO objects
            If multiple emission factors share a category, the first one
            encountered is used.
        """
        from backend.models import EmissionFactor

        results = self._session.query(EmissionFactor).filter(
            EmissionFactor.is_active == True  # noqa: E712
        ).all()

        efs: Dict[str, EmissionFactorDTO] = {}
        for ef in results:
            # Use category if available, otherwise activity_name
            key = ef.category if ef.category else ef.activity_name
            if key and key not in efs:
                efs[key] = self._to_dto(ef)

        return efs

    def _to_dto(self, orm_ef) -> EmissionFactorDTO:
        """
        Convert SQLAlchemy EmissionFactor model to EmissionFactorDTO.

        Args:
            orm_ef: SQLAlchemy EmissionFactor model instance

        Returns:
            EmissionFactorDTO with data from the ORM model
        """
        return EmissionFactorDTO(
            id=str(orm_ef.id),
            category=orm_ef.category or orm_ef.activity_name,
            co2e_kg=float(orm_ef.co2e_factor),
            unit=orm_ef.unit,
            data_source=orm_ef.data_source,
            uncertainty=self._calculate_uncertainty(orm_ef)
        )

    def _calculate_uncertainty(self, orm_ef) -> Optional[float]:
        """
        Calculate uncertainty value from min/max range.

        If both uncertainty_min and uncertainty_max are set,
        calculates uncertainty as a relative range.

        Args:
            orm_ef: SQLAlchemy EmissionFactor model instance

        Returns:
            Uncertainty as float (0.0-1.0) or None if not available
        """
        if orm_ef.uncertainty_min is not None and orm_ef.uncertainty_max is not None:
            factor = float(orm_ef.co2e_factor)
            if factor > 0:
                min_val = float(orm_ef.uncertainty_min)
                max_val = float(orm_ef.uncertainty_max)
                # Return relative uncertainty as (max - min) / (2 * factor)
                return (max_val - min_val) / (2 * factor)
        return None
