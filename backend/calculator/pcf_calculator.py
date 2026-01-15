"""
PCF Calculator Module - Simplified Calculation Engine

This module implements a simplified PCF (Product Carbon Footprint) calculator
with support for dependency injection. The calculator can work with either:
1. Injected EmissionFactorProvider (decoupled, testable)
2. Brightway2 database (legacy mode for backward compatibility)

Calculation Scope: Cradle-to-gate (excludes use phase and end-of-life)
Standard: ISO 14067, GHG Protocol Product Standard
Impact Method: IPCC 2021 GWP100

Features:
- Simple flat BOM calculation
- Hierarchical BOM traversal (max 2 levels)
- Breakdown by category (materials, energy, transport)
- Data quality scoring
- Integration with database products
- Non-blocking async initialization (TASK-CALC-P7-016)
- Decoupled from ORM via dependency injection (TASK-CALC-P7-022)
- Robust sync with retry logic (TASK-BE-P9-010)

TASK-CALC-003: Implement Simplified PCF Calculator
TASK-CALC-P7-016: Make Brightway2 Initialization Non-Blocking
TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache
TASK-BE-P9-010: Fix emission factor sync failures due to database locks
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .exceptions import EmissionFactorNotFoundError
from .providers import EmissionFactorDTO, EmissionFactorProvider

logger = logging.getLogger(__name__)


# ==================== Data Classes for Calculation ====================


@dataclass
class BOMItem:
    """
    Bill of Materials item for calculation input.

    Represents a single material/component in the BOM with its quantity.

    Attributes:
        material: Material/category name (must match emission factor category)
        quantity: Amount of material
        unit: Unit of measurement (e.g., "kg", "kWh")
    """

    material: str
    quantity: float
    unit: str


@dataclass
class ComponentBreakdown:
    """
    Breakdown of emissions by component.

    Provides detailed emissions data for a single BOM component.

    Attributes:
        material: Material/category name
        co2e: Total CO2e emissions for this component
        quantity: Amount of material used
        unit: Unit of measurement
        emission_factor: CO2e per unit used for calculation
    """

    material: str
    co2e: float
    quantity: float = 0.0
    unit: str = "kg"
    emission_factor: float = 0.0


@dataclass
class CalculationResult:
    """
    Result of PCF calculation.

    Contains total emissions and detailed breakdown by component.

    Attributes:
        total_co2e: Total CO2e emissions in kg
        breakdown: List of ComponentBreakdown for each BOM item
        calculation_method: Calculation methodology used
    """

    total_co2e: float
    breakdown: List[ComponentBreakdown]
    calculation_method: str = "attributional"


# ==================== Module-level State (Legacy Brightway2 Support) ====================

# Module-level state for singleton pattern
# TASK-CALC-P7-016: Support non-blocking async initialization
_calculator_instance: Optional["PCFCalculator"] = None
_init_lock = asyncio.Lock()
_initialized = False


def _initialize_brightway_sync() -> None:
    """
    Synchronous Brightway2 initialization to be run in thread pool.

    This function performs the actual Brightway2 initialization work,
    including creating the PCFCalculator instance and building the
    name-to-activity lookup cache.

    This is designed to be called via asyncio.to_thread() to avoid
    blocking the event loop during FastAPI startup.

    TASK-BE-P9-010: Updated to use skip_if_synced=True for faster startup
    when emission factors are already synced. Also includes retry logic
    for database lock errors.

    Raises:
        Exception: If Brightway2 project or database not initialized
    """
    global _calculator_instance, _initialized

    if _initialized:
        logger.debug("PCFCalculator already initialized, skipping")
        return

    logger.info("Starting synchronous Brightway2 initialization in thread pool...")

    # Import and run Brightway setup
    from backend.calculator.brightway_setup import initialize_brightway
    from backend.calculator.emission_factor_sync import sync_emission_factors
    from backend.database.connection import db_context

    # Initialize Brightway2
    initialize_brightway()

    # Sync emission factors from database
    # TASK-BE-P9-010: Use skip_if_synced=True for faster startup when data already synced
    # This avoids re-syncing on every server restart, improving startup time.
    # Also includes retry logic for database lock errors.
    with db_context() as session:
        result = sync_emission_factors(db_session=session, skip_if_synced=True)
        if result.get("skipped"):
            logger.info(f"Using existing {result['synced_count']} emission factors in Brightway2")
        else:
            logger.info(f"Synced {result['synced_count']} emission factors to Brightway2")

    # Create calculator instance (legacy mode without ef_provider)
    _calculator_instance = PCFCalculator()
    _initialized = True

    logger.info("Brightway2 initialization complete")


async def initialize_pcf_calculator() -> None:
    """
    Initialize PCF Calculator asynchronously using thread pool.

    This function wraps the synchronous Brightway2 initialization
    in asyncio.to_thread() to prevent blocking the event loop during
    FastAPI startup.

    Uses a lock to ensure initialization only runs once, even if
    called concurrently from multiple tasks.

    Example:
        @app.on_event("startup")
        async def startup_event():
            await initialize_pcf_calculator()
    """
    global _initialized

    # Fast path: already initialized
    if _initialized:
        return

    async with _init_lock:
        # Double-check after acquiring lock
        if _initialized:
            return

        logger.info("Running Brightway2 initialization in thread pool...")
        await asyncio.to_thread(_initialize_brightway_sync)


def get_pcf_calculator() -> "PCFCalculator":
    """
    Get the initialized PCF Calculator instance.

    Returns the singleton PCFCalculator instance that was created
    during async initialization.

    Returns:
        PCFCalculator: The initialized calculator instance

    Raises:
        RuntimeError: If calculator has not been initialized yet.
            Call initialize_pcf_calculator() first.

    Example:
        calculator = get_pcf_calculator()
        result = calculator.calculate(bom)
    """
    if _calculator_instance is None:
        raise RuntimeError(
            "PCF Calculator not initialized. Wait for startup to complete. "
            "Call initialize_pcf_calculator() during application startup."
        )
    return _calculator_instance


def is_calculator_initialized() -> bool:
    """
    Check if the PCF Calculator has been initialized.

    Returns:
        bool: True if calculator is initialized and ready, False otherwise

    Example:
        if is_calculator_initialized():
            calculator = get_pcf_calculator()
    """
    return _initialized


async def wait_for_calculator_ready(timeout: float = 30.0) -> None:
    """
    Wait for the PCF Calculator to be initialized.

    This is useful for request handlers that need to wait for
    initialization to complete before proceeding.

    Args:
        timeout: Maximum seconds to wait (default 30)

    Raises:
        TimeoutError: If calculator is not ready within timeout

    Example:
        await wait_for_calculator_ready()
        calculator = get_pcf_calculator()
    """
    start_time = asyncio.get_event_loop().time()

    while not _initialized:
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(
                f"PCF Calculator not initialized within {timeout} seconds"
            )
        await asyncio.sleep(0.1)


# ==================== PCF Calculator Class ====================


class PCFCalculator:
    """
    Simplified PCF Calculator with dependency injection support.

    This calculator supports two modes:
    1. Decoupled mode: Uses injected EmissionFactorProvider (recommended)
    2. Legacy mode: Uses Brightway2 emission factors database (for backward compatibility)

    Calculation: Total CO2e = sum(quantity_i * emission_factor_i)

    Example (decoupled mode - recommended):
        >>> provider = SQLAlchemyEmissionFactorProvider(session)
        >>> cached = CachedEmissionFactorProvider(provider, ttl_seconds=300)
        >>> calculator = PCFCalculator(ef_provider=cached)
        >>> result = await calculator.calculate(
        ...     product_id="prod-1",
        ...     bom_items=[BOMItem(material="steel", quantity=10, unit="kg")]
        ... )

    Example (legacy Brightway2 mode):
        >>> calculator = PCFCalculator()  # Uses Brightway2 database
        >>> result = calculator.calculate_legacy([{"name": "steel", "quantity": 10, "unit": "kg"}])
    """

    def __init__(self, ef_provider: Optional[EmissionFactorProvider] = None):
        """
        Initialize PCF Calculator.

        Args:
            ef_provider: Optional EmissionFactorProvider for decoupled mode.
                        If not provided, falls back to Brightway2 database (legacy mode).

        Raises:
            Exception: In legacy mode, if Brightway2 project not initialized.
        """
        self._ef_provider = ef_provider
        self._name_to_activity: Dict[str, Any] = {}

        # Only initialize Brightway2 if no provider is injected (legacy mode)
        if ef_provider is None:
            self._init_brightway_mode()
        else:
            logger.info("PCFCalculator initialized in decoupled mode with injected provider")

    def _init_brightway_mode(self) -> None:
        """Initialize Brightway2 mode (legacy)."""
        import brightway2 as bw

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

        # Check if database has activities (TASK-BE-P9-010)
        activity_count = len(self.ef_db)
        if activity_count == 0:
            raise Exception(
                "Emission factors database is empty. "
                "Run sync_emission_factors() to populate it (TASK-CALC-002)."
            )

        # Build name-based lookup cache for O(1) retrieval performance
        for activity in self.ef_db:
            self._name_to_activity[activity["name"]] = activity

        logger.info(
            f"PCFCalculator initialized with {len(self._name_to_activity)} emission factors"
        )

    # ==================== Decoupled Mode Methods (New) ====================

    async def calculate(
        self,
        product_id: str,
        bom_items: List[BOMItem],
        include_transport: bool = False,
    ) -> CalculationResult:
        """
        Calculate PCF for product using injected EF provider (async).

        This is the primary calculation method for decoupled mode.
        Requires ef_provider to be set during initialization.

        Args:
            product_id: Product identifier (for tracking)
            bom_items: List of BOMItem objects with material, quantity, unit
            include_transport: Whether to include transport emissions (not yet implemented)

        Returns:
            CalculationResult with total_co2e and breakdown

        Raises:
            EmissionFactorNotFoundError: If emission factor not found for a material
            RuntimeError: If no ef_provider is configured

        Example:
            >>> result = await calculator.calculate(
            ...     product_id="prod-1",
            ...     bom_items=[
            ...         BOMItem(material="steel", quantity=10, unit="kg"),
            ...         BOMItem(material="aluminum", quantity=5, unit="kg")
            ...     ]
            ... )
            >>> print(f"Total: {result.total_co2e} kg CO2e")
        """
        if self._ef_provider is None:
            raise RuntimeError(
                "No emission factor provider configured. "
                "Initialize PCFCalculator with ef_provider parameter."
            )

        breakdown: List[ComponentBreakdown] = []
        total_co2e = 0.0

        for item in bom_items:
            ef = await self._ef_provider.get_by_category(item.material)

            if ef is None:
                raise EmissionFactorNotFoundError(item.material)

            item_co2e = item.quantity * ef.co2e_kg
            total_co2e += item_co2e

            breakdown.append(
                ComponentBreakdown(
                    material=item.material,
                    co2e=item_co2e,
                    quantity=item.quantity,
                    unit=item.unit,
                    emission_factor=ef.co2e_kg,
                )
            )

            logger.debug(
                f"{item.material}: {item.quantity} {item.unit} x "
                f"{ef.co2e_kg} kg CO2e/{item.unit} = {item_co2e} kg CO2e"
            )

        logger.info(
            f"PCF calculation complete for {product_id}: {total_co2e:.3f} kg CO2e"
        )

        return CalculationResult(
            total_co2e=total_co2e,
            breakdown=breakdown,
            calculation_method="attributional",
        )

    # ==================== Legacy Brightway2 Mode Methods ====================

    def _get_item_name(self, item: Dict[str, Any]) -> str:
        """
        Extract component name from BOM item.

        Supports both "name" and "component_name" field names for flexibility.

        Args:
            item: BOM item dictionary

        Returns:
            Component name string

        Raises:
            ValueError: If neither name field is present
        """
        # Try "name" first (preferred), then "component_name" (legacy)
        if "name" in item:
            return item["name"]
        elif "component_name" in item:
            return item["component_name"]
        else:
            raise ValueError(
                f"BOM item must have 'name' or 'component_name' field. Got: {item.keys()}"
            )

    def calculate_legacy(self, bom: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate PCF for flat BOM using direct multiplication (legacy Brightway2 mode).

        This is the original calculation method using Brightway2 database.
        Use calculate() with ef_provider for new implementations.

        Args:
            bom: List of BOM items with structure:
                [
                    {"name": str, "quantity": float, "unit": str},
                    ...
                ]

        Returns:
            Dictionary with calculation results:
            {
                "total_co2e_kg": float,
                "breakdown": {component_name: float, ...}
            }
        """
        total_co2e = 0.0
        breakdown = {}

        for item in bom:
            component_name = self._get_item_name(item)

            activity = self._name_to_activity.get(component_name)

            if activity is None:
                raise ValueError(
                    f"Emission factor not found: {component_name}. "
                    f"Available factors: {list(self._name_to_activity.keys())}"
                )

            co2e_per_unit = self._get_co2e_from_activity(activity)
            item_co2e = float(item["quantity"]) * co2e_per_unit

            total_co2e += item_co2e
            breakdown[component_name] = item_co2e

            logger.debug(
                f"{component_name}: {item['quantity']} {item['unit']} x "
                f"{co2e_per_unit} kg CO2e/{item['unit']} = {item_co2e} kg CO2e"
            )

        return {"total_co2e_kg": total_co2e, "breakdown": breakdown}

    def calculate_hierarchical(self, bom_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate PCF for hierarchical BOM with parent-child relationships.

        Traverses BOM tree recursively, multiplying quantities through levels.
        Uses Brightway2 database for emission factors.

        Args:
            bom_tree: Hierarchical BOM structure

        Returns:
            Dictionary with calculation results including max_depth
        """
        flat_bom = []
        max_depth = 0

        def traverse(
            node: Dict[str, Any], cumulative_qty: float = 1.0, depth: int = 0
        ):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            if "children" in node and node["children"]:
                for child in node["children"]:
                    child_qty = cumulative_qty * float(child["quantity"])
                    traverse(child, child_qty, depth + 1)
            else:
                node_name = self._get_item_name(node)
                if node_name not in [item["name"] for item in flat_bom]:
                    flat_bom.append(
                        {
                            "name": node_name,
                            "quantity": cumulative_qty,
                            "unit": node["unit"],
                        }
                    )
                else:
                    for item in flat_bom:
                        if item["name"] == node_name:
                            item["quantity"] += cumulative_qty

        traverse(bom_tree)

        result = self.calculate_legacy(flat_bom)
        result["max_depth"] = max_depth

        return result

    def calculate_with_categories(self, bom: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate PCF with breakdown by category (materials, energy, transport).

        Uses Brightway2 database for emission factors.

        Args:
            bom: List of BOM items with optional "category" field

        Returns:
            Dictionary with breakdown_by_category
        """
        result = self.calculate_legacy(bom)

        breakdown_by_category = {}

        for item in bom:
            category = item.get("category", "materials")
            component_name = self._get_item_name(item)
            item_co2e = result["breakdown"][component_name]

            if category not in breakdown_by_category:
                breakdown_by_category[category] = 0.0
            breakdown_by_category[category] += item_co2e

        result["breakdown_by_category"] = breakdown_by_category

        return result

    def calculate_with_quality(self, bom: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate PCF with data quality score and source tracking.

        Uses Brightway2 database for emission factors.

        Args:
            bom: List of BOM items with optional "data_source" field

        Returns:
            Dictionary with data_quality_score and data_sources
        """
        result = self.calculate_legacy(bom)

        data_sources = []

        for item in bom:
            data_source = item.get("data_source", None)
            if data_source and data_source not in data_sources:
                data_sources.append(data_source)

        if len(data_sources) > 0:
            quality_score = 1.0 / (1.0 + 0.1 * (len(data_sources) - 1))
        else:
            quality_score = 0.7

        result["data_quality_score"] = quality_score
        result["data_sources"] = data_sources

        return result

    def calculate_product(self, product_id: str, db_session) -> Dict[str, Any]:
        """
        Calculate PCF for a product from database using its BOM.

        This is a legacy method that delegates to the legacy_calculator module.
        For new implementations, use calculate() with an injected ef_provider.

        Args:
            product_id: UUID of product in database
            db_session: SQLAlchemy database session

        Returns:
            Dictionary with calculation results

        Raises:
            ValueError: If product not found in database
        """
        # Import here to avoid module-level SQLAlchemy dependency
        from backend.calculator.legacy_calculator import calculate_product_from_db
        return calculate_product_from_db(self, product_id, db_session)

    def _get_co2e_from_activity(self, activity) -> float:
        """
        Extract CO2e emission factor from Brightway2 activity.

        Args:
            activity: Brightway2 Activity object

        Returns:
            CO2e emission factor in kg CO2e per unit
        """
        for exchange in activity.exchanges():
            if exchange["type"] == "biosphere":
                return float(exchange["amount"])

        logger.warning(f"No biosphere exchange found for activity: {activity['name']}")
        return 0.0
