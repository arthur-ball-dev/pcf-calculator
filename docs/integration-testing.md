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

### Verify Docker Installation

```bash
docker --version
docker-compose --version
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

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis server hostname |
| `REDIS_PORT` | 6379 | Redis server port |
| `REDIS_DB` | 1 | Redis database number for tests |
| `CELERY_BROKER_URL` | redis://localhost:6379/0 | Celery broker URL |
| `CELERY_RESULT_BACKEND` | redis://localhost:6379/1 | Celery result backend |

### Using docker-compose.test.yml

For CI/CD environments or isolated testing:

```bash
# Start test infrastructure
docker-compose -f docker-compose.test.yml up -d

# Run tests
cd backend && pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Docker Compose Services

### redis

- Image: `redis:7-alpine`
- Port: 6379
- Volume: `redis_data` for persistence
- Health check: `redis-cli ping`

### celery_worker

- Processes background tasks
- Queues: `data_sync`, `calculations`
- Auto-restarts on failure

### celery_beat

- Schedules periodic tasks
- EPA sync: Biweekly (Mon/Thu 2:00 AM UTC)
- DEFRA sync: Biweekly (Tue/Fri 3:00 AM UTC)
- Exiobase sync: Monthly (1st day 4:00 AM UTC)

## Troubleshooting

### Redis Connection Refused

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solution:** Start Redis with `docker-compose up -d redis`

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

Located in `tests/test_*` directories:
- `test_api/` - API endpoint tests
- `test_services/` - Service layer tests
- `test_database/` - Database model tests
- `test_data/` - Data validation tests

### Integration Tests (Redis Required)

Located in `tests/integration/`:
- `test_celery.py` - Celery task execution tests
- `test_postgresql_migration.py` - PostgreSQL migration tests
- `test_ingestion_base.py` - Data ingestion pipeline tests

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

steps:
  - name: Run integration tests
    run: |
      cd backend
      pytest tests/integration/ -v
    env:
      REDIS_HOST: localhost
      REDIS_PORT: 6379
```

## Best Practices

1. **Isolate Test Data**: Use Redis database 1 for tests (not 0)
2. **Clean Up**: Use `clean_redis` fixture for test isolation
3. **Timeouts**: Set reasonable timeouts for async operations
4. **Skip Gracefully**: Use `require_redis` for proper skip messages
5. **Mock External APIs**: Use `respx` or `responses` for HTTP mocking