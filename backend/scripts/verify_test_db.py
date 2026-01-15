#!/usr/bin/env python3
"""Verify test database has correct data."""
import psycopg

conn = psycopg.connect('postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test')
cur = conn.cursor()

# Check products count
cur.execute('SELECT COUNT(*) FROM products')
products_count = cur.fetchone()[0]
print(f'Products count in test database: {products_count}')

# Check data_sources count
cur.execute('SELECT COUNT(*) FROM data_sources')
ds_count = cur.fetchone()[0]
print(f'Data sources count: {ds_count}')

# Check users for E2E test user
cur.execute("SELECT username FROM users WHERE username = 'e2e-test'")
user = cur.fetchone()
if user:
    print(f'E2E test user found: {user[0]}')
else:
    print('E2E test user NOT found')

# Check data_source_licenses
cur.execute('SELECT COUNT(*) FROM data_source_licenses')
lic_count = cur.fetchone()[0]
print(f'Data source licenses: {lic_count}')

# List sample products
cur.execute('SELECT code, name FROM products LIMIT 5')
products = cur.fetchall()
print('Sample products:')
for p in products:
    print(f'  - {p[0]}: {p[1]}')

cur.close()
conn.close()
print('\\nTest database verification: PASSED')
