"""
PCF Calculator Module - Simplified Calculation Engine

This module implements a simplified PCF (Product Carbon Footprint) calculator
using Brightway2 for emission factor management. The calculation approach uses
direct multiplication (quantity × emission_factor) rather than full matrix
inversion for MVP simplicity.

Calculation Scope: Cradle-to-gate (excludes use phase and end-of-life)
Standard: ISO 14067, GHG Protocol Product Standard
Impact Method: IPCC 2021 GWP100

Features:
- Simple flat BOM calculation
- Hierarchical BOM traversal (max 2 levels)
- Breakdown by category (materials, energy, transport)
- Data quality scoring
- Integration with database products

TASK-CALC-003: Implement Simplified PCF Calculator
"""

import brightway2 as bw
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PCFCalculator:
    """
    Simplified PCF Calculator using Brightway2 emission factors.

    This calculator implements a direct multiplication approach:
    Total CO2e = Σ(quantity_i × emission_factor_i)

    For hierarchical BOMs, quantities are multiplied through levels:
    Level 2 CO2e = parent_qty × child_qty × emission_factor
    """

    def __init__(self):
        """
        Initialize PCF Calculator.

        Sets Brightway2 project and loads emission factors database.

        Raises:
            Exception: If Brightway2 project not initialized (run TASK-CALC-001)
        """
        if "pcf_calculator" not in bw.projects:
            raise Exception(
                "Brightway2 project 'pcf_calculator' not found. "
                "Run initialize_brightway() first (TASK-CALC-001)."
            )

        bw.projects.set_current("pcf_calculator")

        if "pcf_emission_factors" not in bw.databases:
            raise Exception(
                "Emission factors database not found. "
                "Run sync_emission_factors() first (TASK-CALC-002)."
            )

        self.ef_db = bw.Database("pcf_emission_factors")
        logger.info("PCFCalculator initialized with pcf_emission_factors database")

    def calculate(self, bom: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate PCF for flat BOM using direct multiplication.

        This is the core calculation method that implements:
        CO2e = Σ(quantity_i × emission_factor_i)

        Args:
            bom: List of BOM items with structure:
                [
                    {"name": str, "quantity": float, "unit": str},
                    ...
                ]

        Returns:
            Dictionary with calculation results:
            {
                "total_co2e_kg": float,  # Total CO2e emissions in kg
                "breakdown": {           # Emissions per component
                    "component_name": float,
                    ...
                }
            }

        Raises:
            ValueError: If emission factor not found for any component

        Example:
            >>> calculator = PCFCalculator()
            >>> bom = [
            ...     {"name": "cotton", "quantity": 0.2, "unit": "kg"},
            ...     {"name": "polyester", "quantity": 0.05, "unit": "kg"}
            ... ]
            >>> result = calculator.calculate(bom)
            >>> print(f"Total: {result['total_co2e_kg']} kg CO2e")
        """
        total_co2e = 0.0
        breakdown = {}

        for item in bom:
            try:
                activity = self.ef_db.get(item["name"])
            except Exception as e:
                raise ValueError(
                    f"Emission factor not found: {item['name']}. "
                    f"Available factors: {[act['name'] for act in self.ef_db]}"
                )

            # Get CO2e factor from activity
            co2e_per_unit = self._get_co2e_from_activity(activity)

            # Simple calculation: quantity × emission_factor
            item_co2e = float(item["quantity"]) * co2e_per_unit

            total_co2e += item_co2e
            breakdown[item["name"]] = item_co2e

            logger.debug(
                f"{item['name']}: {item['quantity']} {item['unit']} × "
                f"{co2e_per_unit} kg CO2e/{item['unit']} = {item_co2e} kg CO2e"
            )

        return {
            "total_co2e_kg": total_co2e,
            "breakdown": breakdown
        }

    def calculate_hierarchical(self, bom_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate PCF for hierarchical BOM with parent-child relationships.

        Traverses BOM tree recursively, multiplying quantities through levels:
        - Level 0: parent (finished product)
        - Level 1: parent_qty × child_qty × emission_factor
        - Level 2: parent_qty × level1_qty × level2_qty × emission_factor

        Args:
            bom_tree: Hierarchical BOM structure:
                {
                    "name": str,
                    "quantity": float,
                    "unit": str,
                    "children": [
                        {
                            "name": str,
                            "quantity": float,
                            "unit": str,
                            "children": [...]
                        },
                        ...
                    ]
                }

        Returns:
            Dictionary with calculation results:
            {
                "total_co2e_kg": float,
                "breakdown": {component_name: co2e},
                "max_depth": int  # Maximum depth reached in BOM tree
            }

        Example:
            >>> bom_tree = {
            ...     "name": "t-shirt",
            ...     "quantity": 1,
            ...     "unit": "unit",
            ...     "children": [
            ...         {
            ...             "name": "cotton_fabric",
            ...             "quantity": 0.2,
            ...             "unit": "kg",
            ...             "children": [
            ...                 {"name": "cotton", "quantity": 1.05, "unit": "kg"}
            ...             ]
            ...         }
            ...     ]
            ... }
            >>> result = calculator.calculate_hierarchical(bom_tree)
        """
        flat_bom = []
        max_depth = 0

        def traverse(node: Dict[str, Any], cumulative_qty: float = 1.0, depth: int = 0):
            """Recursively traverse BOM tree and flatten to material quantities."""
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            if "children" in node and node["children"]:
                # Intermediate node - recurse to children
                for child in node["children"]:
                    child_qty = cumulative_qty * float(child["quantity"])
                    traverse(child, child_qty, depth + 1)
            else:
                # Leaf node - this is a material with emission factor
                if node["name"] not in [item["name"] for item in flat_bom]:
                    flat_bom.append({
                        "name": node["name"],
                        "quantity": cumulative_qty * float(node["quantity"]),
                        "unit": node["unit"]
                    })
                else:
                    # Accumulate quantities for duplicate materials
                    for item in flat_bom:
                        if item["name"] == node["name"]:
                            item["quantity"] += cumulative_qty * float(node["quantity"])

        # Start traversal from root
        traverse(bom_tree)

        # Calculate using flat BOM
        result = self.calculate(flat_bom)
        result["max_depth"] = max_depth

        return result

    def calculate_with_categories(self, bom: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate PCF with breakdown by category (materials, energy, transport).

        Categories are used to organize emissions into standard GHG Protocol
        categories for reporting.

        Args:
            bom: List of BOM items with optional "category" field:
                [
                    {
                        "name": str,
                        "quantity": float,
                        "unit": str,
                        "category": str  # Optional: "materials", "energy", "transport"
                    },
                    ...
                ]

        Returns:
            Dictionary with calculation results:
            {
                "total_co2e_kg": float,
                "breakdown": {component_name: co2e},
                "breakdown_by_category": {
                    "materials": float,
                    "energy": float,
                    "transport": float,
                    ...
                }
            }

        Example:
            >>> bom = [
            ...     {"name": "cotton", "quantity": 0.18, "unit": "kg", "category": "materials"},
            ...     {"name": "electricity_us", "quantity": 2.5, "unit": "kWh", "category": "energy"}
            ... ]
            >>> result = calculator.calculate_with_categories(bom)
        """
        # First, calculate total using base method
        result = self.calculate(bom)

        # Build category breakdown
        breakdown_by_category = {}

        for item in bom:
            # Default category is "materials" if not specified
            category = item.get("category", "materials")

            # Get emissions for this item from breakdown
            item_co2e = result["breakdown"][item["name"]]

            # Accumulate by category
            if category not in breakdown_by_category:
                breakdown_by_category[category] = 0.0
            breakdown_by_category[category] += item_co2e

        result["breakdown_by_category"] = breakdown_by_category

        return result

    def calculate_with_quality(self, bom: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate PCF with data quality score and source tracking.

        Data quality is assessed based on:
        - Data source (EPA, DEFRA, Ecoinvent, etc.)
        - Temporal validity
        - Geographic representativeness

        Args:
            bom: List of BOM items with optional "data_source" field:
                [
                    {
                        "name": str,
                        "quantity": float,
                        "unit": str,
                        "data_source": str  # Optional: "EPA", "DEFRA", etc.
                    },
                    ...
                ]

        Returns:
            Dictionary with calculation results:
            {
                "total_co2e_kg": float,
                "breakdown": {component_name: co2e},
                "data_quality_score": float,  # 0.0 to 1.0
                "data_sources": [str]          # List of data sources used
            }

        Example:
            >>> bom = [
            ...     {"name": "cotton", "quantity": 0.2, "unit": "kg", "data_source": "EPA"}
            ... ]
            >>> result = calculator.calculate_with_quality(bom)
        """
        # First, calculate total using base method
        result = self.calculate(bom)

        # Track data sources
        data_sources = []

        for item in bom:
            # Get data source from item or from emission factor
            data_source = item.get("data_source", None)

            if data_source:
                if data_source not in data_sources:
                    data_sources.append(data_source)
            else:
                # Try to get from emission factor metadata
                try:
                    activity = self.ef_db.get(item["name"])
                    # Brightway2 activities don't have direct data_source attribute
                    # For MVP, we'll use a simple quality score
                except Exception:
                    pass

        # Calculate simple data quality score
        # For MVP: Score based on number of data sources and availability
        # More sophisticated scoring can be added in future phases
        if len(data_sources) > 0:
            # Score: 1.0 if single source, decreases with more sources (less consistent)
            quality_score = 1.0 / (1.0 + 0.1 * (len(data_sources) - 1))
        else:
            # No source info - assume secondary data (medium quality)
            quality_score = 0.7

        result["data_quality_score"] = quality_score
        result["data_sources"] = data_sources

        return result

    def calculate_product(self, product_id: str, db_session: Session) -> Dict[str, Any]:
        """
        Calculate PCF for a product from database using its BOM.

        This method queries the database to get the product's BOM structure
        and calculates emissions using the hierarchical calculation method.

        Args:
            product_id: UUID of product in database
            db_session: SQLAlchemy database session

        Returns:
            Dictionary with calculation results:
            {
                "product_id": str,
                "product_code": str,
                "product_name": str,
                "total_co2e_kg": float,
                "breakdown": {component_name: co2e},
                "breakdown_by_category": {category: co2e},  # If categorized
                "max_depth": int
            }

        Raises:
            ValueError: If product not found in database

        Example:
            >>> with db_context() as session:
            ...     result = calculator.calculate_product("product-id-123", session)
        """
        from backend.models import Product, BillOfMaterials

        # Get product from database
        product = db_session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            raise ValueError(f"Product not found: {product_id}")

        logger.info(f"Calculating PCF for product: {product.code} - {product.name}")

        # Build BOM tree from database
        bom_tree = self._build_bom_tree_from_db(product_id, db_session)

        # If no BOM, return zero emissions
        if not bom_tree.get("children"):
            logger.warning(f"Product {product.code} has no BOM - returning zero emissions")
            return {
                "product_id": product_id,
                "product_code": product.code,
                "product_name": product.name,
                "total_co2e_kg": 0.0,
                "breakdown": {},
                "max_depth": 0
            }

        # Calculate using hierarchical method
        result = self.calculate_hierarchical(bom_tree)

        # Add product metadata to result
        result["product_id"] = product_id
        result["product_code"] = product.code
        result["product_name"] = product.name

        # Try to add category breakdown if we can infer categories
        # For MVP, we'll categorize based on naming conventions:
        # - *electricity* → energy
        # - *transport* → transport
        # - everything else → materials
        breakdown_by_category = {
            "materials": 0.0,
            "energy": 0.0,
            "transport": 0.0
        }

        for component_name, co2e in result["breakdown"].items():
            name_lower = component_name.lower()
            if "electricity" in name_lower or "energy" in name_lower:
                breakdown_by_category["energy"] += co2e
            elif "transport" in name_lower or "truck" in name_lower or "ship" in name_lower:
                breakdown_by_category["transport"] += co2e
            else:
                breakdown_by_category["materials"] += co2e

        result["breakdown_by_category"] = breakdown_by_category

        logger.info(
            f"PCF calculation complete: {product.code} = {result['total_co2e_kg']:.3f} kg CO2e"
        )

        return result

    def _build_bom_tree_from_db(
        self,
        product_id: str,
        db_session: Session,
        depth: int = 0,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Build hierarchical BOM tree from database.

        Recursively traverses BOM relationships to build tree structure.
        Includes circular reference detection.

        Args:
            product_id: UUID of product
            db_session: SQLAlchemy database session
            depth: Current recursion depth (for circular detection)
            max_depth: Maximum recursion depth

        Returns:
            BOM tree dictionary

        Raises:
            ValueError: If circular reference detected or max depth exceeded
        """
        from backend.models import Product, BillOfMaterials

        if depth > max_depth:
            raise ValueError(f"Maximum BOM depth exceeded: {max_depth}")

        # Get product
        product = db_session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            raise ValueError(f"Product not found: {product_id}")

        # Build node
        node = {
            "name": product.code,  # Use code as name for emission factor lookup
            "quantity": 1.0,
            "unit": product.unit,
            "children": []
        }

        # Get BOM items (children)
        bom_items = db_session.query(BillOfMaterials).filter(
            BillOfMaterials.parent_product_id == product_id
        ).all()

        # For each child, recurse or add as leaf
        for bom_item in bom_items:
            child_product = bom_item.child_product

            # Check if child has its own BOM (intermediate) or is a leaf (material)
            child_bom_count = db_session.query(BillOfMaterials).filter(
                BillOfMaterials.parent_product_id == child_product.id
            ).count()

            if child_bom_count > 0:
                # Intermediate node - recurse
                child_tree = self._build_bom_tree_from_db(
                    child_product.id,
                    db_session,
                    depth + 1,
                    max_depth
                )
                child_tree["quantity"] = float(bom_item.quantity)
                node["children"].append(child_tree)
            else:
                # Leaf node - this is a material
                # Try to match to emission factor by code or name
                material_name = self._map_product_to_emission_factor(child_product)

                node["children"].append({
                    "name": material_name,
                    "quantity": float(bom_item.quantity),
                    "unit": bom_item.unit or child_product.unit
                })

        return node

    def _map_product_to_emission_factor(self, product) -> str:
        """
        Map product code/name to emission factor activity name.

        For MVP, we use simple name matching. In future phases, this could
        use a mapping table or fuzzy matching.

        Args:
            product: Product model instance

        Returns:
            Emission factor activity name

        Example:
            Product code "COTTON-001" → emission factor "cotton"
        """
        # Try to match by code (lowercase, remove numbers and hyphens)
        code_normalized = product.code.lower().replace("-", "_")

        # Remove trailing numbers
        import re
        code_normalized = re.sub(r'_?\d+$', '', code_normalized)

        # Check if this matches an emission factor
        try:
            self.ef_db.get(code_normalized)
            return code_normalized
        except Exception:
            pass

        # Try matching by name (lowercase)
        name_normalized = product.name.lower().replace(" ", "_")

        # Check if this matches an emission factor
        try:
            self.ef_db.get(name_normalized)
            return name_normalized
        except Exception:
            pass

        # Fallback: return code as-is
        logger.warning(
            f"Could not map product {product.code} to emission factor. "
            f"Using code as-is: {code_normalized}"
        )
        return code_normalized

    def _get_co2e_from_activity(self, activity) -> float:
        """
        Extract CO2e emission factor from Brightway2 activity.

        The emission factor is stored in the biosphere exchange with
        "Carbon dioxide, fossil" flow.

        Args:
            activity: Brightway2 Activity object

        Returns:
            CO2e emission factor in kg CO2e per unit

        Example:
            >>> activity = ef_db.get("cotton")
            >>> co2e = calculator._get_co2e_from_activity(activity)
            >>> print(f"Cotton: {co2e} kg CO2e/kg")
        """
        for exchange in activity.exchanges():
            if exchange["type"] == "biosphere":
                return float(exchange["amount"])

        # No biosphere exchange found - return 0
        logger.warning(f"No biosphere exchange found for activity: {activity['name']}")
        return 0.0
