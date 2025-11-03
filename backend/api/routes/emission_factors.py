"""
Emission Factors API Routes
TASK-API-003: Implementation of emission factors REST endpoints

Endpoints:
- GET /api/v1/emission-factors - List emission factors with pagination and filtering
- POST /api/v1/emission-factors - Create custom emission factor
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

from backend.database.connection import get_db
from backend.models import EmissionFactor


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class EmissionFactorListItemResponse(BaseModel):
    """Emission factor item in list response"""
    id: str
    activity_name: str
    co2e_factor: float
    unit: str
    data_source: str
    geography: str
    reference_year: Optional[int] = None
    data_quality_rating: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True


class EmissionFactorListResponse(BaseModel):
    """Paginated list of emission factors"""
    items: List[EmissionFactorListItemResponse]
    total: int
    limit: int
    offset: int


class EmissionFactorCreateRequest(BaseModel):
    """Request body for creating emission factor"""
    activity_name: str = Field(..., min_length=1, description="Activity or material name")
    co2e_factor: float = Field(..., ge=0, description="CO2e emission factor (kg CO2e per unit)")
    unit: str = Field(..., min_length=1, description="Unit of measurement")
    data_source: str = Field(..., min_length=1, description="Data source identifier")
    geography: str = Field(default="GLO", description="Geographic scope (default: GLO)")
    reference_year: Optional[int] = Field(default=None, description="Reference year for data")
    data_quality_rating: Optional[float] = Field(default=None, ge=0, le=1, description="Data quality rating (0-1)")
    uncertainty_min: Optional[float] = Field(default=None, description="Minimum uncertainty bound")
    uncertainty_max: Optional[float] = Field(default=None, description="Maximum uncertainty bound")

    @field_validator('co2e_factor')
    @classmethod
    def validate_co2e_factor(cls, v):
        """Validate co2e_factor is non-negative"""
        if v < 0:
            raise ValueError('co2e_factor must be non-negative')
        return v


class EmissionFactorCreateResponse(BaseModel):
    """Response after creating emission factor"""
    id: str
    activity_name: str
    co2e_factor: float
    unit: str
    data_source: str
    geography: str
    reference_year: Optional[int] = None
    data_quality_rating: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["emission-factors"])


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/emission-factors",
    response_model=EmissionFactorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List emission factors",
    description="Get paginated list of emission factors with optional filtering"
)
def list_emission_factors(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    data_source: Optional[str] = Query(None, description="Filter by data source (EPA, DEFRA, Ecoinvent, etc.)"),
    geography: Optional[str] = Query(None, description="Filter by geography (GLO, US, EU, etc.)"),
    unit: Optional[str] = Query(None, description="Filter by unit (kg, L, kWh, etc.)"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name (case-insensitive partial match)"),
    db: Session = Depends(get_db)
) -> EmissionFactorListResponse:
    """
    List all emission factors with pagination and optional filtering.

    Query Parameters:
    - limit: Maximum number of emission factors to return (1-1000, default: 100)
    - offset: Number of emission factors to skip (default: 0)
    - data_source: Filter by data source (exact match)
    - geography: Filter by geography (exact match)
    - unit: Filter by unit (exact match)
    - activity_name: Filter by activity name (case-insensitive partial match)

    Returns:
    - items: List of emission factors
    - total: Total count of emission factors (without pagination)
    - limit: Applied limit
    - offset: Applied offset
    """
    # Build query
    query = db.query(EmissionFactor)

    # Apply filters
    if data_source is not None:
        query = query.filter(EmissionFactor.data_source == data_source)

    if geography is not None:
        query = query.filter(EmissionFactor.geography == geography)

    if unit is not None:
        query = query.filter(EmissionFactor.unit == unit)

    if activity_name is not None:
        # Case-insensitive partial match
        query = query.filter(
            EmissionFactor.activity_name.ilike(f"%{activity_name}%")
        )

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    emission_factors = query.offset(offset).limit(limit).all()

    # Convert emission factors to response format
    items = [
        EmissionFactorListItemResponse(
            id=ef.id,
            activity_name=ef.activity_name,
            co2e_factor=float(ef.co2e_factor),
            unit=ef.unit,
            data_source=ef.data_source,
            geography=ef.geography,
            reference_year=ef.reference_year,
            data_quality_rating=float(ef.data_quality_rating) if ef.data_quality_rating else None,
            created_at=ef.created_at.isoformat() if ef.created_at else ""
        )
        for ef in emission_factors
    ]

    return EmissionFactorListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post(
    "/emission-factors",
    response_model=EmissionFactorCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom emission factor",
    description="Add a custom emission factor to the database"
)
def create_emission_factor(
    emission_factor: EmissionFactorCreateRequest,
    db: Session = Depends(get_db)
) -> EmissionFactorCreateResponse:
    """
    Create a new custom emission factor.

    Request Body:
    - activity_name: Activity or material name (required)
    - co2e_factor: CO2e emission factor in kg CO2e per unit (required, non-negative)
    - unit: Unit of measurement (required)
    - data_source: Data source identifier (required)
    - geography: Geographic scope (default: GLO)
    - reference_year: Reference year for data (optional)
    - data_quality_rating: Data quality rating 0-1 (optional)
    - uncertainty_min: Minimum uncertainty bound (optional)
    - uncertainty_max: Maximum uncertainty bound (optional)

    Returns:
    - Created emission factor with generated ID

    Raises:
    - 409: Emission factor with same composite key already exists
      (activity_name + data_source + geography + reference_year)
    - 422: Validation error (missing required fields, invalid values)
    """
    # Check for duplicate based on unique constraint
    # Composite key: (activity_name, data_source, geography, reference_year)
    existing = db.query(EmissionFactor).filter(
        EmissionFactor.activity_name == emission_factor.activity_name,
        EmissionFactor.data_source == emission_factor.data_source,
        EmissionFactor.geography == emission_factor.geography,
        EmissionFactor.reference_year == emission_factor.reference_year
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Emission factor already exists for activity '{emission_factor.activity_name}' "
                   f"with data_source='{emission_factor.data_source}', "
                   f"geography='{emission_factor.geography}', "
                   f"reference_year={emission_factor.reference_year}"
        )

    # Create new emission factor
    new_emission_factor = EmissionFactor(
        activity_name=emission_factor.activity_name,
        co2e_factor=Decimal(str(emission_factor.co2e_factor)),
        unit=emission_factor.unit,
        data_source=emission_factor.data_source,
        geography=emission_factor.geography,
        reference_year=emission_factor.reference_year,
        data_quality_rating=Decimal(str(emission_factor.data_quality_rating)) if emission_factor.data_quality_rating else None,
        uncertainty_min=Decimal(str(emission_factor.uncertainty_min)) if emission_factor.uncertainty_min else None,
        uncertainty_max=Decimal(str(emission_factor.uncertainty_max)) if emission_factor.uncertainty_max else None
    )

    db.add(new_emission_factor)
    db.commit()
    db.refresh(new_emission_factor)

    return EmissionFactorCreateResponse(
        id=new_emission_factor.id,
        activity_name=new_emission_factor.activity_name,
        co2e_factor=float(new_emission_factor.co2e_factor),
        unit=new_emission_factor.unit,
        data_source=new_emission_factor.data_source,
        geography=new_emission_factor.geography,
        reference_year=new_emission_factor.reference_year,
        data_quality_rating=float(new_emission_factor.data_quality_rating) if new_emission_factor.data_quality_rating else None,
        created_at=new_emission_factor.created_at.isoformat() if new_emission_factor.created_at else ""
    )
