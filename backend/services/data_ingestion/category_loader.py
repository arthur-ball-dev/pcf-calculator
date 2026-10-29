"""
CategoryLoader - Hierarchical product category loading.

TASK-DATA-P5-005: Product Catalog Expansion

This module provides the CategoryLoader class for loading hierarchical
product categories from JSON structures into the database.

Features:
- Recursive category tree loading with parent-child relationships
- Support for 5+ level hierarchies
- Industry sector classification
- Automatic level calculation
- Pre-defined category tree generation for 5 industries

Usage:
    from backend.services.data_ingestion.category_loader import CategoryLoader

    loader = CategoryLoader()
    tree = loader.generate_category_tree()
    count = await loader.load_categories_from_json(db, tree)

Note:
    Category codes are limited to 20 characters to comply with the
    product_categories.code column constraint (String(20)).
    Industry prefixes use single-character abbreviations:
    - E = Electronics
    - A = Apparel
    - U = Automotive (aUto)
    - C = Construction
    - F = Food & Beverage

    The category tree data is stored in data/category_tree.json and
    loaded at runtime by generate_category_tree().
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ProductCategory


# Resolve the path to data/category_tree.json relative to project root.
# The project root is 3 levels up from this file:
#   backend/services/data_ingestion/category_loader.py -> project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CATEGORY_TREE_PATH = _PROJECT_ROOT / "data" / "category_tree.json"


class CategoryLoader:
    """
    Load hierarchical product categories from various sources.

    Supports loading categories from JSON structures with recursive
    parent-child relationships and automatic level calculation.

    Attributes:
        INDUSTRY_SECTORS: List of supported industry sector codes.
    """

    INDUSTRY_SECTORS = [
        "electronics",
        "apparel",
        "automotive",
        "construction",
        "food_beverage",
        "chemicals",
        "machinery",
        "other",
    ]

    async def load_categories_from_json(
        self,
        db: AsyncSession,
        categories_data: List[Dict],
        parent_id: Optional[str] = None,
        level: int = 0
    ) -> int:
        """
        Recursively load categories from JSON structure.

        Args:
            db: AsyncSession database connection
            categories_data: List of category dictionaries with optional 'children'
            parent_id: Parent category ID (None for root categories)
            level: Current hierarchy level (0 for root)

        Returns:
            int: Total count of categories created

        Example:
            categories_data = [
                {
                    "code": "E",
                    "name": "Electronics",
                    "industry_sector": "electronics",
                    "children": [
                        {"code": "E-CMP", "name": "Computers", ...}
                    ]
                }
            ]
        """
        count = 0

        for cat_data in categories_data:
            # Create category
            category = ProductCategory(
                code=cat_data["code"],
                name=cat_data["name"],
                parent_id=parent_id,
                level=level,
                industry_sector=cat_data.get("industry_sector"),
            )
            db.add(category)
            await db.flush()
            count += 1

            # Process children recursively
            if "children" in cat_data:
                count += await self.load_categories_from_json(
                    db,
                    cat_data["children"],
                    parent_id=category.id,
                    level=level + 1
                )

        return count

    def generate_category_tree(self) -> List[Dict]:
        """
        Load a comprehensive category tree for 5 industries from JSON.

        Loads the hierarchical category structure with 5 levels (0-4)
        covering electronics, apparel, automotive, construction, and
        food & beverage industries from data/category_tree.json.

        All category codes are limited to 20 characters maximum to comply
        with the database schema constraint.

        Returns:
            List[Dict]: Category tree structure ready for load_categories_from_json

        Raises:
            FileNotFoundError: If data/category_tree.json does not exist
        """
        with open(_CATEGORY_TREE_PATH, "r", encoding="utf-8") as f:
            tree = json.load(f)

        return tree
