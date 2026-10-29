"""
Authentication Module

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

This module provides authentication and authorization functionality:
- JWT token creation and validation
- Password hashing with bcrypt
- FastAPI dependencies for protected endpoints
- Role-based access control

Usage:
    from backend.auth import create_access_token, verify_password, get_current_user
"""

from backend.auth.jwt import (
    create_access_token,
    decode_token,
    InvalidTokenError,
    TokenExpiredError,
)
from backend.auth.password import (
    hash_password,
    verify_password,
)
from backend.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin,
    check_admin_permission,
    has_permission,
    get_current_user_from_token,
)

__all__ = [
    # JWT functions
    'create_access_token',
    'decode_token',
    'InvalidTokenError',
    'TokenExpiredError',
    # Password functions
    'hash_password',
    'verify_password',
    # Dependencies
    'get_current_user',
    'get_current_active_user',
    'require_admin',
    'check_admin_permission',
    'has_permission',
    'get_current_user_from_token',
]
