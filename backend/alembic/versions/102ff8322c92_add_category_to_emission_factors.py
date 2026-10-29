"""add_category_to_emission_factors

Revision ID: 102ff8322c92
Revises: d9b116c0baf9
Create Date: 2025-11-11 07:21:20.444971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '102ff8322c92'
down_revision: Union[str, None] = 'd9b116c0baf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category column to emission_factors table
    op.add_column('emission_factors', sa.Column('category', sa.String(50), nullable=True))

    # Update existing records with appropriate categories
    connection = op.get_bind()

    # Category mappings based on activity names
    category_mappings = {
        # Materials
        'cotton': 'material',
        'polyester': 'material',
        'plastic_pet': 'material',
        'plastic_abs': 'material',
        'plastic_hdpe': 'material',
        'aluminum': 'material',
        'steel': 'material',
        'glass': 'material',
        'paper': 'material',
        'rubber': 'material',
        'copper': 'material',
        'wood': 'material',
        'leather': 'material',
        'nylon': 'material',
        'ceramic': 'material',
        'foam': 'material',
        # Energy
        'electricity_us': 'energy',
        # Transport
        'transport_truck': 'transport',
        'transport_ship': 'transport',
        # Other
        'water': 'other',
    }

    # Update each emission factor
    for activity_name, category in category_mappings.items():
        connection.execute(
            sa.text("UPDATE emission_factors SET category = :category WHERE activity_name = :activity_name"),
            {"category": category, "activity_name": activity_name}
        )


def downgrade() -> None:
    # Remove category column from emission_factors table
    op.drop_column('emission_factors', 'category')
