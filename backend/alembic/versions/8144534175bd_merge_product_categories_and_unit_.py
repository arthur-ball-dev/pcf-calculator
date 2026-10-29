"""merge_product_categories_and_unit_normalization

Revision ID: 8144534175bd
Revises: 6ff75d78ceef, h8i9j0k1l2m3
Create Date: 2026-02-05 22:09:57.359923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8144534175bd'
down_revision: Union[str, None] = ('6ff75d78ceef', 'h8i9j0k1l2m3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
