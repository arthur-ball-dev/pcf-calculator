"""
Calculations API Routes
TASK-API-002: Implementation of async calculation endpoints
TASK-BE-P5-010: Fix Backend Test Failures - Add enum validation for calculation_type
TASK-FE-P8-003: Added breakdown field to response for expandable items
TASK-API-P7-027: Align API contract types - change 'processing'/'running' to 'in_progress'
TASK-BE-P7-018: Added JWT authentication (user role required)

Endpoints:
- POST /api/v1/calculate - Start async PCF calculation (returns 202 Accepted)
- GET /api/v1/calculations/{id} - Poll for calculation status and results

This module implements the async calculation pattern:
1. Client POSTs to /calculate
2. API returns 202 Accepted with calculation_id immediately
3. Background task executes calculation
4. Client polls /calculations/{id} until status="completed"
"""

import logging
import re
from typing import Optional
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models import Product, PCFCalculation, generate_uuid
from backend.models.user import User
from backend.auth.dependencies import get_optional_user, get_current_active_user
from backend.schemas import (
    CalculationRequest,
    CalculationStartResponse,
    CalculationStatusResponse,
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["calculations"])


# ============================================================================
# Background Task Functions
# ============================================================================

def execute_calculation(
    calculation_id: str,
    product_id: str,
    calculation_type: str,
):
    """
    Background task: Execute PCF calculation using SQL-backed emission factors.

    This function runs asynchronously in the background after returning
    202 Accepted to the client. Updates database with results or error.

    Creates its own database session to avoid using the request-scoped
    session which may be closed by the time this task executes.

    Lifecycle:
    1. Update status to 'in_progress'
    2. Verify product exists
    3. Query BOM items with emission factors from PostgreSQL
    4. Calculate CO2e per component (quantity * emission_factor)
    5. Update status to 'completed' with results
    6. Handle errors and update status to 'failed'

    Args:
        calculation_id: UUID of calculation record
        product_id: UUID of product to calculate
        calculation_type: Type of calculation
    """
    import time
    from backend.database.connection import SessionLocal
    from backend.models import BillOfMaterials, EmissionFactor

    start_time = time.time()
    db_session = SessionLocal()

    try:
        # Update status to 'in_progress'
        calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()

        if not calculation:
            logger.error(f"Calculation {calculation_id} not found in database")
            return

        calculation.status = "in_progress"
        db_session.commit()

        logger.info(f"Starting calculation {calculation_id} for product {product_id}")

        # Verify product exists
        product = db_session.query(Product).filter_by(id=product_id).first()

        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Query BOM items joined with emission factors from PostgreSQL
        bom_rows = (
            db_session.query(
                BillOfMaterials,
                EmissionFactor,
                Product,
            )
            .join(Product, Product.id == BillOfMaterials.child_product_id)
            .outerjoin(EmissionFactor, EmissionFactor.id == BillOfMaterials.emission_factor_id)
            .filter(BillOfMaterials.parent_product_id == product_id)
            .all()
        )

        # Build emission factor lookup by activity_name for fallback matching
        all_efs = db_session.query(EmissionFactor).all()
        ef_by_name = {ef.activity_name: ef for ef in all_efs}

        # Calculate CO2e per component
        total_co2e = 0.0
        materials_co2e = 0.0
        energy_co2e = 0.0
        transport_co2e = 0.0
        breakdown = {}

        for bom_item, ef, child_product in bom_rows:
            quantity = float(bom_item.quantity or 0)

            # If no direct emission_factor_id link, fall back to name matching
            if ef is None and child_product:
                name_lower = child_product.name.lower()
                code_normalized = re.sub(r"_?\d+$", "", child_product.code.lower().replace("-", "_"))
                name_underscored = name_lower.replace(" ", "_")
                ef = ef_by_name.get(name_lower) or ef_by_name.get(code_normalized) or ef_by_name.get(name_underscored)

            factor_value = float(ef.co2e_factor if ef and ef.co2e_factor else 0)
            component_co2e = quantity * factor_value

            component_name = child_product.name if child_product else "Unknown"
            breakdown[component_name] = round(component_co2e, 6)
            total_co2e += component_co2e

            # Categorize by component name heuristics
            name_lower = component_name.lower()
            if "electricity" in name_lower or "energy" in name_lower or "grid" in name_lower:
                energy_co2e += component_co2e
            elif "transport" in name_lower or "truck" in name_lower or "ship" in name_lower:
                transport_co2e += component_co2e
            else:
                materials_co2e += component_co2e

        # Calculate execution time
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update calculation record with results
        calculation.status = "completed"
        calculation.total_co2e_kg = round(total_co2e, 6)
        calculation.materials_co2e = round(materials_co2e, 6)
        calculation.energy_co2e = round(energy_co2e, 6)
        calculation.transport_co2e = round(transport_co2e, 6)
        calculation.calculation_time_ms = elapsed_ms
        calculation.calculation_method = "SQL_DirectCalculation"

        # Store detailed breakdown in JSON field
        calculation.breakdown = breakdown

        db_session.commit()

        logger.info(
            f"Calculation {calculation_id} completed: "
            f"{total_co2e:.3f} kg CO2e in {elapsed_ms}ms"
        )

    except ValueError as e:
        # Product not found or validation error
        logger.error(f"Calculation {calculation_id} validation error: {e}")

        calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()
        if calculation:
            calculation.status = "failed"
            if not calculation.calculation_metadata:
                calculation.calculation_metadata = {}
            calculation.calculation_metadata["error_message"] = str(e)
            db_session.commit()

    except Exception as e:
        # Unexpected error
        logger.error(f"Calculation {calculation_id} failed with error: {e}", exc_info=True)

        calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()
        if calculation:
            calculation.status = "failed"
            if not calculation.calculation_metadata:
                calculation.calculation_metadata = {}
            calculation.calculation_metadata["error_message"] = f"Calculation error: {str(e)}"
            db_session.commit()

    finally:
        db_session.close()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/calculate",
    response_model=CalculationStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start PCF calculation",
    description="Start async calculation and return immediately with calculation_id for polling"
)
def start_calculation(
    request: CalculationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> CalculationStartResponse:
    """
    Start async PCF calculation for a product.

    This endpoint returns immediately (202 Accepted) with a calculation_id.
    The actual calculation runs in the background. Clients should poll
    GET /calculations/{id} to check status and retrieve results.

    Workflow:
    1. Validate product_id exists (returns 202 even if invalid, error in status)
    2. Create calculation record with status="pending"
    3. Queue background task to perform calculation
    4. Return 202 with calculation_id

    Request Body:
    - product_id: UUID of product to calculate
    - calculation_type: Type of calculation (default: cradle_to_gate)
        Valid values: cradle_to_gate, cradle_to_grave, gate_to_gate

    Returns:
    - 202 Accepted: Calculation started
        - calculation_id: UUID for polling status
        - status: "in_progress" (always)

    - 422 Unprocessable Entity: Invalid request (missing product_id or invalid calculation_type)
    """
    # Generate calculation ID
    calc_id = generate_uuid()

    logger.info(
        f"Received calculation request: calc_id={calc_id}, "
        f"product_id={request.product_id}, type={request.calculation_type}"
    )

    # TASK-BE-P9-001: Validate product exists before creating calculation record
    # This prevents FK violation and returns proper 404 for nonexistent products
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        logger.warning(f"Calculation requested for nonexistent product: {request.product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {request.product_id}"
        )

    # Create initial calculation record
    try:
        calculation = PCFCalculation(
            id=calc_id,
            product_id=request.product_id,
            calculation_type=request.calculation_type,  # Use enum value
            status="pending",
            total_co2e_kg=0.0,  # Placeholder until calculation completes
            created_at=datetime.now(UTC)
        )

        db.add(calculation)
        db.commit()

    except Exception as e:
        logger.error(f"Failed to create calculation record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start calculation"
        )

    # Queue background task
    # Background task creates its own session (request session may close)
    background_tasks.add_task(
        execute_calculation,
        calc_id,
        request.product_id,
        request.calculation_type,  # Use enum value
    )

    logger.info(f"Calculation {calc_id} queued for background processing")

    return CalculationStartResponse(
        calculation_id=calc_id,
        status="in_progress"
    )


@router.get(
    "/calculations/{calculation_id}",
    response_model=CalculationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get calculation status",
    description="Poll for calculation status and results"
)
def get_calculation_status(
    calculation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> CalculationStatusResponse:
    """
    Get current status and results of a calculation.

    Clients should poll this endpoint after receiving a calculation_id
    from POST /calculate. Poll until status changes to "completed" or "failed".

    Recommended polling strategy:
    - Poll every 200ms for first 5 seconds
    - Then every 1s until complete
    - Timeout after 30s for simple products

    Path Parameters:
    - calculation_id: UUID returned from POST /calculate

    Returns:
    - 200 OK: Calculation found
        - status="pending": Calculation queued but not yet started
        - status="in_progress": Still calculating (no result yet)
        - status="completed": Done (includes total_co2e_kg, breakdown, and category totals)
        - status="failed": Error occurred (includes error_message)

    - 404 Not Found: calculation_id not found

    Example Response (completed):
    {
        "calculation_id": "abc123...",
        "status": "completed",
        "product_id": "xyz789...",
        "total_co2e_kg": 2.05,
        "materials_co2e": 1.80,
        "energy_co2e": 0.15,
        "transport_co2e": 0.10,
        "calculation_time_ms": 150,
        "breakdown": {
            "cotton": 1.50,
            "polyester": 0.30,
            "electricity_us": 0.15,
            "truck_transport": 0.10
        }
    }
    """
    # Query calculation record
    calculation = db.query(PCFCalculation).filter_by(id=calculation_id).first()

    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation not found"
        )

    # Map internal status values to frontend-compatible values
    # TASK-API-P7-027: Ensure 'running' and 'processing' are mapped to 'in_progress'
    status_value = calculation.status
    if status_value in ("running", "processing"):
        status_value = "in_progress"

    # Build response based on status
    response_data = {
        "calculation_id": calculation.id,
        "status": status_value,
        "product_id": calculation.product_id,
        "created_at": calculation.created_at.isoformat() if calculation.created_at else None
    }

    # Add result fields if completed
    if calculation.status == "completed":
        response_data.update({
            "total_co2e_kg": float(calculation.total_co2e_kg) if calculation.total_co2e_kg else 0.0,
            "materials_co2e": float(calculation.materials_co2e) if calculation.materials_co2e else None,
            "energy_co2e": float(calculation.energy_co2e) if calculation.energy_co2e else None,
            "transport_co2e": float(calculation.transport_co2e) if calculation.transport_co2e else None,
            "calculation_time_ms": calculation.calculation_time_ms,
            # TASK-FE-P8-003: Include breakdown for expandable items in frontend
            "breakdown": calculation.breakdown if calculation.breakdown else None
        })

    # Add error message if failed
    if calculation.status == "failed":
        error_msg = None
        if calculation.calculation_metadata:
            error_msg = calculation.calculation_metadata.get("error_message")
        if not error_msg and calculation.input_data:
            error_msg = calculation.input_data.get("error_message")

        response_data["error_message"] = error_msg or "Calculation failed"

    logger.debug(f"Returning status for calculation {calculation_id}: {status_value}")

    return CalculationStatusResponse(**response_data)
