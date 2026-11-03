"""
Calculation Service - Domain Business Logic

TASK-BE-P7-019: Domain Layer Separation

Contains business logic for calculation-related operations.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from backend.domain.entities.calculation import (
    Calculation,
    CalculationResult,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import (
    ProductNotFoundError,
    CalculationNotFoundError,
)
from backend.domain.repositories.interfaces import (
    CalculationRepository,
    ProductRepository,
)


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
        """
        product = self._product_repo.get_by_id(request.product_id)
        if product is None:
            raise ProductNotFoundError(product_id=request.product_id)

        return self._calculation_repo.create(request)

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
