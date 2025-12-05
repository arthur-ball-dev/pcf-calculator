"""
Admin API Pydantic schemas.

TASK-API-P5-001: Admin Data Sources Endpoints

Pydantic models for admin API request/response validation:
- Data sources list and detail endpoints
- Sync trigger requests and responses
- Sync logs with filtering and pagination
- Coverage statistics
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Enum Definitions (matching contracts)
# ============================================================================


class SourceTypeEnum(str, Enum):
    """Valid data source types."""
    api = "api"
    file = "file"
    database = "database"
    manual = "manual"


class SyncFrequencyEnum(str, Enum):
    """Valid sync frequency values."""
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    manual = "manual"


class SyncStatusEnum(str, Enum):
    """Valid sync status values."""
    pending = "pending"
    queued = "queued"
    started = "started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class SyncTypeEnum(str, Enum):
    """Valid sync type values."""
    scheduled = "scheduled"
    manual = "manual"
    initial = "initial"


class PriorityEnum(str, Enum):
    """Valid priority values."""
    high = "high"
    normal = "normal"
    low = "low"


class GroupByEnum(str, Enum):
    """Valid group_by values for coverage."""
    source = "source"
    geography = "geography"
    category = "category"
    year = "year"


class GapStatusEnum(str, Enum):
    """Coverage gap status."""
    full = "full"
    partial = "partial"
    none = "none"


class SortOrderEnum(str, Enum):
    """Sort order for pagination."""
    asc = "asc"
    desc = "desc"


class SyncLogSortByEnum(str, Enum):
    """Valid sort_by values for sync logs."""
    started_at = "started_at"
    completed_at = "completed_at"
    records_processed = "records_processed"
    records_failed = "records_failed"


# ============================================================================
# Data Source Schemas
# ============================================================================


class LastSyncInfo(BaseModel):
    """Most recent sync information for a data source."""
    model_config = ConfigDict(from_attributes=True)

    sync_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    error_message: Optional[str] = None


class DataSourceStatistics(BaseModel):
    """Aggregated statistics for a data source."""
    total_factors: int
    active_factors: int
    average_quality: Optional[float] = None
    geographies_covered: int
    oldest_reference_year: Optional[int] = None
    newest_reference_year: Optional[int] = None


class DataSourceListItem(BaseModel):
    """Data source item in list response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str
    base_url: Optional[str] = None
    sync_frequency: str
    is_active: bool
    last_sync: Optional[LastSyncInfo] = None
    next_scheduled_sync: Optional[datetime] = None
    statistics: DataSourceStatistics
    created_at: datetime


class DataSourceSummary(BaseModel):
    """Summary statistics for all data sources."""
    total_sources: int
    active_sources: int
    total_emission_factors: int
    sources_with_recent_sync: int
    sources_needing_sync: int


class DataSourceListResponse(BaseModel):
    """Response for GET /admin/data-sources."""
    data_sources: List[DataSourceListItem]
    total: int
    summary: DataSourceSummary


class DataSourceDetailResponse(BaseModel):
    """Response for GET /admin/data-sources/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str
    base_url: Optional[str] = None
    sync_frequency: str
    is_active: bool
    last_sync: Optional[LastSyncInfo] = None
    next_scheduled_sync: Optional[datetime] = None
    statistics: DataSourceStatistics
    created_at: datetime


# ============================================================================
# Sync Trigger Schemas
# ============================================================================


class SyncTriggerRequest(BaseModel):
    """Request body for POST /admin/data-sources/{id}/sync."""
    force_refresh: bool = Field(default=False, description="Force full refresh")
    dry_run: bool = Field(default=False, description="Validate without persisting")
    priority: PriorityEnum = Field(default=PriorityEnum.normal, description="Task priority")


class SyncTriggerDataSource(BaseModel):
    """Data source info in sync trigger response."""
    id: str
    name: str


class SyncTriggerResponse(BaseModel):
    """Response for POST /admin/data-sources/{id}/sync (202 Accepted)."""
    task_id: str
    sync_log_id: str
    status: str
    message: str
    data_source: SyncTriggerDataSource
    estimated_duration: Optional[str] = None
    poll_url: str


# ============================================================================
# Sync Logs Schemas
# ============================================================================


class SyncLogDataSource(BaseModel):
    """Embedded data source info in sync log."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class ErrorDetail(BaseModel):
    """Individual error detail in sync log."""
    record_id: Optional[str] = None
    field: Optional[str] = None
    message: str


class SyncLogMetadata(BaseModel):
    """Sync operation metadata."""
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    api_calls_made: Optional[int] = None
    triggered_by: Optional[str] = None


class SyncLogItem(BaseModel):
    """Sync log item in list response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    data_source: SyncLogDataSource
    sync_type: str
    status: str
    celery_task_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    error_message: Optional[str] = None
    error_details: Optional[List[ErrorDetail]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class SyncLogsSummary(BaseModel):
    """Summary statistics for sync logs."""
    total_syncs: int
    completed_syncs: int
    failed_syncs: int
    total_records_processed: int
    total_records_failed: int
    average_duration_seconds: Optional[float] = None


class SyncLogsListResponse(BaseModel):
    """Response for GET /admin/sync-logs."""
    items: List[SyncLogItem]
    total: int
    limit: int
    offset: int
    has_more: bool
    summary: SyncLogsSummary


class SyncLogDetailResponse(BaseModel):
    """Response for GET /admin/sync-logs/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    data_source: SyncLogDataSource
    sync_type: str
    status: str
    celery_task_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    error_message: Optional[str] = None
    error_details: Optional[List[ErrorDetail]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


# ============================================================================
# Coverage Schemas
# ============================================================================


class CoverageSummary(BaseModel):
    """Overall coverage summary."""
    total_emission_factors: int
    active_emission_factors: int
    unique_activities: int
    geographies_covered: int
    categories_with_factors: int
    categories_without_factors: int
    average_quality_rating: Optional[float] = None
    coverage_percentage: Optional[float] = None


class YearRange(BaseModel):
    """Reference year range."""
    min: Optional[int] = None
    max: Optional[int] = None


class CoverageBySource(BaseModel):
    """Coverage breakdown by data source."""
    source_id: Optional[str] = None
    source_name: str
    total_factors: int
    active_factors: int
    percentage_of_total: float
    geographies: List[str]
    average_quality: Optional[float] = None
    year_range: YearRange


class CoverageByGeography(BaseModel):
    """Coverage breakdown by geography."""
    geography: str
    geography_name: str
    total_factors: int
    sources: List[str]
    percentage_of_total: float


class CoverageByCategory(BaseModel):
    """Coverage breakdown by product category."""
    category_id: str
    category_name: str
    category_code: str
    products_count: int
    products_with_factors: int
    coverage_percentage: float
    factors_available: int
    gap_status: str


class MissingGeography(BaseModel):
    """Geography with products but no factors."""
    geography: str
    products_affected: int


class MissingCategory(BaseModel):
    """Category with no emission factors."""
    category_id: str
    category_name: str
    products_count: int


class OutdatedFactors(BaseModel):
    """Factors with outdated reference year."""
    source_name: str
    count: int
    oldest_year: int


class CoverageGaps(BaseModel):
    """Identified coverage gaps."""
    missing_geographies: List[MissingGeography]
    missing_categories: List[MissingCategory]
    outdated_factors: List[OutdatedFactors]


class CoverageResponse(BaseModel):
    """Response for GET /admin/emission-factors/coverage."""
    summary: CoverageSummary
    by_source: List[CoverageBySource]
    by_geography: List[CoverageByGeography]
    by_category: List[CoverageByCategory]
    gaps: CoverageGaps


# ============================================================================
# Error Response Schemas
# ============================================================================


class ErrorDetailItem(BaseModel):
    """Individual error detail."""
    field: Optional[str] = None
    message: str


class ErrorBody(BaseModel):
    """Standard error body."""
    code: str
    message: str
    details: Optional[List[ErrorDetailItem]] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorBody
    request_id: str
    timestamp: datetime
