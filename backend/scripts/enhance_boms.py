#!/usr/bin/env python3
"""
BOM Enhancement Script with Transport and Other Inputs.

TASK-DATA-P8-002: Enhance Sample BOMs with Transport and Other Inputs

This script:
1. Adds new "other" category emission factors
2. Creates component products for packaging/water/waste
3. Adds transport inputs to ALL products that have BOMs
4. Adds packaging inputs to electronics products
5. Syncs emission factors to Brightway2
"""

import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Tuple, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.models import (
    Product,
    EmissionFactor,
    BillOfMaterials,
)
from backend.database.connection import db_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Step 1: Add "other" category emission factors
# ============================================================================
OTHER_EMISSION_FACTORS = [
    {
        "activity_name": "packaging (cardboard)",
        "co2e_factor": Decimal("0.9"),
        "unit": "kg",
        "category": "other",
        "data_source": "Ecoinvent",
        "geography": "GLO",
    },
    {
        "activity_name": "packaging (plastic)",
        "co2e_factor": Decimal("2.5"),
        "unit": "kg",
        "category": "other",
        "data_source": "Ecoinvent",
        "geography": "GLO",
    },
    {
        "activity_name": "water (process)",
        "co2e_factor": Decimal("0.0003"),
        "unit": "L",
        "category": "other",
        "data_source": "EPA",
        "geography": "GLO",
    },
    {
        "activity_name": "waste (general)",
        "co2e_factor": Decimal("0.5"),
        "unit": "kg",
        "category": "other",
        "data_source": "EPA",
        "geography": "GLO",
    },
]


def add_other_emission_factors(session: Session) -> int:
    """
    Add new 'other' category emission factors.

    Returns:
        Number of new emission factors added.
    """
    added = 0

    for factor_data in OTHER_EMISSION_FACTORS:
        # Check if already exists
        existing = session.query(EmissionFactor).filter_by(
            activity_name=factor_data["activity_name"],
            data_source=factor_data["data_source"],
            geography=factor_data["geography"],
        ).first()

        if existing:
            logger.info(f"Emission factor '{factor_data['activity_name']}' already exists, skipping")
            continue

        ef = EmissionFactor(
            activity_name=factor_data["activity_name"],
            co2e_factor=factor_data["co2e_factor"],
            unit=factor_data["unit"],
            category=factor_data["category"],
            data_source=factor_data["data_source"],
            geography=factor_data["geography"],
        )
        session.add(ef)
        added += 1
        logger.info(f"Added emission factor: {factor_data['activity_name']}")

    session.flush()
    return added


# ============================================================================
# Step 2: Create component products
# ============================================================================
COMPONENT_PRODUCTS = [
    {"code": "packaging_cardboard", "name": "Packaging (Cardboard)", "unit": "kg"},
    {"code": "packaging_plastic", "name": "Packaging (Plastic)", "unit": "kg"},
    {"code": "water_process", "name": "Water (Process)", "unit": "L"},
    {"code": "waste_general", "name": "Waste (General)", "unit": "kg"},
]


def create_component_products(session: Session) -> int:
    """
    Create component products for packaging, water, waste.

    Returns:
        Number of new products created.
    """
    created = 0

    for product_data in COMPONENT_PRODUCTS:
        # Check if already exists
        existing = session.query(Product).filter_by(code=product_data["code"]).first()

        if existing:
            logger.info(f"Product '{product_data['code']}' already exists, skipping")
            continue

        product = Product(
            code=product_data["code"],
            name=product_data["name"],
            unit=product_data["unit"],
            is_finished_product=False,
        )
        session.add(product)
        created += 1
        logger.info(f"Created product: {product_data['code']}")

    session.flush()
    return created


# ============================================================================
# Step 3: Add transport to all BOMs
# ============================================================================

# Transport estimates by product category
TRANSPORT_ESTIMATES = {
    # Electronics - manufactured in Asia, shipped globally
    "E-CMP-LPT": {"truck_tkm": 0.75, "ship_tkm": 15.0, "weight_kg": 1.5},   # Laptops
    "E-CMP-DSK": {"truck_tkm": 2.5, "ship_tkm": 50.0, "weight_kg": 5.0},    # Desktops
    "E-CMP-SRV": {"truck_tkm": 7.5, "ship_tkm": 150.0, "weight_kg": 15.0},  # Servers
    "E-CMP-TAB": {"truck_tkm": 0.5, "ship_tkm": 10.0, "weight_kg": 1.0},    # Tablets
    "E-MOB-PHN": {"truck_tkm": 0.1, "ship_tkm": 2.0, "weight_kg": 0.2},     # Phones
    "E-MOB-WER": {"truck_tkm": 0.05, "ship_tkm": 1.0, "weight_kg": 0.1},    # Wearables
    "E-AV-MON": {"truck_tkm": 2.5, "ship_tkm": 50.0, "weight_kg": 5.0},     # Monitors
    "E-AV-TV": {"truck_tkm": 7.5, "ship_tkm": 150.0, "weight_kg": 15.0},    # TVs
    "E-AV-AUD": {"truck_tkm": 0.5, "ship_tkm": 10.0, "weight_kg": 1.0},     # Audio
    "E-APL": {"truck_tkm": 10.0, "ship_tkm": 200.0, "weight_kg": 20.0},     # Appliances

    # Automotive - regional manufacturing
    "U-BAT": {"truck_tkm": 5.0, "ship_tkm": 25.0, "weight_kg": 10.0},       # Batteries
    "U-ENG": {"truck_tkm": 5.0, "ship_tkm": 25.0, "weight_kg": 10.0},       # Engines
    "U-WHL": {"truck_tkm": 2.5, "ship_tkm": 12.5, "weight_kg": 5.0},        # Wheels
    "U-BRK": {"truck_tkm": 1.0, "ship_tkm": 5.0, "weight_kg": 2.0},         # Brakes

    # Apparel - global supply chains
    "A-TOP": {"truck_tkm": 0.15, "ship_tkm": 3.0, "weight_kg": 0.3},        # Tops
    "A-BOT": {"truck_tkm": 0.25, "ship_tkm": 5.0, "weight_kg": 0.5},        # Bottoms
    "A-FTW": {"truck_tkm": 0.5, "ship_tkm": 10.0, "weight_kg": 1.0},        # Footwear
    "A-ACC": {"truck_tkm": 0.1, "ship_tkm": 2.0, "weight_kg": 0.2},         # Accessories

    # Food & Beverage - regional distribution
    "F-BEV": {"truck_tkm": 0.5, "ship_tkm": 0.0, "weight_kg": 1.0},         # Beverages
    "F-DRY": {"truck_tkm": 0.25, "ship_tkm": 0.0, "weight_kg": 0.5},        # Dry goods
    "F-SNK": {"truck_tkm": 0.1, "ship_tkm": 0.0, "weight_kg": 0.2},         # Snacks
    "F-GRN": {"truck_tkm": 0.25, "ship_tkm": 2.5, "weight_kg": 0.5},        # Grains

    # Construction - heavy, local transport
    "C-STL": {"truck_tkm": 50.0, "ship_tkm": 25.0, "weight_kg": 100.0},     # Steel
    "C-CEM": {"truck_tkm": 25.0, "ship_tkm": 0.0, "weight_kg": 50.0},       # Cement
    "C-LBR": {"truck_tkm": 5.0, "ship_tkm": 0.0, "weight_kg": 10.0},        # Lumber
    "C-INS": {"truck_tkm": 0.5, "ship_tkm": 0.0, "weight_kg": 1.0},         # Insulation

    # Default for unmatched products
    "DEFAULT": {"truck_tkm": 0.5, "ship_tkm": 5.0, "weight_kg": 1.0},
}


def get_transport_estimate(product_code: str) -> Dict[str, float]:
    """Get transport estimate based on product code prefix."""
    for prefix, estimate in TRANSPORT_ESTIMATES.items():
        if prefix != "DEFAULT" and product_code.startswith(prefix):
            return estimate
    return TRANSPORT_ESTIMATES["DEFAULT"]


def add_transport_to_boms(session: Session) -> int:
    """
    Add transport to ALL products that have BOMs and are missing transport.

    Returns:
        Number of transport BOM entries added.
    """
    # Get transport products
    transport_truck = session.query(Product).filter_by(code="transport_truck").first()
    transport_ship = session.query(Product).filter_by(code="transport_ship").first()

    if not transport_truck or not transport_ship:
        logger.error("Transport products not found! Run seed_data.py first.")
        return 0

    # Get all finished products that have BOMs
    result = session.execute(text("""
        SELECT DISTINCT p.id, p.code
        FROM products p
        JOIN bill_of_materials b ON b.parent_product_id = p.id
        WHERE p.is_finished_product = 1
    """))
    products_with_boms = result.fetchall()

    added = 0

    for product_id, product_code in products_with_boms:
        # Check if already has transport_truck
        existing_truck = session.query(BillOfMaterials).filter_by(
            parent_product_id=product_id,
            child_product_id=transport_truck.id,
        ).first()

        # Check if already has transport_ship
        existing_ship = session.query(BillOfMaterials).filter_by(
            parent_product_id=product_id,
            child_product_id=transport_ship.id,
        ).first()

        estimate = get_transport_estimate(product_code)

        # Add transport_truck if missing
        if not existing_truck and estimate["truck_tkm"] > 0:
            bom_truck = BillOfMaterials(
                parent_product_id=product_id,
                child_product_id=transport_truck.id,
                quantity=Decimal(str(estimate["truck_tkm"])),
                unit="tkm",
                notes="Road transport estimate",
            )
            session.add(bom_truck)
            added += 1

        # Add transport_ship if missing and estimate > 0
        if not existing_ship and estimate["ship_tkm"] > 0:
            bom_ship = BillOfMaterials(
                parent_product_id=product_id,
                child_product_id=transport_ship.id,
                quantity=Decimal(str(estimate["ship_tkm"])),
                unit="tkm",
                notes="Sea transport estimate",
            )
            session.add(bom_ship)
            added += 1

    session.flush()
    logger.info(f"Added {added} transport BOM entries")
    return added


# ============================================================================
# Step 4: Add packaging to electronics BOMs
# ============================================================================

PACKAGING_ESTIMATES = {
    "E-CMP-LPT": {"cardboard": 0.3, "plastic": 0.05},   # Laptops
    "E-CMP-DSK": {"cardboard": 0.8, "plastic": 0.1},    # Desktops
    "E-CMP-SRV": {"cardboard": 1.5, "plastic": 0.15},   # Servers
    "E-CMP-TAB": {"cardboard": 0.2, "plastic": 0.03},   # Tablets
    "E-MOB-PHN": {"cardboard": 0.15, "plastic": 0.02},  # Phones
    "E-MOB-WER": {"cardboard": 0.1, "plastic": 0.01},   # Wearables
    "E-AV-MON": {"cardboard": 0.6, "plastic": 0.1},     # Monitors
    "E-AV-TV": {"cardboard": 1.2, "plastic": 0.2},      # TVs
    "E-AV-AUD": {"cardboard": 0.2, "plastic": 0.03},    # Audio
    "E-APL": {"cardboard": 1.5, "plastic": 0.2},        # Appliances
    "DEFAULT": {"cardboard": 0.3, "plastic": 0.05},
}


def get_packaging_estimate(product_code: str) -> Dict[str, float]:
    """Get packaging estimate based on product code prefix."""
    for prefix, estimate in PACKAGING_ESTIMATES.items():
        if prefix != "DEFAULT" and product_code.startswith(prefix):
            return estimate
    return PACKAGING_ESTIMATES["DEFAULT"]


def add_packaging_to_electronics(session: Session) -> int:
    """
    Add packaging to ALL electronics products that have BOMs.

    Returns:
        Number of packaging BOM entries added.
    """
    # Get packaging products
    packaging_cardboard = session.query(Product).filter_by(code="packaging_cardboard").first()
    packaging_plastic = session.query(Product).filter_by(code="packaging_plastic").first()

    if not packaging_cardboard or not packaging_plastic:
        logger.error("Packaging products not found! Run create_component_products first.")
        return 0

    # Get all electronics products (E- prefix) that have BOMs
    result = session.execute(text("""
        SELECT DISTINCT p.id, p.code
        FROM products p
        JOIN bill_of_materials b ON b.parent_product_id = p.id
        WHERE p.code LIKE 'E-%'
        AND p.is_finished_product = 1
    """))
    electronics_products = result.fetchall()

    added = 0

    for product_id, product_code in electronics_products:
        estimate = get_packaging_estimate(product_code)

        # Check if already has packaging_cardboard
        existing_cardboard = session.query(BillOfMaterials).filter_by(
            parent_product_id=product_id,
            child_product_id=packaging_cardboard.id,
        ).first()

        # Check if already has packaging_plastic
        existing_plastic = session.query(BillOfMaterials).filter_by(
            parent_product_id=product_id,
            child_product_id=packaging_plastic.id,
        ).first()

        # Add packaging_cardboard if missing
        if not existing_cardboard and estimate["cardboard"] > 0:
            bom_cardboard = BillOfMaterials(
                parent_product_id=product_id,
                child_product_id=packaging_cardboard.id,
                quantity=Decimal(str(estimate["cardboard"])),
                unit="kg",
                notes="Cardboard packaging estimate",
            )
            session.add(bom_cardboard)
            added += 1

        # Add packaging_plastic if missing
        if not existing_plastic and estimate["plastic"] > 0:
            bom_plastic = BillOfMaterials(
                parent_product_id=product_id,
                child_product_id=packaging_plastic.id,
                quantity=Decimal(str(estimate["plastic"])),
                unit="kg",
                notes="Plastic packaging estimate",
            )
            session.add(bom_plastic)
            added += 1

    session.flush()
    logger.info(f"Added {added} packaging BOM entries to electronics")
    return added


# ============================================================================
# Step 5: Sync emission factors to Brightway2
# ============================================================================

def sync_to_brightway2() -> Dict[str, Any]:
    """
    Sync all emission factors to Brightway2.

    Returns:
        Sync statistics from sync_emission_factors()
    """
    try:
        from backend.calculator.emission_factor_sync import sync_emission_factors
        result = sync_emission_factors()
        logger.info(f"Synced {result['synced_count']} emission factors to Brightway2")
        return result
    except Exception as e:
        logger.warning(f"Could not sync to Brightway2: {e}")
        return {"synced_count": 0, "error": str(e)}


# ============================================================================
# Main entry point
# ============================================================================

def enhance_all_boms() -> Dict[str, Any]:
    """
    Run all BOM enhancement steps.

    Returns:
        Summary of changes made.
    """
    logger.info("=" * 60)
    logger.info("BOM ENHANCEMENT SCRIPT")
    logger.info("=" * 60)

    results = {
        "emission_factors_added": 0,
        "products_created": 0,
        "transport_boms_added": 0,
        "packaging_boms_added": 0,
        "brightway_synced": 0,
    }

    with db_context() as session:
        # Step 1: Add other emission factors
        logger.info("\n1. Adding 'other' category emission factors...")
        results["emission_factors_added"] = add_other_emission_factors(session)

        # Step 2: Create component products
        logger.info("\n2. Creating component products...")
        results["products_created"] = create_component_products(session)

        # Commit so products are available for BOM creation
        session.commit()

        # Step 3: Add transport to all BOMs
        logger.info("\n3. Adding transport to all BOMs...")
        results["transport_boms_added"] = add_transport_to_boms(session)

        # Step 4: Add packaging to electronics
        logger.info("\n4. Adding packaging to electronics...")
        results["packaging_boms_added"] = add_packaging_to_electronics(session)

        # Commit all changes
        session.commit()

    # Step 5: Sync to Brightway2
    logger.info("\n5. Syncing to Brightway2...")
    sync_result = sync_to_brightway2()
    results["brightway_synced"] = sync_result.get("synced_count", 0)

    logger.info("\n" + "=" * 60)
    logger.info("BOM ENHANCEMENT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Emission factors added: {results['emission_factors_added']}")
    logger.info(f"  Products created: {results['products_created']}")
    logger.info(f"  Transport BOMs added: {results['transport_boms_added']}")
    logger.info(f"  Packaging BOMs added: {results['packaging_boms_added']}")
    logger.info(f"  Brightway2 synced: {results['brightway_synced']} factors")

    return results


def main():
    """CLI entry point."""
    try:
        results = enhance_all_boms()
        return 0
    except Exception as e:
        logger.error(f"Error during BOM enhancement: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
