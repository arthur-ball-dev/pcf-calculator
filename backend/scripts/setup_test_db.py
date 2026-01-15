#!/usr/bin/env python3
"""
E2E Test Database Setup Script

TASK-DB-P9-007: Setup Dedicated PostgreSQL Test Database for E2E Tests

This script:
1. Creates pcf_calculator_test database (if not exists)
2. Runs Alembic migrations
3. Seeds required data:
   - Data sources (EPA, DEFRA)
   - Data source licenses
   - E2E test user
   - Sample products for testing

Usage:
    # From project root with venv activated
    python backend/scripts/setup_test_db.py

    # Or with explicit database URL
    TEST_DATABASE_URL=postgresql://... python backend/scripts/setup_test_db.py

    # Reset and recreate database
    python backend/scripts/setup_test_db.py --reset

    # Verify only (no changes)
    python backend/scripts/setup_test_db.py --verify-only

    # Skip data seeding
    python backend/scripts/setup_test_db.py --skip-seed

Environment Variables:
    TEST_DATABASE_URL: Override default test database URL
    SKIP_MIGRATIONS: Set to '1' to skip Alembic migrations
    SKIP_SEED: Set to '1' to skip data seeding

Exit Codes:
    0: Success
    1: Database connection failed
    2: Migration failed
    3: Seeding failed
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse, unquote

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default test database URL (matches docker-compose defaults)
# Use postgresql+psycopg for psycopg3 driver (not psycopg2)
DEFAULT_TEST_DB_URL = (
    "postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test"
)


def get_test_database_url() -> str:
    """
    Get the test database URL from environment or default.

    Returns:
        str: PostgreSQL connection URL for test database
    """
    return os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


def parse_database_url(url: str) -> Dict[str, Any]:
    """
    Parse a PostgreSQL database URL into components.

    Args:
        url: PostgreSQL connection URL (postgresql://user:pass@host:port/db)

    Returns:
        Dict with user, password, host, port, database keys
    """
    parsed = urlparse(url)

    # Handle URL-encoded password
    password = unquote(parsed.password) if parsed.password else ""

    return {
        "user": parsed.username or "postgres",
        "password": password,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "postgres",
    }


def create_test_database() -> bool:
    """
    Create the test database if it doesn't exist.

    Uses psycopg (version 3) to connect to the default 'postgres' database
    and create 'pcf_calculator_test'.

    Returns:
        bool: True if successful, False otherwise
    """
    import psycopg

    test_url = get_test_database_url()
    url_parts = parse_database_url(test_url)

    print(f"Connecting to PostgreSQL at {url_parts['host']}:{url_parts['port']}...")

    try:
        # Connect to default postgres database to create test database
        # psycopg3 supports autocommit as a connection parameter
        conn = psycopg.connect(
            host=url_parts["host"],
            port=url_parts["port"],
            user=url_parts["user"],
            password=url_parts["password"],
            dbname="postgres",
            autocommit=True
        )

        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'pcf_calculator_test'"
        )
        exists = cursor.fetchone()

        if not exists:
            print("Creating database 'pcf_calculator_test'...")
            cursor.execute("CREATE DATABASE pcf_calculator_test")
            print("Database created successfully.")
        else:
            print("Database 'pcf_calculator_test' already exists.")

        cursor.close()
        conn.close()
        return True

    except psycopg.OperationalError as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        print("Ensure PostgreSQL is running: docker-compose up -d postgres")
        return False


def run_migrations() -> bool:
    """
    Run Alembic migrations on the test database.

    Returns:
        bool: True if successful, False otherwise
    """
    if os.getenv("SKIP_MIGRATIONS") == "1":
        print("Skipping migrations (SKIP_MIGRATIONS=1)")
        return True

    print("\nRunning Alembic migrations...")

    test_url = get_test_database_url()
    backend_dir = PROJECT_ROOT / "backend"

    # Set DATABASE_URL for alembic
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
            return False

        print("Migrations completed successfully.")
        if result.stdout:
            print(result.stdout)
        return True

    except Exception as e:
        print(f"Migration error: {e}")
        return False


def seed_data() -> bool:
    """
    Seed the test database with required data.

    Seeds:
    1. Data sources (EPA, DEFRA metadata)
    2. Data source licenses
    3. E2E test user
    4. Sample products for testing

    Returns:
        bool: True if successful, False otherwise
    """
    if os.getenv("SKIP_SEED") == "1":
        print("Skipping seeding (SKIP_SEED=1)")
        return True

    print("\nSeeding test database...")

    # Override DATABASE_URL for seeding
    test_url = get_test_database_url()
    os.environ["DATABASE_URL"] = test_url

    # Reload settings with new DATABASE_URL
    import importlib
    import backend.config as config_module
    importlib.reload(config_module)

    # Re-import connection module to pick up new settings
    import backend.database.connection as conn_module
    importlib.reload(conn_module)

    from backend.database.connection import db_context

    try:
        with db_context() as session:
            # 1. Seed data sources
            print("  - Seeding data sources...")
            from backend.database.seeds.data_sources import seed_data_sources
            ds_count = seed_data_sources(session)
            print(f"    Created/verified {ds_count} data sources")

            # 2. Seed data source licenses
            print("  - Seeding data source licenses...")
            from backend.database.seeds.compliance_seeds import seed_licenses
            licenses = seed_licenses(session)
            print(f"    Created/verified {len(licenses)} licenses")

            # 3. Seed E2E test user
            print("  - Seeding E2E test user...")
            from backend.database.seeds.e2e_test_user import seed_e2e_test_user
            user_id = seed_e2e_test_user(session, force_update=True)
            print(f"    E2E test user created/updated: {user_id}")

            # 4. Seed sample products
            print("  - Seeding sample products...")
            seed_sample_products(session)

            session.commit()
            print("\nSeeding completed successfully.")
            return True

    except Exception as e:
        print(f"Seeding error: {e}")
        import traceback
        traceback.print_exc()
        return False


def seed_sample_products(session) -> None:
    """
    Seed sample products for E2E testing.

    Creates a minimal set of products that cover:
    - Finished goods with BOMs
    - Raw materials
    - Products with different categories

    Args:
        session: SQLAlchemy database session
    """
    from backend.models import Product

    # Check if products already exist
    existing_count = session.query(Product).count()
    if existing_count > 0:
        print(f"    {existing_count} products already exist, skipping sample products")
        return

    sample_products = [
        {
            "code": "E2E-LAPTOP-001",
            "name": "E2E Test Laptop",
            "description": "Sample laptop for E2E testing",
            "unit": "unit",
            "is_finished_product": True,
            "category": "Electronics",
        },
        {
            "code": "E2E-STEEL-001",
            "name": "E2E Test Steel Sheet",
            "description": "Sample steel material for E2E testing",
            "unit": "kg",
            "is_finished_product": False,
            "category": "Materials",
        },
        {
            "code": "E2E-PLASTIC-001",
            "name": "E2E Test Plastic Housing",
            "description": "Sample plastic component for E2E testing",
            "unit": "kg",
            "is_finished_product": False,
            "category": "Materials",
        },
        {
            "code": "E2E-BATTERY-001",
            "name": "E2E Test Battery Pack",
            "description": "Sample battery for E2E testing",
            "unit": "unit",
            "is_finished_product": False,
            "category": "Electronics",
        },
        {
            "code": "E2E-ALUMINUM-001",
            "name": "E2E Test Aluminum Frame",
            "description": "Sample aluminum component for E2E testing",
            "unit": "kg",
            "is_finished_product": False,
            "category": "Materials",
        },
    ]

    for product_data in sample_products:
        product = Product(**product_data)
        session.add(product)

    print(f"    Added {len(sample_products)} sample products")


def reset_test_database() -> bool:
    """
    Drop and recreate all tables in the test database.

    WARNING: This destroys all data in the test database!

    Returns:
        bool: True if successful, False otherwise
    """
    print("\nResetting test database (dropping all tables)...")

    test_url = get_test_database_url()
    os.environ["DATABASE_URL"] = test_url

    # Reload to pick up new URL
    import importlib
    import backend.config as config_module
    importlib.reload(config_module)

    backend_dir = PROJECT_ROOT / "backend"
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url

    # Downgrade to base (drop all tables)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        cwd=str(backend_dir),
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Downgrade failed: {result.stderr}")
        return False

    print("All tables dropped. Running migrations to recreate...")
    return True


def verify_database() -> bool:
    """
    Verify the test database is properly configured.

    Checks:
    1. Database connection works
    2. Required tables exist
    3. E2E test user exists
    4. Data sources are seeded

    Returns:
        bool: True if verification passes, False otherwise
    """
    print("\nVerifying test database...")

    test_url = get_test_database_url()
    os.environ["DATABASE_URL"] = test_url

    import importlib
    import backend.config as config_module
    importlib.reload(config_module)

    # Re-import connection module
    import backend.database.connection as conn_module
    importlib.reload(conn_module)

    from backend.database.connection import db_context, engine

    try:
        with db_context() as session:
            # Check tables exist
            from sqlalchemy import inspect

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            required_tables = [
                "users", "products", "emission_factors",
                "data_sources", "alembic_version"
            ]

            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                print(f"  WARNING: Missing tables: {missing_tables}")
                return False

            print(f"  Tables: {len(tables)} found (including {', '.join(required_tables[:3])}...)")

            # Check E2E test user
            from backend.database.seeds.e2e_test_user import verify_e2e_test_user
            if verify_e2e_test_user(session):
                print("  E2E test user: OK")
            else:
                print("  WARNING: E2E test user not found")
                return False

            # Check data sources
            from backend.models import DataSource
            ds_count = session.query(DataSource).count()
            print(f"  Data sources: {ds_count} found")

            # Check emission factors
            from backend.models import EmissionFactor
            ef_count = session.query(EmissionFactor).count()
            print(f"  Emission factors: {ef_count} found")

            # Check products
            from backend.models import Product
            product_count = session.query(Product).count()
            print(f"  Products: {product_count} found")

            print("\nTest database verification: PASSED")
            return True

    except Exception as e:
        print(f"Verification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for test database setup."""
    parser = argparse.ArgumentParser(
        description="Setup E2E test database for PCF Calculator"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop all tables before setup)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify database, don't create or seed"
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip data seeding"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("PCF Calculator - E2E Test Database Setup")
    print("=" * 60)
    print(f"\nTest Database URL: {get_test_database_url()[:50]}...")

    if args.verify_only:
        success = verify_database()
        sys.exit(0 if success else 1)

    # Step 1: Create database
    if not create_test_database():
        print("\nFailed to create/connect to test database")
        sys.exit(1)

    # Step 2: Reset if requested
    if args.reset:
        if not reset_test_database():
            print("\nFailed to reset test database")
            sys.exit(2)

    # Step 3: Run migrations
    if not run_migrations():
        print("\nFailed to run migrations")
        sys.exit(2)

    # Step 4: Seed data
    if args.skip_seed:
        os.environ["SKIP_SEED"] = "1"

    if not seed_data():
        print("\nFailed to seed data")
        sys.exit(3)

    # Step 5: Verify
    if not verify_database():
        print("\nDatabase verification failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Test database setup complete!")
    print("=" * 60)
    print("\nTo run E2E tests with this database:")
    print("  export DATABASE_URL=postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test")
    print("  cd backend && uvicorn main:app --reload &")
    print("  cd frontend && npm run test:e2e")


if __name__ == "__main__":
    main()
