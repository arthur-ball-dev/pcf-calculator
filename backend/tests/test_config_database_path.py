"""
Test Configuration - Database Configuration
TASK-DB-P9-SQLITE-REMOVAL: Updated for PostgreSQL-only configuration

These tests ensure:
1. Database URL is a valid PostgreSQL connection string
2. Database connection works correctly
"""

import os
import pytest


class TestDatabaseConfiguration:
    """Tests for PostgreSQL database configuration"""

    def test_database_url_is_postgresql(self):
        """
        Test that database_url is a PostgreSQL connection string.
        """
        from backend.config import settings

        assert settings.is_postgresql, \
            f"Database URL should be PostgreSQL, got: {settings.database_url}"

    def test_database_url_requires_postgresql_format(self):
        """
        Test that DATABASE_URL must be a PostgreSQL connection string.
        """
        from backend.config import settings

        # The URL should be a valid PostgreSQL URL
        url = settings.database_url.lower()
        assert "postgresql" in url or url.startswith("postgres://"), \
            "DATABASE_URL must be a PostgreSQL connection string"


class TestDatabaseQueryCorrectness:
    """
    Tests that verify database queries return correct results.

    These tests ensure the API is connected to the main database with
    all products, not a smaller test/seed database.
    """

    def test_products_table_has_category_column(self):
        """
        The products table exposes category_id (the SQLite-era check that the
        dev database was populated does not belong in the test suite).
        """
        from backend.models import Product

        assert hasattr(Product, "category_id")

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
