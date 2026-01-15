# E2E Test Database Configuration

This document explains how to configure and run E2E tests against an isolated PostgreSQL test database (`pcf_calculator_test`).

## Overview

E2E tests should run against a dedicated test database to:
- Prevent pollution of development data
- Ensure reproducible test results
- Allow parallel development and testing

## Test Database

| Property | Value |
|----------|-------|
| Database | `pcf_calculator_test` |
| User | `pcf_user` |
| Password | `DB_PASSWORD` |
| Host | `localhost` |
| Port | `5432` |

**Connection URL:**
```
postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
```

## Prerequisites

1. PostgreSQL running (via Docker or local installation)
2. Python virtual environment activated
3. Backend dependencies installed

## Quick Start

### Option 1: Automated Setup and Run

```bash
# From frontend directory
npm run test:e2e:isolated
```

This command:
1. Runs `backend/scripts/setup_test_db.py` to create/reset the test database
2. Seeds required data (users, products, emission factors)
3. Runs Playwright E2E tests

### Option 2: Manual Setup

```bash
# 1. Setup test database (from frontend directory)
npm run test:e2e:setup

# 2. Start backend with test database (in a separate terminal)
export DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
cd ../backend
source ../.venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Start frontend (in a separate terminal)
cd frontend
npm run dev

# 4. Run E2E tests (in a separate terminal)
cd frontend
npm run test:e2e
```

## NPM Scripts

| Script | Description |
|--------|-------------|
| `test:e2e` | Run E2E tests (uses whatever DB the backend is configured with) |
| `test:e2e:ui` | Run E2E tests with interactive Playwright UI |
| `test:e2e:setup` | Setup/reset the test database only |
| `test:e2e:isolated` | Setup test DB and run tests with test DB URL |
| `test:e2e:report` | Show HTML test report |

## Environment Variables

### Backend (required for isolated testing)

Set `DATABASE_URL` to the test database when starting the backend:

```bash
export DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
```

### Frontend

The frontend `.env` file should have:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

## Test Data

The setup script (`backend/scripts/setup_test_db.py`) seeds:

1. **Data Sources**: EPA, DEFRA metadata
2. **Data Source Licenses**: License information for attribution
3. **E2E Test User**:
   - Username: `e2e-test`
   - Password: `E2ETestPassword123!`
4. **Sample Products**: Test products with BOMs for E2E scenarios

## Resetting the Database

To completely reset the test database:

```bash
python ../backend/scripts/setup_test_db.py --reset
```

This drops all tables and recreates them with fresh seed data.

## Verifying Setup

To verify the test database is correctly configured:

```bash
python ../backend/scripts/setup_test_db.py --verify-only
```

## Troubleshooting

### Connection Refused

Ensure PostgreSQL is running:
```bash
docker-compose up -d postgres
# or check local PostgreSQL service
```

### Authentication Failed

Ensure the test user exists. The setup script creates the database user if it doesn't exist:
```bash
# Check if database exists
psql -U postgres -c "\l" | grep pcf_calculator_test
```

### E2E Test User Not Found

Run the setup script to seed the E2E test user:
```bash
npm run test:e2e:setup
```

### Backend Not Using Test Database

Verify the `DATABASE_URL` environment variable is set before starting the backend:
```bash
echo $DATABASE_URL
# Should show: postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
```

## CI/CD Integration

For CI/CD pipelines, use the following workflow:

```yaml
- name: Setup test database
  run: |
    cd frontend
    npm run test:e2e:setup

- name: Start backend with test database
  run: |
    export DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    sleep 5  # Wait for backend to start

- name: Run E2E tests
  run: |
    cd frontend
    npm run test:e2e
```

## Related Files

- `frontend/playwright.config.ts` - Playwright configuration with test DB documentation
- `backend/scripts/setup_test_db.py` - Test database setup script
- `frontend/tests/e2e/global-setup.ts` - E2E authentication setup
