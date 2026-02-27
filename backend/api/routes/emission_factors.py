"""
Emission Factors API Routes
TASK-API-003: Implementation of emission factors REST endpoints
TASK-BE-P7-018: Added JWT authentication and role-based access control

Endpoints:
- GET /api/v1/emission-factors - List emission factors (user role)
- POST /api/v1/emission-factors - Create emission factor (admin role)
- PUT /api/v1/emission-factors/{id} - Update emission factor (admin role)
- DELETE /api/v1/emission-factors/{id} - Delete emission factor (admin role)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

from backend.database.connection import get_db, get_async_db
from backend.models import EmissionFactor, DataSource
from backend.models.user import User
from backend.auth.dependencies import require_admin, get_optional_user
from backend.services.data_ingestion.emission_factor_mapper import EmissionFactorMapper


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class EmissionFactorListItemResponse(BaseModel):
    """Emission factor item in list response"""
    id: str
    activity_name: str
    category: Optional[str] = None
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
    activity_name: str = Field(
        ...,
        min_length=1,
        description="Activity or material name",
        examples=["custom_steel_alloy"]
    )
    category: Optional[str] = Field(
        None,
        description="Category (material, energy, transport, other)",
        examples=["material"]
    )
    co2e_factor: float = Field(
        ...,
        ge=0,
        description="CO2e emission factor (kg CO2e per unit)",
        examples=[2.8]
    )
    unit: str = Field(
        ...,
        min_length=1,
        description="Unit of measurement",
        examples=["kg"]
    )
    data_source: str = Field(
        ...,
        min_length=1,
        description="Data source identifier",
        examples=["custom"]
    )
    geography: str = Field(
        default="GLO",
        description="Geographic scope (default: GLO)",
        examples=["GLO"]
    )
    reference_year: Optional[int] = Field(
        default=None,
        description="Reference year for data",
        examples=[2024]
    )
    data_quality_rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Data quality rating (0-1)",
        examples=[0.8]
    )
    uncertainty_min: Optional[float] = Field(
        default=None,
        description="Minimum uncertainty bound",
        examples=[2.5]
    )
    uncertainty_max: Optional[float] = Field(
        default=None,
        description="Maximum uncertainty bound",
        examples=[3.1]
    )
    data_source_id: Optional[str] = Field(
        default=None,
        description="Data source ID reference",
        examples=["abc123"]
    )

    @field_validator('co2e_factor')
    @classmethod
    def validate_co2e_factor(cls, v):
        """Validate co2e_factor is non-negative"""
        if v < 0:
            raise ValueError('co2e_factor must be non-negative')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "activity_name": "custom_steel_alloy",
                "category": "material",
                "co2e_factor": 2.8,
                "unit": "kg",
                "data_source": "custom",
                "geography": "GLO",
                "reference_year": 2024,
                "data_quality_rating": 0.8
            }
        }


class EmissionFactorUpdateRequest(BaseModel):
    """Request body for updating emission factor"""
    activity_name: Optional[str] = Field(
        None,
        min_length=1,
        description="Activity or material name"
    )
    category: Optional[str] = Field(
        None,
        description="Category (material, energy, transport, other)"
    )
    co2e_factor: Optional[float] = Field(
        None,
        ge=0,
        description="CO2e emission factor (kg CO2e per unit)"
    )
    unit: Optional[str] = Field(
        None,
        min_length=1,
        description="Unit of measurement"
    )
    geography: Optional[str] = Field(
        None,
        description="Geographic scope"
    )
    reference_year: Optional[int] = Field(
        None,
        description="Reference year for data"
    )
    data_quality_rating: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Data quality rating (0-1)"
    )

    @field_validator('co2e_factor')
    @classmethod
    def validate_co2e_factor(cls, v):
        """Validate co2e_factor is non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError('co2e_factor must be non-negative')
        return v


class EmissionFactorCreateResponse(BaseModel):
    """Response after creating emission factor"""
    id: str
    activity_name: str
    category: Optional[str] = None
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
    data_source: Optional[str] = Query(None, description="Filter by data source (EPA, DEFRA, etc.)"),
    geography: Optional[str] = Query(None, description="Filter by geography (GLO, US, EU, etc.)"),
    unit: Optional[str] = Query(None, description="Filter by unit (kg, L, kWh, etc.)"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name (case-insensitive partial match)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
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
            category=ef.category,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> EmissionFactorCreateResponse:
    """
    Create a new custom emission factor.

    Requires admin role.

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
    - 403: Insufficient permissions (user role)
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
        category=emission_factor.category,
        co2e_factor=Decimal(str(emission_factor.co2e_factor)),
        unit=emission_factor.unit,
        data_source=emission_factor.data_source,
        geography=emission_factor.geography,
        reference_year=emission_factor.reference_year,
        data_quality_rating=Decimal(str(emission_factor.data_quality_rating)) if emission_factor.data_quality_rating else None,
        uncertainty_min=Decimal(str(emission_factor.uncertainty_min)) if emission_factor.uncertainty_min else None,
        uncertainty_max=Decimal(str(emission_factor.uncertainty_max)) if emission_factor.uncertainty_max else None,
        data_source_id=emission_factor.data_source_id
    )

    db.add(new_emission_factor)
    db.commit()
    db.refresh(new_emission_factor)

    return EmissionFactorCreateResponse(
        id=new_emission_factor.id,
        activity_name=new_emission_factor.activity_name,
        category=new_emission_factor.category,
        co2e_factor=float(new_emission_factor.co2e_factor),
        unit=new_emission_factor.unit,
        data_source=new_emission_factor.data_source,
        geography=new_emission_factor.geography,
        reference_year=new_emission_factor.reference_year,
        data_quality_rating=float(new_emission_factor.data_quality_rating) if new_emission_factor.data_quality_rating else None,
        created_at=new_emission_factor.created_at.isoformat() if new_emission_factor.created_at else ""
    )


@router.put(
    "/emission-factors/{factor_id}",
    response_model=EmissionFactorCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update emission factor",
    description="Update an existing emission factor"
)
def update_emission_factor(
    factor_id: str = Path(..., description="Emission factor ID"),
    updates: EmissionFactorUpdateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> EmissionFactorCreateResponse:
    """
    Update an existing emission factor.

    Requires admin role.

    Path Parameters:
    - factor_id: Emission factor ID

    Request Body:
    - Any fields to update (only provided fields are updated)

    Returns:
    - Updated emission factor

    Raises:
    - 403: Insufficient permissions (user role)
    - 404: Emission factor not found
    - 422: Validation error
    """
    # Find the emission factor
    emission_factor = db.query(EmissionFactor).filter(
        EmissionFactor.id == factor_id
    ).first()

    if not emission_factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emission factor not found"
        )

    # Update provided fields
    if updates:
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == 'co2e_factor':
                    setattr(emission_factor, field, Decimal(str(value)))
                elif field == 'data_quality_rating':
                    setattr(emission_factor, field, Decimal(str(value)) if value else None)
                else:
                    setattr(emission_factor, field, value)

    db.commit()
    db.refresh(emission_factor)

    return EmissionFactorCreateResponse(
        id=emission_factor.id,
        activity_name=emission_factor.activity_name,
        category=emission_factor.category,
        co2e_factor=float(emission_factor.co2e_factor),
        unit=emission_factor.unit,
        data_source=emission_factor.data_source,
        geography=emission_factor.geography,
        reference_year=emission_factor.reference_year,
        data_quality_rating=float(emission_factor.data_quality_rating) if emission_factor.data_quality_rating else None,
        created_at=emission_factor.created_at.isoformat() if emission_factor.created_at else ""
    )


@router.delete(
    "/emission-factors/{factor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete emission factor",
    description="Delete an emission factor"
)
def delete_emission_factor(
    factor_id: str = Path(..., description="Emission factor ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete an emission factor.

    Requires admin role.

    Path Parameters:
    - factor_id: Emission factor ID

    Returns:
    - 204 No Content on success

    Raises:
    - 403: Insufficient permissions (user role)
    - 404: Emission factor not found
    """
    # Find the emission factor
    emission_factor = db.query(EmissionFactor).filter(
        EmissionFactor.id == factor_id
    ).first()

    if not emission_factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emission factor not found"
        )

    db.delete(emission_factor)
    db.commit()

    return None


# ============================================================================
# Suggest Endpoint
# ============================================================================

@router.get(
    "/emission-factors/suggest/{component_name:path}",
    response_model=Optional[EmissionFactorListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Suggest emission factor for component",
    description="Get suggested emission factor for a BOM component name using mapping rules"
)
async def suggest_emission_factor(
    component_name: str = Path(..., description="Component name to find matching EF for"),
    unit: str = Query("kg", description="Unit of measurement"),
    geography: Optional[str] = Query(None, description="Geographic region (optional)"),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[EmissionFactorListItemResponse]:
    """
    Get suggested emission factor for a component name.

    Uses the EmissionFactorMapper to find the best matching emission factor
    based on:
    1. Exact match on activity_name
    2. Configured mappings (emission_factor_mappings.json)
    3. Partial/fuzzy match
    4. Category fallback
    5. Geographic fallback (GLO)

    Path Parameters:
    - component_name: Name of the BOM component (e.g., "Rubber", "Steel", "Plastic - HDPE")

    Query Parameters:
    - unit: Unit of measurement (default: "kg")
    - geography: Optional geographic region filter

    Returns:
    - Matching emission factor or null if not found
    """
    mapper = EmissionFactorMapper(db=db)

    factor = await mapper.get_factor_for_component(
        component_name=component_name,
        unit=unit,
        geography=geography,
    )

    if not factor:
        return None

    return EmissionFactorListItemResponse(
        id=factor.id,
        activity_name=factor.activity_name,
        category=factor.category,
        co2e_factor=float(factor.co2e_factor),
        unit=factor.unit,
        data_source=factor.data_source,
        geography=factor.geography,
        reference_year=factor.reference_year,
        data_quality_rating=float(factor.data_quality_rating) if factor.data_quality_rating else None,
        created_at=factor.created_at.isoformat() if factor.created_at else ""
    )


# ============================================================================
# Attribution Response Models
# ============================================================================

class DataSourceAttribution(BaseModel):
    """Attribution information for a single data source."""
    id: str
    name: str
    license_type: Optional[str] = None
    license_url: Optional[str] = None
    attribution_text: Optional[str] = None
    attribution_url: Optional[str] = None
    allows_commercial_use: bool = True
    requires_attribution: bool = False
    requires_share_alike: bool = False


class AttributionResponse(BaseModel):
    """Response containing all data source attributions."""
    attributions: List[DataSourceAttribution]
    notice: str = (
        "This application uses emission factor data from multiple sources. "
        "Please review individual source attributions for compliance requirements."
    )


# ============================================================================
# Attribution Endpoint
# ============================================================================

@router.get(
    "/attributions",
    response_model=AttributionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get data source attributions",
    description="Get license and attribution information for all active data sources"
)
def get_attributions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> AttributionResponse:
    """
    Get attribution and license information for all active data sources.

    This endpoint provides information needed to comply with data source
    license requirements, including:
    - EPA GHG Emission Factors Hub (Public Domain)
    - DEFRA UK Conversion Factors (Open Government Licence v3.0)

    Returns:
    - attributions: List of data source attributions with license info
    - notice: General notice about data usage
    """
    # Query active data sources with license info
    data_sources = (
        db.query(DataSource)
        .filter(DataSource.is_active == True)
        .all()
    )

    attributions = []
    for ds in data_sources:
        attributions.append(
            DataSourceAttribution(
                id=ds.id,
                name=ds.name,
                license_type=ds.license_type,
                license_url=ds.license_url,
                attribution_text=ds.attribution_text,
                attribution_url=ds.attribution_url,
                allows_commercial_use=ds.allows_commercial_use if ds.allows_commercial_use is not None else True,
                requires_attribution=ds.requires_attribution if ds.requires_attribution is not None else False,
                requires_share_alike=ds.requires_share_alike if ds.requires_share_alike is not None else False,
            )
        )

    return AttributionResponse(attributions=attributions)
