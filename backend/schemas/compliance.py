"""
Pydantic schemas for compliance tracking.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

Provides request/response models for:
- Data source license management
- Emission factor provenance tracking
- Compliance reports and verification
"""

from datetime import date, datetime
from typing import Optional, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Data Source License Schemas
# ============================================================================

class DataSourceLicenseBase(BaseModel):
    """Base schema for data source license fields."""
    license_type: str = Field(
        ...,
        description="License type: US_PUBLIC_DOMAIN, OGL_V3, CC_BY_SA_4, CC_BY_NC_SA_4"
    )
    license_url: Optional[str] = Field(
        None,
        description="URL to full license text"
    )
    attribution_required: bool = Field(
        False,
        description="Whether attribution is legally required"
    )
    attribution_statement: Optional[str] = Field(
        None,
        description="Required attribution text to display"
    )
    commercial_use_allowed: bool = Field(
        True,
        description="Whether commercial use is permitted"
    )
    sharealike_required: bool = Field(
        False,
        description="Whether ShareAlike clause applies"
    )
    additional_restrictions: Optional[str] = Field(
        None,
        description="Any additional restrictions"
    )
    license_version: Optional[str] = Field(
        None,
        description="Version of the license (e.g., '3.0', '4.0')"
    )
    effective_date: Optional[date] = Field(
        None,
        description="Date license became effective"
    )


class DataSourceLicenseCreate(DataSourceLicenseBase):
    """Schema for creating a data source license."""
    data_source_id: UUID = Field(
        ...,
        description="UUID of the parent data source"
    )


class DataSourceLicenseUpdate(BaseModel):
    """Schema for updating a data source license."""
    license_type: Optional[str] = None
    license_url: Optional[str] = None
    attribution_required: Optional[bool] = None
    attribution_statement: Optional[str] = None
    commercial_use_allowed: Optional[bool] = None
    sharealike_required: Optional[bool] = None
    additional_restrictions: Optional[str] = None
    license_version: Optional[str] = None
    effective_date: Optional[date] = None


class DataSourceLicenseResponse(DataSourceLicenseBase):
    """Schema for data source license response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_source_id: UUID
    created_at: datetime


# ============================================================================
# Emission Factor Provenance Schemas
# ============================================================================

class EmissionFactorProvenanceBase(BaseModel):
    """Base schema for emission factor provenance fields."""
    source_document: Optional[str] = Field(
        None,
        description="Original file/sheet name"
    )
    source_row_reference: Optional[str] = Field(
        None,
        description="Row/cell reference in source document"
    )
    ingestion_date: Optional[datetime] = Field(
        None,
        description="When the factor was ingested"
    )


class EmissionFactorProvenanceCreate(EmissionFactorProvenanceBase):
    """Schema for creating provenance record."""
    emission_factor_id: UUID = Field(
        ...,
        description="UUID of the parent emission factor"
    )
    data_source_license_id: Optional[UUID] = Field(
        None,
        description="UUID of the associated license"
    )


class EmissionFactorProvenanceUpdate(BaseModel):
    """Schema for updating provenance record."""
    data_source_license_id: Optional[UUID] = None
    source_document: Optional[str] = None
    source_row_reference: Optional[str] = None
    ingestion_date: Optional[datetime] = None
    license_compliance_verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


class EmissionFactorProvenanceResponse(EmissionFactorProvenanceBase):
    """Schema for provenance response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    emission_factor_id: UUID
    license_compliance_verified: bool
    verification_notes: Optional[str]
    created_at: datetime


class EmissionFactorProvenanceDetail(EmissionFactorProvenanceResponse):
    """Detailed provenance response including license info."""
    model_config = ConfigDict(from_attributes=True)

    data_source_license_id: Optional[UUID] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


# ============================================================================
# Compliance Verification Schemas
# ============================================================================

class ComplianceVerificationRequest(BaseModel):
    """Schema for verifying compliance of an emission factor."""
    verified_by: str = Field(
        ...,
        description="Email or identifier of verifier"
    )
    verification_notes: Optional[str] = Field(
        None,
        description="Notes from compliance verification"
    )


class ComplianceVerificationResponse(BaseModel):
    """Response after compliance verification."""
    provenance_id: UUID
    emission_factor_id: UUID
    license_compliance_verified: bool
    verified_by: str
    verified_at: datetime
    message: str = "Compliance verified successfully"


# ============================================================================
# Compliance Report Schemas
# ============================================================================

class ComplianceReport(BaseModel):
    """Schema for compliance summary report."""
    total_factors: int = Field(
        ...,
        description="Total number of emission factors"
    )
    verified_factors: int = Field(
        ...,
        description="Number of factors with verified compliance"
    )
    unverified_factors: int = Field(
        ...,
        description="Number of factors pending verification"
    )
    factors_by_license: Dict[str, int] = Field(
        ...,
        description="Count of factors grouped by license type"
    )
    attribution_required_sources: List[str] = Field(
        ...,
        description="List of data sources requiring attribution"
    )


class DataSourceComplianceStatus(BaseModel):
    """Compliance status for a single data source."""
    data_source_id: UUID
    data_source_name: str
    license_type: Optional[str]
    attribution_required: bool
    attribution_statement: Optional[str]
    total_factors: int
    verified_factors: int
    compliance_percentage: float


class ComplianceDetailReport(BaseModel):
    """Detailed compliance report with per-source breakdown."""
    summary: ComplianceReport
    sources: List[DataSourceComplianceStatus]
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the report was generated"
    )


# ============================================================================
# Attribution Display Schemas
# ============================================================================

class AttributionInfo(BaseModel):
    """Attribution information for display in UI."""
    source_name: str
    source_code: str = Field(
        ...,
        description="Short code for display (EPA, DEF, EXI)"
    )
    license_type: str
    attribution_required: bool
    attribution_statement: Optional[str]
    license_url: Optional[str]


class CalculationAttributions(BaseModel):
    """Attribution info for factors used in a calculation."""
    calculation_id: UUID
    attributions: List[AttributionInfo]
    disclaimer: str = Field(
        default="This application uses emission factor data from multiple public sources. "
        "The calculations provided are for informational purposes only."
    )
