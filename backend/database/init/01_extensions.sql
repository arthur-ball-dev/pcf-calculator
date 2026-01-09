-- =============================================================================
-- PCF Calculator - PostgreSQL Extensions Initialization
-- =============================================================================
-- TASK-DB-P8-001: PostgreSQL Docker Infrastructure
--
-- This script runs automatically when PostgreSQL container starts for the
-- first time. It creates required extensions for the PCF Calculator.
--
-- Extensions:
-- - uuid-ossp: UUID generation functions (uuid_generate_v4())
-- - pg_trgm: Trigram matching for fuzzy text search (similarity())
--
-- Note: PostgreSQL 13+ includes gen_random_uuid() natively, but uuid-ossp
-- provides additional UUID generation options used in the application.
-- =============================================================================

-- Enable UUID generation extension
-- Used for: Primary key generation in all tables
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable trigram matching extension
-- Used for: Fuzzy text search on product names, descriptions, emission factors
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Verify extensions are installed
DO $$
BEGIN
    RAISE NOTICE 'PCF Calculator PostgreSQL extensions initialized successfully';
    RAISE NOTICE 'uuid-ossp: %', (SELECT extversion FROM pg_extension WHERE extname = 'uuid-ossp');
    RAISE NOTICE 'pg_trgm: %', (SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm');
END
$$;
