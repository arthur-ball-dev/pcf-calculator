"""Debug script to check ORM query results."""
import sys
sys.path.insert(0, '/home/mydev/projects/PCF/product-lca-carbon-calculator')

from backend.database.connection import get_db
from backend.models import Product, BillOfMaterials
from sqlalchemy.orm import joinedload

# Use the same session factory as the API
db = next(get_db())

product_id = "dbbe0d600f694038bb6d924b0dce3665"

# Query exactly like the API does
product = db.query(Product).options(
    joinedload(Product.bom_items).joinedload(BillOfMaterials.child_product)
).filter(Product.id == product_id).first()

print(f"Product: {product.name}")
print(f"BOM items count: {len(product.bom_items)}")
print()
print("BOM Items:")
for bom in product.bom_items[:5]:
    print(f"  - {bom.child_product.name if bom.child_product else 'Unknown'}")
    print(f"    id: {bom.id}")
    print(f"    emission_factor_id: {bom.emission_factor_id}")
    print(f"    emission_factor_id type: {type(bom.emission_factor_id)}")
    print()

# Also try a direct query on BOM
print("Direct BOM query:")
bom_direct = db.query(BillOfMaterials).filter(
    BillOfMaterials.parent_product_id == product_id
).first()
print(f"  emission_factor_id from direct query: {bom_direct.emission_factor_id}")

db.close()
