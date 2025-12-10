"""
Product Catalog Expansion Script.

TASK-DATA-P5-005: Product Catalog Expansion

This script orchestrates the expansion of the product catalog by:
1. Loading hierarchical categories from generated tree
2. Generating sample products for each leaf category
3. Updating full-text search vectors

Usage:
    # As module
    from backend.scripts.expand_product_catalog import expand_catalog
    await expand_catalog(db)

    # From command line (requires async context)
    python -m backend.scripts.expand_product_catalog
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.data_ingestion.category_loader import CategoryLoader
from backend.services.data_ingestion.product_generator import ProductGenerator
from backend.services.data_ingestion.fts_indexer import FullTextSearchIndexer
from backend.models import ProductCategory


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def expand_catalog(
    db: AsyncSession,
    products_per_category: int = 10,
    min_category_level: int = 2
) -> dict:
    """
    Main script to expand product catalog.

    This function orchestrates the full catalog expansion process:
    1. Load hierarchical categories from generated tree structure
    2. Generate products for leaf categories (level >= min_category_level)
    3. Update full-text search vectors for products and categories

    Args:
        db: AsyncSession database connection
        products_per_category: Number of products to generate per category
        min_category_level: Minimum category level for product generation

    Returns:
        dict: Summary with counts of categories, products, and FTS updates

    Example:
        async with get_async_session() as db:
            result = await expand_catalog(db)
            print(f"Loaded {result['categories']} categories")
            print(f"Generated {result['products']} products")
    """
    result = {
        "categories": 0,
        "products": 0,
        "fts_products": 0,
        "fts_categories": 0,
    }

    # Step 1: Load categories
    logger.info("Starting category loading...")
    loader = CategoryLoader()
    category_tree = loader.generate_category_tree()
    cat_count = await loader.load_categories_from_json(db, category_tree)
    result["categories"] = cat_count
    logger.info(f"Loaded {cat_count} categories")

    # Flush to ensure categories are available
    await db.flush()

    # Step 2: Generate products for leaf categories
    logger.info(f"Fetching leaf categories (level >= {min_category_level})...")
    categories_result = await db.execute(
        select(ProductCategory).where(ProductCategory.level >= min_category_level)
    )
    leaf_categories = categories_result.scalars().all()
    logger.info(f"Found {len(leaf_categories)} leaf categories")

    logger.info(f"Generating products ({products_per_category} per category)...")
    generator = ProductGenerator()
    prod_count = await generator.generate_products(
        db, leaf_categories, products_per_category=products_per_category
    )
    result["products"] = prod_count
    logger.info(f"Generated {prod_count} products")

    # Step 3: Update FTS vectors
    logger.info("Updating full-text search vectors...")
    indexer = FullTextSearchIndexer()
    result["fts_products"] = await indexer.update_product_vectors(db)
    result["fts_categories"] = await indexer.update_category_vectors(db)
    logger.info(f"Updated FTS vectors: {result['fts_products']} products, {result['fts_categories']} categories")

    # Commit all changes
    await db.commit()
    logger.info("Catalog expansion completed successfully")

    return result


async def main():
    """
    Command-line entry point for catalog expansion.

    Creates database connection and runs expand_catalog function.
    """
    from backend.database.connection import get_async_session

    logger.info("Product Catalog Expansion Script")
    logger.info("================================")

    async with get_async_session() as db:
        result = await expand_catalog(db)

    logger.info("")
    logger.info("Summary:")
    logger.info(f"  Categories loaded: {result['categories']}")
    logger.info(f"  Products generated: {result['products']}")
    logger.info(f"  FTS products updated: {result['fts_products']}")
    logger.info(f"  FTS categories updated: {result['fts_categories']}")


if __name__ == "__main__":
    asyncio.run(main())
