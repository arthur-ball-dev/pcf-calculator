"""add_license_fields_to_data_sources

Revision ID: a1b2c3d4e5f6
Revises: f8a9b0c1d2e3
Create Date: 2025-12-17 21:00:00.000000

Add license and attribution fields to data_sources table for compliance
with EPA (Public Domain), DEFRA (OGL-3.0), and Exiobase (CC-BY-SA-4.0) terms.

Notes:
- Boolean server_default uses 'true'/'false' for PostgreSQL, '1'/'0' for SQLite
- UPDATE statements use TRUE/FALSE for PostgreSQL, 1/0 for SQLite
"""
from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_postgresql() -> bool:
    """Check if the current database is PostgreSQL."""
    return op.get_bind().dialect.name == 'postgresql'


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def get_boolean_server_default(value: bool) -> str:
    """Get the appropriate boolean server default for the current dialect."""
    if is_postgresql():
        return 'true' if value else 'false'
    return '1' if value else '0'


def upgrade() -> None:
    """Add license and attribution fields to data_sources table."""
    dialect = context.get_context().dialect.name

    # Get dialect-specific boolean defaults
    default_true = get_boolean_server_default(True)
    default_false = get_boolean_server_default(False)

    columns_to_add = [
        ('license_type', sa.Column('license_type', sa.String(100), nullable=True)),
        ('license_url', sa.Column('license_url', sa.Text(), nullable=True)),
        ('attribution_text', sa.Column('attribution_text', sa.Text(), nullable=True)),
        ('attribution_url', sa.Column('attribution_url', sa.Text(), nullable=True)),
        ('allows_commercial_use', sa.Column('allows_commercial_use', sa.Boolean(), server_default=default_true)),
        ('requires_attribution', sa.Column('requires_attribution', sa.Boolean(), server_default=default_false)),
        ('requires_share_alike', sa.Column('requires_share_alike', sa.Boolean(), server_default=default_false)),
    ]

    for col_name, col_def in columns_to_add:
        if not column_exists('data_sources', col_name):
            with op.batch_alter_table('data_sources', schema=None) as batch_op:
                batch_op.add_column(col_def)

    # Update existing data sources with proper attribution info
    # Use dialect-aware boolean values
    if dialect == 'postgresql':
        # PostgreSQL: use TRUE/FALSE
        op.execute("""
            UPDATE data_sources
            SET license_type = 'Public Domain',
                license_url = 'https://www.epa.gov/web-policies-and-procedures/epa-disclaimers',
                attribution_text = 'Data source: U.S. Environmental Protection Agency (EPA) GHG Emission Factors Hub',
                attribution_url = 'https://www.epa.gov/climateleadership/ghg-emission-factors-hub',
                allows_commercial_use = TRUE,
                requires_attribution = FALSE,
                requires_share_alike = FALSE
            WHERE LOWER(name) LIKE '%epa%'
        """)

        op.execute("""
            UPDATE data_sources
            SET license_type = 'Open Government Licence v3.0',
                license_url = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
                attribution_text = 'Contains public sector information licensed under the Open Government Licence v3.0. Source: UK Department for Energy Security and Net Zero (DESNZ) / DEFRA Greenhouse Gas Conversion Factors.',
                attribution_url = 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024',
                allows_commercial_use = TRUE,
                requires_attribution = TRUE,
                requires_share_alike = FALSE
            WHERE LOWER(name) LIKE '%defra%' OR LOWER(name) LIKE '%desnz%' OR LOWER(name) LIKE '%uk%gov%'
        """)

        op.execute("""
            UPDATE data_sources
            SET license_type = 'CC-BY-SA-4.0',
                license_url = 'https://creativecommons.org/licenses/by-sa/4.0/',
                attribution_text = 'EXIOBASE 3 data is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). Credit: EXIOBASE Consortium.',
                attribution_url = 'https://zenodo.org/records/5589597',
                allows_commercial_use = TRUE,
                requires_attribution = TRUE,
                requires_share_alike = TRUE
            WHERE LOWER(name) LIKE '%exiobase%' OR LOWER(name) LIKE '%exio%'
        """)
    else:
        # SQLite: use 1/0
        op.execute("""
            UPDATE data_sources
            SET license_type = 'Public Domain',
                license_url = 'https://www.epa.gov/web-policies-and-procedures/epa-disclaimers',
                attribution_text = 'Data source: U.S. Environmental Protection Agency (EPA) GHG Emission Factors Hub',
                attribution_url = 'https://www.epa.gov/climateleadership/ghg-emission-factors-hub',
                allows_commercial_use = 1,
                requires_attribution = 0,
                requires_share_alike = 0
            WHERE LOWER(name) LIKE '%epa%'
        """)

        op.execute("""
            UPDATE data_sources
            SET license_type = 'Open Government Licence v3.0',
                license_url = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
                attribution_text = 'Contains public sector information licensed under the Open Government Licence v3.0. Source: UK Department for Energy Security and Net Zero (DESNZ) / DEFRA Greenhouse Gas Conversion Factors.',
                attribution_url = 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024',
                allows_commercial_use = 1,
                requires_attribution = 1,
                requires_share_alike = 0
            WHERE LOWER(name) LIKE '%defra%' OR LOWER(name) LIKE '%desnz%' OR LOWER(name) LIKE '%uk%gov%'
        """)

        op.execute("""
            UPDATE data_sources
            SET license_type = 'CC-BY-SA-4.0',
                license_url = 'https://creativecommons.org/licenses/by-sa/4.0/',
                attribution_text = 'EXIOBASE 3 data is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). Credit: EXIOBASE Consortium.',
                attribution_url = 'https://zenodo.org/records/5589597',
                allows_commercial_use = 1,
                requires_attribution = 1,
                requires_share_alike = 1
            WHERE LOWER(name) LIKE '%exiobase%' OR LOWER(name) LIKE '%exio%'
        """)


def downgrade() -> None:
    """Remove license and attribution fields from data_sources table."""
    columns_to_drop = [
        'license_type',
        'license_url',
        'attribution_text',
        'attribution_url',
        'allows_commercial_use',
        'requires_attribution',
        'requires_share_alike',
    ]

    with op.batch_alter_table('data_sources', schema=None) as batch_op:
        for col_name in columns_to_drop:
            if column_exists('data_sources', col_name):
                batch_op.drop_column(col_name)
