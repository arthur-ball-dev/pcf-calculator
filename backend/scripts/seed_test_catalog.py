"""
Seed script for product catalog test data.

TASK-DATA-P5-005: Product Catalog Expansion - Bug Fix

This script seeds the product catalog with categories and products
for integration testing. It can be run standalone or imported
as a pytest hook.

Usage:
    # Standalone seeding of a database
    python -m backend.scripts.seed_test_catalog --db-url sqlite:///test.db

    # Via pytest conftest hook
    pytest_plugins = ["backend.scripts.seed_test_catalog"]
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
        "--db-url",
        type=str,
        default="sqlite:///data/pcf_calculator.db",
        help="Database URL (default: sqlite:///data/pcf_calculator.db)"
    )
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

    # Create database connection
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.models import Base

    engine = create_engine(args.db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
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
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
