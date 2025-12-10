"""
Database models module
Contains SQLAlchemy ORM models for PCF Calculator

All models match the schema defined in backend/database/schema.sql

TASK-DB-P5-002: Extended with DataSource, ProductCategory, DataSyncLog
and additional columns for full-text search and data lineage.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DECIMAL,
    TEXT,
    DateTime,
    Date,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import Base and generate_uuid from base module to avoid circular imports
from backend.models.base import Base, generate_uuid


class Product(Base):
    """
    Product model - Stores all products and components

    Represents finished products, sub-assemblies, and raw materials
    in a flat structure. Hierarchical relationships are defined
    through BillOfMaterials.

    Phase 5 Extensions:
    - category_id: FK to ProductCategory for hierarchical categorization
    - manufacturer: Product manufacturer name
    - country_of_origin: ISO 3166-1 alpha-2 country code
    - search_vector: Full-text search (TSVECTOR in PostgreSQL)
    """
    __tablename__ = "products"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Unique product code
    code = Column(String(100), unique=True, nullable=False)

    # Display name
    name = Column(String(255), nullable=False)

    # Optional description
    description = Column(TEXT, nullable=True)

    # Unit of measure
    unit = Column(String(20), default='unit')

    # Product category (legacy string field)
    category = Column(String(100), nullable=True)

    # Flag for finished products vs components
    is_finished_product = Column(Boolean, default=False)

    # Extensible JSON metadata (store as product_metadata to avoid conflict)
    product_metadata = Column('metadata', JSON, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # === Phase 5 Extensions ===
    # Foreign key to ProductCategory for hierarchical categorization
    category_id = Column(
        String(32),
        ForeignKey('product_categories.id', ondelete='SET NULL'),
        nullable=True
    )

    # Product manufacturer name
    manufacturer = Column(String(255), nullable=True)

    # Country of origin (ISO 3166-1 alpha-2 code)
    country_of_origin = Column(String(50), nullable=True)

    # Full-text search vector (Text for SQLite, TSVECTOR for PostgreSQL)
    search_vector = Column(TEXT, nullable=True)

    # Relationships
    bom_items = relationship(
        "BillOfMaterials",
        foreign_keys="[BillOfMaterials.parent_product_id]",
        back_populates="parent_product",
        cascade="all, delete-orphan"
    )

    used_in_boms = relationship(
        "BillOfMaterials",
        foreign_keys="[BillOfMaterials.child_product_id]",
        back_populates="child_product"
    )

    calculations = relationship(
        "PCFCalculation",
        back_populates="product"
    )

    # Relationship to ProductCategory
    product_category = relationship(
        "ProductCategory",
        back_populates="products",
        foreign_keys=[category_id]
    )

    # Provide instance-level access via __getattribute__
    def __getattribute__(self, name):
        if name == 'metadata':
            return object.__getattribute__(self, 'product_metadata')
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'metadata':
            object.__setattr__(self, 'product_metadata', value)
        else:
            object.__setattr__(self, name, value)

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm')",
            name="ck_product_unit"
        ),
        Index('idx_products_category', 'category_id'),
        Index('idx_products_manufacturer', 'manufacturer'),
        # GIN index for search_vector would be added in PostgreSQL migration
    )

    def __repr__(self) -> str:
        return f"<Product(code='{self.code}', name='{self.name}')>"


class EmissionFactor(Base):
    """
    EmissionFactor model - CO2e emission factors from various sources

    Central repository of emission factors with support for multiple
    data sources, geographies, and temporal validity.

    Phase 5 Extensions:
    - data_source_id: FK to DataSource for lineage tracking
    - external_id: ID in the source system
    - sync_batch_id: UUID linking to DataSyncLog
    - is_active: Soft delete / active flag
    - scope: GHG Protocol scope (Scope 1, Scope 2, Scope 3)
    - search_vector: Full-text search (TSVECTOR in PostgreSQL)
    """
    __tablename__ = "emission_factors"

    # Primary key
    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Activity or material name
    activity_name = Column(String(255), nullable=False)

    # Category for filtering (material, energy, transport, other)
    category = Column(String(50), nullable=True)

    # CO2e emission factor (kg CO2e per unit)
    co2e_factor = Column(DECIMAL(15, 8), nullable=False)

    # Unit of measurement
    unit = Column(String(20), nullable=False)

    # Data source (legacy string field)
    data_source = Column(String(100), nullable=False)

    # Geographic scope
    geography = Column(String(50), default='GLO')

    # Reference year
    reference_year = Column(Integer, nullable=True)

    # Data quality rating (0.0 to 1.0)
    data_quality_rating = Column(DECIMAL(3, 2), nullable=True)

    # Uncertainty range
    uncertainty_min = Column(DECIMAL(15, 8), nullable=True)
    uncertainty_max = Column(DECIMAL(15, 8), nullable=True)

    # Extensible metadata
    emission_metadata = Column('metadata', JSON, nullable=True)

    # Temporal validity
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # === Phase 5 Extensions ===
    # Foreign key to DataSource for lineage tracking
    data_source_id = Column(
        String(32),
        ForeignKey('data_sources.id', ondelete='SET NULL'),
        nullable=True
    )

    # ID in the source system (e.g., EPA ID, DEFRA ID)
    external_id = Column(String(255), nullable=True)

    # UUID linking to sync batch (DataSyncLog)
    sync_batch_id = Column(String(32), nullable=True)

    # Active flag for soft delete
    is_active = Column(Boolean, default=True)

    # GHG Protocol scope classification
    # Values: "Scope 1" (direct), "Scope 2" (energy), "Scope 3" (indirect)
    scope = Column(String(20), nullable=True)

    # Full-text search vector (Text for SQLite, TSVECTOR for PostgreSQL)
    search_vector = Column(TEXT, nullable=True)

    # Relationships
    calculation_details = relationship(
        "CalculationDetail",
        back_populates="emission_factor"
    )

    # Relationship to DataSource
    data_source_ref = relationship(
        "DataSource",
        back_populates="emission_factors",
        foreign_keys=[data_source_id]
    )

    # Provide instance-level access
    def __getattribute__(self, name):
        if name == 'metadata':
            return object.__getattribute__(self, 'emission_metadata')
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'metadata':
            object.__setattr__(self, 'emission_metadata', value)
        else:
            object.__setattr__(self, name, value)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            'activity_name', 'data_source', 'geography', 'reference_year',
            name='uq_emission_factor_composite'
        ),
        CheckConstraint(
            'co2e_factor >= 0',
            name='ck_emission_factor_non_negative'
        ),
        Index('idx_ef_source', 'data_source_id'),
        Index('idx_ef_external', 'external_id'),
        Index('idx_ef_active', 'is_active'),
        Index('idx_ef_scope', 'scope'),
        # GIN index for search_vector would be added in PostgreSQL migration
    )

    def __repr__(self) -> str:
        return f"<EmissionFactor(activity='{self.activity_name}', factor={self.co2e_factor})>"


class BillOfMaterials(Base):
    """
    BillOfMaterials model - Parent-child product relationships

    Defines hierarchical product composition with quantity tracking.
    Supports BOM explosion through recursive queries.
    """
    __tablename__ = "bill_of_materials"

    # Primary key
    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Parent product (assembly)
    parent_product_id = Column(
        String(32),
        ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    # Child product (component)
    child_product_id = Column(
        String(32),
        ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    # Quantity of child per parent
    quantity = Column(DECIMAL(15, 6), nullable=False)

    # Unit of measurement
    unit = Column(String(20), nullable=True)

    # Optional notes
    notes = Column(TEXT, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    parent_product = relationship(
        "Product",
        foreign_keys=[parent_product_id],
        back_populates="bom_items"
    )

    child_product = relationship(
        "Product",
        foreign_keys=[child_product_id],
        back_populates="used_in_boms"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'parent_product_id', 'child_product_id',
            name='uq_bom_parent_child'
        ),
        CheckConstraint(
            'parent_product_id != child_product_id',
            name='ck_bom_no_self_reference'
        ),
        CheckConstraint(
            'quantity > 0',
            name='ck_bom_quantity_positive'
        ),
    )

    def __repr__(self) -> str:
        return f"<BOM(parent={self.parent_product_id}, child={self.child_product_id}, qty={self.quantity})>"


class PCFCalculation(Base):
    """
    PCFCalculation model - PCF calculation results and metadata

    Stores calculation results with detailed emissions breakdown
    and data quality metrics.
    """
    __tablename__ = "pcf_calculations"

    # Primary key
    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Product reference
    product_id = Column(
        String(32),
        ForeignKey('products.id'),
        nullable=False
    )

    # Calculation type
    calculation_type = Column(String(50), default='cradle_to_gate')

    # Total emissions
    total_co2e_kg = Column(DECIMAL(15, 6), nullable=False)

    # Emissions breakdown by category
    materials_co2e = Column(DECIMAL(15, 6), nullable=True)
    energy_co2e = Column(DECIMAL(15, 6), nullable=True)
    transport_co2e = Column(DECIMAL(15, 6), nullable=True)
    waste_co2e = Column(DECIMAL(15, 6), nullable=True)

    # Data quality metrics
    primary_data_share = Column(DECIMAL(5, 2), nullable=True)
    data_quality_score = Column(DECIMAL(3, 2), nullable=True)

    # Calculation metadata
    calculation_method = Column(String(100), nullable=True)
    status = Column(String(50), default='completed')

    # JSON fields
    input_data = Column(JSON, nullable=True)
    breakdown = Column(JSON, nullable=True)
    calculation_metadata = Column('metadata', JSON, nullable=True)

    # Audit fields
    calculated_by = Column(String(100), nullable=True)
    calculation_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    product = relationship(
        "Product",
        back_populates="calculations"
    )

    details = relationship(
        "CalculationDetail",
        back_populates="calculation",
        cascade="all, delete-orphan"
    )

    # Provide instance-level access
    def __getattribute__(self, name):
        if name == 'metadata':
            return object.__getattribute__(self, 'calculation_metadata')
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'metadata':
            object.__setattr__(self, 'calculation_metadata', value)
        else:
            object.__setattr__(self, name, value)

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "calculation_type IN ('cradle_to_gate', 'cradle_to_grave', 'gate_to_gate')",
            name='ck_calculation_type'
        ),
    )

    def __repr__(self) -> str:
        return f"<PCFCalculation(product_id={self.product_id}, total={self.total_co2e_kg})>"


class CalculationDetail(Base):
    """
    CalculationDetail model - Detailed emissions breakdown by component

    Provides full traceability for calculation results by storing
    emissions for each component in the BOM.
    """
    __tablename__ = "calculation_details"

    # Primary key
    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Parent calculation
    calculation_id = Column(
        String(32),
        ForeignKey('pcf_calculations.id', ondelete='CASCADE'),
        nullable=False
    )

    # Component reference (optional for virtual components)
    component_id = Column(
        String(32),
        ForeignKey('products.id'),
        nullable=True
    )

    # Component name (denormalized for history)
    component_name = Column(String(255), nullable=False)

    # Level in BOM hierarchy
    component_level = Column(Integer, default=0)

    # Quantity used
    quantity = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)

    # Emission factor used
    emission_factor_id = Column(
        String(32),
        ForeignKey('emission_factors.id'),
        nullable=True
    )

    # Calculated emissions
    emissions_kg_co2e = Column(DECIMAL(15, 6), nullable=True)

    # Data quality indicator
    data_quality = Column(String(50), nullable=True)

    # Notes
    notes = Column(TEXT, nullable=True)

    # Audit timestamp
    created_at = Column(DateTime, default=func.now())

    # Relationships
    calculation = relationship(
        "PCFCalculation",
        back_populates="details"
    )

    component = relationship(
        "Product",
        foreign_keys=[component_id]
    )

    emission_factor = relationship(
        "EmissionFactor",
        back_populates="calculation_details"
    )

    def __repr__(self) -> str:
        return f"<CalculationDetail(component='{self.component_name}', emissions={self.emissions_kg_co2e})>"


# Import Phase 5 models AFTER all base classes are defined
# This ensures SQLAlchemy can resolve string-based relationship references
from backend.models.data_source import DataSource
from backend.models.product_category import ProductCategory
from backend.models.data_sync_log import DataSyncLog

# Export all models
__all__ = [
    'Base',
    'generate_uuid',
    'Product',
    'EmissionFactor',
    'BillOfMaterials',
    'PCFCalculation',
    'CalculationDetail',
    # Phase 5 models
    'DataSource',
    'ProductCategory',
    'DataSyncLog',
]
