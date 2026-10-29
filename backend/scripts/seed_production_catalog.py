#!/usr/bin/env python3
"""
Production Catalog Seeding Script

TASK-BE-P8-002: Product Catalog Generation (600-850 Products)

This script generates a complete product catalog with detailed BOMs across
5 industries using the BOM template system. Products have realistic component
structures that map to emission factors for carbon footprint calculations.

Product Distribution (Default: 725 total):
- Electronics: 175 products (E-*)
- Apparel: 175 products (A-*)
- Automotive: 125 products (U-*)
- Construction: 175 products (C-*)
- Food & Beverage: 75 products (F-*)

Usage:
    # Dry run (preview only, no database changes)
    python -m backend.scripts.seed_production_catalog --dry-run

    # Full generation
    python -m backend.scripts.seed_production_catalog

    # Custom distribution
    python -m backend.scripts.seed_production_catalog --electronics=200 --apparel=150

    # Verbose output
    python -m backend.scripts.seed_production_catalog --verbose

Requirements:
    - Database must have emission factors loaded (run seed_data.py first)
    - Async database support (aiosqlite for SQLite, asyncpg for PostgreSQL)
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.models import Base, Product, BillOfMaterials, EmissionFactor
from backend.services.data_ingestion.product_generator import ProductGenerator
from backend.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Default product distribution (total: 725)
DEFAULT_DISTRIBUTION = {
    "electronics": 175,
    "apparel": 175,
    "automotive": 125,
    "construction": 175,
    "food_beverage": 75,
}


async def create_async_session() -> AsyncSession:
    """Create async database session."""
    async_url = settings.async_database_url

    engine = create_async_engine(
        async_url,
        echo=False,
    )

    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return async_session_maker()


async def check_prerequisites(session: AsyncSession) -> Dict[str, Any]:
    """
    Check that prerequisites are met for catalog generation.

    Args:
        session: Async database session

    Returns:
        Dict with prerequisite status

    Raises:
        RuntimeError: If critical prerequisites are not met
    """
    logger.info("Checking prerequisites...")

    # Count existing emission factors
    result = await session.execute(
        select(func.count()).select_from(EmissionFactor)
    )
    emission_factor_count = result.scalar()

    # Count existing products
    result = await session.execute(
        select(func.count()).select_from(Product)
    )
    existing_product_count = result.scalar()

    # Count existing BOMs
    result = await session.execute(
        select(func.count()).select_from(BillOfMaterials)
    )
    existing_bom_count = result.scalar()

    status = {
        "emission_factors": emission_factor_count,
        "existing_products": existing_product_count,
        "existing_boms": existing_bom_count,
        "prerequisites_met": emission_factor_count >= 10,
    }

    logger.info(f"  Emission factors: {emission_factor_count}")
    logger.info(f"  Existing products: {existing_product_count}")
    logger.info(f"  Existing BOMs: {existing_bom_count}")

    if not status["prerequisites_met"]:
        raise RuntimeError(
            "Not enough emission factors in database. "
            "Run seed_data.py first to load emission factors."
        )

    return status


async def seed_production_catalog(
    distribution: Dict[str, int],
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Generate production product catalog.

    Args:
        distribution: Dict mapping industry to product count
        dry_run: If True, simulate only without database changes
        verbose: If True, enable verbose logging

    Returns:
        Summary dict with generation results
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    total_target = sum(distribution.values())
    logger.info("=" * 60)
    logger.info("PRODUCTION CATALOG GENERATION")
    logger.info("=" * 60)
    logger.info(f"Target: {total_target} products")
    logger.info(f"Dry run: {dry_run}")
    logger.info("")

    for industry, count in distribution.items():
        logger.info(f"  {industry}: {count} products")

    logger.info("")

    if dry_run:
        logger.info("DRY RUN MODE - No database changes will be made")
        logger.info("")

        # Calculate expected statistics
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        expected_stats = {
            "total_products": total_target,
            "industries": list(distribution.keys()),
            "mode": "dry_run",
        }

        # Calculate expected component products
        unique_components = set()
        for industry in distribution.keys():
            if industry in ALL_TEMPLATES:
                for template in ALL_TEMPLATES[industry].values():
                    for comp in template.base_components:
                        unique_components.add(comp.name)
                    # Add transport components
                    unique_components.add("transport_truck")
                    unique_components.add("transport_ship")

        expected_stats["expected_component_products"] = len(unique_components)
        expected_stats["expected_bom_entries"] = total_target * 17  # Avg 17 per product

        logger.info("Expected Results (estimated):")
        logger.info(f"  Products: ~{expected_stats['total_products']}")
        logger.info(f"  Component products: ~{expected_stats['expected_component_products']}")
        logger.info(f"  BOM entries: ~{expected_stats['expected_bom_entries']}")

        return expected_stats

    # Real generation
    async with await create_async_session() as session:
        try:
            # Check prerequisites
            prereq_status = await check_prerequisites(session)

            # Create generator
            generator = ProductGenerator(session)

            # Generate catalog
            logger.info("Starting product generation...")
            catalog = await generator.generate_full_catalog(distribution)

            # Get final statistics
            stats = generator.get_stats()

            # Count final database state
            result = await session.execute(
                select(func.count()).select_from(Product)
            )
            final_product_count = result.scalar()

            result = await session.execute(
                select(func.count()).select_from(BillOfMaterials)
            )
            final_bom_count = result.scalar()

            # Summary
            logger.info("")
            logger.info("=" * 60)
            logger.info("GENERATION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Products created: {stats['products_created']}")
            logger.info(f"BOM entries created: {stats['bom_entries_created']}")
            logger.info(f"Component products: {stats['components_created']}")
            logger.info(f"Mapping failures: {stats['mapping_failures']}")
            logger.info("")
            logger.info("Products by Industry:")
            for industry, count in stats.get("by_industry", {}).items():
                logger.info(f"  {industry}: {count}")
            logger.info("")
            logger.info(f"Total products in database: {final_product_count}")
            logger.info(f"Total BOM entries in database: {final_bom_count}")

            return {
                "status": "success",
                "products_created": stats["products_created"],
                "bom_entries_created": stats["bom_entries_created"],
                "components_created": stats["components_created"],
                "mapping_failures": stats["mapping_failures"],
                "by_industry": stats["by_industry"],
                "final_product_count": final_product_count,
                "final_bom_count": final_bom_count,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error during generation: {e}")
            raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate production product catalog with detailed BOMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview what would be generated
    python -m backend.scripts.seed_production_catalog --dry-run

    # Full generation with defaults
    python -m backend.scripts.seed_production_catalog

    # Custom counts
    python -m backend.scripts.seed_production_catalog --electronics=200 --apparel=150
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--electronics",
        type=int,
        default=DEFAULT_DISTRIBUTION["electronics"],
        help=f"Electronics product count (default: {DEFAULT_DISTRIBUTION['electronics']})",
    )

    parser.add_argument(
        "--apparel",
        type=int,
        default=DEFAULT_DISTRIBUTION["apparel"],
        help=f"Apparel product count (default: {DEFAULT_DISTRIBUTION['apparel']})",
    )

    parser.add_argument(
        "--automotive",
        type=int,
        default=DEFAULT_DISTRIBUTION["automotive"],
        help=f"Automotive product count (default: {DEFAULT_DISTRIBUTION['automotive']})",
    )

    parser.add_argument(
        "--construction",
        type=int,
        default=DEFAULT_DISTRIBUTION["construction"],
        help=f"Construction product count (default: {DEFAULT_DISTRIBUTION['construction']})",
    )

    parser.add_argument(
        "--food-beverage",
        type=int,
        default=DEFAULT_DISTRIBUTION["food_beverage"],
        help=f"Food & Beverage product count (default: {DEFAULT_DISTRIBUTION['food_beverage']})",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    distribution = {
        "electronics": args.electronics,
        "apparel": args.apparel,
        "automotive": args.automotive,
        "construction": args.construction,
        "food_beverage": args.food_beverage,
    }

    try:
        result = asyncio.run(
            seed_production_catalog(
                distribution=distribution,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
        )

        if result.get("status") == "success":
            return 0

        return 0

    except RuntimeError as e:
        logger.error(f"Prerequisite error: {e}")
        return 1

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
