#!/usr/bin/env python3
"""
Quick script to seed test database data.
Uses psycopg3 driver explicitly.
"""
import os
import sys

# Set the test database URL with the correct psycopg3 driver
os.environ['DATABASE_URL'] = 'postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test'

# Clear cached modules
for mod_name in list(sys.modules.keys()):
    if 'backend' in mod_name:
        del sys.modules[mod_name]

# Import with fresh config
from backend.config import settings
from backend.database.connection import db_context

print(f'Using database: {settings.database_url}')

with db_context() as session:
    # Seed data structures
    print('Seeding data structures...')
    from backend.database.seeds.data_sources import seed_data_sources
    ds_count = seed_data_sources(session)
    print(f'  Created/verified {ds_count} data structures')

    # Seed licenses
    print('Seeding data licenses...')
    from backend.database.seeds.compliance_seeds import seed_licenses
    licenses = seed_licenses(session)
    print(f'  Created/verified {len(licenses)} licenses')

    # Seed E2E test user
    print('Seeding E2E test user...')
    from backend.database.seeds.e2e_test_user import seed_e2e_test_user
    user_id = seed_e2e_test_user(session, force_update=True)
    print(f'  E2E test user created/updated: {user_id}')

    # Seed sample products
    print('Seeding sample products...')
    from backend.models import Product

    existing = session.query(Product).count()
    if existing == 0:
        sample_products = [
            {'code': 'E2E-LAPTOP-001', 'name': 'E2E Test Laptop', 'description': 'Sample laptop for E2E testing', 'unit': 'unit', 'is_finished_product': True, 'category': 'Electronics'},
            {'code': 'E2E-STEEL-001', 'name': 'E2E Test Steel Sheet', 'description': 'Sample steel material', 'unit': 'kg', 'is_finished_product': False, 'category': 'Materials'},
            {'code': 'E2E-PLASTIC-001', 'name': 'E2E Test Plastic Housing', 'description': 'Sample plastic component', 'unit': 'kg', 'is_finished_product': False, 'category': 'Materials'},
        ]
        for p_data in sample_products:
            product = Product(**p_data)
            session.add(product)
        print(f'  Added {len(sample_products)} sample products')
    else:
        print(f'  {existing} products already exist, skipping')

    session.commit()
    print('Seeding completed.')
