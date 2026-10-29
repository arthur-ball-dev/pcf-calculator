"""
Safe HTTP Client with SSRF Protection.

TASK-BE-P7-021: SSRF Prevention in Data Connectors

This module provides a secure HTTP client wrapper that integrates URL
validation with SSRF protection. All data connectors should use this
client instead of making direct HTTP requests.

Features:
- Pre-request URL validation
- Redirect validation (each redirect target is validated)
- Response size limits
- Configurable timeouts
- Maximum redirect limits

Usage:
    from backend.services.data_ingestion.security import (
        SafeHTTPClient,
        URLValidator,
        get_allowed_domains
    )

    validator = URLValidator(allowed_domains=get_allowed_domains())
    client = SafeHTTPClient(validator=validator)
    response = await client.get("https://api.epa.gov/data")
"""

from typing import Optional
import httpx

from .url_validator import URLValidator
from .exceptions import SSRFBlockedError


class SafeHTTPClient:
    """
    HTTP client with built-in SSRF protection.

    This client wraps httpx.AsyncClient and performs URL validation
    before every request. It also validates redirect targets and
    enforces response size limits.

    Attributes:
        validator: URLValidator instance for URL validation.
        timeout: Request timeout in seconds.
        max_size: Maximum response size in bytes.
        follow_redirects: Whether to follow redirects.
        max_redirects: Maximum number of redirects to follow.

    Example:
        >>> validator = URLValidator(allowed_domains=["api.epa.gov"])
        >>> client = SafeHTTPClient(validator=validator, timeout=30.0)
        >>> response = await client.get("https://api.epa.gov/data")
        >>> response.status_code
        200
    """

    def __init__(
        self,
        validator: URLValidator,
        timeout: float = 30.0,
        max_size: int = 10 * 1024 * 1024,  # 10MB default
        follow_redirects: bool = True,
        max_redirects: int = 5,
    ):
        """
        Initialize SafeHTTPClient.

        Args:
            validator: URLValidator instance for URL validation.
            timeout: Request timeout in seconds (default: 30.0).
            max_size: Maximum response size in bytes (default: 10MB).
            follow_redirects: Whether to follow redirects (default: True).
            max_redirects: Maximum number of redirects to follow (default: 5).
        """
        self.validator = validator
        self.timeout = timeout
        self.max_size = max_size
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects

    async def get(
        self,
        url: str,
        headers: Optional[dict] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a GET request with SSRF protection.

        Validates the URL before making the request. If redirects are
        enabled, each redirect target is also validated.

        Args:
            url: The URL to fetch.
            headers: Optional headers to include in the request.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            httpx.Response object.

        Raises:
            SSRFBlockedError: If the URL or any redirect target fails validation.
            httpx.TimeoutException: If the request times out.
        """
        # Validate original URL before making request
        self.validator.validate(url)

        # Create client with follow_redirects=False to handle manually
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=False,
        ) as client:
            response = await self._fetch_with_redirect_validation(
                client=client,
                url=url,
                headers=headers,
                redirect_count=0,
                **kwargs
            )
            return response

    async def _fetch_with_redirect_validation(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Optional[dict],
        redirect_count: int,
        **kwargs
    ) -> httpx.Response:
        """
        Fetch URL with redirect validation.

        Each redirect target is validated against SSRF rules before
        following.

        Args:
            client: httpx.AsyncClient instance.
            url: The URL to fetch.
            headers: Optional headers.
            redirect_count: Current redirect count.
            **kwargs: Additional arguments.

        Returns:
            httpx.Response object.

        Raises:
            SSRFBlockedError: If redirect count exceeded or target blocked.
        """
        # Check redirect limit
        if redirect_count > self.max_redirects:
            raise SSRFBlockedError(
                f"Too many redirects (exceeded maximum of {self.max_redirects})"
            )

        # Make request
        response = await client.get(url, headers=headers, **kwargs)

        # Handle redirects
        if response.is_redirect and self.follow_redirects:
            redirect_url = response.headers.get("location")

            if not redirect_url:
                raise SSRFBlockedError("Redirect response missing Location header")

            # Handle relative redirects
            if not redirect_url.startswith(("http://", "https://")):
                # Resolve relative URL
                from urllib.parse import urljoin
                redirect_url = urljoin(url, redirect_url)

            # Validate redirect target
            try:
                self.validator.validate(redirect_url)
            except SSRFBlockedError as e:
                raise SSRFBlockedError(
                    f"Redirect target blocked: {str(e)}"
                )

            # Follow redirect
            return await self._fetch_with_redirect_validation(
                client=client,
                url=redirect_url,
                headers=headers,
                redirect_count=redirect_count + 1,
                **kwargs
            )

        # Check response size
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    raise SSRFBlockedError(
                        f"Response exceeds maximum size limit "
                        f"({size} > {self.max_size} bytes)"
                    )
            except ValueError:
                pass  # Invalid content-length header, skip check

        return response

    async def post(
        self,
        url: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a POST request with SSRF protection.

        Args:
            url: The URL to post to.
            data: Form data to send.
            json: JSON data to send.
            headers: Optional headers.
            **kwargs: Additional arguments.

        Returns:
            httpx.Response object.

        Raises:
            SSRFBlockedError: If the URL fails validation.
            httpx.TimeoutException: If the request times out.
        """
        # Validate URL before making request
        self.validator.validate(url)

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=False,
        ) as client:
            response = await client.post(
                url,
                data=data,
                json=json,
                headers=headers,
                **kwargs
            )

            # Check response size
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.max_size:
                        raise SSRFBlockedError(
                            f"Response exceeds maximum size limit "
                            f"({size} > {self.max_size} bytes)"
                        )
                except ValueError:
                    pass

            return response
