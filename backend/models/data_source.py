"""
DataSource model - Tracks emission factor data sources

TASK-DB-P5-002: Extended Database Schema

Represents external data sources for emission factors such as
EPA GHG Emission Factors Hub, DEFRA Conversion Factors, and Exiobase.

Attributes:
    id: UUID primary key
    name: Unique name of the data source
    source_type: Type of source (api, file, database, manual)
    base_url: URL for API or file download location
    api_key_env_var: Environment variable name for API key
    sync_frequency: How often to sync (daily, weekly, biweekly, monthly, manual)
    last_sync_at: Timestamp of last successful sync
    is_active: Whether this source is active
    created_at: Creation timestamp
    updated_at: Last update timestamp

Relationships:
    emission_factors: EmissionFactor objects from this source
    sync_logs: DataSyncLog records for this source
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models import Base, generate_uuid


class DataSource(Base):
    """
    DataSource model - Tracks external data sources for emission factors.

    Represents sources like EPA, DEFRA, Exiobase where emission
    factor data is sourced from.
    """
    __tablename__ = "data_sources"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Unique name of the data source
    name = Column(String(100), nullable=False, unique=True)

    # Type of source: api, file, database, manual
    source_type = Column(String(50), nullable=False)

    # Base URL for API or file download
    base_url = Column(Text, nullable=True)

    # Environment variable name for API key (e.g., "EPA_API_KEY")
    api_key_env_var = Column(String(100), nullable=True)

    # Sync frequency: daily, weekly, biweekly, monthly, manual
    sync_frequency = Column(String(20), default='biweekly')

    # Timestamp of last successful sync
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Whether this source is active
    is_active = Column(Boolean, default=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    emission_factors = relationship(
        "EmissionFactor",
        back_populates="data_source_ref",
        foreign_keys="[EmissionFactor.data_source_id]"
    )

    sync_logs = relationship(
        "DataSyncLog",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DataSource(name='{self.name}', type='{self.source_type}')>"
