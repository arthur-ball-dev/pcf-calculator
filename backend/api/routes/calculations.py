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
from decimal import Decimal
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.api.dependencies import get_calculation_service
from backend.models.user import User
from backend.auth.dependencies import get_optional_user
from backend.domain.entities.calculation import (
    BOMLineInput,
    Calculation,
    CreateCalculationRequest,
)
from backend.domain.entities.errors import DomainValidationError, ProductNotFoundError
from backend.domain.services.calculation_service import CalculationService
from backend.schemas import (
    CalculationRequest,
    CalculationStartResponse,
    CalculationStatusResponse,
)
# The background task lives in the service layer (issue #34); tests patch it through this module.
from backend.services.calculation_runner import execute_calculation

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["calculations"])


# ============================================================================
# Background Task Functions
# ============================================================================

def get_background_session_factory() -> Callable[[], Session]:
    """
    Session factory used by the background calculation task.

    Exposed as a FastAPI dependency so tests can override it and let the task
    share the request's transactional session.
    """
    from backend.database.connection import SessionLocal
    return SessionLocal


def _status_response(calculation: Calculation) -> CalculationStatusResponse:
    """Build the polling response: result fields only once completed, the error once failed."""
    response_data: Dict[str, Any] = {
        "calculation_id": calculation.id,
        "status": calculation.public_status,
        "product_id": calculation.product_id,
        "created_at": calculation.created_at.isoformat() if calculation.created_at else None,
    }

    if calculation.status == "completed":
        response_data.update({
            "total_co2e_kg": calculation.total_co2e_kg,
            "materials_co2e": calculation.materials_co2e,
            "energy_co2e": calculation.energy_co2e,
            "transport_co2e": calculation.transport_co2e,
            "calculation_time_ms": calculation.calculation_time_ms,
            # TASK-FE-P8-003: Include breakdown for expandable items in frontend
            "breakdown": calculation.breakdown if calculation.breakdown else None,
        })

    if calculation.status == "failed":
        response_data["error_message"] = calculation.error_message or "Calculation failed"

    return CalculationStatusResponse(**response_data)


# ============================================================================
# API Endpoints
# ============================================================================

def _bom_lines(request: CalculationRequest) -> Optional[tuple]:
    """The submitted BOM as domain rows (#195), or None to calculate the catalog BOM."""
    if request.bom is None:
        return None
    return tuple(
        BOMLineInput(
            name=line.name,
            quantity=Decimal(str(line.quantity)),
            unit=line.unit,
            category=line.category,
            emission_factor_id=line.emission_factor_id,
        )
        for line in request.bom
    )


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
    service: CalculationService = Depends(get_calculation_service),
    current_user: Optional[User] = Depends(get_optional_user),
    session_factory: Callable[[], Session] = Depends(get_background_session_factory),
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
    logger.info(
        f"Received calculation request: product_id={request.product_id}, "
        f"type={request.calculation_type}"
    )

    try:
        calculation = service.create_calculation(
            CreateCalculationRequest(
                product_id=request.product_id,
                calculation_type=request.calculation_type,
                bom=_bom_lines(request),
            )
        )
    except (ProductNotFoundError, DomainValidationError):
        # Handled by backend/api/error_handlers.py: 404 PRODUCT_NOT_FOUND, 422 VALIDATION_ERROR
        raise
    except Exception as e:
        logger.error(f"Failed to create calculation record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start calculation"
        )

    calc_id = calculation.id

    # Queue background task
    # Background task creates its own session (request session may close)
    background_tasks.add_task(
        execute_calculation,
        calc_id,
        request.product_id,
        request.calculation_type,
        session_factory,
        calculation.resolved_bom,
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
    service: CalculationService = Depends(get_calculation_service),
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
    # Raises CalculationNotFoundError, handled by backend/api/error_handlers.py as 404
    calculation = service.get_calculation(calculation_id)

    logger.debug(
        f"Returning status for calculation {calculation_id}: {calculation.public_status}"
    )

    return _status_response(calculation)
