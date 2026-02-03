#!/usr/bin/env python3
"""
Deduplicate Products Script

This script removes duplicate products from the database, keeping only
the first occurrence of each product name. It also properly handles
cascading deletes for associated BOM items.

Usage:
    cd backend && python scripts/deduplicate_products.py

    # Dry run (default) - shows what would be deleted
    python scripts/deduplicate_products.py --dry-run

    # Actually delete duplicates
    python scripts/deduplicate_products.py --execute
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.connection import SessionLocal


@contextmanager
def get_db_session():
    """Get a database session as a context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def find_duplicate_products(db):
    """Find all products with duplicate names, keeping the oldest (lowest id) one."""
    query = text("""
        WITH ranked AS (
            SELECT
                id,
                name,
                code,
                is_finished_product,
                ROW_NUMBER() OVER (PARTITION BY name ORDER BY id) as rn
            FROM products
            WHERE deleted_at IS NULL
        )
        SELECT id, name, code, is_finished_product
        FROM ranked
        WHERE rn > 1
        ORDER BY name, id
    """)
    return db.execute(query).fetchall()


def count_bom_items_for_products(db, product_ids: list):
    """Count BOM items that would be affected."""
    if not product_ids:
        return 0

    # SQLite-compatible: build IN clause with placeholders
    placeholders = ', '.join([f':id{i}' for i in range(len(product_ids))])
    params = {f'id{i}': pid for i, pid in enumerate(product_ids)}

    query = text(f"""
        SELECT COUNT(*) FROM bill_of_materials
        WHERE parent_product_id IN ({placeholders}) OR child_product_id IN ({placeholders})
    """)
    result = db.execute(query, params).scalar()
    return result or 0


def delete_duplicate_products(db, product_ids: list):
    """Delete products and their associated records from all referencing tables."""
    if not product_ids:
        return 0, 0

    # SQLite-compatible: build IN clause with placeholders
    placeholders = ', '.join([f':id{i}' for i in range(len(product_ids))])
    params = {f'id{i}': pid for i, pid in enumerate(product_ids)}

    total_related_deleted = 0

    # Delete calculation_details referencing these products as components
    calc_details_query = text(f"""
        DELETE FROM calculation_details
        WHERE component_id IN ({placeholders})
    """)
    calc_details_result = db.execute(calc_details_query, params)
    total_related_deleted += calc_details_result.rowcount

    # Delete pcf_calculations for these products
    pcf_calc_query = text(f"""
        DELETE FROM pcf_calculations
        WHERE product_id IN ({placeholders})
    """)
    pcf_calc_result = db.execute(pcf_calc_query, params)
    total_related_deleted += pcf_calc_result.rowcount

    # Delete BOM items where this product is the parent OR child
    bom_query = text(f"""
        DELETE FROM bill_of_materials
        WHERE parent_product_id IN ({placeholders}) OR child_product_id IN ({placeholders})
    """)
    bom_result = db.execute(bom_query, params)
    total_related_deleted += bom_result.rowcount

    # Finally delete the products
    product_query = text(f"""
        DELETE FROM products
        WHERE id IN ({placeholders})
    """)
    product_result = db.execute(product_query, params)
    products_deleted = product_result.rowcount

    return products_deleted, total_related_deleted


def get_stats(db):
    """Get current database statistics."""
    stats = {}

    # Total products
    stats['total_products'] = db.execute(
        text("SELECT COUNT(*) FROM products WHERE deleted_at IS NULL")
    ).scalar()

    # Unique product names
    stats['unique_names'] = db.execute(
        text("SELECT COUNT(DISTINCT name) FROM products WHERE deleted_at IS NULL")
    ).scalar()

    # Finished products
    stats['finished_products'] = db.execute(
        text("SELECT COUNT(*) FROM products WHERE deleted_at IS NULL AND is_finished_product = true")
    ).scalar()

    # Products with BOMs
    stats['products_with_bom'] = db.execute(
        text("""
            SELECT COUNT(DISTINCT parent_product_id)
            FROM bill_of_materials bom
            JOIN products p ON bom.parent_product_id = p.id
            WHERE p.deleted_at IS NULL AND p.is_finished_product = true
        """)
    ).scalar()

    # Total BOM items
    stats['total_bom_items'] = db.execute(
        text("SELECT COUNT(*) FROM bill_of_materials")
    ).scalar()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Deduplicate products in the database")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the deletion (default is dry-run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be deleted without making changes (default)"
    )
    args = parser.parse_args()

    # If --execute is passed, dry_run is False
    dry_run = not args.execute

    print("=" * 60)
    print("Product Deduplication Script")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will delete)'}")
    print()

    with get_db_session() as db:
        # Get current stats
        print("Current Database Statistics:")
        print("-" * 40)
        stats_before = get_stats(db)
        for key, value in stats_before.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print()

        # Find duplicates
        duplicates = find_duplicate_products(db)

        if not duplicates:
            print("No duplicate products found. Database is clean.")
            return

        # Group by name for reporting
        by_name = {}
        for row in duplicates:
            name = row[1]
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(row)

        print(f"Found {len(duplicates)} duplicate products across {len(by_name)} names:")
        print("-" * 40)

        # Show top 10 most duplicated
        sorted_names = sorted(by_name.items(), key=lambda x: -len(x[1]))[:10]
        for name, rows in sorted_names:
            print(f"  {len(rows)+1}x '{name}' (keeping 1, removing {len(rows)})")

        if len(by_name) > 10:
            print(f"  ... and {len(by_name) - 10} more product names with duplicates")

        print()

        # Get product IDs to delete
        product_ids = [row[0] for row in duplicates]

        # Count affected BOM items
        bom_count = count_bom_items_for_products(db, product_ids)

        print(f"Will delete:")
        print(f"  - {len(product_ids)} duplicate products")
        print(f"  - {bom_count} associated BOM items")
        print()

        if dry_run:
            print("DRY RUN - No changes made.")
            print("Run with --execute to actually delete duplicates.")
        else:
            print("Executing deletion...")
            products_deleted, bom_deleted = delete_duplicate_products(db, product_ids)
            db.commit()

            print(f"Deleted {products_deleted} products and {bom_deleted} BOM items.")
            print()

            # Get stats after
            print("Database Statistics After Cleanup:")
            print("-" * 40)
            stats_after = get_stats(db)
            for key, value in stats_after.items():
                before = stats_before[key]
                diff = value - before
                diff_str = f" ({diff:+d})" if diff != 0 else ""
                print(f"  {key.replace('_', ' ').title()}: {value}{diff_str}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
