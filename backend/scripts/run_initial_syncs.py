#!/usr/bin/env python3
"""
Initial Sync Script for External Data Connectors.

TASK-DATA-P8-003: Activate External Data Connectors (EPA/DEFRA)
TASK-DATA-P9: Modified to load from local files instead of downloading

This script runs the initial synchronization for external data sources:
- EPA GHG Emission Factors Hub
- DEFRA Conversion Factors

Expected Emission Factor Counts:
- EPA: 75-125 records
- DEFRA: 200-400 records
- Total: 275-525 records

IMPORTANT: This script now loads from local files in data/epa/ and data/defra/.
If files don't exist, run download_external_data.py first.

Usage:
    # Run all syncs (from local files)
    python backend/scripts/run_initial_syncs.py

    # Run specific source
    python backend/scripts/run_initial_syncs.py --source epa
    python backend/scripts/run_initial_syncs.py --source defra

    # Dry run (no database writes)
    python backend/scripts/run_initial_syncs.py --dry-run

    # Force download from web (ignore local files)
    python backend/scripts/run_initial_syncs.py --download

    # Limit records (for testing)
    python backend/scripts/run_initial_syncs.py --max-records 10
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings
from backend.models import DataSource, EmissionFactor
from backend.database.seeds.data_sources import seed_data_sources, verify_data_sources


# Data source names mapping
DATA_SOURCE_NAMES = {
    "epa": "EPA GHG Emission Factors Hub",
    "defra": "DEFRA Conversion Factors",
}

# Expected count ranges for validation
EXPECTED_COUNTS = {
    "epa": (75, 125),
    "defra": (200, 400),
}

# Local file paths (TASK-DATA-P9)
# These are used instead of downloading when files exist
LOCAL_FILES = {
    "epa_fuels": Path(__file__).parent.parent.parent / "data" / "epa" / "ghg-emission-factors-hub-2024.xlsx",
    "epa_egrid": Path(__file__).parent.parent.parent / "data" / "epa" / "egrid2022_data.xlsx",
    "defra": Path(__file__).parent.parent.parent / "data" / "defra" / "ghg-conversion-factors-2024.xlsx",
}


class SyncRunner:
    """Manages running sync operations for external data sources."""

    def __init__(
        self,
        dry_run: bool = False,
        max_records: int = None,
        verbose: bool = True,
        force_download: bool = False,
    ):
        """
        Initialize the sync runner.

        Args:
            dry_run: If True, don't write to database
            max_records: Limit records per source (for testing)
            verbose: Print progress messages
            force_download: If True, download from web instead of using local files
        """
        self.dry_run = dry_run
        self.max_records = max_records
        self.verbose = verbose
        self.force_download = force_download
        self.results = {}

    def log(self, message: str):
        """Print log message if verbose."""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def run_sync(
        self,
        source_key: str,
        session: AsyncSession
    ) -> dict:
        """
        Run sync for a specific data source.

        Args:
            source_key: Key for the data source (epa, defra)
            session: Async database session

        Returns:
            Dictionary with sync results
        """
        source_name = DATA_SOURCE_NAMES.get(source_key)
        if not source_name:
            raise ValueError(f"Unknown source key: {source_key}")

        self.log(f"Starting sync for {source_name}...")

        # Get data source from database
        result = await session.execute(
            select(DataSource).where(DataSource.name == source_name)
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            self.log(f"ERROR: Data source '{source_name}' not found in database")
            self.log("Run seed_data_sources() first to create data sources")
            return {
                "source": source_name,
                "status": "error",
                "message": "Data source not found",
            }

        if self.dry_run:
            self.log(f"DRY RUN: Would sync {source_name} (data_source_id: {data_source.id})")
            return {
                "source": source_name,
                "status": "dry_run",
                "message": "Dry run - no changes made",
            }

        # Import the appropriate ingestion class
        try:
            if source_key == "epa":
                from backend.services.data_ingestion.epa_ingestion import (
                    EPAEmissionFactorsIngestion
                )
                # EPA has multiple files - sync fuels and egrid
                total_result = {
                    "source": source_name,
                    "status": "completed",
                    "records_created": 0,
                    "records_updated": 0,
                    "records_failed": 0,
                }

                for file_key in ["fuels", "egrid"]:
                    self.log(f"  Syncing EPA {file_key}...")
                    ingestion = EPAEmissionFactorsIngestion(
                        db=session,
                        data_source_id=data_source.id,
                        file_key=file_key,
                        sync_type="initial"
                    )

                    # TASK-DATA-P9: Check for local file first
                    local_file_key = f"epa_{file_key}"
                    local_path = LOCAL_FILES.get(local_file_key)

                    if local_path and local_path.exists() and not self.force_download:
                        self.log(f"    Using local file: {local_path}")
                        with open(local_path, "rb") as f:
                            raw_data = f.read()
                        parsed_data = await ingestion.parse_data(raw_data)
                        transformed_data = await ingestion.transform_data(parsed_data)
                        result = await ingestion.load_data(transformed_data)
                    else:
                        if not self.force_download and local_path:
                            self.log(f"    Local file not found, downloading from web...")
                        result = await ingestion.execute_sync(max_records=self.max_records)

                    total_result["records_created"] += result.records_created
                    total_result["records_updated"] += result.records_updated
                    total_result["records_failed"] += result.records_failed

                return total_result

            elif source_key == "defra":
                from backend.services.data_ingestion.defra_ingestion import (
                    DEFRAEmissionFactorsIngestion
                )
                ingestion = DEFRAEmissionFactorsIngestion(
                    db=session,
                    data_source_id=data_source.id,
                    sync_type="initial"
                )

                # TASK-DATA-P9: Check for local file first
                local_path = LOCAL_FILES.get("defra")

                if local_path and local_path.exists() and not self.force_download:
                    self.log(f"  Using local file: {local_path}")
                    with open(local_path, "rb") as f:
                        raw_data = f.read()
                    parsed_data = await ingestion.parse_data(raw_data)
                    transformed_data = await ingestion.transform_data(parsed_data)
                    result = await ingestion.load_data(transformed_data)
                else:
                    if not self.force_download and local_path:
                        self.log(f"  Local file not found, downloading from web...")
                    result = await ingestion.execute_sync(max_records=self.max_records)

            else:
                raise ValueError(f"Unknown source key: {source_key}")

            return {
                "source": source_name,
                "status": result.status,
                "records_created": result.records_created,
                "records_updated": result.records_updated,
                "records_failed": result.records_failed,
                "sync_log_id": result.sync_log_id,
            }

        except Exception as e:
            self.log(f"ERROR syncing {source_name}: {str(e)}")
            return {
                "source": source_name,
                "status": "error",
                "message": str(e),
            }

    async def run_all_syncs(self, sources: list = None):
        """
        Run syncs for specified sources or all sources.

        Args:
            sources: List of source keys to sync (default: all)
        """
        if sources is None:
            sources = list(DATA_SOURCE_NAMES.keys())

        self.log("=" * 60)
        self.log("PCF Calculator - External Data Connector Initial Sync")
        self.log("=" * 60)

        if self.dry_run:
            self.log("MODE: DRY RUN (no database changes)")
        if self.max_records:
            self.log(f"LIMIT: {self.max_records} records per source")

        self.log("")

        # Create async database engine
        # Use the async_database_url property which handles driver conversion
        database_url = settings.async_database_url

        engine = create_async_engine(database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # First, ensure data sources exist
            self.log("Verifying data sources are seeded...")
            from sqlalchemy.orm import Session as SyncSession
            from sqlalchemy import create_engine as create_sync_engine

            sync_engine = create_sync_engine(settings.database_url, echo=False)
            with SyncSession(sync_engine) as sync_session:
                if not verify_data_sources(sync_session):
                    self.log("Seeding data sources...")
                    count = seed_data_sources(sync_session)
                    self.log(f"Created {count} data sources")
                else:
                    self.log("Data sources already exist")

            self.log("")

            # Run syncs for each source
            for source_key in sources:
                result = await self.run_sync(source_key, session)
                self.results[source_key] = result

                if result["status"] == "completed":
                    self.log(f"  Created: {result.get('records_created', 0)}")
                    self.log(f"  Updated: {result.get('records_updated', 0)}")
                    self.log(f"  Failed: {result.get('records_failed', 0)}")
                elif result["status"] == "error":
                    self.log(f"  Error: {result.get('message', 'Unknown error')}")

                self.log("")

        await engine.dispose()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print sync summary."""
        self.log("=" * 60)
        self.log("SYNC SUMMARY")
        self.log("=" * 60)

        total_created = 0
        total_updated = 0
        total_failed = 0
        all_successful = True

        for source_key, result in self.results.items():
            status = result["status"]
            source_name = DATA_SOURCE_NAMES.get(source_key, source_key)

            if status == "completed":
                created = result.get("records_created", 0)
                updated = result.get("records_updated", 0)
                failed = result.get("records_failed", 0)
                total_created += created
                total_updated += updated
                total_failed += failed

                # Check against expected counts
                expected_min, expected_max = EXPECTED_COUNTS.get(source_key, (0, float('inf')))
                count_ok = expected_min <= created <= expected_max
                status_str = "OK" if count_ok else "WARN"

                self.log(f"{source_name}: {created} created [{status_str}]")
                if not count_ok:
                    self.log(f"  Expected: {expected_min}-{expected_max} records")
            elif status == "dry_run":
                self.log(f"{source_name}: DRY RUN")
            else:
                all_successful = False
                self.log(f"{source_name}: FAILED - {result.get('message', 'Unknown error')}")

        self.log("-" * 60)
        self.log(f"Total Created: {total_created}")
        self.log(f"Total Updated: {total_updated}")
        self.log(f"Total Failed: {total_failed}")
        self.log("")

        # Check total against expected range
        expected_total_min = sum(EXPECTED_COUNTS[k][0] for k in self.results.keys() if k in EXPECTED_COUNTS)
        expected_total_max = sum(EXPECTED_COUNTS[k][1] for k in self.results.keys() if k in EXPECTED_COUNTS)

        if expected_total_min <= total_created <= expected_total_max:
            self.log(f"Total count {total_created} is within expected range ({expected_total_min}-{expected_total_max})")
        else:
            self.log(f"WARNING: Total count {total_created} outside expected range ({expected_total_min}-{expected_total_max})")

        if all_successful and total_failed == 0:
            self.log("")
            self.log("All syncs completed successfully!")
        else:
            self.log("")
            self.log("WARNING: Some syncs had issues. Check logs above.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run initial sync for external data connectors"
    )
    parser.add_argument(
        "--source",
        choices=["epa", "defra", "all"],
        default="all",
        help="Data source to sync (default: all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database, just show what would happen"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Force download from web instead of using local files"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Limit number of records per source (for testing)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    sources = None
    if args.source != "all":
        sources = [args.source]

    runner = SyncRunner(
        dry_run=args.dry_run,
        max_records=args.max_records,
        verbose=not args.quiet,
        force_download=args.download,
    )

    await runner.run_all_syncs(sources)


if __name__ == "__main__":
    asyncio.run(main())
