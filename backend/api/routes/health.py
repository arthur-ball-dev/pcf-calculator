"""
Health check endpoints for PCF Calculator API.

TASK-BE-P5-001: Celery + Redis Setup
TASK-DB-P9-001: Database connection pool health check

This module provides health check endpoints for monitoring:
- celery_health: Check Celery worker health and broker connectivity
- database_health: Check database connection pool status

Usage:
    GET /api/v1/health/celery
    GET /api/v1/health/db

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
from backend.database.connection import get_pool_status, POOL_CONFIG


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


@router.get("/db")
async def database_health() -> Dict[str, Any]:
    """
    Check database connection pool health.

    Returns pool metrics useful for monitoring and alerting:
    - status: "healthy", "degraded", or "unhealthy"
    - pool: Connection pool metrics
    - config: Pool configuration (for reference)

    Health Criteria:
    - healthy: checked_out < pool_size + 10, overflow < 10
    - degraded: approaching limits but still functional
    - unhealthy: pool exhaustion or errors

    TASK-DB-P9-001: Added for production health monitoring.

    Returns:
        dict: Health status including:
            - status: "healthy", "degraded", or "unhealthy"
            - pool: Current pool metrics
            - config: Pool configuration values
            - error: Exception message (if error occurred)
    """
    try:
        pool_status = get_pool_status()

        # Calculate health based on pool utilization
        pool_size = pool_status["pool_size"]
        checked_out = pool_status["checked_out"]
        overflow = pool_status["overflow"]
        max_overflow = POOL_CONFIG.get("max_overflow", 20)

        # Determine health status
        if checked_out < pool_size and overflow == 0:
            # Well within limits
            status = "healthy"
        elif checked_out < pool_size + max_overflow // 2:
            # Approaching limits but OK
            status = "healthy"
        elif checked_out < pool_size + max_overflow:
            # Getting close to exhaustion
            status = "degraded"
        else:
            # Pool exhausted
            status = "unhealthy"

        return {
            "status": status,
            "pool": pool_status,
            "config": {
                "pool_size": POOL_CONFIG["pool_size"],
                "max_overflow": POOL_CONFIG["max_overflow"],
                "pool_timeout": POOL_CONFIG["pool_timeout"],
                "pool_recycle": POOL_CONFIG["pool_recycle"],
                "pool_pre_ping": POOL_CONFIG["pool_pre_ping"],
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
