"""
Pydantic Schemas for Product Search and Categories API
TASK-API-P5-002: Enhanced Product Search - Implementation

Contains request/response models for:
- GET /api/v1/products/search
- GET /api/v1/products/categories
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re


# ============================================================================
# Industry Sector Enum
# ============================================================================

class IndustrySector(str, Enum):
    """Valid industry sectors for filtering."""
    ELECTRONICS = "electronics"
    APPAREL = "apparel"
    AUTOMOTIVE = "automotive"
    CONSTRUCTION = "construction"
    FOOD_BEVERAGE = "food_beverage"
    CHEMICALS = "chemicals"
    MACHINERY = "machinery"
    OTHER = "other"


# ============================================================================
# Category Schemas (for both search and categories endpoints)
# ============================================================================

class CategoryInfo(BaseModel):
    """Category information embedded in product search results."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    industry_sector: Optional[str] = None


class CategoryTreeNode(BaseModel):
    """Category node in hierarchical tree response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    level: int
    industry_sector: Optional[str] = None
    product_count: Optional[int] = None
    children: List["CategoryTreeNode"] = []


# Forward reference resolution for recursive model
CategoryTreeNode.model_rebuild()


# ============================================================================
# Product Search Schemas
# ============================================================================

class ProductSearchItem(BaseModel):
    """Single product item in search results."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: Optional[str] = None
    unit: str
    category: Optional[CategoryInfo] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_finished_product: bool
    relevance_score: Optional[float] = None
    created_at: str


class ProductSearchResponse(BaseModel):
    """Response model for product search endpoint."""
    items: List[ProductSearchItem]
    total: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# Product Categories Schemas
# ============================================================================

class ProductCategoriesResponse(BaseModel):
    """Response model for product categories endpoint."""
    categories: List[CategoryTreeNode]
    total_categories: int
    max_depth: int


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_country_code(value: Optional[str]) -> Optional[str]:
    """Validate ISO 3166-1 alpha-2 country code."""
    if value is None:
        return None
    if not re.match(r"^[A-Z]{2}$", value):
        raise ValueError("Country code must be ISO 3166-1 alpha-2 format (2 uppercase letters)")
    return value


def validate_query_length(value: Optional[str]) -> Optional[str]:
    """Validate search query length."""
    if value is None or value == "":
        return None
    if len(value) < 2:
        raise ValueError("Query must be at least 2 characters")
    if len(value) > 200:
        raise ValueError("Query must not exceed 200 characters")
    return value
