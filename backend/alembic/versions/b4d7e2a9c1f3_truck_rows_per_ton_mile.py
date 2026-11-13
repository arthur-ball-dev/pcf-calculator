"""catalog truck rows in tkm use the per-ton-mile truck factor

The catalog's "Transport - Truck" rows are measured in tkm but were linked to EPA's
"Transport - Medium- and Heavy-Duty Truck" factor per vehicle-mile (distance driven), which a
freight quantity can't be converted to. EPA's per-short-ton-mile truck factor is also loaded;
point the rows at it (#195 follow-up; the factor mapper now prefers a factor of a compatible
unit, so a fresh catalog load gets this right too).

Revision ID: b4d7e2a9c1f3
Revises: 7d3e1f9a2b4c
Create Date: 2026-11-12 22:30:00

"""
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection


# revision identifiers, used by Alembic.
revision: str = 'b4d7e2a9c1f3'
down_revision: Union[str, None] = '7d3e1f9a2b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TRUCK = '%Medium- and Heavy-Duty Truck%'


def _truck_factor(bind: Connection, unit: str) -> Optional[str]:
    return bind.execute(
        sa.text(
            "SELECT id FROM emission_factors "
            "WHERE unit = :unit AND activity_name ILIKE :truck "
            "ORDER BY length(activity_name), id LIMIT 1"
        ),
        {"unit": unit, "truck": _TRUCK},
    ).scalar()


def move_truck_rows_to_ton_mile(bind: Connection) -> int:
    """Point tkm rows linked to a per-vehicle-mile truck factor at the per-ton-mile one."""
    ton_mile = _truck_factor(bind, "short ton-mile")
    if ton_mile is None:
        return 0
    result = bind.execute(
        sa.text(
            "UPDATE bill_of_materials SET emission_factor_id = :ton_mile "
            "WHERE lower(unit) = 'tkm' AND emission_factor_id IN ("
            "  SELECT id FROM emission_factors "
            "  WHERE unit = 'vehicle-mile' AND activity_name ILIKE :truck)"
        ),
        {"ton_mile": ton_mile, "truck": _TRUCK},
    )
    return result.rowcount


def move_truck_rows_to_vehicle_mile(bind: Connection) -> int:
    """Reverse of move_truck_rows_to_ton_mile."""
    ton_mile = _truck_factor(bind, "short ton-mile")
    vehicle_mile = _truck_factor(bind, "vehicle-mile")
    if ton_mile is None or vehicle_mile is None:
        return 0
    result = bind.execute(
        sa.text(
            "UPDATE bill_of_materials SET emission_factor_id = :vehicle_mile "
            "WHERE lower(unit) = 'tkm' AND emission_factor_id = :ton_mile"
        ),
        {"vehicle_mile": vehicle_mile, "ton_mile": ton_mile},
    )
    return result.rowcount


def upgrade() -> None:
    move_truck_rows_to_ton_mile(op.get_bind())


def downgrade() -> None:
    move_truck_rows_to_vehicle_mile(op.get_bind())
