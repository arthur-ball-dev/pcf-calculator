"""
Apparel industry BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

Data sources:
- Higg Materials Sustainability Index (public methodology)
- Cotton Inc. lifecycle studies (public)
- Brand sustainability reports (public)

Templates:
- TSHIRT_TEMPLATE: T-shirts with basic/premium/organic variants
- JEANS_TEMPLATE: Jeans with regular/distressed/raw variants
- SHOES_TEMPLATE: Shoes with running/casual/boots variants
- JACKET_TEMPLATE: Jackets with light/winter/outdoor variants

All component names map to emission factors via:
- backend/services/data_ingestion/emission_factor_mapper.py
- backend/data/emission_factor_mappings.json
"""

from .base import BOMTemplate, ComponentSpec


TSHIRT_TEMPLATE = BOMTemplate(
    name="tshirt",
    industry="apparel",
    typical_mass_kg=0.2,
    base_components=[
        # Main fabric
        ComponentSpec(
            "textile_cotton", (0.15, 0.25), "kg",
            "Cotton fabric", "material"
        ),
        ComponentSpec(
            "textile_polyester", (0.02, 0.05), "kg",
            "Thread and labels", "material", optional=True, probability=0.5
        ),

        # Hardware
        ComponentSpec(
            "plastic_abs", (0.001, 0.003), "kg",
            "Buttons/clips", "material", optional=True, probability=0.3
        ),

        # Processing
        ComponentSpec(
            "water_process", (0.05, 0.1), "m3",
            "Dyeing and finishing", "other"
        ),
        ComponentSpec(
            "electricity_manufacturing", (0.5, 1.0), "kWh",
            "Cutting and sewing", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_plastic", (0.01, 0.02), "kg",
            "Poly bag", "other"
        ),
        ComponentSpec(
            "packaging_cardboard", (0.02, 0.04), "kg",
            "Tag and tissue", "other"
        ),
    ],
    variants={
        "basic": {
            "textile_cotton": 0.9,
            "water_process": 0.9,
        },
        "premium": {
            "textile_cotton": 1.2,
            "water_process": 1.3,
            "electricity_manufacturing": 1.2,
        },
        "organic": {
            "textile_cotton": 1.1,
            "water_process": 0.8,  # Less chemical processing
        },
    },
)


JEANS_TEMPLATE = BOMTemplate(
    name="jeans",
    industry="apparel",
    typical_mass_kg=0.6,
    base_components=[
        # Main fabric
        ComponentSpec(
            "textile_cotton", (0.4, 0.7), "kg",
            "Denim fabric", "material"
        ),
        ComponentSpec(
            "textile_polyester", (0.03, 0.06), "kg",
            "Thread and lining", "material"
        ),

        # Hardware
        ComponentSpec(
            "copper", (0.01, 0.02), "kg",
            "Rivets and buttons", "material"
        ),
        ComponentSpec(
            "steel", (0.005, 0.01), "kg",
            "Zipper", "material"
        ),

        # Processing
        ComponentSpec(
            "water_process", (0.15, 0.3), "m3",
            "Dyeing and washing", "other"
        ),
        ComponentSpec(
            "electricity_manufacturing", (1.0, 2.0), "kWh",
            "Manufacturing", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.05, 0.1), "kg",
            "Tags and hangers", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.02, 0.04), "kg",
            "Bag", "other"
        ),
    ],
    variants={
        "regular": {
            # Base configuration
        },
        "distressed": {
            "water_process": 1.5,
            "electricity_manufacturing": 1.3,
        },
        "raw": {
            "water_process": 0.5,
            "electricity_manufacturing": 0.8,
        },
    },
)


SHOES_TEMPLATE = BOMTemplate(
    name="shoes",
    industry="apparel",
    typical_mass_kg=0.8,
    base_components=[
        # Sole
        ComponentSpec(
            "rubber", (0.2, 0.4), "kg",
            "Outsole", "material"
        ),
        ComponentSpec(
            "plastic_abs", (0.1, 0.2), "kg",
            "Midsole (EVA)", "material"
        ),

        # Upper
        ComponentSpec(
            "textile_polyester", (0.1, 0.2), "kg",
            "Upper fabric", "material"
        ),
        ComponentSpec(
            "textile_cotton", (0.05, 0.1), "kg",
            "Lining", "material"
        ),

        # Hardware
        ComponentSpec(
            "steel", (0.01, 0.02), "kg",
            "Eyelets", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (2.0, 4.0), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.15, 0.25), "kg",
            "Shoebox", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.02, 0.05), "kg",
            "Tissue and bag", "other"
        ),
    ],
    variants={
        "running": {
            "rubber": 0.8,
            "plastic_abs": 1.2,
        },
        "casual": {
            "rubber": 0.9,
            "textile_polyester": 0.8,
        },
        "boots": {
            "rubber": 1.3,
            "textile_polyester": 1.5,
            "steel": 2.0,
        },
    },
)


JACKET_TEMPLATE = BOMTemplate(
    name="jacket",
    industry="apparel",
    typical_mass_kg=1.0,
    base_components=[
        # Main fabric
        ComponentSpec(
            "textile_polyester", (0.3, 0.5), "kg",
            "Outer shell", "material"
        ),
        ComponentSpec(
            "textile_cotton", (0.2, 0.4), "kg",
            "Lining", "material"
        ),

        # Insulation (optional for light jackets)
        ComponentSpec(
            "textile_polyester", (0.1, 0.3), "kg",
            "Insulation fill", "material", optional=True, probability=0.6
        ),

        # Hardware
        ComponentSpec(
            "steel", (0.02, 0.04), "kg",
            "Zipper", "material"
        ),
        ComponentSpec(
            "plastic_abs", (0.01, 0.02), "kg",
            "Buttons/snaps", "material"
        ),

        # Processing
        ComponentSpec(
            "water_process", (0.03, 0.06), "m3",
            "Processing", "other"
        ),
        ComponentSpec(
            "electricity_manufacturing", (2.0, 4.0), "kWh",
            "Manufacturing", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.1, 0.2), "kg",
            "Tag and hanger", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.03, 0.06), "kg",
            "Bag", "other"
        ),
    ],
    variants={
        "light": {
            "textile_polyester": 0.6,
            "textile_cotton": 0.5,
        },
        "winter": {
            "textile_polyester": 1.3,
            "textile_cotton": 1.2,
        },
        "outdoor": {
            "textile_polyester": 1.4,
            "water_process": 1.5,  # Waterproof treatment
        },
    },
)


APPAREL_TEMPLATES = {
    "tshirt": TSHIRT_TEMPLATE,
    "jeans": JEANS_TEMPLATE,
    "shoes": SHOES_TEMPLATE,
    "jacket": JACKET_TEMPLATE,
}


__all__ = [
    "TSHIRT_TEMPLATE",
    "JEANS_TEMPLATE",
    "SHOES_TEMPLATE",
    "JACKET_TEMPLATE",
    "APPAREL_TEMPLATES",
]
