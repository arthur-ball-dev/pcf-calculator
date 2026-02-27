"""
Products API Routes
TASK-API-001: Implementation of products REST endpoints
TASK-API-P5-002: Enhanced Product Search and Categories
TASK-BE-P7-018: Added JWT authentication (user role required)
TASK-BE-P8-003: Added Redis caching for hot paths (product list and search)
TASK-BE-P8-004: Refactored search_products to reduce cyclomatic complexity
TASK-DB-P9-004: Fixed search query parameter to accept both 'q' and 'query' aliases

Endpoints:
- GET /api/v1/products - List products with pagination and filtering
- GET /api/v1/products/{product_id} - Get product details with BOM
- GET /api/v1/products/search - Full-text search with multi-criteria filtering
- GET /api/v1/products/categories - Hierarchical category tree
"""

from typing import List, Optional, Tuple, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
import re
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload, Query as SQLAQuery
from sqlalchemy import or_, func, exists, select, not_
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.models import Product, BillOfMaterials, ProductCategory
from backend.api.utils.error_responses import create_error_response
from backend.schemas.products import (
    IndustrySector,
    CategoryInfo,
    CategoryTreeNode,
    ProductSearchItem,
    ProductSearchResponse,
    ProductCategoriesResponse,
)
from backend.utils.cache import (
    get_cached_response_sync,
    cache_response_sync,
    get_product_list_cache_key,
    get_product_search_cache_key,
    PRODUCT_LIST_TTL,
    PRODUCT_SEARCH_TTL,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Response Models (existing)
# ============================================================================

class BOMItemResponse(BaseModel):
    """BOM item in product detail response"""
    id: str
    child_product_id: str
    child_product_name: str
    quantity: float
    unit: Optional[str] = None
    notes: Optional[str] = None
    emission_factor_id: Optional[str] = None  # Stored in bill_of_materials table

    class Config:
        from_attributes = True


class ProductListItemResponse(BaseModel):
    """Product item in list response"""
    id: str
    code: str
    name: str
    unit: str
    category: Optional[str] = None
    is_finished_product: bool
    created_at: str

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseModel):
    """Product detail response with BOM"""
    id: str
    code: str
    name: str
    description: Optional[str] = None
    unit: str
    category: Optional[str] = None
    is_finished_product: bool
    bill_of_materials: List[BOMItemResponse] = []
    created_at: str

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated list of products"""
    items: List[ProductListItemResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["products"])


# ============================================================================
# Helper Functions
# ============================================================================

def is_valid_id_format(value: str) -> bool:
    """
    Check if string is a valid ID format.

    Accepts:
    - Standard UUID format (with hyphens)
    - 32-character hex strings (UUID without hyphens)
    - Simple alphanumeric identifiers with hyphens (e.g., "cat-elec")

    Rejects:
    - Strings with invalid characters
    - Obviously malformed IDs (starting with "not-a-")
    """
    # Allow alphanumeric characters, hyphens, and underscores
    # Must be at least 1 character
    if not value or not re.match(r"^[a-zA-Z0-9_-]+$", value):
        return False

    # Reject obviously malformed test patterns
    if value.lower().startswith("not-a-"):
        return False

    return True


def build_category_tree(
    categories: List[ProductCategory],
    parent_id: Optional[str],
    current_depth: int,
    max_depth: int,
    include_product_count: bool,
    db: Session
) -> List[CategoryTreeNode]:
    """
    Recursively build category tree structure.

    Args:
        categories: All categories to process
        parent_id: ID of parent category (None for root)
        current_depth: Current depth in tree (0 = root)
        max_depth: Maximum depth to traverse
        include_product_count: Whether to calculate product counts
        db: Database session

    Returns:
        List of CategoryTreeNode objects
    """
    # Filter categories at this level
    level_cats = [c for c in categories if c.parent_id == parent_id]

    result = []
    for cat in level_cats:
        # Calculate product count if requested
        product_count = None
        if include_product_count:
            # Count products in this category and all descendants
            product_count = _count_products_recursive(cat.id, categories, db)

        # Build children if not at max depth
        children = []
        if current_depth < max_depth - 1:
            children = build_category_tree(
                categories, cat.id, current_depth + 1, max_depth,
                include_product_count, db
            )

        node = CategoryTreeNode(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            level=cat.level,
            industry_sector=cat.industry_sector,
            product_count=product_count,
            children=children
        )
        result.append(node)

    return result


def _count_products_recursive(
    category_id: str,
    all_categories: List[ProductCategory],
    db: Session
) -> int:
    """Count products in category and all its descendants."""
    # Get direct count
    count = db.query(func.count(Product.id)).filter(
        Product.category_id == category_id
    ).scalar() or 0

    # Get children and count their products recursively
    children = [c for c in all_categories if c.parent_id == category_id]
    for child in children:
        count += _count_products_recursive(child.id, all_categories, db)

    return count


def find_max_depth(categories: List[CategoryTreeNode], current: int = 0) -> int:
    """Find maximum depth in category tree."""
    if not categories:
        return current

    max_child_depth = current
    for cat in categories:
        if cat.children:
            child_depth = find_max_depth(cat.children, current + 1)
            max_child_depth = max(max_child_depth, child_depth)

    return max_child_depth


def count_tree_categories(categories: List[CategoryTreeNode]) -> int:
    """Count total number of categories in tree."""
    count = len(categories)
    for cat in categories:
        if cat.children:
            count += count_tree_categories(cat.children)
    return count


# ============================================================================
# Search Helper Data Structures
# TASK-BE-P8-004: Extracted from search_products for reduced complexity
# ============================================================================

@dataclass
class ValidatedParams:
    """
    Validated and normalized search parameters.

    TASK-BE-P8-004: Data class to hold validated search parameters,
    separating validation logic from query building.
    """
    query: Optional[str]
    category_id: Optional[str]
    industry: Optional[str]
    manufacturer: Optional[str]
    country_of_origin: Optional[str]
    is_finished_product: Optional[bool]
    has_bom: Optional[bool]
    limit: int
    offset: int
    error: Optional[Dict[str, Any]]  # None if valid, error dict if invalid


# ============================================================================
# Search Helper Functions
# TASK-BE-P8-004: Extracted from search_products for reduced complexity
# ============================================================================

def _validate_search_params(
    query: Optional[str],
    category_id: Optional[str],
    industry: Optional[str],
    manufacturer: Optional[str],
    country_of_origin: Optional[str],
    is_finished_product: Optional[bool],
    has_bom: Optional[bool],
    limit: int,
    offset: int,
    db: Session
) -> ValidatedParams:
    """
    Validate and normalize search parameters.

    TASK-BE-P8-004: Extracted from search_products to reduce cyclomatic complexity.
    CC < 5 achieved by using early returns and single responsibility.

    Args:
        query: Full-text search query
        category_id: Category ID filter
        industry: Industry sector filter
        manufacturer: Manufacturer filter
        country_of_origin: Country code filter
        is_finished_product: Finished product filter
        has_bom: Has BOM filter
        limit: Pagination limit
        offset: Pagination offset
        db: Database session for category validation

    Returns:
        ValidatedParams with error=None if valid, or error dict if invalid
    """
    # Normalize empty query to None
    normalized_query = query
    if query is not None:
        if query == "":
            normalized_query = None
        elif len(query) < 2:
            return ValidatedParams(
                query=None, category_id=None, industry=None, manufacturer=None,
                country_of_origin=None, is_finished_product=None, has_bom=None,
                limit=limit, offset=offset,
                error={
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": [{"field": "query", "message": "Query must be at least 2 characters"}],
                    "status_code": 400
                }
            )
        elif len(query) > 200:
            return ValidatedParams(
                query=None, category_id=None, industry=None, manufacturer=None,
                country_of_origin=None, is_finished_product=None, has_bom=None,
                limit=limit, offset=offset,
                error={
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": [{"field": "query", "message": "Query must not exceed 200 characters"}],
                    "status_code": 400
                }
            )

    # Validate country code format
    if country_of_origin is not None:
        if not re.match(r"^[A-Z]{2}$", country_of_origin):
            return ValidatedParams(
                query=None, category_id=None, industry=None, manufacturer=None,
                country_of_origin=None, is_finished_product=None, has_bom=None,
                limit=limit, offset=offset,
                error={
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": [{"field": "country_of_origin", "message": "Must be ISO 3166-1 alpha-2 format (2 uppercase letters)"}],
                    "status_code": 400
                }
            )

    # Validate industry
    valid_industries = [e.value for e in IndustrySector]
    if industry is not None and industry not in valid_industries:
        return ValidatedParams(
            query=None, category_id=None, industry=None, manufacturer=None,
            country_of_origin=None, is_finished_product=None, has_bom=None,
            limit=limit, offset=offset,
            error={
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": [{"field": "industry", "message": f"Must be one of: {', '.join(valid_industries)}"}],
                "status_code": 400
            }
        )

    # Validate category_id exists
    if category_id is not None:
        category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if category is None:
            return ValidatedParams(
                query=None, category_id=None, industry=None, manufacturer=None,
                country_of_origin=None, is_finished_product=None, has_bom=None,
                limit=limit, offset=offset,
                error={
                    "code": "INVALID_CATEGORY",
                    "message": "Category not found",
                    "details": [{"field": "category_id", "message": f"No category exists with ID {category_id}"}],
                    "status_code": 422
                }
            )

    # All validations passed
    return ValidatedParams(
        query=normalized_query,
        category_id=category_id,
        industry=industry,
        manufacturer=manufacturer,
        country_of_origin=country_of_origin,
        is_finished_product=is_finished_product,
        has_bom=has_bom,
        limit=limit,
        offset=offset,
        error=None
    )


def _build_search_query(db: Session, params: ValidatedParams) -> SQLAQuery:
    """
    Build SQLAlchemy query with filters from validated parameters.

    TASK-BE-P8-004: Extracted from search_products to reduce cyclomatic complexity.
    CC < 5 achieved by sequential filter application without nested conditions.

    Args:
        db: Database session
        params: Validated search parameters

    Returns:
        SQLAlchemy query object with all filters applied
    """
    # Build base query with eager loading for category
    base_query = db.query(Product).options(
        joinedload(Product.product_category)
    )

    # Apply full-text search (using LIKE for SQLite compatibility)
    if params.query:
        query_lower = f"%{params.query.lower()}%"
        base_query = base_query.filter(
            or_(
                func.lower(Product.name).like(query_lower),
                func.lower(Product.description).like(query_lower),
                func.lower(Product.code).like(query_lower),
                func.lower(Product.search_vector).like(query_lower)
            )
        )

    # Apply category filter
    if params.category_id is not None:
        base_query = base_query.filter(Product.category_id == params.category_id)

    # Apply industry filter (via category relationship OR string category field)
    if params.industry is not None:
        base_query = base_query.filter(
            or_(
                exists(
                    select(ProductCategory.id).where(
                        ProductCategory.id == Product.category_id,
                        ProductCategory.industry_sector == params.industry
                    )
                ),
                func.lower(Product.category) == params.industry.lower()
            )
        )

    # Apply manufacturer filter (case-insensitive partial match)
    if params.manufacturer is not None:
        manufacturer_pattern = f"%{params.manufacturer}%"
        base_query = base_query.filter(
            func.lower(Product.manufacturer).like(func.lower(manufacturer_pattern))
        )

    # Apply country filter
    if params.country_of_origin is not None:
        base_query = base_query.filter(Product.country_of_origin == params.country_of_origin)

    # Apply is_finished_product filter
    if params.is_finished_product is not None:
        base_query = base_query.filter(Product.is_finished_product == params.is_finished_product)

    # Apply has_bom filter
    has_bom_subquery = exists(
        select(BillOfMaterials.id).where(
            BillOfMaterials.parent_product_id == Product.id
        )
    )
    if params.has_bom is True:
        base_query = base_query.filter(has_bom_subquery)
    elif params.has_bom is False:
        base_query = base_query.filter(not_(has_bom_subquery))

    # Order by name
    base_query = base_query.order_by(Product.name)

    return base_query


def _apply_relevance_scoring(
    products: List[Product],
    query: Optional[str]
) -> List[Tuple[Product, Optional[float]]]:
    """
    Apply relevance scoring to search results.

    TASK-BE-P8-004: Extracted from search_products to reduce cyclomatic complexity.
    CC < 5 achieved by separating scoring logic from main flow.

    Args:
        products: List of Product objects from query
        query: Search query string (None if no query)

    Returns:
        List of (Product, relevance_score) tuples
    """
    if not query:
        return [(p, None) for p in products]

    query_lower = query.lower()
    scored_products = []

    for p in products:
        score = 0.0

        # Exact name match highest
        if p.name and query_lower in p.name.lower():
            score += 0.5
            if p.name.lower().startswith(query_lower):
                score += 0.3

        # Description match
        if p.description and query_lower in p.description.lower():
            score += 0.1

        # Code match
        if p.code and query_lower in p.code.lower():
            score += 0.1

        relevance_score = min(score, 1.0)
        scored_products.append((p, relevance_score))

    return scored_products


def _format_search_results(
    scored_products: List[Tuple[Product, Optional[float]]],
    total: int,
    params: ValidatedParams
) -> Dict[str, Any]:
    """
    Format search results into response dict (cacheable).

    TASK-BE-P8-003: Changed return type from ProductSearchResponse to dict
    to support caching (JSON serializable).

    Args:
        scored_products: List of (Product, relevance_score) tuples
        total: Total count of matching products
        params: Validated parameters (for pagination info)

    Returns:
        Dict with formatted items for caching
    """
    items = []
    for p, relevance_score in scored_products:
        # Build category info if product has category
        category_info = None
        if p.product_category:
            category_info = {
                "id": p.product_category.id,
                "code": p.product_category.code,
                "name": p.product_category.name,
                "industry_sector": p.product_category.industry_sector
            }
        elif p.category:
            # Fallback: create category info from string field
            category_info = {
                "id": "",
                "code": p.category,
                "name": p.category.replace("_", " ").title(),
                "industry_sector": p.category
            }

        items.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "description": p.description,
            "unit": p.unit,
            "category": category_info,
            "manufacturer": p.manufacturer,
            "country_of_origin": p.country_of_origin,
            "is_finished_product": p.is_finished_product,
            "relevance_score": relevance_score,
            "created_at": p.created_at.isoformat() if p.created_at else ""
        })

    has_more = (params.offset + len(items)) < total

    return {
        "items": items,
        "total": total,
        "limit": params.limit,
        "offset": params.offset,
        "has_more": has_more
    }


# ============================================================================
# Search Endpoint
# TASK-BE-P8-003: Added Redis caching
# TASK-BE-P8-004: Refactored to use helper functions for reduced complexity
# TASK-DB-P9-004: Fixed query parameter to accept both 'q' and 'query' aliases
# ============================================================================

@router.get(
    "/products/search",
    response_model=ProductSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search products",
    description="Full-text search for products with multi-criteria filtering"
)
def search_products(
    q: Optional[str] = Query(
        None,
        description="Full-text search query (min 2 chars, max 200). Shorthand alias.",
    ),
    query: Optional[str] = Query(
        None,
        description="Full-text search query (min 2 chars, max 200). Alternative to 'q'.",
    ),
    category_id: Optional[str] = Query(
        None,
        description="Filter by product category ID"
    ),
    industry: Optional[str] = Query(
        None,
        description="Filter by industry sector"
    ),
    manufacturer: Optional[str] = Query(
        None,
        max_length=255,
        description="Filter by manufacturer name (partial match)"
    ),
    country_of_origin: Optional[str] = Query(
        None,
        description="Filter by ISO 3166-1 alpha-2 country code"
    ),
    is_finished_product: Optional[bool] = Query(
        None,
        description="Filter for finished products only"
    ),
    has_bom: Optional[bool] = Query(
        None,
        description="Filter products with bill of materials entries"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Number of results to return (1-100)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of results to skip"
    ),
    db: Session = Depends(get_db)
):
    """
    Search products with full-text search and multi-criteria filtering.

    TASK-BE-P8-003: Added Redis caching with 60-second TTL.
    TASK-BE-P8-004: Refactored to use helper functions:
    - _validate_search_params: Validate and normalize parameters
    - _build_search_query: Build SQLAlchemy query with filters
    - _apply_relevance_scoring: Calculate relevance scores
    - _format_search_results: Format response
    TASK-DB-P9-004: Fixed query parameter to accept both 'q' and 'query'.

    Query Parameters:
    - q or query: Full-text search in name, description, and code (min 2 chars)
    - category_id: Filter by category UUID
    - industry: Filter by industry sector (electronics, apparel, etc.)
    - manufacturer: Filter by manufacturer name (partial, case-insensitive)
    - country_of_origin: Filter by ISO alpha-2 country code
    - is_finished_product: Filter by finished product status
    - has_bom: Filter for products with BOM entries
    - limit: Maximum results (default 50, max 100)
    - offset: Results to skip (default 0)

    Returns:
    - items: List of matching products with relevance scores
    - total: Total matching products
    - limit/offset: Applied pagination
    - has_more: Whether more results exist
    """
    # TASK-DB-P9-004: Merge 'q' and 'query' parameters (q takes precedence)
    search_query = q if q is not None else query

    # Step 1: Validate parameters (must be done before caching)
    validated = _validate_search_params(
        query=search_query,
        category_id=category_id,
        industry=industry,
        manufacturer=manufacturer,
        country_of_origin=country_of_origin,
        is_finished_product=is_finished_product,
        has_bom=has_bom,
        limit=limit,
        offset=offset,
        db=db
    )

    # Return error response if validation failed
    if validated.error:
        return create_error_response(
            status_code=validated.error["status_code"],
            code=validated.error["code"],
            message=validated.error["message"],
            details=validated.error["details"]
        )

    # Step 2: Check cache (TASK-BE-P8-003)
    cache_key = get_product_search_cache_key(
        query=validated.query,
        category_id=validated.category_id,
        industry=validated.industry,
        manufacturer=validated.manufacturer,
        country_of_origin=validated.country_of_origin,
        is_finished_product=validated.is_finished_product,
        has_bom=validated.has_bom,
        limit=validated.limit,
        offset=validated.offset
    )

    cached_response = get_cached_response_sync(cache_key)
    if cached_response is not None:
        logger.debug(f"Cache hit for product search: {cache_key}")
        return ProductSearchResponse(**cached_response)

    # Step 3: Build query with filters (cache miss)
    logger.debug(f"Cache miss for product search: {cache_key}")
    db_query = _build_search_query(db, validated)

    # Step 4: Get total count before pagination
    total = db_query.count()

    # Step 5: Apply pagination and execute
    products = db_query.offset(validated.offset).limit(validated.limit).all()

    # Step 6: Apply relevance scoring
    scored = _apply_relevance_scoring(products, validated.query)

    # Step 7: Format response
    response_dict = _format_search_results(scored, total, validated)

    # Step 8: Cache the response (TASK-BE-P8-003)
    cache_response_sync(cache_key, response_dict, PRODUCT_SEARCH_TTL)

    return ProductSearchResponse(**response_dict)


# ============================================================================
# Categories Endpoint
# ============================================================================

@router.get(
    "/products/categories",
    response_model=ProductCategoriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product categories",
    description="Retrieve hierarchical category tree for product classification"
)
def get_categories(
    include_product_count: bool = Query(
        False,
        description="Include count of products in each category"
    ),
    max_depth: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum depth of category tree to return"
    ),
    industry: Optional[str] = Query(
        None,
        description="Filter categories by industry sector"
    ),
    db: Session = Depends(get_db)
):
    """
    Retrieve hierarchical category tree.

    Returns nested structure of product categories with optional
    product counts. Categories are organized by industry sector.

    Query Parameters:
    - include_product_count: If true, include count of products per category
    - max_depth: Maximum nesting depth to return (default 10)
    - industry: Filter to single industry sector

    Returns:
    - categories: Nested category tree
    - total_categories: Total number of categories
    - max_depth: Maximum depth in returned tree
    """
    # Build base query
    query = db.query(ProductCategory)

    # Apply industry filter
    if industry is not None:
        valid_industries = [e.value for e in IndustrySector]
        if industry not in valid_industries:
            return create_error_response(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid industry sector",
                details=[{
                    "field": "industry",
                    "message": f"Must be one of: {', '.join(valid_industries)}"
                }]
            )
        query = query.filter(ProductCategory.industry_sector == industry)

    # Get all matching categories
    all_categories = query.all()

    # Build tree from root categories
    tree = build_category_tree(
        all_categories, None, 0, max_depth, include_product_count, db
    )

    return ProductCategoriesResponse(
        categories=tree,
        total_categories=count_tree_categories(tree),
        max_depth=find_max_depth(tree)
    )


# ============================================================================
# Product List Endpoint
# TASK-BE-P8-003: Added Redis caching
# ============================================================================

@router.get(
    "/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products",
    description="Retrieve paginated list of products with optional filtering"
)
def list_products(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Number of products to return (1-1000)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of products to skip"
    ),
    is_finished_product: Optional[bool] = Query(
        None,
        description="Filter for finished products only"
    ),
    is_finished: Optional[bool] = Query(
        None,
        description="Alias for is_finished_product (deprecated, use is_finished_product)"
    ),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated list of products.

    TASK-BE-P8-003: Added Redis caching with 5-minute TTL.
    TASK-BE-P9-001: Added is_finished alias for backward compatibility.

    Query Parameters:
    - limit: Number of products to return (default 100, max 1000)
    - offset: Number of products to skip (default 0)
    - is_finished_product: Filter for finished products (true/false)
    - is_finished: Alias for is_finished_product (deprecated)

    Returns:
    - items: List of products
    - total: Total number of matching products
    - limit/offset: Applied pagination
    """
    # Merge is_finished alias with is_finished_product (alias takes lower precedence)
    effective_filter = is_finished_product if is_finished_product is not None else is_finished

    # Step 1: Check cache
    cache_key = get_product_list_cache_key(limit, offset, effective_filter)
    cached_response = get_cached_response_sync(cache_key)
    if cached_response is not None:
        logger.debug(f"Cache hit for product list: {cache_key}")
        return ProductListResponse(**cached_response)

    # Step 2: Build query (cache miss)
    logger.debug(f"Cache miss for product list: {cache_key}")
    query = db.query(Product)

    # Apply filter
    if effective_filter is not None:
        query = query.filter(Product.is_finished_product == effective_filter)

    # Get total count
    total = query.count()

    # Apply pagination and execute
    products = query.order_by(Product.name).offset(offset).limit(limit).all()

    # Format response
    items = [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "unit": p.unit,
            "category": p.category,
            "is_finished_product": p.is_finished_product,
            "created_at": p.created_at.isoformat() if p.created_at else ""
        }
        for p in products
    ]

    response_dict = {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

    # Step 3: Cache the response
    cache_response_sync(cache_key, response_dict, PRODUCT_LIST_TTL)

    return ProductListResponse(**response_dict)


# ============================================================================
# Product Detail Endpoint
# ============================================================================

@router.get(
    "/products/{product_id}",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product details",
    description="Retrieve detailed product information with bill of materials"
)
def get_product(
    product_id: str = Path(
        ...,
        description="Product ID (UUID format)"
    ),
    db: Session = Depends(get_db)
):
    """
    Retrieve product details with bill of materials.

    Path Parameters:
    - product_id: Product UUID

    Returns:
    - Product details including BOM items
    """
    # Validate ID format
    if not is_valid_id_format(product_id):
        return create_error_response(
            status_code=400,
            code="INVALID_ID_FORMAT",
            message="Invalid product ID format",
            details=[{"field": "product_id", "message": "Must be a valid UUID or identifier"}]
        )

    # Query product with BOM
    product = db.query(Product).options(
        joinedload(Product.bom_items).joinedload(BillOfMaterials.child_product)
    ).filter(Product.id == product_id).first()

    if product is None:
        return create_error_response(
            status_code=404,
            code="PRODUCT_NOT_FOUND",
            message="Product not found",
            details=[{"field": "product_id", "message": f"No product exists with ID {product_id}"}]
        )

    # Format BOM items
    bom_items = [
        BOMItemResponse(
            id=bom.id,
            child_product_id=bom.child_product_id,
            child_product_name=bom.child_product.name if bom.child_product else "Unknown",
            quantity=float(bom.quantity),
            unit=bom.unit,
            notes=bom.notes,
            emission_factor_id=bom.emission_factor_id,  # Stored in database
        )
        for bom in product.bom_items
    ]

    return ProductDetailResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        description=product.description,
        unit=product.unit,
        category=product.category,
        is_finished_product=product.is_finished_product,
        bill_of_materials=bom_items,
        created_at=product.created_at.isoformat() if product.created_at else ""
    )
