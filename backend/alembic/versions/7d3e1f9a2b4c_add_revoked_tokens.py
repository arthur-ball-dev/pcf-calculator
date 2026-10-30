"""add revoked_tokens denylist for logout

Revision ID: 7d3e1f9a2b4c
Revises: 5c754d1c1305
Create Date: 2026-10-30 19:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d3e1f9a2b4c'
down_revision: Union[str, None] = '5c754d1c1305'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'revoked_tokens',
        sa.Column('jti', sa.String(length=32), primary_key=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_revoked_tokens_expires_at', 'revoked_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_revoked_tokens_expires_at', table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
