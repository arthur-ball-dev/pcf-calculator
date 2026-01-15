"""
Emission Factor Sync Module for Brightway2 Integration

This module syncs emission factors from SQLite database to Brightway2
"pcf_emission_factors" database with proper CO2e biosphere exchanges.

Features:
- Syncs all emission factors from SQLite to Brightway2
- Creates proper biosphere exchanges for CO2e
- Idempotent (safe to run multiple times)
- Updates existing factors when database changes
- Error handling for missing dependencies
- Retry logic for SQLite database lock errors (TASK-BE-P9-010)
- Optional skip_if_synced flag for startup optimization

TASK-CALC-002: Sync Emission Factors to Brightway2
TASK-BE-P9-010: Fix emission factor sync failures due to database locks
"""

import time
import brightway2 as bw
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default CO2 biosphere flow to use for emissions
# Using "Carbon dioxide, fossil" from biosphere3
DEFAULT_CO2_FLOW_CODE = "349b29d1-3e58-4c66-98b9-9d1a076efd2e"

# Retry configuration for SQLite lock errors (TASK-BE-P9-010)
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 0.5  # seconds
MAX_RETRY_DELAY = 10.0  # seconds


def is_sync_needed(db_session: Session) -> bool:
    """
    Check if emission factor sync is needed.

    Compares the count of emission factors in the PostgreSQL/SQLite database
    with the count in Brightway2. Also checks for empty Brightway2 database.

    Note: This only checks counts, not whether individual values have changed.
    For detecting content changes, use force=True on sync_emission_factors().

    Args:
        db_session: SQLAlchemy session for database access

    Returns:
        True if sync is needed (Brightway2 empty or counts differ),
        False if counts match (data may or may not be stale)

    TASK-BE-P9-010: Added to optimize sync by skipping when unnecessary
    """
    from backend.models import EmissionFactor

    # Count emission factors in SQL database
    sql_count = db_session.query(EmissionFactor).count()

    # Check Brightway2 database
    if "pcf_calculator" not in bw.projects:
        logger.debug("Sync needed: Brightway2 project does not exist")
        return True

    bw.projects.set_current("pcf_calculator")

    if "pcf_emission_factors" not in bw.databases:
        logger.debug("Sync needed: pcf_emission_factors database does not exist")
        return True

    ef_db = bw.Database("pcf_emission_factors")
    bw_count = len(ef_db)

    if bw_count == 0 and sql_count > 0:
        logger.debug(f"Sync needed: Brightway2 database empty but SQL has {sql_count} factors")
        return True

    if bw_count != sql_count:
        logger.debug(f"Sync needed: Count mismatch - SQL={sql_count}, BW2={bw_count}")
        return True

    logger.debug(f"Sync not needed: Both databases have {sql_count} emission factors")
    return False


def sync_emission_factors(
    db_session: Optional[Session] = None,
    validate_biosphere: bool = False,
    skip_if_synced: bool = False,
    max_retries: int = MAX_RETRIES,
) -> Dict[str, Any]:
    """
    Sync emission factors from SQLite database to Brightway2.

    Reads all emission factors from the SQLite emission_factors table
    and creates corresponding activities in Brightway2 "pcf_emission_factors"
    database. Each activity has a biosphere exchange representing the CO2e
    emission factor.

    The sync is idempotent - running multiple times will not create duplicates.
    Instead, the existing database is cleared and recreated with current data.

    Includes retry logic with exponential backoff for SQLite lock errors
    (TASK-BE-P9-010).

    Args:
        db_session: SQLAlchemy session for database access.
                   If None, creates a new session automatically.
        validate_biosphere: If True, raises error if biosphere3 database
                           is not available. Default False.
        skip_if_synced: If True, skip sync when Brightway2 already has
                        emission factors with matching count. Default False.
                        This is useful for startup optimization but should NOT
                        be used when expecting data updates to be reflected.
        max_retries: Maximum number of retries for database lock errors.
                    Default 5.

    Returns:
        Dictionary with sync statistics:
        {
            "synced_count": int,  # Number of emission factors synced
            "skipped": bool       # True if sync was skipped (skip_if_synced=True and data present)
        }

    Raises:
        KeyError: If validate_biosphere=True and biosphere3 not available
        Exception: If Brightway2 project not initialized
        Exception: If database lock persists after max retries

    Example:
        >>> from backend.calculator.emission_factor_sync import sync_emission_factors
        >>> result = sync_emission_factors()
        >>> print(f"Synced {result['synced_count']} emission factors")

    Example (startup optimization):
        >>> # Skip sync if already populated (for faster startup)
        >>> result = sync_emission_factors(skip_if_synced=True)
        >>> if result.get('skipped'):
        ...     print("Using existing Brightway2 data")
    """
    # Set current Brightway2 project
    if "pcf_calculator" not in bw.projects:
        raise Exception(
            "Brightway2 project 'pcf_calculator' not found. "
            "Run initialize_brightway() first (TASK-CALC-001)."
        )

    bw.projects.set_current("pcf_calculator")

    # Validate biosphere3 if requested
    if validate_biosphere:
        if "biosphere3" not in bw.databases:
            raise KeyError(
                "biosphere3 database not found. "
                "Run initialize_brightway() to install biosphere3."
            )

    # Get database session if not provided
    if db_session is None:
        from backend.database.connection import db_context

        with db_context() as session:
            return _sync_with_retry(session, skip_if_synced, max_retries)
    else:
        return _sync_with_retry(db_session, skip_if_synced, max_retries)


def _sync_with_retry(
    db_session: Session,
    skip_if_synced: bool,
    max_retries: int,
) -> Dict[str, Any]:
    """
    Perform sync with retry logic for database lock errors.

    Uses exponential backoff with jitter for retries.

    Args:
        db_session: Active SQLAlchemy session
        skip_if_synced: If True, skip sync when counts match
        max_retries: Maximum number of retries

    Returns:
        Dictionary with sync statistics

    TASK-BE-P9-010: Added retry logic for robustness
    """
    import random

    # Check if sync should be skipped (optimization)
    if skip_if_synced and not is_sync_needed(db_session):
        bw.projects.set_current("pcf_calculator")
        ef_db = bw.Database("pcf_emission_factors")
        count = len(ef_db)
        logger.info(f"Sync skipped: Brightway2 already has {count} emission factors")
        return {"synced_count": count, "skipped": True}

    last_exception = None
    retry_delay = INITIAL_RETRY_DELAY

    for attempt in range(max_retries):
        try:
            result = _sync_emission_factors_impl(db_session)
            result["skipped"] = False
            return result
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's a database lock error
            if "database is locked" in error_msg or "locked" in error_msg:
                last_exception = e
                if attempt < max_retries - 1:
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0, retry_delay * 0.5)
                    sleep_time = min(retry_delay + jitter, MAX_RETRY_DELAY)
                    logger.warning(
                        f"Database locked during sync (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Database locked after {max_retries} attempts. "
                        f"Last error: {e}"
                    )
            else:
                # Non-lock error, raise immediately
                raise

    # If we get here, all retries failed
    raise Exception(
        f"Failed to sync emission factors after {max_retries} attempts. "
        f"Database appears to be locked by another process. "
        f"Original error: {last_exception}"
    )


def _sync_emission_factors_impl(db_session: Session) -> Dict[str, Any]:
    """
    Internal implementation of emission factor sync.

    Separated from main function to handle session management cleanly.

    Args:
        db_session: Active SQLAlchemy session

    Returns:
        Dictionary with sync statistics
    """
    from backend.models import EmissionFactor

    # Query all emission factors from database
    factors = db_session.query(EmissionFactor).all()

    logger.info(f"Found {len(factors)} emission factors in database")

    # Clear and recreate pcf_emission_factors database
    # This ensures idempotency - no duplicates on re-run
    if "pcf_emission_factors" in bw.databases:
        ef_db = bw.Database("pcf_emission_factors")
        ef_db.delete(warn=False)  # Suppress deprecation warning
        logger.info("Cleared existing pcf_emission_factors database")

    ef_db = bw.Database("pcf_emission_factors")

    # Build activity data for Brightway2
    data = {}

    for factor in factors:
        # Use activity_name as the code (unique identifier)
        code = factor.activity_name

        # Create activity with biosphere exchange
        activity_data = {
            "name": factor.activity_name,
            "unit": factor.unit,
            "type": "process",
            "location": factor.geography or "GLO",
            "categories": ("emission_factor",),
            "exchanges": [
                {
                    # Production exchange (self-reference)
                    "input": ("pcf_emission_factors", code),
                    "amount": 1.0,
                    "unit": factor.unit,
                    "type": "production",
                },
                {
                    # CO2e biosphere exchange
                    # Uses "Carbon dioxide, fossil" flow from biosphere3
                    "input": ("biosphere3", DEFAULT_CO2_FLOW_CODE),
                    "amount": float(factor.co2e_factor),
                    "unit": "kg",
                    "type": "biosphere",
                    "name": "Carbon dioxide, fossil",
                },
            ],
        }

        # Store in data dictionary with database key
        data[(ef_db.name, code)] = activity_data

    # Write all activities to Brightway2 database
    if data:
        ef_db.write(data)
        logger.info(f"Synced {len(factors)} emission factors to Brightway2")
    else:
        # Handle empty database case
        ef_db.write({})
        logger.info("No emission factors to sync (empty database)")

    return {
        "synced_count": len(factors)
    }


def get_emission_factor_activity(activity_name: str) -> Optional[Any]:
    """
    Retrieve an emission factor activity from Brightway2.

    Helper function to get activities by name after sync.

    Args:
        activity_name: Name of the emission factor activity

    Returns:
        Brightway2 Activity object, or None if not found

    Example:
        >>> cotton = get_emission_factor_activity("cotton")
        >>> if cotton:
        ...     print(f"Cotton CO2e: {list(cotton.exchanges())[0]['amount']}")
    """
    bw.projects.set_current("pcf_calculator")

    if "pcf_emission_factors" not in bw.databases:
        logger.warning("pcf_emission_factors database not found")
        return None

    ef_db = bw.Database("pcf_emission_factors")

    try:
        return ef_db.get(activity_name)
    except Exception as e:
        logger.warning(f"Activity '{activity_name}' not found: {e}")
        return None


def list_synced_emission_factors() -> list[str]:
    """
    List all synced emission factor names.

    Returns:
        List of activity names in pcf_emission_factors database

    Example:
        >>> factors = list_synced_emission_factors()
        >>> print(f"Synced factors: {', '.join(factors)}")
    """
    bw.projects.set_current("pcf_calculator")

    if "pcf_emission_factors" not in bw.databases:
        return []

    ef_db = bw.Database("pcf_emission_factors")
    return [activity["name"] for activity in ef_db]
