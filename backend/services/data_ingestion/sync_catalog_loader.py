"""
SyncCatalogLoader - Synchronous catalog loading for tests.

TASK-DATA-P5-005: Product Catalog Expansion - Bug Fix

This module provides synchronous versions of CategoryLoader and ProductGenerator
for use in test fixtures that use synchronous SQLAlchemy sessions.

The async versions in category_loader.py and product_generator.py are used
for production code with AsyncSession. This sync version is specifically
for test fixtures using standard Session.

Usage:
    from backend.services.data_ingestion.sync_catalog_loader import SyncCatalogLoader

    loader = SyncCatalogLoader()
    result = loader.load_full_catalog(session, products_per_category=5)
"""

import random
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models import Product, ProductCategory
from backend.services.data_ingestion.category_loader import CategoryLoader
from backend.services.data_ingestion.product_generator import ProductGenerator


class SyncCatalogLoader:
    """
    Synchronous catalog loader for test fixtures.

    Provides sync versions of category loading and product generation
    for use with standard SQLAlchemy Session (not AsyncSession).

    Generates 1000+ categories across 10+ industries with 5 levels of hierarchy.
    """

    # Valid units according to Product model's CHECK constraint
    VALID_UNITS = {'unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm'}

    # Map invalid units to valid ones
    UNIT_MAPPING = {
        'set': 'unit',      # "Brake Pad Set" -> unit
        'pair': 'unit',     # pairs -> unit
        'piece': 'unit',    # pieces -> unit
        'each': 'unit',     # each -> unit
        'pack': 'unit',     # pack -> unit
        'box': 'unit',      # box -> unit
        'roll': 'unit',     # roll -> unit
        'sheet': 'unit',    # sheet -> unit
        'bottle': 'unit',   # bottle -> unit
        'can': 'unit',      # can -> unit
        'tube': 'unit',     # tube -> unit
        'bag': 'unit',      # bag -> unit
    }

    # Additional industries to reach 1000+ categories
    ADDITIONAL_INDUSTRIES = {
        "chemicals": {
            "prefix": "CH",
            "subcategories": [
                ("BSC", "Basic Chemicals", [
                    ("ORG", "Organic Chemicals", [
                        ("ETH", "Ethylene", ["HDG", "LDG", "PRM"]),
                        ("PRO", "Propylene", ["STD", "PLY", "GRD"]),
                        ("BTD", "Butadiene", ["CRD", "REF", "PUR"]),
                        ("BNZ", "Benzene", ["IND", "LAB", "SPE"]),
                        ("TOL", "Toluene", ["IND", "LAB", "SLV"]),
                        ("XYL", "Xylene", ["ORT", "PAR", "MIX"]),
                    ]),
                    ("INO", "Inorganic Chemicals", [
                        ("ACD", "Acids", ["HCL", "H2S", "NIT", "PHS"]),
                        ("ALK", "Alkalis", ["NAO", "KOH", "CAO"]),
                        ("SLT", "Salts", ["SOD", "POT", "CAL"]),
                    ]),
                ]),
                ("SPE", "Specialty Chemicals", [
                    ("ADH", "Adhesives", [
                        ("EPX", "Epoxy", ["2PT", "1PT", "STR"]),
                        ("ACR", "Acrylic", ["CLR", "COL", "STR"]),
                        ("PUR", "Polyurethane", ["FLX", "RIG", "FOA"]),
                    ]),
                    ("CAT", "Catalysts", [
                        ("HET", "Heterogeneous", ["ZEO", "MET", "OXD"]),
                        ("HOM", "Homogeneous", ["ORG", "MET", "ENZ"]),
                    ]),
                    ("SRF", "Surfactants", [
                        ("ANI", "Anionic", ["SLS", "LES", "SOS"]),
                        ("CAT", "Cationic", ["QAC", "AMI", "EST"]),
                        ("NON", "Non-ionic", ["APE", "ALC", "EST"]),
                    ]),
                ]),
                ("AGR", "Agrochemicals", [
                    ("FRT", "Fertilizers", [
                        ("NIT", "Nitrogen", ["URA", "AMN", "NIT"]),
                        ("PHS", "Phosphorus", ["DAP", "MAP", "TSP"]),
                        ("POT", "Potassium", ["MOP", "SOP", "KNO"]),
                    ]),
                    ("PES", "Pesticides", [
                        ("HRB", "Herbicides", ["GLY", "PAR", "ATR"]),
                        ("INS", "Insecticides", ["PYR", "NEO", "ORG"]),
                        ("FUN", "Fungicides", ["AZO", "STR", "COP"]),
                    ]),
                ]),
            ]
        },
        "machinery": {
            "prefix": "M",
            "subcategories": [
                ("IND", "Industrial Machinery", [
                    ("CNC", "CNC Machines", [
                        ("LAT", "Lathes", ["2AX", "3AX", "4AX", "5AX"]),
                        ("MIL", "Milling", ["VRT", "HRZ", "UNV"]),
                        ("GRN", "Grinding", ["SRF", "CYL", "CNT"]),
                        ("DRL", "Drilling", ["RAD", "VRT", "HRZ"]),
                    ]),
                    ("PRS", "Presses", [
                        ("HYD", "Hydraulic", ["50T", "100T", "200T", "500T"]),
                        ("MEC", "Mechanical", ["OBS", "CRA", "KNU"]),
                        ("PNE", "Pneumatic", ["LOW", "MED", "HI"]),
                    ]),
                    ("CON", "Conveyors", [
                        ("BLT", "Belt", ["FLT", "TRG", "MOD"]),
                        ("RLR", "Roller", ["GRV", "PWR", "ACC"]),
                        ("CHN", "Chain", ["SLT", "DRG", "ENC"]),
                    ]),
                ]),
                ("PKG", "Packaging Machinery", [
                    ("FIL", "Filling", [
                        ("LIQ", "Liquid", ["GRV", "PIS", "PER"]),
                        ("PWD", "Powder", ["AUG", "VAC", "NET"]),
                        ("GRN", "Granule", ["VOL", "WGT", "CNT"]),
                    ]),
                    ("SEA", "Sealing", [
                        ("HSL", "Heat Seal", ["BAR", "IMP", "ROT"]),
                        ("ULT", "Ultrasonic", ["PLG", "ROT", "LIN"]),
                        ("IND", "Induction", ["CAP", "LIN", "FOI"]),
                    ]),
                    ("WRP", "Wrapping", [
                        ("SHR", "Shrink", ["TUN", "GUN", "LWR"]),
                        ("STR", "Stretch", ["TBL", "RBT", "ARM"]),
                        ("FLW", "Flow", ["HRZ", "VRT", "INV"]),
                    ]),
                ]),
                ("MTL", "Material Handling", [
                    ("FRK", "Forklifts", [
                        ("ELC", "Electric", ["3WH", "4WH", "RCH"]),
                        ("LPG", "LPG", ["STD", "HDY", "RGH"]),
                        ("DSL", "Diesel", ["STD", "HDY", "CNT"]),
                    ]),
                    ("CRN", "Cranes", [
                        ("OVH", "Overhead", ["SNG", "DBL", "GNT"]),
                        ("JIB", "Jib", ["WMT", "FLR", "MOB"]),
                        ("MOB", "Mobile", ["RGH", "ALL", "CRW"]),
                    ]),
                    ("HOI", "Hoists", [
                        ("ELC", "Electric", ["CHN", "WIR", "BLT"]),
                        ("PNE", "Pneumatic", ["CHN", "BAL", "TRL"]),
                        ("MAN", "Manual", ["CHN", "LVR", "RCH"]),
                    ]),
                ]),
            ]
        },
        "healthcare": {
            "prefix": "H",
            "subcategories": [
                ("MED", "Medical Devices", [
                    ("DIA", "Diagnostic", [
                        ("IMG", "Imaging", ["MRI", "CTN", "XRY", "ULT"]),
                        ("MON", "Monitoring", ["ECG", "BPM", "PLS", "SPO"]),
                        ("LAB", "Laboratory", ["HEM", "CHM", "IMM"]),
                    ]),
                    ("SUR", "Surgical", [
                        ("INS", "Instruments", ["SCL", "FRC", "RET", "CLP"]),
                        ("IMP", "Implants", ["ORT", "CRD", "DEN"]),
                        ("ROB", "Robotic", ["ARM", "END", "MIC"]),
                    ]),
                    ("PRS", "Prosthetics", [
                        ("LMB", "Limb", ["LEG", "ARM", "HND", "FT"]),
                        ("JNT", "Joint", ["HIP", "KNE", "SHL", "ELB"]),
                        ("SEN", "Sensory", ["AUD", "VIS", "NEU"]),
                    ]),
                ]),
                ("PHA", "Pharmaceuticals", [
                    ("API", "Active Ingredients", [
                        ("SYN", "Synthetic", ["SMO", "PEP", "OLI"]),
                        ("NAT", "Natural", ["EXT", "FRM", "BIO"]),
                        ("BIO", "Biological", ["MAB", "VAC", "ENZ"]),
                    ]),
                    ("DOS", "Dosage Forms", [
                        ("SOL", "Solid", ["TAB", "CAP", "PWD"]),
                        ("LIQ", "Liquid", ["SYR", "SUS", "SOL"]),
                        ("TOP", "Topical", ["CRM", "OIN", "GEL", "PTH"]),
                    ]),
                ]),
                ("CON", "Consumables", [
                    ("SYR", "Syringes", [
                        ("DSP", "Disposable", ["1ML", "3ML", "5ML", "10ML"]),
                        ("SAF", "Safety", ["RET", "SHD", "NED"]),
                    ]),
                    ("GLV", "Gloves", [
                        ("LTX", "Latex", ["PWD", "PFR", "STR"]),
                        ("NIT", "Nitrile", ["STD", "EXT", "CHM"]),
                        ("VNL", "Vinyl", ["CLR", "BLU", "PWD"]),
                    ]),
                    ("MSK", "Masks", [
                        ("SRG", "Surgical", ["L1", "L2", "L3"]),
                        ("N95", "N95", ["STD", "VLV", "KN95"]),
                        ("FAC", "Face Shields", ["FUL", "HLF", "VIS"]),
                    ]),
                ]),
            ]
        },
        "packaging": {
            "prefix": "P",
            "subcategories": [
                ("PLS", "Plastics", [
                    ("FLM", "Films", [
                        ("LDP", "LDPE", ["CLR", "COL", "PRT"]),
                        ("HDP", "HDPE", ["CLR", "WHT", "BLK"]),
                        ("BOP", "BOPP", ["CLR", "MET", "MTT"]),
                        ("PET", "PET", ["CLR", "GRN", "AMB"]),
                    ]),
                    ("CON", "Containers", [
                        ("BTL", "Bottles", ["PET", "HDP", "PP"]),
                        ("JAR", "Jars", ["SQR", "RND", "WMO"]),
                        ("TUB", "Tubs", ["RND", "SQR", "OVL"]),
                    ]),
                    ("CLO", "Closures", [
                        ("SCP", "Screw Caps", ["STD", "CRC", "TER"]),
                        ("FLP", "Flip Tops", ["HNG", "SNP", "DSC"]),
                        ("PMP", "Pumps", ["LOT", "TRG", "FOA"]),
                    ]),
                ]),
                ("PPR", "Paper", [
                    ("CRD", "Cardboard", [
                        ("CRG", "Corrugated", ["SNG", "DBL", "TRP"]),
                        ("FLD", "Folding", ["SBS", "CRB", "KFT"]),
                    ]),
                    ("LBL", "Labels", [
                        ("PSA", "Pressure Sensitive", ["PPR", "FLM", "FOI"]),
                        ("SLV", "Sleeve", ["SHR", "STR", "RLF"]),
                        ("TAG", "Tags", ["HNG", "STR", "RFD"]),
                    ]),
                ]),
                ("MET", "Metal", [
                    ("CAN", "Cans", [
                        ("BEV", "Beverage", ["ALU", "STL", "BIM"]),
                        ("FOD", "Food", ["3PC", "2PC", "DRW"]),
                    ]),
                    ("FOI", "Foils", [
                        ("ALU", "Aluminum", ["PLN", "COT", "LAM"]),
                        ("TIN", "Tinplate", ["ETP", "TFS", "TIN"]),
                    ]),
                ]),
            ]
        },
        "energy": {
            "prefix": "EN",
            "subcategories": [
                ("SOL", "Solar", [
                    ("PNL", "Panels", [
                        ("MON", "Monocrystalline", ["60C", "72C", "96C", "144C"]),
                        ("POL", "Polycrystalline", ["60C", "72C", "120C"]),
                        ("THF", "Thin Film", ["CDS", "CIG", "ASI"]),
                    ]),
                    ("INV", "Inverters", [
                        ("STR", "String", ["3KW", "5KW", "10KW", "20KW"]),
                        ("CEN", "Central", ["50KW", "100KW", "500KW"]),
                        ("MIC", "Micro", ["250W", "350W", "500W"]),
                    ]),
                    ("MNT", "Mounting", [
                        ("ROF", "Roof", ["FLT", "TLT", "BAL"]),
                        ("GND", "Ground", ["FXD", "TRK", "2AX"]),
                    ]),
                ]),
                ("WND", "Wind", [
                    ("TUR", "Turbines", [
                        ("ONS", "Onshore", ["2MW", "3MW", "4MW", "5MW"]),
                        ("OFF", "Offshore", ["6MW", "8MW", "10MW", "15MW"]),
                    ]),
                    ("GEN", "Generators", [
                        ("PMG", "Permanent Magnet", ["DDR", "GRD", "MDR"]),
                        ("DFI", "DFIG", ["STD", "ENH", "CMP"]),
                    ]),
                    ("BLD", "Blades", [
                        ("FBR", "Fiberglass", ["40M", "60M", "80M"]),
                        ("CRB", "Carbon Fiber", ["60M", "80M", "100M"]),
                    ]),
                ]),
                ("BAT", "Storage", [
                    ("LIO", "Lithium-Ion", [
                        ("NMC", "NMC", ["5KW", "10KW", "50KW", "100KW"]),
                        ("LFP", "LFP", ["5KW", "10KW", "50KW", "100KW"]),
                        ("NCA", "NCA", ["5KW", "10KW", "50KW"]),
                    ]),
                    ("FLO", "Flow", [
                        ("VAN", "Vanadium", ["50KW", "100KW", "500KW"]),
                        ("ZNB", "Zinc-Bromine", ["50KW", "100KW", "250KW"]),
                    ]),
                ]),
            ]
        },
        "agriculture": {
            "prefix": "AG",
            "subcategories": [
                ("CRP", "Crops", [
                    ("GRN", "Grains", [
                        ("WHT", "Wheat", ["HRD", "SFT", "DRM"]),
                        ("CRN", "Corn", ["YLW", "WHT", "SWT"]),
                        ("RIC", "Rice", ["LNG", "MED", "SHT"]),
                        ("BRL", "Barley", ["SPN", "WIN", "MLT"]),
                        ("OAT", "Oats", ["FED", "MLL", "NKD"]),
                    ]),
                    ("VEG", "Vegetables", [
                        ("LFY", "Leafy", ["LET", "SPN", "KLE", "CBD"]),
                        ("ROT", "Root", ["CRT", "PTT", "BET", "ONI"]),
                        ("FRT", "Fruiting", ["TOM", "PEP", "CUC", "SQU"]),
                    ]),
                    ("FRT", "Fruits", [
                        ("CIT", "Citrus", ["ORG", "LMN", "GRP", "LIM"]),
                        ("STN", "Stone", ["PCH", "PLM", "CHR", "APR"]),
                        ("BRY", "Berry", ["STR", "BLU", "RAS", "BLK"]),
                    ]),
                ]),
                ("LVS", "Livestock", [
                    ("CTL", "Cattle", [
                        ("BEF", "Beef", ["ANG", "HRF", "LIM"]),
                        ("DRY", "Dairy", ["HLS", "JRS", "GRN"]),
                    ]),
                    ("POU", "Poultry", [
                        ("CHK", "Chicken", ["BRL", "LYR", "RNG"]),
                        ("TRK", "Turkey", ["BRD", "HRT", "WLD"]),
                    ]),
                    ("SWN", "Swine", [
                        ("BRD", "Breeding", ["YRK", "DRC", "HMP"]),
                        ("FNS", "Finishing", ["MKT", "RST", "SPE"]),
                    ]),
                ]),
                ("EQP", "Equipment", [
                    ("TRC", "Tractors", [
                        ("CMP", "Compact", ["25H", "35H", "50H"]),
                        ("UTL", "Utility", ["50H", "75H", "100H"]),
                        ("RWC", "Row Crop", ["100H", "150H", "200H"]),
                    ]),
                    ("HRV", "Harvesters", [
                        ("CMB", "Combines", ["SML", "MED", "LRG"]),
                        ("FOR", "Forage", ["PUL", "SPT", "CHP"]),
                    ]),
                    ("IRR", "Irrigation", [
                        ("PVT", "Pivot", ["CTR", "LNR", "CNR"]),
                        ("DRP", "Drip", ["SRF", "SUB", "MIC"]),
                    ]),
                ]),
            ]
        },
    }

    def __init__(self):
        """Initialize with CategoryLoader for tree generation."""
        self._category_loader = CategoryLoader()
        self._product_generator = ProductGenerator()

    def _normalize_unit(self, unit: str) -> str:
        """
        Normalize unit to a valid value for the Product model.

        Args:
            unit: The unit string from a template

        Returns:
            str: A valid unit string ('unit', 'kg', 'g', 'L', 'mL', 'm', 'cm', 'kWh', 'MJ', 'tkm')
        """
        if unit in self.VALID_UNITS:
            return unit
        # Check mapping for known invalid units
        if unit.lower() in self.UNIT_MAPPING:
            return self.UNIT_MAPPING[unit.lower()]
        # Default to 'unit' for unknown units
        return 'unit'

    def _generate_extended_categories(self) -> List[Dict]:
        """
        Generate additional category trees for extended industries.

        Returns:
            List[Dict]: Additional category trees to supplement the base tree.
        """
        extended_tree = []

        for industry, config in self.ADDITIONAL_INDUSTRIES.items():
            prefix = config["prefix"]
            industry_cat = {
                "code": prefix,
                "name": industry.replace("_", " ").title(),
                "industry_sector": industry,
                "children": []
            }

            for l1_code, l1_name, l2_categories in config["subcategories"]:
                l1_cat = {
                    "code": f"{prefix}-{l1_code}",
                    "name": l1_name,
                    "industry_sector": industry,
                    "children": []
                }

                for l2_code, l2_name, l3_categories in l2_categories:
                    l2_cat = {
                        "code": f"{prefix}-{l1_code}-{l2_code}",
                        "name": l2_name,
                        "industry_sector": industry,
                        "children": []
                    }

                    for l3_code, l3_name, l4_codes in l3_categories:
                        l3_cat = {
                            "code": f"{prefix}-{l1_code}-{l2_code}-{l3_code}"[:20],
                            "name": l3_name,
                            "industry_sector": industry,
                            "children": []
                        }

                        for i, l4_code in enumerate(l4_codes):
                            l4_cat = {
                                "code": f"{prefix}-{l1_code}-{l2_code}-{l3_code}-{l4_code}"[:20],
                                "name": f"{l3_name} - {l4_code}",
                                "industry_sector": industry,
                            }
                            l3_cat["children"].append(l4_cat)

                        l2_cat["children"].append(l3_cat)

                    l1_cat["children"].append(l2_cat)

                industry_cat["children"].append(l1_cat)

            extended_tree.append(industry_cat)

        return extended_tree

    def load_categories_from_json(
        self,
        db: Session,
        categories_data: List[Dict],
        parent_id: Optional[str] = None,
        level: int = 0
    ) -> int:
        """
        Recursively load categories from JSON structure (synchronous version).

        Args:
            db: Session database connection
            categories_data: List of category dictionaries with optional 'children'
            parent_id: Parent category ID (None for root categories)
            level: Current hierarchy level (0 for root)

        Returns:
            int: Total count of categories created
        """
        count = 0

        for cat_data in categories_data:
            category = ProductCategory(
                code=cat_data["code"],
                name=cat_data["name"],
                parent_id=parent_id,
                level=level,
                industry_sector=cat_data.get("industry_sector"),
            )
            db.add(category)
            db.flush()
            count += 1

            if "children" in cat_data:
                count += self.load_categories_from_json(
                    db,
                    cat_data["children"],
                    parent_id=category.id,
                    level=level + 1
                )

        return count

    def generate_products(
        self,
        db: Session,
        categories: List[ProductCategory],
        products_per_category: int = 5
    ) -> int:
        """
        Generate sample products for each category (synchronous version).

        Args:
            db: Session database connection
            categories: List of ProductCategory objects to generate products for
            products_per_category: Number of products to create per category

        Returns:
            int: Total count of products created
        """
        count = 0

        for category in categories:
            industry = category.industry_sector or "other"
            templates = self._product_generator.PRODUCT_TEMPLATES.get(industry, [])

            # Use generic templates for industries without specific templates
            if not templates:
                templates = [
                    (f"{category.name} - Standard", "unit"),
                    (f"{category.name} - Premium", "unit"),
                    (f"{category.name} - Economy", "unit"),
                    (f"{category.name} - Professional", "unit"),
                    (f"{category.name} - Industrial", "unit"),
                ]

            for i in range(products_per_category):
                if templates == self._product_generator.PRODUCT_TEMPLATES.get(industry, []):
                    # Use standard templates
                    template, unit = random.choice(templates)
                    product_name = self._product_generator._fill_template(template)
                    description = self._product_generator._generate_description(product_name, industry)
                else:
                    # Use generic templates
                    template, unit = templates[i % len(templates)]
                    product_name = template
                    description = f"Quality {product_name} for {industry} applications."

                # Normalize unit to a valid value
                normalized_unit = self._normalize_unit(unit)

                product = Product(
                    code=f"{category.code}-{i+1:03d}",
                    name=product_name,
                    description=description,
                    unit=normalized_unit,
                    category_id=category.id,
                    manufacturer=random.choice(self._product_generator._BRAND_VALUES),
                    country_of_origin=random.choice(["US", "CN", "DE", "JP", "GB", "KR", "IN", "MX", "IT", "FR"]),
                    is_finished_product=category.level >= 2,
                )
                db.add(product)
                count += 1

        db.flush()
        return count

    def load_full_catalog(
        self,
        db: Session,
        products_per_category: int = 3,
        min_category_level: int = 2
    ) -> dict:
        """
        Load full catalog with categories and products.

        This is the main entry point for test fixtures to load
        the complete product catalog with 1000+ categories and products.

        Args:
            db: Session database connection
            products_per_category: Number of products per leaf category
            min_category_level: Minimum category level for product generation

        Returns:
            dict: Summary with 'categories' and 'products' counts
        """
        result = {
            "categories": 0,
            "products": 0,
        }

        # Step 1: Generate and load base category tree (424 categories)
        category_tree = self._category_loader.generate_category_tree()
        cat_count = self.load_categories_from_json(db, category_tree)

        # Step 2: Generate and load extended category tree (~600 more categories)
        extended_tree = self._generate_extended_categories()
        cat_count += self.load_categories_from_json(db, extended_tree)

        result["categories"] = cat_count

        # Flush to ensure categories are available
        db.flush()

        # Step 3: Get leaf categories for product generation
        leaf_categories = db.query(ProductCategory).filter(
            ProductCategory.level >= min_category_level
        ).all()

        # Step 4: Generate products (at least 1000)
        prod_count = self.generate_products(
            db, leaf_categories, products_per_category=products_per_category
        )
        result["products"] = prod_count

        # Commit all changes
        db.commit()

        return result
