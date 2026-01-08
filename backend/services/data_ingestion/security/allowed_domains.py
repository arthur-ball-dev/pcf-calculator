"""
Allowed domains configuration for SSRF prevention.

TASK-BE-P7-021: SSRF Prevention in Data Connectors

This module defines the allowlist of domains that data connectors are permitted
to access. Only URLs pointing to these domains will be allowed through the
SSRF protection layer.

The allowlist approach is the recommended security practice for SSRF prevention
as it provides a positive security model - only explicitly allowed targets can
be accessed, rather than trying to block all possible malicious targets.
"""

from typing import List

# Allowed domains for emission factor data sources
# These are the trusted data sources for PCF Calculator
ALLOWED_DOMAINS: List[str] = [
    # EPA (US Environmental Protection Agency)
    "api.epa.gov",
    "www.epa.gov",

    # DEFRA (UK Department for Environment, Food & Rural Affairs)
    "api.defra.gov.uk",
    "naei.beis.gov.uk",

    # Ecoinvent (Life Cycle Inventory Database)
    "ecoquery.ecoinvent.org",
    "v391.ecoquery.ecoinvent.org",
]


def get_allowed_domains() -> List[str]:
    """
    Get list of allowed domains for data fetching.

    Returns a copy of the allowed domains list to prevent modification
    of the original list.

    Returns:
        List of domain strings that are allowed for data fetching.

    Example:
        >>> domains = get_allowed_domains()
        >>> "api.epa.gov" in domains
        True
    """
    return ALLOWED_DOMAINS.copy()


def add_allowed_domain(domain: str) -> None:
    """
    Add a domain to the allowlist.

    This should be used sparingly and only during development or testing.
    In production, the allowlist should be managed through configuration.

    Args:
        domain: The domain to add to the allowlist.

    Example:
        >>> add_allowed_domain("api.example.com")
        >>> "api.example.com" in get_allowed_domains()
        True
    """
    if domain not in ALLOWED_DOMAINS:
        ALLOWED_DOMAINS.append(domain)


def remove_allowed_domain(domain: str) -> bool:
    """
    Remove a domain from the allowlist.

    Args:
        domain: The domain to remove from the allowlist.

    Returns:
        True if the domain was removed, False if it wasn't in the list.

    Example:
        >>> remove_allowed_domain("api.example.com")
        True
    """
    if domain in ALLOWED_DOMAINS:
        ALLOWED_DOMAINS.remove(domain)
        return True
    return False
