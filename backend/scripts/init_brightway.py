#!/usr/bin/env python3
"""
Initialize Brightway2 for PCF Calculations

This script must run after database migrations and seeding.
It initializes the Brightway2 project and syncs emission factors.

Usage:
    python backend/scripts/init_brightway.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from backend.calculator.brightway_setup import initialize_brightway
from backend.calculator.emission_factor_sync import sync_emission_factors
from backend.database.connection import db_context

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize Brightway2 and sync emission factors"""
    try:
        logger.info("=" * 60)
        logger.info("BRIGHTWAY2 INITIALIZATION")
        logger.info("=" * 60)

        # Step 1: Initialize Brightway2 project
        logger.info("Step 1: Initializing Brightway2 project...")
        initialize_brightway()
        logger.info("✓ Brightway2 project initialized")

        # Step 2: Sync emission factors from SQLite to Brightway2
        logger.info("Step 2: Syncing emission factors to Brightway2...")
        with db_context() as session:
            result = sync_emission_factors(db_session=session)
            logger.info(f"✓ Synced {result['synced_count']} emission factors")

        logger.info("=" * 60)
        logger.info("BRIGHTWAY2 INITIALIZATION COMPLETE")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Brightway2 initialization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
