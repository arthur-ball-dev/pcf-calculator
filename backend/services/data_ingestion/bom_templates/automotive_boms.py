"""
Automotive industry BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

Data sources:
- EPA GREET model material breakdowns (public)
- OEM sustainability reports (public)
- Academic vehicle LCA studies (public)

Note: Templates are for automotive COMPONENTS, not complete vehicles.

Templates:
- CAR_SEAT_TEMPLATE: Car seats with manual/power/heated variants
- WHEEL_ASSEMBLY_TEMPLATE: Wheel assemblies with standard/performance/economy
- DASHBOARD_TEMPLATE: Dashboard assemblies with basic/premium/digital variants

All component names map to emission factors via:
- backend/services/data_ingestion/emission_factor_mapper.py
- backend/data/emission_factor_mappings.json
"""

from .base import BOMTemplate, ComponentSpec


CAR_SEAT_TEMPLATE = BOMTemplate(
    name="car_seat",
    industry="automotive",
    typical_mass_kg=15.0,
    base_components=[
        # Frame
        ComponentSpec(
            "steel", (5.0, 8.0), "kg",
            "Frame structure", "material"
        ),

        # Covers and trim
        ComponentSpec(
            "plastic_abs", (2.0, 4.0), "kg",
            "Covers and trim", "material"
        ),

        # Upholstery
        ComponentSpec(
            "textile_polyester", (1.0, 2.0), "kg",
            "Upholstery fabric", "material"
        ),

        # Cushioning
        ComponentSpec(
            "foam_polyurethane", (2.0, 4.0), "kg",
            "Cushion foam", "material"
        ),

        # Motors (optional for power seats)
        ComponentSpec(
            "motor_electric", (0.5, 1.0), "kg",
            "Adjustment motors", "material", optional=True, probability=0.6
        ),

        # Wiring
        ComponentSpec(
            "copper", (0.2, 0.4), "kg",
            "Wiring harness", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (10, 20), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (1.0, 2.0), "kg",
            "Shipping box", "other"
        ),
    ],
    variants={
        "manual": {
            "motor_electric": 0,
            "copper": 0.5,
        },
        "power": {
            "motor_electric": 1.0,
            "copper": 1.5,
        },
        "heated": {
            "motor_electric": 1.2,
            "copper": 2.0,
        },
    },
)


WHEEL_ASSEMBLY_TEMPLATE = BOMTemplate(
    name="wheel_assembly",
    industry="automotive",
    typical_mass_kg=25.0,
    base_components=[
        # Wheel rim
        ComponentSpec(
            "aluminum", (5.0, 10.0), "kg",
            "Wheel rim", "material"
        ),

        # Tire
        ComponentSpec(
            "rubber", (8.0, 12.0), "kg",
            "Tire", "material"
        ),

        # Hub
        ComponentSpec(
            "steel", (2.0, 4.0), "kg",
            "Hub and bearings", "material"
        ),

        # Reinforcement (optional for performance)
        ComponentSpec(
            "carbon_fiber", (0.1, 0.3), "kg",
            "Reinforcement", "material", optional=True, probability=0.2
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (15, 25), "kWh",
            "Manufacturing", "energy"
        ),
    ],
    variants={
        "standard": {
            # Base configuration
        },
        "performance": {
            "aluminum": 0.8,
            "carbon_fiber": 2.0,
            "rubber": 1.1,
        },
        "economy": {
            "aluminum": 0.6,
            "steel": 1.5,
            "carbon_fiber": 0,
        },
    },
)


DASHBOARD_TEMPLATE = BOMTemplate(
    name="dashboard",
    industry="automotive",
    typical_mass_kg=8.0,
    base_components=[
        # Main structure
        ComponentSpec(
            "plastic_abs", (3.0, 5.0), "kg",
            "Dashboard shell", "material"
        ),

        # Metal reinforcement
        ComponentSpec(
            "steel", (1.0, 2.0), "kg",
            "Metal frame", "material"
        ),

        # Electronics
        ComponentSpec(
            "pcb_board", (0.2, 0.4), "kg",
            "Control boards", "material"
        ),
        ComponentSpec(
            "copper", (0.3, 0.6), "kg",
            "Wiring", "material"
        ),

        # Display (optional)
        ComponentSpec(
            "lcd_panel", (0.1, 0.3), "kg",
            "Digital display", "material", optional=True, probability=0.5
        ),

        # Instruments
        ComponentSpec(
            "glass", (0.1, 0.2), "kg",
            "Gauge covers", "material"
        ),

        # Manufacturing
        ComponentSpec(
            "electricity_manufacturing", (8, 15), "kWh",
            "Assembly", "energy"
        ),

        # Packaging
        ComponentSpec(
            "packaging_cardboard", (1.5, 3.0), "kg",
            "Shipping protection", "other"
        ),
    ],
    variants={
        "basic": {
            "lcd_panel": 0,
            "pcb_board": 0.5,
        },
        "premium": {
            "lcd_panel": 1.0,
            "pcb_board": 1.5,
            "copper": 1.5,
        },
        "digital": {
            "lcd_panel": 2.0,
            "pcb_board": 2.0,
            "glass": 0.5,
        },
    },
)


AUTOMOTIVE_TEMPLATES = {
    "car_seat": CAR_SEAT_TEMPLATE,
    "wheel_assembly": WHEEL_ASSEMBLY_TEMPLATE,
    "dashboard": DASHBOARD_TEMPLATE,
}


__all__ = [
    "CAR_SEAT_TEMPLATE",
    "WHEEL_ASSEMBLY_TEMPLATE",
    "DASHBOARD_TEMPLATE",
    "AUTOMOTIVE_TEMPLATES",
]
