"""
Production data statistics with mapping coverage.

Usage:
    python backend/scripts/production_stats.py
"""
import asyncio
import json
from pathlib import Path

from backend.database.connection import SessionLocal, _get_async_session_maker
from backend.models import Product, BillOfMaterials, EmissionFactor
from backend.services.data_ingestion.emission_factor_mapper import EmissionFactorMapper
from sqlalchemy import func, distinct


async def test_mappings(component_names: list) -> dict:
    """Test which components map to emission factors."""
    AsyncSessionLocal = _get_async_session_maker()
    async with AsyncSessionLocal() as session:
        mapper = EmissionFactorMapper(db=session)

        results = {"mapped": [], "unmapped": []}
        for name in set(component_names):
            factor = await mapper.get_factor_for_component(name, "kg")
            if factor:
                results["mapped"].append(
                    (name, factor.activity_name, getattr(factor, "data_source", "unknown"))
                )
            else:
                results["unmapped"].append(name)
        return results


def main():
    db = SessionLocal()

    # Products breakdown
    total_products = db.query(Product).count()
    products_with_bom = db.query(distinct(BillOfMaterials.parent_product_id)).count()
    products_without_bom = total_products - products_with_bom

    # Components
    component_ids = db.query(distinct(BillOfMaterials.child_product_id)).all()
    component_ids = [c[0] for c in component_ids]
    parent_ids = db.query(distinct(BillOfMaterials.parent_product_id)).all()
    parent_ids = [p[0] for p in parent_ids]
    pure_components = set(component_ids) - set(parent_ids)

    # Categories
    categories = (
        db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    )

    # Emission factors
    ef_query = db.query(EmissionFactor).all()
    total_efs = len(ef_query)
    ef_by_provider = {}
    proxy_count = 0
    for ef in ef_query:
        provider = getattr(ef, "data_source")
        if provider == "PROXY":
            proxy_count += 1
        ef_by_provider[provider] = ef_by_provider.get(provider, 0) + 1

    # Get component names from database
    component_products = db.query(Product).filter(Product.id.in_(component_ids)).all()
    component_names = [p.name for p in component_products]

    # Test mappings
    results = asyncio.run(test_mappings(component_names))
    db.close()

    print("=" * 60)
    print("PRODUCTION DATA STATISTICS")
    print("=" * 60)
    print()
    print("PRODUCTS")
    print("-" * 40)
    print(f"  Total Products:           {total_products}")
    print(f"  Products with BOM:        {products_with_bom}")
    print(f"  Products without BOM:     {products_without_bom}")
    print(f"  Pure Components:          {len(pure_components)}")
    print()
    print("PRODUCT CATEGORIES")
    print("-" * 40)
    for cat, count in sorted(categories, key=lambda x: -x[1]):
        print(f"  {cat or 'None':<25} {count:>5}")
    print()
    print("EMISSION FACTORS BY PROVIDER")
    print("-" * 40)
    print(f"  Total EFs:                {total_efs}")
    for provider, count in sorted(ef_by_provider.items(), key=lambda x: -x[1]):
        print(f"    {provider:<20} {count:>5}")
    print(f"  Proxy EFs:                {proxy_count}")
    print()
    print("COMPONENT-TO-EF MAPPING COVERAGE")
    print("-" * 40)
    print(f"  Unique component names:   {len(set(component_names))}")
    print(f"  Successfully mapped:      {len(results['mapped'])}")
    print(f"  No EF found:              {len(results['unmapped'])}")
    print()
    print("  Successfully Mapped Components:")
    for name, ef_name, provider in sorted(results["mapped"], key=lambda x: x[0]):
        print(f"    {name:<25} -> {ef_name[:35]} ({provider})")
    print()
    if results["unmapped"]:
        print("  Components Without EF (Data Gap):")
        for name in sorted(results["unmapped"]):
            print(f"    - {name}")


if __name__ == "__main__":
    main()
