"""
Admin API Routes Module.

TASK-API-P5-001: Admin Data Sources Endpoints
TASK-BE-P7-018: Added JWT authentication (admin role required)

Combines all admin sub-routers into a single admin router:
- Data sources management
- Sync logs viewing
- Coverage statistics

All routes are prefixed with /admin and require admin role.
"""

from fastapi import APIRouter, Depends

from backend.api.routes.admin.data_sources import router as data_sources_router
from backend.api.routes.admin.sync_logs import router as sync_logs_router
from backend.api.routes.admin.coverage import router as coverage_router
from backend.auth.dependencies import require_admin

# Create combined admin router
# All admin routes require admin role (TASK-BE-P7-018)
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)

# Include sub-routers
router.include_router(data_sources_router)
router.include_router(sync_logs_router)
router.include_router(coverage_router)

__all__ = ["router"]
