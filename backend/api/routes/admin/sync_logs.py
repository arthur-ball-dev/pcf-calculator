"""
Admin Sync Logs API Routes.

TASK-API-P5-001: Admin Data Sources Endpoints

Endpoints:
- GET /admin/sync-logs - Get sync history with filters
- GET /admin/sync-logs/{id} - Get single sync log details

Contract Reference: phase5-contracts/admin-sync-logs-contract.yaml
"""

import uuid
from datetime import datetime, date, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models import DataSource, DataSyncLog
from backend.schemas.admin import (
    SyncStatusEnum,
    SyncTypeEnum,
    SyncLogSortByEnum,
    SortOrderEnum,
    SyncLogsListResponse,
    SyncLogItem,
    SyncLogDetailResponse,
    SyncLogsSummary,
    SyncLogDataSource,
    ErrorDetail,
)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(tags=["admin-sync-logs"])


# ============================================================================
# Helper Functions
# ============================================================================


def create_error_response(code: str, message: str, details: Optional[list] = None) -> dict:
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


def sync_log_to_item(log: DataSyncLog) -> SyncLogItem:
    """Convert a DataSyncLog model to SyncLogItem response."""
    # Calculate duration
    duration_seconds = None
    if log.completed_at and log.started_at:
        duration_seconds = (log.completed_at - log.started_at).total_seconds()

    # Parse error_details if present
    error_details = None
    if log.error_details:
        error_details = [
            ErrorDetail(
                record_id=e.get("record_id"),
                field=e.get("field"),
                message=e.get("message", "Unknown error"),
            )
            for e in log.error_details
        ]

    return SyncLogItem(
        id=log.id,
        data_source=SyncLogDataSource(
            id=log.data_source.id,
            name=log.data_source.name,
        ),
        sync_type=log.sync_type,
        status=log.status,
        celery_task_id=log.celery_task_id,
        started_at=log.started_at,
        completed_at=log.completed_at,
        duration_seconds=duration_seconds,
        records_processed=log.records_processed or 0,
        records_created=log.records_created or 0,
        records_updated=log.records_updated or 0,
        records_skipped=log.records_skipped or 0,
        records_failed=log.records_failed or 0,
        error_message=log.error_message,
        error_details=error_details,
        metadata=log.sync_metadata,
        created_at=log.created_at or log.started_at,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/sync-logs",
    response_model=SyncLogsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List sync logs",
    description="Retrieve sync operation history with filtering and pagination.",
)
def list_sync_logs(
    data_source_id: Optional[str] = Query(
        None, description="Filter by specific data source"
    ),
    status_filter: Optional[SyncStatusEnum] = Query(
        None, alias="status", description="Filter by sync status"
    ),
    sync_type: Optional[SyncTypeEnum] = Query(
        None, description="Filter by sync type"
    ),
    start_date: Optional[date] = Query(
        None, description="Filter syncs started on or after this date (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None, description="Filter syncs started on or before this date (YYYY-MM-DD)"
    ),
    has_errors: Optional[bool] = Query(
        None, description="Filter to only syncs with errors (records_failed > 0)"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of results to skip"
    ),
    sort_by: SyncLogSortByEnum = Query(
        SyncLogSortByEnum.started_at, description="Sort field"
    ),
    sort_order: SortOrderEnum = Query(
        SortOrderEnum.desc, description="Sort direction"
    ),
    db: Session = Depends(get_db),
) -> SyncLogsListResponse:
    """
    Retrieve sync operation history with filtering and pagination.

    Query Parameters:
    - data_source_id: Filter by specific data source
    - status: Filter by sync status (pending, in_progress, completed, failed, cancelled)
    - sync_type: Filter by sync type (scheduled, manual, initial)
    - start_date: Filter syncs started on or after this date
    - end_date: Filter syncs started on or before this date
    - has_errors: Filter to only syncs with errors (records_failed > 0)
    - limit: Number of results to return (1-100, default: 50)
    - offset: Number of results to skip (default: 0)
    - sort_by: Sort field (started_at, completed_at, records_processed, records_failed)
    - sort_order: Sort direction (asc, desc)

    Returns:
    - items: List of sync log entries
    - total: Total matching sync logs
    - limit/offset: Applied pagination
    - has_more: Whether more results exist
    - summary: Summary of filtered results
    """
    # Validate data_source_id if provided
    if data_source_id:
        data_source = (
            db.query(DataSource)
            .filter(DataSource.id == data_source_id)
            .first()
        )
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=create_error_response(
                    code="INVALID_DATA_SOURCE",
                    message="Data source not found",
                    details=[
                        {"field": "data_source_id", "message": f"No data source exists with ID {data_source_id}"}
                    ],
                ),
            )

    # Build base query
    query = db.query(DataSyncLog)

    # Apply filters
    if data_source_id:
        query = query.filter(DataSyncLog.data_source_id == data_source_id)

    if status_filter:
        query = query.filter(DataSyncLog.status == status_filter.value)

    if sync_type:
        query = query.filter(DataSyncLog.sync_type == sync_type.value)

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(DataSyncLog.started_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(DataSyncLog.started_at <= end_datetime)

    if has_errors is True:
        query = query.filter(DataSyncLog.records_failed > 0)
    elif has_errors is False:
        query = query.filter(DataSyncLog.records_failed == 0)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(DataSyncLog, sort_by.value)
    if sort_order == SortOrderEnum.desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    logs = query.offset(offset).limit(limit).all()

    # Convert to response items
    items = [sync_log_to_item(log) for log in logs]

    # Calculate summary
    # Use the same filtered query for summary stats
    summary_query = db.query(DataSyncLog)
    if data_source_id:
        summary_query = summary_query.filter(DataSyncLog.data_source_id == data_source_id)
    if status_filter:
        summary_query = summary_query.filter(DataSyncLog.status == status_filter.value)
    if sync_type:
        summary_query = summary_query.filter(DataSyncLog.sync_type == sync_type.value)
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        summary_query = summary_query.filter(DataSyncLog.started_at >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        summary_query = summary_query.filter(DataSyncLog.started_at <= end_datetime)
    if has_errors is True:
        summary_query = summary_query.filter(DataSyncLog.records_failed > 0)
    elif has_errors is False:
        summary_query = summary_query.filter(DataSyncLog.records_failed == 0)

    total_syncs = summary_query.count()

    completed_syncs = summary_query.filter(DataSyncLog.status == "completed").count()

    failed_syncs = summary_query.filter(DataSyncLog.status == "failed").count()

    total_records_processed = (
        db.query(func.sum(DataSyncLog.records_processed))
        .filter(
            *([DataSyncLog.data_source_id == data_source_id] if data_source_id else []),
            *([DataSyncLog.status == status_filter.value] if status_filter else []),
            *([DataSyncLog.sync_type == sync_type.value] if sync_type else []),
        )
        .scalar() or 0
    )

    total_records_failed = (
        db.query(func.sum(DataSyncLog.records_failed))
        .filter(
            *([DataSyncLog.data_source_id == data_source_id] if data_source_id else []),
            *([DataSyncLog.status == status_filter.value] if status_filter else []),
            *([DataSyncLog.sync_type == sync_type.value] if sync_type else []),
        )
        .scalar() or 0
    )

    # Calculate average duration for completed syncs
    completed_logs = (
        summary_query
        .filter(
            DataSyncLog.status == "completed",
            DataSyncLog.completed_at.isnot(None),
        )
        .all()
    )

    average_duration = None
    if completed_logs:
        durations = [
            (log.completed_at - log.started_at).total_seconds()
            for log in completed_logs
            if log.completed_at and log.started_at
        ]
        if durations:
            average_duration = sum(durations) / len(durations)

    summary = SyncLogsSummary(
        total_syncs=total_syncs,
        completed_syncs=completed_syncs,
        failed_syncs=failed_syncs,
        total_records_processed=total_records_processed,
        total_records_failed=total_records_failed,
        average_duration_seconds=average_duration,
    )

    return SyncLogsListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=total > offset + limit,
        summary=summary,
    )


@router.get(
    "/sync-logs/{sync_log_id}",
    response_model=SyncLogDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sync log details",
    description="Get detailed information for a specific sync log entry.",
    responses={
        404: {"description": "Sync log not found"},
    },
)
def get_sync_log(
    sync_log_id: str,
    db: Session = Depends(get_db),
) -> SyncLogDetailResponse:
    """
    Get detailed information for a specific sync log entry.

    Path Parameters:
    - sync_log_id: Unique sync log identifier

    Returns:
    - Sync log details with full error information

    Raises:
    - 404: Sync log not found
    """
    # Query sync log
    log = (
        db.query(DataSyncLog)
        .filter(DataSyncLog.id == sync_log_id)
        .first()
    )

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                code="NOT_FOUND",
                message="Sync log not found",
                details=[
                    {"field": "id", "message": f"No sync log exists with ID {sync_log_id}"}
                ],
            ),
        )

    # Calculate duration
    duration_seconds = None
    if log.completed_at and log.started_at:
        duration_seconds = (log.completed_at - log.started_at).total_seconds()

    # Parse error_details if present
    error_details = None
    if log.error_details:
        error_details = [
            ErrorDetail(
                record_id=e.get("record_id"),
                field=e.get("field"),
                message=e.get("message", "Unknown error"),
            )
            for e in log.error_details
        ]

    return SyncLogDetailResponse(
        id=log.id,
        data_source=SyncLogDataSource(
            id=log.data_source.id,
            name=log.data_source.name,
        ),
        sync_type=log.sync_type,
        status=log.status,
        celery_task_id=log.celery_task_id,
        started_at=log.started_at,
        completed_at=log.completed_at,
        duration_seconds=duration_seconds,
        records_processed=log.records_processed or 0,
        records_created=log.records_created or 0,
        records_updated=log.records_updated or 0,
        records_skipped=log.records_skipped or 0,
        records_failed=log.records_failed or 0,
        error_message=log.error_message,
        error_details=error_details,
        metadata=log.sync_metadata,
        created_at=log.created_at or log.started_at,
    )
