"""
Admin Coverage API Routes.

TASK-API-P5-001: Admin Data Sources Endpoints

Endpoints:
- GET /admin/emission-factors/coverage - Get coverage statistics

Contract Reference: phase5-contracts/admin-coverage-contract.yaml
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models import DataSource, EmissionFactor, Product, ProductCategory
from backend.schemas.admin import (
    GroupByEnum,
    CoverageResponse,
    CoverageSummary,
    CoverageBySource,
    CoverageByGeography,
    CoverageByCategory,
    CoverageGaps,
    MissingGeography,
    MissingCategory,
    OutdatedFactors,
    YearRange,
)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(tags=["admin-coverage"])


# ============================================================================
# Geography Name Mapping
# ============================================================================

GEOGRAPHY_NAMES: Dict[str, str] = {
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "CN": "China",
    "JP": "Japan",
    "IN": "India",
    "BR": "Brazil",
    "CA": "Canada",
    "AU": "Australia",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "KR": "South Korea",
    "MX": "Mexico",
    "RU": "Russia",
    "GLO": "Global",
    "EU": "European Union",
    "ROW": "Rest of World",
    "BD": "Bangladesh",
    "VN": "Vietnam",
    "ID": "Indonesia",
    "PH": "Philippines",
    "TH": "Thailand",
    "PK": "Pakistan",
}


def get_geography_name(code: str) -> str:
    """Get the full name for a geography code."""
    return GEOGRAPHY_NAMES.get(code, code)


# ============================================================================
# Helper Functions
# ============================================================================


def create_error_response(code: str, message: str, details: Optional[list] = None) -> dict:
    """Create a standardized error response dict."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/emission-factors/coverage",
    response_model=CoverageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get emission factor coverage",
    description="Get emission factor coverage statistics by data source, geography, and product category.",
)
def get_coverage(
    group_by: GroupByEnum = Query(
        GroupByEnum.source, description="Primary grouping dimension"
    ),
    data_source_id: Optional[str] = Query(
        None, description="Filter to specific data source"
    ),
    include_inactive: bool = Query(
        False, description="Include inactive emission factors in counts"
    ),
    db: Session = Depends(get_db),
) -> CoverageResponse:
    """
    Get emission factor coverage statistics.

    Query Parameters:
    - group_by: Primary grouping dimension (source, geography, category, year)
    - data_source_id: Filter to specific data source
    - include_inactive: Include inactive emission factors (default: false)

    Returns:
    - summary: Overall coverage summary
    - by_source: Coverage breakdown by data source
    - by_geography: Coverage breakdown by geography
    - by_category: Coverage breakdown by product category
    - gaps: Identified coverage gaps
    """
    # Validate data_source_id if provided
    if data_source_id:
        data_source = (
            db.query(DataSource)
            .filter(DataSource.id == data_source_id)
            .first()
        )
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=create_error_response(
                    code="INVALID_DATA_SOURCE",
                    message="Data source not found",
                    details=[
                        {"field": "data_source_id", "message": f"No data source exists with ID {data_source_id}"}
                    ],
                ),
            )

    # Build base query for emission factors
    base_query = db.query(EmissionFactor)
    if data_source_id:
        base_query = base_query.filter(EmissionFactor.data_source_id == data_source_id)
    if not include_inactive:
        base_query = base_query.filter(EmissionFactor.is_active == True)

    # ============================================================================
    # Summary Statistics
    # ============================================================================

    total_emission_factors = base_query.count()

    active_query = db.query(EmissionFactor)
    if data_source_id:
        active_query = active_query.filter(EmissionFactor.data_source_id == data_source_id)
    active_emission_factors = active_query.filter(EmissionFactor.is_active == True).count()

    unique_activities = (
        base_query
        .with_entities(EmissionFactor.activity_name)
        .distinct()
        .count()
    )

    geographies_covered = (
        base_query
        .with_entities(EmissionFactor.geography)
        .distinct()
        .count()
    )

    # Average quality rating
    avg_quality = base_query.with_entities(
        func.avg(EmissionFactor.data_quality_rating)
    ).scalar()

    # Categories analysis
    all_categories = db.query(ProductCategory).all()
    emission_factor_categories = set(
        row[0] for row in base_query.with_entities(EmissionFactor.category).distinct().all()
        if row[0]
    )

    # Count categories with and without factors
    categories_with_factors = 0
    categories_without_factors = 0

    for cat in all_categories:
        # Check if any products in this category have matching factors
        # Simple heuristic: check if category name appears in emission factor categories
        if cat.name in emission_factor_categories or cat.code in emission_factor_categories:
            categories_with_factors += 1
        else:
            categories_without_factors += 1

    # Calculate coverage percentage
    total_products = db.query(Product).count()
    products_with_factors = 0  # Would require matching logic
    coverage_percentage = 0.0
    if total_products > 0 and total_emission_factors > 0:
        # Simplified calculation: assume some coverage if factors exist
        coverage_percentage = min(100.0, (total_emission_factors / max(1, total_products)) * 10)

    summary = CoverageSummary(
        total_emission_factors=total_emission_factors,
        active_emission_factors=active_emission_factors,
        unique_activities=unique_activities,
        geographies_covered=geographies_covered,
        categories_with_factors=categories_with_factors,
        categories_without_factors=categories_without_factors,
        average_quality_rating=float(avg_quality) if avg_quality else None,
        coverage_percentage=round(coverage_percentage, 1),
    )

    # ============================================================================
    # Coverage by Source
    # ============================================================================

    by_source: List[CoverageBySource] = []

    # Get all data sources with factors
    source_stats = (
        db.query(
            EmissionFactor.data_source_id,
            func.count(EmissionFactor.id).label("total"),
            func.count(EmissionFactor.id).filter(EmissionFactor.is_active == True).label("active"),
            func.avg(EmissionFactor.data_quality_rating).filter(EmissionFactor.is_active == True).label("avg_quality"),
            func.min(EmissionFactor.reference_year).filter(EmissionFactor.is_active == True).label("min_year"),
            func.max(EmissionFactor.reference_year).filter(EmissionFactor.is_active == True).label("max_year"),
        )
    )

    if data_source_id:
        source_stats = source_stats.filter(EmissionFactor.data_source_id == data_source_id)
    if not include_inactive:
        source_stats = source_stats.filter(EmissionFactor.is_active == True)

    source_stats = source_stats.group_by(EmissionFactor.data_source_id).all()

    for row in source_stats:
        source_id = row[0]
        total = row[1]
        active = row[2]
        avg_qual = row[3]
        min_year = row[4]
        max_year = row[5]

        # Get source name
        if source_id:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            source_name = source.name if source else "Unknown"
        else:
            source_name = "Legacy/Unlinked"

        # Get geographies for this source
        geos = (
            db.query(EmissionFactor.geography)
            .filter(EmissionFactor.data_source_id == source_id)
            .filter(EmissionFactor.is_active == True)
            .distinct()
            .all()
        )
        geographies = [g[0] for g in geos if g[0]]

        # Calculate percentage
        percentage = (total / total_emission_factors * 100) if total_emission_factors > 0 else 0

        by_source.append(
            CoverageBySource(
                source_id=source_id,
                source_name=source_name,
                total_factors=total,
                active_factors=active or 0,
                percentage_of_total=round(percentage, 1),
                geographies=geographies,
                average_quality=float(avg_qual) if avg_qual else None,
                year_range=YearRange(min=min_year, max=max_year),
            )
        )

    # ============================================================================
    # Coverage by Geography
    # ============================================================================

    by_geography: List[CoverageByGeography] = []

    geo_stats = (
        db.query(
            EmissionFactor.geography,
            func.count(EmissionFactor.id).label("total"),
        )
    )

    if data_source_id:
        geo_stats = geo_stats.filter(EmissionFactor.data_source_id == data_source_id)
    if not include_inactive:
        geo_stats = geo_stats.filter(EmissionFactor.is_active == True)

    geo_stats = geo_stats.group_by(EmissionFactor.geography).all()

    for row in geo_stats:
        geo_code = row[0]
        total = row[1]

        if not geo_code:
            continue

        # Get sources covering this geography
        sources_query = (
            db.query(DataSource.name)
            .join(EmissionFactor, EmissionFactor.data_source_id == DataSource.id)
            .filter(EmissionFactor.geography == geo_code)
            .filter(EmissionFactor.is_active == True)
            .distinct()
            .all()
        )
        sources = [s[0] for s in sources_query]

        # Calculate percentage
        percentage = (total / total_emission_factors * 100) if total_emission_factors > 0 else 0

        by_geography.append(
            CoverageByGeography(
                geography=geo_code,
                geography_name=get_geography_name(geo_code),
                total_factors=total,
                sources=sources,
                percentage_of_total=round(percentage, 1),
            )
        )

    # Sort by total_factors descending
    by_geography.sort(key=lambda x: x.total_factors, reverse=True)

    # ============================================================================
    # Coverage by Category
    # ============================================================================

    by_category: List[CoverageByCategory] = []

    for cat in all_categories[:100]:  # Limit to 100 categories for performance
        # Count products in this category
        products_count = (
            db.query(Product)
            .filter(Product.category_id == cat.id)
            .count()
        )

        # Count factors that might apply to this category
        # This is a simplified check - would need proper category mapping
        factors_available = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.category == cat.name,
                EmissionFactor.is_active == True,
            )
            .count()
        )

        # For now, use a heuristic for products with factors
        products_with_factors = min(products_count, factors_available) if factors_available > 0 else 0

        # Calculate coverage percentage
        coverage_pct = (products_with_factors / products_count * 100) if products_count > 0 else 0

        # Determine gap status
        if coverage_pct >= 80:
            gap_status = "full"
        elif coverage_pct > 0:
            gap_status = "partial"
        else:
            gap_status = "none"

        by_category.append(
            CoverageByCategory(
                category_id=cat.id,
                category_name=cat.name,
                category_code=cat.code,
                products_count=products_count,
                products_with_factors=products_with_factors,
                coverage_percentage=round(coverage_pct, 1),
                factors_available=factors_available,
                gap_status=gap_status,
            )
        )

    # ============================================================================
    # Coverage Gaps
    # ============================================================================

    # Missing geographies - geographies with products but no factors
    product_geos = (
        db.query(Product.country_of_origin)
        .filter(Product.country_of_origin.isnot(None))
        .distinct()
        .all()
    )
    product_geo_set = set(g[0] for g in product_geos if g[0])

    factor_geos = set(g.geography for g in by_geography)

    missing_geographies: List[MissingGeography] = []
    for geo in product_geo_set - factor_geos:
        products_affected = (
            db.query(Product)
            .filter(Product.country_of_origin == geo)
            .count()
        )
        if products_affected > 0:
            missing_geographies.append(
                MissingGeography(
                    geography=geo,
                    products_affected=products_affected,
                )
            )

    # Missing categories - categories with products but no factors
    missing_categories: List[MissingCategory] = [
        MissingCategory(
            category_id=cat.category_id,
            category_name=cat.category_name,
            products_count=cat.products_count,
        )
        for cat in by_category
        if cat.gap_status == "none" and cat.products_count > 0
    ]

    # Outdated factors - factors with reference year > 3 years old
    current_year = datetime.now().year
    outdated_threshold = current_year - 3

    outdated_by_source = (
        db.query(
            DataSource.name,
            func.count(EmissionFactor.id).label("count"),
            func.min(EmissionFactor.reference_year).label("oldest_year"),
        )
        .join(EmissionFactor, EmissionFactor.data_source_id == DataSource.id)
        .filter(
            EmissionFactor.is_active == True,
            EmissionFactor.reference_year < outdated_threshold,
        )
        .group_by(DataSource.name)
        .all()
    )

    outdated_factors: List[OutdatedFactors] = [
        OutdatedFactors(
            source_name=row[0],
            count=row[1],
            oldest_year=row[2],
        )
        for row in outdated_by_source
        if row[1] > 0
    ]

    gaps = CoverageGaps(
        missing_geographies=missing_geographies,
        missing_categories=missing_categories,
        outdated_factors=outdated_factors,
    )

    return CoverageResponse(
        summary=summary,
        by_source=by_source,
        by_geography=by_geography,
        by_category=by_category,
        gaps=gaps,
    )
