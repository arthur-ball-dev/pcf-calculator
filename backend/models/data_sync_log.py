"""
DataSyncLog model - Audit trail for data synchronization operations

TASK-DB-P5-002: Extended Database Schema

Tracks every data sync operation for debugging, compliance, and monitoring.

Attributes:
    id: UUID primary key
    data_source_id: FK to data_sources table
    sync_type: Type of sync (scheduled, manual, initial)
    status: Status (pending, in_progress, completed, failed, cancelled)
    celery_task_id: Associated Celery task ID
    records_processed: Total records processed
    records_created: New records created
    records_updated: Existing records updated
    records_skipped: Records skipped
    records_failed: Records that failed
    error_message: Error message if failed
    error_details: Structured error details (JSONB)
    metadata: Additional sync metadata (JSONB)
    started_at: When sync started
    completed_at: When sync completed
    created_at: Log creation timestamp

Relationships:
    data_source: The DataSource being synced
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models import Base, generate_uuid


class DataSyncLog(Base):
    """
    DataSyncLog model - Audit trail for data synchronization operations.

    Tracks status, progress, and errors for each sync operation.
    """
    __tablename__ = "data_sync_logs"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Foreign key to data_sources
    data_source_id = Column(
        String(32),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False
    )

    # Type of sync: scheduled, manual, initial
    sync_type = Column(String(20), nullable=False)

    # Status: pending, in_progress, completed, failed, cancelled
    status = Column(String(20), nullable=False)

    # Associated Celery task ID for async operations
    celery_task_id = Column(String(255), nullable=True)

    # Record counters
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # JSONB in PostgreSQL

    # Additional metadata
    sync_metadata = Column('metadata', JSON, nullable=True)  # JSONB in PostgreSQL

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to data source
    data_source = relationship(
        "DataSource",
        back_populates="sync_logs",
        foreign_keys=[data_source_id]
    )

    # Provide instance-level access for metadata
    def __getattribute__(self, name):
        if name == 'metadata':
            return object.__getattribute__(self, 'sync_metadata')
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'metadata':
            object.__setattr__(self, 'sync_metadata', value)
        else:
            object.__setattr__(self, name, value)

    # Table indexes
    __table_args__ = (
        Index('idx_sync_log_source', 'data_source_id'),
        Index('idx_sync_log_status', 'status'),
        Index('idx_sync_log_started', 'started_at'),
        Index('idx_sync_log_celery_task', 'celery_task_id'),
    )

    def __repr__(self) -> str:
        return f"<DataSyncLog(source_id='{self.data_source_id}', status='{self.status}')>"
