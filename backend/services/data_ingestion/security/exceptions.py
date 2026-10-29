"""
Security exceptions for SSRF prevention.

TASK-BE-P7-021: SSRF Prevention in Data Connectors

This module defines custom exceptions for SSRF (Server-Side Request Forgery)
prevention. These exceptions are raised when URL validation fails due to
security concerns.
"""


class SSRFBlockedError(Exception):
    """
    Exception raised when a URL is blocked due to SSRF prevention rules.

    This exception is raised in the following scenarios:
    - URL points to a private/internal IP address
    - URL points to localhost or loopback address
    - URL points to cloud metadata endpoints
    - URL domain is not in the allowlist
    - DNS resolution returns a private IP (DNS rebinding attack)
    - URL uses a blocked scheme (not HTTPS)
    - URL uses a non-standard port
    - Redirect target is blocked
    - Response exceeds maximum size limit
    - Too many redirects

    Attributes:
        message: Human-readable description of why the URL was blocked.
    """

    def __init__(self, message: str):
        """
        Initialize SSRFBlockedError with a descriptive message.

        Args:
            message: Description of why the URL was blocked.
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
