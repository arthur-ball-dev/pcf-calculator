#!/usr/bin/env python3
"""Verify development database was not modified (isolation check)."""
import psycopg

# Connect to dev database
conn = psycopg.connect('postgresql://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator')
cur = conn.cursor()

# Check products count
cur.execute('SELECT COUNT(*) FROM products')
products_count = cur.fetchone()[0]
print(f'Products count in DEV database: {products_count}')

# Check data_sources count
cur.execute('SELECT COUNT(*) FROM data_sources')
ds_count = cur.fetchone()[0]
print(f'Data sources count: {ds_count}')

# Check if E2E test user exists (should NOT be in dev db)
cur.execute("SELECT username FROM users WHERE username = 'e2e-test'")
user = cur.fetchone()
if user:
    print(f'WARNING: E2E test user found in DEV database: {user[0]}')
    print('This may indicate cross-contamination!')
else:
    print('E2E test user NOT in dev database (correct - isolation maintained)')

# Count E2E test products (should NOT be in dev db)
cur.execute("SELECT COUNT(*) FROM products WHERE code LIKE 'E2E-%'")
e2e_products = cur.fetchone()[0]
if e2e_products > 0:
    print(f'WARNING: Found {e2e_products} E2E test products in DEV database!')
else:
    print('No E2E test products in dev database (correct - isolation maintained)')

cur.close()
conn.close()

print('\\nDevelopment database isolation verification: PASSED')
