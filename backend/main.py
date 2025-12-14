"""
FastAPI application entry point
PCF Calculator MVP - Product Carbon Footprint Calculator
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.errors import ServerErrorMiddleware

from backend.config import settings
from backend.middleware import SecurityHeadersMiddleware
from backend.api.routes.products import router as products_router
from backend.api.routes.calculations import router as calculations_router
from backend.api.routes.emission_factors import router as emission_factors_router
from backend.api.routes.admin import router as admin_router
from backend.calculator.brightway_setup import initialize_brightway
from backend.calculator.emission_factor_sync import sync_emission_factors
from backend.database.connection import db_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# Startup event: Initialize Brightway2 and sync emission factors
@app.on_event("startup")
async def startup_event():
    """Initialize Brightway2 and sync emission factors on server startup."""
    try:
        logger.info("Initializing Brightway2 for PCF calculations...")
        initialize_brightway()

        # Sync emission factors from SQLite to Brightway2
        with db_context() as session:
            result = sync_emission_factors(db_session=session)
            logger.info(f"Synced {result['synced_count']} emission factors to Brightway2")
    except Exception as e:
        logger.error(f"Failed to initialize Brightway2: {e}", exc_info=True)
        # Don't fail startup - allow server to run for debugging


# Configure CORS middleware
# Order: CORS should be first to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


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