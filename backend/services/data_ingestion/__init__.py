"""
Data Ingestion Service Package.

TASK-DATA-P5-001: Base Ingestion Framework
TASK-DATA-P5-002: EPA Data Connector
TASK-DATA-P5-003: DEFRA Data Connector

This package provides the foundation for data ingestion from external sources:
- BaseDataIngestion: Abstract base class for all connectors
- EPAEmissionFactorsIngestion: EPA GHG Emission Factors Hub connector
- DEFRAEmissionFactorsIngestion: DEFRA UK Government Conversion Factors
- DataIngestionHTTPClient: HTTP client with retry logic
- Custom exceptions for error handling
- Pydantic schemas for validation

Usage:
    from backend.services.data_ingestion import (
        BaseDataIngestion,
        EPAEmissionFactorsIngestion,
        DEFRAEmissionFactorsIngestion,
        DataIngestionHTTPClient,
        DataIngestionError,
        FetchError,
        ParseError,
        TransformError,
        ValidationError,
    )

    # Using EPA connector
    ingestion = EPAEmissionFactorsIngestion(
        db=async_session,
        data_source_id="epa-source-uuid",
        file_key="fuels"  # or "egrid"
    )
    result = await ingestion.execute_sync()

    # Using DEFRA connector
    ingestion = DEFRAEmissionFactorsIngestion(
        db=async_session,
        data_source_id="defra-source-uuid"
    )
    result = await ingestion.execute_sync()

    # Custom connector
    class MyConnector(BaseDataIngestion):
        async def fetch_raw_data(self) -> bytes:
            client = DataIngestionHTTPClient()
            return await client.download_file("https://example.com/data.csv")

        async def parse_data(self, raw_data: bytes) -> List[Dict]:
            # Parse implementation
            ...

        async def transform_data(self, parsed_data: List[Dict]) -> List[Dict]:
            # Transform implementation
            ...
"""

from backend.services.data_ingestion.base import BaseDataIngestion
from backend.services.data_ingestion.epa_ingestion import (
    EPAEmissionFactorsIngestion
)
from backend.services.data_ingestion.defra_ingestion import (
    DEFRAEmissionFactorsIngestion
)
from backend.services.data_ingestion.http_client import DataIngestionHTTPClient
from backend.services.data_ingestion.exceptions import (
    DataIngestionError,
    FetchError,
    ParseError,
    TransformError,
    ValidationError,
)


__all__ = [
    # Base class
    "BaseDataIngestion",
    # Connectors
    "EPAEmissionFactorsIngestion",
    "DEFRAEmissionFactorsIngestion",
    # HTTP client
    "DataIngestionHTTPClient",
    # Exceptions
    "DataIngestionError",
    "FetchError",
    "ParseError",
    "TransformError",
    "ValidationError",
]
