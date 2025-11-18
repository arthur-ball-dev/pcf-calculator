-- ============================================================================
-- PCF Calculator MVP - SQLite Database Schema
-- ============================================================================
-- Version: 1.0
-- Created: 2025-10-23
-- Database: SQLite 3.35+
-- Description: Complete schema for Product Carbon Footprint calculation system
--              with support for hierarchical BOMs, emission factors, and
--              calculation audit trails.
-- ============================================================================

-- Enable foreign key constraints (critical for SQLite)
PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABLE: products
-- ============================================================================
-- Stores all products and components in a flat structure.
-- Supports finished products, sub-assemblies, and raw materials.
-- ============================================================================

CREATE TABLE products (
    -- Primary identifier (auto-generated UUID-like hex string)
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Unique product code (e.g., 'TSHIRT-001', 'COTTON-FABRIC-001')
    code VARCHAR(100) UNIQUE NOT NULL,

    -- Display name
    name VARCHAR(255) NOT NULL,

    -- Optional detailed description
    description TEXT,

    -- Unit of measure (restricted to standard units)
    unit VARCHAR(20) DEFAULT 'unit',

    -- Product category for filtering/grouping
    category VARCHAR(100),

    -- Flag to identify finished products vs components
    is_finished_product BOOLEAN DEFAULT 0,

    -- Extensible JSON metadata field
    metadata JSON,

    -- Audit timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,  -- Soft delete support

    -- CHECK constraint: unit must be from allowed list
    CHECK (unit IN ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ'))
);

-- Indexes for products table
CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_finished ON products(is_finished_product);

-- ============================================================================
-- TABLE: emission_factors
-- ============================================================================
-- Central repository of CO2e emission factors from various data sources.
-- Supports multiple sources, geographies, and temporal validity.
-- ============================================================================

CREATE TABLE emission_factors (
    -- Primary identifier
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Activity or material name (e.g., 'Cotton Fabric', 'Electricity')
    activity_name VARCHAR(255) NOT NULL,

    -- CO2 equivalent emission factor (kg CO2e per unit)
    co2e_factor DECIMAL(15,8) NOT NULL,

    -- Unit of measurement for the factor
    unit VARCHAR(20) NOT NULL,

    -- Data source (e.g., 'EPA', 'DEFRA', 'Ecoinvent')
    data_source VARCHAR(100) NOT NULL,

    -- Geographic scope (e.g., 'GLO', 'US', 'EU')
    geography VARCHAR(50) DEFAULT 'GLO',

    -- Reference year for the data
    reference_year INTEGER,

    -- Data quality rating (0.0 to 1.0)
    data_quality_rating DECIMAL(3,2),

    -- Uncertainty range
    uncertainty_min DECIMAL(15,8),
    uncertainty_max DECIMAL(15,8),

    -- Extensible JSON metadata
    metadata JSON,

    -- Temporal validity
    valid_from DATE,
    valid_to DATE,

    -- Audit timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Composite unique constraint: prevent duplicate entries for same activity/source/geography/year
    UNIQUE(activity_name, data_source, geography, reference_year),

    -- CHECK constraint: emission factor must be non-negative
    CHECK (co2e_factor >= 0)
);

-- Indexes for emission_factors table
CREATE INDEX idx_ef_activity ON emission_factors(activity_name);
CREATE INDEX idx_ef_geography ON emission_factors(geography);
CREATE INDEX idx_ef_source ON emission_factors(data_source);

-- ============================================================================
-- TABLE: bill_of_materials
-- ============================================================================
-- Defines parent-child relationships between products (BOM structure).
-- Supports hierarchical product composition with quantity tracking.
-- ============================================================================

CREATE TABLE bill_of_materials (
    -- Primary identifier
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Parent product (assembly or finished product)
    parent_product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

    -- Child product (component or sub-assembly)
    child_product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

    -- Quantity of child needed per unit of parent
    quantity DECIMAL(15,6) NOT NULL,

    -- Unit of measurement for quantity
    unit VARCHAR(20),

    -- Optional notes
    notes TEXT,

    -- Audit timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate parent-child pairs
    UNIQUE(parent_product_id, child_product_id),

    -- CHECK constraints
    CHECK (parent_product_id != child_product_id),  -- Prevent self-reference
    CHECK (quantity > 0)  -- Quantity must be positive (not zero or negative)
);

-- Indexes for bill_of_materials table
CREATE INDEX idx_bom_parent ON bill_of_materials(parent_product_id);
CREATE INDEX idx_bom_child ON bill_of_materials(child_product_id);

-- ============================================================================
-- TABLE: pcf_calculations
-- ============================================================================
-- Stores PCF calculation results and metadata.
-- Supports different calculation types and detailed emissions breakdown.
-- ============================================================================

CREATE TABLE pcf_calculations (
    -- Primary identifier
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Product being calculated
    product_id TEXT NOT NULL REFERENCES products(id),

    -- Type of LCA boundary
    calculation_type VARCHAR(50) DEFAULT 'cradle_to_gate',

    -- Total emissions result
    total_co2e_kg DECIMAL(15,6) NOT NULL,

    -- Emissions breakdown by category
    materials_co2e DECIMAL(15,6),
    energy_co2e DECIMAL(15,6),
    transport_co2e DECIMAL(15,6),
    waste_co2e DECIMAL(15,6),

    -- Data quality metrics
    primary_data_share DECIMAL(5,2),  -- Percentage of primary data
    data_quality_score DECIMAL(3,2),   -- Overall quality score (0-1)

    -- Calculation metadata
    calculation_method VARCHAR(100),   -- e.g., 'brightway2', 'direct'
    status VARCHAR(50) DEFAULT 'completed',

    -- JSON fields for extensibility
    input_data JSON,       -- Original input data
    breakdown JSON,        -- Detailed breakdown
    metadata JSON,         -- Additional metadata

    -- Audit fields
    calculated_by VARCHAR(100),
    calculation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- CHECK constraint: calculation_type must be valid
    CHECK (calculation_type IN ('cradle_to_gate', 'cradle_to_grave', 'gate_to_gate'))
);

-- Indexes for pcf_calculations table
CREATE INDEX idx_calc_product ON pcf_calculations(product_id);
CREATE INDEX idx_calc_date ON pcf_calculations(created_at);
CREATE INDEX idx_calc_status ON pcf_calculations(status);

-- ============================================================================
-- TABLE: calculation_details
-- ============================================================================
-- Detailed breakdown of emissions by component for traceability.
-- Links to both calculations and emission factors for full audit trail.
-- ============================================================================

CREATE TABLE calculation_details (
    -- Primary identifier
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Parent calculation
    calculation_id TEXT NOT NULL REFERENCES pcf_calculations(id) ON DELETE CASCADE,

    -- Component reference (optional, may be NULL for virtual components)
    component_id TEXT REFERENCES products(id),

    -- Component name (denormalized for historical tracking)
    component_name VARCHAR(255) NOT NULL,

    -- Level in BOM hierarchy (0 = root)
    component_level INTEGER DEFAULT 0,

    -- Quantity used
    quantity DECIMAL(15,6),
    unit VARCHAR(20),

    -- Emission factor used
    emission_factor_id TEXT REFERENCES emission_factors(id),

    -- Calculated emissions for this component
    emissions_kg_co2e DECIMAL(15,6),

    -- Data quality indicator
    data_quality VARCHAR(50),

    -- Notes
    notes TEXT,

    -- Audit timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for calculation_details table
CREATE INDEX idx_detail_calc ON calculation_details(calculation_id);
CREATE INDEX idx_detail_component ON calculation_details(component_id);

-- ============================================================================
-- VIEW: v_bom_explosion
-- ============================================================================
-- Recursive CTE view for BOM explosion with calculated cumulative quantities.
-- Includes cycle detection and depth limiting to prevent infinite recursion.
-- ============================================================================

CREATE VIEW v_bom_explosion AS
WITH RECURSIVE bom_tree AS (
    -- Base case: Start with all finished products
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
    WHERE p.is_finished_product = 1

    UNION ALL

    -- Recursive case: Traverse BOM hierarchy
    SELECT
        bt.root_id,
        bt.root_name,
        child.id AS component_id,
        child.name AS component_name,
        bt.level + 1,
        bt.cumulative_quantity * bom.quantity AS cumulative_quantity,
        COALESCE(bom.unit, child.unit) AS unit,
        bt.path || '/' || child.id AS path
    FROM bom_tree bt
    JOIN bill_of_materials bom ON bt.component_id = bom.parent_product_id
    JOIN products child ON bom.child_product_id = child.id
    WHERE bt.level + 1 < 10  -- Prevent infinite recursion (max 10 levels: 0-9)
      AND INSTR(bt.path, '/' || child.id) = 0  -- Prevent cycles
)
SELECT
    root_id,
    root_name,
    component_id,
    component_name,
    level,
    cumulative_quantity,
    unit,
    path
FROM bom_tree
ORDER BY root_id, level, component_name;

-- ============================================================================
-- VIEW: v_product_pcf
-- ============================================================================
-- Helper view to calculate PCF directly from BOM explosion and emission factors.
-- Useful for quick calculations without running full Brightway2 analysis.
-- ============================================================================

CREATE VIEW v_product_pcf AS
SELECT
    be.root_id AS product_id,
    be.root_name AS product_name,
    SUM(be.cumulative_quantity * COALESCE(ef.co2e_factor, 0)) AS total_co2e_kg,
    COUNT(DISTINCT be.component_id) AS component_count,
    AVG(ef.data_quality_rating) AS avg_data_quality
FROM v_bom_explosion be
LEFT JOIN emission_factors ef
    ON be.component_name = ef.activity_name
    AND (ef.valid_from IS NULL OR ef.valid_from <= DATE('now'))
    AND (ef.valid_to IS NULL OR ef.valid_to >= DATE('now'))
GROUP BY be.root_id, be.root_name;

-- ============================================================================
-- VIEW: v_data_quality_metrics
-- ============================================================================
-- Analyzes data quality and completeness for products.
-- Shows percentage of components with emission factors.
-- ============================================================================

CREATE VIEW v_data_quality_metrics AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    COUNT(CASE WHEN ef.id IS NOT NULL THEN 1 END) AS components_with_factors,
    COUNT(*) AS total_components,
    ROUND(COUNT(CASE WHEN ef.id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) AS completeness_percent,
    AVG(ef.data_quality_rating) AS average_quality_score
FROM products p
LEFT JOIN v_bom_explosion be ON p.id = be.root_id
LEFT JOIN emission_factors ef ON be.component_name = ef.activity_name
WHERE p.is_finished_product = 1
GROUP BY p.id, p.name;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
