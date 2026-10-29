"""
Product Name Pools - Fictional brand names and product lines for unique naming.

Provides NAME_POOLS data and ProductNameGenerator class to assign unique,
realistic product names using fictional brands derived from real brand names.

Each industry has:
- 10-12 fictional brands (inspired by real brands, not trademarked)
- Per-template line names and variant suffixes
- Enough combinatorial capacity for 200+ unique names per industry

Usage:
    from backend.services.data_ingestion.product_name_pools import ProductNameGenerator

    gen = ProductNameGenerator()
    name, brand = gen.generate_unique_name(
        template_name="laptop",
        variant="gaming_17",
        industry="electronics",
        product_index=1,
    )
    # e.g. ("Dellware ProEdge 200 Titan 17", "Dellware")
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Human-readable display names for BOM template keys
# ---------------------------------------------------------------------------

TEMPLATE_DISPLAY_NAMES: dict[str, str] = {
    # Electronics
    "laptop": "Laptop",
    "smartphone": "Smartphone",
    "monitor": "Monitor",
    "tablet": "Tablet",
    # Apparel
    "tshirt": "T-Shirt",
    "jeans": "Jeans",
    "shoes": "Shoes",
    "jacket": "Jacket",
    # Automotive
    "car_seat": "Car Seat",
    "wheel_assembly": "Wheel Assembly",
    "dashboard": "Dashboard",
    # Construction
    "window_unit": "Window",
    "door_assembly": "Door",
    "hvac_unit": "HVAC Unit",
    # Food & Beverage
    "beverage_bottle": "Beverage",
    "canned_food": "Canned Food",
    "packaged_snack": "Snack",
}


# ---------------------------------------------------------------------------
# NAME_POOLS: per-industry brands, per-template lines and variant suffixes
# ---------------------------------------------------------------------------

NAME_POOLS: dict[str, dict] = {
    # ======================================================================
    # ELECTRONICS
    # ======================================================================
    "electronics": {
        "brands": [
            "Dellware", "Lenara", "Aceron", "Axus", "Hewlix", "Applix",
            "Samsara", "Sonara", "Lumigen", "Mosaic", "Goovex", "Huvari",
        ],
        "templates": {
            "laptop": {
                "lines": [
                    "ProEdge", "ThinkLine", "AeroBook", "ZenPro",
                    "SwiftNote", "EliteBook", "IdeaPad", "Precision",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Essential", "Select"],
                    "business_13": ["Compact 13", "Slim 13", "Travel 13", "Exec 13"],
                    "gaming_17": ["Titan 17", "Fury 17", "Storm 17", "Blaze 17"],
                    "ultrabook": ["Air", "Feather", "Whisper", "Aura"],
                },
            },
            "smartphone": {
                "lines": [
                    "PixelEdge", "GalaxyNova", "VelvetPro", "ZenPhone",
                    "NexusWave", "PrismView", "ClearCall", "ArcLine",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Lite", "SE"],
                    "flagship": ["Ultra", "Max", "Pro Max", "Platinum"],
                    "budget": ["Essentials", "Go", "Lite SE", "Value"],
                },
            },
            "monitor": {
                "lines": [
                    "CrystalView", "UltraSharp", "ProDisplay", "VividLine",
                    "TrueColor", "PixelPerfect", "ClearSight", "OptiView",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Basic", "Entry"],
                    "24_inch": ["Compact 24", "Desktop 24", "Studio 24", "Slim 24"],
                    "27_inch": ["Wide 27", "Pro 27", "Studio 27", "Curve 27"],
                    "32_inch": ["Ultra 32", "Panorama 32", "Command 32", "Cinema 32"],
                },
            },
            "tablet": {
                "lines": [
                    "SlateBook", "TabPro", "PadElite", "SurfaceGo",
                    "CanvasTab", "MediaPad", "NoteSlate", "FlexTab",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Essentials", "Lite"],
                    "standard": ["Standard", "Core", "Essentials", "Lite"],
                    "pro": ["Pro", "Pro Max", "Studio", "Creator"],
                },
            },
        },
    },

    # ======================================================================
    # APPAREL
    # ======================================================================
    "apparel": {
        "brands": [
            "Nikora", "Patagon", "Levara", "Adara", "Nordface", "Undermark",
            "Carhaven", "Columbix", "Timberline", "Luluweave", "Vantera", "Arctline",
        ],
        "templates": {
            "tshirt": {
                "lines": [
                    "ComfortFit", "BreezeTee", "ActiveWear", "ClassicCut",
                    "UrbanLine", "SoftTouch", "FreshKnit", "PureCotton",
                ],
                "suffixes": {
                    "base": ["Crew", "V-Neck", "Henley", "Scoop"],
                    "basic": ["Crew", "V-Neck", "Henley", "Scoop"],
                    "premium": ["Premium Crew", "Luxury Blend", "Signature Fit", "Elite Knit"],
                    "organic": ["Organic Crew", "EcoBlend", "Green Cotton", "NatureFit"],
                },
            },
            "jeans": {
                "lines": [
                    "TrueFit", "StreetEdge", "DenimCraft", "BlueLine",
                    "UrbanCut", "RawEdge", "ClassicWeave", "IndigoPro",
                ],
                "suffixes": {
                    "base": ["Straight", "Slim", "Regular", "Relaxed"],
                    "regular": ["Straight", "Slim", "Regular", "Relaxed"],
                    "distressed": ["Ripped", "Worn Edge", "Vintage Wash", "Faded"],
                    "raw": ["Selvedge", "Unwashed", "Raw Edge", "Heritage"],
                },
            },
            "shoes": {
                "lines": [
                    "StridePro", "FlexStep", "TrailBlazer", "UrbanSole",
                    "AirGlide", "PaceMaker", "GripTech", "CloudWalk",
                ],
                "suffixes": {
                    "base": ["All-Purpose", "Daily", "Classic", "Essential"],
                    "running": ["Racer", "Marathon", "Sprint", "Tempo"],
                    "casual": ["Loafer", "Slip-On", "Canvas", "Weekend"],
                    "boots": ["Hiker", "Trail", "Alpine", "Summit"],
                },
            },
            "jacket": {
                "lines": [
                    "ShieldLayer", "WindGuard", "ThermoCore", "StormBreaker",
                    "AllWeather", "PeakShell", "FrostLine", "VentureCoat",
                ],
                "suffixes": {
                    "base": ["Standard", "All-Season", "Everyday", "Classic"],
                    "light": ["Windbreaker", "Shell", "Breeze", "Light Layer"],
                    "winter": ["Parka", "Down Fill", "Arctic", "Insulated"],
                    "outdoor": ["Expedition", "Trail Pro", "Summit", "Backcountry"],
                },
            },
        },
    },

    # ======================================================================
    # AUTOMOTIVE
    # ======================================================================
    "automotive": {
        "brands": [
            "Boschwerk", "Bremora", "Continex", "Recarix", "Boltstar",
            "Densara", "Delphion", "Magnara", "Valorex", "Akebora",
        ],
        "templates": {
            "car_seat": {
                "lines": [
                    "ErgoRide", "ComfortZone", "ProSeat", "PrimeDrive",
                    "LuxSeat", "ActiveSit", "TourPro", "RaceLine",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Classic", "Essential"],
                    "manual": ["Manual Adjust", "Basic Recline", "Lever Control", "Hand Adjust"],
                    "power": ["Power Adjust", "Electric", "Motorized", "Auto Position"],
                    "heated": ["Heated Comfort", "Climate", "ThermoSeat", "Warm Drive"],
                },
            },
            "wheel_assembly": {
                "lines": [
                    "SpinForce", "AlloyTech", "RoadGrip", "TorqueLine",
                    "PrecisionRim", "DriveStar", "AxlePro", "TrackSet",
                ],
                "suffixes": {
                    "base": ["Standard", "OEM", "Factory", "Stock"],
                    "standard": ["Standard", "OEM", "Factory", "Stock"],
                    "performance": ["Sport", "Track", "Racing", "GT"],
                    "economy": ["Value", "Budget", "EcoRide", "Saver"],
                },
            },
            "dashboard": {
                "lines": [
                    "CockpitPro", "DashView", "PanelCraft", "ControlHub",
                    "InstrumentLine", "DrivePanel", "InfoCenter", "CommandDeck",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Classic", "Essential"],
                    "basic": ["Standard", "Core", "Classic", "Essential"],
                    "premium": ["Premium", "Luxury", "Executive", "Prestige"],
                    "digital": ["Digital", "Smart Screen", "TechDash", "Virtual"],
                },
            },
        },
    },

    # ======================================================================
    # CONSTRUCTION
    # ======================================================================
    "construction": {
        "brands": [
            "Andervane", "Pellmark", "Traneway", "Carriex", "Lennara",
            "Jeldmark", "Masonara", "Daikora", "Rhemax", "Owenmark",
            "Marvex", "Milguard",
        ],
        "templates": {
            "window_unit": {
                "lines": [
                    "ClearView", "SunShield", "GlassLine", "BrightFrame",
                    "VistaPro", "PanoGlass", "LightEdge", "AeroPane",
                ],
                "suffixes": {
                    "base": ["Standard", "Classic", "Essential", "Builder"],
                    "single_pane": ["Single Clear", "Basic Pane", "Economy", "Lite"],
                    "double_pane": ["Dual Pane", "Insulated", "ThermoSeal", "EnergyGuard"],
                    "triple_pane": ["Triple Seal", "MaxInsulate", "Arctic Grade", "UltraEfficient"],
                },
            },
            "door_assembly": {
                "lines": [
                    "EntryPro", "SecureGate", "DoorCraft", "ThresholdLine",
                    "PassagePro", "FrameWorks", "AccessLine", "PortalCraft",
                ],
                "suffixes": {
                    "base": ["Standard", "Classic", "Essential", "Builder"],
                    "interior": ["Interior", "Room Divider", "Passage", "Hallway"],
                    "exterior": ["Exterior", "Entry", "Weatherproof", "StormGuard"],
                    "fire_rated": ["Fire Rated", "SafeShield", "Code Plus", "FireStop"],
                },
            },
            "hvac_unit": {
                "lines": [
                    "ClimatePro", "AirFlow", "TempControl", "CoolBreeze",
                    "HeatWave", "VentMax", "AirCore", "ThermalEdge",
                ],
                "suffixes": {
                    "base": ["Standard", "Core", "Essential", "Builder"],
                    "residential": ["Home", "Family", "Comfort", "Household"],
                    "commercial": ["Office", "Business", "Commercial", "Enterprise"],
                    "industrial": ["Industrial", "Heavy Duty", "Plant Grade", "Facility"],
                },
            },
        },
    },

    # ======================================================================
    # FOOD & BEVERAGE
    # ======================================================================
    "food_beverage": {
        "brands": [
            "Naturevale", "Del Moro", "Tropicara", "Honeswell", "Dasara",
            "Laycrest", "Kindwell", "Fiora Springs", "Clifhaven", "Red Crest",
        ],
        "templates": {
            "beverage_bottle": {
                "lines": [
                    "PureFlow", "FreshSip", "ClearSpring", "AquaLine",
                    "VitalDrink", "NatureSip", "HydraFresh", "CrispWave",
                ],
                "suffixes": {
                    "base": ["Classic", "Original", "Standard", "Everyday"],
                    "small_330ml": ["Mini 330", "Travel 330", "Pocket 330", "Go 330"],
                    "standard_500ml": ["Classic 500", "Regular 500", "Daily 500", "Core 500"],
                    "large_1L": ["Family 1L", "Value 1L", "Mega 1L", "Share 1L"],
                },
            },
            "canned_food": {
                "lines": [
                    "HarvestGold", "FarmFresh", "PantryPick", "KitchenPro",
                    "MealReady", "HomeTaste", "NaturesCan", "FreshSeal",
                ],
                "suffixes": {
                    "base": ["Classic", "Original", "Everyday", "Standard"],
                    "small": ["Snack Size", "Single Serve", "Mini Can", "Portion"],
                    "standard": ["Classic Can", "Regular", "Family Favorite", "Daily"],
                    "large": ["Family Size", "Value Can", "Bulk", "Feast"],
                },
            },
            "packaged_snack": {
                "lines": [
                    "CrunchTime", "SnackWell", "BiteBright", "TastyTrail",
                    "MunchBox", "FlavorBurst", "GoodBite", "NibleNook",
                ],
                "suffixes": {
                    "base": ["Classic", "Original", "Traditional", "Signature"],
                    "single_serve": ["Single", "On-the-Go", "Pocket Pack", "Mini"],
                    "multi_pack": ["Multi Pack", "Variety Box", "Assorted", "6-Pack"],
                    "family_size": ["Family Size", "Party Pack", "Sharing", "Mega"],
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# ProductNameGenerator
# ---------------------------------------------------------------------------


class ProductNameGenerator:
    """Generate unique, realistic product names from industry-specific name pools.

    Combines brand + product line + model number + variant suffix to produce
    names like "Dellware ProEdge 200 Titan 17". Guarantees uniqueness via
    a tracking set and model-number increment fallback.

    Attributes:
        _used_names: Set of already-issued product names.
    """

    def __init__(self) -> None:
        self._used_names: set[str] = set()

    def generate_unique_name(
        self,
        template_name: str,
        variant: str | None,
        industry: str,
        product_index: int,
    ) -> tuple[str, str]:
        """Return ``(product_name, brand_name)`` guaranteed unique.

        Args:
            template_name: BOM template key (e.g. ``"laptop"``).
            variant: Variant key or ``None`` for base.
            industry: Industry key (e.g. ``"electronics"``).
            product_index: 1-based index used to rotate through pools.

        Returns:
            Tuple of (unique product name, brand name).
        """
        pool = NAME_POOLS.get(industry)
        if pool is None:
            # Fallback for unknown industry
            name = f"{industry.title()} Product {product_index}"
            return name, industry.title()

        brands = pool["brands"]
        template_pool = pool["templates"].get(template_name)
        if template_pool is None:
            name = f"{industry.title()} {template_name.title()} {product_index}"
            return name, brands[product_index % len(brands)]

        lines = template_pool["lines"]
        suffixes_map = template_pool["suffixes"]

        brand = brands[product_index % len(brands)]
        line = lines[product_index % len(lines)]

        variant_key = variant if variant and variant in suffixes_map else "base"
        suffixes = suffixes_map[variant_key]
        suffix = suffixes[product_index % len(suffixes)]

        model_num = self._generate_model_number(product_index, industry)

        display_name = TEMPLATE_DISPLAY_NAMES.get(
            template_name, template_name.replace("_", " ").title()
        )
        candidate = f"{brand} {line} {model_num} {suffix} {display_name}"

        # Guarantee uniqueness via model-number bump
        while candidate in self._used_names:
            model_num = self._increment_model(model_num)
            candidate = f"{brand} {line} {model_num} {suffix} {display_name}"

        self._used_names.add(candidate)
        return candidate, brand

    # ------------------------------------------------------------------
    # Model number helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_model_number(product_index: int, industry: str) -> str:
        """Produce a model number string from the product index.

        Pattern varies by industry to feel natural:
        - electronics: 3-digit (100, 210, 320 ...)
        - apparel: letter+2-digit (A10, B20 ...)
        - automotive: 4-digit (1000, 2100 ...)
        - construction: 2-digit series (S10, S20 ...)
        - food_beverage: 3-digit (100, 200 ...)
        """
        if industry == "electronics":
            return str(100 + product_index * 10)
        elif industry == "apparel":
            letter = chr(65 + (product_index % 26))  # A-Z
            num = 10 + (product_index % 90)
            return f"{letter}{num}"
        elif industry == "automotive":
            return str(1000 + product_index * 100)
        elif industry == "construction":
            return f"S{10 + product_index * 10}"
        else:
            return str(100 + product_index * 10)

    @staticmethod
    def _increment_model(model_num: str) -> str:
        """Bump a model number to resolve collisions."""
        # Try to increment the numeric portion
        if model_num.startswith("S"):
            num = int(model_num[1:]) + 1
            return f"S{num}"
        # Letter prefix (apparel)
        if model_num and model_num[0].isalpha() and model_num[1:].isdigit():
            num = int(model_num[1:]) + 1
            return f"{model_num[0]}{num}"
        # Pure numeric
        try:
            return str(int(model_num) + 1)
        except ValueError:
            return model_num + "X"


__all__ = ["NAME_POOLS", "ProductNameGenerator", "TEMPLATE_DISPLAY_NAMES"]
