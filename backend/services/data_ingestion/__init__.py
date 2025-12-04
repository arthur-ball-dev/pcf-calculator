"""
Data Ingestion Service Package.

TASK-DATA-P5-001: Base Ingestion Framework

This package provides the foundation for data ingestion from external sources:
- BaseDataIngestion: Abstract base class for all connectors
- DataIngestionHTTPClient: HTTP client with retry logic
- Custom exceptions for error handling
- Pydantic schemas for validation

Usage:
    from backend.services.data_ingestion import (
        BaseDataIngestion,
        DataIngestionHTTPClient,
        DataIngestionError,
        FetchError,
        ParseError,
        TransformError,
        ValidationError,
    )

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
    # HTTP client
    "DataIngestionHTTPClient",
    # Exceptions
    "DataIngestionError",
    "FetchError",
    "ParseError",
    "TransformError",
    "ValidationError",
]
