"""Quick test script for emission factor mapper."""
import asyncio
import sys
sys.path.insert(0, '/home/mydev/projects/PCF/product-lca-carbon-calculator')

from backend.database.connection import get_async_session
from backend.services.data_ingestion.emission_factor_mapper import EmissionFactorMapper

async def test():
    async with get_async_session() as session:
        mapper = EmissionFactorMapper(db=session)

        # Test component names from the BOM
        test_names = ['Plastic Pet', 'Plastic Hdpe', 'Plastic Pp', 'Water Process', 'Electricity Manufacturing']

        print("Testing emission factor mapping:")
        print("-" * 60)

        for name in test_names:
            factor = await mapper.get_factor_for_component(name, 'kg')
            if factor:
                print(f'{name:30} -> {factor.activity_name} (id: {factor.id[:8]}...)')
            else:
                print(f'{name:30} -> NOT FOUND')

        # Print warnings
        warnings = mapper.get_warnings()
        if warnings:
            print(f'\nWarnings ({len(warnings)}):')
            for w in warnings[:5]:
                print(f'  - {w}')

if __name__ == "__main__":
    asyncio.run(test())
