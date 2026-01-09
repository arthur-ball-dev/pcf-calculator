#!/usr/bin/env python3
"""
Verification Script for External Data Sync.

TASK-DATA-P8-003: Activate External Data Connectors (EPA/DEFRA/Exiobase)

This script verifies that the external data sync completed successfully by:
1. Checking emission factor counts by data source
2. Validating data quality (positive values, valid units)
3. Verifying sync logs exist and are successful
4. Checking for orphaned records
5. Verifying license compliance (Exiobase v3.8)

Expected Emission Factor Counts:
- EPA: 75-125 records
- DEFRA: 200-400 records
- EXIOBASE: 500-1000 records
- Total: 775-1525 records

Usage:
    # Full verification
    python backend/scripts/verify_external_sync.py

    # JSON output for automation
    python backend/scripts/verify_external_sync.py --json

    # Check specific source
    python backend/scripts/verify_external_sync.py --source epa
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models import DataSource, EmissionFactor, DataSyncLog


# Data source configuration
DATA_SOURCES = {
    "epa": {
        "name": "EPA GHG Emission Factors Hub",
        "expected_min": 75,
        "expected_max": 125,
        "geography": "US",
    },
    "defra": {
        "name": "DEFRA Conversion Factors",
        "expected_min": 200,
        "expected_max": 400,
        "geography": "GB",
    },
    "exiobase": {
        "name": "Exiobase",
        "expected_min": 500,
        "expected_max": 1000,
        "geography": None,  # Multiple geographies
    },
}


class SyncVerifier:
    """Verifies external data sync completion and data quality."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the verifier.

        Args:
            verbose: Print detailed output
        """
        self.verbose = verbose
        self.engine = create_engine(settings.DATABASE_URL, echo=False)
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "sources": {},
            "summary": {},
            "warnings": [],
            "errors": [],
        }

    def log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(message)

    def verify_all(self, sources: List[str] = None) -> Dict[str, Any]:
        """
        Run all verification checks.

        Args:
            sources: Specific sources to verify (default: all)

        Returns:
            Dictionary with verification results
        """
        if sources is None:
            sources = list(DATA_SOURCES.keys())

        self.log("=" * 60)
        self.log("PCF Calculator - External Sync Verification")
        self.log("=" * 60)
        self.log("")

        with Session(self.engine) as session:
            # Verify license compliance first
            self.verify_license_compliance()
            self.log("")

            # Verify each data source
            for source_key in sources:
                self.verify_source(session, source_key)
                self.log("")

            # Summary checks
            self.verify_no_orphaned_records(session)
            self.verify_data_quality(session)
            self.generate_summary(session)

        self.log("")
        self.print_final_status()

        return self.results

    def verify_license_compliance(self):
        """Verify Exiobase uses v3.8 for license compliance."""
        self.log("Checking license compliance...")

        try:
            from backend.services.data_ingestion.exiobase_ingestion import (
                ExiobaseEmissionFactorsIngestion
            )

            url = ExiobaseEmissionFactorsIngestion.ZENODO_URL

            if "5589597" in url:
                self.log("  [OK] Exiobase uses v3.8 (CC-BY-SA 4.0)")
                self.results["license_compliance"] = {
                    "exiobase_version": "3.8",
                    "license": "CC-BY-SA 4.0",
                    "commercial_use": True,
                    "status": "compliant",
                }
            elif "14614930" in url:
                self.log("  [ERROR] Exiobase uses v3.9 (CC-BY-NC-SA)")
                self.log("         Non-commercial restriction detected!")
                self.results["license_compliance"] = {
                    "exiobase_version": "3.9",
                    "license": "CC-BY-NC-SA",
                    "commercial_use": False,
                    "status": "non_compliant",
                }
                self.results["errors"].append(
                    "Exiobase v3.9 has NC license - cannot use commercially"
                )
            else:
                self.log(f"  [WARN] Unknown Exiobase URL: {url}")
                self.results["license_compliance"] = {
                    "status": "unknown",
                    "url": url,
                }
                self.results["warnings"].append(
                    f"Unknown Exiobase URL: {url}"
                )

        except ImportError as e:
            self.log(f"  [ERROR] Could not import Exiobase module: {e}")
            self.results["errors"].append(f"Could not import Exiobase module: {e}")

    def verify_source(self, session: Session, source_key: str):
        """
        Verify a specific data source.

        Args:
            session: Database session
            source_key: Key of source to verify (epa, defra, exiobase)
        """
        config = DATA_SOURCES.get(source_key)
        if not config:
            self.log(f"Unknown source: {source_key}")
            return

        source_name = config["name"]
        self.log(f"Verifying {source_name}...")

        result = {
            "name": source_name,
            "status": "unknown",
            "factor_count": 0,
            "expected_range": f"{config['expected_min']}-{config['expected_max']}",
            "sync_logs": [],
        }

        # Find data source
        data_source = session.execute(
            select(DataSource).where(DataSource.name == source_name)
        ).scalar_one_or_none()

        if not data_source:
            self.log(f"  [ERROR] Data source not found in database")
            result["status"] = "not_found"
            self.results["errors"].append(f"Data source '{source_name}' not found")
            self.results["sources"][source_key] = result
            return

        result["data_source_id"] = data_source.id

        # Count emission factors
        factor_count = session.execute(
            select(func.count(EmissionFactor.id)).where(
                EmissionFactor.data_source_id == data_source.id
            )
        ).scalar()

        result["factor_count"] = factor_count

        # Check against expected range
        if config["expected_min"] <= factor_count <= config["expected_max"]:
            self.log(f"  [OK] Factor count: {factor_count} (expected: {config['expected_min']}-{config['expected_max']})")
            result["status"] = "ok"
        elif factor_count == 0:
            self.log(f"  [ERROR] No emission factors found")
            result["status"] = "empty"
            self.results["errors"].append(f"{source_name} has no emission factors")
        elif factor_count < config["expected_min"]:
            self.log(f"  [WARN] Factor count low: {factor_count} (expected: {config['expected_min']}-{config['expected_max']})")
            result["status"] = "low"
            self.results["warnings"].append(
                f"{source_name} has fewer factors than expected: {factor_count}"
            )
        else:
            self.log(f"  [WARN] Factor count high: {factor_count} (expected: {config['expected_min']}-{config['expected_max']})")
            result["status"] = "high"
            self.results["warnings"].append(
                f"{source_name} has more factors than expected: {factor_count}"
            )

        # Check sync logs
        recent_sync = session.execute(
            select(DataSyncLog).where(
                DataSyncLog.data_source_id == data_source.id
            ).order_by(DataSyncLog.created_at.desc()).limit(1)
        ).scalar_one_or_none()

        if recent_sync:
            result["last_sync"] = {
                "id": recent_sync.id,
                "status": recent_sync.status,
                "sync_type": recent_sync.sync_type,
                "records_created": recent_sync.records_created,
                "records_updated": recent_sync.records_updated,
                "records_failed": recent_sync.records_failed,
                "completed_at": recent_sync.completed_at.isoformat() if recent_sync.completed_at else None,
            }

            if recent_sync.status == "completed":
                self.log(f"  [OK] Last sync completed at {recent_sync.completed_at}")
            else:
                self.log(f"  [WARN] Last sync status: {recent_sync.status}")
                self.results["warnings"].append(
                    f"{source_name} last sync status: {recent_sync.status}"
                )
        else:
            self.log(f"  [WARN] No sync logs found")
            result["last_sync"] = None
            self.results["warnings"].append(f"{source_name} has no sync logs")

        # Check geography if specified
        if config["geography"]:
            geo_count = session.execute(
                select(func.count(EmissionFactor.id)).where(
                    EmissionFactor.data_source_id == data_source.id,
                    EmissionFactor.geography == config["geography"]
                )
            ).scalar()

            if geo_count == factor_count:
                self.log(f"  [OK] All factors have geography '{config['geography']}'")
            else:
                self.log(f"  [WARN] {factor_count - geo_count} factors don't have expected geography")
                self.results["warnings"].append(
                    f"{source_name}: {factor_count - geo_count} factors missing expected geography"
                )

        self.results["sources"][source_key] = result

    def verify_no_orphaned_records(self, session: Session):
        """Check for emission factors without valid data source."""
        self.log("Checking for orphaned records...")

        orphaned_count = session.execute(text("""
            SELECT COUNT(*) FROM emission_factors ef
            LEFT JOIN data_sources ds ON ef.data_source_id = ds.id
            WHERE ds.id IS NULL
        """)).scalar()

        if orphaned_count == 0:
            self.log("  [OK] No orphaned emission factors found")
        else:
            self.log(f"  [ERROR] Found {orphaned_count} orphaned emission factors")
            self.results["errors"].append(
                f"{orphaned_count} orphaned emission factors found"
            )

        self.results["orphaned_records"] = orphaned_count

    def verify_data_quality(self, session: Session):
        """Verify data quality across all sources."""
        self.log("Checking data quality...")

        # Check for negative or zero CO2e factors
        invalid_factors = session.execute(text("""
            SELECT COUNT(*) FROM emission_factors
            WHERE co2e_factor <= 0
        """)).scalar()

        if invalid_factors == 0:
            self.log("  [OK] All factors have positive CO2e values")
        else:
            self.log(f"  [WARN] {invalid_factors} factors have non-positive CO2e values")
            self.results["warnings"].append(
                f"{invalid_factors} factors have non-positive CO2e values"
            )

        # Check for missing external_ids
        missing_external_id = session.execute(text("""
            SELECT COUNT(*) FROM emission_factors
            WHERE external_id IS NULL OR external_id = ''
        """)).scalar()

        if missing_external_id == 0:
            self.log("  [OK] All factors have external_id")
        else:
            self.log(f"  [WARN] {missing_external_id} factors missing external_id")
            self.results["warnings"].append(
                f"{missing_external_id} factors missing external_id"
            )

        # Check for missing units
        missing_unit = session.execute(text("""
            SELECT COUNT(*) FROM emission_factors
            WHERE unit IS NULL OR unit = ''
        """)).scalar()

        if missing_unit == 0:
            self.log("  [OK] All factors have unit specified")
        else:
            self.log(f"  [ERROR] {missing_unit} factors missing unit")
            self.results["errors"].append(
                f"{missing_unit} factors missing unit"
            )

        self.results["data_quality"] = {
            "invalid_factors": invalid_factors,
            "missing_external_id": missing_external_id,
            "missing_unit": missing_unit,
        }

    def generate_summary(self, session: Session):
        """Generate summary statistics."""
        self.log("-" * 60)
        self.log("SUMMARY")
        self.log("-" * 60)

        # Total counts by source
        total_factors = 0
        for source_key, result in self.results["sources"].items():
            count = result.get("factor_count", 0)
            total_factors += count
            self.log(f"  {result['name']}: {count} factors")

        self.log(f"  Total: {total_factors} emission factors")
        self.log("")

        # Expected vs actual
        expected_min = sum(
            DATA_SOURCES[k]["expected_min"]
            for k in self.results["sources"].keys()
        )
        expected_max = sum(
            DATA_SOURCES[k]["expected_max"]
            for k in self.results["sources"].keys()
        )

        if expected_min <= total_factors <= expected_max:
            self.log(f"  [OK] Total within expected range ({expected_min}-{expected_max})")
        else:
            self.log(f"  [WARN] Total outside expected range ({expected_min}-{expected_max})")
            self.results["warnings"].append(
                f"Total factor count {total_factors} outside expected range"
            )

        self.results["summary"] = {
            "total_factors": total_factors,
            "expected_range": f"{expected_min}-{expected_max}",
            "warning_count": len(self.results["warnings"]),
            "error_count": len(self.results["errors"]),
        }

    def print_final_status(self):
        """Print final verification status."""
        self.log("=" * 60)

        error_count = len(self.results["errors"])
        warning_count = len(self.results["warnings"])

        if error_count == 0 and warning_count == 0:
            self.results["status"] = "passed"
            self.log("VERIFICATION PASSED - All checks OK")
        elif error_count == 0:
            self.results["status"] = "passed_with_warnings"
            self.log(f"VERIFICATION PASSED with {warning_count} warning(s)")
        else:
            self.results["status"] = "failed"
            self.log(f"VERIFICATION FAILED - {error_count} error(s), {warning_count} warning(s)")

        if warning_count > 0:
            self.log("")
            self.log("Warnings:")
            for warning in self.results["warnings"]:
                self.log(f"  - {warning}")

        if error_count > 0:
            self.log("")
            self.log("Errors:")
            for error in self.results["errors"]:
                self.log(f"  - {error}")

        self.log("=" * 60)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify external data sync completion"
    )
    parser.add_argument(
        "--source",
        choices=["epa", "defra", "exiobase", "all"],
        default="all",
        help="Data source to verify (default: all)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output JSON, suppress other output"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    sources = None
    if args.source != "all":
        sources = [args.source]

    verifier = SyncVerifier(verbose=not args.quiet)
    results = verifier.verify_all(sources)

    if args.json:
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    if results["status"] == "failed":
        sys.exit(1)
    elif results["status"] == "passed_with_warnings":
        sys.exit(0)  # Warnings are not failures
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
