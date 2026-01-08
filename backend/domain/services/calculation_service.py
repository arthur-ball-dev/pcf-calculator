"""
Calculation Service - Domain Business Logic

TASK-BE-P7-019: Domain Layer Separation

Contains business logic for calculation-related operations.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from typing import List

from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import (
    ProductNotFoundError,
    CalculationNotFoundError,
    DomainValidationError,
)
from backend.domain.repositories.interfaces import (
    CalculationRepository,
    ProductRepository,
)


# Valid calculation methods
VALID_CALCULATION_METHODS = {"attributional", "consequential"}


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
    ):
        """
        Initialize the service with repositories.

        Args:
            calculation_repo: Repository implementing CalculationRepository interface.
            product_repo: Repository implementing ProductRepository interface.
        """
        self._calculation_repo = calculation_repo
        self._product_repo = product_repo

    async def create_calculation(
        self, request: CreateCalculationRequest
    ) -> CalculationResult:
        """
        Create a new calculation request.

        Validates that the product exists and the calculation method is valid
        before creating the calculation.

        Args:
            request: CreateCalculationRequest with calculation parameters.

        Returns:
            CalculationResult with pending status.

        Raises:
            ProductNotFoundError: If the product does not exist.
            DomainValidationError: If the calculation method is invalid.
        """
        # Validate calculation method
        if request.calculation_method not in VALID_CALCULATION_METHODS:
            raise DomainValidationError(
                f"Invalid calculation_method: {request.calculation_method}. "
                f"Must be one of: {', '.join(sorted(VALID_CALCULATION_METHODS))}"
            )

        # Validate product exists
        product = await self._product_repo.get_by_id(request.product_id)
        if product is None:
            raise ProductNotFoundError(product_id=request.product_id)

        # Create calculation
        return await self._calculation_repo.create(request)

    async def get_calculation(self, calculation_id: str) -> Calculation:
        """
        Get a calculation by ID.

        Args:
            calculation_id: The unique identifier of the calculation.

        Returns:
            Calculation domain entity.

        Raises:
            CalculationNotFoundError: If the calculation does not exist.
        """
        calculation = await self._calculation_repo.get_by_id(calculation_id)
        if calculation is None:
            raise CalculationNotFoundError(calculation_id=calculation_id)
        return calculation

    async def list_calculations_for_product(
        self, product_id: str
    ) -> List[Calculation]:
        """
        List all calculations for a specific product.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            List of Calculation domain entities.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        # Validate product exists
        product = await self._product_repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id=product_id)

        return await self._calculation_repo.list_for_product(product_id)
