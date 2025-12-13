"""
Calculations API Routes
TASK-API-002: Implementation of async calculation endpoints
TASK-BE-P5-010: Fix Backend Test Failures - Add enum validation for calculation_type

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
from typing import Optional, Literal
from datetime import datetime, UTC
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from backend.database.connection import get_db
from backend.models import Product, PCFCalculation, generate_uuid
from backend.calculator.pcf_calculator import PCFCalculator

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Types
# ============================================================================

class CalculationType(str, Enum):
    """Valid calculation types for PCF calculations."""
    cradle_to_gate = "cradle_to_gate"
    cradle_to_grave = "cradle_to_grave"
    gate_to_gate = "gate_to_gate"


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class CalculationRequest(BaseModel):
    """Request model for POST /calculate"""
    product_id: str = Field(..., description="UUID of product to calculate PCF for")
    calculation_type: CalculationType = Field(
        default=CalculationType.cradle_to_gate,
        description="Type of calculation (cradle_to_gate, cradle_to_grave, gate_to_gate)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "calculation_type": "cradle_to_gate"
            }
        }


class CalculationStartResponse(BaseModel):
    """Response model for POST /calculate (202 Accepted)"""
    calculation_id: str = Field(..., description="UUID for tracking calculation status")
    status: str = Field(..., description="Initial status (always 'processing')")

    class Config:
        json_schema_extra = {
            "example": {
                "calculation_id": "calc123abc456def789ghi012jkl345mno",
                "status": "processing"
            }
        }


class CalculationStatusResponse(BaseModel):
    """Response model for GET /calculations/{id}"""
    calculation_id: str = Field(..., description="Calculation UUID")
    status: str = Field(..., description="Current status: processing, completed, failed")
    product_id: Optional[str] = Field(None, description="Product UUID")
    created_at: Optional[str] = Field(None, description="Calculation start time (ISO 8601)")

    # Fields present when completed
    total_co2e_kg: Optional[float] = Field(None, description="Total emissions in kg CO2e")
    materials_co2e: Optional[float] = Field(None, description="Materials emissions in kg CO2e")
    energy_co2e: Optional[float] = Field(None, description="Energy emissions in kg CO2e")
    transport_co2e: Optional[float] = Field(None, description="Transport emissions in kg CO2e")
    calculation_time_ms: Optional[int] = Field(None, description="Calculation duration in milliseconds")

    # Fields present when failed
    error_message: Optional[str] = Field(None, description="Error details if status=failed")

    class Config:
        json_schema_extra = {
            "example": {
                "calculation_id": "calc123abc456def789ghi012jkl345mno",
                "status": "completed",
                "product_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "created_at": "2025-11-02T12:34:56.789Z",
                "total_co2e_kg": 2.05,
                "materials_co2e": 1.80,
                "energy_co2e": 0.15,
                "transport_co2e": 0.10,
                "calculation_time_ms": 150
            }
        }


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
    db_session: Session
):
    """
    Background task: Execute PCF calculation using Brightway2.

    This function runs asynchronously in the background after returning
    202 Accepted to the client. Updates database with results or error.

    Lifecycle:
    1. Update status to 'running'
    2. Verify product exists
    3. Perform calculation using PCFCalculator
    4. Update status to 'completed' with results
    5. Handle errors and update status to 'failed'

    Args:
        calculation_id: UUID of calculation record
        product_id: UUID of product to calculate
        calculation_type: Type of calculation
        db_session: SQLAlchemy database session
    """
    import time
    start_time = time.time()

    try:
        # Update status to 'running'
        calculation = db_session.query(PCFCalculation).filter_by(id=calculation_id).first()

        if not calculation:
            logger.error(f"Calculation {calculation_id} not found in database")
            return

        calculation.status = "running"
        db_session.commit()

        logger.info(f"Starting calculation {calculation_id} for product {product_id}")

        # Verify product exists
        product = db_session.query(Product).filter_by(id=product_id).first()

        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Initialize calculator and perform calculation
        calculator = PCFCalculator()
        result = calculator.calculate_product(product_id, db_session)

        # Calculate execution time
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update calculation record with results
        calculation.status = "completed"
        calculation.total_co2e_kg = result["total_co2e_kg"]
        calculation.materials_co2e = result.get("breakdown_by_category", {}).get("materials", 0.0)
        calculation.energy_co2e = result.get("breakdown_by_category", {}).get("energy", 0.0)
        calculation.transport_co2e = result.get("breakdown_by_category", {}).get("transport", 0.0)
        calculation.calculation_time_ms = elapsed_ms
        calculation.calculation_method = "Brightway2_PCFCalculator"

        # Store detailed breakdown in JSON field
        calculation.breakdown = result.get("breakdown", {})

        db_session.commit()

        logger.info(
            f"Calculation {calculation_id} completed: "
            f"{result['total_co2e_kg']:.3f} kg CO2e in {elapsed_ms}ms"
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
async def start_calculation(
    request: CalculationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
        - status: "processing" (always)

    - 422 Unprocessable Entity: Invalid request (missing product_id or invalid calculation_type)
    """
    # Generate calculation ID
    calc_id = generate_uuid()

    logger.info(
        f"Received calculation request: calc_id={calc_id}, "
        f"product_id={request.product_id}, type={request.calculation_type.value}"
    )

    # Create initial calculation record
    # Note: We don't validate product_id exists here to avoid blocking
    # The background task will handle validation and set status to failed if needed
    try:
        calculation = PCFCalculation(
            id=calc_id,
            product_id=request.product_id,
            calculation_type=request.calculation_type.value,  # Use enum value
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
    # Important: Pass a NEW database session to background task
    # FastAPI's dependency injection doesn't work in background tasks
    background_tasks.add_task(
        execute_calculation,
        calc_id,
        request.product_id,
        request.calculation_type.value,  # Use enum value
        db  # This session will be used by background task
    )

    logger.info(f"Calculation {calc_id} queued for background processing")

    return CalculationStartResponse(
        calculation_id=calc_id,
        status="processing"
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
    db: Session = Depends(get_db)
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
        - status="processing": Still calculating (no result yet)
        - status="completed": Done (includes total_co2e_kg and breakdown)
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
        "calculation_time_ms": 150
    }
    """
    # Query calculation record
    calculation = db.query(PCFCalculation).filter_by(id=calculation_id).first()

    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation not found"
        )

    # Build response based on status
    response_data = {
        "calculation_id": calculation.id,
        "status": calculation.status,
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
            "calculation_time_ms": calculation.calculation_time_ms
        })

    # Add error message if failed
    if calculation.status == "failed":
        error_msg = None
        if calculation.calculation_metadata:
            error_msg = calculation.calculation_metadata.get("error_message")
        if not error_msg and calculation.input_data:
            error_msg = calculation.input_data.get("error_message")

        response_data["error_message"] = error_msg or "Calculation failed"

    logger.debug(f"Returning status for calculation {calculation_id}: {calculation.status}")

    return CalculationStatusResponse(**response_data)
