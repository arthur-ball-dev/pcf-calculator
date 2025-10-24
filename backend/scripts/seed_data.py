#!/usr/bin/env python3
"""
Seed Data Loading Script
TASK-DATA-003: Load emission factors from CSV and test products/BOMs from JSON

This script loads:
1. Emission factors from data/emission_factors_simple.csv (20 factors)
2. Test products and BOMs from data/bom_*.json (3 products)
3. Energy and transport data as BOM components

The script is idempotent - can be run multiple times safely.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import models
from backend.models import (
    Product,
    EmissionFactor,
    BillOfMaterials,
)
from backend.database.connection import db_context


def get_project_root() -> Path:
    """Get project root directory"""
    # Script is in backend/scripts/, so go up 2 levels
    return Path(__file__).parent.parent.parent


def load_emission_factors(session: Session) -> int:
    """
    Load emission factors from CSV into database.

    Args:
        session: Database session

    Returns:
        Number of new emission factors loaded
    """
    csv_path = get_project_root() / "data" / "emission_factors_simple.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Emission factors CSV not found: {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)

    loaded_count = 0

    for _, row in df.iterrows():
        # Check if already exists (idempotency)
        existing = session.query(EmissionFactor).filter_by(
            activity_name=row['activity_name'],
            data_source=row['data_source'],
            geography=row['geography']
        ).first()

        if existing:
            # Already exists, skip
            continue

        # Create new emission factor
        ef = EmissionFactor(
            activity_name=row['activity_name'],
            co2e_factor=Decimal(str(row['co2e_factor'])),
            unit=row['unit'],
            data_source=row['data_source'],
            geography=row['geography']
        )

        session.add(ef)
        loaded_count += 1

    session.commit()

    return loaded_count


def validate_bom_emission_factors(
    session: Session,
    bom_items: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Validate that all BOM components have corresponding emission factors.

    Args:
        session: Database session
        bom_items: List of BOM items from JSON

    Returns:
        Tuple of (is_valid, missing_components)
    """
    missing = []

    for item in bom_items:
        component_name = item['component_name']

        # Check if emission factor exists
        ef = session.query(EmissionFactor).filter_by(
            activity_name=component_name
        ).first()

        if not ef:
            missing.append(component_name)

    is_valid = len(missing) == 0
    return is_valid, missing


def get_or_create_component(
    session: Session,
    component_name: str,
    unit: str
) -> Product:
    """
    Get or create a component product.

    Args:
        session: Database session
        component_name: Component code (e.g., 'cotton', 'electricity_us')
        unit: Unit of measurement (must be in allowed list)

    Returns:
        Product instance
    """
    # Check if exists
    component = session.query(Product).filter_by(code=component_name).first()

    if component:
        return component

    # Create new component (unit is now validated to include 'tkm')
    component = Product(
        code=component_name,
        name=component_name.replace('_', ' ').title(),
        unit=unit,
        is_finished_product=False
    )

    session.add(component)
    session.flush()  # Ensure component has an ID before returning

    return component


def load_product_from_json(
    session: Session,
    json_path: Path
) -> Tuple[Optional[Product], int]:
    """
    Load a single product and its BOM from JSON file.

    Args:
        session: Database session
        json_path: Path to JSON BOM file

    Returns:
        Tuple of (Product, number of BOM items created)
    """
    if not json_path.exists():
        raise FileNotFoundError(f"BOM JSON not found: {json_path}")

    with open(json_path, 'r') as f:
        bom_data = json.load(f)

    product_data = bom_data['product']
    bom_items = bom_data.get('bill_of_materials', [])
    energy_data = bom_data.get('energy_data', {})
    transport_data = bom_data.get('transport_data', [])

    # Validate BOM components have emission factors
    is_valid, missing = validate_bom_emission_factors(session, bom_items)
    if not is_valid:
        print(f"Warning: Missing emission factors for: {missing}")

    # Check if product already exists (idempotency)
    existing_product = session.query(Product).filter_by(
        code=product_data['code']
    ).first()

    if existing_product:
        # Product already exists, skip
        return existing_product, 0

    # Create product
    product = Product(
        code=product_data['code'],
        name=product_data['name'],
        unit=product_data['unit'],
        is_finished_product=product_data['is_finished_product']
    )

    session.add(product)
    session.flush()  # Get product ID

    bom_count = 0

    # Create BOM items for materials
    for item in bom_items:
        component = get_or_create_component(
            session,
            item['component_name'],
            item['unit']
        )

        # Ensure component has an ID
        if not component.id:
            session.flush()

        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=component.id,
            quantity=Decimal(str(item['quantity'])),
            unit=item['unit'],
            notes=item.get('description')
        )

        session.add(bom)
        bom_count += 1

    # Add energy data as BOM component if present
    if energy_data and 'electricity_kwh' in energy_data and energy_data['electricity_kwh'] > 0:
        electricity = get_or_create_component(
            session,
            'electricity_us',
            'kWh'
        )

        # Ensure electricity component has an ID
        if not electricity.id:
            session.flush()

        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=electricity.id,
            quantity=Decimal(str(energy_data['electricity_kwh'])),
            unit='kWh'
        )

        session.add(bom)
        bom_count += 1

    # Add transport data as BOM components
    for transport in transport_data:
        mode = transport['mode']  # 'truck' or 'ship'
        distance_km = transport['distance_km']
        mass_kg = transport['mass_kg']

        # Calculate tonne-km (tkm) = (mass_kg * distance_km) / 1000
        tkm = (mass_kg * distance_km) / 1000

        component_name = f"transport_{mode}"

        # Create transport component with 'tkm' unit (now supported)
        transport_component = get_or_create_component(
            session,
            component_name,
            'tkm'
        )

        # Ensure transport component has an ID
        if not transport_component.id:
            session.flush()

        # Store quantity in tkm with unit 'tkm'
        bom = BillOfMaterials(
            parent_product_id=product.id,
            child_product_id=transport_component.id,
            quantity=Decimal(str(tkm)),
            unit='tkm'
        )

        session.add(bom)
        bom_count += 1

    session.commit()

    return product, bom_count


def load_products_and_boms(session: Session) -> int:
    """
    Load all products and BOMs from JSON files.

    Args:
        session: Database session

    Returns:
        Number of products loaded
    """
    data_dir = get_project_root() / "data"

    # List of BOM JSON files to load
    bom_files = [
        'bom_tshirt_realistic.json',
        'bom_water_bottle_realistic.json',
        'bom_phone_case_realistic.json'
    ]

    products_loaded = 0
    total_bom_items = 0

    for filename in bom_files:
        json_path = data_dir / filename

        if not json_path.exists():
            print(f"Warning: BOM file not found: {json_path}")
            continue

        product, bom_count = load_product_from_json(session, json_path)

        if product and bom_count > 0:
            products_loaded += 1
            total_bom_items += bom_count
            print(f"Loaded: {product.code} with {bom_count} BOM items")

    return products_loaded


def seed_all_data(session: Session) -> Dict[str, Any]:
    """
    Load all seed data (emission factors, products, BOMs).

    Args:
        session: Database session

    Returns:
        Summary dictionary with counts
    """
    print("=" * 60)
    print("SEED DATA LOADING")
    print("=" * 60)

    # Load emission factors
    print("\n1. Loading emission factors from CSV...")
    ef_count = load_emission_factors(session)
    total_ef = session.query(EmissionFactor).count()
    print(f"   Loaded {ef_count} new emission factors (Total: {total_ef})")

    # Load products and BOMs
    print("\n2. Loading products and BOMs from JSON...")
    products_loaded = load_products_and_boms(session)
    total_products = session.query(Product).count()
    total_boms = session.query(BillOfMaterials).count()
    print(f"   Loaded {products_loaded} new products (Total Products: {total_products})")
    print(f"   Total BOM relationships: {total_boms}")

    print("\n" + "=" * 60)
    print("SEED DATA LOADING COMPLETE")
    print("=" * 60)

    return {
        'status': 'success',
        'emission_factors_loaded': ef_count,
        'products_loaded': products_loaded,
        'bom_relationships_created': total_boms
    }


def main():
    """Main entry point for CLI execution"""
    try:
        with db_context() as session:
            result = seed_all_data(session)

        print(f"\nSummary:")
        print(f"  - Emission Factors: {result['emission_factors_loaded']} loaded")
        print(f"  - Products: {result['products_loaded']} loaded")
        print(f"  - BOM Relationships: {result['bom_relationships_created']} total")
        print(f"\nStatus: {result['status']}")

        return 0

    except Exception as e:
        print(f"\nError during seed data loading: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
