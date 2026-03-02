# Integration Testing Guide

This guide explains how to run integration tests for the PCF Calculator backend, particularly those requiring Redis and Celery infrastructure.

## Overview

The PCF Calculator uses Celery for background task processing (data synchronization, calculations) with Redis as the message broker. Integration tests verify that these components work correctly together.

## Quick Start

### Running Integration Tests

```bash
# Start Redis infrastructure
docker-compose up -d redis

# Run integration tests
cd backend && pytest tests/integration/ -v

# Stop infrastructure when done
docker-compose down
```

Or use the helper script:

```bash
./scripts/test-integration.sh
```

## Prerequisites

### Required Software

- Docker and Docker Compose
- Python 3.13+
- Virtual environment with project dependencies
- PostgreSQL 15+ (for database tests)

### Verify Docker Installation

```bash
docker --version
docker-compose --version
```

### PostgreSQL Test Database Setup

For running database integration tests locally:

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Or use local PostgreSQL installation
# Create test database
createdb pcf_calculator_test

# Create test user
createuser pcf_test_user
psql -c "ALTER USER pcf_test_user WITH PASSWORD 'pcf_test_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE pcf_calculator_test TO pcf_test_user;"
```

Set the test database URL in your environment:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://pcf_test_user:pcf_test_password@localhost:5432/pcf_calculator_test
```

## Infrastructure Setup

### Option 1: Docker Compose (Recommended)

Start only Redis for running tests:

```bash
# Start Redis only (lighter weight for testing)
docker-compose up -d redis

# Verify Redis is running
docker-compose ps
docker exec pcf-redis redis-cli ping
```

Start full Celery infrastructure for development:

```bash
# Start Redis, Celery worker, and Celery beat
docker-compose up -d

# View logs
docker-compose logs -f celery_worker
```

### Option 2: Local Redis

If you have Redis installed locally:

```bash
# macOS with Homebrew
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis-server

# Verify connection
redis-cli ping
```

## Running Tests

### All Integration Tests

```bash
cd backend
pytest tests/integration/ -v
```

### Celery-Specific Tests

```bash
cd backend
pytest tests/integration/test_celery.py -v
```

### Skip Integration Tests

If you don't have Redis available:

```bash
cd backend
pytest --ignore=tests/integration/ -v
```

### Run with Coverage

```bash
cd backend
pytest tests/integration/ --cov=. --cov-report=html -v
```

## Test Fixtures

### redis_available

Session-scoped fixture that checks Redis connectivity:

```python
def test_something(redis_available):
    if not redis_available:
        pytest.skip("Redis not available")
    # Test code...
```

### require_redis

Convenience fixture that automatically skips if Redis is unavailable:

```python
def test_celery_task(require_redis, celery_app):
    # This test will be skipped if Redis is not running
    result = sync_data_source.apply(args=["EPA_GHG_HUB"])
    assert result.successful()
```

### redis_client

Provides a connected Redis client for tests:

```python
def test_redis_operations(redis_client):
    redis_client.set("test_key", "test_value")
    assert redis_client.get("test_key") == b"test_value"
```

### clean_redis

Flushes the test Redis database before each test:

```python
def test_isolated(clean_redis):
    # Database is empty at start
    clean_redis.set("key", "value")
    # Database is flushed after test
```

### db_session

Provides a PostgreSQL database session for integration tests:

```python
def test_database_query(db_session):
    # Uses PostgreSQL test database
    result = db_session.execute(select(Product))
    products = result.scalars().all()
    assert len(products) >= 0
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis server hostname |
| `REDIS_PORT` | 6379 | Redis server port |
| `REDIS_DB` | 1 | Redis database number for tests |
| `CELERY_BROKER_URL` | redis://localhost:6379/0 | Celery broker URL |
| `CELERY_RESULT_BACKEND` | redis://localhost:6379/1 | Celery result backend |
| `DATABASE_URL` | postgresql+psycopg://... | PostgreSQL connection URL |
| `TEST_DATABASE_URL` | postgresql+psycopg://... | Test database connection URL |

## Docker Compose Services

### redis

- Image: `redis:7-alpine`
- Port: 6379
- Volume: `redis_data` for persistence
- Health check: `redis-cli ping`

### postgres

- Image: `postgres:15-alpine`
- Port: 5432
- Volume: `postgres_data` for persistence
- Health check: `pg_isready`

### celery_worker

- Processes background tasks
- Queues: `data_sync`, `calculations`
- Auto-restarts on failure

### celery_beat

- Schedules periodic tasks
- EPA sync: Biweekly (Mon/Thu 2:00 AM UTC)
- DEFRA sync: Biweekly (Tue/Fri 3:00 AM UTC)

## Troubleshooting

### Redis Connection Refused

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solution:** Start Redis with `docker-compose up -d redis`

### PostgreSQL Connection Refused

```
OperationalError: connection refused
```

**Solution:** Start PostgreSQL with `docker-compose up -d postgres` or verify local PostgreSQL is running

### Tests Skipped

If tests show as skipped:

1. Check Redis is running: `docker-compose ps`
2. Verify connectivity: `redis-cli ping`
3. Check environment variables are set correctly

### Celery Task Not Found

```
NotRegisteredError: 'backend.tasks.data_sync.sync_data_source'
```

**Solution:** Ensure tasks are properly imported in `backend/core/celery_app.py`

### Slow Test Execution

- Use `task_always_eager=True` for unit tests (mocks Celery)
- Use `task_always_eager=False` only for integration tests
- Set shorter timeouts: `task_time_limit=60`

## Test Categories

### Unit Tests (No Redis Required)

Located in `tests/` subdirectories:
- `api/` - API endpoint tests
- `services/` - Service layer tests
- `database/` - Database model tests
- `test_data/` - Data validation tests

### Integration Tests (Redis/PostgreSQL Required)

Located in `tests/integration/`:

**Core Infrastructure:**
- `test_celery.py` - Celery task execution and worker tests
- `test_postgresql_migration.py` - PostgreSQL migration and schema tests
- `test_redis_fixtures.py` - Redis fixture functionality tests
- `test_pool_behavior.py` - Connection pool behavior tests
- `test_docker_postgres.py` - Docker PostgreSQL integration tests

**ETL & Data Ingestion:**
- `test_ingestion_base.py` - Base data ingestion pipeline tests
- `test_epa_mock.py` - EPA GHG Hub data ingestion tests (mocked API)
- `test_defra_mock.py` - DEFRA data ingestion tests (mocked API)
- `test_external_sync.py` - External data sync verification tests
- `test_factor_mapping.py` - Emission factor mapping tests

**Product & Catalog:**
- `test_catalog_generation.py` - Product catalog generation tests
- `test_product_catalog.py` - Product catalog API tests
- `test_product_search_performance.py` - Search performance benchmarks

**Compliance:**
- `test_compliance_schema.py` - Compliance schema validation tests

## CI/CD Integration

### GitHub Actions Example

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

  postgres:
    image: postgres:15-alpine
    ports:
      - 5432:5432
    env:
      POSTGRES_DB: pcf_calculator_test
      POSTGRES_USER: pcf_test_user
      POSTGRES_PASSWORD: pcf_test_password
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

steps:
  - name: Run integration tests
    run: |
      cd backend
      pytest tests/integration/ -v
    env:
      REDIS_HOST: localhost
      REDIS_PORT: 6379
      DATABASE_URL: postgresql+psycopg://pcf_test_user:pcf_test_password@localhost:5432/pcf_calculator_test
```

## Best Practices

1. **Isolate Test Data**: Use Redis database 1 for tests (not 0)
2. **Clean Up**: Use `clean_redis` fixture for test isolation
3. **Timeouts**: Set reasonable timeouts for async operations
4. **Skip Gracefully**: Use `require_redis` for proper skip messages
5. **Mock External APIs**: Use `respx` or `responses` for HTTP mocking
6. **Use PostgreSQL**: All tests should use PostgreSQL to match production
