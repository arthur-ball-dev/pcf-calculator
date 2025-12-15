"""
Test Configuration - Database Path Resolution
TASK-BE-P7-003: Tests for absolute database path resolution

The bug was that the database path is relative (./pcf_calculator.db) and when
the server is started from the backend/ directory, it resolves to a different
database file than the main project database.

These tests ensure:
1. Database path is always resolved to an absolute path
2. Database path points to the project root database file
3. Database path does not change based on working directory
"""

import os
import pytest
from pathlib import Path


class TestDatabasePathResolution:
    """Tests for database path resolution to prevent working directory issues"""

    def test_database_url_is_absolute_path(self):
        """
        Test that database_url resolves to an absolute path.

        This prevents issues when the server is started from different directories
        (e.g., 'cd backend && uvicorn main:app' vs 'uvicorn backend.main:app').
        """
        from backend.config import settings

        # Extract the path from the database URL
        if settings.is_sqlite:
            # Remove the sqlite:/// prefix
            db_path = settings.database_url.replace("sqlite:///", "")

            # The path should be absolute (starts with / on Unix)
            # or should resolve correctly regardless of cwd
            assert db_path.startswith("/") or os.path.isabs(db_path), \
                f"Database path should be absolute, got: {db_path}"

    def test_database_url_resolves_to_project_root(self):
        """
        Test that database_url resolves to the project root database.

        The main database file should be in the project root, not in
        subdirectories like backend/.
        """
        from backend.config import settings

        if settings.is_sqlite:
            # Get the database path
            db_path = settings.database_url.replace("sqlite:///", "")

            # Resolve to absolute path
            abs_db_path = os.path.abspath(db_path) if not os.path.isabs(db_path) else db_path

            # The parent directory should be the project root (contains backend/, frontend/)
            parent_dir = os.path.dirname(abs_db_path)

            # Project root should contain these markers
            has_backend = os.path.isdir(os.path.join(parent_dir, "backend"))
            has_frontend = os.path.isdir(os.path.join(parent_dir, "frontend"))

            assert has_backend and has_frontend, \
                f"Database path should be in project root. Got: {abs_db_path}"

    def test_database_path_consistent_across_working_directories(self):
        """
        Test that database path is the same regardless of current working directory.

        This is the key test that would catch the bug where starting from
        'cd backend' uses a different database than starting from project root.
        """
        from backend.config import settings

        if settings.is_sqlite:
            # Get the resolved database path
            db_path = settings.database_url.replace("sqlite:///", "")

            # The path should be absolute
            assert os.path.isabs(db_path), \
                f"Database path must be absolute to be consistent across directories. Got: {db_path}"

            # The path should contain 'pcf_calculator.db'
            assert "pcf_calculator.db" in db_path, \
                f"Database filename should be pcf_calculator.db. Got: {db_path}"

            # The path should NOT be inside the backend directory
            assert "/backend/" not in db_path and "\\backend\\" not in db_path, \
                f"Database should not be in backend/ subdirectory. Got: {db_path}"

    def test_database_file_exists_at_resolved_path(self):
        """
        Test that the database file exists at the resolved path.

        This validates that the configuration points to a real database file.
        """
        from backend.config import settings

        if settings.is_sqlite and ":memory:" not in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")

            # Resolve to absolute if needed
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)

            assert os.path.exists(db_path), \
                f"Database file should exist at: {db_path}"


class TestDatabaseQueryCorrectness:
    """
    Tests that verify database queries return correct results.

    These tests ensure the API is connected to the main database with
    all products, not a smaller test/seed database.
    """

    def test_database_has_products_with_category_id(self):
        """
        Test that database contains products with category_id set.

        The main database has ~4,000 products with category_id.
        The incorrect backend/pcf_calculator.db only has 18 products without category_id.
        """
        from backend.database.connection import SessionLocal
        from backend.models import Product
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # Count products with category_id
            products_with_category = db.query(func.count(Product.id)).filter(
                Product.category_id != None
            ).scalar()

            # If we're connected to the main database, we should have products with category_id
            # This test will FAIL if connected to the old backend/pcf_calculator.db
            assert products_with_category > 0, \
                "Database should contain products with category_id. " \
                "If this fails, the API may be using the wrong database file."
        finally:
            db.close()

    def test_total_product_count_exceeds_seed_data(self):
        """
        Test that total product count is greater than seed data (18 products).

        The main database has ~4,000 products.
        The incorrect database only has 18 seed products.
        """
        from backend.database.connection import SessionLocal
        from backend.models import Product
        from sqlalchemy import func

        db = SessionLocal()
        try:
            total_products = db.query(func.count(Product.id)).scalar()

            # Main database should have more than seed data
            # Seed data was 18 products
            assert total_products > 18, \
                f"Database should have more than 18 products. Got: {total_products}. " \
                "This may indicate using the wrong database file."
        finally:
            db.close()
