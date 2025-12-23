"""
Calculation Domain Entity

TASK-BE-P7-019: Domain Layer Separation

Contains pure Python domain entities for Calculation-related concepts.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass
from typing import Optional

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

    def __post_init__(self):
        """Validate entity on construction."""
        if not self.id:
            raise DomainValidationError("Calculation ID cannot be empty")
        if self.total_co2e_kg < 0:
            raise DomainValidationError(
                f"CO2e value cannot be negative, got {self.total_co2e_kg}"
            )


@dataclass(frozen=True)
class CalculationResult:
    """
    Result of creating a calculation request.

    Used for returning pending calculation status.

    Attributes:
        id: Unique identifier for the calculation.
        status: Current status (typically "pending").
        product_id: ID of the product being calculated.
    """

    id: str
    status: str
    product_id: str


@dataclass(frozen=True)
class CreateCalculationRequest:
    """
    Request to create a new calculation.

    Attributes:
        product_id: ID of the product to calculate.
        calculation_method: Method to use (attributional, consequential).
        include_transport: Whether to include transport emissions.
    """

    product_id: str
    calculation_method: str
    include_transport: bool = False
