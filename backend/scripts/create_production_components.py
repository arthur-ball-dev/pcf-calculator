#!/usr/bin/env python3
"""
Create Production Components Script.

TASK-DATA-P10: Create production component products based on expanded emission factors.

This script creates ~65 production component products that map directly to the
expanded EPA Table 9 materials and DEFRA material use factors.

Components created are:
- Plastics (9): HDPE, LDPE, PET, PP, PS, PVC, PLA, LLDPE, Mixed Plastics
- Metals (6): Aluminum, Steel, Copper, Mixed Metals, Scrap Metal, Structural Steel
- Paper/Wood (6): Paper, Cardboard, Lumber, MDF, Mixed Paper, Office Paper
- Construction (8): Concrete, Glass, Drywall, Insulation, Asphalt, Bricks, Carpet, Vinyl
- Electronics (7): Desktop CPU, Display, Peripherals, IT Equipment, Portable Electronics
- Batteries (3): Alkaline Battery, Li-ion Battery, NiMh Battery
- Energy (4): UK Grid Electricity, US Grid Electricity, Natural Gas, Diesel
- Transport (6): Truck, Rail, Ship, Aircraft, Van, HGV
- Water (2): Water Supply, Water Treatment
- Waste (6): Food Waste, Yard Waste, Mixed Organics, Mixed MSW, Garden Waste, Mixed Recyclables

Usage:
    # After running load_production_data.py to load emission factors:
    python backend/scripts/create_production_components.py
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings
from backend.models import Product, EmissionFactor


# Production component definitions
# Each component maps to an emission factor activity_name pattern
PRODUCTION_COMPONENTS: List[Dict[str, Any]] = [
    # ========================================================================
    # PLASTICS (from EPA Table 9)
    # ========================================================================
    {
        "code": "material_hdpe",
        "name": "Plastic - HDPE",
        "description": "High-Density Polyethylene plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["HDPE - Recycled", "Plastics: HDPE", "HDPE"],
    },
    {
        "code": "material_ldpe",
        "name": "Plastic - LDPE",
        "description": "Low-Density Polyethylene plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["LDPE - Recycled", "Plastics: LDPE", "LDPE"],
    },
    {
        "code": "material_pet",
        "name": "Plastic - PET",
        "description": "Polyethylene Terephthalate plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["PET - Recycled", "Plastics: PET", "PET"],
    },
    {
        "code": "material_pp",
        "name": "Plastic - PP",
        "description": "Polypropylene plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["PP - Recycled", "Plastics: PP", "PP"],
    },
    {
        "code": "material_ps",
        "name": "Plastic - PS",
        "description": "Polystyrene plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["PS - Recycled", "Plastics: PS", "PS"],
    },
    {
        "code": "material_pvc",
        "name": "Plastic - PVC",
        "description": "Polyvinyl Chloride plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["PVC - Recycled", "Plastics: PVC", "PVC"],
    },
    {
        "code": "material_pla",
        "name": "PLA Bioplastic",
        "description": "Polylactic Acid bioplastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["PLA", "Polylactic Acid"],
    },
    {
        "code": "material_lldpe",
        "name": "LLDPE Plastic",
        "description": "Linear Low-Density Polyethylene plastic material",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["LLDPE", "Linear Low-Density"],
    },
    {
        "code": "material_mixed_plastics",
        "name": "Mixed Plastics",
        "description": "Mixed plastic materials",
        "unit": "kg",
        "category": "plastics",
        "ef_patterns": ["Mixed Plastics"],
    },

    # ========================================================================
    # METALS (from EPA Table 9)
    # ========================================================================
    {
        "code": "material_aluminum",
        "name": "Aluminum",
        "description": "Aluminum metal material",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Aluminum", "Aluminium"],
    },
    {
        "code": "material_steel",
        "name": "Steel",
        "description": "Steel metal material",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Steel Cans", "Steel"],
    },
    {
        "code": "material_copper",
        "name": "Copper",
        "description": "Copper wire metal material",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Copper Wire - Recycled", "Copper Wire - Landfilled", "Copper Wire"],
    },
    {
        "code": "material_mixed_metals",
        "name": "Mixed Metals",
        "description": "Mixed metal materials",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Mixed Metals"],
    },
    {
        "code": "material_scrap_metal",
        "name": "Scrap Metal",
        "description": "Scrap metal material",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Scrap metal", "Scrap"],
    },
    {
        "code": "material_structural_steel",
        "name": "Structural Steel",
        "description": "Structural steel for construction",
        "unit": "kg",
        "category": "metals",
        "ef_patterns": ["Structural Steel"],
    },

    # ========================================================================
    # PAPER/WOOD (from EPA Table 9)
    # ========================================================================
    {
        "code": "material_paper",
        "name": "Paper",
        "description": "Paper material",
        "unit": "kg",
        "category": "paper",
        "ef_patterns": ["Paper", "Office Paper"],
    },
    {
        "code": "material_cardboard",
        "name": "Cardboard",
        "description": "Corrugated cardboard material",
        "unit": "kg",
        "category": "paper",
        "ef_patterns": ["Corrugated Containers", "Cardboard"],
    },
    {
        "code": "material_lumber",
        "name": "Wood - Lumber",
        "description": "Dimensional lumber wood material",
        "unit": "kg",
        "category": "wood",
        "ef_patterns": ["Dimensional Lumber - Recycled", "Dimensional Lumber - Landfilled", "Dimensional Lumber"],
    },
    {
        "code": "material_mdf",
        "name": "MDF Board",
        "description": "Medium-density Fiberboard",
        "unit": "kg",
        "category": "wood",
        "ef_patterns": ["Medium-density Fiberboard", "MDF"],
    },
    {
        "code": "material_mixed_paper",
        "name": "Mixed Paper",
        "description": "Mixed paper materials",
        "unit": "kg",
        "category": "paper",
        "ef_patterns": ["Mixed Paper"],
    },
    {
        "code": "material_office_paper",
        "name": "Office Paper",
        "description": "Office paper material",
        "unit": "kg",
        "category": "paper",
        "ef_patterns": ["Office Paper"],
    },

    # ========================================================================
    # CONSTRUCTION (from EPA Table 9)
    # ========================================================================
    {
        "code": "material_concrete",
        "name": "Concrete",
        "description": "Concrete material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Concrete"],
    },
    {
        "code": "material_glass",
        "name": "Glass",
        "description": "Glass material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Glass"],
    },
    {
        "code": "material_drywall",
        "name": "Drywall",
        "description": "Drywall/Gypsum board material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Drywall", "Plasterboard"],
    },
    {
        "code": "material_insulation",
        "name": "Fiberglass Insulation",
        "description": "Fiberglass insulation material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Fiberglass Insulation", "Insulation"],
    },
    {
        "code": "material_asphalt",
        "name": "Asphalt",
        "description": "Asphalt material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Asphalt Concrete", "Asphalt Shingles", "Asphalt"],
    },
    {
        "code": "material_bricks",
        "name": "Clay Bricks",
        "description": "Clay bricks material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Clay Bricks", "Bricks"],
    },
    {
        "code": "material_carpet",
        "name": "Carpet",
        "description": "Carpet flooring material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Carpet"],
    },
    {
        "code": "material_vinyl_flooring",
        "name": "Vinyl Flooring",
        "description": "Vinyl flooring material",
        "unit": "kg",
        "category": "construction",
        "ef_patterns": ["Vinyl Flooring"],
    },

    # ========================================================================
    # ELECTRONICS (from EPA Table 9)
    # ========================================================================
    {
        "code": "material_desktop_cpu",
        "name": "Desktop CPU",
        "description": "Desktop computer CPU component",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["Desktop CPUs", "Desktop CPU"],
    },
    {
        "code": "material_display",
        "name": "Flat-panel Display",
        "description": "Flat-panel display component",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["Flat-panel Displays", "Display"],
    },
    {
        "code": "material_peripherals",
        "name": "Electronic Peripherals",
        "description": "Electronic peripheral components",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["Electronic Peripherals", "Peripherals"],
    },
    {
        "code": "material_it_equipment",
        "name": "IT Equipment",
        "description": "IT equipment components",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["IT equipment", "Hard-copy Devices"],
    },
    {
        "code": "material_portable_electronics",
        "name": "Portable Electronics",
        "description": "Portable electronic devices",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["Portable Electronic Devices", "Mixed Electronics"],
    },
    {
        "code": "material_crt_display",
        "name": "CRT Display",
        "description": "CRT display component (legacy)",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["CRT Displays"],
    },
    {
        "code": "material_mixed_electronics",
        "name": "Mixed Electronics",
        "description": "Mixed electronic components",
        "unit": "kg",
        "category": "electronics",
        "ef_patterns": ["Mixed Electronics"],
    },

    # ========================================================================
    # BATTERIES (from DEFRA Material use)
    # ========================================================================
    {
        "code": "material_battery_alkaline",
        "name": "Alkaline Battery",
        "description": "Alkaline battery component",
        "unit": "kg",
        "category": "batteries",
        "ef_patterns": ["Batteries - Alkaline", "Alkaline"],
    },
    {
        "code": "material_battery_lithium",
        "name": "Li-ion Battery",
        "description": "Lithium-ion battery component",
        "unit": "kg",
        "category": "batteries",
        "ef_patterns": ["Batteries - Li ion", "Li-ion", "Lithium"],
    },
    {
        "code": "material_battery_nimh",
        "name": "NiMh Battery",
        "description": "Nickel-Metal Hydride battery component",
        "unit": "kg",
        "category": "batteries",
        "ef_patterns": ["Batteries - NiMh", "NiMh"],
    },

    # ========================================================================
    # ELECTRICAL APPLIANCES (from DEFRA Material use)
    # ========================================================================
    {
        "code": "material_fridges",
        "name": "Fridges and Freezers",
        "description": "Refrigeration appliances",
        "unit": "kg",
        "category": "electrical",
        "ef_patterns": ["Fridges and freezers", "Fridges"],
    },
    {
        "code": "material_large_appliances",
        "name": "Large Appliances",
        "description": "Large electrical appliances",
        "unit": "kg",
        "category": "electrical",
        "ef_patterns": ["Large appliances"],
    },
    {
        "code": "material_small_appliances",
        "name": "Small Appliances",
        "description": "Small electrical appliances",
        "unit": "kg",
        "category": "electrical",
        "ef_patterns": ["Small appliances", "Small electrical"],
    },

    # ========================================================================
    # ENERGY - ELECTRICITY (from EPA eGRID and DEFRA)
    # ========================================================================
    {
        "code": "energy_uk_grid",
        "name": "Electricity - UK",
        "description": "UK national grid electricity",
        "unit": "kWh",
        "category": "electricity",
        "ef_patterns": ["UK electricity", "Grid Electricity"],
    },
    {
        "code": "energy_us_grid",
        "name": "Electricity - US",
        "description": "US average grid electricity",
        "unit": "kWh",
        "category": "electricity",
        "ef_patterns": ["Grid Electricity - RFCW", "Grid Electricity - US"],
    },

    # ========================================================================
    # ENERGY - FUELS (from EPA Table 1/2 and DEFRA Fuels)
    # ========================================================================
    {
        "code": "energy_natural_gas",
        "name": "Natural Gas",
        "description": "Natural gas fuel",
        "unit": "kg",
        "category": "fuels",
        "ef_patterns": ["Natural Gas"],
    },
    {
        "code": "energy_diesel",
        "name": "Diesel Fuel",
        "description": "Diesel fuel",
        "unit": "kg",
        "category": "fuels",
        "ef_patterns": ["Diesel"],
    },
    {
        "code": "energy_gasoline",
        "name": "Gasoline Fuel",
        "description": "Gasoline/petrol fuel",
        "unit": "kg",
        "category": "fuels",
        "ef_patterns": ["Motor Gasoline", "Gasoline", "Petrol"],
    },
    {
        "code": "energy_lpg",
        "name": "LPG Fuel",
        "description": "Liquefied Petroleum Gas fuel",
        "unit": "kg",
        "category": "fuels",
        "ef_patterns": ["LPG", "Liquefied Petroleum"],
    },

    # ========================================================================
    # TRANSPORT (from EPA Table 8 and DEFRA Freighting goods)
    # ========================================================================
    {
        "code": "transport_truck",
        "name": "Transport - Truck",
        "description": "Medium/Heavy duty truck freight transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Medium- and Heavy-Duty Truck", "HGV"],
    },
    {
        "code": "transport_rail",
        "name": "Transport - Rail",
        "description": "Rail freight transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Rail", "Freight train"],
    },
    {
        "code": "transport_ship",
        "name": "Transport - Ship",
        "description": "Waterborne freight transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Waterborne Craft", "Sea tanker"],
    },
    {
        "code": "transport_aircraft",
        "name": "Transport - Air",
        "description": "Air freight transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Aircraft", "Air freight"],
    },
    {
        "code": "transport_van",
        "name": "Transport - Van",
        "description": "Light delivery van transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Light-Duty Truck", "Vans"],
    },
    {
        "code": "transport_passenger_car",
        "name": "Transport - Passenger Car",
        "description": "Passenger car transport",
        "unit": "tkm",
        "category": "transport",
        "ef_patterns": ["Transport - Passenger Car"],
    },

    # ========================================================================
    # WATER (from DEFRA Water supply/treatment)
    # ========================================================================
    {
        "code": "water_supply",
        "name": "Water - Supply",
        "description": "Water supply utility",
        "unit": "L",
        "category": "water",
        "ef_patterns": ["Water supply"],
    },
    {
        "code": "water_treatment",
        "name": "Water - Treatment",
        "description": "Water treatment utility",
        "unit": "L",
        "category": "water",
        "ef_patterns": ["Water treatment"],
    },

    # ========================================================================
    # WASTE (from EPA Table 9)
    # ========================================================================
    {
        "code": "waste_food",
        "name": "Waste - Food",
        "description": "Food waste disposal",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Food Waste - Composted", "Food Waste - Landfilled"],
    },
    {
        "code": "waste_yard",
        "name": "Waste - Yard",
        "description": "Yard waste/green waste",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Yard Trimmings - Composted", "Yard Trimmings - Landfilled"],
    },
    {
        "code": "waste_mixed_organics",
        "name": "Waste - Organics",
        "description": "Mixed organic waste",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Mixed Organics - Composted", "Mixed Organics"],
    },
    {
        "code": "waste_mixed_msw",
        "name": "Waste - MSW",
        "description": "Mixed municipal solid waste",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Mixed MSW - Landfilled", "Mixed MSW - Combusted"],
    },
    {
        "code": "waste_mixed_recyclables",
        "name": "Waste - Recyclables",
        "description": "Mixed recyclable materials",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Mixed Recyclables - Recycled"],
    },
    {
        "code": "waste_tires",
        "name": "Rubber",
        "description": "Tire/rubber waste and material",
        "unit": "kg",
        "category": "waste",
        "ef_patterns": ["Tires - Recycled", "Tires - Landfilled", "Tires"],
    },
]


async def create_production_components() -> dict:
    """
    Create production component products in the database.

    Returns:
        Dict with creation statistics
    """
    async_url = settings.async_database_url

    engine = create_async_engine(async_url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    stats = {
        "created": 0,
        "skipped": 0,
        "errors": 0,
        "by_category": {},
    }

    async with async_session_maker() as session:
        for comp_def in PRODUCTION_COMPONENTS:
            code = comp_def["code"]
            name = comp_def["name"]
            category = comp_def["category"]

            # Initialize category counter
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0

            # Check if component already exists
            result = await session.execute(
                select(Product).where(Product.code == code)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [SKIP] {code} - already exists")
                stats["skipped"] += 1
                continue

            # Create component product
            product = Product(
                id=str(uuid4()).replace("-", ""),
                code=code,
                name=name,
                description=comp_def["description"],
                unit=comp_def["unit"],
                category=category,
                is_finished_product=False,
                product_metadata={
                    "is_production_component": True,
                    "ef_patterns": comp_def["ef_patterns"],
                    "category": category,
                },
            )

            session.add(product)
            stats["created"] += 1
            stats["by_category"][category] += 1
            print(f"  [CREATE] {code} - {name}")

        await session.commit()

    await engine.dispose()
    return stats


async def verify_emission_factor_mapping() -> dict:
    """
    Verify that production components can be mapped to emission factors.

    Returns:
        Dict with mapping statistics
    """
    async_url = settings.async_database_url

    engine = create_async_engine(async_url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    stats = {
        "total_components": len(PRODUCTION_COMPONENTS),
        "mappable": 0,
        "unmappable": [],
    }

    async with async_session_maker() as session:
        for comp_def in PRODUCTION_COMPONENTS:
            code = comp_def["code"]
            patterns = comp_def["ef_patterns"]
            found = False

            for pattern in patterns:
                # Try to find matching emission factor
                result = await session.execute(
                    select(EmissionFactor).where(
                        EmissionFactor.activity_name.ilike(f"%{pattern}%"),
                        EmissionFactor.is_active == True,
                    ).limit(1)
                )
                ef = result.scalar_one_or_none()

                if ef:
                    found = True
                    break

            if found:
                stats["mappable"] += 1
            else:
                stats["unmappable"].append(code)

    await engine.dispose()
    return stats


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("PCF Calculator - Create Production Components")
    print("=" * 60)
    print()

    # Create components
    print("Creating production components...")
    stats = asyncio.run(create_production_components())

    print()
    print(f"Created: {stats['created']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    print("\nBy category:")
    for cat, count in sorted(stats["by_category"].items()):
        print(f"  {cat}: {count}")

    # Verify mapping
    print()
    print("Verifying emission factor mapping...")
    mapping_stats = asyncio.run(verify_emission_factor_mapping())

    print(f"\nTotal components: {mapping_stats['total_components']}")
    print(f"Mappable to EFs: {mapping_stats['mappable']}")

    if mapping_stats["unmappable"]:
        print(f"\nUnmappable components ({len(mapping_stats['unmappable'])}):")
        for code in mapping_stats["unmappable"]:
            print(f"  - {code}")

    print()
    print("=" * 60)
    print("PRODUCTION COMPONENTS CREATED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
