"""
Data synchronization Celery tasks for PCF Calculator.

TASK-BE-P5-001: Celery + Redis Setup

This module contains Celery tasks for synchronizing emission factor data
from external sources (EPA, DEFRA, Exiobase).

Tasks:
- sync_data_source: Sync emission factors from a data source
- check_sync_status: Check status of a sync operation

Usage:
    from backend.tasks.data_sync import sync_data_source, check_sync_status

    # Trigger async sync
    result = sync_data_source.delay("EPA_GHG_HUB")
    print(f"Task ID: {result.id}")

    # With options
    result = sync_data_source.apply_async(
        args=["EPA_GHG_HUB"],
        kwargs={"force_refresh": True},
        queue="data_sync"
    )

    # Check sync status
    status = check_sync_status.delay("sync-log-uuid")
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from sqlalchemy import select

from backend.core.celery_app import celery_app
from backend.database.connection import SessionLocal
from backend.models import DataSource, DataSyncLog
from backend.services.data_ingestion import (
    EPAEmissionFactorsIngestion,
    DEFRAEmissionFactorsIngestion,
)


# Mapping of data source names to ingestion classes
# ExiobaseEmissionFactorsIngestion will be added when implemented
INGESTION_CLASSES: Dict[str, type] = {
    "EPA_GHG_HUB": EPAEmissionFactorsIngestion,
    "DEFRA_CONVERSION": DEFRAEmissionFactorsIngestion,
    # "EXIOBASE": ExiobaseEmissionFactorsIngestion,  # TODO: Implement in TASK-DATA-P5-004
}


@asynccontextmanager
async def async_session_maker():
    """Create an async session context manager for Celery tasks.

    This async context manager wraps SessionLocal() to provide a consistent
    interface that can be easily mocked in tests using:
        with patch("backend.tasks.data_sync.async_session_maker") as mock:
            mock.return_value.__aenter__.return_value = mock_session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="backend.tasks.data_sync.sync_data_source",
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 3},
    acks_late=True,
)
def sync_data_source(
    self,
    source_name: str,
    force_refresh: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sync emission factors from a data source.

    This task fetches, parses, transforms, and loads emission factor data
    from external sources (EPA, DEFRA, Exiobase).

    Args:
        self: Celery task instance (bound task)
        source_name: Name of the data source (e.g., "EPA_GHG_HUB")
        force_refresh: If True, ignore incremental sync logic
        dry_run: If True, validate without persisting

    Returns:
        dict: Sync statistics including:
            - sync_log_id: UUID of the sync log entry
            - status: "completed" or "failed"
            - records_processed: Total records processed
            - records_created: New records created
            - records_updated: Existing records updated
            - records_skipped: Records skipped (unchanged)
            - records_failed: Records that failed validation

    Raises:
        ValueError: If data source not found, inactive, or no ingestion class
        ConnectionError: If external API is unavailable (will trigger retry)
        TimeoutError: If sync times out (will trigger retry)
    """
    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _async_sync_data_source(self, source_name, force_refresh, dry_run)
        )
    finally:
        loop.close()


async def _async_sync_data_source(
    task_instance,
    source_name: str,
    force_refresh: bool,
    dry_run: bool
) -> Dict[str, Any]:
    """
    Async implementation of sync_data_source.

    Args:
        task_instance: Celery task instance for state updates
        source_name: Name of the data source
        force_refresh: Force full refresh
        dry_run: Validate without persisting

    Returns:
        dict: Sync statistics
    """
    async with async_session_maker() as db:
        # Get data source - await for async mock compatibility
        result = await db.execute(
            select(DataSource).where(DataSource.name == source_name)
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            raise ValueError(f"Data source not found: {source_name}")

        if not data_source.is_active:
            raise ValueError(f"Data source is inactive: {source_name}")

        # Get ingestion class
        ingestion_class = INGESTION_CLASSES.get(source_name)
        if not ingestion_class:
            raise ValueError(f"No ingestion class for: {source_name}")

        # Determine sync type
        sync_type = "manual" if task_instance.request.id else "scheduled"

        # Create ingestion instance
        ingestion = ingestion_class(
            db=db,
            data_source_id=data_source.id,
            sync_type=sync_type
        )

        # Update task state to SYNCING
        task_instance.update_state(
            state="SYNCING",
            meta={"source": source_name, "started": True}
        )

        # Execute sync
        sync_result = await ingestion.execute_sync()

        # Commit transaction
        db.commit()

        return sync_result.dict()


@celery_app.task(
    bind=True,
    name="backend.tasks.data_sync.check_sync_status",
)
def check_sync_status(self, sync_log_id: str) -> Dict[str, Any]:
    """
    Check status of a sync operation.

    Args:
        self: Celery task instance (bound task)
        sync_log_id: UUID of the sync log entry

    Returns:
        dict: Sync status information including:
            - status: "pending", "in_progress", "completed", "failed", or "not_found"
            - records_processed: Total records processed
            - records_created: New records created
            - records_failed: Records that failed
            - error_message: Error message if failed
    """
    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_async_check_sync_status(sync_log_id))
    finally:
        loop.close()


async def _async_check_sync_status(sync_log_id: str) -> Dict[str, Any]:
    """
    Async implementation of check_sync_status.

    Args:
        sync_log_id: UUID of the sync log entry

    Returns:
        dict: Sync status information
    """
    from uuid import UUID

    async with async_session_maker() as db:
        # Parse UUID (handle both hex and hyphenated formats)
        try:
            log_uuid = UUID(sync_log_id)
            log_id = log_uuid.hex
        except ValueError:
            log_id = sync_log_id

        result = await db.execute(
            select(DataSyncLog).where(DataSyncLog.id == log_id)
        )
        sync_log = result.scalar_one_or_none()

        if not sync_log:
            return {"status": "not_found"}

        return {
            "status": sync_log.status,
            "records_processed": sync_log.records_processed,
            "records_created": sync_log.records_created,
            "records_failed": sync_log.records_failed,
            "error_message": sync_log.error_message,
        }
