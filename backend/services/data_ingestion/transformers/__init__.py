"""
Transformers Package for Data Ingestion.

TASK-DATA-P7-025: Refactor High-Complexity Transform Function

This package provides modular, low-complexity transformation functions
for ETL pipelines. Each transformer handles a specific data type with
clear single-responsibility methods.

Components:
- helpers.py: Common helper functions (parse_emission_factor, convert_unit, etc.)
- fuel_transformer.py: FuelTransformer class for fuel emission records

Usage:
    from backend.services.data_ingestion.transformers import (
        FuelTransformer,
        TransformedRecord,
        TransformationError,
        parse_emission_factor,
        validate_required_fields,
        convert_unit,
        parse_uncertainty,
        normalize_fuel_type,
    )

    transformer = FuelTransformer()
    result = transformer.transform(raw_record)
"""

from backend.services.data_ingestion.transformers.helpers import (
    TransformationError,
    parse_emission_factor,
    validate_required_fields,
    convert_unit,
    parse_uncertainty,
    normalize_fuel_type,
)

from backend.services.data_ingestion.transformers.fuel_transformer import (
    FuelTransformer,
    TransformedRecord,
)


__all__ = [
    # Exception
    "TransformationError",
    # Helper functions
    "parse_emission_factor",
    "validate_required_fields",
    "convert_unit",
    "parse_uncertainty",
    "normalize_fuel_type",
    # Transformer class
    "FuelTransformer",
    "TransformedRecord",
]
