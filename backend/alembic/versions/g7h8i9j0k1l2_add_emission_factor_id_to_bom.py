"""add_emission_factor_id_to_bom

Revision ID: g7h8i9j0k1l2
Revises: 196daf0f7c71
Create Date: 2026-01-21 19:15:00.000000

Adds emission_factor_id column to bill_of_materials table to store
the assigned emission factor for each BOM component. This enables
consistent EF pre-population when loading product BOMs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = '196daf0f7c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add emission_factor_id column to bill_of_materials
    op.add_column(
        'bill_of_materials',
        sa.Column('emission_factor_id', sa.String(32), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_bom_emission_factor',
        'bill_of_materials',
        'emission_factors',
        ['emission_factor_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove foreign key first
    op.drop_constraint('fk_bom_emission_factor', 'bill_of_materials', type_='foreignkey')

    # Remove column
    op.drop_column('bill_of_materials', 'emission_factor_id')
