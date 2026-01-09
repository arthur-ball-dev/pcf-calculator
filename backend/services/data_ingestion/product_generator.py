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

        # Generate product name
        variant_name = variant.replace("_", " ").title() if variant else "Standard"
        product_name = f"{template.name.title()} - {variant_name}"

        # Create product
        product = Product(
            id=str(uuid4()).replace("-", ""),
            code=product_code,
            name=product_name,
            description=f"{product_name} product generated from {template.name} template",
            unit="unit",
            is_finished_product=True,
            manufacturer=random.choice(["ProTech", "EcoSmart", "GreenEdge", "CorePro"]),
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

        # Create BOM entry
        bom = BillOfMaterials(
            id=str(uuid4()).replace("-", ""),
            parent_product_id=parent.id,
            child_product_id=component_product.id,
            quantity=quantity,
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


# ============================================================================
# Legacy ProductGenerator for backward compatibility with Phase 5 interface
# ============================================================================


class LegacyProductGenerator:
    """
    Legacy ProductGenerator for backward compatibility with Phase 5 interface.

    This class maintains the original interface for existing code that
    uses ProductGenerator without an AsyncSession parameter.

    See ProductGenerator for the new interface with BOM template support.
    """

    PRODUCT_TEMPLATES: Dict[str, List[Tuple[str, str]]] = {
        "electronics": [
            ("Business Laptop {size}-inch", "unit"),
            ("Gaming Laptop {size}-inch", "unit"),
            ("{brand} Smartphone Pro", "unit"),
            ("{size}\" LED Monitor", "unit"),
            ("Wireless {type} Headphones", "unit"),
            ("{brand} Smartwatch Series", "unit"),
            ("{type} Bluetooth Speaker", "unit"),
            ("{size}\" OLED Television", "unit"),
            ("{brand} Tablet {size}-inch", "unit"),
            ("USB-C {type} Hub", "unit"),
            ("Mechanical {type} Keyboard", "unit"),
            ("Wireless {type} Mouse", "unit"),
            ("{brand} Desktop Computer", "unit"),
            ("{size}\" Gaming Monitor", "unit"),
            ("{type} Server Rack Unit", "unit"),
            ("Home {type} Router", "unit"),
            ("{brand} Fitness Band", "unit"),
            ("4K {type} Webcam", "unit"),
            ("{type} Power Bank {capacity}mAh", "unit"),
            ("Smart {type} Thermostat", "unit"),
        ],
        "apparel": [
            ("{material} T-Shirt", "unit"),
            ("{brand} Denim Jeans", "unit"),
            ("Winter Jacket - {material}", "unit"),
            ("{type} Running Shoes", "unit"),
            ("{material} Polo Shirt", "unit"),
            ("{brand} Sweater - {type}", "unit"),
            ("{material} Dress Shirt", "unit"),
            ("{type} Athletic Shorts", "unit"),
            ("{brand} Sneakers", "unit"),
            ("{material} Cardigan", "unit"),
            ("Down {type} Parka", "unit"),
            ("{brand} Hiking Boots", "unit"),
            ("{material} Chino Pants", "unit"),
            ("Leather {type} Belt", "unit"),
            ("{brand} Backpack", "unit"),
            ("{material} Pullover Hoodie", "unit"),
            ("{type} Work Boots", "unit"),
            ("{brand} Crossbody Bag", "unit"),
            ("{material} Windbreaker", "unit"),
            ("Canvas {type} Tote Bag", "unit"),
        ],
        "automotive": [
            ("{type} Engine Component", "unit"),
            ("Brake Pad Set - {material}", "unit"),
            ("Alloy Wheel {size}\"", "unit"),
            ("Car Battery {capacity}Ah", "unit"),
            ("{type} Brake Rotor", "unit"),
            ("Spark Plug Set - {brand}", "unit"),
            ("{material} Air Filter", "unit"),
            ("{size}\" Performance Tire", "unit"),
            ("Oil Filter - {type}", "unit"),
            ("{brand} Alternator", "unit"),
            ("EV Battery Pack {capacity}kWh", "unit"),
            ("{type} Suspension Strut", "unit"),
            ("Brake Caliper - {material}", "unit"),
            ("{brand} Drive Motor", "unit"),
            ("{type} Exhaust System", "unit"),
            ("Radiator - {material}", "unit"),
            ("Transmission Fluid - {type}", "L"),
            ("{brand} Starter Motor", "unit"),
            ("Timing Belt Kit - {type}", "unit"),
            ("Coolant - {brand}", "L"),
        ],
        "construction": [
            ("Portland Cement Type {type}", "kg"),
            ("Steel Rebar {size}mm", "kg"),
            ("Concrete Block {dimensions}", "unit"),
            ("Insulation Board {thickness}mm", "unit"),
            ("Ready-Mix Concrete {type} MPa", "kg"),
            ("Fiberglass Insulation R-{size}", "unit"),
            ("Plywood Sheet {thickness}mm", "unit"),
            ("{type} I-Beam", "kg"),
            ("Lumber 2x{size}", "unit"),
            ("Wire Mesh - {type}", "unit"),
            ("XPS Foam Board {thickness}mm", "unit"),
            ("{brand} Roofing Shingles", "unit"),
            ("Mineral Wool {thickness}mm", "unit"),
            ("Structural Steel Column", "kg"),
            ("Marine Plywood {thickness}mm", "unit"),
            ("Precast Concrete Panel", "unit"),
            ("EPS Insulation {thickness}mm", "unit"),
            ("{type} Gravel", "kg"),
            ("Sand - {type} Grade", "kg"),
            ("Brick - {type}", "unit"),
        ],
        "food_beverage": [
            ("Organic {type} Coffee", "kg"),
            ("{brand} Bottled Water", "L"),
            ("Whole Grain {type} Flour", "kg"),
            ("Fresh {type} Juice", "L"),
            ("{brand} {type} Tea", "kg"),
            ("Premium {type} Cheese", "kg"),
            ("Rolled {type} Oats", "kg"),
            ("{brand} Sparkling Water", "L"),
            ("Greek {type} Yogurt", "kg"),
            ("All-Purpose {type} Flour", "kg"),
            ("Cold Brew {type} Coffee", "L"),
            ("{brand} Almond Milk", "L"),
            ("Breakfast {type} Cereal", "kg"),
            ("Roasted {type} Almonds", "kg"),
            ("{brand} Orange Juice", "L"),
            ("Kettle {type} Chips", "kg"),
            ("Whole {type} Milk", "L"),
            ("{brand} Mixed Nuts", "kg"),
            ("Tortilla {type} Chips", "kg"),
            ("Energy {type} Drink", "L"),
        ],
    }

    # Placeholder values for template filling
    _SIZE_VALUES = ["13", "14", "15", "17", "24", "27", "32", "10", "12", "16", "18", "19", "20"]
    _BRAND_VALUES = ["ProTech", "UltraMax", "EcoSmart", "PrimeLine", "CorePro", "MaxWave",
                     "TrueLife", "GreenEdge", "BluePeak", "RedLine", "SilverCrest", "GoldStar"]
    _TYPE_VALUES = ["Premium", "Standard", "Pro", "Elite", "Basic", "Advanced", "Classic",
                    "Signature", "Performance", "Value", "Executive", "Ultimate"]
    _MATERIAL_VALUES = ["Cotton", "Polyester", "Steel", "Aluminum", "Organic", "Wool",
                        "Titanium", "Composite", "Ceramic", "Carbon", "Synthetic", "Linen"]
    _CAPACITY_VALUES = ["45", "60", "75", "100", "150", "200", "3000", "5000", "10000", "20000"]
    _THICKNESS_VALUES = ["25", "50", "75", "100", "150", "200", "12", "18", "19"]
    _DIMENSIONS_VALUES = ["8x8x16", "12x8x4", "6x6x6", "4x8x16", "10x10x20", "8x4x16"]

    def __init__(self):
        """Initialize ProductGenerator."""
        pass

    async def generate_products(
        self,
        db: AsyncSession,
        categories: List[ProductCategory],
        products_per_category: int = 5
    ) -> int:
        """
        Generate sample products for each category.

        Args:
            db: AsyncSession database connection
            categories: List of ProductCategory objects to generate products for
            products_per_category: Number of products to create per category

        Returns:
            int: Total count of products created

        Example:
            generator = ProductGenerator()
            count = await generator.generate_products(db, categories, 10)
        """
        count = 0

        for category in categories:
            industry = category.industry_sector or "other"
            templates = self.PRODUCT_TEMPLATES.get(industry, [])

            if not templates:
                continue

            for i in range(products_per_category):
                template, unit = random.choice(templates)

                # Generate product name with variations
                product_name = self._fill_template(template)

                # Generate a unique product description
                description = self._generate_description(product_name, industry)

                product = Product(
                    code=f"{category.code}-{i+1:03d}",
                    name=product_name,
                    description=description,
                    unit=unit,
                    category_id=category.id,
                    manufacturer=random.choice(self._BRAND_VALUES),
                    country_of_origin=random.choice(["US", "CN", "DE", "JP", "GB", "KR", "IN", "MX", "IT", "FR"]),
                    is_finished_product=category.level >= 2,  # Leaf categories are finished products
                )
                db.add(product)
                count += 1

        await db.flush()
        return count

    def _fill_template(self, template: str) -> str:
        """
        Fill template placeholders with random values.

        Args:
            template: String with {placeholder} markers

        Returns:
            str: Template with all placeholders replaced

        Example:
            template = "Business Laptop {size}-inch"
            result = self._fill_template(template)
            # Returns something like "Business Laptop 15-inch"
        """
        result = template

        # Replace placeholders with random values
        if "{size}" in result:
            result = result.replace("{size}", random.choice(self._SIZE_VALUES))

        if "{brand}" in result:
            result = result.replace("{brand}", random.choice(self._BRAND_VALUES))

        if "{type}" in result:
            result = result.replace("{type}", random.choice(self._TYPE_VALUES))

        if "{material}" in result:
            result = result.replace("{material}", random.choice(self._MATERIAL_VALUES))

        if "{capacity}" in result:
            result = result.replace("{capacity}", random.choice(self._CAPACITY_VALUES))

        if "{thickness}" in result:
            result = result.replace("{thickness}", random.choice(self._THICKNESS_VALUES))

        if "{dimensions}" in result:
            result = result.replace("{dimensions}", random.choice(self._DIMENSIONS_VALUES))

        return result

    def _generate_description(self, product_name: str, industry: str) -> str:
        """
        Generate a product description based on name and industry.

        Args:
            product_name: Generated product name
            industry: Industry sector code

        Returns:
            str: A descriptive paragraph for the product
        """
        industry_descriptions = {
            "electronics": [
                f"High-quality {product_name} designed for optimal performance and reliability.",
                f"Advanced {product_name} featuring cutting-edge technology and premium build quality.",
                f"Professional-grade {product_name} engineered for demanding applications.",
            ],
            "apparel": [
                f"Stylish and comfortable {product_name} made from premium materials.",
                f"Durable {product_name} designed for everyday wear and lasting comfort.",
                f"Fashion-forward {product_name} combining style with exceptional quality.",
            ],
            "automotive": [
                f"Precision-engineered {product_name} meeting strict OEM specifications.",
                f"High-performance {product_name} designed for reliability and durability.",
                f"Quality-tested {product_name} for optimal vehicle performance.",
            ],
            "construction": [
                f"Industrial-grade {product_name} meeting building code requirements.",
                f"Durable {product_name} designed for structural applications.",
                f"Quality {product_name} with consistent specifications for construction projects.",
            ],
            "food_beverage": [
                f"Premium quality {product_name} sourced from trusted suppliers.",
                f"Fresh and delicious {product_name} made with natural ingredients.",
                f"Carefully crafted {product_name} meeting quality and safety standards.",
            ],
        }

        descriptions = industry_descriptions.get(industry, [
            f"Quality {product_name} designed for excellent performance.",
        ])

        return random.choice(descriptions)


__all__ = ["ProductGenerator", "LegacyProductGenerator"]
