"""
Calculator Exception Classes.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module defines custom exceptions for the PCF calculator,
providing clear error messages for common failure scenarios.
"""


class CalculatorError(Exception):
    """
    Base exception for all calculator errors.

    All calculator-specific exceptions should inherit from this class
    to allow catching all calculator errors with a single except clause.
    """

    pass


class EmissionFactorNotFoundError(CalculatorError):
    """
    Raised when an emission factor is not found for a given category.

    This exception is raised during PCF calculations when a BOM item
    references a material/category that has no corresponding emission
    factor in the database.

    Attributes:
        category: The category that was not found
        message: Descriptive error message

    Example:
        >>> raise EmissionFactorNotFoundError("unknown_material")
        EmissionFactorNotFoundError: No emission factor found for category: unknown_material
    """

    def __init__(self, category: str, message: str = None):
        """
        Initialize exception with category name.

        Args:
            category: The category that was not found
            message: Optional custom message (auto-generated if not provided)
        """
        self.category = category
        if message is None:
            message = f"No emission factor found for category: {category}"
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class CalculationError(CalculatorError):
    """
    Raised when a calculation fails for any reason.

    This exception is raised when the PCF calculation encounters
    an error that prevents completion.

    Attributes:
        product_id: ID of the product being calculated
        reason: Description of what went wrong
    """

    def __init__(self, product_id: str, reason: str):
        """
        Initialize exception with product ID and reason.

        Args:
            product_id: ID of the product being calculated
            reason: Description of what went wrong
        """
        self.product_id = product_id
        self.reason = reason
        message = f"Calculation failed for product {product_id}: {reason}"
        super().__init__(message)


class CircularReferenceError(CalculatorError):
    """
    Raised when a circular reference is detected in the BOM.

    This exception is raised during BOM traversal when a product
    references itself (directly or indirectly) creating an infinite loop.

    Attributes:
        product_ids: List of product IDs in the circular reference chain
    """

    def __init__(self, product_ids: list):
        """
        Initialize exception with product ID chain.

        Args:
            product_ids: List of product IDs forming the circular reference
        """
        self.product_ids = product_ids
        chain = " -> ".join(product_ids)
        message = f"Circular reference detected in BOM: {chain}"
        super().__init__(message)


class MaxDepthExceededError(CalculatorError):
    """
    Raised when BOM traversal exceeds maximum depth.

    This exception is raised as a safety measure to prevent
    extremely deep BOM hierarchies from causing stack overflow
    or excessive resource consumption.

    Attributes:
        max_depth: The maximum allowed depth
        product_id: ID of the product where limit was exceeded
    """

    def __init__(self, max_depth: int, product_id: str = None):
        """
        Initialize exception with depth limit and product ID.

        Args:
            max_depth: The maximum allowed depth
            product_id: Optional ID of the product where limit was exceeded
        """
        self.max_depth = max_depth
        self.product_id = product_id
        if product_id:
            message = f"Maximum BOM depth ({max_depth}) exceeded at product {product_id}"
        else:
            message = f"Maximum BOM depth ({max_depth}) exceeded"
        super().__init__(message)
