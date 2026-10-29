"""limit v_bom_explosion view to 10 levels (0-9)

The original schema.sql view stopped recursing with `bt.level + 1 < 10`
(max 10 levels: 0-9, matching MAX_BOM_DEPTH = 10). The Alembic versions use
`bt.level < 10`, which also emits level 10 (11 levels). Restore the original limit.

Revision ID: 5c754d1c1305
Revises: 527b7d06729d
Create Date: 2026-10-20 18:28:39

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5c754d1c1305'
down_revision: Union[str, None] = '527b7d06729d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VIEW_SQL = """
    CREATE OR REPLACE VIEW v_bom_explosion AS
    WITH RECURSIVE bom_tree AS (
        -- Base case: Finished products
        SELECT
            p.id AS root_id,
            p.name AS root_name,
            p.id AS component_id,
            p.name AS component_name,
            0 AS level,
            1.0 AS cumulative_quantity,
            p.unit,
            CAST(p.id AS TEXT) AS path
        FROM products p
        WHERE p.is_finished_product = TRUE

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
            bt.path || '/' || CAST(child.id AS TEXT) AS path
        FROM bom_tree bt
        JOIN bill_of_materials bom ON bt.component_id = bom.parent_product_id
        JOIN products child ON bom.child_product_id = child.id
        WHERE {depth_limit}  -- Prevent infinite recursion
          AND POSITION(child.id IN bt.path) = 0  -- Prevent cycles
    )
    SELECT * FROM bom_tree
"""


def upgrade() -> None:
    op.execute(VIEW_SQL.format(depth_limit="bt.level + 1 < 10"))


def downgrade() -> None:
    op.execute(VIEW_SQL.format(depth_limit="bt.level < 10"))
