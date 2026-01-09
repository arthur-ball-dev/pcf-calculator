"""
Base classes for BOM templates.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

This module provides the foundational classes for generating realistic
Bill of Materials (BOM) templates for product carbon footprint calculations.

Classes:
    ComponentSpec: Specification for a single BOM component with quantity ranges
    BOMTemplate: Template for generating complete product BOMs with variants

Usage:
    from backend.services.data_ingestion.bom_templates.base import (
        BOMTemplate,
        ComponentSpec,
    )

    # Define components
    components = [
        ComponentSpec("aluminum", (0.5, 1.0), "kg", "Chassis", "material"),
        ComponentSpec("copper", (0.05, 0.1), "kg", "Wiring", "material"),
    ]

    # Create template
    template = BOMTemplate(
        name="laptop",
        industry="electronics",
        base_components=components,
        variants={"gaming": {"aluminum": 1.5}},
    )

    # Generate BOM
    bom_components = template.get_components(variant="gaming")
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
import random


@dataclass
class ComponentSpec:
    """
    Specification for a BOM component.

    Defines a component with a name that maps to emission factors,
    a quantity range for random generation, unit of measurement,
    and category classification.

    Attributes:
        name: Component name (maps to emission factor activity_name)
        qty_range: Tuple of (min, max) quantity values
        unit: Unit of measurement (kg, kWh, L, tkm, etc.)
        description: Optional human-readable description
        category: Component category (material, energy, transport, other)
        optional: If True, component may be omitted based on probability
        probability: Probability of inclusion if optional (0.0 to 1.0)

    Example:
        >>> spec = ComponentSpec(
        ...     name="aluminum",
        ...     qty_range=(0.5, 1.5),
        ...     unit="kg",
        ...     description="Aluminum chassis",
        ...     category="material",
        ... )
        >>> qty = spec.generate_quantity()
        >>> 0.5 <= float(qty) <= 1.5
        True
    """

    name: str  # Maps to emission factor activity_name
    qty_range: Tuple[float, float]  # (min, max) quantity
    unit: str
    description: Optional[str] = None
    category: str = "material"  # material, energy, transport, other
    optional: bool = False  # If True, may be omitted from some products
    probability: float = 1.0  # Probability of inclusion if optional

    def generate_quantity(self) -> Decimal:
        """
        Generate random quantity within the specified range.

        Returns:
            Decimal: Random quantity rounded to 4 decimal places

        Example:
            >>> spec = ComponentSpec("steel", (1.0, 2.0), "kg")
            >>> qty = spec.generate_quantity()
            >>> isinstance(qty, Decimal)
            True
        """
        qty = random.uniform(self.qty_range[0], self.qty_range[1])
        return Decimal(str(round(qty, 4)))


@dataclass
class BOMTemplate:
    """
    Template for generating product BOMs.

    Defines a product type with base components, variant modifiers,
    and typical mass for transport calculations. Templates can generate
    realistic BOMs with random quantities within specified ranges.

    Attributes:
        name: Template name (e.g., "laptop", "tshirt")
        industry: Industry classification (electronics, apparel, etc.)
        base_components: List of ComponentSpec defining the BOM structure
        variants: Dict of variant names to modifier dicts
        product_name_pattern: Pattern for generating product names
        typical_mass_kg: Typical product mass for transport calculations

    Example:
        >>> from backend.services.data_ingestion.bom_templates.base import (
        ...     BOMTemplate,
        ...     ComponentSpec,
        ... )
        >>> components = [
        ...     ComponentSpec("aluminum", (0.5, 1.0), "kg"),
        ...     ComponentSpec("copper", (0.05, 0.1), "kg"),
        ... ]
        >>> template = BOMTemplate(
        ...     name="laptop",
        ...     industry="electronics",
        ...     base_components=components,
        ...     variants={"gaming": {"aluminum": 1.5}},
        ... )
        >>> bom = template.get_components(variant="gaming")
        >>> len(bom) >= 2
        True
    """

    name: str
    industry: str
    base_components: List[ComponentSpec]
    variants: Dict[str, Dict[str, float]] = field(default_factory=dict)
    product_name_pattern: str = "{industry}_{variant}_{index}"
    typical_mass_kg: float = 1.0  # For transport calculations

    def get_components(
        self,
        variant: Optional[str] = None
    ) -> List[ComponentSpec]:
        """
        Get components with variant modifiers applied.

        Applies variant modifiers to quantity ranges and handles optional
        component inclusion based on probability.

        Args:
            variant: Optional variant name for applying modifiers

        Returns:
            List[ComponentSpec]: Modified component specifications

        Example:
            >>> template = BOMTemplate(
            ...     name="test",
            ...     industry="test",
            ...     base_components=[
            ...         ComponentSpec("aluminum", (1.0, 2.0), "kg"),
            ...     ],
            ...     variants={"heavy": {"aluminum": 2.0}},
            ... )
            >>> components = template.get_components(variant="heavy")
            >>> components[0].qty_range
            (2.0, 4.0)
        """
        components = []
        variant_mods = self.variants.get(variant, {}) if variant else {}

        for comp in self.base_components:
            # Apply variant modifier if present
            modifier = variant_mods.get(comp.name, 1.0)
            if modifier == 0:
                continue  # Skip this component for this variant

            # Check if optional component should be included
            if comp.optional and random.random() > comp.probability:
                continue

            # Create modified component
            modified = ComponentSpec(
                name=comp.name,
                qty_range=(
                    comp.qty_range[0] * modifier,
                    comp.qty_range[1] * modifier,
                ),
                unit=comp.unit,
                description=comp.description,
                category=comp.category,
                optional=comp.optional,
            )
            components.append(modified)

        return components

    def calculate_transport(
        self,
        mass_kg: float,
        truck_distance_km: float = 300,
        ship_distance_km: float = 5000,
    ) -> List[ComponentSpec]:
        """
        Calculate transport components based on product mass.

        Generates transport component specifications for truck and ship
        freight based on mass and typical distances. Includes 10% variance
        in quantity ranges.

        Args:
            mass_kg: Product mass in kilograms
            truck_distance_km: Domestic/regional truck distance (default 300km)
            ship_distance_km: International shipping distance (default 5000km)

        Returns:
            List[ComponentSpec]: Transport component specifications

        Example:
            >>> template = BOMTemplate("test", "test", [])
            >>> transport = template.calculate_transport(2.0, 300, 5000)
            >>> len(transport)
            2
            >>> transport[0].name
            'transport_truck'
        """
        mass_tonnes = mass_kg / 1000

        # Calculate base tonne-km values
        truck_tkm = mass_tonnes * truck_distance_km
        ship_tkm = mass_tonnes * ship_distance_km

        return [
            ComponentSpec(
                name="transport_truck",
                qty_range=(
                    truck_tkm * 0.9,
                    truck_tkm * 1.1,
                ),
                unit="tkm",
                description="Domestic/regional shipping",
                category="transport",
            ),
            ComponentSpec(
                name="transport_ship",
                qty_range=(
                    ship_tkm * 0.9,
                    ship_tkm * 1.1,
                ),
                unit="tkm",
                description="International shipping",
                category="transport",
            ),
        ]


__all__ = [
    "ComponentSpec",
    "BOMTemplate",
]
