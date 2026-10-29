"""
Emission Factor Provider Interface and Data Transfer Objects.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

This module defines the abstraction layer for emission factor data access,
allowing the PCF calculator to work with different data sources through
dependency injection.

Key Components:
- EmissionFactorDTO: Immutable data transfer object (no ORM dependency)
- EmissionFactorProvider: Abstract interface for data access

Design Principles:
- No SQLAlchemy imports in this module
- Frozen dataclasses for immutability
- Async interface for compatibility with async SQLAlchemy
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class EmissionFactorDTO:
    """
    Data transfer object for emission factors - no ORM dependency.

    This immutable object carries emission factor data between layers
    without coupling to any specific database implementation.

    Attributes:
        id: Unique identifier for the emission factor
        category: Material/process category (e.g., "steel", "aluminum")
        co2e_kg: CO2 equivalent in kg per unit
        unit: Unit of measurement (e.g., "kg", "kWh")
        data_source: Data source name (e.g., "EPA", "DEFRA")
        uncertainty: Optional uncertainty value (0.0-1.0)

    Example:
        >>> ef = EmissionFactorDTO(
        ...     id="ef-001",
        ...     category="steel",
        ...     co2e_kg=2.5,
        ...     unit="kg",
        ...     data_source="EPA"
        ... )
        >>> ef.co2e_kg
        2.5
    """

    id: str
    category: str
    co2e_kg: float
    unit: str
    data_source: str
    uncertainty: Optional[float] = None


class EmissionFactorProvider(ABC):
    """
    Abstract interface for emission factor data access.

    This interface defines the contract that all emission factor providers
    must implement, enabling dependency injection and easy testing with
    mock providers.

    Implementing classes:
    - SQLAlchemyEmissionFactorProvider: Database access via SQLAlchemy ORM
    - CachedEmissionFactorProvider: Caching wrapper for any provider
    - MockEmissionFactorProvider: For testing (in test files)

    Example usage with dependency injection:
        >>> provider = SQLAlchemyEmissionFactorProvider(session)
        >>> cached_provider = CachedEmissionFactorProvider(provider, ttl_seconds=300)
        >>> calculator = PCFCalculator(ef_provider=cached_provider)
    """

    @abstractmethod
    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """
        Get emission factor by category name.

        Args:
            category: Material/process category (e.g., "steel", "aluminum")

        Returns:
            EmissionFactorDTO if found, None otherwise

        Example:
            >>> ef = await provider.get_by_category("steel")
            >>> if ef:
            ...     print(f"Steel: {ef.co2e_kg} kg CO2e/kg")
        """
        pass

    @abstractmethod
    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """
        Get all emission factors as category -> DTO mapping.

        Returns:
            Dictionary mapping category names to EmissionFactorDTO objects

        Example:
            >>> all_efs = await provider.get_all()
            >>> for category, ef in all_efs.items():
            ...     print(f"{category}: {ef.co2e_kg} kg CO2e/{ef.unit}")
        """
        pass
