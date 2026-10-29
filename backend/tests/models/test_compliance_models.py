"""
Test suite for Compliance Tracking models.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

This test suite validates:
- DataSourceLicense model CRUD operations
- EmissionFactorProvenance model CRUD operations
- Foreign key relationships and cascade behaviors
- License type validation
- Compliance verification workflow
- Timestamp auto-update functionality

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (models not yet implemented)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from datetime import datetime, date, timezone
from decimal import Decimal
import uuid

# Import models - compliance models will be implemented in Phase B
from backend.models import Base


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing."""
    from backend.models import Base
    try:
        from backend.models import DataSourceLicense, EmissionFactorProvenance
    except ImportError:
        pytest.skip("Compliance models not yet implemented")

    Base.metadata.create_all(db_engine)
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


# ============================================================================
# Test Scenario 1: DataSourceLicense CRUD Operations
# ============================================================================

class TestDataSourceLicenseCRUD:
    """Test DataSourceLicense model CRUD operations."""

    def test_create_license_with_required_fields(self, db_session: Session):
        """Test creating a data source license with required fields."""
        from backend.models import DataSource, DataSourceLicense

        # Create data source first
        data_source = DataSource(
            name="EPA GHG Factors",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        # Create license
        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="US_PUBLIC_DOMAIN"
        )
        db_session.add(license_record)
        db_session.commit()

        # Verify creation
        assert license_record.id is not None
        assert license_record.data_source_id == data_source.id
        assert license_record.license_type == "US_PUBLIC_DOMAIN"
        assert license_record.created_at is not None

    def test_create_license_with_all_fields(self, db_session: Session):
        """Test creating a license with all fields populated."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="DEFRA Factors",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3",
            license_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            attribution_required=True,
            attribution_statement="Contains UK Government GHG Conversion Factors Crown copyright",
            commercial_use_allowed=True,
            sharealike_required=False,
            additional_restrictions=None,
            license_version="3.0",
            effective_date=date(2024, 1, 1)
        )
        db_session.add(license_record)
        db_session.commit()

        assert license_record.id is not None
        assert license_record.license_type == "OGL_V3"
        assert license_record.license_url == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        assert license_record.attribution_required is True
        assert license_record.commercial_use_allowed is True
        assert license_record.sharealike_required is False
        assert license_record.license_version == "3.0"
        assert license_record.effective_date == date(2024, 1, 1)

    def test_read_license_by_id(self, db_session: Session):
        """Test reading a license by ID."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="CC_BY_SA_4"
        )
        db_session.add(license_record)
        db_session.commit()

        license_id = license_record.id
        db_session.expire_all()

        retrieved = db_session.get(DataSourceLicense, license_id)
        assert retrieved is not None
        assert retrieved.license_type == "CC_BY_SA_4"

    def test_update_license(self, db_session: Session):
        """Test updating a license record."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Update Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="US_PUBLIC_DOMAIN",
            attribution_required=False
        )
        db_session.add(license_record)
        db_session.commit()

        # Update
        license_record.attribution_required = True
        license_record.attribution_statement = "EPA GHG Emission Factors Hub"
        db_session.commit()

        db_session.expire_all()
        retrieved = db_session.get(DataSourceLicense, license_record.id)
        assert retrieved.attribution_required is True
        assert retrieved.attribution_statement == "EPA GHG Emission Factors Hub"

    def test_delete_license(self, db_session: Session):
        """Test deleting a license record."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Delete Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="US_PUBLIC_DOMAIN"
        )
        db_session.add(license_record)
        db_session.commit()

        license_id = license_record.id
        db_session.delete(license_record)
        db_session.commit()

        retrieved = db_session.get(DataSourceLicense, license_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 2: DataSourceLicense Relationships
# ============================================================================

class TestDataSourceLicenseRelationships:
    """Test DataSourceLicense relationships with DataSource."""

    def test_license_references_data_source(self, db_session: Session):
        """Test that license references its parent data source."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Relationship Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3"
        )
        db_session.add(license_record)
        db_session.commit()

        # Verify FK relationship
        assert license_record.data_source_id == data_source.id

        # Access data source via relationship
        db_session.refresh(license_record)
        assert license_record.data_source.name == "Relationship Test Source"

    def test_data_source_licenses_relationship(self, db_session: Session):
        """Test accessing licenses from data source."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Multi License Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license1 = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3",
            license_version="3.0"
        )
        license2 = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3",
            license_version="3.1"
        )
        db_session.add_all([license1, license2])
        db_session.commit()

        db_session.refresh(data_source)
        assert len(data_source.licenses) == 2

    def test_cascade_delete_data_source_deletes_licenses(self, db_session: Session):
        """Test that deleting data source cascades to delete licenses."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Cascade Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="CC_BY_SA_4"
        )
        db_session.add(license_record)
        db_session.commit()

        license_id = license_record.id

        # Delete data source - should cascade
        db_session.delete(data_source)
        db_session.commit()

        # License should be deleted
        retrieved = db_session.get(DataSourceLicense, license_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 3: EmissionFactorProvenance CRUD Operations
# ============================================================================

class TestEmissionFactorProvenanceCRUD:
    """Test EmissionFactorProvenance model CRUD operations."""

    def test_create_provenance_with_required_fields(self, db_session: Session):
        """Test creating provenance record with required fields."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        # Create emission factor first
        ef = EmissionFactor(
            activity_name="Test Activity",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="EPA",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        assert provenance.id is not None
        assert provenance.emission_factor_id == ef.id
        assert provenance.created_at is not None
        assert provenance.license_compliance_verified is False

    def test_create_provenance_with_all_fields(self, db_session: Session):
        """Test creating provenance with all fields populated."""
        from backend.models import (
            DataSource, DataSourceLicense, EmissionFactor, EmissionFactorProvenance
        )

        # Create data source and license
        data_source = DataSource(
            name="DEFRA",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3"
        )
        db_session.add(license_record)
        db_session.commit()

        # Create emission factor
        ef = EmissionFactor(
            activity_name="Grid Electricity UK",
            co2e_factor=Decimal("0.21233"),
            unit="kWh",
            data_source="DEFRA",
            geography="UK"
        )
        db_session.add(ef)
        db_session.commit()

        # Create full provenance
        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            data_source_license_id=license_record.id,
            source_document="ghg-conversion-factors-2024.xlsx",
            source_row_reference="Sheet1!B15",
            ingestion_date=datetime.now(timezone.utc),
            license_compliance_verified=True,
            verification_notes="Verified OGL v3.0 compliance",
            verified_by="admin@example.com",
            verified_at=datetime.now(timezone.utc)
        )
        db_session.add(provenance)
        db_session.commit()

        assert provenance.id is not None
        assert provenance.source_document == "ghg-conversion-factors-2024.xlsx"
        assert provenance.source_row_reference == "Sheet1!B15"
        assert provenance.license_compliance_verified is True
        assert provenance.verified_by == "admin@example.com"

    def test_read_provenance_by_id(self, db_session: Session):
        """Test reading provenance by ID."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Natural Gas",
            co2e_factor=Decimal("2.0"),
            unit="m3",
            data_source="EPA",
            geography="US"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            source_document="epa-ghg-factors-2024.xlsx"
        )
        db_session.add(provenance)
        db_session.commit()

        prov_id = provenance.id
        db_session.expire_all()

        retrieved = db_session.get(EmissionFactorProvenance, prov_id)
        assert retrieved is not None
        assert retrieved.source_document == "epa-ghg-factors-2024.xlsx"

    def test_update_provenance_verification(self, db_session: Session):
        """Test updating provenance verification status."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Diesel Fuel",
            co2e_factor=Decimal("2.68"),
            unit="L",
            data_source="EPA",
            geography="US"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            license_compliance_verified=False
        )
        db_session.add(provenance)
        db_session.commit()

        # Verify compliance
        provenance.license_compliance_verified = True
        provenance.verified_by = "compliance@example.com"
        provenance.verified_at = datetime.now(timezone.utc)
        provenance.verification_notes = "Public domain - no attribution required"
        db_session.commit()

        db_session.expire_all()
        retrieved = db_session.get(EmissionFactorProvenance, provenance.id)
        assert retrieved.license_compliance_verified is True
        assert retrieved.verified_by == "compliance@example.com"

    def test_delete_provenance(self, db_session: Session):
        """Test deleting provenance record."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="To Delete",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        prov_id = provenance.id
        db_session.delete(provenance)
        db_session.commit()

        retrieved = db_session.get(EmissionFactorProvenance, prov_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 4: EmissionFactorProvenance Relationships
# ============================================================================

class TestEmissionFactorProvenanceRelationships:
    """Test EmissionFactorProvenance relationships."""

    def test_provenance_references_emission_factor(self, db_session: Session):
        """Test provenance references its parent emission factor."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Aluminum Production",
            co2e_factor=Decimal("8.5"),
            unit="kg",
            data_source="Test",
            geography="EU"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            source_document="test_data.csv"
        )
        db_session.add(provenance)
        db_session.commit()

        db_session.refresh(provenance)
        assert provenance.emission_factor.activity_name == "Aluminum Production"

    def test_emission_factor_provenance_relationship(self, db_session: Session):
        """Test accessing provenance from emission factor."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Steel Production",
            co2e_factor=Decimal("1.85"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            source_document="test_data.csv"
        )
        db_session.add(provenance)
        db_session.commit()

        db_session.refresh(ef)
        # One-to-one relationship
        assert ef.provenance is not None
        assert ef.provenance.source_document == "test_data.csv"

    def test_provenance_references_license(self, db_session: Session):
        """Test provenance can reference license record."""
        from backend.models import (
            DataSource, DataSourceLicense, EmissionFactor, EmissionFactorProvenance
        )

        data_source = DataSource(
            name="Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="CC_BY_SA_4"
        )
        db_session.add(license_record)
        db_session.commit()

        ef = EmissionFactor(
            activity_name="Copper Wire",
            co2e_factor=Decimal("3.5"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            data_source_license_id=license_record.id
        )
        db_session.add(provenance)
        db_session.commit()

        db_session.refresh(provenance)
        assert provenance.license is not None
        assert provenance.license.license_type == "CC_BY_SA_4"

    def test_cascade_delete_emission_factor_deletes_provenance(self, db_session: Session):
        """Test deleting emission factor cascades to delete provenance."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Cascade Delete Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        prov_id = provenance.id

        # Delete emission factor
        db_session.delete(ef)
        db_session.commit()

        # Provenance should be deleted
        retrieved = db_session.get(EmissionFactorProvenance, prov_id)
        assert retrieved is None

    def test_license_deletion_sets_provenance_license_null(self, db_session: Session):
        """Test deleting license sets provenance license_id to NULL."""
        from backend.models import (
            DataSource, DataSourceLicense, EmissionFactor, EmissionFactorProvenance
        )

        data_source = DataSource(
            name="License Null Test",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="CC_BY_SA_4"
        )
        db_session.add(license_record)
        db_session.commit()

        ef = EmissionFactor(
            activity_name="License Null EF",
            co2e_factor=Decimal("2.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            data_source_license_id=license_record.id
        )
        db_session.add(provenance)
        db_session.commit()

        prov_id = provenance.id

        # Delete license - provenance should have NULL license_id
        db_session.delete(license_record)
        db_session.commit()

        db_session.expire_all()
        retrieved = db_session.get(EmissionFactorProvenance, prov_id)
        assert retrieved is not None
        assert retrieved.data_source_license_id is None


# ============================================================================
# Test Scenario 5: License Type Validation
# ============================================================================

class TestLicenseTypeValidation:
    """Test license type field values."""

    def test_valid_license_types(self, db_session: Session):
        """Test that expected license types are accepted."""
        from backend.models import DataSource, DataSourceLicense

        valid_types = ["US_PUBLIC_DOMAIN", "OGL_V3", "CC_BY_SA_4", "CC_BY_NC_SA_4"]

        for i, license_type in enumerate(valid_types):
            data_source = DataSource(
                name=f"License Type Test {i}",
                source_type="file"
            )
            db_session.add(data_source)
            db_session.commit()

            license_record = DataSourceLicense(
                data_source_id=data_source.id,
                license_type=license_type
            )
            db_session.add(license_record)

        db_session.commit()

        # All should be created
        from backend.models import DataSourceLicense
        count = db_session.query(DataSourceLicense).count()
        assert count == 4

    def test_license_type_constants(self, db_session: Session):
        """Test that LICENSE_TYPES constant is defined on model."""
        from backend.models import DataSourceLicense

        # Verify LICENSE_TYPES constant exists
        assert hasattr(DataSourceLicense, "LICENSE_TYPES")
        assert "US_PUBLIC_DOMAIN" in DataSourceLicense.LICENSE_TYPES
        assert "OGL_V3" in DataSourceLicense.LICENSE_TYPES
        assert "CC_BY_SA_4" in DataSourceLicense.LICENSE_TYPES


# ============================================================================
# Test Scenario 6: Compliance Verification Workflow
# ============================================================================

class TestComplianceVerificationWorkflow:
    """Test compliance verification workflow scenarios."""

    def test_unverified_factor_workflow(self, db_session: Session):
        """Test creating unverified factor and then verifying."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Unverified Activity",
            co2e_factor=Decimal("5.0"),
            unit="kg",
            data_source="DEFRA",
            geography="UK"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            source_document="defra-2024.xlsx",
            ingestion_date=datetime.now(timezone.utc),
            license_compliance_verified=False
        )
        db_session.add(provenance)
        db_session.commit()

        # Query unverified factors
        from backend.models import EmissionFactorProvenance
        unverified = db_session.query(EmissionFactorProvenance).filter(
            EmissionFactorProvenance.license_compliance_verified == False
        ).all()
        assert len(unverified) >= 1

        # Verify the factor
        provenance.license_compliance_verified = True
        provenance.verified_by = "legal@company.com"
        provenance.verified_at = datetime.now(timezone.utc)
        provenance.verification_notes = "OGL v3.0 requires attribution"
        db_session.commit()

        # Verify it's now compliant
        db_session.expire_all()
        retrieved = db_session.get(EmissionFactorProvenance, provenance.id)
        assert retrieved.license_compliance_verified is True

    def test_query_factors_by_verification_status(self, db_session: Session):
        """Test querying factors by verification status."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        # Create verified and unverified factors
        ef1 = EmissionFactor(
            activity_name="Verified Factor",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="EPA",
            geography="US"
        )
        ef2 = EmissionFactor(
            activity_name="Unverified Factor",
            co2e_factor=Decimal("2.0"),
            unit="kg",
            data_source="DEFRA",
            geography="UK"
        )
        db_session.add_all([ef1, ef2])
        db_session.commit()

        prov1 = EmissionFactorProvenance(
            emission_factor_id=ef1.id,
            license_compliance_verified=True,
            verified_by="admin",
            verified_at=datetime.now(timezone.utc)
        )
        prov2 = EmissionFactorProvenance(
            emission_factor_id=ef2.id,
            license_compliance_verified=False
        )
        db_session.add_all([prov1, prov2])
        db_session.commit()

        # Query verified
        verified = db_session.query(EmissionFactorProvenance).filter(
            EmissionFactorProvenance.license_compliance_verified == True
        ).all()
        assert len(verified) >= 1

        # Query unverified
        unverified = db_session.query(EmissionFactorProvenance).filter(
            EmissionFactorProvenance.license_compliance_verified == False
        ).all()
        assert len(unverified) >= 1


# ============================================================================
# Test Scenario 7: Default Values
# ============================================================================

class TestDefaultValues:
    """Test default values for model fields."""

    def test_license_default_values(self, db_session: Session):
        """Test DataSourceLicense default values."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Default Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="US_PUBLIC_DOMAIN"
        )
        db_session.add(license_record)
        db_session.commit()

        # Check defaults
        assert license_record.attribution_required is False
        assert license_record.commercial_use_allowed is True
        assert license_record.sharealike_required is False

    def test_provenance_default_values(self, db_session: Session):
        """Test EmissionFactorProvenance default values."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Default Provenance Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        # Check defaults
        assert provenance.license_compliance_verified is False


# ============================================================================
# Test Scenario 8: Timestamps
# ============================================================================

class TestTimestamps:
    """Test timestamp field behavior."""

    def test_license_created_at_auto_set(self, db_session: Session):
        """Test that license created_at is auto-set."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Timestamp Test Source",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3"
        )
        db_session.add(license_record)
        db_session.commit()

        assert license_record.created_at is not None

    def test_provenance_created_at_auto_set(self, db_session: Session):
        """Test that provenance created_at is auto-set."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Provenance Timestamp Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        assert provenance.created_at is not None


# ============================================================================
# Test Scenario 9: Model Repr
# ============================================================================

class TestModelRepr:
    """Test model __repr__ methods."""

    def test_license_repr(self, db_session: Session):
        """Test DataSourceLicense __repr__."""
        from backend.models import DataSource, DataSourceLicense

        data_source = DataSource(
            name="Repr Test",
            source_type="file"
        )
        db_session.add(data_source)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type="OGL_V3"
        )
        db_session.add(license_record)
        db_session.commit()

        repr_str = repr(license_record)
        assert "DataSourceLicense" in repr_str
        assert "OGL_V3" in repr_str

    def test_provenance_repr(self, db_session: Session):
        """Test EmissionFactorProvenance __repr__."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        ef = EmissionFactor(
            activity_name="Repr EF Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        provenance = EmissionFactorProvenance(
            emission_factor_id=ef.id
        )
        db_session.add(provenance)
        db_session.commit()

        repr_str = repr(provenance)
        assert "EmissionFactorProvenance" in repr_str
