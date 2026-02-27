"""
Product Categories API Routes (split from products.py for ARCH-009).

Endpoints:
- GET /api/v1/products/categories - Hierarchical category tree
"""

from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.connection import get_db
from backend.models import Product, ProductCategory
from backend.models.user import User
from backend.auth.dependencies import get_optional_user
from backend.api.utils.error_responses import create_error_response
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

def build_category_tree(
    categories: List[ProductCategory],
    parent_id: Optional[str],
    current_depth: int,
    max_depth: int,
    include_product_count: bool,
    db: Session
) -> List[CategoryTreeNode]:
    """Recursively build category tree structure."""
    level_cats = [c for c in categories if c.parent_id == parent_id]

    result = []
    for cat in level_cats:
        product_count = None
        if include_product_count:
            product_count = _count_products_recursive(cat.id, categories, db)

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
    count = db.query(func.count(Product.id)).filter(
        Product.category_id == category_id
    ).scalar() or 0

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
    industry: Optional[str] = Query(None, description="Filter categories by industry sector"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Retrieve hierarchical category tree."""
    query = db.query(ProductCategory)

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

    all_categories = query.all()

    tree = build_category_tree(
        all_categories, None, 0, max_depth, include_product_count, db
    )

    return ProductCategoriesResponse(
        categories=tree,
        total_categories=count_tree_categories(tree),
        max_depth=find_max_depth(tree)
    )
