"""
Product Categories API Routes (split from products.py for ARCH-009).

Endpoints:
- GET /api/v1/products/categories - Hierarchical category tree
"""

from typing import Optional
import logging

from fastapi import APIRouter, Depends, Query, status

from backend.api.dependencies import get_category_service
from backend.models.user import User
from backend.auth.dependencies import get_optional_user
from backend.api.utils.error_responses import create_error_response
from backend.domain.entities.category import CategoryNode
from backend.domain.entities.errors import CategoryNotFoundError
from backend.domain.services.category_service import CategoryService
from backend.schemas.products import (
    IndustrySector,
    CategoryTreeNode,
    ProductCategoriesResponse,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["products"])


# ============================================================================
# Helper Functions
# ============================================================================

def _to_response_node(node: CategoryNode) -> CategoryTreeNode:
    """Convert a domain tree node, with its children, to the response schema."""
    return CategoryTreeNode(
        id=node.id,
        code=node.code,
        name=node.name,
        level=node.level,
        industry_sector=node.industry_sector,
        product_count=node.product_count,
        children=[_to_response_node(child) for child in node.children],
    )


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
    include_product_count: bool = Query(False, description="Include count of products in each category"),
    max_depth: int = Query(10, ge=1, le=100, description="Maximum depth of category tree to return"),
    depth: Optional[int] = Query(
        None, ge=1, le=5,
        description="Depth of the tree to return (1-5). Takes precedence over max_depth.",
    ),
    parent_id: Optional[str] = Query(None, description="Return only the subtree under this category"),
    industry: Optional[str] = Query(None, description="Filter categories by industry sector"),
    service: CategoryService = Depends(get_category_service),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Retrieve hierarchical category tree, optionally rooted at parent_id."""
    effective_depth = depth if depth is not None else max_depth

    root_parent_id: Optional[str] = None
    if parent_id is not None:
        try:
            root_parent_id = service.get_category(parent_id).id
        except CategoryNotFoundError:
            return create_error_response(
                status_code=404,
                code="NOT_FOUND",
                message="Category not found",
                details=[{"field": "parent_id", "message": f"No category with id '{parent_id}'"}]
            )

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

    tree = service.get_tree(
        root_parent_id=root_parent_id,
        max_depth=effective_depth,
        include_product_count=include_product_count,
        industry=industry,
    )

    return ProductCategoriesResponse(
        categories=[_to_response_node(node) for node in tree.categories],
        total_categories=tree.total_categories,
        max_depth=tree.max_depth,
    )
