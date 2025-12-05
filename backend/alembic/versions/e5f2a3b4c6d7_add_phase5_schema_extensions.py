"""add_phase5_schema_extensions

Revision ID: e5f2a3b4c6d7
Revises: d9b116c0baf9
Create Date: 2025-12-04 14:00:00.000000

TASK-DB-P5-002: Extended Database Schema

This migration adds Phase 5 schema extensions:
- data_sources table for tracking emission factor sources
- product_categories table for hierarchical product categorization
- data_sync_logs table for sync operation audit trail
- New columns to products table (category_id, manufacturer, country_of_origin, search_vector)
- New columns to emission_factors table (data_source_id, external_id, sync_batch_id, is_active, search_vector)
- Indexes for optimized queries

Notes:
- search_vector columns are TEXT in SQLite (TSVECTOR in PostgreSQL)
- GIN indexes for full-text search are PostgreSQL-specific and handled conditionally
- Migration is idempotent - checks for existence before creating
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e5f2a3b4c6d7'
down_revision: Union[str, None] = 'd9b116c0baf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_postgresql() -> bool:
    """Check if the current database is PostgreSQL."""
    return op.get_bind().dialect.name == 'postgresql'


def is_sqlite() -> bool:
    """Check if the current database is SQLite."""
    return op.get_bind().dialect.name == 'sqlite'


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """
    Add Phase 5 schema extensions.

    Creates new tables and adds columns to existing tables for:
    - Data source tracking (DataSource)
    - Product categorization (ProductCategory)
    - Sync operation audit trail (DataSyncLog)
    - Full-text search support (search_vector columns)
    """
    # Step 1: Drop the view before altering tables
    op.execute("DROP VIEW IF EXISTS v_bom_explosion")

    # Step 2: Create data_sources table if it doesn't exist
    if not table_exists('data_sources'):
        op.create_table(
            'data_sources',
            sa.Column('id', sa.String(32), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False, unique=True),
            sa.Column('source_type', sa.String(50), nullable=False),
            sa.Column('base_url', sa.Text(), nullable=True),
            sa.Column('api_key_env_var', sa.String(100), nullable=True),
            sa.Column('sync_frequency', sa.String(20), server_default='biweekly'),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        )

    # Step 3: Create product_categories table if it doesn't exist
    if not table_exists('product_categories'):
        op.create_table(
            'product_categories',
            sa.Column('id', sa.String(32), primary_key=True),
            sa.Column('code', sa.String(20), nullable=False, unique=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('parent_id', sa.String(32), sa.ForeignKey('product_categories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('industry_sector', sa.String(100), nullable=True),
            sa.Column('search_vector', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # Create indexes for product_categories if they don't exist
    if not index_exists('product_categories', 'idx_category_parent'):
        op.create_index('idx_category_parent', 'product_categories', ['parent_id'])
    if not index_exists('product_categories', 'idx_category_industry'):
        op.create_index('idx_category_industry', 'product_categories', ['industry_sector'])
    if not index_exists('product_categories', 'idx_category_level'):
        op.create_index('idx_category_level', 'product_categories', ['level'])

    # Step 4: Create data_sync_logs table if it doesn't exist
    if not table_exists('data_sync_logs'):
        op.create_table(
            'data_sync_logs',
            sa.Column('id', sa.String(32), primary_key=True),
            sa.Column('data_source_id', sa.String(32), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
            sa.Column('sync_type', sa.String(20), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('celery_task_id', sa.String(255), nullable=True),
            sa.Column('records_processed', sa.Integer(), server_default='0'),
            sa.Column('records_created', sa.Integer(), server_default='0'),
            sa.Column('records_updated', sa.Integer(), server_default='0'),
            sa.Column('records_skipped', sa.Integer(), server_default='0'),
            sa.Column('records_failed', sa.Integer(), server_default='0'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('error_details', sa.JSON(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # Create indexes for data_sync_logs if they don't exist
    if not index_exists('data_sync_logs', 'idx_sync_log_source'):
        op.create_index('idx_sync_log_source', 'data_sync_logs', ['data_source_id'])
    if not index_exists('data_sync_logs', 'idx_sync_log_status'):
        op.create_index('idx_sync_log_status', 'data_sync_logs', ['status'])
    if not index_exists('data_sync_logs', 'idx_sync_log_started'):
        op.create_index('idx_sync_log_started', 'data_sync_logs', ['started_at'])
    if not index_exists('data_sync_logs', 'idx_sync_log_celery_task'):
        op.create_index('idx_sync_log_celery_task', 'data_sync_logs', ['celery_task_id'])

    # Step 5: Add new columns to products table if they don't exist
    columns_to_add = [
        ('category_id', sa.Column('category_id', sa.String(32), nullable=True)),
        ('manufacturer', sa.Column('manufacturer', sa.String(255), nullable=True)),
        ('country_of_origin', sa.Column('country_of_origin', sa.String(50), nullable=True)),
        ('search_vector', sa.Column('search_vector', sa.Text(), nullable=True)),
    ]

    for col_name, col_def in columns_to_add:
        if not column_exists('products', col_name):
            with op.batch_alter_table('products', schema=None) as batch_op:
                batch_op.add_column(col_def)

    # Create indexes for new products columns if they don't exist
    if not index_exists('products', 'idx_products_category'):
        op.create_index('idx_products_category', 'products', ['category_id'])
    if not index_exists('products', 'idx_products_manufacturer'):
        op.create_index('idx_products_manufacturer', 'products', ['manufacturer'])

    # Step 6: Add new columns to emission_factors table if they don't exist
    ef_columns_to_add = [
        ('data_source_id', sa.Column('data_source_id', sa.String(32), nullable=True)),
        ('external_id', sa.Column('external_id', sa.String(255), nullable=True)),
        ('sync_batch_id', sa.Column('sync_batch_id', sa.String(32), nullable=True)),
        ('is_active', sa.Column('is_active', sa.Boolean(), server_default='1')),
        ('search_vector', sa.Column('search_vector', sa.Text(), nullable=True)),
    ]

    for col_name, col_def in ef_columns_to_add:
        if not column_exists('emission_factors', col_name):
            with op.batch_alter_table('emission_factors', schema=None) as batch_op:
                batch_op.add_column(col_def)

    # Create indexes for new emission_factors columns if they don't exist
    if not index_exists('emission_factors', 'idx_ef_source'):
        op.create_index('idx_ef_source', 'emission_factors', ['data_source_id'])
    if not index_exists('emission_factors', 'idx_ef_external'):
        op.create_index('idx_ef_external', 'emission_factors', ['external_id'])
    if not index_exists('emission_factors', 'idx_ef_active'):
        op.create_index('idx_ef_active', 'emission_factors', ['is_active'])

    # Step 7: Recreate v_bom_explosion view
    op.execute("""
        CREATE VIEW IF NOT EXISTS v_bom_explosion AS
        WITH RECURSIVE bom_tree AS (
            -- Base case: Start with finished products
            SELECT
                p.id AS root_id,
                p.name AS root_name,
                p.id AS component_id,
                p.name AS component_name,
                0 AS level,
                1.0 AS cumulative_quantity,
                p.unit,
                p.id AS path
            FROM products p
            WHERE p.is_finished_product = 1

            UNION ALL

            -- Recursive case: Traverse BOM
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
            WHERE bt.level < 10  -- Prevent infinite recursion
              AND INSTR(bt.path, child.id) = 0  -- Prevent cycles
        )
        SELECT * FROM bom_tree
    """)

    # Step 8: PostgreSQL-specific: Create GIN indexes and triggers for full-text search
    if is_postgresql():
        # Create GIN indexes for TSVECTOR columns
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_search_gin
            ON products USING GIN(to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(code, '') || ' ' || COALESCE(description, '')))
        """)
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ef_search_gin
            ON emission_factors USING GIN(to_tsvector('english', COALESCE(activity_name, '')))
        """)
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_category_search_gin
            ON product_categories USING GIN(to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(code, '')))
        """)

        # Create trigger function for products search_vector
        op.execute("""
            CREATE OR REPLACE FUNCTION update_product_search_vector()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.code, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        op.execute("""
            DROP TRIGGER IF EXISTS products_search_vector_update ON products;
            CREATE TRIGGER products_search_vector_update
            BEFORE INSERT OR UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();
        """)

        # Create trigger function for emission_factors search_vector
        op.execute("""
            CREATE OR REPLACE FUNCTION update_emission_factor_search_vector()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.activity_name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.category, '')), 'B');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        op.execute("""
            DROP TRIGGER IF EXISTS ef_search_vector_update ON emission_factors;
            CREATE TRIGGER ef_search_vector_update
            BEFORE INSERT OR UPDATE ON emission_factors
            FOR EACH ROW EXECUTE FUNCTION update_emission_factor_search_vector();
        """)

        # Create trigger function for product_categories search_vector
        op.execute("""
            CREATE OR REPLACE FUNCTION update_category_search_vector()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.code, '')), 'B');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        op.execute("""
            DROP TRIGGER IF EXISTS categories_search_vector_update ON product_categories;
            CREATE TRIGGER categories_search_vector_update
            BEFORE INSERT OR UPDATE ON product_categories
            FOR EACH ROW EXECUTE FUNCTION update_category_search_vector();
        """)


def downgrade() -> None:
    """
    Remove Phase 5 schema extensions.

    Drops new tables and removes columns added to existing tables.
    """
    # Step 1: Drop the view before altering tables
    op.execute("DROP VIEW IF EXISTS v_bom_explosion")

    # Step 2: PostgreSQL-specific: Drop triggers and functions
    if is_postgresql():
        op.execute("DROP TRIGGER IF EXISTS products_search_vector_update ON products")
        op.execute("DROP FUNCTION IF EXISTS update_product_search_vector()")
        op.execute("DROP TRIGGER IF EXISTS ef_search_vector_update ON emission_factors")
        op.execute("DROP FUNCTION IF EXISTS update_emission_factor_search_vector()")
        op.execute("DROP TRIGGER IF EXISTS categories_search_vector_update ON product_categories")
        op.execute("DROP FUNCTION IF EXISTS update_category_search_vector()")

        # Drop GIN indexes
        op.execute("DROP INDEX IF EXISTS idx_products_search_gin")
        op.execute("DROP INDEX IF EXISTS idx_ef_search_gin")
        op.execute("DROP INDEX IF EXISTS idx_category_search_gin")

    # Step 3: Drop indexes from emission_factors
    if index_exists('emission_factors', 'idx_ef_source'):
        op.drop_index('idx_ef_source', table_name='emission_factors')
    if index_exists('emission_factors', 'idx_ef_external'):
        op.drop_index('idx_ef_external', table_name='emission_factors')
    if index_exists('emission_factors', 'idx_ef_active'):
        op.drop_index('idx_ef_active', table_name='emission_factors')

    # Step 4: Remove columns from emission_factors
    with op.batch_alter_table('emission_factors', schema=None) as batch_op:
        if column_exists('emission_factors', 'search_vector'):
            batch_op.drop_column('search_vector')
        if column_exists('emission_factors', 'is_active'):
            batch_op.drop_column('is_active')
        if column_exists('emission_factors', 'sync_batch_id'):
            batch_op.drop_column('sync_batch_id')
        if column_exists('emission_factors', 'external_id'):
            batch_op.drop_column('external_id')
        if column_exists('emission_factors', 'data_source_id'):
            batch_op.drop_column('data_source_id')

    # Step 5: Drop indexes from products
    if index_exists('products', 'idx_products_category'):
        op.drop_index('idx_products_category', table_name='products')
    if index_exists('products', 'idx_products_manufacturer'):
        op.drop_index('idx_products_manufacturer', table_name='products')

    # Step 6: Remove columns from products
    with op.batch_alter_table('products', schema=None) as batch_op:
        if column_exists('products', 'search_vector'):
            batch_op.drop_column('search_vector')
        if column_exists('products', 'country_of_origin'):
            batch_op.drop_column('country_of_origin')
        if column_exists('products', 'manufacturer'):
            batch_op.drop_column('manufacturer')
        if column_exists('products', 'category_id'):
            batch_op.drop_column('category_id')

    # Step 7: Drop indexes from data_sync_logs
    if table_exists('data_sync_logs'):
        if index_exists('data_sync_logs', 'idx_sync_log_celery_task'):
            op.drop_index('idx_sync_log_celery_task', table_name='data_sync_logs')
        if index_exists('data_sync_logs', 'idx_sync_log_started'):
            op.drop_index('idx_sync_log_started', table_name='data_sync_logs')
        if index_exists('data_sync_logs', 'idx_sync_log_status'):
            op.drop_index('idx_sync_log_status', table_name='data_sync_logs')
        if index_exists('data_sync_logs', 'idx_sync_log_source'):
            op.drop_index('idx_sync_log_source', table_name='data_sync_logs')

    # Step 8: Drop data_sync_logs table
    if table_exists('data_sync_logs'):
        op.drop_table('data_sync_logs')

    # Step 9: Drop indexes from product_categories
    if table_exists('product_categories'):
        if index_exists('product_categories', 'idx_category_level'):
            op.drop_index('idx_category_level', table_name='product_categories')
        if index_exists('product_categories', 'idx_category_industry'):
            op.drop_index('idx_category_industry', table_name='product_categories')
        if index_exists('product_categories', 'idx_category_parent'):
            op.drop_index('idx_category_parent', table_name='product_categories')

    # Step 10: Drop product_categories table
    if table_exists('product_categories'):
        op.drop_table('product_categories')

    # Step 11: Drop data_sources table
    if table_exists('data_sources'):
        op.drop_table('data_sources')

    # Step 12: Recreate v_bom_explosion view
    op.execute("""
        CREATE VIEW IF NOT EXISTS v_bom_explosion AS
        WITH RECURSIVE bom_tree AS (
            -- Base case: Start with finished products
            SELECT
                p.id AS root_id,
                p.name AS root_name,
                p.id AS component_id,
                p.name AS component_name,
                0 AS level,
                1.0 AS cumulative_quantity,
                p.unit,
                p.id AS path
            FROM products p
            WHERE p.is_finished_product = 1

            UNION ALL

            -- Recursive case: Traverse BOM
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
            WHERE bt.level < 10  -- Prevent infinite recursion
              AND INSTR(bt.path, child.id) = 0  -- Prevent cycles
        )
        SELECT * FROM bom_tree
    """)
