"""
Security middleware for PCF Calculator Backend
Implements security headers following OWASP best practices
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses

    Headers added:
    - X-Content-Type-Options: nosniff - Prevents MIME type sniffing
    - X-Frame-Options: DENY - Prevents clickjacking attacks
    - X-XSS-Protection: 1; mode=block - Enables XSS filter in browsers
    - Strict-Transport-Security - Enforces HTTPS connections

    Reference: https://owasp.org/www-project-secure-headers/
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response: HTTP response with security headers added
        """
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by denying iframe embedding
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS connections (1 year max-age)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
