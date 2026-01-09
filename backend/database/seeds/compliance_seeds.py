"""
Seed data for compliance tracking tables.

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

Seeds license information for EPA, DEFRA, and EXIOBASE data sources.

Usage:
    from backend.database.seeds.compliance_seeds import seed_licenses
    from backend.database.connection import db_context

    with db_context() as session:
        licenses = seed_licenses(session)
        print(f"Seeded {len(licenses)} licenses")
"""

from typing import Dict, List, Optional, Any
from datetime import date
from sqlalchemy.orm import Session


# License data for each data source
# Keys match source codes used in External_Data_Source_Compliance_Guide.md
LICENSE_DATA: Dict[str, Dict[str, Any]] = {
    "EPA": {
        "license_type": "US_PUBLIC_DOMAIN",
        "license_url": "https://www.epa.gov/web-policies-and-procedures/epa-disclaimers",
        "attribution_required": False,
        "attribution_statement": (
            "Data from U.S. Environmental Protection Agency (EPA) GHG Emission Factors Hub. "
            "This work is in the public domain under 17 U.S.C. Section 105."
        ),
        "commercial_use_allowed": True,
        "sharealike_required": False,
        "additional_restrictions": None,
        "license_version": None,
        "effective_date": None,
        "data_source_pattern": "EPA",  # Pattern to match in data_sources.name
    },
    "DEFRA": {
        "license_type": "OGL_V3",
        "license_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "attribution_required": True,
        "attribution_statement": (
            "Contains public sector information licensed under the Open Government Licence v3.0. "
            "Source: UK Department for Energy Security and Net Zero (DESNZ) / DEFRA "
            "Greenhouse Gas Conversion Factors."
        ),
        "commercial_use_allowed": True,
        "sharealike_required": False,
        "additional_restrictions": None,
        "license_version": "3.0",
        "effective_date": date(2024, 1, 1),
        "data_source_pattern": "DEFRA",
    },
    "EXIOBASE": {
        "license_type": "CC_BY_SA_4",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "attribution_required": True,
        "attribution_statement": (
            "EXIOBASE 3 data is licensed under Creative Commons Attribution-ShareAlike 4.0 "
            "International (CC BY-SA 4.0). Credit: EXIOBASE Consortium. "
            "Any derivative works must be shared under the same license."
        ),
        "commercial_use_allowed": True,
        "sharealike_required": True,
        "additional_restrictions": (
            "Derivative works must be shared under CC BY-SA 4.0 or compatible license."
        ),
        "license_version": "4.0",
        "effective_date": None,
        "data_source_pattern": "Exiobase",  # Case-sensitive pattern
    },
}


def seed_licenses(
    session: Session,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Seed license records for known data sources.

    Creates DataSourceLicense records for EPA, DEFRA, and EXIOBASE
    data sources based on their licensing requirements.

    Args:
        session: SQLAlchemy database session
        skip_existing: If True, skip sources that already have licenses

    Returns:
        Dict mapping source codes to created DataSourceLicense objects
    """
    from backend.models import DataSource, DataSourceLicense

    created_licenses: Dict[str, Any] = {}

    for source_code, license_info in LICENSE_DATA.items():
        pattern = license_info["data_source_pattern"]

        # Find matching data source
        data_source = session.query(DataSource).filter(
            DataSource.name.like(f"%{pattern}%")
        ).first()

        if not data_source:
            # Data source not found - skip
            continue

        # Check if license already exists
        if skip_existing:
            existing = session.query(DataSourceLicense).filter(
                DataSourceLicense.data_source_id == data_source.id
            ).first()
            if existing:
                created_licenses[source_code] = existing
                continue

        # Create license record
        license_record = DataSourceLicense(
            data_source_id=data_source.id,
            license_type=license_info["license_type"],
            license_url=license_info["license_url"],
            attribution_required=license_info["attribution_required"],
            attribution_statement=license_info["attribution_statement"],
            commercial_use_allowed=license_info["commercial_use_allowed"],
            sharealike_required=license_info["sharealike_required"],
            additional_restrictions=license_info.get("additional_restrictions"),
            license_version=license_info.get("license_version"),
            effective_date=license_info.get("effective_date")
        )
        session.add(license_record)
        created_licenses[source_code] = license_record

    if created_licenses:
        session.commit()

    return created_licenses


def get_license_for_source(
    session: Session,
    source_name: str
) -> Optional[Any]:
    """
    Get the license for a data source by name.

    Args:
        session: SQLAlchemy database session
        source_name: Name or pattern to match data source

    Returns:
        DataSourceLicense object or None
    """
    from backend.models import DataSource, DataSourceLicense

    data_source = session.query(DataSource).filter(
        DataSource.name.like(f"%{source_name}%")
    ).first()

    if not data_source:
        return None

    return session.query(DataSourceLicense).filter(
        DataSourceLicense.data_source_id == data_source.id
    ).first()


def verify_license_compliance(
    session: Session,
    source_code: str
) -> Dict[str, Any]:
    """
    Get compliance status for a data source.

    Args:
        session: SQLAlchemy database session
        source_code: Source code (EPA, DEFRA, EXIOBASE)

    Returns:
        Dict with compliance status information
    """
    from backend.models import DataSource, DataSourceLicense

    license_info = LICENSE_DATA.get(source_code)
    if not license_info:
        return {"status": "unknown", "message": f"Unknown source code: {source_code}"}

    pattern = license_info["data_source_pattern"]
    data_source = session.query(DataSource).filter(
        DataSource.name.like(f"%{pattern}%")
    ).first()

    if not data_source:
        return {
            "status": "error",
            "message": f"Data source not found for pattern: {pattern}"
        }

    license_record = session.query(DataSourceLicense).filter(
        DataSourceLicense.data_source_id == data_source.id
    ).first()

    if not license_record:
        return {
            "status": "missing",
            "message": "License record not found - run seed_licenses()",
            "data_source_id": data_source.id,
            "data_source_name": data_source.name
        }

    return {
        "status": "compliant",
        "data_source_id": data_source.id,
        "data_source_name": data_source.name,
        "license_type": license_record.license_type,
        "attribution_required": license_record.attribution_required,
        "attribution_statement": license_record.attribution_statement,
        "commercial_use_allowed": license_record.commercial_use_allowed,
        "sharealike_required": license_record.sharealike_required
    }


def get_attribution_text(license_record) -> str:
    """
    Generate attribution text for display in UI.

    Args:
        license_record: DataSourceLicense object

    Returns:
        Attribution text string for display
    """
    if not license_record.attribution_required:
        return ""

    return license_record.attribution_statement or ""


def get_all_attributions(session: Session) -> List[Dict[str, Any]]:
    """
    Get attribution requirements for all data sources.

    Args:
        session: SQLAlchemy database session

    Returns:
        List of dicts with attribution info for each source
    """
    from backend.models import DataSource, DataSourceLicense

    attributions = []

    licenses = session.query(DataSourceLicense).join(DataSource).all()

    for license_record in licenses:
        data_source = license_record.data_source
        attributions.append({
            "source_name": data_source.name,
            "license_type": license_record.license_type,
            "attribution_required": license_record.attribution_required,
            "attribution_statement": license_record.attribution_statement or "",
            "license_url": license_record.license_url or "",
            "commercial_use_allowed": license_record.commercial_use_allowed,
            "sharealike_required": license_record.sharealike_required
        })

    return attributions
