#!/usr/bin/env python3
"""Setup PostgreSQL database with schema and seed data.

This script creates all tables using SQLAlchemy's create_all()
which is database-agnostic and works with both SQLite and PostgreSQL.

Usage:
    DATABASE_URL="postgresql+psycopg://..." python scripts/setup_postgresql.py
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import engine
from backend.models import Base
from sqlalchemy import inspect, text


def setup_database():
    """Create all tables and verify setup."""
    print(f"Connecting to: {engine.url}")
    print(f"Dialect: {engine.dialect.name}")

    # Drop existing tables for clean slate
    print("\nDropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    # Create all tables from SQLAlchemy models
    print("Creating tables from SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)

    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTables created ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")

    # Create the v_bom_explosion view (PostgreSQL-specific)
    if engine.dialect.name == 'postgresql':
        print("\nCreating v_bom_explosion view (PostgreSQL)...")
        with engine.connect() as conn:
            conn.execute(text("DROP VIEW IF EXISTS v_bom_explosion"))
            conn.execute(text("""
                CREATE VIEW v_bom_explosion AS
                WITH RECURSIVE bom_tree AS (
                    SELECT
                        p.id AS root_id,
                        p.name AS root_name,
                        p.id AS component_id,
                        p.name AS component_name,
                        0 AS level,
                        1.0 AS cumulative_quantity,
                        p.unit,
                        CAST(p.id AS TEXT) AS path
                    FROM products p
                    WHERE p.is_finished_product = TRUE

                    UNION ALL

                    SELECT
                        bt.root_id,
                        bt.root_name,
                        child.id AS component_id,
                        child.name AS component_name,
                        bt.level + 1,
                        bt.cumulative_quantity * bom.quantity,
                        COALESCE(bom.unit, child.unit) AS unit,
                        bt.path || '/' || child.id AS path
                    FROM bom_tree bt
                    JOIN bill_of_materials bom ON bt.component_id = bom.parent_product_id
                    JOIN products child ON bom.child_product_id = child.id
                    WHERE bt.level < 10
                      AND POSITION(child.id IN bt.path) = 0
                )
                SELECT * FROM bom_tree
            """))
            conn.commit()
        print("View created successfully")

    print("\n✓ PostgreSQL database setup complete!")
    return True


if __name__ == "__main__":
    setup_database()
