"""
Authentication API schemas (issue #20: the last request/response models that
lived inline in a route module).
"""

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Request model for the login endpoint."""
    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "testuser", "password": "validpassword123"}}
    )

    username: str = Field(..., min_length=1, max_length=50, description="Username for authentication")
    password: str = Field(..., min_length=1, description="Password for authentication")


class TokenResponse(BaseModel):
    """Response model for successful authentication."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    )

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class UserInfoResponse(BaseModel):
    """Response model for the current-user endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "abc123def456ghi789jkl012",
                "username": "testuser",
                "email": "testuser@example.com",
                "role": "user",
                "is_active": True,
            }
        }
    )

    user_id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role (user or admin)")
    is_active: bool = Field(..., description="Account active status")


__all__ = ["LoginRequest", "TokenResponse", "UserInfoResponse"]
