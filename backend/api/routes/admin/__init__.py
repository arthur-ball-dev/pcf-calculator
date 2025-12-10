"""
Admin API Routes Module.

TASK-API-P5-001: Admin Data Sources Endpoints

Combines all admin sub-routers into a single admin router:
- Data sources management
- Sync logs viewing
- Coverage statistics

All routes are prefixed with /admin.
"""

from fastapi import APIRouter

from backend.api.routes.admin.data_sources import router as data_sources_router
from backend.api.routes.admin.sync_logs import router as sync_logs_router
from backend.api.routes.admin.coverage import router as coverage_router

# Create combined admin router
router = APIRouter(prefix="/admin", tags=["admin"])

# Include sub-routers
router.include_router(data_sources_router)
router.include_router(sync_logs_router)
router.include_router(coverage_router)

__all__ = ["router"]
