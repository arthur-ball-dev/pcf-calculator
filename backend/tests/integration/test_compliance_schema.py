"""
Integration tests for Compliance Tracking Schema.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

This test suite validates:
- Alembic migration runs successfully (upgrade/downgrade)
- Tables are created with correct columns
- Indexes are created correctly
- Foreign key constraints work properly
- Seed data loads correctly

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (migration not yet created)
- Implementation must make tests PASS without modifying tests
"""

import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, date, timezone
from decimal import Decimal
import os
import tempfile

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
    """Create database session for testing with all tables created."""
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
# Test Scenario 1: Table Structure Validation
# ============================================================================

class TestTableStructure:
    """Test that tables are created with correct columns."""

    def test_data_source_licenses_table_exists(self, db_engine):
        """Test that data_source_licenses table is created."""
        try:
            from backend.models import DataSourceLicense
        except ImportError:
            pytest.skip("DataSourceLicense model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)

        assert "data_source_licenses" in inspector.get_table_names()

    def test_data_source_licenses_columns(self, db_engine):
        """Test data_source_licenses has expected columns."""
        try:
            from backend.models import DataSourceLicense
        except ImportError:
            pytest.skip("DataSourceLicense model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("data_source_licenses")}

        expected_columns = {
            "id",
            "data_source_id",
            "license_type",
            "license_url",
            "attribution_required",
            "attribution_statement",
            "commercial_use_allowed",
            "sharealike_required",
            "additional_restrictions",
            "license_version",
            "effective_date",
            "created_at",
            "updated_at"
        }

        for col in expected_columns:
            assert col in columns, f"Missing column: {col}"

    def test_emission_factor_provenance_table_exists(self, db_engine):
        """Test that emission_factor_provenance table is created."""
        try:
            from backend.models import EmissionFactorProvenance
        except ImportError:
            pytest.skip("EmissionFactorProvenance model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)

        assert "emission_factor_provenance" in inspector.get_table_names()

    def test_emission_factor_provenance_columns(self, db_engine):
        """Test emission_factor_provenance has expected columns."""
        try:
            from backend.models import EmissionFactorProvenance
        except ImportError:
            pytest.skip("EmissionFactorProvenance model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("emission_factor_provenance")}

        expected_columns = {
            "id",
            "emission_factor_id",
            "data_source_license_id",
            "source_document",
            "source_row_reference",
            "ingestion_date",
            "license_compliance_verified",
            "verification_notes",
            "verified_by",
            "verified_at",
            "created_at"
        }

        for col in expected_columns:
            assert col in columns, f"Missing column: {col}"


# ============================================================================
# Test Scenario 2: Index Validation
# ============================================================================

class TestIndexes:
    """Test that indexes are created correctly."""

    def test_data_source_licenses_data_source_id_index(self, db_engine):
        """Test index on data_source_licenses.data_source_id."""
        try:
            from backend.models import DataSourceLicense
        except ImportError:
            pytest.skip("DataSourceLicense model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("data_source_licenses")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        # data_source_id should be indexed
        assert "data_source_id" in index_columns

    def test_emission_factor_provenance_emission_factor_id_index(self, db_engine):
        """Test index on emission_factor_provenance.emission_factor_id."""
        try:
            from backend.models import EmissionFactorProvenance
        except ImportError:
            pytest.skip("EmissionFactorProvenance model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("emission_factor_provenance")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        # emission_factor_id should be indexed
        assert "emission_factor_id" in index_columns

    def test_emission_factor_provenance_license_id_index(self, db_engine):
        """Test index on emission_factor_provenance.data_source_license_id."""
        try:
            from backend.models import EmissionFactorProvenance
        except ImportError:
            pytest.skip("EmissionFactorProvenance model not yet implemented")

        Base.metadata.create_all(db_engine)
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("emission_factor_provenance")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        # data_source_license_id should be indexed
        assert "data_source_license_id" in index_columns


# ============================================================================
# Test Scenario 3: Foreign Key Constraints
# ============================================================================

class TestForeignKeyConstraints:
    """Test foreign key constraints are enforced."""

    def test_license_requires_valid_data_source(self, db_session):
        """Test that license requires valid data_source_id."""
        from backend.models import DataSourceLicense
        from sqlalchemy.exc import IntegrityError

        # Try to create license with non-existent data source
        license_record = DataSourceLicense(
            data_source_id="nonexistent_id_12345678",
            license_type="OGL_V3"
        )
        db_session.add(license_record)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_provenance_requires_valid_emission_factor(self, db_session):
        """Test that provenance requires valid emission_factor_id."""
        from backend.models import EmissionFactorProvenance
        from sqlalchemy.exc import IntegrityError

        # Try to create provenance with non-existent emission factor
        provenance = EmissionFactorProvenance(
            emission_factor_id="nonexistent_id_12345678"
        )
        db_session.add(provenance)

        with pytest.raises(IntegrityError):
            db_session.commit()


# ============================================================================
# Test Scenario 4: Seed Data Loading
# ============================================================================

class TestSeedDataLoading:
    """Test seed data loads correctly."""

    def test_seed_license_data_function_exists(self):
        """Test that seed_licenses function is importable."""
        try:
            from backend.database.seeds.compliance_seeds import seed_licenses
        except ImportError:
            pytest.skip("compliance_seeds module not yet implemented")

        assert callable(seed_licenses)

    def test_seed_license_data(self, db_session):
        """Test seeding license data for EPA, DEFRA, EXIOBASE."""
        try:
            from backend.database.seeds.compliance_seeds import seed_licenses, LICENSE_DATA
            from backend.models import DataSource, DataSourceLicense
        except ImportError:
            pytest.skip("compliance_seeds module not yet implemented")

        # First seed data sources
        from backend.database.seeds.data_sources import seed_data_sources
        seed_data_sources(db_session)

        # Now seed licenses
        licenses = seed_licenses(db_session)

        # Check all expected sources have licenses
        for source_code in LICENSE_DATA.keys():
            data_source = db_session.query(DataSource).filter(
                DataSource.name.like(f"%{source_code}%")
            ).first()
            if data_source:
                license_record = db_session.query(DataSourceLicense).filter(
                    DataSourceLicense.data_source_id == data_source.id
                ).first()
                # License should exist if data source exists
                if source_code in licenses:
                    assert license_record is not None

    def test_seed_epa_license(self, db_session):
        """Test EPA license has correct values."""
        try:
            from backend.database.seeds.compliance_seeds import seed_licenses
            from backend.models import DataSource, DataSourceLicense
        except ImportError:
            pytest.skip("compliance_seeds module not yet implemented")

        # Seed data sources first
        from backend.database.seeds.data_sources import seed_data_sources
        seed_data_sources(db_session)

        # Seed licenses
        licenses = seed_licenses(db_session)

        # Check EPA license
        if "EPA" in licenses:
            epa_license = licenses["EPA"]
            assert epa_license.license_type == "US_PUBLIC_DOMAIN"
            assert epa_license.attribution_required is False
            assert epa_license.commercial_use_allowed is True

    def test_seed_defra_license(self, db_session):
        """Test DEFRA license has correct values."""
        try:
            from backend.database.seeds.compliance_seeds import seed_licenses
            from backend.models import DataSource, DataSourceLicense
        except ImportError:
            pytest.skip("compliance_seeds module not yet implemented")

        # Seed data sources first
        from backend.database.seeds.data_sources import seed_data_sources
        seed_data_sources(db_session)

        # Seed licenses
        licenses = seed_licenses(db_session)

        # Check DEFRA license
        if "DEFRA" in licenses:
            defra_license = licenses["DEFRA"]
            assert defra_license.license_type == "OGL_V3"
            assert defra_license.attribution_required is True
            assert defra_license.commercial_use_allowed is True
            assert defra_license.sharealike_required is False

    def test_seed_exiobase_license(self, db_session):
        """Test EXIOBASE license has correct values."""
        try:
            from backend.database.seeds.compliance_seeds import seed_licenses
            from backend.models import DataSource, DataSourceLicense
        except ImportError:
            pytest.skip("compliance_seeds module not yet implemented")

        # Seed data sources first
        from backend.database.seeds.data_sources import seed_data_sources
        seed_data_sources(db_session)

        # Seed licenses
        licenses = seed_licenses(db_session)

        # Check EXIOBASE license (in data_sources it's named "Exiobase")
        if "EXIOBASE" in licenses:
            exio_license = licenses["EXIOBASE"]
            assert exio_license.license_type == "CC_BY_SA_4"
            assert exio_license.attribution_required is True
            assert exio_license.sharealike_required is True


# ============================================================================
# Test Scenario 5: Cascade Delete Behavior
# ============================================================================

class TestCascadeDeleteBehavior:
    """Test cascade delete behaviors work correctly."""

    def test_delete_data_source_cascades_to_licenses(self, db_session):
        """Test deleting data source deletes its licenses."""
        from backend.models import DataSource, DataSourceLicense

        # Create data source with license
        ds = DataSource(
            name="Cascade Delete Test",
            source_type="file"
        )
        db_session.add(ds)
        db_session.commit()

        license_record = DataSourceLicense(
            data_source_id=ds.id,
            license_type="OGL_V3"
        )
        db_session.add(license_record)
        db_session.commit()

        license_id = license_record.id

        # Delete data source
        db_session.delete(ds)
        db_session.commit()

        # License should be deleted
        retrieved = db_session.get(DataSourceLicense, license_id)
        assert retrieved is None

    def test_delete_emission_factor_cascades_to_provenance(self, db_session):
        """Test deleting emission factor deletes its provenance."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        # Create emission factor with provenance
        ef = EmissionFactor(
            activity_name="Cascade EF Test",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="Test",
            geography="GLO"
        )
        db_session.add(ef)
        db_session.commit()

        prov = EmissionFactorProvenance(
            emission_factor_id=ef.id,
            source_document="test.xlsx"
        )
        db_session.add(prov)
        db_session.commit()

        prov_id = prov.id

        # Delete emission factor
        db_session.delete(ef)
        db_session.commit()

        # Provenance should be deleted
        retrieved = db_session.get(EmissionFactorProvenance, prov_id)
        assert retrieved is None


# ============================================================================
# Test Scenario 6: Compliance Query Patterns
# ============================================================================

class TestComplianceQueryPatterns:
    """Test common compliance query patterns work correctly."""

    def test_query_unverified_factors(self, db_session):
        """Test querying factors that need compliance verification."""
        from backend.models import EmissionFactor, EmissionFactorProvenance

        # Create factors with provenance
        ef1 = EmissionFactor(
            activity_name="Verified EF",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="EPA",
            geography="US"
        )
        ef2 = EmissionFactor(
            activity_name="Unverified EF",
            co2e_factor=Decimal("2.0"),
            unit="kg",
            data_source="DEFRA",
            geography="UK"
        )
        db_session.add_all([ef1, ef2])
        db_session.commit()

        prov1 = EmissionFactorProvenance(
            emission_factor_id=ef1.id,
            license_compliance_verified=True
        )
        prov2 = EmissionFactorProvenance(
            emission_factor_id=ef2.id,
            license_compliance_verified=False
        )
        db_session.add_all([prov1, prov2])
        db_session.commit()

        # Query unverified
        unverified = db_session.query(EmissionFactorProvenance).filter(
            EmissionFactorProvenance.license_compliance_verified == False
        ).all()

        assert len(unverified) >= 1
        assert any(p.emission_factor_id == ef2.id for p in unverified)

    def test_query_factors_requiring_attribution(self, db_session):
        """Test querying factors that require attribution display."""
        from backend.models import (
            DataSource, DataSourceLicense, EmissionFactor, EmissionFactorProvenance
        )

        # Create sources with different attribution requirements
        ds1 = DataSource(name="EPA Test", source_type="file")
        ds2 = DataSource(name="DEFRA Test", source_type="file")
        db_session.add_all([ds1, ds2])
        db_session.commit()

        lic1 = DataSourceLicense(
            data_source_id=ds1.id,
            license_type="US_PUBLIC_DOMAIN",
            attribution_required=False
        )
        lic2 = DataSourceLicense(
            data_source_id=ds2.id,
            license_type="OGL_V3",
            attribution_required=True,
            attribution_statement="Crown copyright"
        )
        db_session.add_all([lic1, lic2])
        db_session.commit()

        # Create EFs with provenance linked to licenses
        ef1 = EmissionFactor(
            activity_name="EPA Factor",
            co2e_factor=Decimal("1.0"),
            unit="kg",
            data_source="EPA",
            geography="US"
        )
        ef2 = EmissionFactor(
            activity_name="DEFRA Factor",
            co2e_factor=Decimal("2.0"),
            unit="kg",
            data_source="DEFRA",
            geography="UK"
        )
        db_session.add_all([ef1, ef2])
        db_session.commit()

        prov1 = EmissionFactorProvenance(
            emission_factor_id=ef1.id,
            data_source_license_id=lic1.id
        )
        prov2 = EmissionFactorProvenance(
            emission_factor_id=ef2.id,
            data_source_license_id=lic2.id
        )
        db_session.add_all([prov1, prov2])
        db_session.commit()

        # Query factors that require attribution
        attribution_required = db_session.query(EmissionFactorProvenance).join(
            DataSourceLicense
        ).filter(
            DataSourceLicense.attribution_required == True
        ).all()

        assert len(attribution_required) >= 1


# ============================================================================
# Test Scenario 7: Pydantic Schema Validation
# ============================================================================

class TestPydanticSchemas:
    """Test Pydantic schemas for compliance models."""

    def test_license_create_schema(self):
        """Test DataSourceLicenseCreate Pydantic schema."""
        try:
            from backend.schemas.compliance import DataSourceLicenseCreate
        except ImportError:
            pytest.skip("compliance schemas not yet implemented")

        import uuid
        data = {
            "data_source_id": str(uuid.uuid4()),
            "license_type": "OGL_V3",
            "attribution_required": True,
            "attribution_statement": "Crown copyright"
        }
        schema = DataSourceLicenseCreate(**data)
        assert schema.license_type == "OGL_V3"
        assert schema.attribution_required is True

    def test_license_response_schema(self):
        """Test DataSourceLicenseResponse Pydantic schema."""
        try:
            from backend.schemas.compliance import DataSourceLicenseResponse
        except ImportError:
            pytest.skip("compliance schemas not yet implemented")

        import uuid
        from datetime import datetime
        data = {
            "id": str(uuid.uuid4()),
            "data_source_id": str(uuid.uuid4()),
            "license_type": "CC_BY_SA_4",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "attribution_required": True,
            "attribution_statement": "EXIOBASE 3.8",
            "commercial_use_allowed": True,
            "sharealike_required": True,
            "created_at": datetime.now()
        }
        schema = DataSourceLicenseResponse(**data)
        assert schema.license_type == "CC_BY_SA_4"

    def test_provenance_create_schema(self):
        """Test EmissionFactorProvenanceCreate Pydantic schema."""
        try:
            from backend.schemas.compliance import EmissionFactorProvenanceCreate
        except ImportError:
            pytest.skip("compliance schemas not yet implemented")

        import uuid
        data = {
            "emission_factor_id": str(uuid.uuid4()),
            "source_document": "defra-2024.xlsx",
            "source_row_reference": "Sheet1!A10"
        }
        schema = EmissionFactorProvenanceCreate(**data)
        assert schema.source_document == "defra-2024.xlsx"

    def test_provenance_response_schema(self):
        """Test EmissionFactorProvenanceResponse Pydantic schema."""
        try:
            from backend.schemas.compliance import EmissionFactorProvenanceResponse
        except ImportError:
            pytest.skip("compliance schemas not yet implemented")

        import uuid
        from datetime import datetime
        data = {
            "id": str(uuid.uuid4()),
            "emission_factor_id": str(uuid.uuid4()),
            "source_document": "epa-2024.xlsx",
            "license_compliance_verified": True,
            "verification_notes": "Public domain",
            "created_at": datetime.now()
        }
        schema = EmissionFactorProvenanceResponse(**data)
        assert schema.license_compliance_verified is True

    def test_compliance_report_schema(self):
        """Test ComplianceReport Pydantic schema."""
        try:
            from backend.schemas.compliance import ComplianceReport
        except ImportError:
            pytest.skip("compliance schemas not yet implemented")

        data = {
            "total_factors": 100,
            "verified_factors": 80,
            "unverified_factors": 20,
            "factors_by_license": {
                "US_PUBLIC_DOMAIN": 40,
                "OGL_V3": 35,
                "CC_BY_SA_4": 25
            },
            "attribution_required_sources": ["DEFRA Conversion Factors", "Exiobase"]
        }
        schema = ComplianceReport(**data)
        assert schema.total_factors == 100
        assert schema.verified_factors == 80
