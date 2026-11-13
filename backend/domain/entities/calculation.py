"""
Calculation Domain Entity

TASK-BE-P7-019: Domain Layer Separation

Contains pure Python domain entities for Calculation-related concepts.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from backend.domain.entities.errors import DomainValidationError


@dataclass(frozen=True)
class Calculation:
    """
    Calculation domain entity - immutable, no ORM dependency.

    Represents a completed PCF calculation with results.

    Attributes:
        id: Unique identifier for the calculation.
        product_id: ID of the product this calculation is for.
        total_co2e_kg: Total carbon emissions in kg CO2e.
        status: Calculation status (pending, completed, failed).
        calculation_type: Type of calculation (cradle_to_gate, etc.).
        materials_co2e: Optional emissions from materials.
        energy_co2e: Optional emissions from energy.
        transport_co2e: Optional emissions from transport.
        waste_co2e: Optional emissions from waste.
        created_at: When the calculation was requested.
        calculation_time_ms: How long the calculation took.
        breakdown: Emissions per component.
        error_message: Why the calculation failed, if it did.
    """

    id: str
    product_id: str
    total_co2e_kg: float
    status: str
    calculation_type: Optional[str] = None
    materials_co2e: Optional[float] = None
    energy_co2e: Optional[float] = None
    transport_co2e: Optional[float] = None
    waste_co2e: Optional[float] = None
    created_at: Optional[datetime] = None
    calculation_time_ms: Optional[int] = None
    breakdown: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate entity on construction."""
        if not self.id:
            raise DomainValidationError("Calculation ID cannot be empty")
        if self.total_co2e_kg < 0:
            raise DomainValidationError(
                f"CO2e value cannot be negative, got {self.total_co2e_kg}"
            )

    @property
    def public_status(self) -> str:
        """The status clients see: the runner's working states are all in_progress."""
        if self.status in ("running", "processing"):
            return "in_progress"
        return self.status


@dataclass(frozen=True)
class CalculationResult:
    """
    Result of creating a calculation request.

    Used for returning pending calculation status.

    Attributes:
        id: Unique identifier for the calculation.
        status: Current status (typically "pending").
        product_id: ID of the product being calculated.
        resolved_bom: The validated submitted BOM to calculate, or None for the catalog BOM.
    """

    id: str
    status: str
    product_id: str
    resolved_bom: Optional[Tuple["ResolvedBOMLine", ...]] = field(default=None, compare=False)


@dataclass(frozen=True)
class BOMLineInput:
    """
    One row of a BOM submitted with a calculation (the BOM as edited in the wizard, #195).

    Attributes:
        name: Component name, unique within the BOM (it keys the breakdown).
        quantity: Amount, in `unit`.
        unit: Unit of `quantity`; converted to the emission factor's unit.
        category: material, energy, transport, combustion or other.
        emission_factor_id: Emission factor to multiply by.
    """

    name: str
    quantity: Decimal
    unit: str
    category: str
    emission_factor_id: str


@dataclass(frozen=True)
class ResolvedBOMLine:
    """A validated BOM row, ready to calculate: quantity is in the factor's unit."""

    name: str
    quantity: Decimal
    co2e_factor: Decimal
    category: str


@dataclass(frozen=True)
class CreateCalculationRequest:
    """
    Request to create a new calculation.

    Attributes:
        product_id: ID of the product to calculate.
        calculation_type: Boundary to calculate (cradle_to_gate, etc.).
        bom: The submitted BOM, or None to calculate the catalog BOM.
    """

    product_id: str
    calculation_type: str
    bom: Optional[Tuple[BOMLineInput, ...]] = None
