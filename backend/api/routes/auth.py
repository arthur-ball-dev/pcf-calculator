"""
Authentication API Routes

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

Endpoints:
- POST /api/v1/auth/login - Authenticate user and return JWT token
- POST /api/v1/auth/refresh - Refresh access token
- POST /api/v1/auth/logout - Revoke the current token
- GET /api/v1/auth/me - Get current user info

Security Notes:
- Password comparison uses constant-time algorithm
- Tokens expire after 1 hour by default
- Rate limiting should be implemented at infrastructure level
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.schemas.auth import LoginRequest, TokenResponse, UserInfoResponse

from backend.auth.jwt import (
    create_access_token,
    decode_token,
    InvalidTokenError,
    TokenExpiredError,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.auth.password import verify_password
from backend.auth.revocation import revoke_token
from backend.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    bearer_scheme,
)
from backend.database.connection import get_db
from backend.models.user import User


# ============================================================================
# Router Configuration
# ============================================================================


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with username and password, returns JWT access token",
    responses={
        401: {"description": "Invalid username or password"},
        422: {"description": "Validation error (missing fields)"},
    },
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    Validates username and password against database. If valid, returns
    a JWT token that can be used for subsequent authenticated requests.

    Request Body:
    - username: User's username
    - password: User's password

    Returns:
    - access_token: JWT for authentication
    - token_type: "bearer"
    - expires_in: Token validity in seconds (3600 = 1 hour)

    Raises:
    - 401: Invalid username or password
    - 401: User account is inactive
    - 422: Validation error (missing required fields)
    """
    # Look up user by username
    user = db.query(User).filter(User.username == request.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }

    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using current valid token",
    responses={
        401: {"description": "Token expired or invalid"},
    },
)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token.

    Returns a new access token for the authenticated user and revokes the one
    presented, so only one token in a chain is live and logout ends the session.
    The current token must still be valid (not expired).

    Headers:
    - Authorization: Bearer <current_token>

    Returns:
    - access_token: New JWT for authentication
    - token_type: "bearer"
    - expires_in: Token validity in seconds

    Raises:
    - 401: Token expired or invalid
    """
    # Create new access token
    token_data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }

    access_token = create_access_token(data=token_data)
    revoke_token(db, decode_token(credentials.credentials))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    description="Revoke the current access token so it can no longer be used",
    responses={
        401: {"description": "Not authenticated, or token already revoked"},
    },
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Revoke the access token used for this request.

    Only this token is revoked: other sessions of the same user keep working.
    get_current_active_user has already rejected a missing, invalid, expired or
    revoked token, so the token here decodes cleanly.

    Raises:
    - 401: Not authenticated, or token already revoked
    """
    revoke_token(db, decode_token(credentials.credentials))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user info",
    description="Get information about the currently authenticated user",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserInfoResponse:
    """
    Get current authenticated user information.

    Returns user profile information for the authenticated user.

    Headers:
    - Authorization: Bearer <token>

    Returns:
    - user_id: User UUID
    - username: Username
    - email: Email address
    - role: User role (user or admin)
    - is_active: Account status

    Raises:
    - 401: Not authenticated or token invalid
    """
    return UserInfoResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
    )


__all__ = ['router']
