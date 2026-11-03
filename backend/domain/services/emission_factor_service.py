"""
Emission Factor Service - Domain Business Logic

Listing, creating, updating and deleting emission factors, and data source licences.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from typing import Any, Dict, List

from backend.domain.entities.emission_factor import (
    DataSourceLicense,
    EmissionFactor,
    EmissionFactorFilters,
    EmissionFactorPage,
    NewEmissionFactor,
)
from backend.domain.entities.errors import (
    DuplicateEmissionFactorError,
    EmissionFactorNotFoundError,
)
from backend.domain.repositories.interfaces import EmissionFactorRepository


class EmissionFactorService:
    """Domain service for emission factors."""

    def __init__(self, emission_factor_repo: EmissionFactorRepository):
        """
        Initialize the service with a repository.

        Args:
            emission_factor_repo: Repository implementing EmissionFactorRepository interface.
        """
        self._repo = emission_factor_repo

    def list_factors(
        self, filters: EmissionFactorFilters, limit: int = 100, offset: int = 0
    ) -> EmissionFactorPage:
        """List emission factors with pagination."""
        return self._repo.list_all(filters, limit=limit, offset=offset)

    def create_factor(self, factor: NewEmissionFactor) -> EmissionFactor:
        """
        Create an emission factor.

        Raises:
            DuplicateEmissionFactorError: If one already exists with the same activity,
                data source, geography and reference year.
        """
        if self._repo.exists(
            factor.activity_name, factor.data_source, factor.geography, factor.reference_year
        ):
            raise DuplicateEmissionFactorError(
                activity_name=factor.activity_name,
                data_source=factor.data_source,
                geography=factor.geography,
                reference_year=factor.reference_year,
            )
        return self._repo.create(factor)

    def update_factor(self, factor_id: str, changes: Dict[str, Any]) -> EmissionFactor:
        """
        Update an emission factor.

        Args:
            factor_id: The emission factor to update.
            changes: The fields to change; a None value leaves the field as it is.

        Raises:
            EmissionFactorNotFoundError: If the emission factor does not exist.
        """
        updated = self._repo.update(factor_id, changes)
        if updated is None:
            raise EmissionFactorNotFoundError(factor_id=factor_id)
        return updated

    def delete_factor(self, factor_id: str) -> None:
        """
        Delete an emission factor.

        Raises:
            EmissionFactorNotFoundError: If the emission factor does not exist.
        """
        if not self._repo.delete(factor_id):
            raise EmissionFactorNotFoundError(factor_id=factor_id)

    def list_licenses(self) -> List[DataSourceLicense]:
        """List licence and attribution details of the active data sources."""
        return self._repo.list_active_licenses()
