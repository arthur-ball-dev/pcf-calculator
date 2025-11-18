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

TASK-CALC-002: Sync Emission Factors to Brightway2
"""

import brightway2 as bw
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default CO2 biosphere flow to use for emissions
# Using "Carbon dioxide, fossil" from biosphere3
DEFAULT_CO2_FLOW_CODE = "349b29d1-3e58-4c66-98b9-9d1a076efd2e"


def sync_emission_factors(
    db_session: Optional[Session] = None,
    validate_biosphere: bool = False
) -> Dict[str, Any]:
    """
    Sync emission factors from SQLite database to Brightway2.

    Reads all emission factors from the SQLite emission_factors table
    and creates corresponding activities in Brightway2 "pcf_emission_factors"
    database. Each activity has a biosphere exchange representing the CO2e
    emission factor.

    The sync is idempotent - running multiple times will not create duplicates.
    Instead, the existing database is cleared and recreated with current data.

    Args:
        db_session: SQLAlchemy session for database access.
                   If None, creates a new session automatically.
        validate_biosphere: If True, raises error if biosphere3 database
                           is not available. Default False.

    Returns:
        Dictionary with sync statistics:
        {
            "synced_count": int  # Number of emission factors synced
        }

    Raises:
        KeyError: If validate_biosphere=True and biosphere3 not available
        Exception: If Brightway2 project not initialized

    Example:
        >>> from backend.calculator.emission_factor_sync import sync_emission_factors
        >>> result = sync_emission_factors()
        >>> print(f"Synced {result['synced_count']} emission factors")
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
            return _sync_emission_factors_impl(session)
    else:
        return _sync_emission_factors_impl(db_session)


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
    from sqlalchemy import text

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
