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
    1. Drop v_bom_explosion view (depends on products table)
    2. Update existing transport products from 'kg' to 'tkm'
    3. Drop old constraint and create new constraint with 'tkm' included
    4. Recreate v_bom_explosion view
    """
    # Step 1: Drop the view before altering the products table
    # SQLite batch_alter_table will recreate the table, which breaks view references
    op.execute("DROP VIEW IF EXISTS v_bom_explosion")

    # Step 2: Update existing transport products from 'kg' to 'tkm'
    # These were created with the workaround
    op.execute("""
        UPDATE products
        SET unit = 'tkm'
        WHERE code IN ('transport_truck', 'transport_ship')
          AND unit = 'kg'
    """)

    # Step 3: For SQLite, we need to recreate the table with the new constraint
    # This is handled by batch_alter_table
    with op.batch_alter_table('products', schema=None) as batch_op:
        # Drop the old constraint (SQLite will handle this during table recreation)
        batch_op.drop_constraint('ck_product_unit', type_='check')

        # Add the new constraint with 'tkm' included
        batch_op.create_check_constraint(
            'ck_product_unit',
            "unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm')"
        )

    # Step 4: Recreate v_bom_explosion view
    op.execute("""
        CREATE VIEW v_bom_explosion AS
        WITH RECURSIVE bom_tree AS (
            -- Base case: Start with finished products
            SELECT
                p.id AS root_id,
                p.name AS root_name,
                p.id AS component_id,
                p.name AS component_name,
                0 AS level,
                1.0 AS cumulative_quantity,
                p.unit,
                p.id AS path
            FROM products p
            WHERE p.is_finished_product = 1

            UNION ALL

            -- Recursive case: Traverse BOM
            SELECT
                bt.root_id,
                bt.root_name,
                child.id AS component_id,
                child.name AS component_name,
                bt.level + 1,
                bt.cumulative_quantity * bom.quantity,
                COALESCE(bom.unit, child.unit) AS unit,
                bt.path || '/' || child.id AS path
            FROM bom_tree bt
            JOIN bill_of_materials bom ON bt.component_id = bom.parent_product_id
            JOIN products child ON bom.child_product_id = child.id
            WHERE bt.level < 10  -- Prevent infinite recursion
              AND INSTR(bt.path, child.id) = 0  -- Prevent cycles
        )
        SELECT * FROM bom_tree
    """)


def downgrade() -> None:
    """
    Remove 'tkm' from Product.unit CHECK constraint and revert transport products.

    Steps:
    1. Drop v_bom_explosion view
    2. Update transport products back to 'kg' (workaround)
    3. Drop new constraint and create old constraint without 'tkm'
    4. Recreate v_bom_explosion view
    """
    # Step 1: Drop the view before altering the products table
    op.execute("DROP VIEW IF EXISTS v_bom_explosion")

    # Step 2: Update transport products back to 'kg' (workaround state)
    op.execute("""
        UPDATE products
        SET unit = 'kg'
        WHERE code IN ('transport_truck', 'transport_ship')
          AND unit = 'tkm'
    """)

    # Step 3: Recreate table with old constraint
    with op.batch_alter_table('products', schema=None) as batch_op:
        # Drop the new constraint
        batch_op.drop_constraint('ck_product_unit', type_='check')

        # Add the old constraint without 'tkm'
        batch_op.create_check_constraint(
            'ck_product_unit',
            "unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ')"
        )

    # Step 4: Recreate v_bom_explosion view with old constraint
    op.execute("""
        CREATE VIEW v_bom_explosion AS
        WITH RECURSIVE bom_tree AS (
            -- Base case: Start with finished products
            SELECT
                p.id AS root_id,
                p.name AS root_name,
                p.id AS component_id,
                p.name AS component_name,
                0 AS level,
                1.0 AS cumulative_quantity,
                p.unit,
                p.id AS path
            FROM products p
            WHERE p.is_finished_product = 1

            UNION ALL

            -- Recursive case: Traverse BOM
            SELECT
                bt.root_id,
                bt.root_name,
                child.id AS component_id,
                child.name AS component_name,
                bt.level + 1,
                bt.cumulative_quantity * bom.quantity,
                COALESCE(bom.unit, child.unit) AS unit,
                bt.path || '/' || child.id AS path
            FROM bom_tree bt
            JOIN bill_of_materials bom ON bt.component_id = bom.parent_product_id
            JOIN products child ON bom.child_product_id = child.id
            WHERE bt.level < 10  -- Prevent infinite recursion
              AND INSTR(bt.path, child.id) = 0  -- Prevent cycles
        )
        SELECT * FROM bom_tree
    """)
