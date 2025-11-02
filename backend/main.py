"""
FastAPI application entry point
PCF Calculator MVP - Product Carbon Footprint Calculator
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.errors import ServerErrorMiddleware

from backend.config import settings
from backend.middleware import SecurityHeadersMiddleware
from backend.api.routes.products import router as products_router

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
    description="Product Carbon Footprint Calculator MVP"
)

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
                "code": "CALCULATION_FAILED",
                "message": "Internal server error",
                "details": []
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Include API routers
app.include_router(products_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        dict: Status and version information
    """
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
