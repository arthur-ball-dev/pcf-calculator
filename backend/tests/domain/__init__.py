"""
Domain layer tests for PCF Calculator.

TASK-BE-P7-019: Domain Layer Separation Tests

This package contains tests for the domain layer architecture:
- test_entities.py: Pure domain entity tests (no SQLAlchemy)
- test_repositories.py: Repository interface and implementation tests
- test_services.py: Domain service business logic tests

These tests verify:
1. Domain entities are immutable (frozen dataclasses)
2. Domain entities contain validation logic
3. Repository interfaces are abstract
4. Services depend on repository interfaces, not implementations
5. Clean separation between domain and infrastructure
"""
