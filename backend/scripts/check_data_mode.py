#!/usr/bin/env python3
"""
Check Data Mode Script.

TASK-DATA-P9: Report current database state and determine data mode.

This script queries the database and determines whether it contains:
- Test Mode: ~23 EFs, ~16 products, test BOMs
- Production Mode: ~275-525 EFs, ~700-800 products, production BOMs
- Empty: No data loaded
- Unknown/Mixed: Data doesn't match expected patterns

Usage:
    python backend/scripts/check_data_mode.py
    python backend/scripts/check_data_mode.py --verbose  # Show detailed breakdown
    python backend/scripts/check_data_mode.py --json     # Output as JSON
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.database.connection import db_context
from backend.models import (
    EmissionFactor,
    Product,
    BillOfMaterials,
    PCFCalculation,
)


# Expected data ranges for each mode
# TASK-DATA-P9: Updated ranges based on actual EPA/DEFRA data
MODES = {
    "test": {
        "ef_min": 20,
        "ef_max": 50,
        "product_min": 10,
        "product_max": 50,
        "description": "Test data (23 EFs + ~16 products + test BOMs)",
    },
    "production": {
        "ef_min": 100,
        "ef_max": 600,
        "product_min": 500,
        "product_max": 1000,
        "description": "Production data (EPA/DEFRA EFs + ~700 products)",
    },
}


def get_counts(session: Session) -> dict:
    """
    Get counts of all major entities in the database.

    Args:
        session: Database session

    Returns:
        Dictionary with entity counts
    """
    ef_count = session.query(func.count(EmissionFactor.id)).scalar() or 0
    product_count = session.query(func.count(Product.id)).scalar() or 0
    bom_count = session.query(func.count(BillOfMaterials.id)).scalar() or 0
    calc_count = session.query(func.count(PCFCalculation.id)).scalar() or 0

    # Get finished product count
    finished_count = session.query(func.count(Product.id)).filter(
        Product.is_finished_product == True  # noqa: E712
    ).scalar() or 0

    return {
        "emission_factors": ef_count,
        "products": product_count,
        "finished_products": finished_count,
        "component_products": product_count - finished_count,
        "bom_relationships": bom_count,
        "pcf_calculations": calc_count,
    }


def get_ef_breakdown(session: Session) -> dict:
    """
    Get emission factor breakdown by data source.

    Args:
        session: Database session

    Returns:
        Dictionary with counts per data source
    """
    # Group by data_source
    results = session.query(
        EmissionFactor.data_source,
        func.count(EmissionFactor.id)
    ).group_by(
        EmissionFactor.data_source
    ).all()

    breakdown = {}
    for source, count in results:
        source_name = source if source else "Unknown"
        breakdown[source_name] = count

    return breakdown


def get_product_breakdown(session: Session) -> dict:
    """
    Get product breakdown by type.

    Args:
        session: Database session

    Returns:
        Dictionary with product type counts
    """
    # Count finished vs component products
    finished = session.query(func.count(Product.id)).filter(
        Product.is_finished_product == True  # noqa: E712
    ).scalar() or 0

    components = session.query(func.count(Product.id)).filter(
        Product.is_finished_product == False  # noqa: E712
    ).scalar() or 0

    return {
        "finished_products": finished,
        "component_products": components,
    }


def check_bom_integrity(session: Session) -> dict:
    """
    Check BOM integrity - verify all BOMs reference valid products.

    Args:
        session: Database session

    Returns:
        Dictionary with integrity check results
    """
    # Count BOMs with missing parent products
    orphan_parent_query = text("""
        SELECT COUNT(*) FROM bill_of_materials bom
        LEFT JOIN products p ON bom.parent_product_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_parents = session.execute(orphan_parent_query).scalar() or 0

    # Count BOMs with missing child products
    orphan_child_query = text("""
        SELECT COUNT(*) FROM bill_of_materials bom
        LEFT JOIN products p ON bom.child_product_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_children = session.execute(orphan_child_query).scalar() or 0

    total_boms = session.query(func.count(BillOfMaterials.id)).scalar() or 0

    return {
        "total_boms": total_boms,
        "orphan_parents": orphan_parents,
        "orphan_children": orphan_children,
        "is_valid": orphan_parents == 0 and orphan_children == 0,
    }


def determine_mode(counts: dict) -> str:
    """
    Determine the current data mode based on counts.

    Args:
        counts: Dictionary with entity counts

    Returns:
        Mode string: "test", "production", "empty", or "unknown"
    """
    ef_count = counts["emission_factors"]
    product_count = counts["products"]

    if ef_count == 0 and product_count == 0:
        return "empty"

    # Check if matches test mode
    test_cfg = MODES["test"]
    if (test_cfg["ef_min"] <= ef_count <= test_cfg["ef_max"] and
            test_cfg["product_min"] <= product_count <= test_cfg["product_max"]):
        return "test"

    # Check if matches production mode
    prod_cfg = MODES["production"]
    if (prod_cfg["ef_min"] <= ef_count <= prod_cfg["ef_max"] and
            prod_cfg["product_min"] <= product_count <= prod_cfg["product_max"]):
        return "production"

    return "unknown"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check current data mode in PCF Calculator database"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed breakdown",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    with db_context() as session:
        counts = get_counts(session)
        mode = determine_mode(counts)
        ef_breakdown = get_ef_breakdown(session)
        product_breakdown = get_product_breakdown(session)
        bom_integrity = check_bom_integrity(session)

    # Build output data
    output = {
        "mode": mode,
        "counts": counts,
        "ef_breakdown": ef_breakdown,
        "product_breakdown": product_breakdown,
        "bom_integrity": bom_integrity,
    }

    if args.json:
        print(json.dumps(output, indent=2))
        return 0

    # Text output
    print("=" * 60)
    print("PCF Calculator - Data Mode Check")
    print("=" * 60)
    print()

    # Mode determination
    if mode == "empty":
        print("MODE: EMPTY")
        print("  No data loaded in the database.")
        print()
        print("To load data, run one of:")
        print("  python backend/scripts/load_test_data.py")
        print("  python backend/scripts/load_production_data.py")
    elif mode == "test":
        print("MODE: TEST")
        print(f"  {MODES['test']['description']}")
    elif mode == "production":
        print("MODE: PRODUCTION")
        print(f"  {MODES['production']['description']}")
    else:
        print("MODE: UNKNOWN")
        print("  Data doesn't match expected test or production patterns.")
        print("  Consider running load_test_data.py or load_production_data.py")

    print()
    print("-" * 60)
    print("ENTITY COUNTS")
    print("-" * 60)
    print(f"  Emission Factors: {counts['emission_factors']}")
    print(f"  Products: {counts['products']}")
    print(f"    - Finished: {counts['finished_products']}")
    print(f"    - Components: {counts['component_products']}")
    print(f"  BOM Relationships: {counts['bom_relationships']}")
    print(f"  PCF Calculations: {counts['pcf_calculations']}")

    if args.verbose or ef_breakdown:
        print()
        print("-" * 60)
        print("EMISSION FACTOR BREAKDOWN (by data source)")
        print("-" * 60)
        if ef_breakdown:
            for source, count in sorted(ef_breakdown.items()):
                print(f"  {source}: {count}")
        else:
            print("  No emission factors loaded")

    print()
    print("-" * 60)
    print("BOM INTEGRITY CHECK")
    print("-" * 60)
    if bom_integrity["is_valid"]:
        print(f"  Status: VALID")
        print(f"  Total BOMs: {bom_integrity['total_boms']}")
    else:
        print(f"  Status: INVALID")
        print(f"  Orphan parents: {bom_integrity['orphan_parents']}")
        print(f"  Orphan children: {bom_integrity['orphan_children']}")

    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
