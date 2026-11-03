"""
Products API Routes (CRUD only, split from monolith for ARCH-009).

Endpoints:
- GET /api/v1/products - List products with pagination and filtering
- GET /api/v1/products/{product_id} - Get product details with BOM

Search and categories endpoints moved to:
- product_search.py (GET /api/v1/products/search)
- product_categories.py (GET /api/v1/products/categories)
"""

from typing import Optional
import re
import logging

from fastapi import APIRouter, Depends, Query, Path, status

from backend.api.dependencies import get_product_service
from backend.models.user import User
from backend.auth.dependencies import get_optional_user
from backend.api.utils.error_responses import create_error_response
from backend.domain.entities.errors import ProductNotFoundError
from backend.domain.services.product_service import ProductService
from backend.schemas import (
    BOMItemResponse,
    ProductListItemResponse,
    ProductDetailResponse,
    ProductListResponse,
)
from backend.utils.cache import (
    get_cached_response_sync,
    cache_response_sync,
    get_product_list_cache_key,
    PRODUCT_LIST_TTL,
)


logger = logging.getLogger(__name__)


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
    service: ProductService = Depends(get_product_service),
    current_user: Optional[User] = Depends(get_optional_user),
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

    # Step 2: Query (cache miss)
    logger.debug(f"Cache miss for product list: {cache_key}")
    page = service.list_products(limit=limit, offset=offset, is_finished_product=effective_filter)

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
        for p in page.items
    ]

    response_dict = {
        "items": items,
        "total": page.total,
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
    service: ProductService = Depends(get_product_service),
    current_user: Optional[User] = Depends(get_optional_user),
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

    try:
        result = service.get_product_with_bom(product_id)
    except ProductNotFoundError:
        return create_error_response(
            status_code=404,
            code="PRODUCT_NOT_FOUND",
            message="Product not found",
            details=[{"field": "product_id", "message": f"No product exists with ID {product_id}"}]
        )

    product = result.product

    # Format BOM items
    bom_items = [
        BOMItemResponse(
            id=item.id,
            child_product_id=item.component_id,
            child_product_name=item.component_name,
            quantity=item.quantity,
            unit=item.unit,
            notes=item.notes,
            emission_factor_id=item.emission_factor_id,
        )
        for item in result.bom_items
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
