#!/usr/bin/env python3
"""
Load Test Data Script.

TASK-DATA-P9: Switch to test mode by clearing all data and loading test fixtures.

WARNING: This script is for LOCAL DEVELOPMENT ONLY.
         It will refuse to run in production environments (Railway).

This script:
1. CLEARS ALL DATA:
   - DELETE FROM calculation_details
   - DELETE FROM pcf_calculations
   - DELETE FROM bill_of_materials
   - DELETE FROM products
   - DELETE FROM emission_factors

2. LOADS TEST DATA:
   - 23 emission factors from data/emission_factors_simple.csv
   - ~16 test products from data/bom_*.json
   - Test BOMs from data/bom_*.json files

3. VERIFIES:
   - Confirms correct counts loaded
   - Validates BOM integrity

Usage:
    python backend/scripts/load_test_data.py
    python backend/scripts/load_test_data.py --dry-run  # Show what would happen
"""

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import db_context
from backend.database.seeds.data_sources import seed_data_sources
from backend.models import (
    Product,
    EmissionFactor,
    BillOfMaterials,
    PCFCalculation,
    CalculationDetail,
)


def clear_all_data(session: Session, dry_run: bool = False) -> dict:
    """
    Clear all data from the database tables.

    Clears in order to respect foreign key constraints.

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


def load_emission_factors(session: Session) -> int:
    """
    Load emission factors from CSV.

    Args:
        session: Database session

    Returns:
        Number of emission factors loaded
    """
    csv_path = project_root / "data" / "emission_factors_simple.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Emission factors CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    loaded_count = 0

    for _, row in df.iterrows():
        ef = EmissionFactor(
            activity_name=row['activity_name'],
            co2e_factor=Decimal(str(row['co2e_factor'])),
            unit=row['unit'],
            data_source=row['data_source'],
            geography=row['geography'],
        )
        session.add(ef)
        loaded_count += 1

    session.commit()
    return loaded_count


def get_or_create_component(session: Session, component_name: str, unit: str) -> Product:
    """
    Get or create a component product.

    Args:
        session: Database session
        component_name: Component code
        unit: Unit of measurement

    Returns:
        Product instance
    """
    component = session.query(Product).filter_by(code=component_name).first()

    if component:
        return component

    component = Product(
        code=component_name,
        name=component_name.replace('_', ' ').title(),
        unit=unit,
        is_finished_product=False,
    )
    session.add(component)
    session.flush()
    return component


def load_product_from_json(session: Session, json_path: Path) -> tuple:
    """
    Load a single product and its BOM from JSON file.

    Args:
        session: Database session
        json_path: Path to JSON BOM file

    Returns:
        Tuple of (Product, bom_count)
    """
    with open(json_path, 'r') as f:
        bom_data = json.load(f)

    product_data = bom_data['product']
    bom_items = bom_data.get('bill_of_materials', [])
    energy_data = bom_data.get('energy_data', {})
    transport_data = bom_data.get('transport_data', [])

    # Create product
    product = Product(
        code=product_data['code'],
        name=product_data['name'],
        unit=product_data['unit'],
        is_finished_product=product_data['is_finished_product'],
    )
    session.add(product)
    session.flush()

    bom_count = 0

    # Create BOM items for materials
    for item in bom_items:
        component = get_or_create_component(
            session,
            item['component_name'],
            item['unit'],
        )

        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=component.id,
            quantity=Decimal(str(item['quantity'])),
            unit=item['unit'],
            notes=item.get('description'),
        )
        session.add(bom)
        bom_count += 1

    # Add energy data as BOM component if present
    if energy_data and energy_data.get('electricity_kwh', 0) > 0:
        electricity = get_or_create_component(session, 'electricity_us', 'kWh')
        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=electricity.id,
            quantity=Decimal(str(energy_data['electricity_kwh'])),
            unit='kWh',
        )
        session.add(bom)
        bom_count += 1

    # Add transport data as BOM components
    for transport in transport_data:
        mode = transport['mode']
        distance_km = transport['distance_km']
        mass_kg = transport['mass_kg']
        tkm = (mass_kg * distance_km) / 1000

        component_name = f"transport_{mode}"
        transport_component = get_or_create_component(session, component_name, 'tkm')

        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=transport_component.id,
            quantity=Decimal(str(tkm)),
            unit='tkm',
        )
        session.add(bom)
        bom_count += 1

    session.commit()
    return product, bom_count


def load_products_and_boms(session: Session) -> tuple:
    """
    Load all test products and BOMs from JSON files.

    Args:
        session: Database session

    Returns:
        Tuple of (products_loaded, total_bom_items)
    """
    data_dir = project_root / "data"

    # List of BOM JSON files to load
    bom_files = [
        'bom_tshirt_realistic.json',
        'bom_water_bottle_realistic.json',
        'bom_phone_case_realistic.json',
        'bom_laptop.json',
        'bom_smartphone.json',
        'bom_desk_lamp.json',
        'bom_wireless_earbuds.json',
        'bom_running_shoes.json',
        'bom_backpack.json',
        'bom_sunglasses.json',
        'bom_bicycle_helmet.json',
        'bom_coffee_mug.json',
        'bom_yoga_mat.json',
    ]

    products_loaded = 0
    total_bom_items = 0

    for filename in bom_files:
        json_path = data_dir / filename

        if not json_path.exists():
            print(f"  Warning: BOM file not found: {json_path}")
            continue

        product, bom_count = load_product_from_json(session, json_path)
        products_loaded += 1
        total_bom_items += bom_count
        print(f"  Loaded: {product.code} ({bom_count} BOM items)")

    return products_loaded, total_bom_items


def verify_data(session: Session) -> dict:
    """
    Verify the loaded data.

    Args:
        session: Database session

    Returns:
        Dictionary with verification results
    """
    ef_count = session.query(EmissionFactor).count()
    product_count = session.query(Product).count()
    bom_count = session.query(BillOfMaterials).count()

    # Check BOM integrity
    orphan_query = text("""
        SELECT COUNT(*) FROM bill_of_materials bom
        LEFT JOIN products p ON bom.child_product_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_children = session.execute(orphan_query).scalar() or 0

    return {
        "emission_factors": ef_count,
        "products": product_count,
        "bom_relationships": bom_count,
        "orphan_bom_children": orphan_children,
        "is_valid": orphan_children == 0,
    }


def is_production_environment() -> bool:
    """
    Check if running in a production environment.

    Detects Railway and other production indicators.

    Returns:
        True if production environment detected
    """
    # Railway sets RAILWAY_ENVIRONMENT
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return True

    # Check for explicit production flag
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        return True

    # Check for Railway-specific variables
    if os.environ.get("RAILWAY_PROJECT_ID"):
        return True

    return False


def main() -> int:
    """Main entry point."""
    # SAFETY CHECK: Block execution in production environments
    if is_production_environment():
        print("=" * 60)
        print("ERROR: Cannot run load_test_data.py in production!")
        print("=" * 60)
        print()
        print("This script is for LOCAL DEVELOPMENT ONLY.")
        print("Test data should never be loaded in production.")
        print()
        print("Detected production environment indicators:")
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            print(f"  - RAILWAY_ENVIRONMENT={os.environ.get('RAILWAY_ENVIRONMENT')}")
        if os.environ.get("RAILWAY_PROJECT_ID"):
            print(f"  - RAILWAY_PROJECT_ID is set")
        if os.environ.get("ENVIRONMENT", "").lower() == "production":
            print(f"  - ENVIRONMENT={os.environ.get('ENVIRONMENT')}")
        print()
        print("If you need to reset production data, use load_production_data.py")
        return 1

    parser = argparse.ArgumentParser(
        description="Load test data into PCF Calculator database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PCF Calculator - Load Test Data")
    print("=" * 60)

    if args.dry_run:
        print("MODE: DRY RUN (no changes will be made)")
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

        # Step 2: Seed data sources (if needed)
        print("Step 2: Seeding data sources...")
        ds_count = seed_data_sources(session)
        print(f"  Created {ds_count} data sources")
        print()

        # Step 3: Load emission factors
        print("Step 3: Loading emission factors from CSV...")
        ef_count = load_emission_factors(session)
        print(f"  Loaded {ef_count} emission factors")
        print()

        # Step 4: Load products and BOMs
        print("Step 4: Loading products and BOMs from JSON...")
        products_loaded, bom_items = load_products_and_boms(session)
        print(f"  Loaded {products_loaded} products with {bom_items} BOM items")
        print()

        # Step 5: Verify
        print("Step 5: Verifying loaded data...")
        verification = verify_data(session)
        print(f"  Emission Factors: {verification['emission_factors']}")
        print(f"  Products: {verification['products']}")
        print(f"  BOM Relationships: {verification['bom_relationships']}")

        if verification['is_valid']:
            print("  BOM Integrity: VALID")
        else:
            print(f"  BOM Integrity: INVALID ({verification['orphan_bom_children']} orphans)")

    print()
    print("=" * 60)
    print("TEST DATA LOADED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("To verify, run:")
    print("  python backend/scripts/check_data_mode.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
