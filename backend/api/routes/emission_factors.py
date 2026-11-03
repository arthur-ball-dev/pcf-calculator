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

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_emission_factor_service
from backend.database.connection import get_async_db
from backend.domain.entities.emission_factor import (
    EmissionFactor,
    EmissionFactorFilters,
    NewEmissionFactor,
)
from backend.domain.services.emission_factor_service import EmissionFactorService
from backend.models.user import User
from backend.auth.dependencies import require_admin, get_optional_user
from backend.services.data_ingestion.emission_factor_mapper import EmissionFactorMapper
from backend.schemas import (
    EmissionFactorListItemResponse,
    EmissionFactorListResponse,
    EmissionFactorCreateRequest,
    EmissionFactorCreateResponse,
    EmissionFactorUpdateRequest,
    DataSourceAttribution,
    AttributionResponse,
)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["emission-factors"])


# ============================================================================
# Response Helpers
# ============================================================================

def _saved_response(factor: EmissionFactor) -> EmissionFactorCreateResponse:
    """Build the response for a created or updated emission factor."""
    return EmissionFactorCreateResponse(
        id=factor.id,
        activity_name=factor.activity_name,
        category=factor.category,
        co2e_factor=factor.co2e_factor,
        unit=factor.unit,
        data_source=factor.data_source,
        geography=factor.geography,
        reference_year=factor.reference_year,
        data_quality_rating=factor.data_quality_rating,
        created_at=factor.created_at.isoformat() if factor.created_at else ""
    )


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
    service: EmissionFactorService = Depends(get_emission_factor_service),
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
    page = service.list_factors(
        EmissionFactorFilters(
            data_source=data_source,
            geography=geography,
            unit=unit,
            activity_name=activity_name,
        ),
        limit=limit,
        offset=offset,
    )

    items = [
        EmissionFactorListItemResponse(
            id=ef.id,
            activity_name=ef.activity_name,
            category=ef.category,
            co2e_factor=ef.co2e_factor,
            unit=ef.unit,
            data_source=ef.data_source,
            geography=ef.geography,
            reference_year=ef.reference_year,
            data_quality_rating=ef.data_quality_rating,
            created_at=ef.created_at.isoformat() if ef.created_at else ""
        )
        for ef in page.items
    ]

    return EmissionFactorListResponse(
        items=items,
        total=page.total,
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
    service: EmissionFactorService = Depends(get_emission_factor_service),
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
    created = service.create_factor(
        NewEmissionFactor(
            activity_name=emission_factor.activity_name,
            category=emission_factor.category,
            co2e_factor=emission_factor.co2e_factor,
            unit=emission_factor.unit,
            data_source=emission_factor.data_source,
            geography=emission_factor.geography,
            reference_year=emission_factor.reference_year,
            data_quality_rating=emission_factor.data_quality_rating,
            uncertainty_min=emission_factor.uncertainty_min,
            uncertainty_max=emission_factor.uncertainty_max,
            data_source_id=emission_factor.data_source_id,
        )
    )

    return _saved_response(created)


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
    service: EmissionFactorService = Depends(get_emission_factor_service),
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
    changes = updates.model_dump(exclude_unset=True) if updates else {}

    return _saved_response(service.update_factor(factor_id, changes))


@router.delete(
    "/emission-factors/{factor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete emission factor",
    description="Delete an emission factor"
)
def delete_emission_factor(
    factor_id: str = Path(..., description="Emission factor ID"),
    service: EmissionFactorService = Depends(get_emission_factor_service),
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
    service.delete_factor(factor_id)

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
    service: EmissionFactorService = Depends(get_emission_factor_service),
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
    attributions = [
        DataSourceAttribution(
            id=license_.id,
            name=license_.name,
            license_type=license_.license_type,
            license_url=license_.license_url,
            attribution_text=license_.attribution_text,
            attribution_url=license_.attribution_url,
            allows_commercial_use=license_.allows_commercial_use,
            requires_attribution=license_.requires_attribution,
            requires_share_alike=license_.requires_share_alike,
        )
        for license_ in service.list_licenses()
    ]

    return AttributionResponse(attributions=attributions)
