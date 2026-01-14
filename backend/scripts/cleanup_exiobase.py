#!/usr/bin/env python3
"""
Database Cleanup Script: Remove Exiobase Data

This script removes all Exiobase-related data from the database:
1. Delete test product "Test EV Battery Housing (Exiobase)"
2. Delete emission_factors where data_source = "Exiobase"
3. Delete data_sources record where name = "Exiobase"
4. Delete data_source_licenses for Exiobase
5. Nullify BOM component references to deleted emission factors

Run from project root:
    python -m backend.scripts.cleanup_exiobase

    # Dry run (show what would be deleted)
    python -m backend.scripts.cleanup_exiobase --dry-run
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database.connection import db_context


def cleanup_exiobase(dry_run: bool = False) -> dict:
    """
    Remove all Exiobase-related data from the database.

    Args:
        dry_run: If True, show what would be deleted without making changes

    Returns:
        Dict with counts of deleted/affected records
    """
    results = {
        "products_deleted": 0,
        "emission_factors_deleted": 0,
        "data_sources_deleted": 0,
        "licenses_deleted": 0,
        "bom_items_updated": 0,
    }

    print("=" * 60)
    print("DATABASE CLEANUP: Remove Exiobase Data")
    print("=" * 60)

    if dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    print()

    with db_context() as session:
        # 1. Count and delete test product
        print("Step 1: Finding Exiobase test products...")
        product_count = session.execute(text("""
            SELECT COUNT(*) FROM products
            WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
        """)).scalar()
        print(f"  Found {product_count} Exiobase test product(s)")

        if not dry_run and product_count > 0:
            # Delete in order to respect foreign keys

            # 1. Delete calculation_details referencing these products
            session.execute(text("""
                DELETE FROM calculation_details
                WHERE component_id IN (
                    SELECT id FROM products
                    WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
                )
            """))

            # 2. Delete pcf_calculations for these products
            session.execute(text("""
                DELETE FROM pcf_calculations
                WHERE product_id IN (
                    SELECT id FROM products
                    WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
                )
            """))

            # 3. Delete BOM items for these products (as parent or child)
            session.execute(text("""
                DELETE FROM bill_of_materials
                WHERE parent_product_id IN (
                    SELECT id FROM products
                    WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
                )
                OR child_product_id IN (
                    SELECT id FROM products
                    WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
                )
            """))

            # 4. Finally delete the products
            session.execute(text("""
                DELETE FROM products
                WHERE name LIKE '%Exiobase%' OR code LIKE '%EXIO%'
            """))
            results["products_deleted"] = product_count
            print(f"  Deleted {product_count} product(s)")

        # 2. Count and delete Exiobase emission factors
        print("\nStep 2: Finding Exiobase emission factors...")
        ef_count = session.execute(text("""
            SELECT COUNT(*) FROM emission_factors
            WHERE data_source = 'Exiobase'
               OR data_source LIKE '%EXIOBASE%'
               OR data_source_id IN (
                   SELECT id FROM data_sources WHERE name LIKE '%Exiobase%'
               )
        """)).scalar()
        print(f"  Found {ef_count} Exiobase emission factor(s)")

        if not dry_run and ef_count > 0:
            # Delete the emission factors
            session.execute(text("""
                DELETE FROM emission_factors
                WHERE data_source = 'Exiobase'
                   OR data_source LIKE '%EXIOBASE%'
                   OR data_source_id IN (
                       SELECT id FROM data_sources WHERE name LIKE '%Exiobase%'
                   )
            """))
            results["emission_factors_deleted"] = ef_count
            print(f"  Deleted {ef_count} emission factor(s)")

        # 3. Count and delete Exiobase data source licenses (if table exists)
        print("\nStep 3: Finding Exiobase data source licenses...")
        try:
            license_count = session.execute(text("""
                SELECT COUNT(*) FROM data_source_licenses
                WHERE data_source_id IN (
                    SELECT id FROM data_sources WHERE name LIKE '%Exiobase%'
                )
            """)).scalar()
            print(f"  Found {license_count} Exiobase license(s)")

            if not dry_run and license_count > 0:
                session.execute(text("""
                    DELETE FROM data_source_licenses
                    WHERE data_source_id IN (
                        SELECT id FROM data_sources WHERE name LIKE '%Exiobase%'
                    )
                """))
                results["licenses_deleted"] = license_count
                print(f"  Deleted {license_count} license(s)")
        except Exception as e:
            if "no such table" in str(e).lower():
                print("  Table data_source_licenses does not exist - skipping")
            else:
                raise

        # 4. Count and delete Exiobase data source
        print("\nStep 4: Finding Exiobase data source...")
        ds_count = session.execute(text("""
            SELECT COUNT(*) FROM data_sources
            WHERE name LIKE '%Exiobase%'
        """)).scalar()
        print(f"  Found {ds_count} Exiobase data source(s)")

        if not dry_run and ds_count > 0:
            # Delete sync logs first (if table exists)
            try:
                session.execute(text("""
                    DELETE FROM data_sync_logs
                    WHERE data_source_id IN (
                        SELECT id FROM data_sources WHERE name LIKE '%Exiobase%'
                    )
                """))
            except Exception as e:
                if "no such table" not in str(e).lower():
                    raise
            # Then delete the data source
            session.execute(text("""
                DELETE FROM data_sources
                WHERE name LIKE '%Exiobase%'
            """))
            results["data_sources_deleted"] = ds_count
            print(f"  Deleted {ds_count} data source(s)")

        if not dry_run:
            session.commit()
            print("\nChanges committed to database.")
        else:
            print("\nDRY RUN: No changes made.")

    # Print summary
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"  Products deleted: {results['products_deleted']}")
    print(f"  Emission factors deleted: {results['emission_factors_deleted']}")
    print(f"  Data sources deleted: {results['data_sources_deleted']}")
    print(f"  Licenses deleted: {results['licenses_deleted']}")
    print(f"  BOM items updated: {results['bom_items_updated']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Remove all Exiobase data from the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes"
    )
    args = parser.parse_args()

    cleanup_exiobase(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
