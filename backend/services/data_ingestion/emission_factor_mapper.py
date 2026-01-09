"""
Emission Factor Mapper Service

TASK-DATA-P8-004: Emission Factor Mapping Infrastructure

Maps BOM component names to emission factors from external sources.
Supports exact match, fuzzy match, category-based fallbacks, and proxy factors.

Mapping Strategy:
1. Exact Match - activity_name matches exactly
2. Partial Match - case-insensitive substring
3. Category Fallback - use category-level average
4. Geographic Fallback - use GLO if specific region unavailable
5. Proxy Factor - use calculated proxy from EPA+DEFRA
6. Log Warning - record unmapped component

CRITICAL: Proxy factors use EPA + DEFRA only (no Exiobase) to avoid ShareAlike.

Usage:
    from backend.services.data_ingestion.emission_factor_mapper import (
        EmissionFactorMapper
    )

    mapper = EmissionFactorMapper(db=async_session)
    factor = await mapper.get_factor_for_component(
        component_name="aluminum",
        unit="kg",
        geography="US"
    )

    # Get unmapped component warnings
    warnings = mapper.get_warnings()

    # Clear cache for fresh lookups
    mapper.clear_cache()
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EmissionFactor, DataSource


logger = logging.getLogger(__name__)

# Path to mapping configuration
MAPPING_CONFIG_PATH = Path(__file__).parent.parent.parent / "data" / "emission_factor_mappings.json"


class EmissionFactorMapper:
    """
    Maps component names to emission factors.

    Provides a hierarchical lookup strategy:
    1. Check cache first
    2. Try exact match on activity_name
    3. Try partial/fuzzy match (ILIKE)
    4. Try category-based fallback
    5. Try geographic fallback (GLO)
    6. Try proxy factor
    7. Log warning if not found

    Attributes:
        db: AsyncSession for database queries
        _mapping_cache: Dict caching lookups by key
        _warnings: List of unmapped component warnings
        _aliases: Dict mapping alternate names to canonical names
        _mappings: Dict mapping canonical names to activity_names
        _category_defaults: Dict of category default factors
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the mapper.

        Args:
            db: SQLAlchemy async session for database operations
        """
        self.db = db
        self._mapping_cache: Dict[str, Optional[EmissionFactor]] = {}
        self._warnings: List[Dict[str, Any]] = []
        self._aliases: Dict[str, str] = {}
        self._mappings: Dict[str, List[str]] = {}
        self._category_defaults: Dict[str, str] = {}

        # Load mapping configuration
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load mapping configuration from JSON file."""
        try:
            if MAPPING_CONFIG_PATH.exists():
                with open(MAPPING_CONFIG_PATH, 'r') as f:
                    config = json.load(f)

                self._mappings = config.get("mappings", {})
                self._aliases = config.get("aliases", {})
                self._category_defaults = config.get("category_defaults", {})

                logger.info(
                    f"Loaded mapping config: {len(self._mappings)} mappings, "
                    f"{len(self._aliases)} aliases"
                )
            else:
                logger.warning(
                    f"Mapping config not found at {MAPPING_CONFIG_PATH}, using defaults"
                )
                # Default aliases for common variations
                self._aliases = {
                    "aluminium": "aluminum",
                    "aluminium_sheet": "aluminum",
                    "steel_cold_rolled": "steel",
                    "hdpe": "plastic_abs",
                    "ldpe": "plastic_abs",
                }
        except Exception as e:
            logger.error(f"Error loading mapping config: {e}")
            self._mappings = {}
            self._aliases = {}
            self._category_defaults = {}

    def _resolve_alias(self, component_name: str) -> str:
        """
        Resolve component name through alias mapping.

        Args:
            component_name: Original component name

        Returns:
            Canonical name if alias exists, otherwise original name
        """
        lower_name = component_name.lower().strip()
        return self._aliases.get(lower_name, component_name)

    async def get_factor_for_component(
        self,
        component_name: str,
        unit: str,
        geography: Optional[str] = None,
    ) -> Optional[EmissionFactor]:
        """
        Get emission factor for a BOM component.

        Matching priority:
        1. Exact match on activity_name
        2. Partial/fuzzy match
        3. Category fallback
        4. Geographic fallback (GLO)
        5. Proxy factor
        6. Return None and log warning

        Args:
            component_name: Name of BOM component
            unit: Unit of measurement
            geography: Optional geographic region

        Returns:
            Matching EmissionFactor or None if not found
        """
        # Resolve aliases first
        resolved_name = self._resolve_alias(component_name)

        # Build cache key
        cache_key = f"{resolved_name}:{unit}:{geography or 'any'}"

        # Check cache first
        if cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        # Try exact match
        factor = await self._exact_match(resolved_name, unit, geography)
        if factor:
            self._mapping_cache[cache_key] = factor
            return factor

        # Try partial match
        factor = await self._partial_match(resolved_name, unit, geography)
        if factor:
            self._mapping_cache[cache_key] = factor
            return factor

        # Try category fallback
        factor = await self._category_fallback(resolved_name, unit)
        if factor:
            self._mapping_cache[cache_key] = factor
            return factor

        # Try geographic fallback (GLO) if not already GLO
        if geography and geography != "GLO":
            factor = await self._exact_match(resolved_name, unit, "GLO")
            if factor:
                self._mapping_cache[cache_key] = factor
                return factor

        # Try proxy factor
        factor = await self._get_proxy_factor(resolved_name, unit)
        if factor:
            self._mapping_cache[cache_key] = factor
            return factor

        # Log warning for unmapped component
        self._warnings.append({
            "component_name": component_name,
            "unit": unit,
            "geography": geography,
            "message": "No emission factor found",
        })
        logger.warning(f"No emission factor found for: {component_name} ({unit})")

        # Cache the miss to avoid repeated lookups
        self._mapping_cache[cache_key] = None
        return None

    async def _exact_match(
        self,
        component_name: str,
        unit: str,
        geography: Optional[str],
    ) -> Optional[EmissionFactor]:
        """
        Find exact match on activity_name.

        Args:
            component_name: Name to match exactly
            unit: Unit of measurement
            geography: Optional geographic region

        Returns:
            EmissionFactor if found, None otherwise
        """
        query = select(EmissionFactor).where(
            EmissionFactor.activity_name == component_name,
            EmissionFactor.unit == unit,
            EmissionFactor.is_active == True,
        )
        if geography:
            query = query.where(EmissionFactor.geography == geography)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _partial_match(
        self,
        component_name: str,
        unit: str,
        geography: Optional[str],
    ) -> Optional[EmissionFactor]:
        """
        Find partial match using ILIKE (case-insensitive).

        Returns the factor with the shortest activity_name (most specific match).

        Args:
            component_name: Name to search for (substring)
            unit: Unit of measurement
            geography: Optional geographic region

        Returns:
            Best matching EmissionFactor or None
        """
        query = select(EmissionFactor).where(
            EmissionFactor.activity_name.ilike(f"%{component_name}%"),
            EmissionFactor.unit == unit,
            EmissionFactor.is_active == True,
        )
        if geography:
            query = query.where(EmissionFactor.geography == geography)

        result = await self.db.execute(query)
        factors = result.scalars().all()

        # Return best match (shortest name = most specific)
        if factors:
            return min(factors, key=lambda f: len(f.activity_name))
        return None

    async def _category_fallback(
        self,
        component_name: str,
        unit: str,
    ) -> Optional[EmissionFactor]:
        """
        Find average factor for similar category.

        Args:
            component_name: Name to extract category from
            unit: Unit of measurement

        Returns:
            Category-level EmissionFactor or None
        """
        # Extract category from component name
        category = self._extract_category(component_name)
        if not category:
            return None

        query = select(EmissionFactor).where(
            EmissionFactor.category == category,
            EmissionFactor.unit == unit,
            EmissionFactor.is_active == True,
        )
        result = await self.db.execute(query)
        factors = result.scalars().all()

        if factors:
            # Return first match (could enhance to return average)
            return factors[0]
        return None

    async def _get_proxy_factor(
        self,
        component_name: str,
        unit: str,
    ) -> Optional[EmissionFactor]:
        """
        Get proxy factor from calculated proxies.

        Proxy factors are marked with data_source="PROXY" and include
        derivation metadata documenting how they were calculated from
        EPA + DEFRA data (no Exiobase to avoid ShareAlike).

        Args:
            component_name: Name to look up in proxy factors
            unit: Unit of measurement

        Returns:
            Proxy EmissionFactor or None
        """
        return await self._load_proxy_factor(component_name, unit)

    async def _load_proxy_factor(
        self,
        component_name: str,
        unit: str,
    ) -> Optional[EmissionFactor]:
        """
        Load proxy factor from database.

        Args:
            component_name: Name to look up
            unit: Unit of measurement

        Returns:
            Proxy EmissionFactor or None
        """
        query = select(EmissionFactor).where(
            EmissionFactor.activity_name == component_name,
            EmissionFactor.data_source == "PROXY",
            EmissionFactor.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _extract_category(self, component_name: str) -> Optional[str]:
        """
        Extract category from component name.

        Maps component name keywords to standardized categories.

        Args:
            component_name: Name to extract category from

        Returns:
            Category string or None
        """
        category_map = {
            # Materials
            "steel": "material",
            "aluminum": "material",
            "aluminium": "material",
            "plastic": "material",
            "copper": "material",
            "glass": "material",
            "rubber": "material",
            "textile": "material",
            "paper": "material",
            "cardboard": "material",
            "wood": "material",
            "concrete": "material",
            "cement": "material",
            "lithium": "material",
            "battery": "material",
            "semiconductor": "material",
            "carbon": "material",
            "fiber": "material",
            # Energy
            "electricity": "energy",
            "power": "energy",
            "grid": "energy",
            "natural_gas": "energy",
            "diesel": "energy",
            "fuel": "energy",
            # Transport
            "transport": "transport",
            "shipping": "transport",
            "freight": "transport",
            "truck": "transport",
            "ship": "transport",
            "air": "transport",
            # Other
            "packaging": "other",
            "water": "other",
            "waste": "other",
        }

        component_lower = component_name.lower()
        for keyword, category in category_map.items():
            if keyword in component_lower:
                return category
        return None

    def get_warnings(self) -> List[Dict[str, Any]]:
        """
        Return list of unmapped components.

        Returns:
            List of warning dicts with component_name, unit, geography, message
        """
        return self._warnings.copy()

    def clear_cache(self) -> None:
        """Clear mapping cache and warnings."""
        self._mapping_cache.clear()
        self._warnings.clear()
        logger.debug("Mapper cache cleared")

    async def get_coverage_report(
        self,
        component_names: List[str],
        unit: str = "kg",
    ) -> Dict[str, Any]:
        """
        Generate coverage report for a list of component names.

        Args:
            component_names: List of component names to check
            unit: Default unit for lookups

        Returns:
            Dict with coverage statistics
        """
        total = len(component_names)
        mapped = 0
        unmapped = []
        proxy_used = 0

        for name in component_names:
            factor = await self.get_factor_for_component(name, unit)
            if factor:
                mapped += 1
                if factor.data_source == "PROXY":
                    proxy_used += 1
            else:
                unmapped.append(name)

        return {
            "total_components": total,
            "mapped_count": mapped,
            "unmapped_count": len(unmapped),
            "coverage_percentage": (mapped / total * 100) if total > 0 else 0,
            "proxy_usage_count": proxy_used,
            "unmapped_components": unmapped,
        }


__all__ = [
    "EmissionFactorMapper",
]
