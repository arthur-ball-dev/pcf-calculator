"""
Backfill emission_factor_id for existing BOM entries.

This script updates BOM entries that have null emission_factor_id
by looking up the appropriate emission factor based on the child product name.
"""
import asyncio
import sys
sys.path.insert(0, '/home/mydev/projects/PCF/product-lca-carbon-calculator')

from sqlalchemy import select, update
from backend.database.connection import get_async_session
from backend.models import BillOfMaterials, Product
from backend.services.data_ingestion.emission_factor_mapper import EmissionFactorMapper


async def backfill_emission_factors():
    """Backfill emission_factor_id for all BOM entries with null values."""
    async with get_async_session() as session:
        mapper = EmissionFactorMapper(db=session)

        # Get all BOM entries with null emission_factor_id
        query = (
            select(BillOfMaterials, Product.name)
            .join(Product, BillOfMaterials.child_product_id == Product.id)
            .where(BillOfMaterials.emission_factor_id.is_(None))
        )
        result = await session.execute(query)
        bom_entries = result.all()

        print(f"Found {len(bom_entries)} BOM entries with null emission_factor_id")

        updated = 0
        not_found = 0

        for bom, child_name in bom_entries:
            # Look up emission factor for this component
            factor = await mapper.get_factor_for_component(
                component_name=child_name,
                unit=bom.unit or 'kg',
            )

            if factor:
                # Update the BOM entry
                await session.execute(
                    update(BillOfMaterials)
                    .where(BillOfMaterials.id == bom.id)
                    .values(emission_factor_id=factor.id)
                )
                updated += 1
            else:
                not_found += 1
                if not_found <= 10:
                    print(f"  No factor found for: {child_name} ({bom.unit})")

        await session.commit()

        print(f"\nResults:")
        print(f"  Updated: {updated}")
        print(f"  Not found: {not_found}")

        # Show warnings from mapper
        warnings = mapper.get_warnings()
        if warnings and len(warnings) > 10:
            print(f"\nMapper warnings: {len(warnings)} components not mapped")
            print("  (First 10 shown above)")


if __name__ == "__main__":
    asyncio.run(backfill_emission_factors())
