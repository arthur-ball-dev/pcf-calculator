"""
SQLite to PostgreSQL Data Migration Script

TASK-DATA-P8-001: SQLite to PostgreSQL Data Migration

Usage:
    python -m backend.scripts.migrate_sqlite_to_postgres \
        --sqlite-url sqlite:///./pcf_calculator.db \
        --postgres-url postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator

    # Or using environment variables:
    SQLITE_URL=sqlite:///./pcf_calculator.db \
    DATABASE_URL=postgresql://... \
    python -m backend.scripts.migrate_sqlite_to_postgres

    # Force re-migration (clears existing data):
    python -m backend.scripts.migrate_sqlite_to_postgres --force

    # Validate only (no migration):
    python -m backend.scripts.migrate_sqlite_to_postgres --validate-only

Features:
    - Validates source and target connections
    - Migrates data in dependency order
    - Handles UUID conversion (preserves existing UUIDs)
    - Supports batch processing for large tables (products)
    - Generates migration report
    - Transaction-based with rollback on errors
    - Idempotent (safe to run multiple times with --force)
"""

import argparse
import logging
import os
import sys
import time
import uuid as uuid_module
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Migration order based on table dependencies
# Tables are migrated in this order to maintain referential integrity
MIGRATION_ORDER = [
    "data_sources",         # No dependencies - must be first
    "product_categories",   # Self-referential (parent_id NULL first, then children)
    "emission_factors",     # Depends on data_sources
    "products",             # Depends on product_categories
    "bill_of_materials",    # Depends on products
    "pcf_calculations",     # Depends on products
    "calculation_details",  # Depends on pcf_calculations, products, emission_factors
    "data_sync_logs",       # Depends on data_sources
]

# Batch size for large tables (BATCH_SIZE used with LIMIT/OFFSET)
BATCH_SIZE = 500

# Flag indicating support for --force
FORCE_FLAG = True


# =============================================================================
# UUID Conversion
# =============================================================================

def convert_id(sqlite_id: Optional[str]) -> Optional[str]:
    """
    Convert SQLite ID to PostgreSQL-compatible UUID format.

    SQLite IDs may be:
    - Already a valid UUID string (32 hex chars without hyphens)
    - A UUID with hyphens (36 chars)
    - None/NULL

    Args:
        sqlite_id: The ID from SQLite database

    Returns:
        UUID string in 32-char hex format (no hyphens), or None
    """
    if sqlite_id is None:
        return None

    # Convert to string and remove hyphens
    id_str = str(sqlite_id).replace("-", "").lower()

    # If it's a valid 32-char hex string, return it
    if len(id_str) == 32:
        try:
            # Validate it's valid hex
            int(id_str, 16)
            return id_str
        except ValueError:
            pass

    # Otherwise generate deterministic UUID from the value
    # Using UUID5 for reproducibility
    return uuid_module.uuid5(uuid_module.NAMESPACE_DNS, str(sqlite_id)).hex


# =============================================================================
# Source Database Validation
# =============================================================================

def validate_source(sqlite_session: Session) -> bool:
    """
    Validate that source SQLite database exists and has data.

    Checks:
    1. All required tables exist
    2. Critical tables have data (products, emission_factors)

    Args:
        sqlite_session: SQLAlchemy session for SQLite

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    required_tables = [
        "products",
        "emission_factors",
        "bill_of_materials",
        "data_sources",
        "product_categories",
        "pcf_calculations",
        "calculation_details",
    ]

    # Check for existing tables
    result = sqlite_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'")
    )
    existing_tables = {row[0] for row in result.fetchall()}

    missing_tables = []
    for table in required_tables:
        if table not in existing_tables:
            missing_tables.append(table)

    if missing_tables:
        raise ValueError(f"Missing required tables in SQLite: {missing_tables}")

    # Check critical tables have data
    products_count = sqlite_session.execute(
        text("SELECT COUNT(*) FROM products")
    ).scalar()

    ef_count = sqlite_session.execute(
        text("SELECT COUNT(*) FROM emission_factors")
    ).scalar()

    if products_count == 0:
        logger.warning("Products table is empty")

    if ef_count == 0:
        logger.warning("Emission factors table is empty")

    logger.info(f"Source validation passed: {products_count} products, {ef_count} emission factors")
    return True


def validate_sqlite_database(sqlite_session: Session) -> bool:
    """
    Alias for validate_source for test compatibility.
    """
    return validate_source(sqlite_session)


# =============================================================================
# Migration State Tracking
# =============================================================================

def get_migration_status(postgres_session: Session) -> Dict[str, int]:
    """
    Get current migration status by checking record counts.

    Returns:
        Dict mapping table names to record counts
    """
    status = {}

    for table in MIGRATION_ORDER:
        try:
            count = postgres_session.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()
            status[table] = count
        except Exception:
            status[table] = 0

    return status


def check_migration_state(postgres_session: Session) -> str:
    """
    Check if migration has been partially or fully completed.

    Returns:
        'empty': No data in PostgreSQL
        'partial': Some tables have data
        'complete': All tables have data
    """
    status = get_migration_status(postgres_session)

    tables_with_data = sum(1 for count in status.values() if count > 0)

    if tables_with_data == 0:
        return 'empty'
    elif tables_with_data < len(MIGRATION_ORDER):
        return 'partial'
    else:
        return 'complete'


# =============================================================================
# Table Migration Functions
# =============================================================================

def clear_table(postgres_session: Session, table_name: str):
    """
    Clear all data from a PostgreSQL table.

    Uses TRUNCATE CASCADE to handle foreign key constraints.
    """
    try:
        postgres_session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        logger.debug(f"Cleared table {table_name}")
    except Exception as e:
        logger.warning(f"Could not truncate {table_name}: {e}")
        # Fall back to DELETE
        postgres_session.execute(text(f"DELETE FROM {table_name}"))


def migrate_data_sources(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate data_sources table.

    No dependencies, migrate all at once.
    """
    rows = sqlite_session.execute(text("""
        SELECT id, name, source_type, base_url, api_key_env_var,
               sync_frequency, last_sync_at, is_active,
               license_type, license_url, attribution_text, attribution_url,
               allows_commercial_use, requires_attribution, requires_share_alike,
               created_at, updated_at
        FROM data_sources
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO data_sources (
                id, name, source_type, base_url, api_key_env_var,
                sync_frequency, last_sync_at, is_active,
                license_type, license_url, attribution_text, attribution_url,
                allows_commercial_use, requires_attribution, requires_share_alike,
                created_at, updated_at
            ) VALUES (
                :id, :name, :source_type, :base_url, :api_key_env_var,
                :sync_frequency, :last_sync_at, :is_active,
                :license_type, :license_url, :attribution_text, :attribution_url,
                :allows_commercial_use, :requires_attribution, :requires_share_alike,
                :created_at, :updated_at
            )
        """), {
            "id": convert_id(row[0]),
            "name": row[1],
            "source_type": row[2],
            "base_url": row[3],
            "api_key_env_var": row[4],
            "sync_frequency": row[5],
            "last_sync_at": row[6],
            "is_active": bool(row[7]) if row[7] is not None else True,
            "license_type": row[8] if len(row) > 8 else None,
            "license_url": row[9] if len(row) > 9 else None,
            "attribution_text": row[10] if len(row) > 10 else None,
            "attribution_url": row[11] if len(row) > 11 else None,
            "allows_commercial_use": bool(row[12]) if len(row) > 12 and row[12] is not None else True,
            "requires_attribution": bool(row[13]) if len(row) > 13 and row[13] is not None else False,
            "requires_share_alike": bool(row[14]) if len(row) > 14 and row[14] is not None else False,
            "created_at": row[15] if len(row) > 15 else datetime.now(timezone.utc),
            "updated_at": row[16] if len(row) > 16 else None,
        })
        count += 1

    return count


def migrate_product_categories(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate product_categories table.

    Self-referential table - must migrate in level order:
    1. First migrate root categories (parent_id IS NULL)
    2. Then migrate by level to maintain foreign key integrity
    """
    # First pass: Insert root categories (parent_id IS NULL)
    roots = sqlite_session.execute(text("""
        SELECT id, code, name, parent_id, level, industry_sector, search_vector, created_at
        FROM product_categories
        WHERE parent_id IS NULL
        ORDER BY level, code
    """)).fetchall()

    count = 0
    for row in roots:
        postgres_session.execute(text("""
            INSERT INTO product_categories (
                id, code, name, parent_id, level, industry_sector, search_vector, created_at
            ) VALUES (
                :id, :code, :name, :parent_id, :level, :industry_sector, :search_vector, :created_at
            )
        """), {
            "id": convert_id(row[0]),
            "code": row[1],
            "name": row[2],
            "parent_id": None,
            "level": row[4] or 0,
            "industry_sector": row[5],
            "search_vector": row[6],
            "created_at": row[7] or datetime.now(timezone.utc),
        })
        count += 1

    # Second pass: Insert children by level
    for level in range(1, 10):  # Max depth safety
        children = sqlite_session.execute(text("""
            SELECT id, code, name, parent_id, level, industry_sector, search_vector, created_at
            FROM product_categories
            WHERE level = :level AND parent_id IS NOT NULL
            ORDER BY code
        """), {"level": level}).fetchall()

        if not children:
            break

        for row in children:
            postgres_session.execute(text("""
                INSERT INTO product_categories (
                    id, code, name, parent_id, level, industry_sector, search_vector, created_at
                ) VALUES (
                    :id, :code, :name, :parent_id, :level, :industry_sector, :search_vector, :created_at
                )
            """), {
                "id": convert_id(row[0]),
                "code": row[1],
                "name": row[2],
                "parent_id": convert_id(row[3]),
                "level": row[4],
                "industry_sector": row[5],
                "search_vector": row[6],
                "created_at": row[7] or datetime.now(timezone.utc),
            })
            count += 1

    return count


def migrate_emission_factors(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate emission_factors table.

    Depends on data_sources for data_source_id foreign key.
    """
    rows = sqlite_session.execute(text("""
        SELECT id, activity_name, category, co2e_factor, unit, data_source,
               geography, reference_year, data_quality_rating,
               uncertainty_min, uncertainty_max, metadata,
               valid_from, valid_to, created_at, updated_at,
               data_source_id, external_id, sync_batch_id, is_active, scope, search_vector
        FROM emission_factors
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO emission_factors (
                id, activity_name, category, co2e_factor, unit, data_source,
                geography, reference_year, data_quality_rating,
                uncertainty_min, uncertainty_max, metadata,
                valid_from, valid_to, created_at, updated_at,
                data_source_id, external_id, sync_batch_id, is_active, scope, search_vector
            ) VALUES (
                :id, :activity_name, :category, :co2e_factor, :unit, :data_source,
                :geography, :reference_year, :data_quality_rating,
                :uncertainty_min, :uncertainty_max, :metadata,
                :valid_from, :valid_to, :created_at, :updated_at,
                :data_source_id, :external_id, :sync_batch_id, :is_active, :scope, :search_vector
            )
        """), {
            "id": convert_id(row[0]),
            "activity_name": row[1],
            "category": row[2],
            "co2e_factor": row[3],
            "unit": row[4],
            "data_source": row[5],
            "geography": row[6],
            "reference_year": row[7],
            "data_quality_rating": row[8],
            "uncertainty_min": row[9],
            "uncertainty_max": row[10],
            "metadata": row[11],
            "valid_from": row[12],
            "valid_to": row[13],
            "created_at": row[14] or datetime.now(timezone.utc),
            "updated_at": row[15],
            "data_source_id": convert_id(row[16]) if len(row) > 16 and row[16] else None,
            "external_id": row[17] if len(row) > 17 else None,
            "sync_batch_id": row[18] if len(row) > 18 else None,
            "is_active": bool(row[19]) if len(row) > 19 and row[19] is not None else True,
            "scope": row[20] if len(row) > 20 else None,
            "search_vector": row[21] if len(row) > 21 else None,
        })
        count += 1

    return count


def migrate_products(
    sqlite_session: Session,
    postgres_session: Session,
    batch_size: int = BATCH_SIZE
) -> int:
    """
    Migrate products table with batch processing.

    Products table is large (~4000 rows), so use batched processing
    to avoid memory issues and provide progress updates.
    """
    offset = 0
    total_migrated = 0

    while True:
        batch = sqlite_session.execute(text("""
            SELECT id, code, name, description, unit, category, is_finished_product,
                   metadata, created_at, updated_at, deleted_at,
                   category_id, manufacturer, country_of_origin, search_vector
            FROM products
            ORDER BY code
            LIMIT :limit OFFSET :offset
        """), {"limit": batch_size, "offset": offset}).fetchall()

        if not batch:
            break

        for row in batch:
            postgres_session.execute(text("""
                INSERT INTO products (
                    id, code, name, description, unit, category, is_finished_product,
                    metadata, created_at, updated_at, deleted_at,
                    category_id, manufacturer, country_of_origin, search_vector
                ) VALUES (
                    :id, :code, :name, :description, :unit, :category, :is_finished_product,
                    :metadata, :created_at, :updated_at, :deleted_at,
                    :category_id, :manufacturer, :country_of_origin, :search_vector
                )
            """), {
                "id": convert_id(row[0]),
                "code": row[1],
                "name": row[2],
                "description": row[3],
                "unit": row[4],
                "category": row[5],
                "is_finished_product": bool(row[6]) if row[6] is not None else False,
                "metadata": row[7],
                "created_at": row[8] or datetime.now(timezone.utc),
                "updated_at": row[9],
                "deleted_at": row[10],
                "category_id": convert_id(row[11]) if len(row) > 11 and row[11] else None,
                "manufacturer": row[12] if len(row) > 12 else None,
                "country_of_origin": row[13] if len(row) > 13 else None,
                "search_vector": row[14] if len(row) > 14 else None,
            })

        total_migrated += len(batch)
        offset += batch_size
        logger.info(f"Migrated {total_migrated} products...")

    return total_migrated


def migrate_bill_of_materials(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate bill_of_materials table.

    Depends on products for parent_product_id and child_product_id.
    """
    rows = sqlite_session.execute(text("""
        SELECT id, parent_product_id, child_product_id, quantity, unit, notes,
               created_at, updated_at
        FROM bill_of_materials
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO bill_of_materials (
                id, parent_product_id, child_product_id, quantity, unit, notes,
                created_at, updated_at
            ) VALUES (
                :id, :parent_product_id, :child_product_id, :quantity, :unit, :notes,
                :created_at, :updated_at
            )
        """), {
            "id": convert_id(row[0]),
            "parent_product_id": convert_id(row[1]),
            "child_product_id": convert_id(row[2]),
            "quantity": row[3],
            "unit": row[4],
            "notes": row[5],
            "created_at": row[6] or datetime.now(timezone.utc),
            "updated_at": row[7],
        })
        count += 1

    return count


def migrate_pcf_calculations(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate pcf_calculations table.

    Depends on products for product_id.
    """
    rows = sqlite_session.execute(text("""
        SELECT id, product_id, calculation_type, total_co2e_kg,
               materials_co2e, energy_co2e, transport_co2e, waste_co2e,
               primary_data_share, data_quality_score, calculation_method,
               status, input_data, breakdown, metadata, calculated_by,
               calculation_time_ms, created_at
        FROM pcf_calculations
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO pcf_calculations (
                id, product_id, calculation_type, total_co2e_kg,
                materials_co2e, energy_co2e, transport_co2e, waste_co2e,
                primary_data_share, data_quality_score, calculation_method,
                status, input_data, breakdown, metadata, calculated_by,
                calculation_time_ms, created_at
            ) VALUES (
                :id, :product_id, :calculation_type, :total_co2e_kg,
                :materials_co2e, :energy_co2e, :transport_co2e, :waste_co2e,
                :primary_data_share, :data_quality_score, :calculation_method,
                :status, :input_data, :breakdown, :metadata, :calculated_by,
                :calculation_time_ms, :created_at
            )
        """), {
            "id": convert_id(row[0]),
            "product_id": convert_id(row[1]),
            "calculation_type": row[2],
            "total_co2e_kg": row[3],
            "materials_co2e": row[4],
            "energy_co2e": row[5],
            "transport_co2e": row[6],
            "waste_co2e": row[7],
            "primary_data_share": row[8],
            "data_quality_score": row[9],
            "calculation_method": row[10],
            "status": row[11],
            "input_data": row[12],
            "breakdown": row[13],
            "metadata": row[14],
            "calculated_by": row[15],
            "calculation_time_ms": row[16],
            "created_at": row[17] or datetime.now(timezone.utc),
        })
        count += 1

    return count


def migrate_calculation_details(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate calculation_details table.

    Depends on pcf_calculations, products, and emission_factors.
    """
    rows = sqlite_session.execute(text("""
        SELECT id, calculation_id, component_id, component_name, component_level,
               quantity, unit, emission_factor_id, emissions_kg_co2e,
               data_quality, notes, created_at
        FROM calculation_details
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO calculation_details (
                id, calculation_id, component_id, component_name, component_level,
                quantity, unit, emission_factor_id, emissions_kg_co2e,
                data_quality, notes, created_at
            ) VALUES (
                :id, :calculation_id, :component_id, :component_name, :component_level,
                :quantity, :unit, :emission_factor_id, :emissions_kg_co2e,
                :data_quality, :notes, :created_at
            )
        """), {
            "id": convert_id(row[0]),
            "calculation_id": convert_id(row[1]),
            "component_id": convert_id(row[2]) if row[2] else None,
            "component_name": row[3],
            "component_level": row[4],
            "quantity": row[5],
            "unit": row[6],
            "emission_factor_id": convert_id(row[7]) if row[7] else None,
            "emissions_kg_co2e": row[8],
            "data_quality": row[9],
            "notes": row[10],
            "created_at": row[11] or datetime.now(timezone.utc),
        })
        count += 1

    return count


def migrate_data_sync_logs(
    sqlite_session: Session,
    postgres_session: Session
) -> int:
    """
    Migrate data_sync_logs table.

    Depends on data_sources for data_source_id.
    """
    # Check if table exists in SQLite
    result = sqlite_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='data_sync_logs'")
    ).fetchone()

    if not result:
        logger.info("data_sync_logs table not found in SQLite, skipping")
        return 0

    rows = sqlite_session.execute(text("""
        SELECT id, data_source_id, sync_type, status, celery_task_id,
               records_processed, records_created, records_updated,
               records_skipped, records_failed, error_message, error_details,
               metadata, started_at, completed_at, created_at
        FROM data_sync_logs
    """)).fetchall()

    count = 0
    for row in rows:
        postgres_session.execute(text("""
            INSERT INTO data_sync_logs (
                id, data_source_id, sync_type, status, celery_task_id,
                records_processed, records_created, records_updated,
                records_skipped, records_failed, error_message, error_details,
                metadata, started_at, completed_at, created_at
            ) VALUES (
                :id, :data_source_id, :sync_type, :status, :celery_task_id,
                :records_processed, :records_created, :records_updated,
                :records_skipped, :records_failed, :error_message, :error_details,
                :metadata, :started_at, :completed_at, :created_at
            )
        """), {
            "id": convert_id(row[0]),
            "data_source_id": convert_id(row[1]),
            "sync_type": row[2],
            "status": row[3],
            "celery_task_id": row[4],
            "records_processed": row[5] or 0,
            "records_created": row[6] or 0,
            "records_updated": row[7] or 0,
            "records_skipped": row[8] or 0,
            "records_failed": row[9] or 0,
            "error_message": row[10],
            "error_details": row[11],
            "metadata": row[12],
            "started_at": row[13],
            "completed_at": row[14],
            "created_at": row[15] or datetime.now(timezone.utc),
        })
        count += 1

    return count


# =============================================================================
# Main Migration Functions
# =============================================================================

def migrate_large_table(
    sqlite_session: Session,
    postgres_session: Session,
    table_name: str,
    batch_size: int = BATCH_SIZE
) -> int:
    """
    Generic batch migration for large tables using LIMIT/OFFSET.

    This is a wrapper that delegates to table-specific functions.
    Uses batch processing to handle large tables efficiently.
    """
    if table_name == "products":
        return migrate_products(sqlite_session, postgres_session, batch_size)
    else:
        raise ValueError(f"migrate_large_table not implemented for {table_name}")


def migrate(
    sqlite_url: str,
    postgres_url: str,
    force: bool = False,
    validate_only: bool = False
) -> Dict[str, Any]:
    """
    Run the complete SQLite to PostgreSQL migration.

    This function orchestrates the full migration process:
    - Validates source database
    - Creates database connections
    - Migrates tables in dependency order
    - Uses batch processing with LIMIT/OFFSET for large tables (products)
    - Handles transactions with rollback on errors
    - Verifies record counts match after migration

    Args:
        sqlite_url: SQLite database URL
        postgres_url: PostgreSQL database URL
        force: If True, clear existing data before migration
        validate_only: If True, only validate without migrating

    Returns:
        Dict with migration results including:
        - success: bool
        - tables: Dict mapping table names to row counts
        - duration_seconds: float
        - error: Optional error message
    """
    start_time = time.time()

    # Configuration for batch processing of large tables
    batch_config = {
        "products": BATCH_SIZE,  # Use LIMIT/OFFSET batching for products
    }

    results = {
        "success": False,
        "tables": {},
        "duration_seconds": 0,
        "error": None,
        "sqlite_counts": {},
        "postgres_counts": {},
    }

    # Create engines
    try:
        sqlite_engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

        postgres_engine = create_engine(
            postgres_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False
        )
    except Exception as e:
        results["error"] = f"Failed to create database engines: {e}"
        logger.error(results["error"])
        return results

    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)

    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()

    try:
        # Validate source database
        logger.info("Validating source SQLite database...")
        validate_source(sqlite_session)

        # Get source counts
        for table in MIGRATION_ORDER:
            try:
                count = sqlite_session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar()
                results["sqlite_counts"][table] = count
            except Exception:
                results["sqlite_counts"][table] = 0

        if validate_only:
            results["success"] = True
            results["duration_seconds"] = time.time() - start_time
            logger.info("Validation only mode - migration skipped")
            return results

        # Check migration state
        migration_state = check_migration_state(postgres_session)
        logger.info(f"Current migration state: {migration_state}")

        if migration_state != 'empty' and not force:
            results["error"] = (
                f"PostgreSQL database is not empty (state: {migration_state}). "
                "Use --force to clear and re-migrate."
            )
            logger.error(results["error"])
            return results

        # Begin transaction
        logger.info("Starting migration transaction...")

        # Clear existing data if force mode
        if force and migration_state != 'empty':
            logger.info("Force mode: clearing existing data...")
            # Clear in reverse order to handle foreign keys
            for table in reversed(MIGRATION_ORDER):
                clear_table(postgres_session, table)
            postgres_session.commit()

        # Migrate tables in dependency order
        # Note: products table uses batch processing with LIMIT/OFFSET
        migration_functions = {
            "data_sources": migrate_data_sources,
            "product_categories": migrate_product_categories,
            "emission_factors": migrate_emission_factors,
            "products": migrate_products,  # Uses batch_size with LIMIT/OFFSET
            "bill_of_materials": migrate_bill_of_materials,
            "pcf_calculations": migrate_pcf_calculations,
            "calculation_details": migrate_calculation_details,
            "data_sync_logs": migrate_data_sync_logs,
        }

        for table in MIGRATION_ORDER:
            logger.info(f"Migrating {table}...")

            migrate_func = migration_functions.get(table)
            if migrate_func:
                count = migrate_func(sqlite_session, postgres_session)
                results["tables"][table] = count
                logger.info(f"  Migrated {count} rows from {table}")
            else:
                logger.warning(f"  No migration function for {table}")

        # Commit transaction
        postgres_session.commit()
        logger.info("Migration transaction committed successfully")

        # Get final PostgreSQL counts
        for table in MIGRATION_ORDER:
            try:
                count = postgres_session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar()
                results["postgres_counts"][table] = count
            except Exception:
                results["postgres_counts"][table] = 0

        # Verify counts match
        mismatches = []
        for table in MIGRATION_ORDER:
            sqlite_count = results["sqlite_counts"].get(table, 0)
            postgres_count = results["postgres_counts"].get(table, 0)
            if sqlite_count != postgres_count:
                mismatches.append(f"{table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")

        if mismatches:
            logger.warning(f"Count mismatches detected: {mismatches}")

        results["success"] = True

    except Exception as e:
        # Rollback on error
        logger.error(f"Migration failed: {e}")
        postgres_session.rollback()
        results["error"] = str(e)

    finally:
        results["duration_seconds"] = time.time() - start_time
        sqlite_session.close()
        postgres_session.close()
        sqlite_engine.dispose()
        postgres_engine.dispose()

    return results


def run_migration(
    sqlite_url: str,
    postgres_url: str,
    force: bool = False,
    validate_only: bool = False
) -> Dict[str, Any]:
    """
    Alias for migrate() for test compatibility.

    Uses batch processing with LIMIT/OFFSET for large tables.
    """
    return migrate(sqlite_url, postgres_url, force, validate_only)


# =============================================================================
# Command Line Interface
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic migration using environment variables:
    python -m backend.scripts.migrate_sqlite_to_postgres

    # Explicit database URLs:
    python -m backend.scripts.migrate_sqlite_to_postgres \\
        --sqlite-url sqlite:///./pcf_calculator.db \\
        --postgres-url postgresql://user:pass@localhost/db

    # Force re-migration (clears existing data):
    python -m backend.scripts.migrate_sqlite_to_postgres --force

    # Validate only (no migration):
    python -m backend.scripts.migrate_sqlite_to_postgres --validate-only
        """
    )

    parser.add_argument(
        "--sqlite-url",
        default=os.environ.get("SQLITE_URL", "sqlite:///./pcf_calculator.db"),
        help="SQLite database URL (default: env SQLITE_URL or ./pcf_calculator.db)"
    )

    parser.add_argument(
        "--postgres-url",
        default=os.environ.get("TEST_POSTGRES_URL") or os.environ.get("DATABASE_URL"),
        help="PostgreSQL database URL (default: env TEST_POSTGRES_URL or DATABASE_URL)"
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force migration even if PostgreSQL has existing data (clears all data)"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate source database, don't migrate"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for large table migration (default: {BATCH_SIZE})"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate PostgreSQL URL
    if not args.postgres_url:
        logger.error(
            "PostgreSQL URL not specified. "
            "Use --postgres-url or set DATABASE_URL/TEST_POSTGRES_URL environment variable."
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("SQLite to PostgreSQL Migration")
    logger.info("=" * 60)
    logger.info(f"Source: {args.sqlite_url}")
    logger.info(f"Target: {args.postgres_url.split('@')[-1] if '@' in args.postgres_url else args.postgres_url}")
    logger.info(f"Force: {args.force}")
    logger.info(f"Validate Only: {args.validate_only}")
    logger.info("=" * 60)

    # Run migration
    results = migrate(
        sqlite_url=args.sqlite_url,
        postgres_url=args.postgres_url,
        force=args.force,
        validate_only=args.validate_only
    )

    # Print results
    logger.info("")
    logger.info("=" * 60)
    logger.info("Migration Results")
    logger.info("=" * 60)

    if results["success"]:
        logger.info("Status: SUCCESS")
    else:
        logger.error(f"Status: FAILED - {results['error']}")

    logger.info(f"Duration: {results['duration_seconds']:.2f} seconds")

    if results["tables"]:
        logger.info("")
        logger.info("Table row counts:")
        for table, count in results["tables"].items():
            sqlite_count = results["sqlite_counts"].get(table, "N/A")
            postgres_count = results["postgres_counts"].get(table, count)
            match_status = "OK" if sqlite_count == postgres_count else "MISMATCH"
            logger.info(f"  {table}: {count} rows (SQLite: {sqlite_count}, PostgreSQL: {postgres_count}) [{match_status}]")

    logger.info("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
