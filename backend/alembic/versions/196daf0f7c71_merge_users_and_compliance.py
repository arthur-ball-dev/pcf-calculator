"""merge_users_and_compliance

Revision ID: 196daf0f7c71
Revises: 3fa07f59348b, c3d4e5f6a7b8
Create Date: 2026-01-14 14:26:44.482167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '196daf0f7c71'
down_revision: Union[str, None] = ('3fa07f59348b', 'c3d4e5f6a7b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
