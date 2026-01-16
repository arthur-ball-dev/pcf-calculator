"""add_product_categories

Revision ID: 6ff75d78ceef
Revises: 196daf0f7c71
Create Date: 2026-01-15 22:05:46.073440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ff75d78ceef'
down_revision: Union[str, None] = '196daf0f7c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Product code to category mapping
PRODUCT_CATEGORIES = {
    # Apparel
    'TSHIRT-001': 'apparel',
    'SHOES-001': 'apparel',
    'BACKPACK-001': 'apparel',
    # Consumer Goods
    'BOTTLE-001': 'consumer goods',
    'CASE-001': 'consumer goods',
    'MUG-001': 'consumer goods',
    'SUNGLASSES-001': 'consumer goods',
    # Electronics
    'LAPTOP-001': 'electronics',
    'PHONE-001': 'electronics',
    'LAMP-001': 'electronics',
    'EARBUDS-001': 'electronics',
    # Sports & Recreation
    'HELMET-001': 'sports',
    'YOGAMAT-001': 'sports',
}


def upgrade() -> None:
    """Update product categories for industry filtering."""
    connection = op.get_bind()

    for code, category in PRODUCT_CATEGORIES.items():
        connection.execute(
            sa.text(
                "UPDATE products SET category = :category WHERE code = :code"
            ),
            {"category": category, "code": code}
        )


def downgrade() -> None:
    """Reset product categories to NULL."""
    connection = op.get_bind()

    for code in PRODUCT_CATEGORIES.keys():
        connection.execute(
            sa.text(
                "UPDATE products SET category = NULL WHERE code = :code"
            ),
            {"code": code}
        )
