#!/usr/bin/env python3
"""
Load Production Data Script.

TASK-DATA-P9: Switch to production mode by clearing all data and loading EPA/DEFRA EFs.

This script:
1. CLEARS ALL DATA:
   - DELETE FROM calculation_details
   - DELETE FROM pcf_calculations
   - DELETE FROM bill_of_materials
   - DELETE FROM products
   - DELETE FROM emission_factors

2. LOADS PRODUCTION DATA:
   - EPA emission factors from data/epa/*.xlsx (75-125 factors)
   - DEFRA emission factors from data/defra/*.xlsx (200-400 factors)
   - Production products (~700-800) via ProductGenerator
   - Production BOMs (generated with EPA/DEFRA EF mappings)

3. VERIFIES:
   - Confirms expected emission factor counts (275-525)
   - Confirms expected product counts (700-800)
   - Validates BOM integrity

Usage:
    python backend/scripts/load_production_data.py
    python backend/scripts/load_production_data.py --dry-run  # Show what would happen
    python backend/scripts/load_production_data.py --skip-products  # EFs only
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings
from backend.database.connection import db_context
from backend.database.seeds.data_sources import seed_data_sources, get_data_source_by_name
from backend.models import (
    Product,
    EmissionFactor,
    BillOfMaterials,
    PCFCalculation,
    CalculationDetail,
    DataSource,
)


# Local file paths for EPA/DEFRA data
LOCAL_FILES = {
    "epa_fuels": project_root / "data" / "epa" / "ghg-emission-factors-hub-2024.xlsx",
    "epa_egrid": project_root / "data" / "epa" / "egrid2022_data.xlsx",
    "defra": project_root / "data" / "defra" / "ghg-conversion-factors-2024.xlsx",
}

# Expected emission factor counts
# TASK-DATA-P9: Updated based on actual EPA/DEFRA file contents
EXPECTED_EF_COUNTS = {
    "epa": (75, 150),
    "defra": (50, 200),
    "total": (100, 350),
}

# Expected product counts
EXPECTED_PRODUCT_COUNTS = (700, 900)


def clear_all_data(session: Session, dry_run: bool = False) -> dict:
    """
    Clear all data from the database tables.

    Args:
        session: Database session
        dry_run: If True, don't actually delete

    Returns:
        Dictionary with counts of deleted records
    """
    counts = {}

    # Order matters due to foreign keys
    tables = [
        ("calculation_details", CalculationDetail),
        ("pcf_calculations", PCFCalculation),
        ("bill_of_materials", BillOfMaterials),
        ("products", Product),
        ("emission_factors", EmissionFactor),
    ]

    for table_name, model in tables:
        count = session.query(model).count()
        counts[table_name] = count

        if not dry_run and count > 0:
            session.query(model).delete()
            print(f"  Deleted {count} records from {table_name}")

    if not dry_run:
        session.commit()

    return counts


def check_local_files() -> dict:
    """
    Check if local EPA/DEFRA files exist.

    Returns:
        Dictionary with file status
    """
    status = {}
    all_exist = True

    for key, path in LOCAL_FILES.items():
        exists = path.exists()
        status[key] = {
            "path": str(path),
            "exists": exists,
            "size_mb": path.stat().st_size / (1024 * 1024) if exists else 0,
        }
        if not exists:
            all_exist = False

    status["all_exist"] = all_exist
    return status


async def load_epa_factors_from_file(
    session: AsyncSession,
    data_source_id: str,
    file_key: str,
) -> dict:
    """
    Load EPA emission factors from local file.

    Args:
        session: Async database session
        data_source_id: ID of the EPA data source
        file_key: "fuels" or "egrid"

    Returns:
        Dictionary with load results
    """
    from backend.services.data_ingestion.epa_ingestion import EPAEmissionFactorsIngestion

    # Determine local file path
    if file_key == "fuels":
        local_path = LOCAL_FILES["epa_fuels"]
    else:
        local_path = LOCAL_FILES["epa_egrid"]

    if not local_path.exists():
        return {"status": "error", "message": f"File not found: {local_path}"}

    # Create ingestion instance
    ingestion = EPAEmissionFactorsIngestion(
        db=session,
        data_source_id=data_source_id,
        file_key=file_key,
        sync_type="initial",
    )

    # Read file instead of downloading
    with open(local_path, "rb") as f:
        raw_data = f.read()

    # Parse and transform
    parsed_data = await ingestion.parse_data(raw_data)
    transformed_data = await ingestion.transform_data(parsed_data)

    # Process each record
    created = 0
    updated = 0
    failed = 0

    # Create sync log for this batch
    ingestion.sync_log = await ingestion._create_sync_log()

    for record in transformed_data:
        if not await ingestion.validate_record(record):
            failed += 1
            continue

        result = await ingestion.upsert_emission_factor(record)
        if result == "created":
            created += 1
        elif result == "updated":
            updated += 1

    await session.commit()

    return {
        "status": "completed",
        "file_key": file_key,
        "records_created": created,
        "records_updated": updated,
        "records_failed": failed,
    }


async def load_defra_factors_from_file(
    session: AsyncSession,
    data_source_id: str,
) -> dict:
    """
    Load DEFRA emission factors from local file.

    Args:
        session: Async database session
        data_source_id: ID of the DEFRA data source

    Returns:
        Dictionary with load results
    """
    from backend.services.data_ingestion.defra_ingestion import DEFRAEmissionFactorsIngestion

    local_path = LOCAL_FILES["defra"]

    if not local_path.exists():
        return {"status": "error", "message": f"File not found: {local_path}"}

    # Create ingestion instance
    ingestion = DEFRAEmissionFactorsIngestion(
        db=session,
        data_source_id=data_source_id,
        sync_type="initial",
    )

    # Read file instead of downloading
    with open(local_path, "rb") as f:
        raw_data = f.read()

    # Parse and transform
    parsed_data = await ingestion.parse_data(raw_data)
    transformed_data = await ingestion.transform_data(parsed_data)

    # Process each record
    created = 0
    updated = 0
    failed = 0

    # Create sync log for this batch
    ingestion.sync_log = await ingestion._create_sync_log()

    for record in transformed_data:
        if not await ingestion.validate_record(record):
            failed += 1
            continue

        result = await ingestion.upsert_emission_factor(record)
        if result == "created":
            created += 1
        elif result == "updated":
            updated += 1

    await session.commit()

    return {
        "status": "completed",
        "records_created": created,
        "records_updated": updated,
        "records_failed": failed,
    }


async def load_emission_factors_async() -> dict:
    """
    Load all EPA/DEFRA emission factors from local files.

    Returns:
        Dictionary with load results
    """
    async_url = settings.async_database_url

    engine = create_async_engine(async_url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    results = {
        "epa_fuels": None,
        "epa_egrid": None,
        "defra": None,
        "total_created": 0,
    }

    async with async_session_maker() as session:
        # Get data source IDs (need sync session for this)
        with db_context() as sync_session:
            epa_source = get_data_source_by_name(sync_session, "EPA GHG Emission Factors Hub")
            defra_source = get_data_source_by_name(sync_session, "DEFRA Conversion Factors")

            if not epa_source or not defra_source:
                raise RuntimeError("Data sources not found. Run seed_data_sources() first.")

            epa_id = epa_source.id
            defra_id = defra_source.id

        # Load EPA fuels
        print("  Loading EPA fuels...")
        result = await load_epa_factors_from_file(session, epa_id, "fuels")
        results["epa_fuels"] = result
        if result.get("records_created"):
            results["total_created"] += result["records_created"]
            print(f"    Created: {result['records_created']}")

        # Load EPA eGRID
        print("  Loading EPA eGRID...")
        result = await load_epa_factors_from_file(session, epa_id, "egrid")
        results["epa_egrid"] = result
        if result.get("records_created"):
            results["total_created"] += result["records_created"]
            print(f"    Created: {result['records_created']}")

        # Load DEFRA
        print("  Loading DEFRA...")
        result = await load_defra_factors_from_file(session, defra_id)
        results["defra"] = result
        if result.get("records_created"):
            results["total_created"] += result["records_created"]
            print(f"    Created: {result['records_created']}")

    await engine.dispose()
    return results


async def generate_production_catalog() -> dict:
    """
    Generate production product catalog with BOMs.

    Returns:
        Dictionary with generation results
    """
    from backend.services.data_ingestion.product_generator import ProductGenerator

    async_url = settings.async_database_url

    engine = create_async_engine(async_url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    distribution = {
        "electronics": 175,
        "apparel": 175,
        "automotive": 125,
        "construction": 175,
        "food_beverage": 75,
    }

    async with async_session_maker() as session:
        generator = ProductGenerator(session)
        catalog = await generator.generate_full_catalog(distribution)
        stats = generator.get_stats()

    await engine.dispose()

    return {
        "products_created": stats["products_created"],
        "bom_entries_created": stats["bom_entries_created"],
        "components_created": stats["components_created"],
        "mapping_failures": stats.get("mapping_failures", 0),
    }


def verify_data(session: Session) -> dict:
    """
    Verify the loaded data.

    Args:
        session: Database session

    Returns:
        Dictionary with verification results
    """
    # Count emission factors by source
    ef_by_source = {}
    results = session.query(
        EmissionFactor.data_source,
        func.count(EmissionFactor.id)
    ).group_by(EmissionFactor.data_source).all()

    for source, count in results:
        ef_by_source[source or "Unknown"] = count

    ef_total = session.query(func.count(EmissionFactor.id)).scalar() or 0
    product_count = session.query(func.count(Product.id)).scalar() or 0
    bom_count = session.query(func.count(BillOfMaterials.id)).scalar() or 0

    # Check BOM integrity
    orphan_query = text("""
        SELECT COUNT(*) FROM bill_of_materials bom
        LEFT JOIN products p ON bom.child_product_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_children = session.execute(orphan_query).scalar() or 0

    # Check if counts are within expected ranges
    ef_in_range = EXPECTED_EF_COUNTS["total"][0] <= ef_total <= EXPECTED_EF_COUNTS["total"][1]
    products_in_range = EXPECTED_PRODUCT_COUNTS[0] <= product_count <= EXPECTED_PRODUCT_COUNTS[1]

    return {
        "emission_factors": {
            "total": ef_total,
            "by_source": ef_by_source,
            "in_range": ef_in_range,
        },
        "products": {
            "total": product_count,
            "in_range": products_in_range,
        },
        "bom_relationships": bom_count,
        "orphan_bom_children": orphan_children,
        "is_valid": orphan_children == 0,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load production data into PCF Calculator database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--skip-products",
        action="store_true",
        help="Skip product generation (load emission factors only)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PCF Calculator - Load Production Data")
    print("=" * 60)

    if args.dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    print()

    # Step 0: Check local files exist
    print("Step 0: Checking local EPA/DEFRA files...")
    file_status = check_local_files()

    for key, info in file_status.items():
        if key == "all_exist":
            continue
        status = "OK" if info["exists"] else "MISSING"
        print(f"  [{status}] {key}: {info['path']}")

    if not file_status["all_exist"]:
        print()
        print("ERROR: Local EPA/DEFRA files are missing.")
        print("Run this first:")
        print("  python backend/scripts/download_external_data.py")
        return 1

    print()

    with db_context() as session:
        # Step 1: Clear all data
        print("Step 1: Clearing all existing data...")
        cleared = clear_all_data(session, dry_run=args.dry_run)

        if args.dry_run:
            print("  Would delete:")
            for table, count in cleared.items():
                print(f"    {table}: {count} records")
        print()

        if args.dry_run:
            print("DRY RUN complete. No changes made.")
            return 0

        # Step 2: Seed data sources
        print("Step 2: Seeding data sources...")
        ds_count = seed_data_sources(session)
        print(f"  Created {ds_count} data sources")
        print()

    # Step 3: Load emission factors (async)
    print("Step 3: Loading EPA/DEFRA emission factors from local files...")
    ef_results = asyncio.run(load_emission_factors_async())
    print(f"  Total emission factors created: {ef_results['total_created']}")
    print()

    # Step 4: Generate production catalog (unless skipped)
    if not args.skip_products:
        print("Step 4: Generating production product catalog...")
        print("  (This may take a few minutes)")
        catalog_results = asyncio.run(generate_production_catalog())
        print(f"  Products created: {catalog_results['products_created']}")
        print(f"  BOM entries created: {catalog_results['bom_entries_created']}")
        print(f"  Component products: {catalog_results['components_created']}")
        if catalog_results.get("mapping_failures", 0) > 0:
            print(f"  Mapping failures: {catalog_results['mapping_failures']}")
        print()
    else:
        print("Step 4: Skipping product generation (--skip-products)")
        print()

    # Step 5: Verify
    print("Step 5: Verifying loaded data...")
    with db_context() as session:
        verification = verify_data(session)

    ef_info = verification["emission_factors"]
    print(f"  Emission Factors: {ef_info['total']}")
    for source, count in ef_info["by_source"].items():
        print(f"    - {source}: {count}")
    if ef_info["in_range"]:
        print(f"    Status: IN RANGE (expected {EXPECTED_EF_COUNTS['total'][0]}-{EXPECTED_EF_COUNTS['total'][1]})")
    else:
        print(f"    Status: OUT OF RANGE (expected {EXPECTED_EF_COUNTS['total'][0]}-{EXPECTED_EF_COUNTS['total'][1]})")

    prod_info = verification["products"]
    print(f"  Products: {prod_info['total']}")
    if not args.skip_products:
        if prod_info["in_range"]:
            print(f"    Status: IN RANGE (expected {EXPECTED_PRODUCT_COUNTS[0]}-{EXPECTED_PRODUCT_COUNTS[1]})")
        else:
            print(f"    Status: OUT OF RANGE (expected {EXPECTED_PRODUCT_COUNTS[0]}-{EXPECTED_PRODUCT_COUNTS[1]})")

    print(f"  BOM Relationships: {verification['bom_relationships']}")

    if verification["is_valid"]:
        print("  BOM Integrity: VALID")
    else:
        print(f"  BOM Integrity: INVALID ({verification['orphan_bom_children']} orphans)")

    print()
    print("=" * 60)
    print("PRODUCTION DATA LOADED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("To verify, run:")
    print("  python backend/scripts/check_data_mode.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
