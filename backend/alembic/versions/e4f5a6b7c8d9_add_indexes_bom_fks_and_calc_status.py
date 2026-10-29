"""add indexes on BOM FKs and calculation status

Revision ID: e4f5a6b7c8d9
Revises: 8144534175bd
Create Date: 2026-02-27

PERF-004: Add missing database indexes on BOM foreign keys
and calculation product_id/status for query performance.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = '8144534175bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(connection, index_name: str) -> bool:
    """Check if an index already exists."""
    inspector = inspect(connection)
    for table_name in ['bill_of_materials', 'pcf_calculations']:
        try:
            indexes = inspector.get_indexes(table_name)
            if any(idx['name'] == index_name for idx in indexes):
                return True
        except Exception:
            pass
    return False


def upgrade() -> None:
    conn = op.get_bind()

    # BOM indexes
    if not _index_exists(conn, 'idx_bom_parent'):
        op.create_index('idx_bom_parent', 'bill_of_materials', ['parent_product_id'])
    if not _index_exists(conn, 'idx_bom_child'):
        op.create_index('idx_bom_child', 'bill_of_materials', ['child_product_id'])
    if not _index_exists(conn, 'idx_bom_emission_factor'):
        op.create_index('idx_bom_emission_factor', 'bill_of_materials', ['emission_factor_id'])

    # Calculation indexes
    if not _index_exists(conn, 'idx_calc_product'):
        op.create_index('idx_calc_product', 'pcf_calculations', ['product_id'])
    if not _index_exists(conn, 'idx_calc_status'):
        op.create_index('idx_calc_status', 'pcf_calculations', ['status'])


def downgrade() -> None:
    op.drop_index('idx_calc_status', table_name='pcf_calculations')
    op.drop_index('idx_calc_product', table_name='pcf_calculations')
    op.drop_index('idx_bom_emission_factor', table_name='bill_of_materials')
    op.drop_index('idx_bom_child', table_name='bill_of_materials')
    op.drop_index('idx_bom_parent', table_name='bill_of_materials')
