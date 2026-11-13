"""
SQLAlchemy Emission Factor Repository Implementation

Implements EmissionFactorRepository using SQLAlchemy ORM.
Handles mapping between ORM models and domain entities.
"""

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from backend.domain.entities.emission_factor import (
    DataSourceLicense,
    EmissionFactor,
    EmissionFactorFilters,
    EmissionFactorPage,
    NewEmissionFactor,
)
from backend.domain.repositories.interfaces import EmissionFactorRepository
from backend.models import DataSource as DataSourceModel
from backend.models import EmissionFactor as EmissionFactorModel


def _decimal_or_none(value: Optional[float]) -> Optional[Decimal]:
    return Decimal(str(value)) if value else None


class SQLAlchemyEmissionFactorRepository(EmissionFactorRepository):
    """SQLAlchemy implementation of EmissionFactorRepository."""

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session.
        """
        self._session = session

    def list_all(
        self, filters: EmissionFactorFilters, limit: int = 100, offset: int = 0
    ) -> EmissionFactorPage:
        query = self._session.query(EmissionFactorModel)

        if filters.data_source is not None:
            query = query.filter(EmissionFactorModel.data_source == filters.data_source)
        if filters.geography is not None:
            query = query.filter(EmissionFactorModel.geography == filters.geography)
        if filters.unit is not None:
            query = query.filter(EmissionFactorModel.unit == filters.unit)
        if filters.activity_name is not None:
            query = query.filter(EmissionFactorModel.activity_name.ilike(f"%{filters.activity_name}%"))

        total = query.count()
        factors = query.offset(offset).limit(limit).all()

        return EmissionFactorPage(items=[self._to_domain(f) for f in factors], total=total)

    def exists(
        self,
        activity_name: str,
        data_source: str,
        geography: str,
        reference_year: Optional[int],
    ) -> bool:
        return (
            self._session.query(EmissionFactorModel)
            .filter(
                EmissionFactorModel.activity_name == activity_name,
                EmissionFactorModel.data_source == data_source,
                EmissionFactorModel.geography == geography,
                EmissionFactorModel.reference_year == reference_year,
            )
            .first()
            is not None
        )

    def get_by_ids(self, factor_ids: Iterable[str]) -> Dict[str, EmissionFactor]:
        ids = set(factor_ids)
        if not ids:
            return {}
        factors = (
            self._session.query(EmissionFactorModel)
            .filter(EmissionFactorModel.id.in_(ids))
            .all()
        )
        return {f.id: self._to_domain(f) for f in factors}

    def create(self, factor: NewEmissionFactor) -> EmissionFactor:
        orm_factor = EmissionFactorModel(
            activity_name=factor.activity_name,
            category=factor.category,
            co2e_factor=Decimal(str(factor.co2e_factor)),
            unit=factor.unit,
            data_source=factor.data_source,
            geography=factor.geography,
            reference_year=factor.reference_year,
            data_quality_rating=_decimal_or_none(factor.data_quality_rating),
            uncertainty_min=_decimal_or_none(factor.uncertainty_min),
            uncertainty_max=_decimal_or_none(factor.uncertainty_max),
            data_source_id=factor.data_source_id,
        )

        self._session.add(orm_factor)
        self._session.commit()
        self._session.refresh(orm_factor)

        return self._to_domain(orm_factor)

    def update(self, factor_id: str, changes: Dict[str, Any]) -> Optional[EmissionFactor]:
        orm_factor = self._find(factor_id)
        if orm_factor is None:
            return None

        for field, value in changes.items():
            if value is None:
                continue
            if field == "co2e_factor":
                setattr(orm_factor, field, Decimal(str(value)))
            elif field == "data_quality_rating":
                setattr(orm_factor, field, _decimal_or_none(value))
            else:
                setattr(orm_factor, field, value)

        self._session.commit()
        self._session.refresh(orm_factor)

        return self._to_domain(orm_factor)

    def delete(self, factor_id: str) -> bool:
        orm_factor = self._find(factor_id)
        if orm_factor is None:
            return False

        self._session.delete(orm_factor)
        self._session.commit()
        return True

    def list_active_licenses(self) -> List[DataSourceLicense]:
        data_sources = (
            self._session.query(DataSourceModel).filter(DataSourceModel.is_active == True).all()  # noqa: E712
        )
        return [
            DataSourceLicense(
                id=ds.id,
                name=ds.name,
                license_type=ds.license_type,
                license_url=ds.license_url,
                attribution_text=ds.attribution_text,
                attribution_url=ds.attribution_url,
                allows_commercial_use=ds.allows_commercial_use if ds.allows_commercial_use is not None else True,
                requires_attribution=ds.requires_attribution if ds.requires_attribution is not None else False,
                requires_share_alike=ds.requires_share_alike if ds.requires_share_alike is not None else False,
            )
            for ds in data_sources
        ]

    def _find(self, factor_id: str) -> Optional[EmissionFactorModel]:
        return (
            self._session.query(EmissionFactorModel)
            .filter(EmissionFactorModel.id == factor_id)
            .first()
        )

    @staticmethod
    def _to_domain(orm_factor: EmissionFactorModel) -> EmissionFactor:
        rating = orm_factor.data_quality_rating
        return EmissionFactor(
            id=orm_factor.id,
            activity_name=orm_factor.activity_name,
            category=orm_factor.category,
            co2e_factor=float(orm_factor.co2e_factor),
            unit=orm_factor.unit,
            data_source=orm_factor.data_source,
            geography=orm_factor.geography,
            reference_year=orm_factor.reference_year,
            data_quality_rating=float(rating) if rating else None,
            created_at=orm_factor.created_at,
        )
