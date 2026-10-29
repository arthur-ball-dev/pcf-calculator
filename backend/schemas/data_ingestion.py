"""
Pydantic schemas for data ingestion operations.

TASK-DATA-P5-001: Base Ingestion Framework

This module provides validation schemas for:
- ValidationError: Records validation errors during ingestion
- SyncResult: Result of a sync operation with statistics
- SyncRequest: Request parameters for initiating a sync

Usage:
    from backend.schemas.data_ingestion import (
        ValidationError, SyncResult, SyncRequest
    )

    result = SyncResult(
        sync_log_id="abc123",
        status="completed",
        records_processed=100,
        records_created=95,
        records_updated=0,
        records_skipped=0,
        records_failed=5
    )
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ValidationError(BaseModel):
    """
    Represents a validation error for a single record.

    Attributes:
        record_id: External ID of the record that failed validation (if available)
        field: Name of the field that failed validation (if known)
        message: Human-readable description of the validation error

    Example:
        error = ValidationError(
            record_id="EPA-001",
            field="co2e_factor",
            message="CO2e factor must be positive"
        )
    """
    record_id: Optional[str] = Field(
        default=None,
        description="External ID of the record that failed validation"
    )
    field: Optional[str] = Field(
        default=None,
        description="Name of the field that failed validation"
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable validation error message"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "record_id": "EPA-001",
                "field": "co2e_factor",
                "message": "CO2e factor must be positive"
            }
        }
    )


class SyncResult(BaseModel):
    """
    Result of a data synchronization operation.

    Contains statistics about the sync operation and overall status.

    Attributes:
        sync_log_id: UUID of the sync log entry
        status: Final status (completed, failed)
        records_processed: Total records processed
        records_created: New records created
        records_updated: Existing records updated
        records_skipped: Records skipped (unchanged)
        records_failed: Records that failed validation
        errors: List of validation errors (up to 100)
        started_at: When sync started
        completed_at: When sync completed

    Example:
        result = SyncResult(
            sync_log_id="abc123def456",
            status="completed",
            records_processed=100,
            records_created=95,
            records_updated=5,
            records_skipped=0,
            records_failed=0
        )
    """
    sync_log_id: str = Field(
        ...,
        description="UUID of the sync log entry"
    )
    status: str = Field(
        ...,
        description="Final status: completed, failed, or cancelled"
    )
    records_processed: int = Field(
        default=0,
        ge=0,
        description="Total number of records processed"
    )
    records_created: int = Field(
        default=0,
        ge=0,
        description="Number of new records created"
    )
    records_updated: int = Field(
        default=0,
        ge=0,
        description="Number of existing records updated"
    )
    records_skipped: int = Field(
        default=0,
        ge=0,
        description="Number of records skipped (unchanged)"
    )
    records_failed: int = Field(
        default=0,
        ge=0,
        description="Number of records that failed validation"
    )
    errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of validation errors (limited to 100)"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when sync started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when sync completed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sync_log_id": "abc123def456ghi789",
                "status": "completed",
                "records_processed": 100,
                "records_created": 95,
                "records_updated": 3,
                "records_skipped": 0,
                "records_failed": 2,
                "errors": [
                    {
                        "record_id": "EPA-099",
                        "field": "co2e_factor",
                        "message": "CO2e factor must be positive"
                    }
                ]
            }
        }
    )


class SyncRequest(BaseModel):
    """
    Request parameters for initiating a data sync.

    Attributes:
        force_refresh: If True, fetch all data even if unchanged
        dry_run: If True, validate without committing changes
        priority: Priority level for background processing

    Example:
        request = SyncRequest(
            force_refresh=True,
            dry_run=False,
            priority="high"
        )
    """
    force_refresh: bool = Field(
        default=False,
        description="Force full refresh even if data unchanged"
    )
    dry_run: bool = Field(
        default=False,
        description="Validate data without committing to database"
    )
    priority: str = Field(
        default="normal",
        description="Processing priority: low, normal, high"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "force_refresh": False,
                "dry_run": False,
                "priority": "normal"
            }
        }
    )


__all__ = [
    "ValidationError",
    "SyncResult",
    "SyncRequest",
]
