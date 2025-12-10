"""
Health check endpoints for PCF Calculator API.

TASK-BE-P5-001: Celery + Redis Setup

This module provides health check endpoints for monitoring:
- celery_health: Check Celery worker health and broker connectivity

Usage:
    GET /api/v1/health/celery

    Response (healthy):
    {
        "status": "healthy",
        "workers": 2,
        "broker": "connected"
    }

    Response (unhealthy):
    {
        "status": "unhealthy",
        "message": "No workers responding"
    }
"""

from typing import Dict, Any

from fastapi import APIRouter

from backend.core.celery_app import celery_app


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/celery")
async def celery_health() -> Dict[str, Any]:
    """
    Check Celery worker health.

    Pings all Celery workers to verify they are responsive and
    the broker connection is working.

    Returns:
        dict: Health status including:
            - status: "healthy" or "unhealthy"
            - workers: Number of responsive workers (if healthy)
            - broker: Broker connection status (if healthy)
            - message: Error message (if unhealthy)
            - error: Exception message (if error occurred)
    """
    try:
        # Ping workers with 1 second timeout
        ping_response = celery_app.control.ping(timeout=1.0)

        if not ping_response:
            return {
                "status": "unhealthy",
                "message": "No workers responding"
            }

        return {
            "status": "healthy",
            "workers": len(ping_response),
            "broker": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
