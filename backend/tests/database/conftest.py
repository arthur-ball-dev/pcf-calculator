"""
Pytest fixtures for database tests.

TASK-DB-P9-001: Connection pool configuration

This conftest.py sets production-ready pool settings before
any backend modules are imported, ensuring tests validate
against correct configuration values.

The os.environ settings here are picked up by pydantic Settings
when backend.config is first imported, overriding any .env file values.
"""

import os

# TASK-DB-P9-001: Set production-ready pool settings for tests
# These ensure tests validate against production-appropriate configuration
# Must be set BEFORE backend.config is imported anywhere
os.environ["DB_POOL_SIZE"] = "10"
os.environ["DB_MAX_OVERFLOW"] = "20"
os.environ["DB_POOL_TIMEOUT"] = "30"
os.environ["DB_POOL_RECYCLE"] = "1800"
