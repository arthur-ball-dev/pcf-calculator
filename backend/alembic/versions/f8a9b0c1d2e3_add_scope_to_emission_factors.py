"""add_scope_to_emission_factors

Revision ID: f8a9b0c1d2e3
Revises: 102ff8322c92, e5f2a3b4c6d7
Create Date: 2025-12-05 10:00:00.000000

This migration:
1. Merges the two branch heads (102ff8322c92 and e5f2a3b4c6d7)
2. Adds scope column to emission_factors table for GHG Protocol classification

The scope column tracks emission categories per GHG Protocol:
- "Scope 1": Direct emissions (fuels, on-site combustion)
- "Scope 2": Indirect from purchased energy (electricity, steam)
- "Scope 3": Other indirect emissions (materials, transport, waste)

Note: The Phase 5 schema extensions from e5f2a3b4c6d7 may already be
partially applied to the database. This migration handles that gracefully.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, Sequence[str]] = ('102ff8322c92', 'e5f2a3b4c6d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """Add scope column to emission_factors table."""
    # Add scope column if it doesn't exist
    if not column_exists('emission_factors', 'scope'):
        with op.batch_alter_table('emission_factors', schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('scope', sa.String(20), nullable=True)
            )

    # Create index for scope column if it doesn't exist
    if not index_exists('emission_factors', 'idx_ef_scope'):
        op.create_index('idx_ef_scope', 'emission_factors', ['scope'])


def downgrade() -> None:
    """Remove scope column from emission_factors table."""
    # Drop index if it exists
    if index_exists('emission_factors', 'idx_ef_scope'):
        op.drop_index('idx_ef_scope', table_name='emission_factors')

    # Remove scope column if it exists
    if column_exists('emission_factors', 'scope'):
        with op.batch_alter_table('emission_factors', schema=None) as batch_op:
            batch_op.drop_column('scope')
