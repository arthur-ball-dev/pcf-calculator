"""
BOM Template System for generating realistic product BOMs.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

This module provides templates for generating realistic Bill of Materials (BOM)
for products across 5 industries:
- Electronics (laptop, smartphone, monitor, tablet)
- Apparel (tshirt, jeans, shoes, jacket)
- Automotive (car_seat, wheel_assembly, dashboard)
- Construction (window_unit, door_assembly, hvac_unit)
- Food & Beverage (beverage_bottle, canned_food, packaged_snack)

Usage:
    from backend.services.data_ingestion.bom_templates import (
        ALL_TEMPLATES,
        BOMTemplate,
        ComponentSpec,
    )

    # Access all templates
    for industry, templates in ALL_TEMPLATES.items():
        for name, template in templates.items():
            components = template.get_components()
            print(f"{industry}/{name}: {len(components)} components")

    # Generate a specific BOM
    from backend.services.data_ingestion.bom_templates.electronics_boms import (
        LAPTOP_TEMPLATE,
    )

    laptop_bom = LAPTOP_TEMPLATE.get_components(variant="gaming")
    for component in laptop_bom:
        qty = component.generate_quantity()
        print(f"{component.name}: {qty} {component.unit}")

Template Statistics:
    - 17 templates across 5 industries
    - 35+ unique component types
    - All components mappable to emission factors
    - Variants support for product customization
    - Transport calculation support

Data Sources:
    - Electronics: iFixit teardowns, Apple/Dell environmental reports
    - Apparel: Higg MSI, Cotton Inc. studies, brand sustainability reports
    - Automotive: EPA GREET model, OEM sustainability reports
    - Construction: Athena Impact Estimator, NIST BIRDS database
    - Food & Beverage: Academic LCAs, USDA database, packaging standards
"""

from .base import BOMTemplate, ComponentSpec
from .electronics_boms import ELECTRONICS_TEMPLATES
from .apparel_boms import APPAREL_TEMPLATES
from .automotive_boms import AUTOMOTIVE_TEMPLATES
from .construction_boms import CONSTRUCTION_TEMPLATES
from .food_beverage_boms import FOOD_BEVERAGE_TEMPLATES


# Aggregate all templates by industry
ALL_TEMPLATES = {
    "electronics": ELECTRONICS_TEMPLATES,
    "apparel": APPAREL_TEMPLATES,
    "automotive": AUTOMOTIVE_TEMPLATES,
    "construction": CONSTRUCTION_TEMPLATES,
    "food_beverage": FOOD_BEVERAGE_TEMPLATES,
}


def get_template_stats() -> dict:
    """
    Get statistics about all templates.

    Returns:
        dict: Statistics including template count, component count, etc.
    """
    total_templates = 0
    all_component_names = set()

    for industry, templates in ALL_TEMPLATES.items():
        total_templates += len(templates)
        for template in templates.values():
            for component in template.base_components:
                all_component_names.add(component.name)

    return {
        "industries": len(ALL_TEMPLATES),
        "total_templates": total_templates,
        "unique_components": len(all_component_names),
        "component_names": sorted(all_component_names),
    }


__all__ = [
    # Base classes
    "BOMTemplate",
    "ComponentSpec",

    # Industry template collections
    "ELECTRONICS_TEMPLATES",
    "APPAREL_TEMPLATES",
    "AUTOMOTIVE_TEMPLATES",
    "CONSTRUCTION_TEMPLATES",
    "FOOD_BEVERAGE_TEMPLATES",

    # Aggregated templates
    "ALL_TEMPLATES",

    # Utility functions
    "get_template_stats",
]
