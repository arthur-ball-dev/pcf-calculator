#!/usr/bin/env python3
"""
Data Quality Validation Script
TASK-DATA-004: Validate data quality of loaded seed data

Validates:
- Emission factors completeness and validity
- BOM coverage (implicit matching: Product.code == EmissionFactor.activity_name)
- Data quality ratings
- Overall quality score

CRITICAL: Uses actual schema (no emission_factor_id foreign key)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any
from collections import defaultdict

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from backend.models import (
    Product,
    EmissionFactor,
    BillOfMaterials,
)


def validate_data_quality(session: Session) -> Dict[str, Any]:
    """
    Validate data quality of loaded seed data.

    Args:
        session: SQLAlchemy database session

    Returns:
        dict: Quality report with metrics and validation results
    """
    validation_errors = 0
    error_details = []

    # 1. Validate Emission Factors
    emission_factors_report = _validate_emission_factors(session)

    # 2. Validate Products and BOM
    products_report = _validate_products(session)

    # 3. Validate BOM Completeness (implicit matching)
    bom_completeness_report = _validate_bom_completeness(session)

    # 4. Calculate Average Data Quality
    average_data_quality = _calculate_average_data_quality(session)

    # 5. Calculate Overall Quality Score
    overall_quality_score = _calculate_overall_quality_score(
        bom_completeness_report['coverage_percent'],
        average_data_quality,
        emission_factors_report['valid_ranges']
    )

    # Construct final report
    quality_report = {
        'validation_timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'emission_factors': emission_factors_report,
        'products': products_report,
        'bom_completeness': bom_completeness_report,
        'average_data_quality': average_data_quality,
        'overall_quality_score': overall_quality_score,
        'validation_errors': validation_errors,
        'error_details': error_details
    }

    return quality_report


def _validate_emission_factors(session: Session) -> Dict[str, Any]:
    """
    Validate emission factors for completeness and validity.

    Args:
        session: Database session

    Returns:
        dict: Emission factors validation report
    """
    # Count emission factors
    ef_count = session.query(EmissionFactor).count()

    # Check completeness (all required fields present)
    # Required: activity_name, co2e_factor, unit, data_source
    ef_with_nulls = session.query(EmissionFactor).filter(
        (EmissionFactor.activity_name == None) |
        (EmissionFactor.co2e_factor == None) |
        (EmissionFactor.unit == None) |
        (EmissionFactor.data_source == None)
    ).count()

    completeness_percent = 100.0 if ef_count > 0 else 0.0
    if ef_with_nulls > 0:
        completeness_percent = ((ef_count - ef_with_nulls) / ef_count) * 100.0

    # Check valid ranges (co2e_factor >= 0)
    ef_invalid = session.query(EmissionFactor).filter(
        EmissionFactor.co2e_factor < 0
    ).count()
    valid_ranges = (ef_invalid == 0)

    # Calculate average CO2e factor
    avg_co2e = session.query(func.avg(EmissionFactor.co2e_factor)).scalar()
    average_co2e_factor = float(avg_co2e) if avg_co2e is not None else 0.0

    # Count data sources
    data_sources_query = session.query(
        EmissionFactor.data_source,
        func.count(EmissionFactor.id)
    ).group_by(EmissionFactor.data_source).all()

    data_sources = {source: count for source, count in data_sources_query}

    return {
        'count': ef_count,
        'completeness_percent': completeness_percent,
        'valid_ranges': valid_ranges,
        'average_co2e_factor': average_co2e_factor,
        'data_sources': data_sources
    }


def _validate_products(session: Session) -> Dict[str, Any]:
    """
    Validate products and BOM structure.

    Args:
        session: Database session

    Returns:
        dict: Products validation report with per-product details
    """
    # Count finished products
    finished_products = session.query(Product).filter(
        Product.is_finished_product == True
    ).all()

    finished_count = len(finished_products)

    # Count products with BOM
    products_with_bom = []
    for product in finished_products:
        bom_count = session.query(BillOfMaterials).filter(
            BillOfMaterials.parent_product_id == product.id
        ).count()
        if bom_count > 0:
            products_with_bom.append(product)

    with_bom_count = len(products_with_bom)

    # Calculate BOM coverage percentage
    bom_coverage_percent = 0.0
    if finished_count > 0:
        bom_coverage_percent = (with_bom_count / finished_count) * 100.0

    # Generate per-product details
    product_details = []
    for product in products_with_bom:
        product_detail = _get_product_bom_coverage(session, product)
        product_details.append(product_detail)

    return {
        'finished_products': finished_count,
        'with_bom': with_bom_count,
        'bom_coverage_percent': bom_coverage_percent,
        'product_details': product_details
    }


def _get_product_bom_coverage(session: Session, product: Product) -> Dict[str, Any]:
    """
    Get BOM coverage details for a single product.

    Args:
        session: Database session
        product: Product to analyze

    Returns:
        dict: Product BOM coverage details
    """
    # Get all BOM items for this product (use relationships, not level field)
    bom_items = session.query(BillOfMaterials).filter(
        BillOfMaterials.parent_product_id == product.id
    ).all()

    bom_component_count = len(bom_items)
    components_with_factors = 0

    for bom_item in bom_items:
        child_component = bom_item.child_product

        # Check if component has matching emission factor (implicit matching)
        emission_factor = session.query(EmissionFactor).filter(
            EmissionFactor.activity_name == child_component.code
        ).first()

        if emission_factor is not None:
            components_with_factors += 1

    # Calculate coverage percentage
    coverage_percent = 0.0
    if bom_component_count > 0:
        coverage_percent = (components_with_factors / bom_component_count) * 100.0

    return {
        'code': product.code,
        'name': product.name,
        'bom_component_count': bom_component_count,
        'components_with_factors': components_with_factors,
        'coverage_percent': coverage_percent
    }


def _validate_bom_completeness(session: Session) -> Dict[str, Any]:
    """
    Validate BOM completeness across all products.
    Uses implicit matching: Product.code == EmissionFactor.activity_name

    Args:
        session: Database session

    Returns:
        dict: BOM completeness report
    """
    # Get all BOM items
    all_bom_items = session.query(BillOfMaterials).all()
    total_components = len(all_bom_items)

    components_with_factors = 0
    missing_factors = []

    # Track unique component codes to avoid duplicates in missing list
    checked_codes = set()

    for bom_item in all_bom_items:
        child_component = bom_item.child_product
        component_code = child_component.code

        # Check if component has matching emission factor (implicit matching)
        emission_factor = session.query(EmissionFactor).filter(
            EmissionFactor.activity_name == component_code
        ).first()

        if emission_factor is not None:
            components_with_factors += 1
        elif component_code not in checked_codes:
            # Only add to missing list once per unique code
            missing_factors.append(component_code)
            checked_codes.add(component_code)

    # Calculate coverage percentage
    coverage_percent = 0.0
    if total_components > 0:
        coverage_percent = (components_with_factors / total_components) * 100.0

    return {
        'total_components': total_components,
        'components_with_factors': components_with_factors,
        'coverage_percent': coverage_percent,
        'missing_factors': sorted(missing_factors)
    }


def _calculate_average_data_quality(session: Session) -> float:
    """
    Calculate average data quality rating from emission factors.

    Args:
        session: Database session

    Returns:
        float: Average data quality rating (or 0.0 if none)
    """
    # Calculate average of non-null data_quality_rating values
    avg_quality = session.query(
        func.avg(EmissionFactor.data_quality_rating)
    ).filter(
        EmissionFactor.data_quality_rating != None
    ).scalar()

    return float(avg_quality) if avg_quality is not None else 0.0


def _calculate_overall_quality_score(
    bom_coverage_percent: float,
    average_data_quality: float,
    valid_ranges: bool
) -> float:
    """
    Calculate overall quality score (1-5 scale).

    Formula:
    - BOM completeness (40%): coverage_percent / 20 (max 5.0)
    - Data quality ratings (40%): average_data_quality (0-5 scale)
    - Valid ranges (20%): 5.0 if all valid, 0.0 if any invalid

    Args:
        bom_coverage_percent: BOM coverage percentage (0-100)
        average_data_quality: Average data quality rating (0-5)
        valid_ranges: Whether all emission factors have valid ranges

    Returns:
        float: Overall quality score (1-5)
    """
    bom_score = (bom_coverage_percent / 20)  # Max 5.0 when 100%
    quality_score = average_data_quality  # Already on 0-5 scale
    valid_score = 5.0 if valid_ranges else 0.0  # Scale to 0-5

    # Weighted average
    overall_score = (
        (bom_score * 0.4) +
        (quality_score * 0.4) +
        (valid_score * 0.2)
    )

    # Clamp to 1-5 range
    return max(1.0, min(5.0, overall_score))


def main():
    """Main entry point for CLI execution"""
    import json

    # Connect to database
    db_path = backend_dir / "pcf_calculator.db"
    engine = create_engine(f"sqlite:///{db_path}")

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Enable foreign key constraints
        session.execute("PRAGMA foreign_keys = ON")
        session.commit()

        print("Running data quality validation...")
        quality_report = validate_data_quality(session)

        # Pretty print report
        print("\n" + "=" * 80)
        print("DATA QUALITY VALIDATION REPORT")
        print("=" * 80)
        print(json.dumps(quality_report, indent=2, default=str))
        print("=" * 80)

        # Summary
        print(f"\nOverall Quality Score: {quality_report['overall_quality_score']:.2f}/5.0")
        print(f"BOM Coverage: {quality_report['bom_completeness']['coverage_percent']:.1f}%")
        print(f"Emission Factors: {quality_report['emission_factors']['count']}")
        print(f"Validation Errors: {quality_report['validation_errors']}")

        if quality_report['bom_completeness']['missing_factors']:
            print(f"\nWARNING: Missing emission factors for:")
            for code in quality_report['bom_completeness']['missing_factors']:
                print(f"  - {code}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
