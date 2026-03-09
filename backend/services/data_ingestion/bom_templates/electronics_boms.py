"""
Electronics industry BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)
TASK-BE-P8-002: Product Catalog Generation - Units match DEFRA (kg for gas, m3 for water)

Data sources:
- iFixit teardown reports (public)
- Apple Environmental Reports (public PDFs)
- Dell product carbon footprints (public)

Templates:
- LAPTOP_TEMPLATE: Laptops with business/gaming/ultrabook variants
- SMARTPHONE_TEMPLATE: Smartphones with flagship/budget variants
- MONITOR_TEMPLATE: Computer monitors with size variants
- TABLET_TEMPLATE: Tablets with standard/pro variants

All component names map to emission factors via:
- backend/services/data_ingestion/emission_factor_mapper.py
- backend/data/emission_factor_mappings.json
"""

from .base import BOMTemplate, ComponentSpec


LAPTOP_TEMPLATE = BOMTemplate(
    name="laptop",
    industry="electronics",
    typical_mass_kg=2.0,
    base_components=[
        # Chassis and structure
        ComponentSpec(
            "aluminum", (0.6, 1.2), "kg",
            "Chassis/housing", "material"
        ),
        ComponentSpec(
            "steel", (0.05, 0.15), "kg",
            "Screws and fasteners", "material"
        ),
        ComponentSpec(
            "plastic_abs", (0.2, 0.5), "kg",
            "Keyboard, palm rest", "material"
        ),
        ComponentSpec(
            "glass", (0.1, 0.2), "kg",
            "Display cover", "material"
        ),
        ComponentSpec(
            "magnesium", (0.05, 0.15), "kg",
            "Internal frame", "material", optional=True, probability=0.5
        ),

        # Electronics
        ComponentSpec(
            "copper", (0.08, 0.15), "kg",
            "Wiring and traces", "material"
        ),
        ComponentSpec(
            "pcb_board", (0.1, 0.2), "kg",
            "Main board", "material"
        ),
        ComponentSpec(
            "lithium_ion_battery", (0.2, 0.4), "kg",
            "Battery pack", "material"
        ),
        ComponentSpec(
            "semiconductor", (0.02, 0.05), "kg",
            "CPU, GPU, chips", "material"
        ),

        # Display
        ComponentSpec(
            "lcd_panel", (0.15, 0.3), "kg",
            "LCD display", "material", optional=True, probability=0.7
        ),
        ComponentSpec(
            "led_backlight", (0.02, 0.05), "kg",
            "Backlight unit", "material", optional=True, probability=0.7
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (50, 100), "kWh",
            "Assembly electricity", "energy"
        ),
        ComponentSpec(
            "natural_gas_manufacturing", (0.5, 1.5), "kg",
            "Manufacturing heat", "energy"
        ),
        ComponentSpec(
            "water_process", (0.02, 0.05), "m3",
            "Manufacturing water", "other"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.3, 0.6), "kg",
            "Box packaging", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.05, 0.15), "kg",
            "Protective wrap", "other"
        ),

        # End of life
        ComponentSpec(
            "waste_general", (0.05, 0.1), "kg",
            "Manufacturing scrap", "other"
        ),
    ],
    variants={
        "business_13": {
            "aluminum": 0.8,
            "electricity_manufacturing": 0.9,
            "lithium_ion_battery": 0.8,
        },
        "gaming_17": {
            "aluminum": 1.4,
            "electricity_manufacturing": 1.5,
            "lithium_ion_battery": 1.5,
            "copper": 1.3,
        },
        "ultrabook": {
            "aluminum": 1.2,
            "plastic_abs": 0.5,
            "steel": 0.5,
            "magnesium": 1.5,
        },
    },
)


SMARTPHONE_TEMPLATE = BOMTemplate(
    name="smartphone",
    industry="electronics",
    typical_mass_kg=0.2,
    base_components=[
        # Structure
        ComponentSpec(
            "aluminum", (0.02, 0.05), "kg",
            "Frame", "material"
        ),
        ComponentSpec(
            "glass", (0.03, 0.06), "kg",
            "Screen and back", "material"
        ),
        ComponentSpec(
            "stainless_steel", (0.005, 0.01), "kg",
            "Buttons and SIM tray", "material"
        ),

        # Electronics
        ComponentSpec(
            "lithium_ion_battery", (0.04, 0.06), "kg",
            "Battery", "material"
        ),
        ComponentSpec(
            "pcb_board", (0.02, 0.04), "kg",
            "Main board", "material"
        ),
        ComponentSpec(
            "semiconductor", (0.005, 0.01), "kg",
            "SoC, memory", "material"
        ),
        ComponentSpec(
            "copper", (0.01, 0.02), "kg",
            "Wiring", "material"
        ),
        ComponentSpec(
            "plastic_abs", (0.01, 0.03), "kg",
            "Internal parts", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (15, 35), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.05, 0.1), "kg",
            "Box", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.02, 0.05), "kg",
            "Wrap", "other"
        ),
    ],
    variants={
        "flagship": {
            "semiconductor": 1.3,
            "electricity_manufacturing": 1.2,
            "glass": 1.2,
        },
        "budget": {
            "semiconductor": 0.7,
            "glass": 0.8,
            "aluminum": 0.6,
        },
    },
)


MONITOR_TEMPLATE = BOMTemplate(
    name="monitor",
    industry="electronics",
    typical_mass_kg=5.0,
    base_components=[
        # Structure
        ComponentSpec(
            "plastic_abs", (1.0, 2.0), "kg",
            "Housing", "material"
        ),
        ComponentSpec(
            "steel", (0.5, 1.0), "kg",
            "Stand and frame", "material"
        ),
        ComponentSpec(
            "aluminum", (0.2, 0.5), "kg",
            "Stand base", "material"
        ),

        # Display
        ComponentSpec(
            "lcd_panel", (0.8, 1.5), "kg",
            "LCD panel", "material"
        ),
        ComponentSpec(
            "glass", (0.3, 0.6), "kg",
            "Screen surface", "material"
        ),
        ComponentSpec(
            "led_backlight", (0.05, 0.1), "kg",
            "Backlight", "material"
        ),

        # Electronics
        ComponentSpec(
            "pcb_board", (0.1, 0.2), "kg",
            "Control board", "material"
        ),
        ComponentSpec(
            "copper", (0.1, 0.2), "kg",
            "Cables and wiring", "material"
        ),
        ComponentSpec(
            "capacitor", (0.02, 0.05), "kg",
            "Power supply capacitors", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (25, 50), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.8, 1.5), "kg",
            "Box", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.1, 0.3), "kg",
            "Foam and wrap", "other"
        ),
        ComponentSpec(
            "foam_eps", (0.2, 0.4), "kg",
            "EPS foam protection", "other"
        ),
    ],
    variants={
        "24_inch": {
            "lcd_panel": 0.8,
            "glass": 0.8,
            "plastic_abs": 0.8,
        },
        "27_inch": {
            # Standard - no modifier needed
        },
        "32_inch": {
            "lcd_panel": 1.3,
            "glass": 1.3,
            "plastic_abs": 1.2,
            "packaging_cardboard": 1.3,
        },
    },
)


TABLET_TEMPLATE = BOMTemplate(
    name="tablet",
    industry="electronics",
    typical_mass_kg=0.5,
    base_components=[
        # Structure
        ComponentSpec(
            "aluminum", (0.15, 0.3), "kg",
            "Chassis", "material"
        ),
        ComponentSpec(
            "glass", (0.1, 0.2), "kg",
            "Screen", "material"
        ),

        # Electronics
        ComponentSpec(
            "lithium_ion_battery", (0.1, 0.2), "kg",
            "Battery", "material"
        ),
        ComponentSpec(
            "pcb_board", (0.05, 0.1), "kg",
            "Main board", "material"
        ),
        ComponentSpec(
            "semiconductor", (0.01, 0.02), "kg",
            "SoC, memory", "material"
        ),
        ComponentSpec(
            "copper", (0.02, 0.04), "kg",
            "Wiring", "material"
        ),
        ComponentSpec(
            "lcd_panel", (0.08, 0.15), "kg",
            "Display", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (15, 30), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (0.1, 0.2), "kg",
            "Box", "other"
        ),
        ComponentSpec(
            "packaging_plastic", (0.03, 0.06), "kg",
            "Wrap", "other"
        ),
    ],
    variants={
        "standard": {
            # Base configuration
        },
        "pro": {
            "semiconductor": 1.4,
            "lithium_ion_battery": 1.3,
            "aluminum": 1.2,
        },
    },
)


ELECTRONICS_TEMPLATES = {
    "laptop": LAPTOP_TEMPLATE,
    "smartphone": SMARTPHONE_TEMPLATE,
    "monitor": MONITOR_TEMPLATE,
    "tablet": TABLET_TEMPLATE,
}


__all__ = [
    "LAPTOP_TEMPLATE",
    "SMARTPHONE_TEMPLATE",
    "MONITOR_TEMPLATE",
    "TABLET_TEMPLATE",
    "ELECTRONICS_TEMPLATES",
]
