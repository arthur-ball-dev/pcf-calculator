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
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
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


def _fetch_bom_hierarchy(
    product_id: str,
    db_session: Session,
    max_depth: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch entire BOM hierarchy in a single recursive CTE query.

    Returns flat list of rows with: parent_product_id, child_product_id,
    child_code, child_name, child_unit, quantity, bom_unit, emission_factor_id,
    child_metadata, depth, and has_children flag.

    Args:
        product_id: Root product UUID
        db_session: SQLAlchemy database session
        max_depth: Maximum recursion depth

    Returns:
        List of dicts representing all BOM rows in the hierarchy
    """
    cte_sql = text("""
        WITH RECURSIVE bom_hierarchy AS (
            -- Base case: direct children of root product
            SELECT
                bom.parent_product_id,
                bom.child_product_id,
                p.code AS child_code,
                p.name AS child_name,
                p.unit AS child_unit,
                p.metadata AS child_metadata,
                bom.quantity,
                bom.unit AS bom_unit,
                bom.emission_factor_id,
                1 AS depth
            FROM bill_of_materials bom
            JOIN products p ON p.id = bom.child_product_id
            WHERE bom.parent_product_id = :product_id

            UNION ALL

            -- Recursive case: children of children
            SELECT
                bom.parent_product_id,
                bom.child_product_id,
                p.code AS child_code,
                p.name AS child_name,
                p.unit AS child_unit,
                p.metadata AS child_metadata,
                bom.quantity,
                bom.unit AS bom_unit,
                bom.emission_factor_id,
                bh.depth + 1 AS depth
            FROM bill_of_materials bom
            JOIN products p ON p.id = bom.child_product_id
            JOIN bom_hierarchy bh ON bh.child_product_id = bom.parent_product_id
            WHERE bh.depth < :max_depth
        )
        SELECT
            bh.*,
            EXISTS(
                SELECT 1 FROM bill_of_materials sub
                WHERE sub.parent_product_id = bh.child_product_id
            ) AS has_children
        FROM bom_hierarchy bh
        ORDER BY bh.depth, bh.parent_product_id
    """)

    result = db_session.execute(cte_sql, {"product_id": product_id, "max_depth": max_depth})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


def _batch_fetch_emission_factors(
    ef_ids: Set[str],
    db_session: Session,
) -> Dict[str, EmissionFactor]:
    """
    Batch-fetch emission factors by ID.

    Args:
        ef_ids: Set of emission factor UUIDs to fetch
        db_session: SQLAlchemy database session

    Returns:
        Dict mapping emission factor ID to EmissionFactor object
    """
    if not ef_ids:
        return {}
    factors = (
        db_session.query(EmissionFactor)
        .filter(EmissionFactor.id.in_(ef_ids))
        .all()
    )
    return {ef.id: ef for ef in factors}


def build_bom_tree_from_db(
    calculator,
    product_id: str,
    db_session: Session,
    depth: int = 0,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """
    Build hierarchical BOM tree from database using a single CTE query.

    Fetches entire BOM hierarchy in one query, then builds tree in-memory.
    Emission factors are batch-fetched to avoid N+1 queries.

    Args:
        calculator: PCFCalculator instance (for emission factor mapping)
        product_id: UUID of product
        db_session: SQLAlchemy database session
        depth: Current recursion depth (unused, kept for API compat)
        max_depth: Maximum recursion depth

    Returns:
        BOM tree dictionary

    Raises:
        ValueError: If product not found
    """
    product = db_session.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise ValueError(f"Product not found: {product_id}")

    # Fetch entire hierarchy in one CTE query
    rows = _fetch_bom_hierarchy(product_id, db_session, max_depth)

    if not rows:
        return {
            "name": product.code,
            "quantity": 1.0,
            "unit": product.unit,
            "children": [],
        }

    # Batch-fetch all referenced emission factors
    ef_ids = set()
    for row in rows:
        if row.get("emission_factor_id"):
            ef_ids.add(row["emission_factor_id"])
        meta = row.get("child_metadata")
        if meta and isinstance(meta, dict):
            meta_ef_id = meta.get("emission_factor_id")
            if meta_ef_id:
                ef_ids.add(meta_ef_id)
    ef_cache = _batch_fetch_emission_factors(ef_ids, db_session)

    # Build children lookup: parent_id -> list of child rows
    children_by_parent: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        children_by_parent[row["parent_product_id"]].append(row)

    # Recursively build tree in-memory
    def build_node(parent_id: str) -> List[Dict[str, Any]]:
        children = []
        for row in children_by_parent.get(parent_id, []):
            if row["has_children"]:
                # Intermediate node - recurse
                child_node = {
                    "name": row["child_code"],
                    "quantity": float(row["quantity"]),
                    "unit": row["child_unit"],
                    "children": build_node(row["child_product_id"]),
                }
                children.append(child_node)
            else:
                # Leaf node - map to emission factor
                material_name = _map_to_emission_factor_cached(
                    calculator, row, ef_cache
                )
                children.append({
                    "name": material_name,
                    "quantity": float(row["quantity"]),
                    "unit": row["bom_unit"] or row["child_unit"],
                })
        return children

    return {
        "name": product.code,
        "quantity": 1.0,
        "unit": product.unit,
        "children": build_node(product_id),
    }


def _map_to_emission_factor_cached(
    calculator,
    row: Dict[str, Any],
    ef_cache: Dict[str, EmissionFactor],
) -> str:
    """
    Map a BOM row to emission factor using pre-fetched cache.

    Same priority logic as map_product_to_emission_factor but uses
    the batch-fetched ef_cache instead of individual queries.

    Args:
        calculator: PCFCalculator instance
        row: BOM hierarchy row dict
        ef_cache: Pre-fetched emission factors by ID

    Returns:
        Emission factor activity name
    """
    child_code = row["child_code"]
    child_name = row["child_name"]

    # Priority 1: BOM item's emission_factor_id
    bom_ef_id = row.get("emission_factor_id")
    if bom_ef_id and bom_ef_id in ef_cache:
        ef = ef_cache[bom_ef_id]
        activity_name = ef.activity_name
        if activity_name in calculator._name_to_activity:
            return activity_name

    # Priority 2: Product metadata emission_factor_id
    meta = row.get("child_metadata")
    if meta and isinstance(meta, dict):
        meta_ef_id = meta.get("emission_factor_id")
        if meta_ef_id and meta_ef_id in ef_cache:
            ef = ef_cache[meta_ef_id]
            activity_name = ef.activity_name.lower()
            if activity_name in calculator._name_to_activity:
                return activity_name

    # Priority 3: Exact name match
    name_exact = child_name.lower()
    if name_exact in calculator._name_to_activity:
        return name_exact

    # Priority 4: Code-based match
    code_normalized = child_code.lower().replace("-", "_")
    code_normalized = re.sub(r"_?\d+$", "", code_normalized)
    if code_normalized in calculator._name_to_activity:
        return code_normalized

    # Priority 5: Underscore-separated name
    name_underscored = child_name.lower().replace(" ", "_")
    if name_underscored in calculator._name_to_activity:
        return name_underscored

    # Priority 6: Fall back
    logger.warning(
        f"Could not map product {child_code} ({child_name}) to emission factor. "
        f"Using name as-is: {name_exact}"
    )
    return name_exact


def map_product_to_emission_factor(
    calculator, product, db_session: Session, bom_emission_factor_id: str = None
) -> str:
    """
    Map product code/name to emission factor activity name.

    Priority:
    1. Check BOM item's emission_factor_id (direct link from BOM editor)
    2. Check product metadata for emission_factor_id (set by user or data ingestion)
    3. Try exact name match (lowercase)
    4. Try code-based match (normalized)
    5. Try underscore-separated name match
    6. Fall back to product name (will likely fail calculation)

    Args:
        calculator: PCFCalculator instance (for name lookup cache)
        product: Product model instance
        db_session: SQLAlchemy database session for emission factor lookup
        bom_emission_factor_id: Optional emission_factor_id from BOM item

    Returns:
        Emission factor activity name
    """
    # Priority 1: Check BOM item's emission_factor_id (direct link)
    # This is set when user selects emission factor in BOM Editor
    if bom_emission_factor_id:
        ef = db_session.query(EmissionFactor).filter(
            EmissionFactor.id == bom_emission_factor_id
        ).first()
        if ef:
            activity_name = ef.activity_name
            if activity_name in calculator._name_to_activity:
                logger.debug(
                    f"Mapped product {product.code} via BOM emission_factor_id "
                    f"to activity: {activity_name}"
                )
                return activity_name
            else:
                logger.warning(
                    f"BOM emission_factor_id {bom_emission_factor_id} found for product "
                    f"{product.code}, but activity '{activity_name}' not in calculator cache. "
                    f"Available: {list(calculator._name_to_activity.keys())[:5]}..."
                )
        else:
            logger.warning(
                f"BOM item has emission_factor_id {bom_emission_factor_id} "
                f"but emission factor not found in database"
            )

    # Priority 2: Check product metadata for emission_factor_id
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

    # Priority 3: Exact name match (lowercase)
    name_exact = product.name.lower()
    if name_exact in calculator._name_to_activity:
        return name_exact

    # Priority 4: Code-based match (normalized)
    code_normalized = product.code.lower().replace("-", "_")
    code_normalized = re.sub(r"_?\d+$", "", code_normalized)

    if code_normalized in calculator._name_to_activity:
        return code_normalized

    # Priority 5: Underscore-separated name match
    name_underscored = product.name.lower().replace(" ", "_")
    if name_underscored in calculator._name_to_activity:
        return name_underscored

    # Priority 6: Fall back to product name (will likely fail)
    logger.warning(
        f"Could not map product {product.code} ({product.name}) to emission factor. "
        f"Using name as-is: {name_exact}"
    )
    return name_exact
