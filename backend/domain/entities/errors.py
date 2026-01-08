"""
Domain-specific Error Classes

TASK-BE-P7-019: Domain Layer Separation

Contains error classes for domain-level exceptions.
These are distinct from infrastructure errors (database, HTTP, etc.)
"""


class DomainValidationError(Exception):
    """
    Raised when domain entity validation fails.

    This error is raised during entity construction when
    business rules are violated.
    """

    def __init__(self, message: str):
        self.message = message
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


class DuplicateProductError(Exception):
    """
    Raised when attempting to create a product with a duplicate code.

    Attributes:
        code: The product code that already exists.
    """

    def __init__(self, code: str):
        self.code = code
        self.message = f"Product with code already exists: {code}"
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
