"""
Calculation Service - Domain Business Logic

TASK-BE-P7-019: Domain Layer Separation

Contains business logic for calculation-related operations.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple

from backend.domain.entities.calculation import (
    BOMLineInput,
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
    ResolvedBOMLine,
)
from backend.domain.entities.errors import (
    DomainValidationError,
    ProductNotFoundError,
    CalculationNotFoundError,
)
from backend.domain.repositories.interfaces import (
    CalculationRepository,
    EmissionFactorRepository,
    ProductRepository,
)
from backend.domain.units import are_compatible, convert

# How long a calculation result is kept (#196)
RESULT_LIFETIME = timedelta(hours=1)


class CalculationService:
    """
    Domain service for calculation operations.

    Encapsulates business logic and coordinates with repositories.
    Uses dependency injection for repositories.
    """

    def __init__(
        self,
        calculation_repo: CalculationRepository,
        product_repo: ProductRepository,
        emission_factor_repo: Optional[EmissionFactorRepository] = None,
    ):
        """
        Initialize the service with repositories.

        Args:
            calculation_repo: Repository implementing CalculationRepository interface.
            product_repo: Repository implementing ProductRepository interface.
            emission_factor_repo: Needed to validate a submitted BOM.
        """
        self._calculation_repo = calculation_repo
        self._product_repo = product_repo
        self._emission_factor_repo = emission_factor_repo

    def create_calculation(self, request: CreateCalculationRequest) -> CalculationResult:
        """
        Create a pending calculation for an existing product.

        The calculation type is validated by the API schema.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.

        Raises:
            ProductNotFoundError: If the product does not exist.
            DomainValidationError: If a submitted BOM is invalid (no calculation is created).
        """
        product = self._product_repo.get_by_id(request.product_id)
        if product is None:
            raise ProductNotFoundError(product_id=request.product_id)

        resolved = self._resolve_bom(request.bom) if request.bom is not None else None

        # A result is read only while the browser polls for it; drop ones from earlier
        # sessions so the user's BOM rows in their breakdown don't linger (#196)
        self._calculation_repo.delete_older_than(RESULT_LIFETIME)

        result = self._calculation_repo.create(request)
        return replace(result, resolved_bom=resolved) if resolved is not None else result

    def _resolve_bom(self, lines: Sequence[BOMLineInput]) -> Tuple[ResolvedBOMLine, ...]:
        """
        Validate a submitted BOM and convert each quantity to its emission factor's unit (#195).

        Every row needs an existing emission factor, a unit of the factor unit's kind and a
        name not used by an earlier row (case and surrounding space ignored): the breakdown is
        keyed by name. All problems are reported together, each with its row's field path.
        """
        if self._emission_factor_repo is None:
            raise RuntimeError(
                "CalculationService needs an emission factor repository for a submitted BOM"
            )
        factors = self._emission_factor_repo.get_by_ids(
            {line.emission_factor_id for line in lines}
        )

        details: List[Dict[str, str]] = []
        resolved: List[ResolvedBOMLine] = []
        seen_names = set()
        for index, line in enumerate(lines):
            name_key = line.name.strip().casefold()
            if name_key in seen_names:
                details.append({
                    "field": f"body.bom.{index}.name",
                    "message": f"Another component is already named '{line.name}'",
                })
                continue
            seen_names.add(name_key)

            factor = factors.get(line.emission_factor_id)
            if factor is None:
                details.append({
                    "field": f"body.bom.{index}.emission_factor_id",
                    "message": f"No emission factor exists with ID {line.emission_factor_id}",
                })
                continue
            if not are_compatible(line.unit, factor.unit):
                details.append({
                    "field": f"body.bom.{index}.unit",
                    "message": (
                        f"Unit '{line.unit}' cannot be converted to the emission factor's "
                        f"unit '{factor.unit}'"
                    ),
                })
                continue
            resolved.append(ResolvedBOMLine(
                name=line.name,
                quantity=convert(line.quantity, line.unit, factor.unit),
                co2e_factor=Decimal(str(factor.co2e_factor)),
                category=line.category,
            ))

        if details:
            raise DomainValidationError("The bill of materials is invalid", details=details)
        return tuple(resolved)

    def get_calculation(self, calculation_id: str) -> Calculation:
        """
        Get a calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity.

        Raises:
            CalculationNotFoundError: If the calculation does not exist.
        """
        calculation = self._calculation_repo.get_by_id(calculation_id)
        if calculation is None:
            raise CalculationNotFoundError(calculation_id=calculation_id)
        return calculation
