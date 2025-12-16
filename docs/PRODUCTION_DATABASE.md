# Production Database Setup Guide

## Overview

The PCF Calculator supports both SQLite (development) and PostgreSQL (production) databases.
The application automatically detects the database type from the `DATABASE_URL` environment variable
and configures the connection appropriately.

## Database Options

| Database | Use Case | Connection String Format |
|----------|----------|--------------------------|
| SQLite | Development, testing | `sqlite:///./pcf_calculator.db` |
| PostgreSQL | Production, staging | `postgresql://user:pass@host:5432/db` |
| Supabase | Cloud PostgreSQL | `postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres?sslmode=require` |

## Quick Start

### Development (SQLite - Default)

No configuration needed. The application defaults to SQLite:

```bash
# Default - uses sqlite:///./pcf_calculator.db
cd backend && uvicorn main:app --reload
```

### Production (PostgreSQL)

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/pcf_calculator
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

## PostgreSQL Setup

### Local PostgreSQL Installation

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start the service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@16

# Start the service
brew services start postgresql@16
```

### Create Database and User

```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create database
CREATE DATABASE pcf_calculator;

-- Create user with password
CREATE USER pcf_user WITH ENCRYPTED PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pcf_calculator TO pcf_user;

-- Grant schema privileges (PostgreSQL 15+)
\c pcf_calculator
GRANT ALL ON SCHEMA public TO pcf_user;

-- Exit
\q
```

### Configure Environment

Create a `.env` file from the template:

```bash
cp .env.sample .env
```

Update the `DATABASE_URL`:

```bash
# .env
DATABASE_URL=postgresql://pcf_user:your_secure_password@localhost:5432/pcf_calculator
```

### Run Migrations

```bash
cd backend
source ../.venv/bin/activate
alembic upgrade head
```

### Verify Setup

```bash
# Run validation script
python scripts/validate_database.py

# Or verify manually
python -c "from backend.database.connection import get_engine; e = get_engine(); print(f'Connected to: {e.url}')"
```

## Supabase Setup

[Supabase](https://supabase.com) provides managed PostgreSQL with additional features like
authentication, storage, and real-time subscriptions.

### 1. Create Supabase Project

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project reference ID (e.g., `abcdefghijklmnop`)

### 2. Get Connection String

1. Go to Project Settings > Database
2. Copy the Connection String (URI format)
3. Replace `[YOUR-PASSWORD]` with your database password

### 3. Configure Environment

```bash
# .env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require

# Optional: For Supabase API access
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_KEY=your-anon-key
```

### 4. Connection Pooling (Recommended for Serverless)

For serverless deployments, use the pooler connection (port 6543):

```bash
# Use pooler for serverless/edge functions
DATABASE_URL_POOLED=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres?pgbouncer=true
```

### 5. Run Migrations

```bash
cd backend
alembic upgrade head
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
- Serverless: Use Supabase pooler with smaller pool size

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

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data!
alembic downgrade base
alembic upgrade head
```

## Troubleshooting

### Connection Refused

**Symptoms:** `psycopg2.OperationalError: connection refused`

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   # or
   pg_isready
   ```

2. Check pg_hba.conf allows connections:
   ```bash
   # /etc/postgresql/16/main/pg_hba.conf
   # Add this line for local development:
   host    all    all    127.0.0.1/32    md5
   ```

3. Restart PostgreSQL after changes:
   ```bash
   sudo systemctl restart postgresql
   ```

### SSL Connection Required

**Symptoms:** `SSL connection is required`

**Solutions:**
1. Add SSL mode to connection string:
   ```bash
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   ```

2. For self-signed certificates:
   ```bash
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=prefer
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
DATABASE_URL=sqlite:///./pcf_calculator.db
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
# .env
DATABASE_URL=postgresql://pcf_prod:password@prod-db.internal:5432/pcf_prod?sslmode=require
DEBUG=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Related Documentation

- [Integration Testing](integration-testing.md) - Database testing strategies
- [.env.sample](../.env.sample) - Environment variable template
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Supabase Documentation](https://supabase.com/docs)
