"""
Product Domain Entity

TASK-BE-P7-019: Domain Layer Separation

Contains pure Python domain entities for Product-related concepts.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from backend.domain.entities.errors import DomainValidationError


@dataclass(frozen=True)
class CategorySummary:
    """The category linked to a product."""

    id: str
    code: str
    name: str
    industry_sector: Optional[str] = None


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
        is_finished_product: Finished good rather than component.
        created_at: When the product was created.
        manufacturer: Optional manufacturer name.
        country_of_origin: Optional ISO country code.
        category_info: The linked category, when the query loaded it.
    """

    id: str
    code: str
    name: str
    unit: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_finished_product: bool = False
    created_at: Optional[datetime] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    category_info: Optional[CategorySummary] = None

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
        id: The BOM row's ID.
        component_name: Display name of the component.
        notes: Optional notes about this BOM item.
        emission_factor_id: Linked emission factor, if any.
    """

    component_id: str
    quantity: float
    unit: Optional[str]
    id: Optional[str] = None
    component_name: str = "Unknown"
    notes: Optional[str] = None
    emission_factor_id: Optional[str] = None

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


@dataclass(frozen=True)
class ProductPage:
    """One page of products and the total matching count."""

    items: List[Product]
    total: int


@dataclass(frozen=True)
class ProductSearchCriteria:
    """Validated search filters and pagination."""

    query: Optional[str] = None
    category_id: Optional[str] = None
    industry: Optional[str] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_finished_product: Optional[bool] = None
    has_bom: Optional[bool] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class ScoredProduct:
    """A search result and its relevance, None when the search had no text."""

    product: Product
    relevance_score: Optional[float]


@dataclass(frozen=True)
class ProductSearchResult:
    """One page of search results and the total matching count."""

    items: List[ScoredProduct]
    total: int
