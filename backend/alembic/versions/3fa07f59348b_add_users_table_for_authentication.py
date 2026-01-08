"""add_users_table_for_authentication

Revision ID: 3fa07f59348b
Revises: b2c3d4e5f6a7
Create Date: 2025-12-28 09:35:09.040698

TASK-QA-P7-032: Add users table for E2E test authentication
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fa07f59348b'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table for authentication."""
    op.create_table('users',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index('idx_users_active', ['is_active'], unique=False)
        batch_op.create_index('idx_users_email', ['email'], unique=False)
        batch_op.create_index('idx_users_role', ['role'], unique=False)
        batch_op.create_index('idx_users_username', ['username'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)


def downgrade() -> None:
    """Drop users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.drop_index('idx_users_username')
        batch_op.drop_index('idx_users_role')
        batch_op.drop_index('idx_users_email')
        batch_op.drop_index('idx_users_active')

    op.drop_table('users')
