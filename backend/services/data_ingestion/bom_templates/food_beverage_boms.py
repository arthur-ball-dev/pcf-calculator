"""
Food & Beverage industry BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

Data sources:
- Published academic LCAs (public)
- USDA food composition database (public)
- Packaging industry standards

Note: Focus on packaging and processing, not agricultural inputs.

Templates:
- BEVERAGE_BOTTLE_TEMPLATE: Bottled beverages with size variants
- CANNED_FOOD_TEMPLATE: Canned food products with size variants
- PACKAGED_SNACK_TEMPLATE: Packaged snacks with single/multi/family variants

All component names map to emission factors via:
- backend/services/data_ingestion/emission_factor_mapper.py
- backend/data/emission_factor_mappings.json
"""

from .base import BOMTemplate, ComponentSpec


BEVERAGE_BOTTLE_TEMPLATE = BOMTemplate(
    name="beverage_bottle",
    industry="food_beverage",
    typical_mass_kg=0.5,
    base_components=[
        # Bottle
        ComponentSpec(
            "plastic_pet", (0.02, 0.04), "kg",
            "PET bottle", "material"
        ),

        # Cap
        ComponentSpec(
            "plastic_hdpe", (0.003, 0.006), "kg",
            "Cap", "material"
        ),

        # Label
        ComponentSpec(
            "plastic_pp", (0.002, 0.004), "kg",
            "Label (PP film)", "material"
        ),

        # Processing water
        ComponentSpec(
            "water_process", (0.0003, 0.0005), "m3",
            "Contents (water base)", "other"
        ),

        # Bottling energy
        ComponentSpec(
            "electricity_manufacturing", (0.05, 0.1), "kWh",
            "Bottling", "energy"
        ),

        # Case packaging
        ComponentSpec(
            "packaging_cardboard", (0.02, 0.04), "kg",
            "Case packaging", "other"
        ),

        # Shrink wrap
        ComponentSpec(
            "packaging_plastic", (0.005, 0.01), "kg",
            "Shrink wrap", "other"
        ),
    ],
    variants={
        "small_330ml": {
            "plastic_pet": 0.7,
            "water_process": 0.66,
        },
        "standard_500ml": {
            # Base configuration
        },
        "large_1L": {
            "plastic_pet": 1.5,
            "plastic_hdpe": 1.3,
            "water_process": 2.0,
        },
    },
)


CANNED_FOOD_TEMPLATE = BOMTemplate(
    name="canned_food",
    industry="food_beverage",
    typical_mass_kg=0.6,
    base_components=[
        # Can body
        ComponentSpec(
            "aluminum", (0.02, 0.04), "kg",
            "Can body", "material"
        ),

        # Can lid
        ComponentSpec(
            "steel", (0.01, 0.02), "kg",
            "Can lid", "material"
        ),

        # Label
        ComponentSpec(
            "paper", (0.003, 0.006), "kg",
            "Paper label", "material"
        ),

        # Processing
        ComponentSpec(
            "water_process", (0.0001, 0.0002), "m3",
            "Processing water", "other"
        ),
        ComponentSpec(
            "electricity_manufacturing", (0.1, 0.2), "kWh",
            "Canning process", "energy"
        ),

        # Case packaging
        ComponentSpec(
            "packaging_cardboard", (0.03, 0.06), "kg",
            "Case", "other"
        ),
    ],
    variants={
        "small": {
            "aluminum": 0.6,
            "steel": 0.6,
        },
        "standard": {
            # Base configuration
        },
        "large": {
            "aluminum": 1.5,
            "steel": 1.5,
        },
    },
)


PACKAGED_SNACK_TEMPLATE = BOMTemplate(
    name="packaged_snack",
    industry="food_beverage",
    typical_mass_kg=0.2,
    base_components=[
        # Primary packaging (flexible film)
        ComponentSpec(
            "packaging_plastic", (0.01, 0.02), "kg",
            "Primary bag (multi-layer film)", "material"
        ),

        # Secondary packaging
        ComponentSpec(
            "packaging_cardboard", (0.03, 0.05), "kg",
            "Display box", "material", optional=True, probability=0.4
        ),

        # Closure
        ComponentSpec(
            "plastic_pp", (0.002, 0.004), "kg",
            "Clip/seal", "material"
        ),

        # Processing
        ComponentSpec(
            "electricity_manufacturing", (0.02, 0.05), "kWh",
            "Packaging line", "energy"
        ),

        # Nitrogen flush
        ComponentSpec(
            "waste_general", (0.001, 0.002), "kg",
            "Process waste", "other"
        ),

        # Case packaging
        ComponentSpec(
            "packaging_cardboard", (0.02, 0.04), "kg",
            "Shipping case (allocated)", "other"
        ),
    ],
    variants={
        "single_serve": {
            "packaging_plastic": 0.6,
            "packaging_cardboard": 0.5,
        },
        "multi_pack": {
            # Base configuration
        },
        "family_size": {
            "packaging_plastic": 1.8,
            "packaging_cardboard": 1.5,
        },
    },
)


FOOD_BEVERAGE_TEMPLATES = {
    "beverage_bottle": BEVERAGE_BOTTLE_TEMPLATE,
    "canned_food": CANNED_FOOD_TEMPLATE,
    "packaged_snack": PACKAGED_SNACK_TEMPLATE,
}


__all__ = [
    "BEVERAGE_BOTTLE_TEMPLATE",
    "CANNED_FOOD_TEMPLATE",
    "PACKAGED_SNACK_TEMPLATE",
    "FOOD_BEVERAGE_TEMPLATES",
]
