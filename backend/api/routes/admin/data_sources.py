"""
Admin Data Sources API Routes.

TASK-API-P5-001: Admin Data Sources Endpoints
TASK-BE-P7-002: Activate Data Connector Admin Endpoints

Endpoints:
- GET /admin/data-sources - List all data sources with status
- GET /admin/data-sources/{id} - Get single data source details
- POST /admin/data-sources/{id}/sync - Trigger manual sync with real connectors

Contract References:
- phase5-contracts/admin-data-sources-contract.yaml
- phase5-contracts/admin-sync-contract.yaml
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.database.connection import get_db
from backend.models import DataSource, DataSyncLog, EmissionFactor
from backend.schemas.admin import (
    SourceTypeEnum,
    PriorityEnum,
    DataSourceListResponse,
    DataSourceListItem,
    DataSourceDetailResponse,
    DataSourceSummary,
    DataSourceStatistics,
    LastSyncInfo,
    SyncTriggerRequest,
    SyncTriggerResponse,
    SyncTriggerDataSource,
    ErrorResponse,
    ErrorBody,
    ErrorDetailItem,
)
from backend.services.data_ingestion.registry import (
    get_connector_class,
    is_connector_available,
)
from backend.services.data_ingestion.base import BaseDataIngestion


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(tags=["admin-data-sources"])


# ============================================================================
# Background Sync Execution
# ============================================================================


async def execute_sync_task(
    data_source_id: str,
    data_source_name: str,
    sync_log_id: str,
    force_refresh: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Execute data sync for a specific data source.

    This function runs the actual connector to fetch and import data.
    It creates its own async database session for the background task.

    Args:
        data_source_id: UUID of the data source to sync
        data_source_name: Name of the data source (used to look up connector)
        sync_log_id: UUID of the sync log entry to update
        force_refresh: Whether to force a full refresh
        dry_run: Whether to validate without persisting
    """
    from backend.config import settings

    # Create async engine and session for background task
    # Use SQLite async driver for SQLite databases
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite:///"):
        async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif database_url.startswith("postgresql://"):
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        async_url = database_url

    engine = create_async_engine(async_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

    try:
        async with async_session_maker() as session:
            # Get connector class
            ConnectorClass = get_connector_class(data_source_name)

            # Instantiate connector
            connector = ConnectorClass(
                db=session,
                data_source_id=data_source_id,
                sync_type="manual",
            )

            # Update sync log status to in_progress
            sync_log = await session.get(DataSyncLog, sync_log_id)
            if sync_log:
                sync_log.status = "in_progress"
                await session.commit()

            # Execute the sync
            logger.info(f"Starting sync for data source: {data_source_name}")
            result = await connector.execute_sync()
            logger.info(
                f"Sync completed for {data_source_name}: "
                f"{result.records_created} created, "
                f"{result.records_updated} updated, "
                f"{result.records_failed} failed"
            )

            # Update sync log with results
            sync_log = await session.get(DataSyncLog, sync_log_id)
            if sync_log:
                sync_log.status = result.status
                sync_log.completed_at = datetime.now(timezone.utc)
                sync_log.records_processed = result.records_processed
                sync_log.records_created = result.records_created
                sync_log.records_updated = result.records_updated
                sync_log.records_failed = result.records_failed
                await session.commit()

    except Exception as e:
        logger.error(f"Sync failed for {data_source_name}: {str(e)}")
        # Try to update sync log with failure
        try:
            async with async_session_maker() as session:
                sync_log = await session.get(DataSyncLog, sync_log_id)
                if sync_log:
                    sync_log.status = "failed"
                    sync_log.completed_at = datetime.now(timezone.utc)
                    sync_log.error_message = str(e)
                    await session.commit()
        except Exception as log_error:
            logger.error(f"Failed to update sync log: {log_error}")
        raise

    finally:
        await engine.dispose()


def execute_sync_in_background(
    data_source_id: str,
    data_source_name: str,
    sync_log_id: str,
    force_refresh: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Execute sync task in a background thread with its own event loop.

    This allows the API to return immediately while the sync runs.

    Args:
        data_source_id: UUID of the data source to sync
        data_source_name: Name of the data source
        sync_log_id: UUID of the sync log entry
        force_refresh: Whether to force a full refresh
        dry_run: Whether to validate without persisting
    """
    def run_async_sync():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                execute_sync_task(
                    data_source_id=data_source_id,
                    data_source_name=data_source_name,
                    sync_log_id=sync_log_id,
                    force_refresh=force_refresh,
                    dry_run=dry_run,
                )
            )
        except Exception as e:
            logger.error(f"Background sync failed: {e}")
        finally:
            loop.close()

    thread = threading.Thread(target=run_async_sync, daemon=True)
    thread.start()


# ============================================================================
# Dependency for Celery Task Trigger (Mock-friendly)
# ============================================================================


def default_sync_task_trigger(
    data_source_id: str,
    data_source_name: str,
    sync_log_id: str,
    force_refresh: bool = False,
    dry_run: bool = False,
    priority: str = "normal"
) -> str:
    """
    Default sync task trigger. Executes real connector in background.

    In production with Celery, this would call sync_data_source.apply_async().
    For now, we use threading for background execution.

    Args:
        data_source_id: UUID of the data source
        data_source_name: Name of the data source (for connector lookup)
        sync_log_id: UUID of the sync log entry
        force_refresh: Force full refresh
        dry_run: Validate without persisting
        priority: Task priority (for future Celery integration)

    Returns:
        Task ID string
    """
    task_id = f"sync-task-{uuid.uuid4().hex}"

    # Execute in background thread
    execute_sync_in_background(
        data_source_id=data_source_id,
        data_source_name=data_source_name,
        sync_log_id=sync_log_id,
        force_refresh=force_refresh,
        dry_run=dry_run,
    )

    return task_id


# Global variable for task trigger (allows test mocking)
_sync_task_trigger: Callable = default_sync_task_trigger


def get_sync_task_trigger() -> Callable:
    """Get the current sync task trigger function."""
    return _sync_task_trigger


def set_sync_task_trigger(trigger: Callable) -> None:
    """Set a custom sync task trigger (for testing)."""
    global _sync_task_trigger
    _sync_task_trigger = trigger


# ============================================================================
# Helper Functions
# ============================================================================


def get_last_sync_info(db: Session, data_source_id: str) -> Optional[LastSyncInfo]:
    """Get the most recent sync log for a data source."""
    last_log = (
        db.query(DataSyncLog)
        .filter(DataSyncLog.data_source_id == data_source_id)
        .order_by(DataSyncLog.started_at.desc())
        .first()
    )

    if not last_log:
        return None

    return LastSyncInfo(
        sync_id=last_log.id,
        status=last_log.status,
        started_at=last_log.started_at,
        completed_at=last_log.completed_at,
        records_processed=last_log.records_processed or 0,
        records_created=last_log.records_created or 0,
        records_updated=last_log.records_updated or 0,
        records_failed=last_log.records_failed or 0,
        error_message=last_log.error_message,
    )


def get_data_source_statistics(db: Session, data_source_id: str) -> DataSourceStatistics:
    """Calculate statistics for a data source."""
    # Total factors
    total_factors = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.data_source_id == data_source_id)
        .count()
    )

    # Active factors
    active_factors = (
        db.query(EmissionFactor)
        .filter(
            EmissionFactor.data_source_id == data_source_id,
            EmissionFactor.is_active == True,
        )
        .count()
    )

    # Average quality rating
    avg_quality = (
        db.query(func.avg(EmissionFactor.data_quality_rating))
        .filter(
            EmissionFactor.data_source_id == data_source_id,
            EmissionFactor.is_active == True,
        )
        .scalar()
    )

    # Geographies covered
    geographies_covered = (
        db.query(EmissionFactor.geography)
        .filter(
            EmissionFactor.data_source_id == data_source_id,
            EmissionFactor.is_active == True,
        )
        .distinct()
        .count()
    )

    # Year range
    min_year = (
        db.query(func.min(EmissionFactor.reference_year))
        .filter(
            EmissionFactor.data_source_id == data_source_id,
            EmissionFactor.is_active == True,
        )
        .scalar()
    )

    max_year = (
        db.query(func.max(EmissionFactor.reference_year))
        .filter(
            EmissionFactor.data_source_id == data_source_id,
            EmissionFactor.is_active == True,
        )
        .scalar()
    )

    return DataSourceStatistics(
        total_factors=total_factors,
        active_factors=active_factors,
        average_quality=float(avg_quality) if avg_quality else None,
        geographies_covered=geographies_covered,
        oldest_reference_year=min_year,
        newest_reference_year=max_year,
    )


def calculate_next_scheduled_sync(
    data_source: DataSource,
) -> Optional[datetime]:
    """Calculate next scheduled sync time based on frequency."""
    if data_source.sync_frequency == "manual":
        return None

    # Use last_sync_at or created_at as base
    base_time = data_source.last_sync_at or data_source.created_at
    if not base_time:
        return None

    # Calculate interval based on frequency
    frequency_days = {
        "daily": 1,
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,
    }

    days = frequency_days.get(data_source.sync_frequency, 14)
    next_sync = base_time + timedelta(days=days)

    # If next_sync is in the past, calculate from now
    now = datetime.now(timezone.utc)
    if next_sync < now:
        # Calculate how many intervals have passed
        elapsed = (now - base_time).days
        intervals_passed = (elapsed // days) + 1
        next_sync = base_time + timedelta(days=days * intervals_passed)

    return next_sync


def check_active_sync(db: Session, data_source_id: str) -> Optional[DataSyncLog]:
    """Check if there's an active sync for this data source."""
    return (
        db.query(DataSyncLog)
        .filter(
            DataSyncLog.data_source_id == data_source_id,
            DataSyncLog.status.in_(["pending", "queued", "started", "in_progress"]),
        )
        .first()
    )


def create_error_response(
    code: str,
    message: str,
    details: Optional[list] = None,
) -> dict:
    """Create a standardized error response dict."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/data-sources",
    response_model=DataSourceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List data sources",
    description="List all configured data sources with their sync status and statistics.",
)
def list_data_sources(
    is_active: Optional[bool] = Query(
        None, description="Filter by active status"
    ),
    source_type: Optional[SourceTypeEnum] = Query(
        None, description="Filter by source type"
    ),
    db: Session = Depends(get_db),
) -> DataSourceListResponse:
    """
    List all configured data sources with their sync status and statistics.

    Query Parameters:
    - is_active: Filter by active status (true/false)
    - source_type: Filter by source type (api, file, database, manual)

    Returns:
    - data_sources: List of data sources with details
    - total: Total count
    - summary: Overall summary statistics
    """
    # Build query
    query = db.query(DataSource)

    # Apply filters
    if is_active is not None:
        query = query.filter(DataSource.is_active == is_active)

    if source_type is not None:
        query = query.filter(DataSource.source_type == source_type.value)

    # Execute query
    data_sources = query.all()

    # Build response items
    items = []
    total_emission_factors = 0
    sources_with_recent_sync = 0
    sources_needing_sync = 0
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for ds in data_sources:
        # Get statistics
        stats = get_data_source_statistics(db, ds.id)
        total_emission_factors += stats.total_factors

        # Get last sync info
        last_sync = get_last_sync_info(db, ds.id)

        # Check if synced recently
        if last_sync and last_sync.started_at:
            started_at = last_sync.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            if started_at >= seven_days_ago:
                sources_with_recent_sync += 1

        # Calculate next scheduled sync
        next_sync = calculate_next_scheduled_sync(ds)

        # Check if sync is needed
        if next_sync:
            if next_sync.tzinfo is None:
                next_sync = next_sync.replace(tzinfo=timezone.utc)
            if next_sync <= datetime.now(timezone.utc):
                sources_needing_sync += 1

        items.append(
            DataSourceListItem(
                id=ds.id,
                name=ds.name,
                source_type=ds.source_type,
                base_url=ds.base_url,
                sync_frequency=ds.sync_frequency,
                is_active=ds.is_active,
                last_sync=last_sync,
                next_scheduled_sync=next_sync,
                statistics=stats,
                created_at=ds.created_at or datetime.now(timezone.utc),
            )
        )

    # Calculate summary
    active_sources = sum(1 for ds in data_sources if ds.is_active)

    summary = DataSourceSummary(
        total_sources=len(data_sources),
        active_sources=active_sources,
        total_emission_factors=total_emission_factors,
        sources_with_recent_sync=sources_with_recent_sync,
        sources_needing_sync=sources_needing_sync,
    )

    return DataSourceListResponse(
        data_sources=items,
        total=len(data_sources),
        summary=summary,
    )


@router.get(
    "/data-sources/{data_source_id}",
    response_model=DataSourceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get data source details",
    description="Get detailed information for a specific data source.",
    responses={
        404: {"description": "Data source not found"},
    },
)
def get_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
) -> DataSourceDetailResponse:
    """
    Get detailed information for a specific data source.

    Path Parameters:
    - data_source_id: Unique data source identifier

    Returns:
    - Data source details with sync status and statistics

    Raises:
    - 404: Data source not found
    """
    # Query data source
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id)
        .first()
    )

    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message="Data source not found",
                details=[
                    {"field": "id", "message": f"No data source exists with ID {data_source_id}"}
                ],
            ),
        )

    # Get statistics and last sync
    stats = get_data_source_statistics(db, data_source.id)
    last_sync = get_last_sync_info(db, data_source.id)
    next_sync = calculate_next_scheduled_sync(data_source)

    return DataSourceDetailResponse(
        id=data_source.id,
        name=data_source.name,
        source_type=data_source.source_type,
        base_url=data_source.base_url,
        sync_frequency=data_source.sync_frequency,
        is_active=data_source.is_active,
        last_sync=last_sync,
        next_scheduled_sync=next_sync,
        statistics=stats,
        created_at=data_source.created_at or datetime.now(timezone.utc),
    )


@router.post(
    "/data-sources/{data_source_id}/sync",
    response_model=SyncTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger data source sync",
    description="Manually trigger a data sync for a specific data source.",
    responses={
        404: {"description": "Data source not found"},
        409: {"description": "Sync already in progress"},
        422: {"description": "Data source is inactive or no connector available"},
        503: {"description": "Task queue unavailable"},
    },
)
def trigger_sync(
    data_source_id: str,
    request: Optional[SyncTriggerRequest] = None,
    db: Session = Depends(get_db),
) -> SyncTriggerResponse:
    """
    Manually trigger a data sync for a specific data source.

    Creates a background task and returns immediately with task_id.
    Use GET /admin/sync-logs to monitor sync progress.

    Path Parameters:
    - data_source_id: Unique data source identifier

    Request Body (optional):
    - force_refresh: Force full refresh (default: false)
    - dry_run: Validate without persisting (default: false)
    - priority: Task priority (high/normal/low, default: normal)

    Returns:
    - 202: Sync task accepted and queued
    - task_id: Task ID for tracking
    - sync_log_id: ID of created sync log entry
    - poll_url: URL to check sync status

    Raises:
    - 404: Data source not found
    - 409: Sync already in progress
    - 422: Data source is inactive or no connector registered
    """
    # Set defaults if no request body
    if request is None:
        request = SyncTriggerRequest()

    # Query data source
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id)
        .first()
    )

    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message="Data source not found",
                details=[
                    {"field": "id", "message": f"No data source exists with ID {data_source_id}"}
                ],
            ),
        )

    # Check if data source is active
    if not data_source.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=create_error_response(
                code="SOURCE_INACTIVE",
                message="Cannot sync inactive data source",
                details=[
                    {"field": "id", "message": "Data source is disabled. Enable it first."}
                ],
            ),
        )

    # Check if connector is available for this data source
    if not is_connector_available(data_source.name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=create_error_response(
                code="NO_CONNECTOR",
                message=f"No connector registered for data source: '{data_source.name}'",
                details=[
                    {
                        "field": "name",
                        "message": f"No connector is available to sync '{data_source.name}'. "
                                   "Only EPA, DEFRA, and Exiobase sources are supported."
                    }
                ],
            ),
        )

    # Check for existing sync in progress
    active_sync = check_active_sync(db, data_source_id)
    if active_sync:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=create_error_response(
                code="SYNC_IN_PROGRESS",
                message="A sync is already in progress for this data source",
                details=[
                    {"field": "data_source_id", "message": f"Active sync: {active_sync.id}"}
                ],
            ),
        )

    # Create sync log entry first
    sync_log = DataSyncLog(
        id=uuid.uuid4().hex,
        data_source_id=data_source_id,
        sync_type="manual",
        status="queued",
        celery_task_id=None,  # Will be updated by trigger
        started_at=datetime.now(timezone.utc),
        records_processed=0,
        records_created=0,
        records_updated=0,
        records_skipped=0,
        records_failed=0,
        sync_metadata={
            "force_refresh": request.force_refresh,
            "dry_run": request.dry_run,
            "priority": request.priority.value,
        },
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    # Trigger the sync task with real connector
    trigger = get_sync_task_trigger()
    task_id = trigger(
        data_source_id=data_source_id,
        data_source_name=data_source.name,
        sync_log_id=sync_log.id,
        force_refresh=request.force_refresh,
        dry_run=request.dry_run,
        priority=request.priority.value,
    )

    # Update sync log with task ID
    sync_log.celery_task_id = task_id
    db.commit()

    # Build message
    message = "Sync task queued successfully"
    if request.dry_run:
        message = "Dry run sync task queued successfully (no changes will be persisted)"

    return SyncTriggerResponse(
        task_id=task_id,
        sync_log_id=sync_log.id,
        status="queued",
        message=message,
        data_source=SyncTriggerDataSource(
            id=data_source.id,
            name=data_source.name,
        ),
        estimated_duration="5 minutes",
        poll_url=f"/admin/sync-logs/{sync_log.id}",
    )
