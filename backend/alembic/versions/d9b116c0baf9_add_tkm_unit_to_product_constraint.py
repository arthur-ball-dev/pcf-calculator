"""add_tkm_unit_to_product_constraint

Revision ID: d9b116c0baf9
Revises: aff16d8a8bf7
Create Date: 2025-10-23 20:08:24.532466

This migration adds 'tkm' (tonne-kilometer) to the Product.unit CHECK constraint
and updates existing transport products to use the correct unit.

Transport emission factors (transport_truck, transport_ship) are measured in
tonne-kilometers (tkm) which represents the transport of one tonne over one kilometer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9b116c0baf9'
down_revision: Union[str, None] = 'aff16d8a8bf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'tkm' to Product.unit CHECK constraint and update existing transport products.

    Steps:
    1. Drop old constraint
    2. Create new constraint with 'tkm' included
    3. Update existing transport products to use 'tkm' unit
    """
    # SQLite doesn't support ALTER TABLE DROP CONSTRAINT, so we need to:
    # 1. Create new table with updated constraint
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table

    # However, for CHECK constraints in SQLite, we can work around this by
    # recreating the table. But first, let's update the data.

    # Update existing transport products from 'kg' to 'tkm'
    # These were created with the workaround
    op.execute("""
        UPDATE products
        SET unit = 'tkm'
        WHERE code IN ('transport_truck', 'transport_ship')
          AND unit = 'kg'
    """)

    # For SQLite, we need to recreate the table with the new constraint
    # This is complex, so we'll use a batch operation
    with op.batch_alter_table('products', schema=None) as batch_op:
        # Drop the old constraint (SQLite will handle this during table recreation)
        batch_op.drop_constraint('ck_product_unit', type_='check')

        # Add the new constraint with 'tkm' included
        batch_op.create_check_constraint(
            'ck_product_unit',
            "unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm')"
        )


def downgrade() -> None:
    """
    Remove 'tkm' from Product.unit CHECK constraint and revert transport products.

    Steps:
    1. Update transport products back to 'kg' (workaround)
    2. Drop new constraint
    3. Create old constraint without 'tkm'
    """
    # Update transport products back to 'kg' (workaround state)
    op.execute("""
        UPDATE products
        SET unit = 'kg'
        WHERE code IN ('transport_truck', 'transport_ship')
          AND unit = 'tkm'
    """)

    # Recreate table with old constraint
    with op.batch_alter_table('products', schema=None) as batch_op:
        # Drop the new constraint
        batch_op.drop_constraint('ck_product_unit', type_='check')

        # Add the old constraint without 'tkm'
        batch_op.create_check_constraint(
            'ck_product_unit',
            "unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ')"
        )
