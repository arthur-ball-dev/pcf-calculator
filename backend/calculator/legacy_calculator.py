"""
Legacy PCF Calculator Methods with Database Integration.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module contains legacy methods that directly access the database
via SQLAlchemy. These are kept for backward compatibility but new code
should use the decoupled PCFCalculator with injected providers.

Note: This module is intentionally separate from pcf_calculator.py
to keep the main calculator module free of SQLAlchemy dependencies.
"""

import logging
import re
from typing import Any, Dict

from sqlalchemy.orm import Session, selectinload

from backend.models import BillOfMaterials, EmissionFactor, Product

logger = logging.getLogger(__name__)


def calculate_product_from_db(
    calculator,
    product_id: str,
    db_session: Session,
) -> Dict[str, Any]:
    """
    Calculate PCF for a product from database using its BOM.

    This legacy method queries the database to get the product's BOM structure
    and calculates emissions using the calculator's hierarchical calculation method.

    Note: For new implementations, use PCFCalculator.calculate() with
    an injected EmissionFactorProvider instead.

    Args:
        calculator: PCFCalculator instance (must be in legacy Brightway2 mode)
        product_id: UUID of product in database
        db_session: SQLAlchemy database session

    Returns:
        Dictionary with calculation results

    Raises:
        ValueError: If product not found in database
    """
    product = db_session.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise ValueError(f"Product not found: {product_id}")

    logger.info(f"Calculating PCF for product: {product.code} - {product.name}")

    bom_tree = build_bom_tree_from_db(
        calculator, product_id, db_session
    )

    if not bom_tree.get("children"):
        logger.warning(
            f"Product {product.code} has no BOM - returning zero emissions"
        )
        return {
            "product_id": product_id,
            "product_code": product.code,
            "product_name": product.name,
            "total_co2e_kg": 0.0,
            "breakdown": {},
            "max_depth": 0,
        }

    result = calculator.calculate_hierarchical(bom_tree)

    result["product_id"] = product_id
    result["product_code"] = product.code
    result["product_name"] = product.name

    breakdown_by_category = {
        "materials": 0.0,
        "energy": 0.0,
        "transport": 0.0,
    }

    for component_name, co2e in result["breakdown"].items():
        name_lower = component_name.lower()
        if "electricity" in name_lower or "energy" in name_lower:
            breakdown_by_category["energy"] += co2e
        elif (
            "transport" in name_lower
            or "truck" in name_lower
            or "ship" in name_lower
        ):
            breakdown_by_category["transport"] += co2e
        else:
            breakdown_by_category["materials"] += co2e

    result["breakdown_by_category"] = breakdown_by_category

    logger.info(
        f"PCF calculation complete: {product.code} = {result['total_co2e_kg']:.3f} kg CO2e"
    )

    return result


def build_bom_tree_from_db(
    calculator,
    product_id: str,
    db_session: Session,
    depth: int = 0,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """
    Build hierarchical BOM tree from database.

    Recursively traverses BOM relationships to build tree structure.

    Args:
        calculator: PCFCalculator instance (for emission factor mapping)
        product_id: UUID of product
        db_session: SQLAlchemy database session
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        BOM tree dictionary

    Raises:
        ValueError: If circular reference detected or max depth exceeded
    """
    if depth > max_depth:
        raise ValueError(f"Maximum BOM depth exceeded: {max_depth}")

    product = (
        db_session.query(Product)
        .options(
            selectinload(Product.bom_items)
            .selectinload(BillOfMaterials.child_product)
            .selectinload(Product.bom_items)
            .selectinload(BillOfMaterials.child_product)
        )
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError(f"Product not found: {product_id}")

    node = {
        "name": product.code,
        "quantity": 1.0,
        "unit": product.unit,
        "children": [],
    }

    bom_items = product.bom_items

    for bom_item in bom_items:
        child_product = bom_item.child_product

        has_child_bom = len(child_product.bom_items) > 0

        if has_child_bom:
            child_tree = build_bom_tree_from_db(
                calculator, child_product.id, db_session, depth + 1, max_depth
            )
            child_tree["quantity"] = float(bom_item.quantity)
            node["children"].append(child_tree)
        else:
            material_name = map_product_to_emission_factor(
                calculator, child_product, db_session
            )

            node["children"].append(
                {
                    "name": material_name,
                    "quantity": float(bom_item.quantity),
                    "unit": bom_item.unit or child_product.unit,
                }
            )

    return node


def map_product_to_emission_factor(
    calculator, product, db_session: Session
) -> str:
    """
    Map product code/name to emission factor activity name.

    Priority:
    1. Check product metadata for emission_factor_id (set by user or data ingestion)
    2. Try exact name match (lowercase)
    3. Try code-based match (normalized)
    4. Try underscore-separated name match
    5. Fall back to product name (will likely fail calculation)

    Args:
        calculator: PCFCalculator instance (for name lookup cache)
        product: Product model instance
        db_session: SQLAlchemy database session for emission factor lookup

    Returns:
        Emission factor activity name
    """
    # Priority 1: Check product metadata for emission_factor_id
    # This is set when user selects emission factor in BOM Editor or by data ingestion
    if product.metadata and isinstance(product.metadata, dict):
        emission_factor_id = product.metadata.get("emission_factor_id")
        if emission_factor_id:
            # Look up emission factor by ID to get its activity_name
            ef = db_session.query(EmissionFactor).filter(
                EmissionFactor.id == emission_factor_id
            ).first()
            if ef:
                activity_name = ef.activity_name.lower()
                if activity_name in calculator._name_to_activity:
                    logger.debug(
                        f"Mapped product {product.code} via metadata emission_factor_id "
                        f"to activity: {activity_name}"
                    )
                    return activity_name
                else:
                    logger.warning(
                        f"Emission factor ID {emission_factor_id} found for product "
                        f"{product.code}, but activity '{activity_name}' not in calculator cache. "
                        f"Available: {list(calculator._name_to_activity.keys())[:5]}..."
                    )
            else:
                logger.warning(
                    f"Product {product.code} has emission_factor_id {emission_factor_id} "
                    f"but emission factor not found in database"
                )

    # Priority 2: Exact name match (lowercase)
    name_exact = product.name.lower()
    if name_exact in calculator._name_to_activity:
        return name_exact

    # Priority 3: Code-based match (normalized)
    code_normalized = product.code.lower().replace("-", "_")
    code_normalized = re.sub(r"_?\d+$", "", code_normalized)

    if code_normalized in calculator._name_to_activity:
        return code_normalized

    # Priority 4: Underscore-separated name match
    name_underscored = product.name.lower().replace(" ", "_")
    if name_underscored in calculator._name_to_activity:
        return name_underscored

    # Priority 5: Fall back to product name (will likely fail)
    logger.warning(
        f"Could not map product {product.code} ({product.name}) to emission factor. "
        f"Using name as-is: {name_exact}"
    )
    return name_exact
