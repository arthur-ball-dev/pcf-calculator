"""
ProductGenerator - Generate products with detailed BOMs for PCF calculations.

TASK-BE-P8-002: Product Catalog Generation (600-850 Products)

This module provides the ProductGenerator class for generating finished products
with complete Bill of Materials (BOM) structures. Products are created using
industry-specific BOM templates with emission factor mapping.

Features:
- Async database session support
- BOM template-based generation
- Emission factor mapping via EmissionFactorMapper
- Transport calculation per template mass
- Variant selection for product customization
- Batch commits every 50 products
- Statistics tracking

Usage:
    from backend.services.data_ingestion.product_generator import ProductGenerator

    async with get_async_session() as session:
        generator = ProductGenerator(session)
        products = await generator.generate_industry_products(
            industry="electronics",
            count=175,
        )
        await session.commit()
        print(generator.get_stats())

Product Code Pattern:
    {IND}-{TMPL}-{VAR}-{INDEX}
    - IND: First 3 chars of industry (uppercase)
    - TMPL: First 4 chars of template name (uppercase)
    - VAR: First 3 chars of variant or "BASE" (uppercase)
    - INDEX: 4-digit zero-padded index
"""

import logging
import random
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Product, BillOfMaterials, EmissionFactor, ProductCategory
from backend.services.data_ingestion.bom_templates import (
    BOMTemplate,
    ComponentSpec,
    ALL_TEMPLATES,
)
from backend.services.data_ingestion.product_name_pools import ProductNameGenerator


logger = logging.getLogger(__name__)


class ProductGenerator:
    """
    Generate finished products with complete BOMs.

    Uses BOM templates to create realistic products with component structures
    that map to emission factors for carbon footprint calculations.

    Attributes:
        db: AsyncSession for database operations
        mapper: EmissionFactorMapper for factor lookups (optional)
        stats: Dictionary tracking generation statistics
        _component_cache: Cache of component products by code

    Example:
        generator = ProductGenerator(async_session)
        products = await generator.generate_industry_products("electronics", 100)
        stats = generator.get_stats()
    """

    # Industry code prefixes
    INDUSTRY_CODES = {
        "electronics": "ELE",
        "apparel": "APP",
        "automotive": "AUT",
        "construction": "CON",
        "food_beverage": "FOD",
    }

    # Batch size for database commits
    BATCH_SIZE = 50

    # Valid units per Product model CHECK constraint
    # 'unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm'
    VALID_UNITS = {'unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm'}

    # Unit mapping for template units not in VALID_UNITS
    UNIT_MAPPING = {
        'm3': 'L',  # cubic meters -> liters (1 m3 = 1000 L, but unit is just for type)
        'm2': 'unit',  # square meters -> unit
        'Wh': 'kWh',  # watt-hours -> kilowatt-hours
        'J': 'MJ',  # joules -> megajoules
        'ton': 'kg',  # metric ton -> kg
        'tonnes': 'kg',  # tonnes -> kg
        't': 'kg',  # tonnes -> kg
        'km': 'm',  # kilometers -> meters
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize ProductGenerator with database session.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.mapper = None  # Optional: EmissionFactorMapper instance
        self.stats = {
            "products_created": 0,
            "bom_entries_created": 0,
            "components_created": 0,
            "mapping_failures": 0,
            "by_industry": {},
        }
        self._component_cache: Dict[str, Product] = {}
        self._product_index_counter: Dict[str, int] = {}
        self._name_generator = ProductNameGenerator()

    def _normalize_unit(self, unit: str) -> str:
        """
        Normalize unit to a valid Product model unit.

        Args:
            unit: Original unit from template

        Returns:
            str: Valid unit for Product model
        """
        if unit in self.VALID_UNITS:
            return unit
        if unit in self.UNIT_MAPPING:
            return self.UNIT_MAPPING[unit]
        # Default fallback
        logger.warning(f"Unknown unit '{unit}', defaulting to 'unit'")
        return 'unit'

    async def generate_product_with_detailed_bom(
        self,
        template: BOMTemplate,
        variant: Optional[str] = None,
        product_index: int = 1,
    ) -> Product:
        """
        Generate a single product with complete BOM from template.

        Creates a finished product and its BOM entries based on the template
        components and variant modifiers. Transport components are automatically
        calculated based on template typical mass.

        Args:
            template: BOMTemplate defining the product structure
            variant: Optional variant name for component modifiers
            product_index: Index number for unique code generation

        Returns:
            Product: Created product instance with BOM entries

        Example:
            from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

            template = ALL_TEMPLATES["electronics"]["laptop"]
            product = await generator.generate_product_with_detailed_bom(
                template=template,
                variant="gaming_17",
                product_index=1,
            )
        """
        # Generate unique product code
        industry_code = self.INDUSTRY_CODES.get(
            template.industry, template.industry[:3].upper()
        )
        template_code = template.name[:4].upper()
        variant_code = (variant[:3] if variant else "BAS").upper()
        product_code = f"{industry_code}-{template_code}-{variant_code}-{product_index:04d}"

        # Generate unique product name via fictional brand pools
        product_name, brand_name = self._name_generator.generate_unique_name(
            template_name=template.name,
            variant=variant,
            industry=template.industry,
            product_index=product_index,
        )

        # Create product
        product = Product(
            id=str(uuid4()).replace("-", ""),
            code=product_code,
            name=product_name,
            description=f"{product_name} - {template.name.replace('_', ' ').title()} by {brand_name}",
            unit="unit",
            category=template.industry,  # Set category for product selector grouping
            is_finished_product=True,
            manufacturer=brand_name,
            country_of_origin=random.choice(["US", "CN", "DE", "JP", "GB", "KR"]),
            product_metadata={
                "template": template.name,
                "variant": variant,
                "industry": template.industry,
                "typical_mass_kg": template.typical_mass_kg,
            },
        )

        self.db.add(product)
        await self.db.flush()

        # Get template components with variant modifiers
        components = template.get_components(variant=variant)

        # Add transport components based on typical mass
        transport_components = template.calculate_transport(template.typical_mass_kg)
        components.extend(transport_components)

        # Aggregate components with same name to avoid unique constraint violation
        # When multiple components have the same name (e.g., textile_polyester for
        # both outer shell and insulation), we sum their quantities
        aggregated_components: Dict[str, ComponentSpec] = {}
        for comp in components:
            if comp.name in aggregated_components:
                # Merge quantities by creating a new ComponentSpec with summed range
                existing = aggregated_components[comp.name]
                new_min = existing.qty_range[0] + comp.qty_range[0]
                new_max = existing.qty_range[1] + comp.qty_range[1]
                aggregated_components[comp.name] = ComponentSpec(
                    name=comp.name,
                    qty_range=(new_min, new_max),
                    unit=comp.unit,
                    description=f"{existing.description or ''} + {comp.description or ''}".strip(' +'),
                    category=comp.category,
                )
            else:
                aggregated_components[comp.name] = comp

        # Create BOM entries for each aggregated component
        for comp in aggregated_components.values():
            bom_entry = await self._create_bom_entry(product, comp, variant)
            if bom_entry:
                self.stats["bom_entries_created"] += 1

        self.stats["products_created"] += 1

        return product

    async def _create_bom_entry(
        self,
        parent: Product,
        component: ComponentSpec,
        variant: Optional[str] = None,
    ) -> Optional[BillOfMaterials]:
        """
        Create a single BOM entry linking parent to component.

        Looks up or creates the component product and links it to the parent
        via a BillOfMaterials entry with a quantity within the component range.

        Args:
            parent: Parent product for the BOM entry
            component: ComponentSpec defining the component
            variant: Optional variant for context

        Returns:
            BillOfMaterials: Created BOM entry, or None if component creation failed

        Note:
            If a mapper is set, emission factor availability is validated before
            creating the component. If no mapper is set, components are always
            created and emission factor lookup happens at calculation time.
        """
        # Get or create component product
        component_product = await self._get_or_create_component_product(component)

        if component_product is None:
            self.stats["mapping_failures"] += 1
            logger.warning(
                f"Failed to create component product: {component.name}"
            )
            return None

        # Generate quantity within range
        quantity = component.generate_quantity()

        # Normalize unit to valid Product unit
        normalized_unit = self._normalize_unit(component.unit)

        # Look up emission factor for this component
        emission_factor_id = None
        if self.mapper:
            factor = await self.mapper.get_factor_for_component(
                component_name=component_product.name,
                unit=normalized_unit,
            )
            if factor:
                emission_factor_id = factor.id

        # Create BOM entry
        bom = BillOfMaterials(
            id=str(uuid4()).replace("-", ""),
            parent_product_id=parent.id,
            child_product_id=component_product.id,
            quantity=quantity,
            unit=normalized_unit,
            emission_factor_id=emission_factor_id,
        )

        self.db.add(bom)
        return bom

    async def _get_or_create_component_product(
        self,
        component: ComponentSpec,
    ) -> Optional[Product]:
        """
        Get existing component product or create new one.

        Uses a cache to avoid duplicate lookups. Creates new component
        products as needed.

        If a mapper is set and returns None for the component's emission factor,
        the component will not be created and None is returned. This allows for
        strict emission factor validation during product generation.

        If no mapper is set, components are always created and emission factor
        lookup happens at calculation time via EmissionFactorMapper.

        Args:
            component: ComponentSpec defining the component

        Returns:
            Product: Existing or newly created component product, or None if
                     mapper validation fails
        """
        # Check cache first
        if component.name in self._component_cache:
            return self._component_cache[component.name]

        # Look up existing product
        result = await self.db.execute(
            select(Product).where(Product.code == component.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            self._component_cache[component.name] = existing
            return existing

        # If mapper is set, validate emission factor exists before creating product
        if self.mapper is not None:
            factor = await self.mapper.get_factor_for_component(
                component.name,
                component.unit,
            )
            if factor is None:
                logger.warning(
                    f"No emission factor found for component: {component.name} ({component.unit})"
                )
                return None

        # Normalize unit to valid Product unit
        normalized_unit = self._normalize_unit(component.unit)

        # Create new component product
        component_product = Product(
            id=str(uuid4()).replace("-", ""),
            code=component.name,
            name=component.name.replace("_", " ").title(),
            description=component.description or f"{component.name} component",
            unit=normalized_unit,
            is_finished_product=False,
            product_metadata={
                "category": component.category,
                "is_component": True,
                "original_unit": component.unit if component.unit != normalized_unit else None,
            },
        )

        self.db.add(component_product)
        await self.db.flush()

        self._component_cache[component.name] = component_product
        self.stats["components_created"] += 1

        return component_product

    async def generate_industry_products(
        self,
        industry: str,
        count: int,
    ) -> List[Product]:
        """
        Generate multiple products for an industry.

        Rotates through available templates and variants for variety.
        Commits in batches of 50 products for memory efficiency.

        Args:
            industry: Industry name (electronics, apparel, automotive,
                construction, food_beverage)
            count: Number of products to generate

        Returns:
            List[Product]: List of created products

        Raises:
            ValueError: If industry is unknown

        Example:
            products = await generator.generate_industry_products(
                industry="electronics",
                count=175,
            )
        """
        if industry not in ALL_TEMPLATES:
            raise ValueError(
                f"Unknown industry: {industry}. "
                f"Available: {list(ALL_TEMPLATES.keys())}"
            )

        templates = list(ALL_TEMPLATES[industry].values())
        products = []

        # Initialize industry counter
        if industry not in self.stats["by_industry"]:
            self.stats["by_industry"][industry] = 0

        # Initialize product index counter for this industry
        if industry not in self._product_index_counter:
            self._product_index_counter[industry] = 0

        for i in range(count):
            # Rotate through templates
            template = templates[i % len(templates)]

            # Select variant (including None for base)
            variants = list(template.variants.keys()) + [None]
            variant = random.choice(variants)

            # Get next index for this industry
            self._product_index_counter[industry] += 1
            product_index = self._product_index_counter[industry]

            # Generate product
            product = await self.generate_product_with_detailed_bom(
                template=template,
                variant=variant,
                product_index=product_index,
            )
            products.append(product)

            # Batch commit
            if (i + 1) % self.BATCH_SIZE == 0:
                await self.db.commit()
                logger.info(
                    f"Generated {i + 1}/{count} {industry} products"
                )

        # Final commit
        await self.db.commit()
        self.stats["by_industry"][industry] = len(products)

        logger.info(
            f"Completed {industry}: {len(products)} products generated"
        )

        return products

    async def generate_full_catalog(
        self,
        distribution: Optional[Dict[str, int]] = None,
    ) -> Dict[str, List[Product]]:
        """
        Generate complete product catalog across all industries.

        Uses default distribution matching target of 600-850 products
        or accepts custom distribution.

        Args:
            distribution: Optional dict mapping industry to count.
                Default: Electronics 175, Apparel 175, Automotive 125,
                Construction 175, Food & Beverage 75 (Total: 725)

        Returns:
            Dict[str, List[Product]]: Products by industry

        Example:
            catalog = await generator.generate_full_catalog()
            total = sum(len(p) for p in catalog.values())
        """
        if distribution is None:
            distribution = {
                "electronics": 175,
                "apparel": 175,
                "automotive": 125,
                "construction": 175,
                "food_beverage": 75,
            }

        catalog = {}
        for industry, count in distribution.items():
            if industry in ALL_TEMPLATES:
                products = await self.generate_industry_products(industry, count)
                catalog[industry] = products
            else:
                logger.warning(f"Skipping unknown industry: {industry}")

        return catalog

    def get_stats(self) -> Dict[str, Any]:
        """
        Get copy of generation statistics.

        Returns:
            Dict[str, Any]: Copy of stats dictionary including:
                - products_created: Total products
                - bom_entries_created: Total BOM entries
                - components_created: Unique component products
                - mapping_failures: Failed emission factor lookups
                - by_industry: Counts by industry
        """
        return self.stats.copy()


__all__ = ["ProductGenerator"]
