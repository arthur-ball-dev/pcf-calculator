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
"""

from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ProductCategory


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
        Generate a comprehensive category tree for 5 industries.

        Generates a hierarchical category structure with 5 levels (0-4)
        covering electronics, apparel, automotive, construction, and
        food & beverage industries.

        All category codes are limited to 20 characters maximum to comply
        with the database schema constraint.

        Returns:
            List[Dict]: Category tree structure ready for load_categories_from_json
        """
        tree = []

        # =====================================================================
        # Electronics Industry (prefix: E)
        # =====================================================================
        tree.append({
            "code": "E",
            "name": "Electronics",
            "industry_sector": "electronics",
            "children": [
                {
                    "code": "E-CMP",
                    "name": "Computers",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "E-CMP-LPT",
                            "name": "Laptops",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-CMP-LPT-BUS",
                                    "name": "Business Laptops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-LPT-BUS-13", "name": "13-inch Business", "industry_sector": "electronics"},
                                        {"code": "E-CMP-LPT-BUS-14", "name": "14-inch Business", "industry_sector": "electronics"},
                                        {"code": "E-CMP-LPT-BUS-15", "name": "15-inch Business", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-LPT-GAM",
                                    "name": "Gaming Laptops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-LPT-GAM-15", "name": "15-inch Gaming", "industry_sector": "electronics"},
                                        {"code": "E-CMP-LPT-GAM-17", "name": "17-inch Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-LPT-ULT",
                                    "name": "Ultrabooks",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-LPT-ULT-13", "name": "13-inch Ultrabook", "industry_sector": "electronics"},
                                        {"code": "E-CMP-LPT-ULT-14", "name": "14-inch Ultrabook", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-CMP-DSK",
                            "name": "Desktop Computers",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-CMP-DSK-WRK",
                                    "name": "Workstations",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-DSK-WRK-ENT", "name": "Entry Workstation", "industry_sector": "electronics"},
                                        {"code": "E-CMP-DSK-WRK-PRO", "name": "Professional Workstation", "industry_sector": "electronics"},
                                        {"code": "E-CMP-DSK-WRK-HPC", "name": "HPC Workstation", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-DSK-GAM",
                                    "name": "Gaming Desktops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-DSK-GAM-MID", "name": "Mid-range Gaming", "industry_sector": "electronics"},
                                        {"code": "E-CMP-DSK-GAM-HI", "name": "High-end Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-DSK-AIO",
                                    "name": "All-in-One Desktops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-DSK-AIO-21", "name": "21-inch AIO", "industry_sector": "electronics"},
                                        {"code": "E-CMP-DSK-AIO-24", "name": "24-inch AIO", "industry_sector": "electronics"},
                                        {"code": "E-CMP-DSK-AIO-27", "name": "27-inch AIO", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-CMP-SRV",
                            "name": "Servers",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-CMP-SRV-RCK",
                                    "name": "Rack Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-SRV-RCK-1U", "name": "1U Rack Server", "industry_sector": "electronics"},
                                        {"code": "E-CMP-SRV-RCK-2U", "name": "2U Rack Server", "industry_sector": "electronics"},
                                        {"code": "E-CMP-SRV-RCK-4U", "name": "4U Rack Server", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-SRV-TWR",
                                    "name": "Tower Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-SRV-TWR-SMB", "name": "SMB Tower Server", "industry_sector": "electronics"},
                                        {"code": "E-CMP-SRV-TWR-ENT", "name": "Enterprise Tower", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-SRV-BLD",
                                    "name": "Blade Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-SRV-BLD-STD", "name": "Standard Blade", "industry_sector": "electronics"},
                                        {"code": "E-CMP-SRV-BLD-HI", "name": "High-density Blade", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-CMP-TAB",
                            "name": "Tablets",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-CMP-TAB-PRO",
                                    "name": "Professional Tablets",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-TAB-PRO-10", "name": "10-inch Pro Tablet", "industry_sector": "electronics"},
                                        {"code": "E-CMP-TAB-PRO-12", "name": "12-inch Pro Tablet", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-CMP-TAB-CON",
                                    "name": "Consumer Tablets",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-CMP-TAB-CON-8", "name": "8-inch Consumer Tablet", "industry_sector": "electronics"},
                                        {"code": "E-CMP-TAB-CON-10", "name": "10-inch Consumer Tablet", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "E-MOB",
                    "name": "Mobile Devices",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "E-MOB-PHN",
                            "name": "Smartphones",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-MOB-PHN-FLG",
                                    "name": "Flagship Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-PHN-FLG-STD", "name": "Standard Flagship", "industry_sector": "electronics"},
                                        {"code": "E-MOB-PHN-FLG-PRO", "name": "Pro Flagship", "industry_sector": "electronics"},
                                        {"code": "E-MOB-PHN-FLG-ULT", "name": "Ultra Flagship", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-MOB-PHN-MID",
                                    "name": "Mid-range Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-PHN-MID-A", "name": "Mid-range A Series", "industry_sector": "electronics"},
                                        {"code": "E-MOB-PHN-MID-M", "name": "Mid-range M Series", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-MOB-PHN-BUD",
                                    "name": "Budget Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-PHN-BUD-ENT", "name": "Entry Budget Phone", "industry_sector": "electronics"},
                                        {"code": "E-MOB-PHN-BUD-VAL", "name": "Value Budget Phone", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-MOB-WER",
                            "name": "Wearables",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-MOB-WER-WTC",
                                    "name": "Smartwatches",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-WER-WTC-PRO", "name": "Pro Smartwatch", "industry_sector": "electronics"},
                                        {"code": "E-MOB-WER-WTC-FIT", "name": "Fitness Smartwatch", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-MOB-WER-FIT",
                                    "name": "Fitness Bands",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-WER-FIT-BSC", "name": "Basic Fitness Band", "industry_sector": "electronics"},
                                        {"code": "E-MOB-WER-FIT-ADV", "name": "Advanced Fitness Band", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-MOB-WER-EAR",
                                    "name": "Wireless Earbuds",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-MOB-WER-EAR-PRO", "name": "Pro Earbuds", "industry_sector": "electronics"},
                                        {"code": "E-MOB-WER-EAR-STD", "name": "Standard Earbuds", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "E-AV",
                    "name": "Audio/Video",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "E-AV-TV",
                            "name": "Televisions",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-AV-TV-OLED",
                                    "name": "OLED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-TV-OLED-55", "name": "55-inch OLED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-OLED-65", "name": "65-inch OLED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-OLED-77", "name": "77-inch OLED TV", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-AV-TV-LED",
                                    "name": "LED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-TV-LED-43", "name": "43-inch LED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-LED-55", "name": "55-inch LED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-LED-65", "name": "65-inch LED TV", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-AV-TV-QLED",
                                    "name": "QLED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-TV-QLED-55", "name": "55-inch QLED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-QLED-65", "name": "65-inch QLED TV", "industry_sector": "electronics"},
                                        {"code": "E-AV-TV-QLED-75", "name": "75-inch QLED TV", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-AV-AUD",
                            "name": "Audio Equipment",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-AV-AUD-SPK",
                                    "name": "Speakers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-AUD-SPK-SND", "name": "Soundbar", "industry_sector": "electronics"},
                                        {"code": "E-AV-AUD-SPK-BLT", "name": "Bluetooth Speaker", "industry_sector": "electronics"},
                                        {"code": "E-AV-AUD-SPK-HI", "name": "Hi-Fi Speaker", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-AV-AUD-HDP",
                                    "name": "Headphones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-AUD-HDP-OVR", "name": "Over-ear Headphones", "industry_sector": "electronics"},
                                        {"code": "E-AV-AUD-HDP-ON", "name": "On-ear Headphones", "industry_sector": "electronics"},
                                        {"code": "E-AV-AUD-HDP-IEM", "name": "In-ear Monitors", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-AV-MON",
                            "name": "Monitors",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-AV-MON-PRO",
                                    "name": "Professional Monitors",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-MON-PRO-24", "name": "24-inch Pro Monitor", "industry_sector": "electronics"},
                                        {"code": "E-AV-MON-PRO-27", "name": "27-inch Pro Monitor", "industry_sector": "electronics"},
                                        {"code": "E-AV-MON-PRO-32", "name": "32-inch Pro Monitor", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-AV-MON-GAM",
                                    "name": "Gaming Monitors",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-AV-MON-GAM-24", "name": "24-inch Gaming Monitor", "industry_sector": "electronics"},
                                        {"code": "E-AV-MON-GAM-27", "name": "27-inch Gaming Monitor", "industry_sector": "electronics"},
                                        {"code": "E-AV-MON-GAM-34", "name": "34-inch UltraWide Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "E-APL",
                    "name": "Home Appliances",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "E-APL-KIT",
                            "name": "Kitchen Appliances",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-APL-KIT-REF",
                                    "name": "Refrigerators",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-APL-KIT-REF-FRD", "name": "French Door Refrigerator", "industry_sector": "electronics"},
                                        {"code": "E-APL-KIT-REF-SXS", "name": "Side-by-Side Refrigerator", "industry_sector": "electronics"},
                                        {"code": "E-APL-KIT-REF-TM", "name": "Top Mount Refrigerator", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-APL-KIT-MWV",
                                    "name": "Microwaves",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-APL-KIT-MWV-CNT", "name": "Countertop Microwave", "industry_sector": "electronics"},
                                        {"code": "E-APL-KIT-MWV-OTR", "name": "Over-the-Range Microwave", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "E-APL-LND",
                            "name": "Laundry Appliances",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "E-APL-LND-WSH",
                                    "name": "Washing Machines",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-APL-LND-WSH-FRT", "name": "Front-load Washer", "industry_sector": "electronics"},
                                        {"code": "E-APL-LND-WSH-TOP", "name": "Top-load Washer", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "E-APL-LND-DRY",
                                    "name": "Dryers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "E-APL-LND-DRY-ELC", "name": "Electric Dryer", "industry_sector": "electronics"},
                                        {"code": "E-APL-LND-DRY-GAS", "name": "Gas Dryer", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Apparel Industry (prefix: A)
        # =====================================================================
        tree.append({
            "code": "A",
            "name": "Apparel",
            "industry_sector": "apparel",
            "children": [
                {
                    "code": "A-TOP",
                    "name": "Tops",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "A-TOP-SHT",
                            "name": "Shirts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-TOP-SHT-TEE",
                                    "name": "T-Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-SHT-TEE-COT", "name": "Cotton T-Shirt", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SHT-TEE-BLD", "name": "Blended T-Shirt", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SHT-TEE-ORG", "name": "Organic T-Shirt", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-TOP-SHT-DRS",
                                    "name": "Dress Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-SHT-DRS-COT", "name": "Cotton Dress Shirt", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SHT-DRS-LNN", "name": "Linen Dress Shirt", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-TOP-SHT-POL",
                                    "name": "Polo Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-SHT-POL-PQE", "name": "Pique Polo", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SHT-POL-JRS", "name": "Jersey Polo", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "A-TOP-SWT",
                            "name": "Sweaters",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-TOP-SWT-PUL",
                                    "name": "Pullovers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-SWT-PUL-WOL", "name": "Wool Pullover", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SWT-PUL-CSH", "name": "Cashmere Pullover", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SWT-PUL-COT", "name": "Cotton Pullover", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-TOP-SWT-CRD",
                                    "name": "Cardigans",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-SWT-CRD-WOL", "name": "Wool Cardigan", "industry_sector": "apparel"},
                                        {"code": "A-TOP-SWT-CRD-COT", "name": "Cotton Cardigan", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "A-TOP-JKT",
                            "name": "Jackets",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-TOP-JKT-WIN",
                                    "name": "Winter Jackets",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-JKT-WIN-DWN", "name": "Down Jacket", "industry_sector": "apparel"},
                                        {"code": "A-TOP-JKT-WIN-PAR", "name": "Parka", "industry_sector": "apparel"},
                                        {"code": "A-TOP-JKT-WIN-PUF", "name": "Puffer Jacket", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-TOP-JKT-LGT",
                                    "name": "Light Jackets",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-TOP-JKT-LGT-WND", "name": "Windbreaker", "industry_sector": "apparel"},
                                        {"code": "A-TOP-JKT-LGT-DNM", "name": "Denim Jacket", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "A-BOT",
                    "name": "Bottoms",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "A-BOT-PNT",
                            "name": "Pants",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-BOT-PNT-JNS",
                                    "name": "Jeans",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-BOT-PNT-JNS-SKN", "name": "Skinny Jeans", "industry_sector": "apparel"},
                                        {"code": "A-BOT-PNT-JNS-STR", "name": "Straight Jeans", "industry_sector": "apparel"},
                                        {"code": "A-BOT-PNT-JNS-BFT", "name": "Bootcut Jeans", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-BOT-PNT-CHN",
                                    "name": "Chinos",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-BOT-PNT-CHN-SLM", "name": "Slim Chinos", "industry_sector": "apparel"},
                                        {"code": "A-BOT-PNT-CHN-REG", "name": "Regular Chinos", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-BOT-PNT-DRS",
                                    "name": "Dress Pants",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-BOT-PNT-DRS-WOL", "name": "Wool Dress Pants", "industry_sector": "apparel"},
                                        {"code": "A-BOT-PNT-DRS-BLD", "name": "Blend Dress Pants", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "A-BOT-SHT",
                            "name": "Shorts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-BOT-SHT-CSL",
                                    "name": "Casual Shorts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-BOT-SHT-CSL-CHN", "name": "Chino Shorts", "industry_sector": "apparel"},
                                        {"code": "A-BOT-SHT-CSL-CRG", "name": "Cargo Shorts", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-BOT-SHT-ATH",
                                    "name": "Athletic Shorts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-BOT-SHT-ATH-RUN", "name": "Running Shorts", "industry_sector": "apparel"},
                                        {"code": "A-BOT-SHT-ATH-GYM", "name": "Gym Shorts", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "A-FTW",
                    "name": "Footwear",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "A-FTW-SNK",
                            "name": "Sneakers",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-FTW-SNK-RUN",
                                    "name": "Running Sneakers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-FTW-SNK-RUN-PRF", "name": "Performance Running", "industry_sector": "apparel"},
                                        {"code": "A-FTW-SNK-RUN-CSL", "name": "Casual Running", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-FTW-SNK-BSK",
                                    "name": "Basketball Sneakers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-FTW-SNK-BSK-HI", "name": "High-top Basketball", "industry_sector": "apparel"},
                                        {"code": "A-FTW-SNK-BSK-LO", "name": "Low-top Basketball", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "A-FTW-BTS",
                            "name": "Boots",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-FTW-BTS-WRK",
                                    "name": "Work Boots",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-FTW-BTS-WRK-STL", "name": "Steel Toe Boot", "industry_sector": "apparel"},
                                        {"code": "A-FTW-BTS-WRK-CMP", "name": "Composite Toe Boot", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-FTW-BTS-FAS",
                                    "name": "Fashion Boots",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-FTW-BTS-FAS-CHE", "name": "Chelsea Boot", "industry_sector": "apparel"},
                                        {"code": "A-FTW-BTS-FAS-DST", "name": "Desert Boot", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "A-ACC",
                    "name": "Accessories",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "A-ACC-BAG",
                            "name": "Bags",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-ACC-BAG-BKP",
                                    "name": "Backpacks",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-ACC-BAG-BKP-LPT", "name": "Laptop Backpack", "industry_sector": "apparel"},
                                        {"code": "A-ACC-BAG-BKP-TRV", "name": "Travel Backpack", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "A-ACC-BAG-HND",
                                    "name": "Handbags",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-ACC-BAG-HND-TOT", "name": "Tote Bag", "industry_sector": "apparel"},
                                        {"code": "A-ACC-BAG-HND-XBD", "name": "Crossbody Bag", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "A-ACC-BLT",
                            "name": "Belts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "A-ACC-BLT-LTH",
                                    "name": "Leather Belts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "A-ACC-BLT-LTH-DRS", "name": "Dress Belt", "industry_sector": "apparel"},
                                        {"code": "A-ACC-BLT-LTH-CSL", "name": "Casual Belt", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Automotive Industry (prefix: U for aUto)
        # =====================================================================
        tree.append({
            "code": "U",
            "name": "Automotive",
            "industry_sector": "automotive",
            "children": [
                {
                    "code": "U-ENG",
                    "name": "Engine Components",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "U-ENG-INT",
                            "name": "Internal Combustion",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-ENG-INT-BLK",
                                    "name": "Engine Blocks",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-ENG-INT-BLK-4CY", "name": "4-Cylinder Block", "industry_sector": "automotive"},
                                        {"code": "U-ENG-INT-BLK-6CY", "name": "6-Cylinder Block", "industry_sector": "automotive"},
                                        {"code": "U-ENG-INT-BLK-8CY", "name": "8-Cylinder Block", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-ENG-INT-PST",
                                    "name": "Pistons",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-ENG-INT-PST-ALU", "name": "Aluminum Piston", "industry_sector": "automotive"},
                                        {"code": "U-ENG-INT-PST-FRG", "name": "Forged Piston", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-ENG-INT-VLV",
                                    "name": "Valves",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-ENG-INT-VLV-INT", "name": "Intake Valve", "industry_sector": "automotive"},
                                        {"code": "U-ENG-INT-VLV-EXH", "name": "Exhaust Valve", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "U-ENG-ELC",
                            "name": "Electric Motors",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-ENG-ELC-DRV",
                                    "name": "Drive Motors",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-ENG-ELC-DRV-150", "name": "150kW Drive Motor", "industry_sector": "automotive"},
                                        {"code": "U-ENG-ELC-DRV-200", "name": "200kW Drive Motor", "industry_sector": "automotive"},
                                        {"code": "U-ENG-ELC-DRV-300", "name": "300kW Drive Motor", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-ENG-ELC-INV",
                                    "name": "Inverters",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-ENG-ELC-INV-SIC", "name": "SiC Inverter", "industry_sector": "automotive"},
                                        {"code": "U-ENG-ELC-INV-IGB", "name": "IGBT Inverter", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "U-BRK",
                    "name": "Braking Systems",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "U-BRK-DSC",
                            "name": "Disc Brakes",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-BRK-DSC-RTR",
                                    "name": "Brake Rotors",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BRK-DSC-RTR-STL", "name": "Steel Rotor", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DSC-RTR-CRB", "name": "Carbon Ceramic Rotor", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DSC-RTR-VNT", "name": "Vented Rotor", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-BRK-DSC-PAD",
                                    "name": "Brake Pads",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BRK-DSC-PAD-SEM", "name": "Semi-Metallic Pad", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DSC-PAD-CER", "name": "Ceramic Pad", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DSC-PAD-ORG", "name": "Organic Pad", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-BRK-DSC-CAL",
                                    "name": "Brake Calipers",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BRK-DSC-CAL-FLT", "name": "Floating Caliper", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DSC-CAL-FXD", "name": "Fixed Caliper", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "U-BRK-DRM",
                            "name": "Drum Brakes",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-BRK-DRM-SHO",
                                    "name": "Brake Shoes",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BRK-DRM-SHO-STD", "name": "Standard Brake Shoe", "industry_sector": "automotive"},
                                        {"code": "U-BRK-DRM-SHO-HDY", "name": "Heavy-Duty Brake Shoe", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "U-WHL",
                    "name": "Wheels & Tires",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "U-WHL-WHL",
                            "name": "Wheels",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-WHL-WHL-ALY",
                                    "name": "Alloy Wheels",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-WHL-WHL-ALY-16", "name": "16-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "U-WHL-WHL-ALY-17", "name": "17-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "U-WHL-WHL-ALY-18", "name": "18-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "U-WHL-WHL-ALY-19", "name": "19-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "U-WHL-WHL-ALY-20", "name": "20-inch Alloy", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-WHL-WHL-STL",
                                    "name": "Steel Wheels",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-WHL-WHL-STL-15", "name": "15-inch Steel", "industry_sector": "automotive"},
                                        {"code": "U-WHL-WHL-STL-16", "name": "16-inch Steel", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "U-WHL-TIR",
                            "name": "Tires",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-WHL-TIR-SUM",
                                    "name": "Summer Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-WHL-TIR-SUM-PRF", "name": "Performance Summer", "industry_sector": "automotive"},
                                        {"code": "U-WHL-TIR-SUM-TRG", "name": "Touring Summer", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-WHL-TIR-WIN",
                                    "name": "Winter Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-WHL-TIR-WIN-STD", "name": "Studless Winter", "industry_sector": "automotive"},
                                        {"code": "U-WHL-TIR-WIN-STU", "name": "Studded Winter", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-WHL-TIR-ALL",
                                    "name": "All-Season Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-WHL-TIR-ALL-TRG", "name": "All-Season Touring", "industry_sector": "automotive"},
                                        {"code": "U-WHL-TIR-ALL-PRF", "name": "All-Season Performance", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "U-BAT",
                    "name": "Batteries",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "U-BAT-EV",
                            "name": "EV Batteries",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-BAT-EV-LIO",
                                    "name": "Li-Ion Battery Packs",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BAT-EV-LIO-40", "name": "40kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "U-BAT-EV-LIO-60", "name": "60kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "U-BAT-EV-LIO-80", "name": "80kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "U-BAT-EV-LIO-100", "name": "100kWh Li-Ion Pack", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-BAT-EV-LFP",
                                    "name": "LFP Battery Packs",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BAT-EV-LFP-50", "name": "50kWh LFP Pack", "industry_sector": "automotive"},
                                        {"code": "U-BAT-EV-LFP-75", "name": "75kWh LFP Pack", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "U-BAT-12V",
                            "name": "12V Batteries",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "U-BAT-12V-LED",
                                    "name": "Lead-Acid Batteries",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BAT-12V-LED-45", "name": "45Ah Lead-Acid", "industry_sector": "automotive"},
                                        {"code": "U-BAT-12V-LED-60", "name": "60Ah Lead-Acid", "industry_sector": "automotive"},
                                        {"code": "U-BAT-12V-LED-75", "name": "75Ah Lead-Acid", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "U-BAT-12V-AGM",
                                    "name": "AGM Batteries",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "U-BAT-12V-AGM-60", "name": "60Ah AGM", "industry_sector": "automotive"},
                                        {"code": "U-BAT-12V-AGM-80", "name": "80Ah AGM", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Construction Industry (prefix: C)
        # =====================================================================
        tree.append({
            "code": "C",
            "name": "Construction",
            "industry_sector": "construction",
            "children": [
                {
                    "code": "C-CEM",
                    "name": "Cement & Concrete",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "C-CEM-PTL",
                            "name": "Portland Cement",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-CEM-PTL-TYP",
                                    "name": "Cement Types",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-CEM-PTL-TYP-I", "name": "Type I Portland", "industry_sector": "construction"},
                                        {"code": "C-CEM-PTL-TYP-II", "name": "Type II Portland", "industry_sector": "construction"},
                                        {"code": "C-CEM-PTL-TYP-III", "name": "Type III Portland", "industry_sector": "construction"},
                                        {"code": "C-CEM-PTL-TYP-IV", "name": "Type IV Portland", "industry_sector": "construction"},
                                        {"code": "C-CEM-PTL-TYP-V", "name": "Type V Portland", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "C-CEM-CON",
                            "name": "Concrete",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-CEM-CON-RDY",
                                    "name": "Ready-Mix Concrete",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-CEM-CON-RDY-25", "name": "25 MPa Ready-Mix", "industry_sector": "construction"},
                                        {"code": "C-CEM-CON-RDY-30", "name": "30 MPa Ready-Mix", "industry_sector": "construction"},
                                        {"code": "C-CEM-CON-RDY-40", "name": "40 MPa Ready-Mix", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-CEM-CON-PRE",
                                    "name": "Precast Concrete",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-CEM-CON-PRE-BLK", "name": "Concrete Block", "industry_sector": "construction"},
                                        {"code": "C-CEM-CON-PRE-PNL", "name": "Precast Panel", "industry_sector": "construction"},
                                        {"code": "C-CEM-CON-PRE-PIP", "name": "Concrete Pipe", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "C-STL",
                    "name": "Steel Products",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "C-STL-REB",
                            "name": "Reinforcing Steel",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-STL-REB-BAR",
                                    "name": "Rebar",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-STL-REB-BAR-10", "name": "10mm Rebar", "industry_sector": "construction"},
                                        {"code": "C-STL-REB-BAR-12", "name": "12mm Rebar", "industry_sector": "construction"},
                                        {"code": "C-STL-REB-BAR-16", "name": "16mm Rebar", "industry_sector": "construction"},
                                        {"code": "C-STL-REB-BAR-20", "name": "20mm Rebar", "industry_sector": "construction"},
                                        {"code": "C-STL-REB-BAR-25", "name": "25mm Rebar", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-STL-REB-MSH",
                                    "name": "Wire Mesh",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-STL-REB-MSH-WLD", "name": "Welded Wire Mesh", "industry_sector": "construction"},
                                        {"code": "C-STL-REB-MSH-EXP", "name": "Expanded Metal Mesh", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "C-STL-STR",
                            "name": "Structural Steel",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-STL-STR-BEM",
                                    "name": "Steel Beams",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-STL-STR-BEM-I", "name": "I-Beam", "industry_sector": "construction"},
                                        {"code": "C-STL-STR-BEM-H", "name": "H-Beam", "industry_sector": "construction"},
                                        {"code": "C-STL-STR-BEM-W", "name": "Wide Flange Beam", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-STL-STR-COL",
                                    "name": "Steel Columns",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-STL-STR-COL-SQU", "name": "Square Column", "industry_sector": "construction"},
                                        {"code": "C-STL-STR-COL-RND", "name": "Round Column", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "C-INS",
                    "name": "Insulation",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "C-INS-FBR",
                            "name": "Fiber Insulation",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-INS-FBR-GLS",
                                    "name": "Fiberglass",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-INS-FBR-GLS-R13", "name": "R-13 Fiberglass", "industry_sector": "construction"},
                                        {"code": "C-INS-FBR-GLS-R19", "name": "R-19 Fiberglass", "industry_sector": "construction"},
                                        {"code": "C-INS-FBR-GLS-R30", "name": "R-30 Fiberglass", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-INS-FBR-ROK",
                                    "name": "Mineral Wool",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-INS-FBR-ROK-50", "name": "50mm Mineral Wool", "industry_sector": "construction"},
                                        {"code": "C-INS-FBR-ROK-100", "name": "100mm Mineral Wool", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "C-INS-FOM",
                            "name": "Foam Insulation",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-INS-FOM-XPS",
                                    "name": "XPS Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-INS-FOM-XPS-25", "name": "25mm XPS Board", "industry_sector": "construction"},
                                        {"code": "C-INS-FOM-XPS-50", "name": "50mm XPS Board", "industry_sector": "construction"},
                                        {"code": "C-INS-FOM-XPS-100", "name": "100mm XPS Board", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-INS-FOM-EPS",
                                    "name": "EPS Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-INS-FOM-EPS-50", "name": "50mm EPS Board", "industry_sector": "construction"},
                                        {"code": "C-INS-FOM-EPS-100", "name": "100mm EPS Board", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-INS-FOM-PIR",
                                    "name": "PIR Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-INS-FOM-PIR-50", "name": "50mm PIR Board", "industry_sector": "construction"},
                                        {"code": "C-INS-FOM-PIR-80", "name": "80mm PIR Board", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "C-LBR",
                    "name": "Lumber & Wood",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "C-LBR-DIM",
                            "name": "Dimensional Lumber",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-LBR-DIM-SFT",
                                    "name": "Softwood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-LBR-DIM-SFT-2X4", "name": "2x4 Stud", "industry_sector": "construction"},
                                        {"code": "C-LBR-DIM-SFT-2X6", "name": "2x6 Stud", "industry_sector": "construction"},
                                        {"code": "C-LBR-DIM-SFT-2X8", "name": "2x8 Joist", "industry_sector": "construction"},
                                        {"code": "C-LBR-DIM-SFT-2X10", "name": "2x10 Joist", "industry_sector": "construction"},
                                        {"code": "C-LBR-DIM-SFT-2X12", "name": "2x12 Joist", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "C-LBR-PLY",
                            "name": "Plywood",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "C-LBR-PLY-STD",
                                    "name": "Standard Plywood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-LBR-PLY-STD-12", "name": "12mm Plywood", "industry_sector": "construction"},
                                        {"code": "C-LBR-PLY-STD-18", "name": "18mm Plywood", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "C-LBR-PLY-MRN",
                                    "name": "Marine Plywood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "C-LBR-PLY-MRN-12", "name": "12mm Marine Ply", "industry_sector": "construction"},
                                        {"code": "C-LBR-PLY-MRN-18", "name": "18mm Marine Ply", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Food & Beverage Industry (prefix: F)
        # =====================================================================
        tree.append({
            "code": "F",
            "name": "Food & Beverage",
            "industry_sector": "food_beverage",
            "children": [
                {
                    "code": "F-BEV",
                    "name": "Beverages",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "F-BEV-HOT",
                            "name": "Hot Beverages",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-BEV-HOT-COF",
                                    "name": "Coffee",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-BEV-HOT-COF-ARB", "name": "Arabica Coffee", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-HOT-COF-ROB", "name": "Robusta Coffee", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-HOT-COF-BLD", "name": "Coffee Blend", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-HOT-COF-ORG", "name": "Organic Coffee", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-BEV-HOT-TEA",
                                    "name": "Tea",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-BEV-HOT-TEA-BLK", "name": "Black Tea", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-HOT-TEA-GRN", "name": "Green Tea", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-HOT-TEA-HRB", "name": "Herbal Tea", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "F-BEV-CLD",
                            "name": "Cold Beverages",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-BEV-CLD-WTR",
                                    "name": "Bottled Water",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-BEV-CLD-WTR-STL", "name": "Still Water", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-WTR-SPK", "name": "Sparkling Water", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-WTR-FLV", "name": "Flavored Water", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-BEV-CLD-JUC",
                                    "name": "Juices",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-BEV-CLD-JUC-ORG", "name": "Orange Juice", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-JUC-APL", "name": "Apple Juice", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-JUC-MIX", "name": "Mixed Fruit Juice", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-BEV-CLD-SFT",
                                    "name": "Soft Drinks",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-BEV-CLD-SFT-COL", "name": "Cola", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-SFT-LMN", "name": "Lemon-Lime Soda", "industry_sector": "food_beverage"},
                                        {"code": "F-BEV-CLD-SFT-ENR", "name": "Energy Drink", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "F-GRN",
                    "name": "Grains & Cereals",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "F-GRN-FLR",
                            "name": "Flour",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-GRN-FLR-WHT",
                                    "name": "Wheat Flour",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-GRN-FLR-WHT-AP", "name": "All-Purpose Flour", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-FLR-WHT-BRD", "name": "Bread Flour", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-FLR-WHT-WHL", "name": "Whole Wheat Flour", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-GRN-FLR-ALT",
                                    "name": "Alternative Flour",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-GRN-FLR-ALT-ALM", "name": "Almond Flour", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-FLR-ALT-OAT", "name": "Oat Flour", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-FLR-ALT-RIC", "name": "Rice Flour", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "F-GRN-CRL",
                            "name": "Cereals",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-GRN-CRL-OAT",
                                    "name": "Oats",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-GRN-CRL-OAT-RLD", "name": "Rolled Oats", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-CRL-OAT-STL", "name": "Steel-Cut Oats", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-CRL-OAT-INT", "name": "Instant Oats", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-GRN-CRL-BRK",
                                    "name": "Breakfast Cereals",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-GRN-CRL-BRK-CRN", "name": "Corn Flakes", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-CRL-BRK-GRN", "name": "Granola", "industry_sector": "food_beverage"},
                                        {"code": "F-GRN-CRL-BRK-MSL", "name": "Muesli", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "F-DRY",
                    "name": "Dairy Products",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "F-DRY-MLK",
                            "name": "Milk",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-DRY-MLK-COW",
                                    "name": "Cow's Milk",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-MLK-COW-WHL", "name": "Whole Milk", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-MLK-COW-2PC", "name": "2% Milk", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-MLK-COW-SKM", "name": "Skim Milk", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-DRY-MLK-PLT",
                                    "name": "Plant-Based Milk",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-MLK-PLT-SOY", "name": "Soy Milk", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-MLK-PLT-ALM", "name": "Almond Milk", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-MLK-PLT-OAT", "name": "Oat Milk", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "F-DRY-CHS",
                            "name": "Cheese",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-DRY-CHS-HRD",
                                    "name": "Hard Cheese",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-CHS-HRD-CHD", "name": "Cheddar Cheese", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-CHS-HRD-PAR", "name": "Parmesan Cheese", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-CHS-HRD-GOU", "name": "Gouda Cheese", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-DRY-CHS-SFT",
                                    "name": "Soft Cheese",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-CHS-SFT-BRI", "name": "Brie Cheese", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-CHS-SFT-MOZ", "name": "Mozzarella", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-CHS-SFT-FET", "name": "Feta Cheese", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "F-DRY-YGT",
                            "name": "Yogurt",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-DRY-YGT-REG",
                                    "name": "Regular Yogurt",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-YGT-REG-PLN", "name": "Plain Yogurt", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-YGT-REG-FRU", "name": "Fruit Yogurt", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-DRY-YGT-GRK",
                                    "name": "Greek Yogurt",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-DRY-YGT-GRK-PLN", "name": "Plain Greek Yogurt", "industry_sector": "food_beverage"},
                                        {"code": "F-DRY-YGT-GRK-FRU", "name": "Fruit Greek Yogurt", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "F-SNK",
                    "name": "Snacks",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "F-SNK-CHP",
                            "name": "Chips & Crisps",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-SNK-CHP-PTT",
                                    "name": "Potato Chips",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-SNK-CHP-PTT-REG", "name": "Regular Chips", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-CHP-PTT-KTL", "name": "Kettle Chips", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-CHP-PTT-RDC", "name": "Reduced Fat Chips", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-SNK-CHP-TRT",
                                    "name": "Tortilla Chips",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-SNK-CHP-TRT-YLW", "name": "Yellow Corn Tortilla", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-CHP-TRT-BLU", "name": "Blue Corn Tortilla", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "F-SNK-NUT",
                            "name": "Nuts & Seeds",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "F-SNK-NUT-RST",
                                    "name": "Roasted Nuts",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-SNK-NUT-RST-ALM", "name": "Roasted Almonds", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-NUT-RST-CSH", "name": "Roasted Cashews", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-NUT-RST-PNT", "name": "Roasted Peanuts", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "F-SNK-NUT-MIX",
                                    "name": "Mixed Nuts",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "F-SNK-NUT-MIX-TRL", "name": "Trail Mix", "industry_sector": "food_beverage"},
                                        {"code": "F-SNK-NUT-MIX-DLX", "name": "Deluxe Mixed Nuts", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        return tree
