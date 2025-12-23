"""
Product Domain Entity

TASK-BE-P7-019: Domain Layer Separation

Contains pure Python domain entities for Product-related concepts.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass
from typing import Optional, List

from backend.domain.entities.errors import DomainValidationError


@dataclass(frozen=True)
class Product:
    """
    Product domain entity - immutable, no ORM dependency.

    Represents a product or component in the PCF calculation system.
    Validation is performed on construction.

    Attributes:
        id: Unique identifier for the product (UUID string).
        code: Unique product code.
        name: Display name of the product.
        unit: Unit of measure (kg, unit, L, etc.).
        category: Optional product category.
        description: Optional description.
    """

    id: str
    code: str
    name: str
    unit: str
    category: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Validate entity on construction."""
        if not self.id:
            raise DomainValidationError("Product ID cannot be empty")
        if not self.code:
            raise DomainValidationError("Product code cannot be empty")
        if not self.name:
            raise DomainValidationError("Product name cannot be empty")


@dataclass(frozen=True)
class BOMItem:
    """
    Bill of Materials Item - represents a component in a product's BOM.

    Attributes:
        component_id: ID of the component product.
        quantity: Quantity of the component required.
        unit: Unit of measure for the quantity.
    """

    component_id: str
    quantity: float
    unit: str

    def __post_init__(self):
        """Validate entity on construction."""
        if self.quantity <= 0:
            raise DomainValidationError(
                f"BOM item quantity must be positive, got {self.quantity}"
            )


@dataclass(frozen=True)
class ProductWithBOM:
    """
    Composite entity containing a product and its Bill of Materials.

    Attributes:
        product: The parent product.
        bom_items: List of BOM items (components).
    """

    product: Product
    bom_items: List[BOMItem]
