"""
ProductGenerator - Generate sample products for categories.

TASK-DATA-P5-005: Product Catalog Expansion

This module provides the ProductGenerator class for generating
sample products for each category in the product catalog.

Features:
- Industry-specific product templates
- Placeholder-based name generation
- Automatic product code generation
- Support for various units of measure

Usage:
    from backend.services.data_ingestion.product_generator import ProductGenerator

    generator = ProductGenerator()
    count = await generator.generate_products(db, categories, products_per_category=10)
"""

import random
from typing import List, Dict, Tuple, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Product, ProductCategory


class ProductGenerator:
    """
    Generate sample products for each category.

    Uses industry-specific templates with placeholder values
    to create realistic product names and descriptions.

    Attributes:
        PRODUCT_TEMPLATES: Dict mapping industry sectors to
            lists of (template, unit) tuples.
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
            ("Brake Pad Set - {material}", "set"),
            ("Alloy Wheel {size}\"", "unit"),
            ("Car Battery {capacity}Ah", "unit"),
            ("{type} Brake Rotor", "unit"),
            ("Spark Plug Set - {brand}", "set"),
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
            ("Transmission Fluid - {type}", "liter"),
            ("{brand} Starter Motor", "unit"),
            ("Timing Belt Kit - {type}", "set"),
            ("Coolant - {brand}", "liter"),
        ],
        "construction": [
            ("Portland Cement Type {type}", "tonne"),
            ("Steel Rebar {size}mm", "tonne"),
            ("Concrete Block {dimensions}", "unit"),
            ("Insulation Board {thickness}mm", "sqm"),
            ("Ready-Mix Concrete {type} MPa", "m3"),
            ("Fiberglass Insulation R-{size}", "sqm"),
            ("Plywood Sheet {thickness}mm", "unit"),
            ("{type} I-Beam", "tonne"),
            ("Lumber 2x{size}", "unit"),
            ("Wire Mesh - {type}", "sqm"),
            ("XPS Foam Board {thickness}mm", "sqm"),
            ("{brand} Roofing Shingles", "sqm"),
            ("Mineral Wool {thickness}mm", "sqm"),
            ("Structural Steel Column", "tonne"),
            ("Marine Plywood {thickness}mm", "unit"),
            ("Precast Concrete Panel", "unit"),
            ("EPS Insulation {thickness}mm", "sqm"),
            ("{type} Gravel", "tonne"),
            ("Sand - {type} Grade", "tonne"),
            ("Brick - {type}", "unit"),
        ],
        "food_beverage": [
            ("Organic {type} Coffee", "kg"),
            ("{brand} Bottled Water", "liter"),
            ("Whole Grain {type} Flour", "kg"),
            ("Fresh {type} Juice", "liter"),
            ("{brand} {type} Tea", "kg"),
            ("Premium {type} Cheese", "kg"),
            ("Rolled {type} Oats", "kg"),
            ("{brand} Sparkling Water", "liter"),
            ("Greek {type} Yogurt", "kg"),
            ("All-Purpose {type} Flour", "kg"),
            ("Cold Brew {type} Coffee", "liter"),
            ("{brand} Almond Milk", "liter"),
            ("Breakfast {type} Cereal", "kg"),
            ("Roasted {type} Almonds", "kg"),
            ("{brand} Orange Juice", "liter"),
            ("Kettle {type} Chips", "kg"),
            ("Whole {type} Milk", "liter"),
            ("{brand} Mixed Nuts", "kg"),
            ("Tortilla {type} Chips", "kg"),
            ("Energy {type} Drink", "liter"),
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
