"""
Password Hashing Module

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

This module provides password hashing and verification using bcrypt.

Security Features:
- Uses bcrypt algorithm (recommended for password storage)
- Automatic salt generation (unique per hash)
- Configurable work factor for future-proofing

Note: Using bcrypt directly instead of passlib to avoid compatibility
issues with Python 3.13 and newer bcrypt library versions.

References:
- bcrypt documentation: https://github.com/pyca/bcrypt
- OWASP Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
"""

import bcrypt


# Work factor for bcrypt (cost factor, default is 12)
# Higher values are more secure but slower
BCRYPT_WORK_FACTOR = 12


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Uses bcrypt with automatic salt generation. Each call produces
    a unique hash even for the same password (due to random salt).

    Args:
        plain_password: Plain text password to hash

    Returns:
        Bcrypt hash string (starts with $2b$ or $2a$)

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    # Convert to bytes
    password_bytes = plain_password.encode('utf-8')

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Performs constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        # Verify using bcrypt's constant-time comparison
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Return False for any error (e.g., invalid hash format)
        return False


__all__ = ['hash_password', 'verify_password']
