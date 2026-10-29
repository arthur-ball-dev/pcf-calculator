"""
Shared error response utilities for API routes.

The API has one error format (#47, knowledge/api/api-specifications.md):

    {
        "error": {"code": "...", "message": "...", "details": [...]},
        "request_id": "req_<12 hex>",
        "timestamp": "<ISO-8601, UTC>"
    }

Three ways to produce it:

- ``create_error_response`` returns a JSONResponse (route handlers that
  return early, e.g. products.py).
- ``create_error_dict`` returns the body; admin routes pass it to
  ``HTTPException(detail=...)`` and the app-level handler in
  backend/api/error_handlers.py sends it as the body, unwrapped.
- A plain ``HTTPException(detail="message")`` is wrapped by the same handler
  with a code derived from the status (NOT_FOUND, UNAUTHORIZED, ...).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi.responses import JSONResponse


def create_error_dict(
    code: str,
    message: str,
    details: Optional[list] = None,
) -> dict:
    """
    Build the standardized error body.

    Args:
        code: Application error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        details: List of error detail dicts ({"field", "message"[, "type"]})

    Returns:
        Dict with the standardized error structure
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


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[List[dict]] = None,
    headers: Optional[dict] = None,
) -> JSONResponse:
    """
    Build a standardized JSON error response.

    Args:
        status_code: HTTP status code
        code: Application error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        details: List of error detail dicts with field/message
        headers: Extra response headers (e.g. WWW-Authenticate)

    Returns:
        JSONResponse with the standardized error body
    """
    return JSONResponse(
        status_code=status_code,
        content=create_error_dict(code, message, details),
        headers=headers,
    )
