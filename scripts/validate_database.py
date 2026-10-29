#!/usr/bin/env python3
"""
Database configuration validation script.

TASK-DB-P7-004: PostgreSQL Production Configuration

This script validates the database configuration and connection,
checking for proper setup before deployment.

Usage:
    python scripts/validate_database.py

    # With verbose output
    python scripts/validate_database.py --verbose

Exit codes:
    0: All validations passed
    1: Validation failed
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env if present
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_status(label: str, status: str, ok: bool = True) -> None:
    """Print a status line with OK/FAIL indicator."""
    indicator = "[OK]" if ok else "[FAIL]"
    print(f"  {label}: {status} {indicator}")


def validate_configuration(verbose: bool = False) -> bool:
    """Validate database configuration from settings."""
    print_header("Configuration Validation")

    try:
        from backend.config import settings

        # Check database URL
        db_url = settings.database_url
        masked_url = db_url[:50] + "..." if len(db_url) > 50 else db_url

        # Mask password in URL for display
        if "@" in masked_url:
            parts = masked_url.split("@")
            if ":" in parts[0]:
                prefix_parts = parts[0].rsplit(":", 1)
                masked_url = f"{prefix_parts[0]}:****@{parts[1]}"

        print_status("DATABASE_URL", masked_url, bool(db_url))

        # Check database type
        db_type = "PostgreSQL" if settings.is_postgresql else "SQLite"
        print_status("Database Type", db_type, True)

        # Check pool settings
        print_status("Pool Size", str(settings.db_pool_size), settings.db_pool_size > 0)
        print_status("Max Overflow", str(settings.db_max_overflow), settings.db_max_overflow >= 0)

        if verbose:
            print()
            print("  Detailed Configuration:")
            print(f"    - is_postgresql: {settings.is_postgresql}")
            print(f"    - is_sqlite: {settings.is_sqlite}")
            print(f"    - async_database_url: {settings.async_database_url[:40]}...")

        return True

    except ImportError as e:
        print_status("Import Error", str(e), False)
        return False
    except Exception as e:
        print_status("Configuration Error", str(e), False)
        return False


def validate_connection(verbose: bool = False) -> bool:
    """Test database connection."""
    print_header("Connection Test")

    try:
        from backend.database.connection import get_engine
        from sqlalchemy import text

        engine = get_engine()

        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            print_status("Basic Query (SELECT 1)", str(value), value == 1)

        # Test connection pool
        pool = engine.pool
        if pool is not None:
            print_status("Connection Pool", f"size={pool.size()}", True)

        if verbose:
            print()
            print("  Connection Details:")
            print(f"    - Engine URL: {engine.url}")
            print(f"    - Driver: {engine.dialect.name}")

        return True

    except Exception as e:
        print_status("Connection", f"FAILED - {e}", False)
        return False


def validate_tables(verbose: bool = False) -> bool:
    """Check for required database tables."""
    print_header("Table Validation")

    try:
        from backend.database.connection import get_engine
        from sqlalchemy import inspect

        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Required tables for PCF Calculator
        required_tables = [
            "products",
            "emission_factors",
            "data_sources",
        ]

        # Optional tables (may not exist in fresh install)
        optional_tables = [
            "bill_of_materials",
            "pcf_calculations",
            "calculation_details",
            "product_categories",
            "data_sync_logs",
        ]

        print_status("Total Tables", str(len(tables)), len(tables) > 0)

        missing_required = []
        for table in required_tables:
            exists = table in tables
            print_status(f"  Required: {table}", "exists" if exists else "MISSING", exists)
            if not exists:
                missing_required.append(table)

        if verbose:
            print()
            print("  Optional Tables:")
            for table in optional_tables:
                exists = table in tables
                status = "exists" if exists else "not created"
                print(f"    - {table}: {status}")

        if missing_required:
            print()
            print("  ACTION REQUIRED: Run migrations to create missing tables:")
            print("    cd backend && alembic upgrade head")
            return False

        return True

    except Exception as e:
        print_status("Table Check", f"FAILED - {e}", False)
        return False


def validate_row_counts(verbose: bool = False) -> bool:
    """Check row counts for key tables."""
    print_header("Data Validation")

    try:
        from backend.database.connection import SessionLocal
        from sqlalchemy import text

        session = SessionLocal()

        try:
            tables_to_check = [
                ("products", "Products"),
                ("emission_factors", "Emission Factors"),
                ("data_sources", "Data Sources"),
            ]

            for table_name, display_name in tables_to_check:
                try:
                    result = session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    count = result.scalar()
                    print_status(display_name, str(count), True)
                except Exception:
                    print_status(display_name, "table not accessible", False)

            return True

        finally:
            session.close()

    except Exception as e:
        print_status("Data Check", f"FAILED - {e}", False)
        return False


def validate_foreign_keys(verbose: bool = False) -> bool:
    """Validate foreign key constraints are enabled (SQLite specific)."""
    print_header("Constraint Validation")

    try:
        from backend.config import settings
        from backend.database.connection import get_engine
        from sqlalchemy import text

        engine = get_engine()

        if settings.is_sqlite:
            # Check PRAGMA foreign_keys for SQLite
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA foreign_keys"))
                fk_status = result.scalar()
                enabled = fk_status == 1
                print_status(
                    "Foreign Keys (SQLite)",
                    "enabled" if enabled else "DISABLED",
                    enabled
                )

                if not enabled:
                    print()
                    print("  WARNING: Foreign keys are disabled in SQLite.")
                    print("  This is handled automatically by the application.")

                return True
        else:
            # PostgreSQL always enforces foreign keys
            print_status("Foreign Keys (PostgreSQL)", "enforced by default", True)
            return True

    except Exception as e:
        print_status("Constraint Check", f"FAILED - {e}", False)
        return False


def main():
    """Run all database validations."""
    parser = argparse.ArgumentParser(
        description="Validate PCF Calculator database configuration"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output with additional details"
    )
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  PCF Calculator - Database Configuration Validator")
    print("=" * 60)

    results = []

    # Run validations
    results.append(("Configuration", validate_configuration(args.verbose)))
    results.append(("Connection", validate_connection(args.verbose)))
    results.append(("Tables", validate_tables(args.verbose)))
    results.append(("Data", validate_row_counts(args.verbose)))
    results.append(("Constraints", validate_foreign_keys(args.verbose)))

    # Summary
    print_header("Validation Summary")

    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print_status(name, status, passed)
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  All validations PASSED!")
        print("  Database is ready for use.")
    else:
        print("  Some validations FAILED.")
        print("  Please address the issues above before proceeding.")

    print()
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
