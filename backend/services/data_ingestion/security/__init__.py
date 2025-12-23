"""
Security module for SSRF prevention in data connectors.

TASK-BE-P7-021: SSRF Prevention in Data Connectors

This module provides security utilities for protecting data connectors
against Server-Side Request Forgery (SSRF) attacks.

Components:
- SSRFBlockedError: Exception raised when a URL is blocked.
- URLValidator: Validates URLs against SSRF rules.
- SafeHTTPClient: HTTP client with built-in SSRF protection.
- get_allowed_domains: Returns list of allowed domains.

Usage:
    from backend.services.data_ingestion.security import (
        URLValidator,
        SafeHTTPClient,
        SSRFBlockedError,
        get_allowed_domains,
    )

    # Create validator with allowed domains
    validator = URLValidator(allowed_domains=get_allowed_domains())

    # Create safe HTTP client
    client = SafeHTTPClient(
        validator=validator,
        timeout=30.0,
        max_size=10 * 1024 * 1024,  # 10MB
    )

    # Make secure requests
    try:
        response = await client.get("https://api.epa.gov/emission-factors")
    except SSRFBlockedError as e:
        print(f"URL blocked: {e}")
"""

from .exceptions import SSRFBlockedError
from .allowed_domains import (
    get_allowed_domains,
    add_allowed_domain,
    remove_allowed_domain,
    ALLOWED_DOMAINS,
)
from .url_validator import URLValidator
from .safe_http_client import SafeHTTPClient

__all__ = [
    # Exceptions
    "SSRFBlockedError",
    # Configuration
    "get_allowed_domains",
    "add_allowed_domain",
    "remove_allowed_domain",
    "ALLOWED_DOMAINS",
    # Core classes
    "URLValidator",
    "SafeHTTPClient",
]
