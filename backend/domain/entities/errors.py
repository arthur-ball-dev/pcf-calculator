"""
Domain-specific Error Classes

TASK-BE-P7-019: Domain Layer Separation

Contains error classes for domain-level exceptions.
These are distinct from infrastructure errors (database, HTTP, etc.)
"""


from typing import Dict, List, Optional


class DomainValidationError(Exception):
    """
    Raised when domain entity validation fails.

    This error is raised during entity construction when
    business rules are violated.
    """

    def __init__(self, message: str, details: Optional[List[Dict[str, str]]] = None):
        """
        Args:
            message: Human-readable summary.
            details: Optional per-field errors, each {"field": ..., "message": ...}; returned
                as the error envelope's details.
        """
        self.message = message
        self.details = details or []
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class ProductNotFoundError(Exception):
    """
    Raised when a product is not found in the repository.

    Attributes:
        product_id: The ID of the product that was not found.
    """

    def __init__(self, product_id: str):
        self.product_id = product_id
        self.message = f"Product not found: {product_id}"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class CategoryNotFoundError(Exception):
    """
    Raised when a product category is not found in the repository.

    Attributes:
        category_id: The ID of the category that was not found.
    """

    def __init__(self, category_id: str):
        self.category_id = category_id
        self.message = f"Category not found: {category_id}"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class EmissionFactorNotFoundError(Exception):
    """
    Raised when an emission factor is not found in the repository.

    Attributes:
        factor_id: The ID of the emission factor that was not found.
    """

    def __init__(self, factor_id: str):
        self.factor_id = factor_id
        self.message = "Emission factor not found"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class DuplicateEmissionFactorError(Exception):
    """Raised when an emission factor with the same composite key already exists."""

    def __init__(
        self,
        activity_name: str,
        data_source: str,
        geography: str,
        reference_year: Optional[int],
    ):
        self.message = (
            f"Emission factor already exists for activity '{activity_name}' "
            f"with data_source='{data_source}', "
            f"geography='{geography}', "
            f"reference_year={reference_year}"
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class CalculationNotFoundError(Exception):
    """
    Raised when a calculation is not found in the repository.

    Attributes:
        calculation_id: The ID of the calculation that was not found.
    """

    def __init__(self, calculation_id: str):
        self.calculation_id = calculation_id
        self.message = f"Calculation not found: {calculation_id}"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
