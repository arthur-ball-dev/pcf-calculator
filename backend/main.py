"""
FastAPI application entry point
PCF Calculator MVP - Product Carbon Footprint Calculator

TASK-BE-P7-018: Added JWT authentication routes and middleware.
TASK-BE-P7-020: Added rate limiting middleware with per-endpoint limits.
TASK-BE-P7-050: Added domain exception handlers for clean architecture.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.errors import ServerErrorMiddleware

from backend.config import settings
from backend.middleware import (
    SecurityHeadersMiddleware,
    ExtendedCORSMiddleware,
    RateLimitMiddleware,
    get_storage,
)
from backend.api.routes.products import router as products_router
from backend.api.routes.calculations import router as calculations_router
from backend.api.routes.emission_factors import router as emission_factors_router
from backend.api.routes.admin import router as admin_router
from backend.api.routes.auth import router as auth_router
from backend.database.connection import db_context
from backend.database.seeds.data_sources import seed_data_sources, verify_data_sources

# Domain layer error imports (TASK-BE-P7-050)
from backend.domain.entities.errors import (
    ProductNotFoundError,
    CalculationNotFoundError,
    DomainValidationError,
    DuplicateProductError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="PCF Calculator API",
    version="1.0.0",
    description=(
        "Product Carbon Footprint Calculator MVP - A full-stack application for calculating "
        "cradle-to-gate carbon emissions using Bill of Materials (BOM) data and emission factors "
        "from EPA, DEFRA, and Ecoinvent databases. Implements ISO 14067 and GHG Protocol standards."
    )
)

# Startup event: Initialize Brightway2, seed data sources, and sync emission factors
@app.on_event("startup")
async def startup_event():
    """
    Initialize application on server startup.

    Performs the following initialization steps:
    1. Seeds data_sources table with EPA, DEFRA, Exiobase entries (idempotent)
    2. Initializes Brightway2 for LCA calculations (non-blocking via thread pool)

    TASK-CALC-P7-016: Brightway2 initialization now uses asyncio.to_thread()
    to prevent blocking the FastAPI event loop during startup.
    """
    # Step 1: Seed data sources (idempotent - safe to call on every startup)
    try:
        with db_context() as session:
            count = seed_data_sources(session, skip_existing=True)
            if count > 0:
                logger.info(f"Seeded {count} new data sources (EPA, DEFRA, Exiobase)")
            else:
                logger.info("Data sources already seeded, skipping")

            # Verify seeding was successful
            if verify_data_sources(session):
                logger.info("Data sources verification passed")
            else:
                logger.warning("Data sources verification failed - some sources may be missing")
    except Exception as e:
        logger.error(f"Failed to seed data sources: {e}", exc_info=True)
        # Do not fail startup - allow server to run for debugging

    # Step 2: Initialize Brightway2 asynchronously (non-blocking)
    # TASK-CALC-P7-016: Use async initialization to prevent blocking the event loop
    try:
        from backend.calculator.pcf_calculator import initialize_pcf_calculator
        logger.info("Starting Brightway2 initialization (non-blocking)...")
        await initialize_pcf_calculator()
        logger.info("Brightway2 initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize Brightway2: {e}", exc_info=True)
        # Do not fail startup - allow server to run for debugging


# Configure CORS middleware
# Order: CORS should be first to handle preflight requests
#
# Security Configuration (TASK-BE-P7-017):
# - allow_methods: Explicit list of HTTP methods used by the frontend
#   (GET, POST, PUT, DELETE for CRUD, OPTIONS for CORS preflight)
# - allow_headers: Explicit list of headers needed by the frontend
#   (Authorization for auth tokens, Content-Type for JSON, X-Request-ID for tracing)
# - expose_headers: Headers that the frontend can read from responses
#   (X-Request-ID for tracing, X-Total-Count for pagination)
#
# Using ExtendedCORSMiddleware to include expose_headers in preflight responses
# for better client compatibility.
#
# Reference: Code Review Report 2025-12-18 (Issue #6)
app.add_middleware(
    ExtendedCORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",      # For JWT auth tokens (TASK-BE-P7-018)
        "Content-Type",       # For JSON requests
        "X-Request-ID",       # For request tracing
        "Accept",             # Standard header
        "Accept-Language",    # Internationalization
        "Cache-Control",      # Caching hints
    ],
    expose_headers=[
        "X-Request-ID",       # Allow frontend to read request ID
        "X-Total-Count",      # For pagination
        "WWW-Authenticate",   # For auth errors (TASK-BE-P7-018)
        "X-RateLimit-Limit",      # Rate limit headers (TASK-BE-P7-020)
        "X-RateLimit-Remaining",  # Rate limit headers (TASK-BE-P7-020)
        "X-RateLimit-Reset",      # Rate limit headers (TASK-BE-P7-020)
        "Retry-After",            # Rate limit headers (TASK-BE-P7-020)
    ],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (TASK-BE-P7-020)
# Order: Rate limiting should be after CORS to ensure preflight requests pass,
# but before route handlers to protect against abuse.
#
# Configuration:
# - General endpoints: 100 requests/minute (configurable via RATE_LIMIT_GENERAL)
# - Calculation endpoints: 10 requests/minute (expensive operations)
# - Auth endpoints: 5 attempts/5 minutes (brute force protection)
# - Admin users: 10x higher limits (configurable via RATE_LIMIT_ADMIN_MULTIPLIER)
#
# Storage: Memory (default) or Redis (for distributed deployments)
rate_limit_storage = get_storage(settings.rate_limit_redis_url)
app.add_middleware(
    RateLimitMiddleware,
    storage=rate_limit_storage,
    default_limit=settings.RATE_LIMIT_GENERAL,
    window_seconds=60,
    endpoint_limits={
        "/api/v1/calculate": settings.RATE_LIMIT_CALCULATION,
        "/api/v1/auth/login": settings.RATE_LIMIT_AUTH_ATTEMPTS,
    },
    endpoint_windows={
        "/api/v1/auth/login": 300,  # 5 minute window for auth
    },
    endpoint_error_messages={
        "/api/v1/auth/login": "Too many login attempts. Please try again later.",
    },
    admin_multiplier=settings.RATE_LIMIT_ADMIN_MULTIPLIER,
    excluded_paths=["/health", "/docs", "/openapi.json", "/redoc"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with method, path, status code, and duration

    Args:
        request: Incoming HTTP request
        call_next: Next middleware/route handler in chain

    Returns:
        Response: HTTP response from downstream handlers
    """
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s"
        )

        return response
    except Exception as exc:
        # If exception occurs, still log it and re-raise
        # The exception handler below will handle it
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"error={type(exc).__name__} "
            f"duration={process_time:.3f}s"
        )
        raise


# ============================================================================
# Domain Exception Handlers (TASK-BE-P7-050)
# ============================================================================


@app.exception_handler(ProductNotFoundError)
async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
    """
    Handle ProductNotFoundError from domain layer.

    Maps domain ProductNotFoundError to HTTP 404 Not Found response.

    Args:
        request: HTTP request that caused the exception
        exc: ProductNotFoundError exception

    Returns:
        JSONResponse: 404 response with error details
    """
    logger.warning(f"Product not found: {exc.product_id}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": f"Product not found: {exc.product_id}",
            "error": {
                "code": "PRODUCT_NOT_FOUND",
                "message": str(exc),
                "details": [{"field": "product_id", "value": exc.product_id}]
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(CalculationNotFoundError)
async def calculation_not_found_handler(request: Request, exc: CalculationNotFoundError):
    """
    Handle CalculationNotFoundError from domain layer.

    Maps domain CalculationNotFoundError to HTTP 404 Not Found response.

    Args:
        request: HTTP request that caused the exception
        exc: CalculationNotFoundError exception

    Returns:
        JSONResponse: 404 response with error details
    """
    logger.warning(f"Calculation not found: {exc.calculation_id}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": f"Calculation not found: {exc.calculation_id}",
            "error": {
                "code": "CALCULATION_NOT_FOUND",
                "message": str(exc),
                "details": [{"field": "calculation_id", "value": exc.calculation_id}]
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(DomainValidationError)
async def domain_validation_error_handler(request: Request, exc: DomainValidationError):
    """
    Handle DomainValidationError from domain layer.

    Maps domain DomainValidationError to HTTP 422 Unprocessable Entity response.

    Args:
        request: HTTP request that caused the exception
        exc: DomainValidationError exception

    Returns:
        JSONResponse: 422 response with error details
    """
    logger.warning(f"Domain validation error: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.message,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": []
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(DuplicateProductError)
async def duplicate_product_handler(request: Request, exc: DuplicateProductError):
    """
    Handle DuplicateProductError from domain layer.

    Maps domain DuplicateProductError to HTTP 409 Conflict response.

    Args:
        request: HTTP request that caused the exception
        exc: DuplicateProductError exception

    Returns:
        JSONResponse: 409 response with error details
    """
    logger.warning(f"Duplicate product code: {exc.code}")

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": f"Product with code already exists: {exc.code}",
            "error": {
                "code": "DUPLICATE_PRODUCT",
                "message": str(exc),
                "details": [{"field": "code", "value": exc.code}]
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions globally

    Logs the full error details server-side but returns a generic
    error message to the client to avoid leaking sensitive information

    Returns error in format matching API specification
    (see knowledge/api-specifications.md lines 470-496)

    Args:
        request: HTTP request that caused the exception
        exc: Exception that was raised

    Returns:
        JSONResponse: Structured error response per API specification
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": []
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Include API routers
# TASK-BE-P7-018: Auth router for login/logout/refresh endpoints
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(calculations_router)
app.include_router(emission_factors_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        dict: Status and version information
    """
    return {"status": "healthy", "version": "1.0.0"}


# Serve frontend static files (React build output)
# Mount this AFTER API routes to avoid conflicts
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
