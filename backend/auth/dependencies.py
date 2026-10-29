"""
FastAPI Authentication Dependencies

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

This module provides FastAPI dependencies for authentication and authorization:
- get_current_user: Extract and validate user from JWT token
- get_current_active_user: Ensure user is active
- require_admin: Require admin role for endpoint access

Role-Based Access Control:
- user: read_products, create_calculation
- admin: all user permissions + manage_emission_factors, trigger_data_sync

Usage:
    @router.get("/protected")
    def protected_endpoint(user: User = Depends(get_current_user)):
        return {"username": user.username}

    @router.post("/admin-only")
    def admin_endpoint(user: User = Depends(require_admin)):
        return {"admin": user.username}
"""

from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.auth.jwt import decode_token, InvalidTokenError, TokenExpiredError
from backend.database.connection import get_db
from backend.models.user import User


# HTTP Bearer token security scheme
# auto_error=False allows us to return 401 instead of 403 for missing credentials
bearer_scheme = HTTPBearer(auto_error=False)


# Permission definitions for role-based access control
ROLE_PERMISSIONS = {
    "user": {
        "read_products",
        "create_calculation",
        "read_emission_factors",
        "read_calculations",
    },
    "admin": {
        # Admin inherits all user permissions
        "read_products",
        "create_calculation",
        "read_emission_factors",
        "read_calculations",
        # Admin-only permissions
        "manage_emission_factors",
        "trigger_data_sync",
        "manage_data_sources",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role (user, admin)
        permission: Permission to check

    Returns:
        True if role has permission, False otherwise

    Example:
        >>> has_permission("admin", "manage_emission_factors")
        True
        >>> has_permission("user", "manage_emission_factors")
        False
    """
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return permission in role_perms


def check_admin_permission(user_data: Dict[str, Any]) -> bool:
    """
    Check if user data represents an admin user.

    Args:
        user_data: Dictionary with user_id, username, role

    Returns:
        True if user is admin

    Raises:
        HTTPException: 403 if user is not admin
    """
    role = user_data.get("role", "")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return True


def get_current_user_from_token(
    token: str,
    db: Session,
) -> User:
    """
    Get user from database based on token claims.

    Validates the token, extracts user_id, and retrieves the user
    from the database. Ensures user exists and is active.

    Args:
        token: JWT token string
        db: Database session

    Returns:
        User object from database

    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    try:
        payload = decode_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency: Get current authenticated user.

    Extracts Bearer token from Authorization header, validates it,
    and returns the corresponding User object from the database.

    Args:
        credentials: HTTP Authorization credentials (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        User object for authenticated user

    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    # Check if credentials are provided
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate required claims
    user_id = payload.get("user_id")
    role = payload.get("role")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate role is present and valid
    if role is None or role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency: Optionally identify the current user.

    If a valid Bearer token is provided, returns the User for audit logging.
    If no token or an invalid token is provided, returns None (does not block).

    SEC-001: Adds audit capability to public GET endpoints without breaking
    unauthenticated access.
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
    except (TokenExpiredError, InvalidTokenError):
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        return None

    return db.query(User).filter(User.id == user_id).first()


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: Get current active user.

    Ensures the authenticated user's account is active.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object if active

    Raises:
        HTTPException: 401 if user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    FastAPI dependency: Require admin role.

    Use this dependency for admin-only endpoints.

    Args:
        current_user: Active user from get_current_active_user dependency

    Returns:
        User object if admin

    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return current_user


__all__ = [
    'bearer_scheme',
    'has_permission',
    'check_admin_permission',
    'get_current_user_from_token',
    'get_current_user',
    'get_optional_user',
    'get_current_active_user',
    'require_admin',
    'ROLE_PERMISSIONS',
]
