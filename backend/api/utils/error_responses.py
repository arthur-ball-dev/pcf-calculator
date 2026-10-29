"""
Shared error response utilities for API routes.

Provides standardized error response formatting used across
all route modules to ensure consistent error structure.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi.responses import JSONResponse


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[List[dict]] = None,
) -> JSONResponse:
    """
    Create a standardized JSON error response.

    Used by route handlers that return JSONResponse directly
    (e.g., products.py for validation errors).

    Args:
        status_code: HTTP status code
        code: Application error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        details: List of error detail dicts with field/message

    Returns:
        JSONResponse with standardized error body
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            },
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def create_error_dict(
    code: str,
    message: str,
    details: Optional[list] = None,
) -> dict:
    """
    Create a standardized error response dict.

    Used by admin route handlers that pass error dicts to
    HTTPException detail parameter.

    Args:
        code: Application error code
        message: Human-readable error message
        details: List of error detail dicts

    Returns:
        Dict with standardized error structure
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
