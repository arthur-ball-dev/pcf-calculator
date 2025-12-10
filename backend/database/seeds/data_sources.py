"""
Seed data for data_sources table.

TASK-DB-P5-002: Extended Database Schema

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


# Initial data sources for emission factors
SEED_DATA_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "EPA GHG Emission Factors Hub",
        "source_type": "file",
        "base_url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        "api_key_env_var": None,
        "sync_frequency": "biweekly",
        "is_active": True,
    },
    {
        "name": "DEFRA Conversion Factors",
        "source_type": "file",
        "base_url": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors",
        "api_key_env_var": None,
        "sync_frequency": "biweekly",
        "is_active": True,
    },
    {
        "name": "Exiobase",
        "source_type": "file",
        "base_url": "https://zenodo.org/record/5589597",
        "api_key_env_var": None,
        "sync_frequency": "monthly",
        "is_active": True,
    },
]


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
