"""Add index on emission_factors.category

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-23

TASK-DB-P7-023: Add database index on emission_factors.category column
to improve query performance for category-based emission factor lookups.

The category column is frequently queried for filtering emission factors
by type (material, energy, transport, etc.) and was causing full table
scans without an index.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    """Create index on emission_factors.category column.

    Uses IF NOT EXISTS pattern for idempotency - safe to run multiple times.
    Index name follows convention: ix_{table_name}_{column_name}
    """
    # Only create index if it doesn't already exist (idempotent)
    if not index_exists('emission_factors', 'ix_emission_factors_category'):
        op.create_index(
            'ix_emission_factors_category',
            'emission_factors',
            ['category'],
            unique=False
        )


def downgrade() -> None:
    """Remove index from emission_factors.category column.

    Safe rollback - checks if index exists before dropping.
    """
    # Only drop index if it exists (safe rollback)
    if index_exists('emission_factors', 'ix_emission_factors_category'):
        op.drop_index('ix_emission_factors_category', table_name='emission_factors')
