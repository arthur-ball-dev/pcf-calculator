"""
JWT Token Module

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

This module provides JWT token creation and validation using python-jose.

Security Features:
- HS256 algorithm for token signing
- Configurable token expiration
- Secret key from file (/etc/environment.txt) or environment variable
- Token payload includes user_id, username, and role
- No hardcoded defaults (P0 security fix)

JWT Specification:
- Algorithm: HS256
- Token Expiry: 1 hour (configurable)
- Required Claims: user_id, username, role, exp

References:
- python-jose: https://python-jose.readthedocs.io/
- JWT RFC 7519: https://datatracker.ietf.org/doc/html/rfc7519
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from jose import jwt, JWTError, ExpiredSignatureError

from backend.config import settings


# JWT Configuration
# P0 Security Fix: Secret key loaded from settings (file or env var, no hardcoded default)
JWT_SECRET_KEY = settings.PCF_CALC_JWT_SECRET_KEY

# Algorithm used for signing tokens
JWT_ALGORITHM = "HS256"

# Default token expiration (1 hour)
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60


class InvalidTokenError(Exception):
    """Raised when token validation fails (malformed, tampered, or invalid signature)."""

    def __init__(self, message: str = "Invalid token"):
        self.message = message
        super().__init__(self.message)


class TokenExpiredError(Exception):
    """Raised when token has expired."""

    def __init__(self, message: str = "Token has expired"):
        self.message = message
        super().__init__(self.message)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Creates a signed JWT containing the provided data plus an expiration claim.
    The token is signed using HS256 algorithm with the configured secret key.

    Args:
        data: Dictionary containing claims to include in token.
              Should include user_id, username, and role.
        expires_delta: Optional custom expiration time.
                      Defaults to DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string (header.payload.signature format)

    Example:
        >>> token = create_access_token(
        ...     data={"user_id": 1, "username": "john", "role": "user"}
        ... )
        >>> len(token.split("."))
        3
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta is None:
        expires_delta = timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire

    # Create and return encoded token
    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Verifies the token signature and expiration. Returns the decoded
    payload if valid, otherwise raises an appropriate exception.

    Args:
        token: JWT string to decode and validate

    Returns:
        Decoded token payload as dictionary

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is malformed, tampered, or has invalid signature

    Example:
        >>> token = create_access_token({"user_id": 1, "username": "john", "role": "user"})
        >>> payload = decode_token(token)
        >>> payload["username"]
        'john'
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return payload

    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")

    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


__all__ = [
    'create_access_token',
    'decode_token',
    'InvalidTokenError',
    'TokenExpiredError',
    'JWT_SECRET_KEY',
    'JWT_ALGORITHM',
    'DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES',
]
