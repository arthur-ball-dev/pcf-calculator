"""
EmissionFactorProvenance model - Tracks provenance of each emission factor.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

This model stores provenance information for emission factors, enabling
audit trails for license compliance and supporting legal review.

Attributes:
    id: UUID primary key (32-char hex string)
    emission_factor_id: FK to emission_factors table (CASCADE delete)
    data_source_license_id: FK to data_source_licenses table (SET NULL on delete)
    source_document: Original file/sheet name
    source_row_reference: Row/cell reference in source document
    ingestion_date: When the factor was ingested
    license_compliance_verified: Whether compliance has been verified
    verification_notes: Notes from compliance verification
    verified_by: Who verified compliance
    verified_at: When compliance was verified
    created_at: Record creation timestamp

Relationships:
    emission_factor: Parent EmissionFactor object
    license: DataSourceLicense object (optional)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, generate_uuid


class EmissionFactorProvenance(Base):
    """
    Tracks provenance of each emission factor for compliance audit.

    Stores source document references, ingestion dates, and compliance
    verification status for each emission factor.
    """
    __tablename__ = "emission_factor_provenance"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Foreign key to emission_factors (CASCADE on delete, index=True for auto-indexing)
    emission_factor_id = Column(
        String(32),
        ForeignKey("emission_factors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Foreign key to data_source_licenses (SET NULL on delete, index=True for auto-indexing)
    data_source_license_id = Column(
        String(32),
        ForeignKey("data_source_licenses.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Source reference information
    source_document = Column(String(500), nullable=True)
    source_row_reference = Column(String(100), nullable=True)

    # Ingestion timestamp
    ingestion_date = Column(DateTime, nullable=True)

    # Compliance verification
    license_compliance_verified = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Record creation timestamp
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    emission_factor = relationship(
        "EmissionFactor",
        back_populates="provenance",
        foreign_keys=[emission_factor_id]
    )

    license = relationship(
        "DataSourceLicense",
        back_populates="provenance_records",
        foreign_keys=[data_source_license_id]
    )

    def __repr__(self) -> str:
        return f"<EmissionFactorProvenance(id={self.id}, factor_id={self.emission_factor_id})>"

    def verify_compliance(
        self,
        verified_by: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Mark this emission factor as compliance-verified.

        Args:
            verified_by: Email or identifier of verifier
            notes: Optional verification notes
        """
        self.license_compliance_verified = True
        self.verified_by = verified_by
        self.verified_at = datetime.utcnow()
        if notes:
            self.verification_notes = notes
