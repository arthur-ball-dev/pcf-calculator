"""
Data Ingestion Service Package.

TASK-DATA-P5-001: Base Ingestion Framework
TASK-DATA-P5-002: EPA Data Connector
TASK-DATA-P5-003: DEFRA Data Connector
TASK-DATA-P5-004: Exiobase Data Connector
TASK-DATA-P5-005: Product Catalog Expansion
TASK-BE-P7-002: Connector Registry

This package provides the foundation for data ingestion from external sources:
- BaseDataIngestion: Abstract base class for all connectors
- EPAEmissionFactorsIngestion: EPA GHG Emission Factors Hub connector
- DEFRAEmissionFactorsIngestion: DEFRA UK Government Conversion Factors
- ExiobaseEmissionFactorsIngestion: Exiobase 3.8.2 MRIO connector
- DataIngestionHTTPClient: HTTP client with retry logic
- Custom exceptions for error handling
- Pydantic schemas for validation
- Connector Registry: Maps data source names to connector classes

Product Catalog Expansion (TASK-DATA-P5-005):
- CategoryLoader: Load hierarchical product categories
- ProductGenerator: Generate sample products per category
- FullTextSearchIndexer: Update FTS vectors for products and categories

Usage:
    from backend.services.data_ingestion import (
        BaseDataIngestion,
        EPAEmissionFactorsIngestion,
        DEFRAEmissionFactorsIngestion,
        ExiobaseEmissionFactorsIngestion,
        DataIngestionHTTPClient,
        DataIngestionError,
        FetchError,
        ParseError,
        TransformError,
        ValidationError,
        # Connector Registry (TASK-BE-P7-002)
        get_connector_class,
        CONNECTOR_REGISTRY,
        is_connector_available,
        list_registered_connectors,
        # Product Catalog Expansion
        CategoryLoader,
        ProductGenerator,
        FullTextSearchIndexer,
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

    # Using Exiobase connector
    ingestion = ExiobaseEmissionFactorsIngestion(
        db=async_session,
        data_source_id="exiobase-source-uuid"
    )
    result = await ingestion.execute_sync()

    # Using connector registry (TASK-BE-P7-002)
    ConnectorClass = get_connector_class("EPA GHG Emission Factors Hub")
    connector = ConnectorClass(db=session, data_source_id=source_id)
    result = await connector.execute_sync()

    # Product Catalog Expansion
    loader = CategoryLoader()
    tree = loader.generate_category_tree()
    await loader.load_categories_from_json(db, tree)

    generator = ProductGenerator()
    await generator.generate_products(db, categories, products_per_category=10)

    indexer = FullTextSearchIndexer()
    await indexer.update_product_vectors(db)
    await indexer.update_category_vectors(db)

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
from backend.services.data_ingestion.exiobase_ingestion import (
    ExiobaseEmissionFactorsIngestion
)
from backend.services.data_ingestion.http_client import DataIngestionHTTPClient
from backend.services.data_ingestion.exceptions import (
    DataIngestionError,
    FetchError,
    ParseError,
    TransformError,
    ValidationError,
)

# TASK-BE-P7-002: Connector Registry
from backend.services.data_ingestion.registry import (
    CONNECTOR_REGISTRY,
    get_connector_class,
    is_connector_available,
    list_registered_connectors,
)

# TASK-DATA-P5-005: Product Catalog Expansion
from backend.services.data_ingestion.category_loader import CategoryLoader
from backend.services.data_ingestion.product_generator import ProductGenerator
from backend.services.data_ingestion.fts_indexer import FullTextSearchIndexer


__all__ = [
    # Base class
    "BaseDataIngestion",
    # Connectors
    "EPAEmissionFactorsIngestion",
    "DEFRAEmissionFactorsIngestion",
    "ExiobaseEmissionFactorsIngestion",
    # HTTP client
    "DataIngestionHTTPClient",
    # Exceptions
    "DataIngestionError",
    "FetchError",
    "ParseError",
    "TransformError",
    "ValidationError",
    # Connector Registry (TASK-BE-P7-002)
    "CONNECTOR_REGISTRY",
    "get_connector_class",
    "is_connector_available",
    "list_registered_connectors",
    # Product Catalog Expansion (TASK-DATA-P5-005)
    "CategoryLoader",
    "ProductGenerator",
    "FullTextSearchIndexer",
]
