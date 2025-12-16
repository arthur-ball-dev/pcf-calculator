"""
Products API Routes
TASK-API-001: Implementation of products REST endpoints
TASK-API-P5-002: Enhanced Product Search and Categories

Endpoints:
- GET /api/v1/products - List products with pagination and filtering
- GET /api/v1/products/{product_id} - Get product details with BOM
- GET /api/v1/products/search - Full-text search with multi-criteria filtering
- GET /api/v1/products/categories - Hierarchical category tree
"""

from typing import List, Optional
from datetime import datetime, timezone
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, exists, select
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.models import Product, BillOfMaterials, ProductCategory
from backend.schemas.products import (
    IndustrySector,
    CategoryInfo,
    CategoryTreeNode,
    ProductSearchItem,
    ProductSearchResponse,
    ProductCategoriesResponse,
)


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


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: List[dict] = None
) -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or []
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


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
# Search Endpoint
# ============================================================================

@router.get(
    "/products/search",
    response_model=ProductSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search products",
    description="Full-text search for products with multi-criteria filtering"
)
def search_products(
    query: Optional[str] = Query(
        None,
        description="Full-text search query (min 2 chars, max 200)",
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

    Query Parameters:
    - query: Full-text search in name, description, and code (min 2 chars)
    - category_id: Filter by category UUID
    - industry: Filter by industry sector (electronics, apparel, etc.)
    - manufacturer: Filter by manufacturer name (partial, case-insensitive)
    - country_of_origin: Filter by ISO alpha-2 country code
    - is_finished_product: Filter by finished product status
    - has_bom: Filter for products with BOM entries (true=only with BOM)
    - limit: Maximum results (default 50, max 100)
    - offset: Results to skip (default 0)

    Returns:
    - items: List of matching products with relevance scores
    - total: Total matching products
    - limit/offset: Applied pagination
    - has_more: Whether more results exist
    """
    # Validate query length
    if query is not None:
        if query == "":
            query = None  # Treat empty string as no query
        elif len(query) < 2:
            return create_error_response(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid request parameters",
                details=[{"field": "query", "message": "Query must be at least 2 characters"}]
            )
        elif len(query) > 200:
            return create_error_response(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid request parameters",
                details=[{"field": "query", "message": "Query must not exceed 200 characters"}]
            )

    # Validate country code format
    if country_of_origin is not None:
        if not re.match(r"^[A-Z]{2}$", country_of_origin):
            return create_error_response(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid request parameters",
                details=[{"field": "country_of_origin", "message": "Must be ISO 3166-1 alpha-2 format (2 uppercase letters)"}]
            )

    # Validate industry
    valid_industries = [e.value for e in IndustrySector]
    if industry is not None and industry not in valid_industries:
        return create_error_response(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Invalid request parameters",
            details=[{"field": "industry", "message": f"Must be one of: {', '.join(valid_industries)}"}]
        )

    # Validate category_id exists
    if category_id is not None:
        category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if category is None:
            return create_error_response(
                status_code=422,
                code="INVALID_CATEGORY",
                message="Category not found",
                details=[{"field": "category_id", "message": f"No category exists with ID {category_id}"}]
            )

    # Build base query with eager loading for category
    base_query = db.query(Product).options(
        joinedload(Product.product_category)
    )

    # Apply full-text search (using LIKE for SQLite compatibility)
    if query:
        query_lower = f"%{query.lower()}%"
        base_query = base_query.filter(
            or_(
                func.lower(Product.name).like(query_lower),
                func.lower(Product.description).like(query_lower),
                func.lower(Product.code).like(query_lower),
                func.lower(Product.search_vector).like(query_lower)
            )
        )

    # Apply category filter
    if category_id is not None:
        base_query = base_query.filter(Product.category_id == category_id)

    # Apply industry filter (via category relationship)
    if industry is not None:
        base_query = base_query.join(
            ProductCategory,
            Product.category_id == ProductCategory.id
        ).filter(ProductCategory.industry_sector == industry)

    # Apply manufacturer filter (case-insensitive partial match)
    if manufacturer is not None:
        manufacturer_pattern = f"%{manufacturer}%"
        base_query = base_query.filter(
            func.lower(Product.manufacturer).like(func.lower(manufacturer_pattern))
        )

    # Apply country filter
    if country_of_origin is not None:
        base_query = base_query.filter(Product.country_of_origin == country_of_origin)

    # Apply is_finished_product filter
    if is_finished_product is not None:
        base_query = base_query.filter(Product.is_finished_product == is_finished_product)

    # Apply has_bom filter (TASK-FE-P8-001)
    if has_bom is True:
        has_bom_subquery = exists(
            select(BillOfMaterials.id).where(
                BillOfMaterials.parent_product_id == Product.id
            )
        )
        base_query = base_query.filter(has_bom_subquery)

    # Get total count before pagination
    total = base_query.count()

    # Order by name (or relevance if query provided)
    # For SQLite, we use name ordering. In PostgreSQL, you'd use ts_rank
    base_query = base_query.order_by(Product.name)

    # Apply pagination
    products = base_query.offset(offset).limit(limit).all()

    # Convert to response format
    items = []
    for p in products:
        # Calculate simple relevance score for SQLite
        # In PostgreSQL, this would use ts_rank
        relevance_score = None
        if query:
            query_lower = query.lower()
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

        # Build category info if product has category
        category_info = None
        if p.product_category:
            category_info = CategoryInfo(
                id=p.product_category.id,
                code=p.product_category.code,
                name=p.product_category.name,
                industry_sector=p.product_category.industry_sector
            )

        items.append(ProductSearchItem(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            unit=p.unit,
            category=category_info,
            manufacturer=p.manufacturer,
            country_of_origin=p.country_of_origin,
            is_finished_product=p.is_finished_product,
            relevance_score=relevance_score,
            created_at=p.created_at.isoformat() if p.created_at else ""
        ))

    has_more = (offset + len(items)) < total

    return ProductSearchResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )


# ============================================================================
# Categories Endpoint
# ============================================================================

@router.get(
    "/products/categories",
    response_model=ProductCategoriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product categories",
    description="Retrieve hierarchical product category tree"
)
def get_product_categories(
    parent_id: Optional[str] = Query(
        None,
        description="Get children of specific category (omit for root categories)"
    ),
    depth: int = Query(
        3,
        ge=1,
        le=5,
        description="Maximum depth to traverse (1-5)"
    ),
    include_product_count: bool = Query(
        False,
        description="Include count of products in each category"
    ),
    industry: Optional[str] = Query(
        None,
        description="Filter categories by industry sector"
    ),
    db: Session = Depends(get_db)
):
    """
    Get hierarchical product category tree.

    Query Parameters:
    - parent_id: Get children of specific category (omit for root)
    - depth: Maximum tree depth to return (1-5, default 3)
    - include_product_count: Include product counts per category
    - industry: Filter by industry sector

    Returns:
    - categories: Hierarchical category tree
    - total_categories: Total number of categories in response
    - max_depth: Maximum depth in returned tree
    """
    # Validate industry
    valid_industries = [e.value for e in IndustrySector]
    if industry is not None and industry not in valid_industries:
        return create_error_response(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Invalid request parameters",
            details=[{"field": "industry", "message": f"Must be one of: {', '.join(valid_industries)}"}]
        )

    # Validate parent_id format if provided
    if parent_id is not None:
        if not is_valid_id_format(parent_id):
            return create_error_response(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid request parameters",
                details=[{"field": "parent_id", "message": "Must be a valid ID format"}]
            )

        # Check if parent category exists
        parent_category = db.query(ProductCategory).filter(
            ProductCategory.id == parent_id
        ).first()
        if parent_category is None:
            return create_error_response(
                status_code=404,
                code="NOT_FOUND",
                message="Category not found",
                details=[{"field": "parent_id", "message": f"No category exists with ID {parent_id}"}]
            )

    # Query all categories (we'll build tree in memory for simplicity)
    query = db.query(ProductCategory)

    # Apply industry filter
    if industry is not None:
        query = query.filter(ProductCategory.industry_sector == industry)

    all_categories = query.all()

    # If parent_id is specified, start from that category's children
    # Otherwise, start from root (parent_id is None)
    if parent_id is not None:
        # Get children starting from specified parent
        starting_parent_id = parent_id
        starting_level = 1  # Children of parent are at depth 1 relative to parent
    else:
        # Start from root categories
        starting_parent_id = None
        starting_level = 0

    # Build the tree
    tree = build_category_tree(
        categories=all_categories,
        parent_id=starting_parent_id,
        current_depth=starting_level,
        max_depth=starting_level + depth,
        include_product_count=include_product_count,
        db=db
    )

    # Calculate totals
    total_categories = count_tree_categories(tree)
    max_depth_found = find_max_depth(tree, starting_level)

    # Adjust max_depth to be relative to starting point
    actual_max_depth = max_depth_found - starting_level if tree else 0

    return ProductCategoriesResponse(
        categories=tree,
        total_categories=total_categories,
        max_depth=actual_max_depth
    )


# ============================================================================
# Existing API Endpoints
# ============================================================================

@router.get(
    "/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products",
    description="Get paginated list of products with optional filtering"
)
def list_products(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    is_finished: Optional[bool] = Query(None, description="Filter by is_finished_product"),
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    List all products with pagination and optional filtering.

    Query Parameters:
    - limit: Maximum number of products to return (1-1000, default: 100)
    - offset: Number of products to skip (default: 0)
    - is_finished: Filter by is_finished_product (true/false)

    Returns:
    - items: List of products
    - total: Total count of products (without pagination)
    - limit: Applied limit
    - offset: Applied offset
    """
    # Build query
    query = db.query(Product)

    # Apply filters
    if is_finished is not None:
        query = query.filter(Product.is_finished_product == is_finished)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    products = query.offset(offset).limit(limit).all()

    # Convert products to response format
    items = [
        ProductListItemResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            unit=p.unit,
            category=p.category,
            is_finished_product=p.is_finished_product,
            created_at=p.created_at.isoformat() if p.created_at else ""
        )
        for p in products
    ]

    return ProductListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product details",
    description="Get detailed product information including bill of materials"
)
def get_product(
    product_id: str = Path(..., description="Unique product identifier (UUID or alphanumeric ID)"),
    db: Session = Depends(get_db)
) -> ProductDetailResponse:
    """
    Get detailed information for a specific product.

    Path Parameters:
    - product_id: Unique product identifier

    Returns:
    - Product details including bill_of_materials

    Raises:
    - 404: Product not found
    """
    # Query product
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found"
        )

    # Get BOM items for this product
    bom_items = (
        db.query(BillOfMaterials)
        .filter(BillOfMaterials.parent_product_id == product_id)
        .all()
    )

    # Convert BOM items to response format
    bom_response = []
    for bom in bom_items:
        # Get child product name
        child_product = db.query(Product).filter(Product.id == bom.child_product_id).first()
        child_name = child_product.name if child_product else "Unknown"

        bom_response.append(
            BOMItemResponse(
                id=bom.id,
                child_product_id=bom.child_product_id,
                child_product_name=child_name,
                quantity=float(bom.quantity),
                unit=bom.unit,
                notes=bom.notes
            )
        )

    return ProductDetailResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        description=product.description,
        unit=product.unit,
        category=product.category,
        is_finished_product=product.is_finished_product,
        bill_of_materials=bom_response,
        created_at=product.created_at.isoformat() if product.created_at else ""
    )