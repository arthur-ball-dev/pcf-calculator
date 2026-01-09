"""
Proxy Factor Loader

TASK-DATA-P8-004: Emission Factor Mapping Infrastructure

Loads calculated proxy emission factors into database from CSV.
Uses EPA + DEFRA only (no EXIOBASE to avoid ShareAlike compliance concerns).

Proxy factors fill gaps where direct emission factors are not available:
- Batteries: Weighted average of materials and electricity
- Semiconductors: Materials + electricity premium
- Carbon Fiber: Aluminum factor with multiplier
- Agricultural inputs: Processing and transport factors

Each proxy includes:
- data_source: "PROXY"
- data_quality_rating: 0.5-0.7 (lower than direct factors)
- metadata: Derivation method and source factors

Usage:
    from backend.services.data_ingestion.proxy_factor_loader import (
        load_proxy_factors
    )

    # With synchronous session
    from backend.database.connection import get_sync_session

    with get_sync_session() as session:
        count = load_proxy_factors(session)
        print(f"Loaded {count} proxy factors")

    # Async version
    count = await load_proxy_factors_async(async_session)
"""

import csv
import logging
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EmissionFactor, DataSource


logger = logging.getLogger(__name__)

# Path to proxy factors CSV
PROXY_CSV_PATH = Path(__file__).parent.parent.parent / "data" / "proxy_emission_factors.csv"


def get_or_create_proxy_source(session: Session) -> DataSource:
    """
    Get or create the PROXY data source.

    Args:
        session: SQLAlchemy session

    Returns:
        DataSource for proxy factors
    """
    result = session.execute(
        select(DataSource).where(DataSource.name == "Calculated Proxy Factors")
    )
    proxy_source = result.scalar_one_or_none()

    if not proxy_source:
        proxy_source = DataSource(
            id=uuid4().hex,
            name="Calculated Proxy Factors",
            source_type="calculated",
            base_url=None,
            license_type="DERIVED",
            attribution_text="Proxy factors calculated from EPA and DEFRA data",
            allows_commercial_use=True,
            requires_attribution=True,
            requires_share_alike=False,
            is_active=True,
        )
        session.add(proxy_source)
        session.flush()
        logger.info("Created PROXY data source")

    return proxy_source


def parse_proxy_row(row: Dict[str, str], data_source_id: str) -> Dict[str, Any]:
    """
    Parse a row from proxy CSV into factor data.

    Args:
        row: CSV row as dict
        data_source_id: ID of PROXY data source

    Returns:
        Dict ready for EmissionFactor creation
    """
    return {
        "activity_name": row["activity_name"].strip(),
        "co2e_factor": Decimal(row["co2e_factor"]),
        "unit": row["unit"].strip(),
        "geography": row["geography"].strip(),
        "category": row["category"].strip() if row.get("category") else "material",
        "data_source": row["data_source"].strip(),
        "data_source_id": data_source_id,
        "data_quality_rating": Decimal(row["data_quality_rating"]),
        "is_active": True,
        "emission_metadata": {
            "derivation_method": row["derivation_method"].strip(),
            "source_factors": row["source_factors"].strip(),
        },
    }


def validate_source_factors(source_factors: str) -> bool:
    """
    Validate that source factors use only EPA and DEFRA.

    CRITICAL: No EXIOBASE to avoid ShareAlike compliance concerns.

    Args:
        source_factors: Semicolon-separated list of source references

    Returns:
        True if valid (EPA/DEFRA only), False if invalid
    """
    if not source_factors:
        return False

    sources = source_factors.split(";")
    for source in sources:
        source_clean = source.strip()
        if not source_clean:
            continue

        # Extract prefix (EPA:aluminum -> EPA)
        if ":" in source_clean:
            prefix = source_clean.split(":")[0].upper()
        else:
            prefix = source_clean.upper()

        # Only allow EPA and DEFRA
        if prefix not in ["EPA", "DEFRA"]:
            logger.error(f"Invalid source reference: {source_clean}")
            return False

    return True


def load_proxy_factors(session: Session) -> int:
    """
    Load proxy emission factors from CSV.

    Args:
        session: SQLAlchemy session

    Returns:
        Number of factors loaded

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If source factors contain EXIOBASE
    """
    if not PROXY_CSV_PATH.exists():
        logger.error(f"Proxy factors CSV not found: {PROXY_CSV_PATH}")
        raise FileNotFoundError(f"Proxy factors CSV not found: {PROXY_CSV_PATH}")

    # Get or create PROXY data source
    proxy_source = get_or_create_proxy_source(session)

    loaded = 0
    updated = 0
    skipped = 0

    with open(PROXY_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                # Validate source factors (EPA + DEFRA only)
                source_factors = row.get("source_factors", "")
                if not validate_source_factors(source_factors):
                    logger.warning(
                        f"Row {row_num}: Skipping {row['activity_name']} - "
                        f"invalid source factors: {source_factors}"
                    )
                    skipped += 1
                    continue

                # Parse row data
                factor_data = parse_proxy_row(row, proxy_source.id)

                # Check if already exists
                existing = session.execute(
                    select(EmissionFactor).where(
                        EmissionFactor.activity_name == factor_data["activity_name"],
                        EmissionFactor.data_source == "PROXY",
                    )
                ).scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.co2e_factor = factor_data["co2e_factor"]
                    existing.unit = factor_data["unit"]
                    existing.geography = factor_data["geography"]
                    existing.category = factor_data["category"]
                    existing.data_quality_rating = factor_data["data_quality_rating"]
                    existing.emission_metadata = factor_data["emission_metadata"]
                    existing.is_active = True
                    updated += 1
                else:
                    # Insert new
                    factor = EmissionFactor(
                        id=uuid4().hex,
                        **factor_data
                    )
                    session.add(factor)
                    loaded += 1

            except Exception as e:
                logger.error(f"Row {row_num}: Error processing {row.get('activity_name', 'unknown')}: {e}")
                skipped += 1

    session.commit()
    logger.info(f"Proxy factors: {loaded} loaded, {updated} updated, {skipped} skipped")

    return loaded + updated


async def get_or_create_proxy_source_async(session: AsyncSession) -> DataSource:
    """
    Get or create the PROXY data source (async version).

    Args:
        session: SQLAlchemy async session

    Returns:
        DataSource for proxy factors
    """
    result = await session.execute(
        select(DataSource).where(DataSource.name == "Calculated Proxy Factors")
    )
    proxy_source = result.scalar_one_or_none()

    if not proxy_source:
        proxy_source = DataSource(
            id=uuid4().hex,
            name="Calculated Proxy Factors",
            source_type="calculated",
            base_url=None,
            license_type="DERIVED",
            attribution_text="Proxy factors calculated from EPA and DEFRA data",
            allows_commercial_use=True,
            requires_attribution=True,
            requires_share_alike=False,
            is_active=True,
        )
        session.add(proxy_source)
        await session.flush()
        logger.info("Created PROXY data source")

    return proxy_source


async def load_proxy_factors_async(session: AsyncSession) -> int:
    """
    Load proxy emission factors from CSV (async version).

    Args:
        session: SQLAlchemy async session

    Returns:
        Number of factors loaded

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If source factors contain EXIOBASE
    """
    if not PROXY_CSV_PATH.exists():
        logger.error(f"Proxy factors CSV not found: {PROXY_CSV_PATH}")
        raise FileNotFoundError(f"Proxy factors CSV not found: {PROXY_CSV_PATH}")

    # Get or create PROXY data source
    proxy_source = await get_or_create_proxy_source_async(session)

    loaded = 0
    updated = 0
    skipped = 0

    with open(PROXY_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                # Validate source factors (EPA + DEFRA only)
                source_factors = row.get("source_factors", "")
                if not validate_source_factors(source_factors):
                    logger.warning(
                        f"Row {row_num}: Skipping {row['activity_name']} - "
                        f"invalid source factors: {source_factors}"
                    )
                    skipped += 1
                    continue

                # Parse row data
                factor_data = parse_proxy_row(row, proxy_source.id)

                # Check if already exists
                result = await session.execute(
                    select(EmissionFactor).where(
                        EmissionFactor.activity_name == factor_data["activity_name"],
                        EmissionFactor.data_source == "PROXY",
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.co2e_factor = factor_data["co2e_factor"]
                    existing.unit = factor_data["unit"]
                    existing.geography = factor_data["geography"]
                    existing.category = factor_data["category"]
                    existing.data_quality_rating = factor_data["data_quality_rating"]
                    existing.emission_metadata = factor_data["emission_metadata"]
                    existing.is_active = True
                    updated += 1
                else:
                    # Insert new
                    factor = EmissionFactor(
                        id=uuid4().hex,
                        **factor_data
                    )
                    session.add(factor)
                    loaded += 1

            except Exception as e:
                logger.error(f"Row {row_num}: Error processing {row.get('activity_name', 'unknown')}: {e}")
                skipped += 1

    await session.commit()
    logger.info(f"Proxy factors: {loaded} loaded, {updated} updated, {skipped} skipped")

    return loaded + updated


def get_proxy_factor_count() -> int:
    """
    Get the number of proxy factors in the CSV file.

    Returns:
        Number of rows in proxy_emission_factors.csv
    """
    if not PROXY_CSV_PATH.exists():
        return 0

    with open(PROXY_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


__all__ = [
    "load_proxy_factors",
    "load_proxy_factors_async",
    "get_or_create_proxy_source",
    "get_or_create_proxy_source_async",
    "validate_source_factors",
    "get_proxy_factor_count",
    "PROXY_CSV_PATH",
]


if __name__ == "__main__":
    # CLI entry point for loading proxy factors
    import sys

    try:
        from backend.database.connection import get_sync_session

        with get_sync_session() as session:
            count = load_proxy_factors(session)
            print(f"Successfully loaded {count} proxy factors")
            sys.exit(0)
    except ImportError:
        print("Error: Could not import database connection")
        print("Run from project root with: python -m backend.services.data_ingestion.proxy_factor_loader")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading proxy factors: {e}")
        sys.exit(1)
