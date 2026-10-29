"""add_unit_normalization_columns

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-05 11:00:00.000000

Adds unit normalization audit columns to emission_factors table and
migrates existing tonne-based factors to kg for consistent calculations.

Columns added:
- original_unit: Original unit before normalization
- original_co2e_factor: Original factor value before conversion
- conversion_factor: Multiplier applied (e.g., 0.001 for tonnes->kg)
- normalized_at: Timestamp when normalization was applied

The migration also normalizes existing tonne-based emission factors to kg
to prevent 1000x calculation errors when BOM quantities (in kg) are
multiplied by per-tonne emission factors.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unit normalization columns and migrate existing tonne-based factors."""
    # Add new columns for unit normalization audit trail
    op.add_column(
        'emission_factors',
        sa.Column('original_unit', sa.String(50), nullable=True)
    )
    op.add_column(
        'emission_factors',
        sa.Column('original_co2e_factor', sa.DECIMAL(15, 8), nullable=True)
    )
    op.add_column(
        'emission_factors',
        sa.Column('conversion_factor', sa.DECIMAL(15, 8), nullable=True, default=1.0)
    )
    op.add_column(
        'emission_factors',
        sa.Column('normalized_at', sa.DateTime(), nullable=True)
    )

    # Migrate existing tonne-based emission factors to kg
    # This fixes the 1000x calculation error for DEFRA and other sources
    # that report factors in kg CO2e per tonne
    op.execute("""
        UPDATE emission_factors
        SET original_unit = unit,
            original_co2e_factor = co2e_factor,
            conversion_factor = 0.001,
            normalized_at = NOW(),
            co2e_factor = co2e_factor * 0.001,
            unit = 'kg'
        WHERE LOWER(unit) IN ('tonnes', 'tonne', 't', 'metric ton', 'metric tons')
    """)

    # Set default conversion_factor for non-normalized factors
    op.execute("""
        UPDATE emission_factors
        SET conversion_factor = 1.0
        WHERE conversion_factor IS NULL
    """)


def downgrade() -> None:
    """Remove unit normalization columns and restore original values."""
    # Restore original values for factors that were normalized
    op.execute("""
        UPDATE emission_factors
        SET co2e_factor = original_co2e_factor,
            unit = original_unit
        WHERE original_co2e_factor IS NOT NULL
    """)

    # Drop the columns
    op.drop_column('emission_factors', 'normalized_at')
    op.drop_column('emission_factors', 'conversion_factor')
    op.drop_column('emission_factors', 'original_co2e_factor')
    op.drop_column('emission_factors', 'original_unit')
