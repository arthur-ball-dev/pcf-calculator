"""
Product Search API Routes (split from products.py for ARCH-009).

Endpoints:
- GET /api/v1/products/search - Full-text search with multi-criteria filtering
"""

from typing import List, Optional, Tuple, Any, Dict
from dataclasses import dataclass
import re
import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload, Query as SQLAQuery
from sqlalchemy import or_, func, exists, select, not_

from backend.database.connection import get_db
from backend.models import Product, BillOfMaterials, ProductCategory
from backend.models.user import User
from backend.auth.dependencies import get_optional_user
from backend.api.utils.error_responses import create_error_response
from backend.schemas.products import (
    IndustrySector,
    CategoryInfo,
    ProductSearchItem,
    ProductSearchResponse,
)
from backend.utils.cache import (
    get_cached_response_sync,
    cache_response_sync,
    get_product_search_cache_key,
    PRODUCT_SEARCH_TTL,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["products"])


# ============================================================================
# Search Helper Data Structures
# ============================================================================

@dataclass
class ValidatedParams:
    """Validated and normalized search parameters."""
    query: Optional[str]
    category_id: Optional[str]
    industry: Optional[str]
    manufacturer: Optional[str]
    country_of_origin: Optional[str]
    is_finished_product: Optional[bool]
    has_bom: Optional[bool]
    limit: int
    offset: int
    error: Optional[Dict[str, Any]]


# ============================================================================
# Search Helper Functions
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
    """Validate and normalize search parameters."""
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
    """Build SQLAlchemy query with filters from validated parameters."""
    base_query = db.query(Product).options(
        joinedload(Product.product_category)
    )

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

    if params.category_id is not None:
        base_query = base_query.filter(Product.category_id == params.category_id)

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

    if params.manufacturer is not None:
        manufacturer_pattern = f"%{params.manufacturer}%"
        base_query = base_query.filter(
            func.lower(Product.manufacturer).like(func.lower(manufacturer_pattern))
        )

    if params.country_of_origin is not None:
        base_query = base_query.filter(Product.country_of_origin == params.country_of_origin)

    if params.is_finished_product is not None:
        base_query = base_query.filter(Product.is_finished_product == params.is_finished_product)

    has_bom_subquery = exists(
        select(BillOfMaterials.id).where(
            BillOfMaterials.parent_product_id == Product.id
        )
    )
    if params.has_bom is True:
        base_query = base_query.filter(has_bom_subquery)
    elif params.has_bom is False:
        base_query = base_query.filter(not_(has_bom_subquery))

    base_query = base_query.order_by(Product.name)
    return base_query


def _apply_relevance_scoring(
    products: List[Product],
    query: Optional[str]
) -> List[Tuple[Product, Optional[float]]]:
    """Apply relevance scoring to search results."""
    if not query:
        return [(p, None) for p in products]

    query_lower = query.lower()
    scored_products = []

    for p in products:
        score = 0.0
        if p.name and query_lower in p.name.lower():
            score += 0.5
            if p.name.lower().startswith(query_lower):
                score += 0.3
        if p.description and query_lower in p.description.lower():
            score += 0.1
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
    """Format search results into response dict (cacheable)."""
    items = []
    for p, relevance_score in scored_products:
        category_info = None
        if p.product_category:
            category_info = {
                "id": p.product_category.id,
                "code": p.product_category.code,
                "name": p.product_category.name,
                "industry_sector": p.product_category.industry_sector
            }
        elif p.category:
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
# ============================================================================

@router.get(
    "/products/search",
    response_model=ProductSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search products",
    description="Full-text search for products with multi-criteria filtering"
)
def search_products(
    q: Optional[str] = Query(None, description="Full-text search query (min 2 chars, max 200). Shorthand alias."),
    query: Optional[str] = Query(None, description="Full-text search query (min 2 chars, max 200). Alternative to 'q'."),
    category_id: Optional[str] = Query(None, description="Filter by product category ID"),
    industry: Optional[str] = Query(None, description="Filter by industry sector"),
    manufacturer: Optional[str] = Query(None, max_length=255, description="Filter by manufacturer name (partial match)"),
    country_of_origin: Optional[str] = Query(None, description="Filter by ISO 3166-1 alpha-2 country code"),
    is_finished_product: Optional[bool] = Query(None, description="Filter for finished products only"),
    has_bom: Optional[bool] = Query(None, description="Filter products with bill of materials entries"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Search products with full-text search and multi-criteria filtering."""
    search_query = q if q is not None else query

    validated = _validate_search_params(
        query=search_query, category_id=category_id, industry=industry,
        manufacturer=manufacturer, country_of_origin=country_of_origin,
        is_finished_product=is_finished_product, has_bom=has_bom,
        limit=limit, offset=offset, db=db
    )

    if validated.error:
        return create_error_response(
            status_code=validated.error["status_code"],
            code=validated.error["code"],
            message=validated.error["message"],
            details=validated.error["details"]
        )

    cache_key = get_product_search_cache_key(
        query=validated.query, category_id=validated.category_id,
        industry=validated.industry, manufacturer=validated.manufacturer,
        country_of_origin=validated.country_of_origin,
        is_finished_product=validated.is_finished_product,
        has_bom=validated.has_bom, limit=validated.limit, offset=validated.offset
    )

    cached_response = get_cached_response_sync(cache_key)
    if cached_response is not None:
        logger.debug(f"Cache hit for product search: {cache_key}")
        return ProductSearchResponse(**cached_response)

    logger.debug(f"Cache miss for product search: {cache_key}")
    db_query = _build_search_query(db, validated)
    total = db_query.count()
    products = db_query.offset(validated.offset).limit(validated.limit).all()
    scored = _apply_relevance_scoring(products, validated.query)
    response_dict = _format_search_results(scored, total, validated)
    cache_response_sync(cache_key, response_dict, PRODUCT_SEARCH_TTL)

    return ProductSearchResponse(**response_dict)
