"""
Data Connector Registry.

TASK-BE-P7-002: Activate Data Connector Admin Endpoints

This module provides a registry mapping data source names to their
corresponding connector classes. Used by the admin sync endpoint
to determine which connector to invoke for a given data source.

Usage:
    from backend.services.data_ingestion.registry import (
        get_connector_class,
        CONNECTOR_REGISTRY,
    )

    # Get connector class by data source name
    ConnectorClass = get_connector_class("EPA GHG Emission Factors Hub")
    connector = ConnectorClass(db=session, data_source_id=source_id)
    result = await connector.execute_sync()

    # Check if connector exists
    if "My Source" in CONNECTOR_REGISTRY:
        ...
"""

from typing import Dict, Type

from backend.services.data_ingestion.base import BaseDataIngestion
from backend.services.data_ingestion.epa_ingestion import EPAEmissionFactorsIngestion
from backend.services.data_ingestion.defra_ingestion import DEFRAEmissionFactorsIngestion
from backend.services.data_ingestion.exiobase_ingestion import ExiobaseEmissionFactorsIngestion


# Registry mapping data source names to connector classes
# Keys must match the 'name' field in data_sources table exactly
CONNECTOR_REGISTRY: Dict[str, Type[BaseDataIngestion]] = {
    "EPA GHG Emission Factors Hub": EPAEmissionFactorsIngestion,
    "DEFRA Conversion Factors": DEFRAEmissionFactorsIngestion,
    "Exiobase": ExiobaseEmissionFactorsIngestion,
}


def get_connector_class(data_source_name: str) -> Type[BaseDataIngestion]:
    """
    Get the connector class for a data source name.

    Args:
        data_source_name: Exact name of the data source as stored in database

    Returns:
        Connector class that inherits from BaseDataIngestion

    Raises:
        ValueError: If no connector is registered for the given name
    """
    if data_source_name not in CONNECTOR_REGISTRY:
        raise ValueError(
            f"No connector registered for data source: '{data_source_name}'. "
            f"Available connectors: {list(CONNECTOR_REGISTRY.keys())}"
        )
    return CONNECTOR_REGISTRY[data_source_name]


def is_connector_available(data_source_name: str) -> bool:
    """
    Check if a connector is available for a data source name.

    Args:
        data_source_name: Name of the data source

    Returns:
        True if a connector is registered, False otherwise
    """
    return data_source_name in CONNECTOR_REGISTRY


def list_registered_connectors() -> list[str]:
    """
    List all registered connector names.

    Returns:
        List of data source names with registered connectors
    """
    return list(CONNECTOR_REGISTRY.keys())


__all__ = [
    "CONNECTOR_REGISTRY",
    "get_connector_class",
    "is_connector_available",
    "list_registered_connectors",
]
