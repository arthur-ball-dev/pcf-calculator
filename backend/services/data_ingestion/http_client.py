"""
HTTP client for data ingestion with retry logic.

TASK-DATA-P5-001: Base Ingestion Framework

This module provides DataIngestionHTTPClient with:
- Configurable timeout (default 300s for large files)
- Retry logic with exponential backoff
- Support for custom headers
- Proper error handling

Usage:
    from backend.services.data_ingestion.http_client import DataIngestionHTTPClient

    client = DataIngestionHTTPClient(timeout=60.0, max_retries=3)
    content = await client.download_file("https://example.com/data.csv")
"""

import asyncio
from typing import Optional, Dict

import httpx


class DataIngestionHTTPClient:
    """
    Configured HTTP client for data ingestion operations.

    Features:
    - Long timeout support for large file downloads
    - Automatic retry with exponential backoff for transient errors
    - Only retries on server errors (5xx) and network issues
    - Does not retry on client errors (4xx)

    Attributes:
        timeout: HTTP request timeout (default 300 seconds)
        max_retries: Maximum number of retry attempts (default 3)
    """

    # HTTP status codes that should trigger retry
    RETRYABLE_STATUS_CODES = {500, 502, 503, 504}

    def __init__(
        self,
        timeout: float = 300.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize HTTP client with configuration.

        Args:
            timeout: Request timeout in seconds (default 300 for large files)
            max_retries: Maximum retry attempts (default 3)
        """
        self.timeout = httpx.Timeout(timeout)
        self.max_retries = max_retries

    async def download_file(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Download file with retry logic.

        Implements exponential backoff: 2^attempt seconds between retries.
        Only retries on:
        - Server errors (5xx status codes)
        - Connection errors
        - Timeout errors

        Client errors (4xx) are not retried.

        Args:
            url: URL to download from
            headers: Optional custom headers (e.g., Authorization)

        Returns:
            Downloaded file content as bytes

        Raises:
            httpx.HTTPStatusError: On HTTP errors after max retries
            httpx.HTTPError: On network errors after max retries
            httpx.TimeoutException: On timeout after max retries
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)

                    # Check if status code is retryable
                    if response.status_code in self.RETRYABLE_STATUS_CODES:
                        # Raise for status to trigger retry logic
                        response.raise_for_status()

                    # For non-retryable errors (4xx), raise immediately
                    response.raise_for_status()

                    return response.content

            except httpx.HTTPStatusError as e:
                # Only retry on 5xx errors
                if e.response.status_code in self.RETRYABLE_STATUS_CODES:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                # 4xx errors - raise immediately without retry
                raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Network/timeout errors - retry with backoff
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

            except httpx.HTTPError as e:
                # Other HTTP errors - retry with backoff
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception

        raise httpx.HTTPError(f"Failed to download {url} after {self.max_retries} attempts")


__all__ = [
    "DataIngestionHTTPClient",
]
