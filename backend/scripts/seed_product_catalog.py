"""
Seed script for product catalog data.

TASK-DATA-P5-005: Product Catalog Expansion

This script seeds the product catalog with categories and products.
It creates 800+ products across multiple industries for demonstration.

Usage:
    # Standalone seeding (uses DATABASE_URL from environment)
    python -m backend.scripts.seed_product_catalog

    # With options
    python -m backend.scripts.seed_product_catalog --products-per-category 5
"""

import sys
from pathlib import Path
from typing import Optional


def seed_catalog_sync(
    db_session,
    products_per_category: int = 3,
    min_category_level: int = 2,
    verbose: bool = True
) -> dict:
    """
    Seed the product catalog with categories and products.

    Args:
        db_session: SQLAlchemy Session
        products_per_category: Number of products per leaf category
        min_category_level: Minimum category level for product generation
        verbose: Print progress messages

    Returns:
        dict: Summary with 'categories' and 'products' counts
    """
    from backend.models import ProductCategory
    from backend.services.data_ingestion.sync_catalog_loader import SyncCatalogLoader

    # Check if database already has data
    existing_count = db_session.query(ProductCategory).count()
    if existing_count > 0:
        if verbose:
            print(f"Database already has {existing_count} categories, skipping seed")
        return {"categories": existing_count, "products": 0, "skipped": True}

    # Load the catalog
    loader = SyncCatalogLoader()
    result = loader.load_full_catalog(
        db_session,
        products_per_category=products_per_category,
        min_category_level=min_category_level
    )

    if verbose:
        print(f"Seeded database with {result['categories']} categories "
              f"and {result['products']} products")

    return result


def main():
    """CLI entry point for seeding a database."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed product catalog data")
    parser.add_argument(
        "--products-per-category",
        type=int,
        default=3,
        help="Number of products per leaf category (default: 3)"
    )
    parser.add_argument(
        "--min-level",
        type=int,
        default=2,
        help="Minimum category level for product generation (default: 2)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output messages"
    )

    args = parser.parse_args()

    # Use the standard database connection (reads DATABASE_URL from env)
    from backend.database.connection import db_context

    try:
        with db_context() as session:
            result = seed_catalog_sync(
                session,
                products_per_category=args.products_per_category,
                min_category_level=args.min_level,
                verbose=not args.quiet
            )

            if not args.quiet:
                print(f"\nSeed complete:")
                print(f"  Categories: {result['categories']}")
                print(f"  Products: {result['products']}")
                if result.get('skipped'):
                    print("  (Database already had data)")

    except Exception as e:
        print(f"Error seeding database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
