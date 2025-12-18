"""
Seed data for data_sources table.

TASK-DB-P5-002: Extended Database Schema
TASK-DATA-P7-001: Seed Data Sources Table

Initial data sources for emission factors:
- EPA GHG Emission Factors Hub
- DEFRA Conversion Factors
- Exiobase

Usage:
    from backend.database.seeds.data_sources import seed_data_sources
    from backend.database.connection import db_context

    with db_context() as session:
        seed_data_sources(session)
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session


# Initial data sources for emission factors with license/attribution info
SEED_DATA_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "EPA GHG Emission Factors Hub",
        "source_type": "file",
        "base_url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        "api_key_env_var": None,
        "sync_frequency": "biweekly",
        "is_active": True,
        # License: Public Domain (US Federal Government)
        "license_type": "Public Domain",
        "license_url": "https://www.epa.gov/web-policies-and-procedures/epa-disclaimers",
        "attribution_text": "Data source: U.S. Environmental Protection Agency (EPA) GHG Emission Factors Hub",
        "attribution_url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        "allows_commercial_use": True,
        "requires_attribution": False,
        "requires_share_alike": False,
    },
    {
        "name": "DEFRA Conversion Factors",
        "source_type": "file",
        "base_url": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors",
        "api_key_env_var": None,
        "sync_frequency": "biweekly",
        "is_active": True,
        # License: Open Government Licence v3.0 (Crown Copyright)
        "license_type": "Open Government Licence v3.0",
        "license_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "attribution_text": "Contains public sector information licensed under the Open Government Licence v3.0. Source: UK Department for Energy Security and Net Zero (DESNZ) / DEFRA Greenhouse Gas Conversion Factors.",
        "attribution_url": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024",
        "allows_commercial_use": True,
        "requires_attribution": True,
        "requires_share_alike": False,
    },
    {
        "name": "Exiobase",
        "source_type": "file",
        "base_url": "https://zenodo.org/record/5589597",
        "api_key_env_var": None,
        "sync_frequency": "monthly",
        "is_active": True,
        # License: CC-BY-SA-4.0 (Zenodo version)
        "license_type": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "attribution_text": "EXIOBASE 3 data is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). Credit: EXIOBASE Consortium.",
        "attribution_url": "https://zenodo.org/records/5589597",
        "allows_commercial_use": True,
        "requires_attribution": True,
        "requires_share_alike": True,
    },
]

# Expected data source names for verification
EXPECTED_DATA_SOURCE_NAMES = {
    "EPA GHG Emission Factors Hub",
    "DEFRA Conversion Factors",
    "Exiobase",
}


def seed_data_sources(session: Session, skip_existing: bool = True) -> int:
    """
    Seed the data_sources table with initial data.

    Args:
        session: SQLAlchemy database session
        skip_existing: If True, skip data sources that already exist by name

    Returns:
        Number of data sources created

    Example:
        from backend.database.connection import db_context
        from backend.database.seeds.data_sources import seed_data_sources

        with db_context() as session:
            count = seed_data_sources(session)
            print(f"Created {count} data sources")
    """
    from backend.models import DataSource

    created_count = 0

    for source_data in SEED_DATA_SOURCES:
        # Check if data source already exists
        if skip_existing:
            existing = session.query(DataSource).filter(
                DataSource.name == source_data["name"]
            ).first()
            if existing:
                continue

        # Create new data source
        data_source = DataSource(
            name=source_data["name"],
            source_type=source_data["source_type"],
            base_url=source_data.get("base_url"),
            api_key_env_var=source_data.get("api_key_env_var"),
            sync_frequency=source_data.get("sync_frequency", "biweekly"),
            is_active=source_data.get("is_active", True),
            # License and attribution fields
            license_type=source_data.get("license_type"),
            license_url=source_data.get("license_url"),
            attribution_text=source_data.get("attribution_text"),
            attribution_url=source_data.get("attribution_url"),
            allows_commercial_use=source_data.get("allows_commercial_use", True),
            requires_attribution=source_data.get("requires_attribution", False),
            requires_share_alike=source_data.get("requires_share_alike", False),
        )
        session.add(data_source)
        created_count += 1

    if created_count > 0:
        session.commit()

    return created_count


def get_data_source_by_name(session: Session, name: str):
    """
    Get a data source by name.

    Args:
        session: SQLAlchemy database session
        name: Data source name

    Returns:
        DataSource object or None
    """
    from backend.models import DataSource

    return session.query(DataSource).filter(
        DataSource.name == name
    ).first()


def update_data_source_attributions(session: Session) -> int:
    """
    Update existing data sources with license and attribution information.

    Call this after running the migration to populate attribution fields
    for data sources that were created before the migration.

    Args:
        session: SQLAlchemy database session

    Returns:
        Number of data sources updated
    """
    from backend.models import DataSource

    updated_count = 0

    for source_data in SEED_DATA_SOURCES:
        existing = session.query(DataSource).filter(
            DataSource.name == source_data["name"]
        ).first()

        if existing:
            # Update license and attribution fields
            existing.license_type = source_data.get("license_type")
            existing.license_url = source_data.get("license_url")
            existing.attribution_text = source_data.get("attribution_text")
            existing.attribution_url = source_data.get("attribution_url")
            existing.allows_commercial_use = source_data.get("allows_commercial_use", True)
            existing.requires_attribution = source_data.get("requires_attribution", False)
            existing.requires_share_alike = source_data.get("requires_share_alike", False)
            updated_count += 1

    if updated_count > 0:
        session.commit()

    return updated_count


def verify_data_sources(session: Session) -> bool:
    """
    Verify that all expected data sources are present in the database.

    Checks that EPA, DEFRA, and Exiobase data sources all exist.

    Args:
        session: SQLAlchemy database session

    Returns:
        True if all expected data sources are present, False otherwise

    Example:
        from backend.database.connection import db_context
        from backend.database.seeds.data_sources import verify_data_sources

        with db_context() as session:
            if verify_data_sources(session):
                print("All data sources are seeded")
            else:
                print("Missing data sources - run seed_data_sources()")
    """
    from backend.models import DataSource

    sources = session.query(DataSource).all()
    actual_names = {s.name for s in sources}

    return EXPECTED_DATA_SOURCE_NAMES.issubset(actual_names)
