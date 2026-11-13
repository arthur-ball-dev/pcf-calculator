"""
Calculation runner: the background task behind POST /api/v1/calculate.

Issue #34 moved this out of the route module; issue #37 made `classify_component`
the single backend keyword classifier (the legacy calculator used to carry a
diverging copy). The frontend keeps its own, finer-grained presentation
classifier in `frontend/src/utils/classifyComponent.ts`; the three categories
here are the ones stored on `pcf_calculations`.

Lifecycle of `execute_calculation`:
1. mark the calculation `in_progress`
2. verify the product exists
3. load the BOM rows joined with their emission factors, or use the BOM the user
   submitted (issue #195: rows already validated and converted to their factor's
   unit by CalculationService; they are never stored)
4. CO2e per component = quantity x factor, in Decimal (issue #23: the columns
   are DECIMAL; summing in float lost precision before it was stored)
5. mark `completed` with the totals and the per-component breakdown
6. on any error mark `failed` with the message

The task owns its database session: the request session that queued it may be
closed by the time it runs.
"""

import logging
import re
import time
from decimal import Decimal
from typing import Callable, Dict, Literal, Optional, Sequence

from sqlalchemy.orm import Session

from backend.domain.entities.calculation import ResolvedBOMLine

logger = logging.getLogger(__name__)

Category = Literal["energy", "transport", "materials"]

_ENERGY_KEYWORDS = ("electricity", "energy", "grid")
_TRANSPORT_KEYWORDS = ("transport", "truck", "ship")

# Totals are stored in DECIMAL(15,6) columns
_PLACES = Decimal("0.000001")


# A submitted row's category (the BOM editor's five) -> the stored total it counts towards
CATEGORY_TOTAL: Dict[str, Category] = {
    "material": "materials",
    "other": "materials",
    "energy": "energy",
    "combustion": "energy",
    "transport": "transport",
}


def classify_component(name: str) -> Category:
    """Map a component name to the stored breakdown category by keyword."""
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in _ENERGY_KEYWORDS):
        return "energy"
    if any(keyword in name_lower for keyword in _TRANSPORT_KEYWORDS):
        return "transport"
    return "materials"


def execute_calculation(
    calculation_id: str,
    product_id: str,
    calculation_type: str,
    session_factory: Optional[Callable[[], Session]] = None,
    bom_lines: Optional[Sequence[ResolvedBOMLine]] = None,
) -> None:
    """
    Background task: compute a product's PCF from its BOM and stored emission factors.

    Args:
        calculation_id: UUID of the pcf_calculations row created by the route
        product_id: UUID of the product to calculate
        calculation_type: calculation scope (recorded on the row by the route)
        session_factory: optional session factory (tests pass the request session's)
        bom_lines: the user's submitted BOM, validated and in factor units; None to
            calculate the product's catalog BOM
    """
    from backend.database.connection import SessionLocal
    from backend.models import PCFCalculation, Product

    start_time = time.time()
    db_session = (session_factory or SessionLocal)()

    try:
        calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()
        if not calculation:
            logger.error(f"Calculation {calculation_id} not found in database")
            return

        calculation.status = "in_progress"
        db_session.commit()
        logger.info(f"Starting calculation {calculation_id} for product {product_id}")

        product = db_session.query(Product).filter_by(id=product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        totals: Dict[Category, Decimal] = {
            "materials": Decimal(0),
            "energy": Decimal(0),
            "transport": Decimal(0),
        }
        total_co2e = Decimal(0)
        breakdown: Dict[str, float] = {}

        if bom_lines is not None:
            for line in bom_lines:
                component_co2e = line.quantity * line.co2e_factor
                breakdown[line.name] = float(component_co2e.quantize(_PLACES))
                total_co2e += component_co2e
                totals[CATEGORY_TOTAL[line.category]] += component_co2e
            method = "SubmittedBOM"
        else:
            total_co2e = _catalog_totals(db_session, product_id, totals, breakdown)
            method = "SQL_DirectCalculation"

        elapsed_ms = int((time.time() - start_time) * 1000)

        calculation.status = "completed"
        calculation.total_co2e_kg = total_co2e.quantize(_PLACES)
        calculation.materials_co2e = totals["materials"].quantize(_PLACES)
        calculation.energy_co2e = totals["energy"].quantize(_PLACES)
        calculation.transport_co2e = totals["transport"].quantize(_PLACES)
        calculation.calculation_time_ms = elapsed_ms
        calculation.calculation_method = method
        calculation.breakdown = breakdown
        db_session.commit()

        logger.info(
            f"Calculation {calculation_id} completed: {total_co2e:.3f} kg CO2e in {elapsed_ms}ms"
        )

    except ValueError as e:
        logger.error(f"Calculation {calculation_id} validation error: {e}")
        _mark_failed(db_session, calculation_id, str(e))

    except Exception as e:
        logger.error(f"Calculation {calculation_id} failed with error: {e}", exc_info=True)
        _mark_failed(db_session, calculation_id, f"Calculation error: {str(e)}")

    finally:
        db_session.close()


def _catalog_totals(
    db_session: Session,
    product_id: str,
    totals: Dict[Category, Decimal],
    breakdown: Dict[str, float],
) -> Decimal:
    """Add the product's catalog BOM to totals and breakdown; returns the total CO2e."""
    from backend.models import BillOfMaterials, EmissionFactor, Product

    bom_rows = (
        db_session.query(BillOfMaterials, EmissionFactor, Product)
        .join(Product, Product.id == BillOfMaterials.child_product_id)
        .outerjoin(EmissionFactor, EmissionFactor.id == BillOfMaterials.emission_factor_id)
        .filter(BillOfMaterials.parent_product_id == product_id)
        .all()
    )

    # Fallback for BOM rows without an emission_factor_id: match by activity name
    ef_by_name = {ef.activity_name: ef for ef in db_session.query(EmissionFactor).all()}

    total_co2e = Decimal(0)
    for bom_item, ef, child_product in bom_rows:
        quantity = Decimal(bom_item.quantity or 0)

        if ef is None and child_product:
            name_lower = child_product.name.lower()
            code_normalized = re.sub(r"_?\d+$", "", child_product.code.lower().replace("-", "_"))
            name_underscored = name_lower.replace(" ", "_")
            ef = (
                ef_by_name.get(name_lower)
                or ef_by_name.get(code_normalized)
                or ef_by_name.get(name_underscored)
            )

        factor_value = Decimal(ef.co2e_factor) if ef and ef.co2e_factor is not None else Decimal(0)
        component_co2e = quantity * factor_value

        component_name = child_product.name if child_product else "Unknown"
        breakdown[component_name] = float(component_co2e.quantize(_PLACES))
        total_co2e += component_co2e
        totals[classify_component(component_name)] += component_co2e

    return total_co2e


def _mark_failed(db_session: Session, calculation_id: str, message: str) -> None:
    from backend.models import PCFCalculation

    calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()
    if calculation:
        calculation.status = "failed"
        if not calculation.calculation_metadata:
            calculation.calculation_metadata = {}
        calculation.calculation_metadata["error_message"] = message
        db_session.commit()


__all__ = ["classify_component", "execute_calculation"]
