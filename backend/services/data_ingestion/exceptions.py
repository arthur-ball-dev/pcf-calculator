"""
Custom exceptions for data ingestion framework.

TASK-DATA-P5-001: Base Ingestion Framework

This module defines exception hierarchy for data ingestion operations:
- DataIngestionError: Base exception class
- FetchError: Errors during data fetch (network, HTTP errors)
- ParseError: Errors during data parsing (malformed files, encoding)
- TransformError: Errors during data transformation (schema mapping)
- ValidationError: Errors during record validation

Usage:
    from backend.services.data_ingestion.exceptions import (
        DataIngestionError, FetchError, ParseError, TransformError, ValidationError
    )

    try:
        data = await connector.fetch_raw_data()
    except FetchError as e:
        logger.error(f"Failed to fetch data: {e}")
"""

from typing import Optional, Dict, Any


class DataIngestionError(Exception):
    """
    Base exception for all data ingestion errors.

    All custom ingestion exceptions inherit from this class,
    allowing for broad exception handling when needed.

    Attributes:
        message: Human-readable error description
        details: Optional dictionary with additional context
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class FetchError(DataIngestionError):
    """
    Error during data fetch from external source.

    Raised when:
    - Network connection fails
    - HTTP request returns error status
    - Download times out
    - Server is unavailable

    Attributes:
        url: The URL that failed
        status_code: HTTP status code if applicable
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class ParseError(DataIngestionError):
    """
    Error during data parsing.

    Raised when:
    - File format is invalid (malformed CSV, XML, JSON)
    - Character encoding issues
    - Required columns/fields missing
    - Data structure doesn't match expected format

    Attributes:
        row_number: Row number where error occurred (if applicable)
        field_name: Field name that caused the error (if applicable)
    """

    def __init__(
        self,
        message: str,
        row_number: Optional[int] = None,
        field_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.row_number = row_number
        self.field_name = field_name


class TransformError(DataIngestionError):
    """
    Error during data transformation.

    Raised when:
    - Data type conversion fails
    - Required field mapping fails
    - Business rule validation fails during transform
    - Unit conversion fails

    Attributes:
        record_id: ID of the record that failed transformation
        source_field: Source field name
        target_field: Target field name
    """

    def __init__(
        self,
        message: str,
        record_id: Optional[str] = None,
        source_field: Optional[str] = None,
        target_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.record_id = record_id
        self.source_field = source_field
        self.target_field = target_field


class ValidationError(DataIngestionError):
    """
    Error during record validation.

    Raised when:
    - Required field is missing or null
    - Field value is out of valid range
    - Data integrity constraint violated
    - Business rule validation fails

    Note: This is different from pydantic.ValidationError. Use full import
    path when both are in use.

    Attributes:
        record_id: ID of the record that failed validation
        field: Field that failed validation
    """

    def __init__(
        self,
        message: str,
        record_id: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.record_id = record_id
        self.field = field


__all__ = [
    "DataIngestionError",
    "FetchError",
    "ParseError",
    "TransformError",
    "ValidationError",
]
