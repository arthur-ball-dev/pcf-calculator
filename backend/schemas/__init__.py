"""
API Schemas Module
TASK-API-004: Consolidated Pydantic request/response models for all API endpoints

This module provides centralized validation models for:
- Products API (list, detail, create)
- Calculations API (request, start, status)
- Emission Factors API (list, create)

All models include:
- Type validation (str, int, float, bool, list, etc.)
- Constraint validation (min/max values, length, patterns)
- Required vs optional field handling
- Clear error messages on validation failure
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal


# ============================================================================
# Common/Shared Models
# ============================================================================

class PaginationParams(BaseModel):
    """Common pagination parameters for list endpoints"""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# ============================================================================
# Products API Models
# ============================================================================

class BOMItemResponse(BaseModel):
    """BOM item in product detail response"""
    id: str = Field(..., description="BOM relationship ID")
    child_product_id: str = Field(..., description="Child product UUID")
    child_product_name: str = Field(..., description="Child product name")
    quantity: float = Field(..., gt=0, description="Quantity of child product per parent")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    notes: Optional[str] = Field(None, description="Optional notes about this BOM item")

    model_config = ConfigDict(from_attributes=True)


class ProductListItemResponse(BaseModel):
    """Product item in list response"""
    id: str = Field(..., description="Product UUID")
    code: str = Field(..., description="Unique product code")
    name: str = Field(..., description="Product name")
    unit: str = Field(..., description="Unit of measurement")
    category: Optional[str] = Field(None, description="Product category")
    is_finished_product: bool = Field(..., description="True if finished product, False if component")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(BaseModel):
    """Product detail response with BOM"""
    id: str = Field(..., description="Product UUID")
    code: str = Field(..., description="Unique product code")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    unit: str = Field(..., description="Unit of measurement")
    category: Optional[str] = Field(None, description="Product category")
    is_finished_product: bool = Field(..., description="True if finished product, False if component")
    bill_of_materials: List[BOMItemResponse] = Field(default_factory=list, description="List of BOM items")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated list of products"""
    items: List[ProductListItemResponse] = Field(..., description="List of products")
    total: int = Field(..., ge=0, description="Total count of products (without pagination)")
    limit: int = Field(..., ge=1, le=1000, description="Applied limit")
    offset: int = Field(..., ge=0, description="Applied offset")


# ============================================================================
# Calculations API Models
# ============================================================================

# Literal type for calculation_type enum
CalculationType = Literal["cradle_to_gate", "cradle_to_grave", "gate_to_gate"]


class CalculationRequest(BaseModel):
    """Request model for POST /calculate"""
    product_id: str = Field(..., min_length=1, description="UUID of product to calculate PCF for")
    calculation_type: CalculationType = Field(
        default="cradle_to_gate",
        description="Type of calculation: cradle_to_gate, cradle_to_grave, or gate_to_gate"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "calculation_type": "cradle_to_gate"
            }
        }
    )


class CalculationStartResponse(BaseModel):
    """Response model for POST /calculate (202 Accepted)"""
    calculation_id: str = Field(..., description="UUID for tracking calculation status")
    status: str = Field(..., description="Initial status (always 'processing')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calculation_id": "calc123abc456def789ghi012jkl345mno",
                "status": "processing"
            }
        }
    )


class CalculationStatusResponse(BaseModel):
    """Response model for GET /calculations/{id}"""
    calculation_id: str = Field(..., description="Calculation UUID")
    status: str = Field(..., description="Current status: processing, completed, failed")
    product_id: Optional[str] = Field(None, description="Product UUID")
    created_at: Optional[str] = Field(None, description="Calculation start time (ISO 8601)")

    # Fields present when completed
    total_co2e_kg: Optional[float] = Field(None, ge=0, description="Total emissions in kg CO2e")
    materials_co2e: Optional[float] = Field(None, ge=0, description="Materials emissions in kg CO2e")
    energy_co2e: Optional[float] = Field(None, ge=0, description="Energy emissions in kg CO2e")
    transport_co2e: Optional[float] = Field(None, ge=0, description="Transport emissions in kg CO2e")
    calculation_time_ms: Optional[int] = Field(None, ge=0, description="Calculation duration in milliseconds")

    # Fields present when failed
    error_message: Optional[str] = Field(None, description="Error details if status=failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calculation_id": "calc123abc456def789ghi012jkl345mno",
                "status": "completed",
                "product_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "created_at": "2025-11-02T12:34:56.789Z",
                "total_co2e_kg": 2.05,
                "materials_co2e": 1.80,
                "energy_co2e": 0.15,
                "transport_co2e": 0.10,
                "calculation_time_ms": 150
            }
        }
    )


# ============================================================================
# Emission Factors API Models
# ============================================================================

class EmissionFactorListItemResponse(BaseModel):
    """Emission factor item in list response"""
    id: str = Field(..., description="Emission factor UUID")
    activity_name: str = Field(..., description="Activity or material name")
    co2e_factor: float = Field(..., ge=0, description="CO2e emission factor (kg CO2e per unit)")
    unit: str = Field(..., description="Unit of measurement")
    data_source: str = Field(..., description="Data source (EPA, DEFRA, Ecoinvent, etc.)")
    geography: str = Field(..., description="Geographic scope (GLO, US, EU, etc.)")
    reference_year: Optional[int] = Field(None, description="Reference year for data")
    data_quality_rating: Optional[float] = Field(None, ge=0, le=1, description="Data quality rating (0-1)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)


class EmissionFactorListResponse(BaseModel):
    """Paginated list of emission factors"""
    items: List[EmissionFactorListItemResponse] = Field(..., description="List of emission factors")
    total: int = Field(..., ge=0, description="Total count of emission factors (without pagination)")
    limit: int = Field(..., ge=1, le=1000, description="Applied limit")
    offset: int = Field(..., ge=0, description="Applied offset")


class EmissionFactorCreateRequest(BaseModel):
    """Request body for creating emission factor"""
    activity_name: str = Field(..., min_length=1, max_length=255, description="Activity or material name")
    co2e_factor: float = Field(..., ge=0, description="CO2e emission factor (kg CO2e per unit)")
    unit: str = Field(..., min_length=1, max_length=20, description="Unit of measurement")
    data_source: str = Field(..., min_length=1, max_length=100, description="Data source identifier")
    geography: str = Field(default="GLO", max_length=50, description="Geographic scope (default: GLO)")
    reference_year: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Reference year for data (1900-2100)"
    )
    data_quality_rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Data quality rating (0-1)"
    )
    uncertainty_min: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum uncertainty bound (non-negative)"
    )
    uncertainty_max: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum uncertainty bound (non-negative)"
    )

    @field_validator('co2e_factor')
    @classmethod
    def validate_co2e_factor(cls, v):
        """Validate co2e_factor is non-negative"""
        if v < 0:
            raise ValueError('co2e_factor must be non-negative')
        return v

    @field_validator('uncertainty_max')
    @classmethod
    def validate_uncertainty_range(cls, v, info):
        """Validate that uncertainty_max >= uncertainty_min if both provided"""
        uncertainty_min = info.data.get('uncertainty_min')
        if v is not None and uncertainty_min is not None:
            if v < uncertainty_min:
                raise ValueError('uncertainty_max must be >= uncertainty_min')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "activity_name": "Steel production",
                "co2e_factor": 2.5,
                "unit": "kg",
                "data_source": "EPA",
                "geography": "US",
                "reference_year": 2024,
                "data_quality_rating": 0.8
            }
        }
    )


class EmissionFactorCreateResponse(BaseModel):
    """Response after creating emission factor"""
    id: str = Field(..., description="Emission factor UUID")
    activity_name: str = Field(..., description="Activity or material name")
    co2e_factor: float = Field(..., description="CO2e emission factor (kg CO2e per unit)")
    unit: str = Field(..., description="Unit of measurement")
    data_source: str = Field(..., description="Data source")
    geography: str = Field(..., description="Geographic scope")
    reference_year: Optional[int] = Field(None, description="Reference year for data")
    data_quality_rating: Optional[float] = Field(None, description="Data quality rating (0-1)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Export All Models
# ============================================================================

__all__ = [
    # Common
    "PaginationParams",
    # Products
    "BOMItemResponse",
    "ProductListItemResponse",
    "ProductDetailResponse",
    "ProductListResponse",
    # Calculations
    "CalculationType",
    "CalculationRequest",
    "CalculationStartResponse",
    "CalculationStatusResponse",
    # Emission Factors
    "EmissionFactorListItemResponse",
    "EmissionFactorListResponse",
    "EmissionFactorCreateRequest",
    "EmissionFactorCreateResponse",
]
