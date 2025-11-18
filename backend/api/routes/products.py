"""
Products API Routes
TASK-API-001: Implementation of products REST endpoints

Endpoints:
- GET /api/v1/products - List products with pagination and filtering
- GET /api/v1/products/{product_id} - Get product details with BOM
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.models import Product, BillOfMaterials


# ============================================================================
# Pydantic Response Models
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
# API Endpoints
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
    product_id: str,
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
