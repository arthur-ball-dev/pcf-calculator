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
                    "code": "ELEC",
                    "name": "Electronics",
                    "industry_sector": "electronics",
                    "children": [
                        {"code": "ELEC-COMP", "name": "Computers", ...}
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

        Returns:
            List[Dict]: Category tree structure ready for load_categories_from_json
        """
        tree = []

        # =====================================================================
        # Electronics Industry
        # =====================================================================
        tree.append({
            "code": "ELEC",
            "name": "Electronics",
            "industry_sector": "electronics",
            "children": [
                {
                    "code": "ELEC-COMP",
                    "name": "Computers",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "ELEC-COMP-LAPT",
                            "name": "Laptops",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-COMP-LAPT-BUS",
                                    "name": "Business Laptops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-LAPT-BUS-13", "name": "13-inch Business", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-LAPT-BUS-14", "name": "14-inch Business", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-LAPT-BUS-15", "name": "15-inch Business", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-LAPT-GAM",
                                    "name": "Gaming Laptops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-LAPT-GAM-15", "name": "15-inch Gaming", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-LAPT-GAM-17", "name": "17-inch Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-LAPT-ULT",
                                    "name": "Ultrabooks",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-LAPT-ULT-13", "name": "13-inch Ultrabook", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-LAPT-ULT-14", "name": "14-inch Ultrabook", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-COMP-DESK",
                            "name": "Desktop Computers",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-COMP-DESK-WRK",
                                    "name": "Workstations",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-DESK-WRK-ENT", "name": "Entry Workstation", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-DESK-WRK-PRO", "name": "Professional Workstation", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-DESK-WRK-HPC", "name": "HPC Workstation", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-DESK-GAM",
                                    "name": "Gaming Desktops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-DESK-GAM-MID", "name": "Mid-range Gaming", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-DESK-GAM-HI", "name": "High-end Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-DESK-AIO",
                                    "name": "All-in-One Desktops",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-DESK-AIO-21", "name": "21-inch AIO", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-DESK-AIO-24", "name": "24-inch AIO", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-DESK-AIO-27", "name": "27-inch AIO", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-COMP-SERV",
                            "name": "Servers",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-COMP-SERV-RCK",
                                    "name": "Rack Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-SERV-RCK-1U", "name": "1U Rack Server", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-SERV-RCK-2U", "name": "2U Rack Server", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-SERV-RCK-4U", "name": "4U Rack Server", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-SERV-TWR",
                                    "name": "Tower Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-SERV-TWR-SMB", "name": "SMB Tower Server", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-SERV-TWR-ENT", "name": "Enterprise Tower", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-SERV-BLD",
                                    "name": "Blade Servers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-SERV-BLD-STD", "name": "Standard Blade", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-SERV-BLD-HI", "name": "High-density Blade", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-COMP-TAB",
                            "name": "Tablets",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-COMP-TAB-PRO",
                                    "name": "Professional Tablets",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-TAB-PRO-10", "name": "10-inch Pro Tablet", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-TAB-PRO-12", "name": "12-inch Pro Tablet", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-COMP-TAB-CON",
                                    "name": "Consumer Tablets",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-COMP-TAB-CON-8", "name": "8-inch Consumer Tablet", "industry_sector": "electronics"},
                                        {"code": "ELEC-COMP-TAB-CON-10", "name": "10-inch Consumer Tablet", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "ELEC-MOBL",
                    "name": "Mobile Devices",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "ELEC-MOBL-PHON",
                            "name": "Smartphones",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-MOBL-PHON-FLG",
                                    "name": "Flagship Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-PHON-FLG-STD", "name": "Standard Flagship", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-PHON-FLG-PRO", "name": "Pro Flagship", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-PHON-FLG-ULT", "name": "Ultra Flagship", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-MOBL-PHON-MID",
                                    "name": "Mid-range Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-PHON-MID-A", "name": "Mid-range A Series", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-PHON-MID-M", "name": "Mid-range M Series", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-MOBL-PHON-BUD",
                                    "name": "Budget Phones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-PHON-BUD-ENT", "name": "Entry Budget Phone", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-PHON-BUD-VAL", "name": "Value Budget Phone", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-MOBL-WEAR",
                            "name": "Wearables",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-MOBL-WEAR-WTC",
                                    "name": "Smartwatches",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-WEAR-WTC-PRO", "name": "Pro Smartwatch", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-WEAR-WTC-FIT", "name": "Fitness Smartwatch", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-MOBL-WEAR-FIT",
                                    "name": "Fitness Bands",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-WEAR-FIT-BSC", "name": "Basic Fitness Band", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-WEAR-FIT-ADV", "name": "Advanced Fitness Band", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-MOBL-WEAR-EAR",
                                    "name": "Wireless Earbuds",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-MOBL-WEAR-EAR-PRO", "name": "Pro Earbuds", "industry_sector": "electronics"},
                                        {"code": "ELEC-MOBL-WEAR-EAR-STD", "name": "Standard Earbuds", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "ELEC-AV",
                    "name": "Audio/Video",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "ELEC-AV-TV",
                            "name": "Televisions",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-AV-TV-OLED",
                                    "name": "OLED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-TV-OLED-55", "name": "55-inch OLED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-OLED-65", "name": "65-inch OLED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-OLED-77", "name": "77-inch OLED TV", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-AV-TV-LED",
                                    "name": "LED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-TV-LED-43", "name": "43-inch LED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-LED-55", "name": "55-inch LED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-LED-65", "name": "65-inch LED TV", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-AV-TV-QLED",
                                    "name": "QLED TVs",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-TV-QLED-55", "name": "55-inch QLED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-QLED-65", "name": "65-inch QLED TV", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-TV-QLED-75", "name": "75-inch QLED TV", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-AV-AUD",
                            "name": "Audio Equipment",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-AV-AUD-SPK",
                                    "name": "Speakers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-AUD-SPK-SND", "name": "Soundbar", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-AUD-SPK-BLT", "name": "Bluetooth Speaker", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-AUD-SPK-HI", "name": "Hi-Fi Speaker", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-AV-AUD-HDP",
                                    "name": "Headphones",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-AUD-HDP-OVR", "name": "Over-ear Headphones", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-AUD-HDP-ON", "name": "On-ear Headphones", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-AUD-HDP-IEM", "name": "In-ear Monitors", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-AV-MON",
                            "name": "Monitors",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-AV-MON-PRO",
                                    "name": "Professional Monitors",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-MON-PRO-24", "name": "24-inch Pro Monitor", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-MON-PRO-27", "name": "27-inch Pro Monitor", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-MON-PRO-32", "name": "32-inch Pro Monitor", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-AV-MON-GAM",
                                    "name": "Gaming Monitors",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-AV-MON-GAM-24", "name": "24-inch Gaming Monitor", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-MON-GAM-27", "name": "27-inch Gaming Monitor", "industry_sector": "electronics"},
                                        {"code": "ELEC-AV-MON-GAM-34", "name": "34-inch UltraWide Gaming", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "ELEC-APPL",
                    "name": "Home Appliances",
                    "industry_sector": "electronics",
                    "children": [
                        {
                            "code": "ELEC-APPL-KIT",
                            "name": "Kitchen Appliances",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-APPL-KIT-REF",
                                    "name": "Refrigerators",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-APPL-KIT-REF-FRD", "name": "French Door Refrigerator", "industry_sector": "electronics"},
                                        {"code": "ELEC-APPL-KIT-REF-SXS", "name": "Side-by-Side Refrigerator", "industry_sector": "electronics"},
                                        {"code": "ELEC-APPL-KIT-REF-TM", "name": "Top Mount Refrigerator", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-APPL-KIT-MWV",
                                    "name": "Microwaves",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-APPL-KIT-MWV-CNT", "name": "Countertop Microwave", "industry_sector": "electronics"},
                                        {"code": "ELEC-APPL-KIT-MWV-OTR", "name": "Over-the-Range Microwave", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "ELEC-APPL-LND",
                            "name": "Laundry Appliances",
                            "industry_sector": "electronics",
                            "children": [
                                {
                                    "code": "ELEC-APPL-LND-WSH",
                                    "name": "Washing Machines",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-APPL-LND-WSH-FRT", "name": "Front-load Washer", "industry_sector": "electronics"},
                                        {"code": "ELEC-APPL-LND-WSH-TOP", "name": "Top-load Washer", "industry_sector": "electronics"},
                                    ]
                                },
                                {
                                    "code": "ELEC-APPL-LND-DRY",
                                    "name": "Dryers",
                                    "industry_sector": "electronics",
                                    "children": [
                                        {"code": "ELEC-APPL-LND-DRY-ELC", "name": "Electric Dryer", "industry_sector": "electronics"},
                                        {"code": "ELEC-APPL-LND-DRY-GAS", "name": "Gas Dryer", "industry_sector": "electronics"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Apparel Industry
        # =====================================================================
        tree.append({
            "code": "APRL",
            "name": "Apparel",
            "industry_sector": "apparel",
            "children": [
                {
                    "code": "APRL-TOPS",
                    "name": "Tops",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "APRL-TOPS-SHRT",
                            "name": "Shirts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-TOPS-SHRT-TEE",
                                    "name": "T-Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-SHRT-TEE-COT", "name": "Cotton T-Shirt", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SHRT-TEE-BLD", "name": "Blended T-Shirt", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SHRT-TEE-ORG", "name": "Organic T-Shirt", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-TOPS-SHRT-DRS",
                                    "name": "Dress Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-SHRT-DRS-COT", "name": "Cotton Dress Shirt", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SHRT-DRS-LNN", "name": "Linen Dress Shirt", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-TOPS-SHRT-POL",
                                    "name": "Polo Shirts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-SHRT-POL-PQE", "name": "Pique Polo", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SHRT-POL-JRS", "name": "Jersey Polo", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "APRL-TOPS-SWTR",
                            "name": "Sweaters",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-TOPS-SWTR-PUL",
                                    "name": "Pullovers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-SWTR-PUL-WOL", "name": "Wool Pullover", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SWTR-PUL-CSH", "name": "Cashmere Pullover", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SWTR-PUL-COT", "name": "Cotton Pullover", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-TOPS-SWTR-CRD",
                                    "name": "Cardigans",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-SWTR-CRD-WOL", "name": "Wool Cardigan", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-SWTR-CRD-COT", "name": "Cotton Cardigan", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "APRL-TOPS-JCKT",
                            "name": "Jackets",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-TOPS-JCKT-WIN",
                                    "name": "Winter Jackets",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-JCKT-WIN-DWN", "name": "Down Jacket", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-JCKT-WIN-PAR", "name": "Parka", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-JCKT-WIN-PUF", "name": "Puffer Jacket", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-TOPS-JCKT-LGT",
                                    "name": "Light Jackets",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-TOPS-JCKT-LGT-WND", "name": "Windbreaker", "industry_sector": "apparel"},
                                        {"code": "APRL-TOPS-JCKT-LGT-DNM", "name": "Denim Jacket", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "APRL-BOTS",
                    "name": "Bottoms",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "APRL-BOTS-PNTS",
                            "name": "Pants",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-BOTS-PNTS-JNS",
                                    "name": "Jeans",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-BOTS-PNTS-JNS-SKN", "name": "Skinny Jeans", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-PNTS-JNS-STR", "name": "Straight Jeans", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-PNTS-JNS-BFT", "name": "Bootcut Jeans", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-BOTS-PNTS-CHN",
                                    "name": "Chinos",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-BOTS-PNTS-CHN-SLM", "name": "Slim Chinos", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-PNTS-CHN-REG", "name": "Regular Chinos", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-BOTS-PNTS-DRS",
                                    "name": "Dress Pants",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-BOTS-PNTS-DRS-WOL", "name": "Wool Dress Pants", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-PNTS-DRS-BLD", "name": "Blend Dress Pants", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "APRL-BOTS-SHRT",
                            "name": "Shorts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-BOTS-SHRT-CSL",
                                    "name": "Casual Shorts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-BOTS-SHRT-CSL-CHN", "name": "Chino Shorts", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-SHRT-CSL-CRG", "name": "Cargo Shorts", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-BOTS-SHRT-ATH",
                                    "name": "Athletic Shorts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-BOTS-SHRT-ATH-RUN", "name": "Running Shorts", "industry_sector": "apparel"},
                                        {"code": "APRL-BOTS-SHRT-ATH-GYM", "name": "Gym Shorts", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "APRL-FTWR",
                    "name": "Footwear",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "APRL-FTWR-SNK",
                            "name": "Sneakers",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-FTWR-SNK-RUN",
                                    "name": "Running Sneakers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-FTWR-SNK-RUN-PRF", "name": "Performance Running", "industry_sector": "apparel"},
                                        {"code": "APRL-FTWR-SNK-RUN-CSL", "name": "Casual Running", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-FTWR-SNK-BSK",
                                    "name": "Basketball Sneakers",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-FTWR-SNK-BSK-HI", "name": "High-top Basketball", "industry_sector": "apparel"},
                                        {"code": "APRL-FTWR-SNK-BSK-LO", "name": "Low-top Basketball", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "APRL-FTWR-BTS",
                            "name": "Boots",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-FTWR-BTS-WRK",
                                    "name": "Work Boots",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-FTWR-BTS-WRK-STL", "name": "Steel Toe Boot", "industry_sector": "apparel"},
                                        {"code": "APRL-FTWR-BTS-WRK-CMP", "name": "Composite Toe Boot", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-FTWR-BTS-FAS",
                                    "name": "Fashion Boots",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-FTWR-BTS-FAS-CHE", "name": "Chelsea Boot", "industry_sector": "apparel"},
                                        {"code": "APRL-FTWR-BTS-FAS-DST", "name": "Desert Boot", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "APRL-ACCS",
                    "name": "Accessories",
                    "industry_sector": "apparel",
                    "children": [
                        {
                            "code": "APRL-ACCS-BAGS",
                            "name": "Bags",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-ACCS-BAGS-BKP",
                                    "name": "Backpacks",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-ACCS-BAGS-BKP-LPT", "name": "Laptop Backpack", "industry_sector": "apparel"},
                                        {"code": "APRL-ACCS-BAGS-BKP-TRV", "name": "Travel Backpack", "industry_sector": "apparel"},
                                    ]
                                },
                                {
                                    "code": "APRL-ACCS-BAGS-HND",
                                    "name": "Handbags",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-ACCS-BAGS-HND-TOT", "name": "Tote Bag", "industry_sector": "apparel"},
                                        {"code": "APRL-ACCS-BAGS-HND-XBD", "name": "Crossbody Bag", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "APRL-ACCS-BLTS",
                            "name": "Belts",
                            "industry_sector": "apparel",
                            "children": [
                                {
                                    "code": "APRL-ACCS-BLTS-LTH",
                                    "name": "Leather Belts",
                                    "industry_sector": "apparel",
                                    "children": [
                                        {"code": "APRL-ACCS-BLTS-LTH-DRS", "name": "Dress Belt", "industry_sector": "apparel"},
                                        {"code": "APRL-ACCS-BLTS-LTH-CSL", "name": "Casual Belt", "industry_sector": "apparel"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Automotive Industry
        # =====================================================================
        tree.append({
            "code": "AUTO",
            "name": "Automotive",
            "industry_sector": "automotive",
            "children": [
                {
                    "code": "AUTO-ENG",
                    "name": "Engine Components",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "AUTO-ENG-INT",
                            "name": "Internal Combustion",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-ENG-INT-BLK",
                                    "name": "Engine Blocks",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-ENG-INT-BLK-4CY", "name": "4-Cylinder Block", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-INT-BLK-6CY", "name": "6-Cylinder Block", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-INT-BLK-8CY", "name": "8-Cylinder Block", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-ENG-INT-PST",
                                    "name": "Pistons",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-ENG-INT-PST-ALU", "name": "Aluminum Piston", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-INT-PST-FRG", "name": "Forged Piston", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-ENG-INT-VLV",
                                    "name": "Valves",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-ENG-INT-VLV-INT", "name": "Intake Valve", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-INT-VLV-EXH", "name": "Exhaust Valve", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "AUTO-ENG-ELC",
                            "name": "Electric Motors",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-ENG-ELC-DRV",
                                    "name": "Drive Motors",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-ENG-ELC-DRV-150", "name": "150kW Drive Motor", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-ELC-DRV-200", "name": "200kW Drive Motor", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-ELC-DRV-300", "name": "300kW Drive Motor", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-ENG-ELC-INV",
                                    "name": "Inverters",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-ENG-ELC-INV-SIC", "name": "SiC Inverter", "industry_sector": "automotive"},
                                        {"code": "AUTO-ENG-ELC-INV-IGB", "name": "IGBT Inverter", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "AUTO-BRK",
                    "name": "Braking Systems",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "AUTO-BRK-DSC",
                            "name": "Disc Brakes",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-BRK-DSC-RTR",
                                    "name": "Brake Rotors",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BRK-DSC-RTR-STL", "name": "Steel Rotor", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DSC-RTR-CRB", "name": "Carbon Ceramic Rotor", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DSC-RTR-VNT", "name": "Vented Rotor", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-BRK-DSC-PAD",
                                    "name": "Brake Pads",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BRK-DSC-PAD-SEM", "name": "Semi-Metallic Pad", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DSC-PAD-CER", "name": "Ceramic Pad", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DSC-PAD-ORG", "name": "Organic Pad", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-BRK-DSC-CAL",
                                    "name": "Brake Calipers",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BRK-DSC-CAL-FLT", "name": "Floating Caliper", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DSC-CAL-FXD", "name": "Fixed Caliper", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "AUTO-BRK-DRM",
                            "name": "Drum Brakes",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-BRK-DRM-SHO",
                                    "name": "Brake Shoes",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BRK-DRM-SHO-STD", "name": "Standard Brake Shoe", "industry_sector": "automotive"},
                                        {"code": "AUTO-BRK-DRM-SHO-HDY", "name": "Heavy-Duty Brake Shoe", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "AUTO-WHL",
                    "name": "Wheels & Tires",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "AUTO-WHL-WHL",
                            "name": "Wheels",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-WHL-WHL-ALY",
                                    "name": "Alloy Wheels",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-WHL-WHL-ALY-16", "name": "16-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-WHL-ALY-17", "name": "17-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-WHL-ALY-18", "name": "18-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-WHL-ALY-19", "name": "19-inch Alloy", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-WHL-ALY-20", "name": "20-inch Alloy", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-WHL-WHL-STL",
                                    "name": "Steel Wheels",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-WHL-WHL-STL-15", "name": "15-inch Steel", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-WHL-STL-16", "name": "16-inch Steel", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "AUTO-WHL-TIR",
                            "name": "Tires",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-WHL-TIR-SUM",
                                    "name": "Summer Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-WHL-TIR-SUM-PRF", "name": "Performance Summer", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-TIR-SUM-TRG", "name": "Touring Summer", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-WHL-TIR-WIN",
                                    "name": "Winter Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-WHL-TIR-WIN-STD", "name": "Studless Winter", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-TIR-WIN-STU", "name": "Studded Winter", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-WHL-TIR-ALL",
                                    "name": "All-Season Tires",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-WHL-TIR-ALL-TRG", "name": "All-Season Touring", "industry_sector": "automotive"},
                                        {"code": "AUTO-WHL-TIR-ALL-PRF", "name": "All-Season Performance", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "AUTO-BAT",
                    "name": "Batteries",
                    "industry_sector": "automotive",
                    "children": [
                        {
                            "code": "AUTO-BAT-EV",
                            "name": "EV Batteries",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-BAT-EV-LIO",
                                    "name": "Li-Ion Battery Packs",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BAT-EV-LIO-40", "name": "40kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-EV-LIO-60", "name": "60kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-EV-LIO-80", "name": "80kWh Li-Ion Pack", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-EV-LIO-100", "name": "100kWh Li-Ion Pack", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-BAT-EV-LFP",
                                    "name": "LFP Battery Packs",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BAT-EV-LFP-50", "name": "50kWh LFP Pack", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-EV-LFP-75", "name": "75kWh LFP Pack", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "AUTO-BAT-12V",
                            "name": "12V Batteries",
                            "industry_sector": "automotive",
                            "children": [
                                {
                                    "code": "AUTO-BAT-12V-LED",
                                    "name": "Lead-Acid Batteries",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BAT-12V-LED-45", "name": "45Ah Lead-Acid", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-12V-LED-60", "name": "60Ah Lead-Acid", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-12V-LED-75", "name": "75Ah Lead-Acid", "industry_sector": "automotive"},
                                    ]
                                },
                                {
                                    "code": "AUTO-BAT-12V-AGM",
                                    "name": "AGM Batteries",
                                    "industry_sector": "automotive",
                                    "children": [
                                        {"code": "AUTO-BAT-12V-AGM-60", "name": "60Ah AGM", "industry_sector": "automotive"},
                                        {"code": "AUTO-BAT-12V-AGM-80", "name": "80Ah AGM", "industry_sector": "automotive"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Construction Industry
        # =====================================================================
        tree.append({
            "code": "CONS",
            "name": "Construction",
            "industry_sector": "construction",
            "children": [
                {
                    "code": "CONS-CEM",
                    "name": "Cement & Concrete",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "CONS-CEM-PTL",
                            "name": "Portland Cement",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-CEM-PTL-TYP",
                                    "name": "Cement Types",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-CEM-PTL-TYP-I", "name": "Type I Portland", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-PTL-TYP-II", "name": "Type II Portland", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-PTL-TYP-III", "name": "Type III Portland", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-PTL-TYP-IV", "name": "Type IV Portland", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-PTL-TYP-V", "name": "Type V Portland", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "CONS-CEM-CON",
                            "name": "Concrete",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-CEM-CON-RDY",
                                    "name": "Ready-Mix Concrete",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-CEM-CON-RDY-25", "name": "25 MPa Ready-Mix", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-CON-RDY-30", "name": "30 MPa Ready-Mix", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-CON-RDY-40", "name": "40 MPa Ready-Mix", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-CEM-CON-PRE",
                                    "name": "Precast Concrete",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-CEM-CON-PRE-BLK", "name": "Concrete Block", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-CON-PRE-PNL", "name": "Precast Panel", "industry_sector": "construction"},
                                        {"code": "CONS-CEM-CON-PRE-PIP", "name": "Concrete Pipe", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "CONS-STL",
                    "name": "Steel Products",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "CONS-STL-REB",
                            "name": "Reinforcing Steel",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-STL-REB-BAR",
                                    "name": "Rebar",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-STL-REB-BAR-10", "name": "10mm Rebar", "industry_sector": "construction"},
                                        {"code": "CONS-STL-REB-BAR-12", "name": "12mm Rebar", "industry_sector": "construction"},
                                        {"code": "CONS-STL-REB-BAR-16", "name": "16mm Rebar", "industry_sector": "construction"},
                                        {"code": "CONS-STL-REB-BAR-20", "name": "20mm Rebar", "industry_sector": "construction"},
                                        {"code": "CONS-STL-REB-BAR-25", "name": "25mm Rebar", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-STL-REB-MSH",
                                    "name": "Wire Mesh",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-STL-REB-MSH-WLD", "name": "Welded Wire Mesh", "industry_sector": "construction"},
                                        {"code": "CONS-STL-REB-MSH-EXP", "name": "Expanded Metal Mesh", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "CONS-STL-STR",
                            "name": "Structural Steel",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-STL-STR-BEM",
                                    "name": "Steel Beams",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-STL-STR-BEM-I", "name": "I-Beam", "industry_sector": "construction"},
                                        {"code": "CONS-STL-STR-BEM-H", "name": "H-Beam", "industry_sector": "construction"},
                                        {"code": "CONS-STL-STR-BEM-W", "name": "Wide Flange Beam", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-STL-STR-COL",
                                    "name": "Steel Columns",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-STL-STR-COL-SQU", "name": "Square Column", "industry_sector": "construction"},
                                        {"code": "CONS-STL-STR-COL-RND", "name": "Round Column", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "CONS-INS",
                    "name": "Insulation",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "CONS-INS-FBR",
                            "name": "Fiber Insulation",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-INS-FBR-GLS",
                                    "name": "Fiberglass",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-INS-FBR-GLS-R13", "name": "R-13 Fiberglass", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FBR-GLS-R19", "name": "R-19 Fiberglass", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FBR-GLS-R30", "name": "R-30 Fiberglass", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-INS-FBR-ROK",
                                    "name": "Mineral Wool",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-INS-FBR-ROK-50", "name": "50mm Mineral Wool", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FBR-ROK-100", "name": "100mm Mineral Wool", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "CONS-INS-FOM",
                            "name": "Foam Insulation",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-INS-FOM-XPS",
                                    "name": "XPS Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-INS-FOM-XPS-25", "name": "25mm XPS Board", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FOM-XPS-50", "name": "50mm XPS Board", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FOM-XPS-100", "name": "100mm XPS Board", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-INS-FOM-EPS",
                                    "name": "EPS Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-INS-FOM-EPS-50", "name": "50mm EPS Board", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FOM-EPS-100", "name": "100mm EPS Board", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-INS-FOM-PIR",
                                    "name": "PIR Foam",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-INS-FOM-PIR-50", "name": "50mm PIR Board", "industry_sector": "construction"},
                                        {"code": "CONS-INS-FOM-PIR-80", "name": "80mm PIR Board", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "CONS-LBR",
                    "name": "Lumber & Wood",
                    "industry_sector": "construction",
                    "children": [
                        {
                            "code": "CONS-LBR-DIM",
                            "name": "Dimensional Lumber",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-LBR-DIM-SFT",
                                    "name": "Softwood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-LBR-DIM-SFT-2X4", "name": "2x4 Stud", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-DIM-SFT-2X6", "name": "2x6 Stud", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-DIM-SFT-2X8", "name": "2x8 Joist", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-DIM-SFT-2X10", "name": "2x10 Joist", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-DIM-SFT-2X12", "name": "2x12 Joist", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "CONS-LBR-PLY",
                            "name": "Plywood",
                            "industry_sector": "construction",
                            "children": [
                                {
                                    "code": "CONS-LBR-PLY-STD",
                                    "name": "Standard Plywood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-LBR-PLY-STD-12", "name": "12mm Plywood", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-PLY-STD-18", "name": "18mm Plywood", "industry_sector": "construction"},
                                    ]
                                },
                                {
                                    "code": "CONS-LBR-PLY-MRN",
                                    "name": "Marine Plywood",
                                    "industry_sector": "construction",
                                    "children": [
                                        {"code": "CONS-LBR-PLY-MRN-12", "name": "12mm Marine Ply", "industry_sector": "construction"},
                                        {"code": "CONS-LBR-PLY-MRN-18", "name": "18mm Marine Ply", "industry_sector": "construction"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        # =====================================================================
        # Food & Beverage Industry
        # =====================================================================
        tree.append({
            "code": "FB",
            "name": "Food & Beverage",
            "industry_sector": "food_beverage",
            "children": [
                {
                    "code": "FB-BEV",
                    "name": "Beverages",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "FB-BEV-HOT",
                            "name": "Hot Beverages",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-BEV-HOT-COF",
                                    "name": "Coffee",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-BEV-HOT-COF-ARB", "name": "Arabica Coffee", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-HOT-COF-ROB", "name": "Robusta Coffee", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-HOT-COF-BLD", "name": "Coffee Blend", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-HOT-COF-ORG", "name": "Organic Coffee", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-BEV-HOT-TEA",
                                    "name": "Tea",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-BEV-HOT-TEA-BLK", "name": "Black Tea", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-HOT-TEA-GRN", "name": "Green Tea", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-HOT-TEA-HRB", "name": "Herbal Tea", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "FB-BEV-CLD",
                            "name": "Cold Beverages",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-BEV-CLD-WTR",
                                    "name": "Bottled Water",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-BEV-CLD-WTR-STL", "name": "Still Water", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-WTR-SPK", "name": "Sparkling Water", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-WTR-FLV", "name": "Flavored Water", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-BEV-CLD-JUC",
                                    "name": "Juices",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-BEV-CLD-JUC-ORG", "name": "Orange Juice", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-JUC-APL", "name": "Apple Juice", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-JUC-MIX", "name": "Mixed Fruit Juice", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-BEV-CLD-SFT",
                                    "name": "Soft Drinks",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-BEV-CLD-SFT-COL", "name": "Cola", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-SFT-LMN", "name": "Lemon-Lime Soda", "industry_sector": "food_beverage"},
                                        {"code": "FB-BEV-CLD-SFT-ENR", "name": "Energy Drink", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "FB-GRN",
                    "name": "Grains & Cereals",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "FB-GRN-FLR",
                            "name": "Flour",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-GRN-FLR-WHT",
                                    "name": "Wheat Flour",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-GRN-FLR-WHT-AP", "name": "All-Purpose Flour", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-FLR-WHT-BRD", "name": "Bread Flour", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-FLR-WHT-WHL", "name": "Whole Wheat Flour", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-GRN-FLR-ALT",
                                    "name": "Alternative Flour",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-GRN-FLR-ALT-ALM", "name": "Almond Flour", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-FLR-ALT-OAT", "name": "Oat Flour", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-FLR-ALT-RIC", "name": "Rice Flour", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "FB-GRN-CRL",
                            "name": "Cereals",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-GRN-CRL-OAT",
                                    "name": "Oats",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-GRN-CRL-OAT-RLD", "name": "Rolled Oats", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-CRL-OAT-STL", "name": "Steel-Cut Oats", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-CRL-OAT-INT", "name": "Instant Oats", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-GRN-CRL-BRK",
                                    "name": "Breakfast Cereals",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-GRN-CRL-BRK-CRN", "name": "Corn Flakes", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-CRL-BRK-GRN", "name": "Granola", "industry_sector": "food_beverage"},
                                        {"code": "FB-GRN-CRL-BRK-MSL", "name": "Muesli", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "FB-DRY",
                    "name": "Dairy Products",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "FB-DRY-MLK",
                            "name": "Milk",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-DRY-MLK-COW",
                                    "name": "Cow's Milk",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-MLK-COW-WHL", "name": "Whole Milk", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-MLK-COW-2PC", "name": "2% Milk", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-MLK-COW-SKM", "name": "Skim Milk", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-DRY-MLK-PLT",
                                    "name": "Plant-Based Milk",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-MLK-PLT-SOY", "name": "Soy Milk", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-MLK-PLT-ALM", "name": "Almond Milk", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-MLK-PLT-OAT", "name": "Oat Milk", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "FB-DRY-CHS",
                            "name": "Cheese",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-DRY-CHS-HRD",
                                    "name": "Hard Cheese",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-CHS-HRD-CHD", "name": "Cheddar Cheese", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-CHS-HRD-PAR", "name": "Parmesan Cheese", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-CHS-HRD-GOU", "name": "Gouda Cheese", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-DRY-CHS-SFT",
                                    "name": "Soft Cheese",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-CHS-SFT-BRI", "name": "Brie Cheese", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-CHS-SFT-MOZ", "name": "Mozzarella", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-CHS-SFT-FET", "name": "Feta Cheese", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "FB-DRY-YGT",
                            "name": "Yogurt",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-DRY-YGT-REG",
                                    "name": "Regular Yogurt",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-YGT-REG-PLN", "name": "Plain Yogurt", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-YGT-REG-FRU", "name": "Fruit Yogurt", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-DRY-YGT-GRK",
                                    "name": "Greek Yogurt",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-DRY-YGT-GRK-PLN", "name": "Plain Greek Yogurt", "industry_sector": "food_beverage"},
                                        {"code": "FB-DRY-YGT-GRK-FRU", "name": "Fruit Greek Yogurt", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
                {
                    "code": "FB-SNK",
                    "name": "Snacks",
                    "industry_sector": "food_beverage",
                    "children": [
                        {
                            "code": "FB-SNK-CHP",
                            "name": "Chips & Crisps",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-SNK-CHP-PTT",
                                    "name": "Potato Chips",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-SNK-CHP-PTT-REG", "name": "Regular Chips", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-CHP-PTT-KTL", "name": "Kettle Chips", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-CHP-PTT-RDC", "name": "Reduced Fat Chips", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-SNK-CHP-TRT",
                                    "name": "Tortilla Chips",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-SNK-CHP-TRT-YLW", "name": "Yellow Corn Tortilla", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-CHP-TRT-BLU", "name": "Blue Corn Tortilla", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                        {
                            "code": "FB-SNK-NUT",
                            "name": "Nuts & Seeds",
                            "industry_sector": "food_beverage",
                            "children": [
                                {
                                    "code": "FB-SNK-NUT-RST",
                                    "name": "Roasted Nuts",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-SNK-NUT-RST-ALM", "name": "Roasted Almonds", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-NUT-RST-CSH", "name": "Roasted Cashews", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-NUT-RST-PNT", "name": "Roasted Peanuts", "industry_sector": "food_beverage"},
                                    ]
                                },
                                {
                                    "code": "FB-SNK-NUT-MIX",
                                    "name": "Mixed Nuts",
                                    "industry_sector": "food_beverage",
                                    "children": [
                                        {"code": "FB-SNK-NUT-MIX-TRL", "name": "Trail Mix", "industry_sector": "food_beverage"},
                                        {"code": "FB-SNK-NUT-MIX-DLX", "name": "Deluxe Mixed Nuts", "industry_sector": "food_beverage"},
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        })

        return tree
