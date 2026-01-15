-- =============================================================================
-- PCF Calculator - E2E Test Database Initialization
-- =============================================================================
-- TASK-DB-P9-007: Setup Dedicated PostgreSQL Test Database for E2E Tests
--
-- This script runs automatically when PostgreSQL container starts for the
-- first time. It creates the dedicated test database for E2E testing.
--
-- Purpose:
-- - Create pcf_calculator_test database for E2E test isolation
-- - Grant necessary permissions to the default user
-- - Enable required extensions in the test database
--
-- Note: Schema migrations must be run separately via Alembic:
--   DATABASE_URL=postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test \
--   alembic upgrade head
--
-- Or use the setup script:
--   python backend/scripts/setup_test_db.py
-- =============================================================================

-- Create E2E test database if it doesn't exist
-- This uses the DO block to conditionally create the database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pcf_calculator_test') THEN
        PERFORM dblink_exec(
            'dbname=' || current_database(),
            'CREATE DATABASE pcf_calculator_test'
        );
        RAISE NOTICE 'Created database: pcf_calculator_test';
    ELSE
        RAISE NOTICE 'Database pcf_calculator_test already exists';
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- If dblink is not available, we'll use a different approach
    -- The setup_test_db.py script handles this case
    RAISE NOTICE 'Could not auto-create test database: %. Use setup_test_db.py script.', SQLERRM;
END
$$;

-- Grant permissions to the default user (if database was just created)
-- Note: This grant will succeed even if the database doesn't exist yet
-- because PostgreSQL defers permission checks
DO $$
BEGIN
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE pcf_calculator_test TO %I', current_user);
    RAISE NOTICE 'Granted privileges on pcf_calculator_test to %', current_user;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not grant privileges (database may not exist yet): %', SQLERRM;
END
$$;

-- Note: Extensions need to be created after connecting to the test database
-- This is handled by the setup_test_db.py script which:
-- 1. Creates the database
-- 2. Connects to it
-- 3. Runs alembic migrations (which handle extensions)

-- Output completion message
DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'PCF Calculator E2E Test Database Initialization Complete';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps to complete test database setup:';
    RAISE NOTICE '  1. Run: python backend/scripts/setup_test_db.py';
    RAISE NOTICE '  2. This will:';
    RAISE NOTICE '     - Create pcf_calculator_test database (if not created above)';
    RAISE NOTICE '     - Run Alembic migrations';
    RAISE NOTICE '     - Seed required data (EPA/DEFRA sources, E2E test user)';
    RAISE NOTICE '';
    RAISE NOTICE 'To run E2E tests with this database:';
    RAISE NOTICE '  export DATABASE_URL=postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test';
    RAISE NOTICE '  cd frontend && npm run test:e2e';
    RAISE NOTICE '';
END
$$;
