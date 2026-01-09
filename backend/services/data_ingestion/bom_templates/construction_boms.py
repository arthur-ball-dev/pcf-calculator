"""
Construction industry BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

Data sources:
- Athena Impact Estimator datasets (public)
- NIST BIRDS database (public)
- Industry material specifications

Templates:
- WINDOW_UNIT_TEMPLATE: Window units with single/double/triple pane variants
- DOOR_ASSEMBLY_TEMPLATE: Door assemblies with interior/exterior/fire_rated
- HVAC_UNIT_TEMPLATE: HVAC units with residential/commercial/industrial variants

All component names map to emission factors via:
- backend/services/data_ingestion/emission_factor_mapper.py
- backend/data/emission_factor_mappings.json
"""

from .base import BOMTemplate, ComponentSpec


WINDOW_UNIT_TEMPLATE = BOMTemplate(
    name="window_unit",
    industry="construction",
    typical_mass_kg=30.0,
    base_components=[
        # Glass
        ComponentSpec(
            "glass", (10.0, 20.0), "kg",
            "Window panes", "material"
        ),

        # Frame
        ComponentSpec(
            "aluminum", (5.0, 10.0), "kg",
            "Window frame", "material"
        ),

        # Seals
        ComponentSpec(
            "rubber", (0.5, 1.0), "kg",
            "Seals and gaskets", "material"
        ),

        # Spacers
        ComponentSpec(
            "plastic_pvc", (1.0, 2.0), "kg",
            "Spacers", "material"
        ),

        # Hardware
        ComponentSpec(
            "steel", (0.5, 1.0), "kg",
            "Hardware (hinges, locks)", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (5, 10), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (2.0, 4.0), "kg",
            "Shipping protection", "other"
        ),
    ],
    variants={
        "single_pane": {
            "glass": 0.5,
            "plastic_pvc": 0.5,
        },
        "double_pane": {
            # Base configuration
        },
        "triple_pane": {
            "glass": 1.5,
            "plastic_pvc": 1.5,
            "aluminum": 1.2,
        },
    },
)


DOOR_ASSEMBLY_TEMPLATE = BOMTemplate(
    name="door_assembly",
    industry="construction",
    typical_mass_kg=40.0,
    base_components=[
        # Door panel
        ComponentSpec(
            "steel", (15.0, 25.0), "kg",
            "Door panel", "material"
        ),

        # Frame (optional wood frame)
        ComponentSpec(
            "wood_lumber", (5.0, 10.0), "kg",
            "Frame", "material", optional=True, probability=0.5
        ),

        # Glass insert (optional)
        ComponentSpec(
            "glass", (2.0, 5.0), "kg",
            "Window insert", "material", optional=True, probability=0.4
        ),

        # Sealing
        ComponentSpec(
            "rubber", (0.3, 0.6), "kg",
            "Weather sealing", "material"
        ),

        # Hardware
        ComponentSpec(
            "copper", (0.2, 0.4), "kg",
            "Lock mechanism", "material"
        ),
        ComponentSpec(
            "steel", (0.5, 1.0), "kg",
            "Hinges", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (8, 15), "kWh",
            "Manufacturing", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (3.0, 5.0), "kg",
            "Shipping", "other"
        ),
    ],
    variants={
        "interior": {
            "steel": 0.5,
            "rubber": 0.3,
            "wood_lumber": 1.0,
        },
        "exterior": {
            "steel": 1.0,
            "rubber": 1.5,
        },
        "fire_rated": {
            "steel": 1.5,
            "glass": 0,
            "rubber": 2.0,
        },
    },
)


HVAC_UNIT_TEMPLATE = BOMTemplate(
    name="hvac_unit",
    industry="construction",
    typical_mass_kg=50.0,
    base_components=[
        # Housing
        ComponentSpec(
            "steel", (15.0, 25.0), "kg",
            "Housing and frame", "material"
        ),

        # Heat exchanger
        ComponentSpec(
            "copper", (5.0, 10.0), "kg",
            "Heat exchanger coils", "material"
        ),
        ComponentSpec(
            "aluminum", (3.0, 6.0), "kg",
            "Heat exchanger fins", "material"
        ),

        # Compressor
        ComponentSpec(
            "steel", (5.0, 10.0), "kg",
            "Compressor", "material"
        ),
        ComponentSpec(
            "copper", (2.0, 4.0), "kg",
            "Compressor motor windings", "material"
        ),

        # Fan
        ComponentSpec(
            "plastic_abs", (1.0, 2.0), "kg",
            "Fan blades", "material"
        ),

        # Electronics
        ComponentSpec(
            "pcb_board", (0.2, 0.5), "kg",
            "Control board", "material"
        ),

        # Refrigerant lines
        ComponentSpec(
            "copper", (1.0, 2.0), "kg",
            "Refrigerant tubing", "material"
        ),

        # Insulation
        ComponentSpec(
            "foam_polyurethane", (1.0, 2.0), "kg",
            "Thermal insulation", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (20, 40), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (5.0, 10.0), "kg",
            "Shipping crate", "other"
        ),
    ],
    variants={
        "residential": {
            "steel": 0.7,
            "copper": 0.7,
            "aluminum": 0.7,
        },
        "commercial": {
            # Base configuration
        },
        "industrial": {
            "steel": 1.5,
            "copper": 1.5,
            "aluminum": 1.5,
            "electricity_manufacturing": 1.5,
        },
    },
)


CONSTRUCTION_TEMPLATES = {
    "window_unit": WINDOW_UNIT_TEMPLATE,
    "door_assembly": DOOR_ASSEMBLY_TEMPLATE,
    "hvac_unit": HVAC_UNIT_TEMPLATE,
}


__all__ = [
    "WINDOW_UNIT_TEMPLATE",
    "DOOR_ASSEMBLY_TEMPLATE",
    "HVAC_UNIT_TEMPLATE",
    "CONSTRUCTION_TEMPLATES",
]
