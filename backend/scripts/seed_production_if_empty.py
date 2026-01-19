#!/usr/bin/env python3
"""
Seed Production Data If Empty.

TASK-DATA-P9: Railway release command to auto-seed production data.

This script is designed to run as a Railway release command. It:
1. Checks if the database has emission factors loaded
2. If EMPTY → loads production EPA/DEFRA data
3. If NOT EMPTY → skips (preserves existing data)

This ensures Railway deployments always have production data,
while not overwriting data that's already been loaded.

Usage:
    python backend/scripts/seed_production_if_empty.py

Exit codes:
    0 - Success (either seeded or skipped)
    1 - Error during seeding
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func

from backend.database.connection import db_context
from backend.models import EmissionFactor, Product


def check_database_state() -> dict:
    """
    Check current database state.

    Returns:
        Dictionary with counts and empty status
    """
    with db_context() as session:
        ef_count = session.query(func.count(EmissionFactor.id)).scalar() or 0
        product_count = session.query(func.count(Product.id)).scalar() or 0

    return {
        "emission_factors": ef_count,
        "products": product_count,
        "is_empty": ef_count == 0,
    }


def is_railway_environment() -> bool:
    """
    Check if running on Railway.

    Returns:
        True if Railway environment detected
    """
    return bool(
        os.environ.get("RAILWAY_ENVIRONMENT") or
        os.environ.get("RAILWAY_PROJECT_ID")
    )


async def load_production_data_async() -> dict:
    """
    Load production EPA/DEFRA emission factors.

    This imports and runs the production data loading logic.

    Returns:
        Dictionary with load results
    """
    # Import here to avoid circular imports
    from backend.scripts.load_production_data import (
        check_local_files,
        clear_all_data,
        load_emission_factors_async,
        generate_production_catalog,
        verify_data,
    )
    from backend.database.connection import db_context
    from backend.database.seeds.data_sources import seed_data_sources

    # Check local files exist
    file_status = check_local_files()
    if not file_status["all_exist"]:
        missing = [k for k, v in file_status.items() if k != "all_exist" and not v.get("exists", True)]
        raise FileNotFoundError(
            f"EPA/DEFRA data files missing: {missing}. "
            "Run download_external_data.py first or include files in deployment."
        )

    # Clear existing data and seed data sources
    with db_context() as session:
        clear_all_data(session, dry_run=False)
        seed_data_sources(session)

    # Load emission factors
    ef_results = await load_emission_factors_async()

    # Generate production catalog
    catalog_results = await generate_production_catalog()

    # Verify
    with db_context() as session:
        verification = verify_data(session)

    return {
        "emission_factors_created": ef_results["total_created"],
        "products_created": catalog_results["products_created"],
        "bom_entries_created": catalog_results["bom_entries_created"],
        "verification": verification,
    }


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("PCF Calculator - Production Data Seeder")
    print("=" * 60)
    print()

    # Report environment
    if is_railway_environment():
        print("Environment: Railway Production")
        env_name = os.environ.get("RAILWAY_ENVIRONMENT", "unknown")
        print(f"  RAILWAY_ENVIRONMENT: {env_name}")
    else:
        print("Environment: Local/Development")
    print()

    # Check database state
    print("Step 1: Checking database state...")
    state = check_database_state()
    print(f"  Emission Factors: {state['emission_factors']}")
    print(f"  Products: {state['products']}")
    print()

    if not state["is_empty"]:
        print("=" * 60)
        print("DATABASE ALREADY HAS DATA - SKIPPING SEED")
        print("=" * 60)
        print()
        print("The database already contains emission factors.")
        print("To reload production data, run load_production_data.py manually.")
        print()
        return 0

    # Database is empty - seed production data
    print("Step 2: Database is empty - loading production data...")
    print()

    try:
        results = asyncio.run(load_production_data_async())

        print()
        print("-" * 60)
        print("SEEDING RESULTS")
        print("-" * 60)
        print(f"  Emission Factors: {results['emission_factors_created']}")
        print(f"  Products: {results['products_created']}")
        print(f"  BOM Entries: {results['bom_entries_created']}")

        verification = results["verification"]
        if verification["is_valid"]:
            print("  BOM Integrity: VALID")
        else:
            print(f"  BOM Integrity: INVALID ({verification['orphan_bom_children']} orphans)")

        print()
        print("=" * 60)
        print("PRODUCTION DATA SEEDED SUCCESSFULLY")
        print("=" * 60)
        return 0

    except FileNotFoundError as e:
        print()
        print("=" * 60)
        print("ERROR: Missing data files")
        print("=" * 60)
        print()
        print(str(e))
        print()
        print("For Railway deployments, ensure EPA/DEFRA files are included")
        print("in the deployment or accessible via environment configuration.")
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Failed to seed production data")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
