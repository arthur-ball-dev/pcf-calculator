"""
Emission Factor Domain Entities

Emission factors and the licence details of the data sources behind them.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class EmissionFactor:
    """An emission factor, as stored."""

    id: str
    activity_name: str
    co2e_factor: float
    unit: str
    data_source: str
    geography: str
    category: Optional[str] = None
    reference_year: Optional[int] = None
    data_quality_rating: Optional[float] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class NewEmissionFactor:
    """The fields of an emission factor to create."""

    activity_name: str
    co2e_factor: float
    unit: str
    data_source: str
    geography: str
    category: Optional[str] = None
    reference_year: Optional[int] = None
    data_quality_rating: Optional[float] = None
    uncertainty_min: Optional[float] = None
    uncertainty_max: Optional[float] = None
    data_source_id: Optional[str] = None


@dataclass(frozen=True)
class EmissionFactorFilters:
    """List filters: exact matches, except a partial case-insensitive activity name."""

    data_source: Optional[str] = None
    geography: Optional[str] = None
    unit: Optional[str] = None
    activity_name: Optional[str] = None


@dataclass(frozen=True)
class EmissionFactorPage:
    """One page of emission factors and the total matching count."""

    items: List[EmissionFactor]
    total: int


@dataclass(frozen=True)
class DataSourceLicense:
    """Licence and attribution details of an active data source."""

    id: str
    name: str
    license_type: Optional[str] = None
    license_url: Optional[str] = None
    attribution_text: Optional[str] = None
    attribution_url: Optional[str] = None
    allows_commercial_use: bool = True
    requires_attribution: bool = False
    requires_share_alike: bool = False
