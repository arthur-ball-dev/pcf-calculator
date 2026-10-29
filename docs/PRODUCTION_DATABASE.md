# Production Database Setup Guide

## Overview

The PCF Calculator uses PostgreSQL as its primary database for all environments (development, testing, and production).
The application automatically detects the database configuration from the `DATABASE_URL` environment variable.

**Note:** SQLite is no longer used. All environments use PostgreSQL as of Phase 9 (2026-01-14).

## Database Environments

| Environment | Database | Connection String Format |
|-------------|----------|--------------------------|
| Development | PostgreSQL (Docker) | `postgresql://user:pass@localhost:5432/db` |
| Production | PostgreSQL (Railway) | `postgres://user:pass@host.railway.internal:5432/db` |
| Testing | PostgreSQL | `postgresql://user:pass@localhost:5432/pcf_calculator_test` |

**Note:** Both `postgres://` and `postgresql://` URL formats are supported. Railway uses `postgres://` which is automatically normalized to `postgresql+psycopg://` for SQLAlchemy compatibility.

## Quick Start

### Development (PostgreSQL via Docker)

```bash
# Start PostgreSQL container
docker compose up -d postgres

# Run migrations
cd backend && alembic upgrade head

# Seed data
python scripts/seed_data.py

# Start server
uvicorn main:app --reload
```

### Production (Railway PostgreSQL)

Railway automatically provisions and configures the PostgreSQL database. The `DATABASE_URL` is auto-injected into the environment.

```bash
# Railway provides DATABASE_URL automatically
# The app handles URL normalization (postgres:// to postgresql+psycopg://)
```

## PostgreSQL Setup

### Local PostgreSQL (Docker Compose)

The project includes a `docker-compose.yml` that configures PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: pcf_user
      POSTGRES_PASSWORD: DB_PASSWORD
      POSTGRES_DB: pcf_calculator
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/database/init:/docker-entrypoint-initdb.d
```

**Start the database:**
```bash
docker compose up -d postgres
```

### Test Database Setup

The application uses a separate test database (`pcf_calculator_test`) for E2E and integration tests.

**Automatic setup via script:**
```bash
cd backend
python scripts/setup_test_db.py
```

**Manual setup:**
```sql
-- Connect as postgres superuser
psql -U pcf_user -d pcf_calculator

-- Create test database
CREATE DATABASE pcf_calculator_test;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pcf_calculator_test TO pcf_user;
```

### Configure Environment

Create a `.env` file:

```bash
# Development
DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator

# Testing
TEST_DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
```

## Railway Deployment

[Railway](https://railway.app) provides simple, fast cloud deployment with built-in PostgreSQL.

**Production URL:** https://pcf.glideslopeintelligence.ai

### 1. Create Railway Project

1. Sign up at [railway.app](https://railway.app)
2. Create a new project from your GitHub repository
3. Railway auto-detects the Python/FastAPI application

### 2. Add PostgreSQL Service

1. In your Railway project, click "New Service" -> "Database" -> "PostgreSQL"
2. Railway automatically provisions a PostgreSQL 16 instance
3. The `DATABASE_URL` environment variable is auto-injected

### 3. URL Normalization

Railway provides `DATABASE_URL` in `postgres://` format:

```
postgres://user:password@host.railway.internal:5432/railway
```

The application automatically normalizes this to `postgresql+psycopg://` for SQLAlchemy compatibility:

```python
# In backend/database/connection.py
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
```

### 4. Environment Variables

Railway provides `DATABASE_URL` automatically. Add these additional variables:

```bash
# Required
PCF_CALC_JWT_SECRET_KEY=your-secure-32-character-secret-key

# Optional - CORS for frontend
CORS_ORIGINS=https://your-frontend-domain.vercel.app
RAILWAY_PUBLIC_URL=https://your-backend.up.railway.app

# Optional - Redis for Celery (if using background tasks)
REDIS_URL=redis://default:xxx@your-redis.railway.internal:6379
```

### 5. Deployment Configuration

The repository includes Railway configuration files:

- `railway.toml` - Main deployment configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Process commands (fallback)

**Key settings in `railway.toml`:**

```toml
[deploy]
# Runs migrations, seeds data, then starts server
startCommand = "sh -c 'PYTHONPATH=/app python3 -m alembic -c backend/alembic.ini upgrade head && PYTHONPATH=/app python3 backend/scripts/seed_data.py && PYTHONPATH=/app python3 -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT'"

healthcheckPath = "/health"
```

### 6. Git Flow for Deployment

The project uses a three-branch deployment flow:

```
develop/* -> main -> production (Railway auto-deploy)
```

- `develop/*` branches: Active development work
- `main`: Stable integration branch
- `production`: Railway auto-deploys from this branch

**Note:** Force push to `production` is expected (it's a deployment-only branch).

### 7. Verify Deployment

After deployment, verify the database connection:

```bash
# Health check
curl https://pcf.glideslopeintelligence.ai/health

# API test
curl https://pcf.glideslopeintelligence.ai/api/v1/emission-factors?limit=5
```

### 8. Troubleshooting Railway

**Build Fails:**
- Check Railway logs for Python dependency issues
- Ensure `requirements.txt` is in `backend/` directory

**Database Connection Issues:**
- Verify PostgreSQL service is running in Railway dashboard
- Check that `DATABASE_URL` is properly set (Railway does this automatically)
- The app handles both `postgres://` and `postgresql://` URL formats

**Migration Errors:**
- Migrations run automatically on deploy via `railway.toml`
- Check Railway logs for Alembic output
- If needed, run migrations manually via Railway CLI:
  ```bash
  railway run alembic -c backend/alembic.ini upgrade head
  ```

## Database Configuration Options

### Connection Pool Settings

PostgreSQL uses connection pooling for performance. Configure in `.env`:

```bash
# Pool size (default: 5)
DB_POOL_SIZE=5

# Maximum overflow connections (default: 10)
DB_MAX_OVERFLOW=10
```

**Recommendations:**
- Development: `pool_size=5`, `max_overflow=10`
- Production: `pool_size=10`, `max_overflow=20`

### How Pooling Works

The application uses SQLAlchemy's `QueuePool`:

```python
# Configured in backend/database/connection.py
engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # Base connections maintained
    max_overflow=10,      # Additional connections under load
    pool_pre_ping=True,   # Verify connections before using
)
```

## Database Schema

### Core Tables

| Table | Purpose | Row Count (Production) |
|-------|---------|----------------------|
| `products` | Finished goods and components | 817 (725 finished + 92 components) |
| `bill_of_materials` | Parent-child relationships with quantities | 7,025+ |
| `emission_factors` | CO2e values with provenance | 342 (268 EPA + 74 DEFRA) |
| `pcf_calculations` | Calculation results and metadata | Variable |
| `data_sources` | EPA, DEFRA configuration | 2 |
| `data_source_licenses` | License terms and attribution requirements | 2 |
| `emission_factor_provenance` | Source document references | Variable |
| `product_categories` | Hierarchical categories | 424 |

### Data Sources

| Source | License | Factors |
|--------|---------|---------|
| EPA | US Public Domain | 268 |
| DEFRA | OGL v3.0 (attribution required) | 74 |

## Migration Management

### Check Migration Status

```bash
cd backend
alembic current  # Show current revision
alembic history  # Show migration history
```

### Create New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new_table"

# Empty migration for manual SQL
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one step
alembic upgrade +1

# Downgrade one step
alembic downgrade -1
```

### Dialect-Aware Migrations

All migrations target PostgreSQL exclusively (SQLite is no longer supported):

```python
from alembic import context

def upgrade():
    # PostgreSQL-only
    op.execute("ALTER TABLE ... SET ... DEFAULT TRUE")
```

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data!
alembic downgrade base
alembic upgrade head
```

## Test Database Configuration

### Backend Tests

All backend tests use PostgreSQL (`pcf_calculator_test` database).

**Transaction rollback pattern:**
```python
@pytest.fixture(scope="function")
def db_session(test_engine):
    # Start a connection and begin a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    session = sessionmaker(bind=connection)()

    yield session

    # Cleanup - rollback transaction
    session.close()
    transaction.rollback()
    connection.close()
```

**Benefits:**
- Production parity: Tests run against PostgreSQL like production
- Fast isolation: Transaction rollback is faster than schema recreation
- Dialect consistency: No SQLite-specific quirks

### E2E Tests

E2E tests use an isolated test database with dedicated test data:

```bash
# Setup test database
cd frontend && npm run test:e2e:setup

# Run E2E tests with isolated database
npm run test:e2e:isolated
```

The test database contains:
- 3 E2E-specific products
- E2E test user
- Pre-seeded data sources (EPA, DEFRA)

## Troubleshooting

### Connection Refused

**Symptoms:** `psycopg.OperationalError: connection refused`

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   docker compose ps
   # or
   pg_isready
   ```

2. Check connection parameters in `.env`

3. Restart PostgreSQL container:
   ```bash
   docker compose restart postgres
   ```

### SSL Connection Required

**Symptoms:** `SSL connection is required`

**Solutions:**
1. Add SSL mode to connection string:
   ```bash
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   ```

2. For local development without SSL:
   ```bash
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=disable
   ```

### Migration Errors

**Symptoms:** `alembic.util.exc.CommandError` or missing tables

**Solutions:**
1. Ensure latest alembic:
   ```bash
   pip install -U alembic
   ```

2. Check migration history:
   ```bash
   alembic history --verbose
   ```

3. Reset migration state (development only):
   ```bash
   alembic stamp base  # Mark as having no migrations
   alembic upgrade head  # Apply all migrations fresh
   ```

### Performance Issues

**Symptoms:** Slow queries, connection timeouts

**Solutions:**
1. Increase pool size:
   ```bash
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

2. Enable query logging for debugging:
   ```bash
   DEBUG=true  # Logs all SQL queries
   ```

3. Check for missing indexes:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM products WHERE code = 'P001';
   ```

## Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Use SSL in production** - Always set `sslmode=require`
3. **Rotate passwords** - Change database passwords periodically
4. **Limit privileges** - Grant only necessary permissions
5. **Use connection pooling** - Prevents connection exhaustion attacks

## Environment-Specific Configuration

### Development

```bash
# .env
DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator
TEST_DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
DEBUG=true
```

### Staging

```bash
# .env
DATABASE_URL=postgresql://pcf_staging:password@staging-db.internal:5432/pcf_staging?sslmode=require
DEBUG=false
DB_POOL_SIZE=5
```

### Production

```bash
# .env (Railway auto-injects DATABASE_URL)
DEBUG=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Related Documentation

- [Integration Testing](integration-testing.md) - Database testing strategies
- [.env.sample](../.env.sample) - Environment variable template
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Railway Documentation](https://docs.railway.app/)

---

**Document Owner:** Technical-Lead / Database-Architect
**Last Updated:** 2026-03-08
