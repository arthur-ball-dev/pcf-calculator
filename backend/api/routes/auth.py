"""
Authentication API Routes

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

Endpoints:
- POST /api/v1/auth/login - Authenticate user and return JWT token
- POST /api/v1/auth/refresh - Refresh access token
- GET /api/v1/auth/me - Get current user info

Security Notes:
- Password comparison uses constant-time algorithm
- Tokens expire after 1 hour by default
- Rate limiting should be implemented at infrastructure level
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.jwt import (
    create_access_token,
    decode_token,
    InvalidTokenError,
    TokenExpiredError,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.auth.password import verify_password
from backend.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    bearer_scheme,
)
from backend.database.connection import get_db
from backend.models.user import User


# ============================================================================
# Request/Response Models
# ============================================================================


class LoginRequest(BaseModel):
    """Request model for login endpoint."""
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username for authentication"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Password for authentication"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "validpassword123"
            }
        }


class TokenResponse(BaseModel):
    """Response model for successful authentication."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class UserInfoResponse(BaseModel):
    """Response model for user info endpoint."""
    user_id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role (user or admin)")
    is_active: bool = Field(..., description="Account active status")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "abc123def456ghi789jkl012",
                "username": "testuser",
                "email": "testuser@example.com",
                "role": "user",
                "is_active": True
            }
        }


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
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
) -> TokenResponse:
    """
    Refresh access token.

    Returns a new access token for the authenticated user.
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

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


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
