"""
Application-level error handlers: one response format for every error (#47).

Every error leaves the API as

    {"error": {"code", "message", "details"}, "request_id", "timestamp"}

(see knowledge/api/api-specifications.md). The handlers here cover the
producers that would otherwise fall back to FastAPI's ``{"detail": ...}``:

- ``HTTPException`` raised anywhere (routes, auth dependencies). A string
  detail becomes ``error.message`` with a code derived from the status; a
  detail that is already an envelope (``create_error_dict``) is sent as the
  body, not nested under ``detail``. Response headers (WWW-Authenticate,
  Retry-After) are preserved.
- ``RequestValidationError`` (pydantic): the per-field errors are listed under
  ``error.details`` as ``{"field", "message", "type"}``.
- The domain errors (TASK-BE-P7-050) keep their specific codes.
- Any other exception: a generic 500 that leaks nothing.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.utils.error_responses import create_error_dict
from backend.domain.entities.errors import (
    CalculationNotFoundError,
    DomainValidationError,
    DuplicateEmissionFactorError,
    EmissionFactorNotFoundError,
    ProductNotFoundError,
)

logger = logging.getLogger(__name__)

# Default application error code for an HTTPException carrying only a message.
STATUS_CODE_TO_ERROR_CODE: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "VALIDATION_ERROR",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_ERROR",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}
FALLBACK_ERROR_CODE = "HTTP_ERROR"


def error_code_for_status(status_code: int) -> str:
    """Application error code used when a route raised a bare HTTPException."""
    return STATUS_CODE_TO_ERROR_CODE.get(status_code, FALLBACK_ERROR_CODE)


def _envelope_from_detail(status_code: int, detail: Any) -> dict:
    """Turn an HTTPException's detail into the error envelope."""
    if isinstance(detail, dict) and isinstance(detail.get("error"), dict):
        # Already built with create_error_dict (admin routes): send as-is,
        # filling in anything a hand-written dict left out.
        error = detail["error"]
        envelope = create_error_dict(
            code=str(error.get("code") or error_code_for_status(status_code)),
            message=str(error.get("message") or "Request failed"),
            details=list(error.get("details") or []),
        )
        for key in ("request_id", "timestamp"):
            if isinstance(detail.get(key), str):
                envelope[key] = detail[key]
        return envelope

    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("msg") or detail)
        return create_error_dict(code=error_code_for_status(status_code), message=message)

    return create_error_dict(code=error_code_for_status(status_code), message=str(detail))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTPException (FastAPI's and Starlette's) in the error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope_from_detail(exc.status_code, exc.detail),
        headers=getattr(exc, "headers", None),
    )


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic request validation errors as VALIDATION_ERROR with field details."""
    details = [
        {
            "field": ".".join(str(part) for part in error.get("loc", ())),
            "message": str(error.get("msg", "")),
            "type": str(error.get("type", "")),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_dict(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
        ),
    )


async def product_not_found_handler(request: Request, exc: ProductNotFoundError) -> JSONResponse:
    logger.warning(f"Product not found: {exc.product_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_dict(
            code="PRODUCT_NOT_FOUND",
            message=str(exc),
            details=[
                {"field": "product_id", "message": f"No product exists with ID {exc.product_id}"}
            ],
        ),
    )


async def calculation_not_found_handler(
    request: Request, exc: CalculationNotFoundError
) -> JSONResponse:
    logger.warning(f"Calculation not found: {exc.calculation_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_dict(
            code="CALCULATION_NOT_FOUND",
            message=str(exc),
            details=[
                {
                    "field": "calculation_id",
                    "message": f"No calculation exists with ID {exc.calculation_id}",
                }
            ],
        ),
    )


async def domain_validation_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
    logger.warning(f"Domain validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_dict(code="VALIDATION_ERROR", message=exc.message, details=exc.details),
    )


async def emission_factor_not_found_handler(
    request: Request, exc: EmissionFactorNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_dict(
            code=error_code_for_status(status.HTTP_404_NOT_FOUND), message=str(exc)
        ),
    )


async def duplicate_emission_factor_handler(
    request: Request, exc: DuplicateEmissionFactorError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_dict(
            code=error_code_for_status(status.HTTP_409_CONFLICT), message=str(exc)
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the full error server-side; return a generic body to the client."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_dict(code="INTERNAL_ERROR", message="Internal server error"),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach every handler to the application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(ProductNotFoundError, product_not_found_handler)
    app.add_exception_handler(CalculationNotFoundError, calculation_not_found_handler)
    app.add_exception_handler(DomainValidationError, domain_validation_handler)
    app.add_exception_handler(EmissionFactorNotFoundError, emission_factor_not_found_handler)
    app.add_exception_handler(DuplicateEmissionFactorError, duplicate_emission_factor_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
