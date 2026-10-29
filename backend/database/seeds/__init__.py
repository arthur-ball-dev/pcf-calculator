"""
Database seed data module for Phase 5 and 7.

Contains initial data for data sources, E2E test user, and other reference tables.

TASK-DB-P5-002: Extended Database Schema
TASK-DATA-P7-001: Seed Data Sources Table
TASK-QA-P7-032: E2E Test User Seeding
"""

from backend.database.seeds.data_sources import (
    SEED_DATA_SOURCES,
    EXPECTED_DATA_SOURCE_NAMES,
    seed_data_sources,
    verify_data_sources,
    get_data_source_by_name,
)

from backend.database.seeds.e2e_test_user import (
    E2E_TEST_USER,
    seed_e2e_test_user,
    verify_e2e_test_user,
    delete_e2e_test_user,
    seed_e2e_test_user_standalone,
)

__all__ = [
    # Data sources
    'SEED_DATA_SOURCES',
    'EXPECTED_DATA_SOURCE_NAMES',
    'seed_data_sources',
    'verify_data_sources',
    'get_data_source_by_name',
    # E2E test user
    'E2E_TEST_USER',
    'seed_e2e_test_user',
    'verify_e2e_test_user',
    'delete_e2e_test_user',
    'seed_e2e_test_user_standalone',
]
