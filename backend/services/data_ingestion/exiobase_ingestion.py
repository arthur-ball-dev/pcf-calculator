"""
Exiobase 3.8 Multi-Regional Input-Output Data Connector.

TASK-DATA-P5-004: Exiobase Data Connector
TASK-DATA-P8-003: Updated URL to v3.8 (Zenodo 5589597) for CC-BY-SA 4.0 compliance

CRITICAL LICENSE COMPLIANCE:
- MUST use Exiobase v3.8 (Zenodo 5589597) - CC-BY-SA 4.0 license
- DO NOT use v3.9 (Zenodo 14614930) - has Non-Commercial (NC) restrictions

This module implements the Exiobase connector that:
- Downloads the MRIO dataset ZIP from Zenodo
- Parses the F matrix (emission satellite accounts)
- Extracts emission factors across 200 products and 49 regions
- Aggregates GHGs to CO2e using GWP100 values
- Transforms records to internal schema

Data Source:
- Exiobase 3.8: https://zenodo.org/records/5589597
- License: CC-BY-SA 4.0 (allows commercial use with ShareAlike)

The F matrix contains emission intensities per product per region with:
- Rows: Environmental stressors (emissions like CO2, CH4, N2O)
- Columns: Region_Product combinations (e.g., "DE_Electricity by coal")

Usage:
    from backend.services.data_ingestion.exiobase_ingestion import (
        ExiobaseEmissionFactorsIngestion
    )

    ingestion = ExiobaseEmissionFactorsIngestion(
        db=session,
        data_source_id=source_id
    )
    result = await ingestion.execute_sync()
"""

import io
import zipfile
from typing import List, Dict, Any, Optional

import httpx
import pandas as pd

from backend.services.data_ingestion.base import BaseDataIngestion


class ExiobaseEmissionFactorsIngestion(BaseDataIngestion):
    """
    Exiobase 3.8 Multi-Regional Input-Output connector.

    Downloads and parses the Exiobase MRIO database, extracting emission
    factors from the F matrix (satellite accounts) for key product categories
    across 49 regions.

    CRITICAL: Uses v3.8 (CC-BY-SA 4.0) for commercial use compliance.
    DO NOT change to v3.9 which has Non-Commercial restrictions.

    Attributes:
        ZENODO_URL: URL to download Exiobase 3.8 IOT ZIP archive
        REGIONS: List of 49 Exiobase region codes (44 countries + 5 RoW)
        PRODUCT_CATEGORIES: Key product categories to extract
        GHG_STRESSORS: GHG emission stressors to process
        reference_year: Reference year for emission factors (default 2022)
    """

    # CRITICAL: Use Exiobase v3.8 (Zenodo 5589597) for CC-BY-SA 4.0 license
    # DO NOT use v3.9 (Zenodo 14614930) - has Non-Commercial (NC) restrictions
    # See: knowledge/db_compliance/External_Data_Source_Compliance_Guide.md
    ZENODO_URL = "https://zenodo.org/api/records/5589597/files/IOT_2019_ixi.zip/content"

    # All 49 Exiobase regions (44 countries + 5 rest-of-world regions)
    REGIONS = [
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
        "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
        "NL", "PL", "PT", "RO", "SE", "SI", "SK", "GB", "US", "JP",
        "CN", "CA", "KR", "BR", "IN", "MX", "RU", "AU", "CH", "TR",
        "TW", "NO", "ID", "ZA",
        "WA", "WL", "WE", "WF", "WM",  # Rest-of-world regions
    ]

    # Key product categories to extract (filtering from ~200 Exiobase products)
    PRODUCT_CATEGORIES = [
        "Electricity",
        "Gas/Diesel Oil",
        "Motor Gasoline",
        "Natural Gas",
        "Coal",
        "Iron and Steel",
        "Aluminium",
        "Cement",
        "Plastics",
        "Paper",
        "Textiles",
        "Chemicals",
        "Motor vehicles",
        "Electronic equipment",
        "Machinery",
    ]

    # GHG stressors to extract from F matrix
    GHG_STRESSORS = [
        "CO2 - combustion - air",
        "CH4 - combustion - air",
        "N2O - combustion - air",
        "CO2 - non combustion - Cement production",
        "CO2 - non combustion - Chemicals",
    ]

    # Possible F matrix file locations within the ZIP archive
    # Exiobase 3.8 uses satellite/F.txt path
    F_MATRIX_PATHS = [
        "satellite/F.txt",
        "satellite/F_",
        "IOT/F.txt",
        "IOT/F_",
        "F.txt",
        "F_",
    ]

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the Exiobase ingestion connector.

        Args:
            *args: Positional arguments passed to BaseDataIngestion
            **kwargs: Keyword arguments passed to BaseDataIngestion
        """
        super().__init__(*args, **kwargs)
        # v3.8 uses 2019 data year
        self.reference_year = 2019

    async def fetch_raw_data(self) -> bytes:
        """
        Download Exiobase ZIP file with streaming.

        Uses streaming download to handle the large file size (~500MB).
        Timeout is extended to 10 minutes to accommodate slow connections.

        Returns:
            Raw bytes of the downloaded ZIP archive

        Raises:
            httpx.HTTPStatusError: On HTTP errors (4xx, 5xx)
            httpx.TimeoutException: On request timeout
        """
        async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
            # Stream download for large file
            async with client.stream("GET", self.ZENODO_URL) as response:
                response.raise_for_status()
                chunks = []
                async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                    chunks.append(chunk)
                return b"".join(chunks)

    async def parse_data(self, raw_data: bytes) -> List[Dict[str, Any]]:
        """
        Parse Exiobase ZIP and extract emission factors from F matrix.

        The F matrix location may vary between Exiobase versions:
        - 3.8: satellite/F.txt

        This method searches multiple possible locations for the F matrix.

        Args:
            raw_data: Raw bytes of the ZIP archive from fetch_raw_data()

        Returns:
            List of dictionaries with extracted emission records containing:
            - stressor: Name of the GHG stressor
            - region: Region code (2-letter)
            - product: Product name
            - value: Emission intensity value

        Raises:
            zipfile.BadZipFile: On corrupted ZIP file
            ValueError: If F matrix not found in ZIP
        """
        records = []

        with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
            # Find emission satellite accounts - check multiple possible locations
            f_matrix_file = self._find_f_matrix_file(zf)

            if not f_matrix_file:
                raise ValueError("Could not find F matrix in Exiobase ZIP")

            with zf.open(f_matrix_file) as f:
                # Read TSV with pandas for efficient matrix handling
                df = pd.read_csv(
                    f,
                    sep="\t",
                    header=0,
                    index_col=0,
                    low_memory=False
                )

                records = self._extract_emission_factors(df)

        return records

    def _find_f_matrix_file(self, zf: zipfile.ZipFile) -> Optional[str]:
        """
        Find the F matrix file within the ZIP archive.

        Searches through multiple possible paths to find the F matrix,
        supporting Exiobase 3.8 file structure.

        Args:
            zf: Open ZipFile object

        Returns:
            Path to F matrix file within ZIP, or None if not found
        """
        all_files = zf.namelist()

        # Strategy 1: Check exact paths and patterns from F_MATRIX_PATHS
        for path_pattern in self.F_MATRIX_PATHS:
            for file_path in all_files:
                # Check for exact match or pattern match
                if path_pattern in file_path:
                    # Verify it's a .txt file
                    if file_path.endswith(".txt"):
                        return file_path

        # Strategy 2: Look for satellite files with F in the name
        satellite_files = [
            f for f in all_files
            if "satellite" in f.lower() and f.endswith(".txt")
        ]
        for f_file in satellite_files:
            if "/F.txt" in f_file or "/F_" in f_file:
                return f_file

        # Strategy 3: Look for IOT directory files
        iot_files = [
            f for f in all_files
            if "iot" in f.lower() and f.endswith(".txt")
        ]
        for f_file in iot_files:
            # Look for emission intensity files (F or S matrix)
            if "/F.txt" in f_file or "/F_" in f_file or "F.txt" in f_file:
                return f_file

        # Strategy 4: Any file named F.txt or starting with F_
        for f_file in all_files:
            if f_file.endswith("/F.txt") or "/F_" in f_file:
                return f_file

        return None

    def _extract_emission_factors(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract emission factors from F matrix DataFrame.

        Filters to:
        1. Only GHG stressors (rows)
        2. Only key product categories (columns)

        Args:
            df: Pandas DataFrame of F matrix with stressors as index

        Returns:
            List of emission records with stressor, region, product, value
        """
        records = []

        # Filter to GHG stressors only
        ghg_df = df[df.index.isin(self.GHG_STRESSORS)]

        if ghg_df.empty:
            # Try partial matching for GHG stressors if exact match fails
            ghg_df = df[df.index.str.contains("CO2|CH4|N2O", case=False, na=False)]

        for stressor_name in ghg_df.index:
            for column in ghg_df.columns:
                value = ghg_df.loc[stressor_name, column]

                if pd.isna(value) or value == 0:
                    continue

                # Parse column name (format: "Region_Product")
                parts = column.split("_", 1)
                if len(parts) != 2:
                    continue

                region, product = parts

                # Filter to key product categories
                if not any(cat.lower() in product.lower()
                          for cat in self.PRODUCT_CATEGORIES):
                    continue

                records.append({
                    "stressor": stressor_name,
                    "region": region,
                    "product": product,
                    "value": float(value),
                })

        return records

    async def transform_data(
        self, parsed_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform Exiobase data to internal schema.

        Aggregates multiple GHG stressors for the same region/product combination
        into a single CO2e value using GWP100 conversion factors.

        Args:
            parsed_data: List of parsed emission records from parse_data()

        Returns:
            List of records matching EmissionFactor schema with fields:
            - activity_name: Product name with region
            - co2e_factor: CO2 equivalent emission factor
            - unit: "kg CO2e per EUR output"
            - scope: "Scope 3" (supply chain emissions)
            - category: Product category
            - geography: Region code
            - reference_year: 2019 (v3.8 data year)
            - data_quality_rating: 0.75 (aggregated data)
            - external_id: Unique identifier
            - metadata: Additional information
        """
        # Group by region and product, summing CO2e
        aggregated: Dict[tuple, Dict[str, Any]] = {}

        for record in parsed_data:
            key = (record["region"], record["product"])

            if key not in aggregated:
                aggregated[key] = {
                    "region": record["region"],
                    "product": record["product"],
                    "co2e_total": 0,
                    "stressors": [],
                }

            # Convert different GHGs to CO2e
            co2e = self._convert_to_co2e(
                record["stressor"],
                record["value"]
            )
            aggregated[key]["co2e_total"] += co2e
            aggregated[key]["stressors"].append(record["stressor"])

        # Transform to internal schema
        transformed = []
        for key, data in aggregated.items():
            region, product = key

            # Clean product name
            clean_product = self._clean_product_name(product)

            external_id = f"EXIO_{region}_{clean_product}"[:200]

            transformed.append({
                "activity_name": f"{clean_product} ({region})",
                "co2e_factor": data["co2e_total"],
                "unit": "kg CO2e per EUR output",  # Exiobase uses monetary units
                "scope": "Scope 3",
                "category": self._categorize_product(product),
                "geography": region,
                "reference_year": self.reference_year,
                "data_quality_rating": 0.75,
                "external_id": external_id,
                "metadata": {
                    "stressors_included": list(set(data["stressors"])),
                    "source": "Exiobase 3.8",
                }
            })

        return transformed

    def _convert_to_co2e(self, stressor: str, value: float) -> float:
        """
        Convert GHG to CO2 equivalent using GWP100.

        Uses AR5 Global Warming Potential values:
        - CO2: GWP = 1
        - CH4: GWP = 28
        - N2O: GWP = 265

        Args:
            stressor: Name of the GHG stressor
            value: Raw emission value

        Returns:
            CO2 equivalent value
        """
        gwp = {
            "CO2": 1,
            "CH4": 28,  # AR5 GWP100
            "N2O": 265,  # AR5 GWP100
        }

        for gas, multiplier in gwp.items():
            if gas in stressor.upper():
                return value * multiplier

        return value  # Assume CO2 if unknown

    def _clean_product_name(self, product: str) -> str:
        """
        Clean and normalize product name.

        Removes region prefixes if present and replaces special characters
        with spaces. Truncates to 100 characters.

        Args:
            product: Raw product name from Exiobase

        Returns:
            Cleaned and normalized product name
        """
        # Remove region prefix if present
        if "_" in product:
            product = product.split("_", 1)[-1]

        # Replace special characters
        product = product.replace("_", " ").replace("-", " ")

        return product.strip()[:100]

    def _categorize_product(self, product: str) -> str:
        """
        Assign category based on product name.

        Maps Exiobase product names to simplified categories for filtering.

        Args:
            product: Product name from Exiobase

        Returns:
            Category string (e.g., "electricity", "energy", "materials")
        """
        product_lower = product.lower()

        categories = {
            "electricity": "electricity",
            "gas": "energy",
            "coal": "energy",
            "oil": "energy",
            "steel": "materials",
            "alumin": "materials",
            "cement": "materials",
            "plastic": "materials",
            "paper": "materials",
            "textile": "materials",
            "chemical": "materials",
            "vehicle": "transport",
            "electronic": "electronics",
            "machine": "machinery",
        }

        for keyword, category in categories.items():
            if keyword in product_lower:
                return category

        return "other"


__all__ = [
    "ExiobaseEmissionFactorsIngestion",
]
