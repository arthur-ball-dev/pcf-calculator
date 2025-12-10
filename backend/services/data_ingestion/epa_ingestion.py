"""
EPA GHG Emission Factors Hub Data Connector.

TASK-DATA-P5-002: EPA Data Connector

This module implements the EPA GHG Emission Factors Hub connector that:
- Downloads Excel files from the EPA website
- Parses fuel and eGRID emission factor data
- Transforms records to internal schema with unit conversions
- Handles lb/MWh to kg/kWh conversion for eGRID data

Data Sources:
- EPA GHG Emission Factors Hub: https://www.epa.gov/climateleadership/ghg-emission-factors-hub
- eGRID Subregion Data: https://www.epa.gov/egrid

Usage:
    from backend.services.data_ingestion.epa_ingestion import EPAEmissionFactorsIngestion

    ingestion = EPAEmissionFactorsIngestion(
        db=session,
        data_source_id=source_id,
        file_key="fuels"  # or "egrid"
    )
    result = await ingestion.execute_sync()
"""

import io
from typing import List, Dict, Any

from openpyxl import load_workbook
import httpx

from backend.services.data_ingestion.base import BaseDataIngestion


class EPAEmissionFactorsIngestion(BaseDataIngestion):
    """
    EPA GHG Emission Factors Hub data connector.

    Supports two file types:
    - fuels: General fuel emission factors (natural gas, diesel, gasoline, etc.)
    - egrid: eGRID electricity emission factors by subregion

    Attributes:
        FILES: Configuration dict with URLs and sheet names for each file type
        file_key: Selected file type ("fuels" or "egrid")
        file_config: Configuration for the selected file type
    """

    # EPA file URLs (may need annual updates)
    FILES = {
        "egrid": {
            "url": "https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx",
            "sheets": ["SUBRGN22", "US22"],
            "type": "electricity",
        },
        "fuels": {
            "url": "https://www.epa.gov/system/files/documents/2024-01/emission-factors_apr2024.xlsx",
            "sheets": ["Table 1 - Fuel", "Table 2 - Mobile"],
            "type": "combustion",
        },
    }

    def __init__(self, *args, file_key: str = "fuels", **kwargs) -> None:
        """
        Initialize the EPA ingestion connector.

        Args:
            *args: Positional arguments passed to BaseDataIngestion
            file_key: Which EPA file to process ("fuels" or "egrid")
            **kwargs: Keyword arguments passed to BaseDataIngestion

        Raises:
            KeyError: If file_key is not "fuels" or "egrid"
        """
        super().__init__(*args, **kwargs)
        self.file_key = file_key
        self.file_config = self.FILES[file_key]

    async def fetch_raw_data(self) -> bytes:
        """
        Download EPA Excel file.

        Returns:
            Raw bytes of the Excel file content

        Raises:
            httpx.HTTPStatusError: On HTTP errors (4xx, 5xx)
            httpx.TimeoutException: On request timeout
        """
        url = self.file_config["url"]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def parse_data(self, raw_data: bytes) -> List[Dict[str, Any]]:
        """
        Parse EPA Excel file into records.

        Extracts data from specified sheets with column headers from first row.
        Each record includes source metadata (_source_sheet, _source_row).

        Args:
            raw_data: Raw bytes from fetch_raw_data()

        Returns:
            List of dictionaries, each representing one emission factor record

        Raises:
            Exception: On corrupted or invalid Excel file
        """
        workbook = load_workbook(io.BytesIO(raw_data), read_only=True)
        records = []

        for sheet_name in self.file_config["sheets"]:
            if sheet_name not in workbook.sheetnames:
                continue

            sheet = workbook[sheet_name]
            headers = None

            for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                # First non-empty row is headers
                if headers is None and any(row):
                    headers = [
                        str(h).strip() if h else f"col_{i}"
                        for i, h in enumerate(row)
                    ]
                    continue

                if headers and any(row):
                    record = dict(zip(headers, row))
                    record["_source_sheet"] = sheet_name
                    record["_source_row"] = row_idx + 1
                    records.append(record)

        workbook.close()
        return records

    async def transform_data(
        self, parsed_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform EPA data to internal schema.

        Routes to _transform_fuel_record or _transform_egrid_record based on
        file_key selection.

        Args:
            parsed_data: List of source-format records from parse_data()

        Returns:
            List of records matching EmissionFactor schema
        """
        transformed = []

        for record in parsed_data:
            # Handle different EPA file formats
            if self.file_key == "egrid":
                transformed.extend(self._transform_egrid_record(record))
            else:
                transformed.extend(self._transform_fuel_record(record))

        return transformed

    def _transform_fuel_record(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform fuel/combustion emission factor record.

        Handles both "Table 1 - Fuel" format (Fuel Type column) and
        "Table 2 - Mobile" format (Vehicle Type column).

        Args:
            record: Single parsed record from EPA fuel Excel file

        Returns:
            List containing zero or one transformed records
        """
        results = []

        # Map EPA columns to internal schema
        activity_name = record.get("Fuel Type") or record.get("Vehicle Type")
        if not activity_name:
            return results

        # Extract CO2e factor (EPA uses kg CO2e per unit)
        co2e = record.get("kg CO2e per unit") or record.get("CO2e Factor")
        if not co2e:
            return results

        try:
            co2e_value = float(co2e)
        except (ValueError, TypeError):
            return results

        results.append({
            "activity_name": str(activity_name).strip(),
            "co2e_factor": co2e_value,
            "unit": record.get("Unit", "unit"),
            "scope": self._determine_scope(record),
            "category": self.file_config["type"],
            "geography": "US",
            "reference_year": 2023,
            "data_quality_rating": 0.90,
            "external_id": f"EPA_{self.file_key}_{activity_name}".replace(" ", "_"),
            "metadata": {
                "source_sheet": record.get("_source_sheet"),
                "source_row": record.get("_source_row"),
            }
        })

        return results

    def _transform_egrid_record(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform eGRID electricity emission factor record.

        Converts EPA's lb/MWh units to kg/kWh for internal use:
        - 1 lb = 0.453592 kg
        - 1 MWh = 1000 kWh
        - lb/MWh * 0.453592 / 1000 = kg/kWh

        Args:
            record: Single parsed record from EPA eGRID Excel file

        Returns:
            List containing zero or one transformed records
        """
        results = []

        subregion = record.get("SUBRGN") or record.get("Subregion")
        if not subregion:
            return results

        # eGRID uses lb CO2e per MWh, convert to kg CO2e per kWh
        co2_rate = record.get("SRCO2RTA") or record.get("CO2 Rate")
        if not co2_rate:
            return results

        try:
            # Convert lb/MWh to kg/kWh
            co2e_value = float(co2_rate) * 0.453592 / 1000
        except (ValueError, TypeError):
            return results

        results.append({
            "activity_name": f"Grid Electricity - {subregion}",
            "co2e_factor": co2e_value,
            "unit": "kg CO2e/kWh",
            "scope": "Scope 2",
            "category": "electricity",
            "geography": "US",
            "reference_year": 2022,
            "data_quality_rating": 0.95,  # eGRID is highly reliable
            "external_id": f"EPA_eGRID_{subregion}",
            "metadata": {
                "subregion_code": subregion,
                "source_sheet": record.get("_source_sheet"),
            }
        })

        return results

    def _determine_scope(self, record: Dict[str, Any]) -> str:
        """
        Determine GHG Protocol scope from EPA data.

        Mapping:
        - Electricity -> Scope 2
        - Mobile/Transportation -> Scope 1
        - Other (stationary combustion, etc.) -> Scope 1

        Args:
            record: Parsed record containing Category field

        Returns:
            GHG Protocol scope string ("Scope 1" or "Scope 2")
        """
        category = record.get("Category", "").lower()
        if "electricity" in category:
            return "Scope 2"
        elif "mobile" in category or "transport" in category:
            return "Scope 1"
        else:
            return "Scope 1"


__all__ = [
    "EPAEmissionFactorsIngestion",
]
