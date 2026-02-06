"""
DataSourceLicense model - Tracks license details for each data source.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

This model stores detailed license information for emission factor data sources,
enabling proper compliance tracking, attribution display, and legal audit trails.

Attributes:
    id: UUID primary key (32-char hex string)
    data_source_id: FK to data_sources table
    license_type: Type of license (US_PUBLIC_DOMAIN, OGL_V3, CC_BY_SA_4, etc.)
    license_url: URL to full license text
    attribution_required: Whether attribution is legally required
    attribution_statement: Required attribution text to display
    commercial_use_allowed: Whether commercial use is permitted
    sharealike_required: Whether ShareAlike clause applies
    additional_restrictions: Any other restrictions
    license_version: Version of the license (e.g., "3.0", "4.0")
    effective_date: Date license became effective
    created_at: Record creation timestamp
    updated_at: Record update timestamp

Relationships:
    data_source: Parent DataSource object
    provenance_records: EmissionFactorProvenance records linked to this license
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, generate_uuid


class DataSourceLicense(Base):
    """
    Tracks license details for each data source.

    Enables compliance tracking, attribution display, and legal audits
    for emission factor data sources (EPA, DEFRA, etc.).
    """
    __tablename__ = "data_source_licenses"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Foreign key to data_sources (index=True creates index automatically)
    data_source_id = Column(
        String(32),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # License type
    license_type = Column(String(50), nullable=False)

    # License URL - link to full license text
    license_url = Column(String(500), nullable=True)

    # Attribution requirements
    attribution_required = Column(Boolean, default=False, nullable=False)
    attribution_statement = Column(Text, nullable=True)

    # Usage permissions
    commercial_use_allowed = Column(Boolean, default=True, nullable=False)
    sharealike_required = Column(Boolean, default=False, nullable=False)

    # Additional restrictions text
    additional_restrictions = Column(Text, nullable=True)

    # License version (e.g., "3.0", "4.0")
    license_version = Column(String(20), nullable=True)

    # Effective date
    effective_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    data_source = relationship(
        "DataSource",
        back_populates="licenses",
        foreign_keys=[data_source_id]
    )

    # Provenance records - no cascade, let FK SET NULL handle it
    # When license is deleted, provenance.data_source_license_id will be set to NULL
    provenance_records = relationship(
        "EmissionFactorProvenance",
        back_populates="license",
        passive_deletes=True  # Let DB handle FK ondelete="SET NULL"
    )

    # Valid license types constant
    LICENSE_TYPES: Dict[str, Dict[str, Any]] = {
        "US_PUBLIC_DOMAIN": {
            "attribution": False,
            "commercial": True,
            "sharealike": False,
            "description": "U.S. Public Domain under 17 U.S.C. Section 105"
        },
        "OGL_V3": {
            "attribution": True,
            "commercial": True,
            "sharealike": False,
            "description": "UK Open Government Licence v3.0"
        },
        "CC_BY_SA_4": {
            "attribution": True,
            "commercial": True,
            "sharealike": True,
            "description": "Creative Commons Attribution-ShareAlike 4.0"
        },
        "CC_BY_NC_SA_4": {
            "attribution": True,
            "commercial": False,
            "sharealike": True,
            "description": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
        },
    }

    def __repr__(self) -> str:
        return f"<DataSourceLicense(id={self.id}, type={self.license_type})>"

    @classmethod
    def get_license_defaults(cls, license_type: str) -> Dict[str, Any]:
        """
        Get default values for a license type.

        Args:
            license_type: One of the LICENSE_TYPES keys

        Returns:
            Dict with attribution, commercial, sharealike defaults
        """
        return cls.LICENSE_TYPES.get(license_type, {
            "attribution": True,
            "commercial": True,
            "sharealike": False,
            "description": "Unknown license type"
        })
