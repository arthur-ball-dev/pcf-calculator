"""Add compliance tracking tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-08

TASK-DB-P8-002: Compliance Tracking Schema (License & Provenance Tables)

This migration creates:
1. data_source_licenses - License information for each data source
2. emission_factor_provenance - Provenance tracking for emission factors

These tables enable:
- License compliance verification
- Attribution display requirements
- Audit trail for data lineage
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    """Create compliance tracking tables."""

    # Create data_source_licenses table
    if not table_exists('data_source_licenses'):
        op.create_table(
            'data_source_licenses',
            # Primary key
            sa.Column('id', sa.String(32), primary_key=True),

            # Foreign key to data_sources
            sa.Column(
                'data_source_id',
                sa.String(32),
                sa.ForeignKey('data_sources.id', ondelete='CASCADE'),
                nullable=False
            ),

            # License information
            sa.Column('license_type', sa.String(50), nullable=False),
            sa.Column('license_url', sa.String(500), nullable=True),

            # Attribution requirements
            sa.Column('attribution_required', sa.Boolean, default=False, nullable=False),
            sa.Column('attribution_statement', sa.Text, nullable=True),

            # Usage permissions
            sa.Column('commercial_use_allowed', sa.Boolean, default=True, nullable=False),
            sa.Column('sharealike_required', sa.Boolean, default=False, nullable=False),

            # Additional fields
            sa.Column('additional_restrictions', sa.Text, nullable=True),
            sa.Column('license_version', sa.String(20), nullable=True),
            sa.Column('effective_date', sa.Date, nullable=True),

            # Timestamps
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
        )

        # Create index on data_source_id
        op.create_index(
            'ix_data_source_licenses_data_source_id',
            'data_source_licenses',
            ['data_source_id']
        )

    # Create emission_factor_provenance table
    if not table_exists('emission_factor_provenance'):
        op.create_table(
            'emission_factor_provenance',
            # Primary key
            sa.Column('id', sa.String(32), primary_key=True),

            # Foreign key to emission_factors (CASCADE delete)
            sa.Column(
                'emission_factor_id',
                sa.String(32),
                sa.ForeignKey('emission_factors.id', ondelete='CASCADE'),
                nullable=False
            ),

            # Foreign key to data_source_licenses (SET NULL on delete)
            sa.Column(
                'data_source_license_id',
                sa.String(32),
                sa.ForeignKey('data_source_licenses.id', ondelete='SET NULL'),
                nullable=True
            ),

            # Source reference
            sa.Column('source_document', sa.String(500), nullable=True),
            sa.Column('source_row_reference', sa.String(100), nullable=True),

            # Ingestion tracking
            sa.Column('ingestion_date', sa.DateTime, nullable=True),

            # Compliance verification
            sa.Column('license_compliance_verified', sa.Boolean, default=False, nullable=False),
            sa.Column('verification_notes', sa.Text, nullable=True),
            sa.Column('verified_by', sa.String(100), nullable=True),
            sa.Column('verified_at', sa.DateTime, nullable=True),

            # Timestamp
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

        # Create indexes
        op.create_index(
            'ix_emission_factor_provenance_emission_factor_id',
            'emission_factor_provenance',
            ['emission_factor_id']
        )

        op.create_index(
            'ix_emission_factor_provenance_license_id',
            'emission_factor_provenance',
            ['data_source_license_id']
        )


def downgrade() -> None:
    """Drop compliance tracking tables."""

    # Drop emission_factor_provenance indexes and table
    if table_exists('emission_factor_provenance'):
        if index_exists('emission_factor_provenance', 'ix_emission_factor_provenance_license_id'):
            op.drop_index('ix_emission_factor_provenance_license_id', table_name='emission_factor_provenance')
        if index_exists('emission_factor_provenance', 'ix_emission_factor_provenance_emission_factor_id'):
            op.drop_index('ix_emission_factor_provenance_emission_factor_id', table_name='emission_factor_provenance')
        op.drop_table('emission_factor_provenance')

    # Drop data_source_licenses index and table
    if table_exists('data_source_licenses'):
        if index_exists('data_source_licenses', 'ix_data_source_licenses_data_source_id'):
            op.drop_index('ix_data_source_licenses_data_source_id', table_name='data_source_licenses')
        op.drop_table('data_source_licenses')
