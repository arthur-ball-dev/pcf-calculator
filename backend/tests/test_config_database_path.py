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
