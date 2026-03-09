"""
JWT Authentication Tests

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access
Phase: A (Tests Only) - TDD Methodology

This module tests:
1. JWT token generation
2. JWT token validation
3. Token expiration handling
4. Login/logout endpoints
5. Password hashing verification
6. Token refresh mechanism

Test Scenarios (from SPEC):
- Scenario 1: Successful Login
- Scenario 2: Invalid Credentials
- Scenario 3: Protected Endpoint Without Token
- Scenario 4: Protected Endpoint With Valid Token
- Scenario 7: Expired Token

References:
- SPEC: project-sdlc-admin/handoffs/active_tasks/BE/TASK-BE-P7-018_*.md
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Unit Tests: JWT Token Generation
# ============================================================================


class TestJWTTokenGeneration:
    """Tests for JWT token creation and structure."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string."""
        # Arrange
        from backend.auth.jwt import create_access_token

        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }

        # Act
        token = create_access_token(data=user_data)

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature (3 parts)
        assert len(token.split(".")) == 3

    def test_create_access_token_includes_user_data(self):
        """Test that token payload includes user data."""
        from backend.auth.jwt import create_access_token, decode_token

        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "admin"
        }

        # Act
        token = create_access_token(data=user_data)
        decoded = decode_token(token)

        # Assert
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "admin"

    def test_create_access_token_has_expiration(self):
        """Test that token includes expiration claim."""
        from backend.auth.jwt import create_access_token, decode_token

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}

        # Act
        token = create_access_token(data=user_data)
        decoded = decode_token(token)

        # Assert
        assert "exp" in decoded
        # Expiration should be in the future
        exp_timestamp = decoded["exp"]
        now_timestamp = datetime.now(timezone.utc).timestamp()
        assert exp_timestamp > now_timestamp

    def test_create_access_token_with_custom_expiry(self):
        """Test that custom expiration time is honored."""
        from backend.auth.jwt import create_access_token, decode_token

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}
        custom_expiry = timedelta(minutes=30)

        # Act
        token = create_access_token(data=user_data, expires_delta=custom_expiry)
        decoded = decode_token(token)

        # Assert
        exp_timestamp = decoded["exp"]
        expected_exp = datetime.now(timezone.utc) + custom_expiry
        # Allow 5 seconds tolerance
        assert abs(exp_timestamp - expected_exp.timestamp()) < 5

    def test_create_access_token_uses_hs256_algorithm(self):
        """Test that token uses HS256 algorithm."""
        import json
        import base64
        from backend.auth.jwt import create_access_token

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}

        # Act
        token = create_access_token(data=user_data)

        # Decode header (first part of JWT)
        header_b64 = token.split(".")[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))

        # Assert
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"


class TestJWTTokenValidation:
    """Tests for JWT token validation and decoding."""

    def test_decode_valid_token_succeeds(self):
        """Test that a valid token can be decoded."""
        from backend.auth.jwt import create_access_token, decode_token

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}
        token = create_access_token(data=user_data)

        # Act
        decoded = decode_token(token)

        # Assert
        assert decoded is not None
        assert decoded["user_id"] == 1

    def test_decode_invalid_token_raises_error(self):
        """Test that an invalid token raises an exception."""
        from backend.auth.jwt import decode_token, InvalidTokenError

        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            decode_token(invalid_token)

    def test_decode_malformed_token_raises_error(self):
        """Test that a malformed token raises an exception."""
        from backend.auth.jwt import decode_token, InvalidTokenError

        malformed_token = "not-a-jwt-at-all"

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            decode_token(malformed_token)

    def test_decode_tampered_token_raises_error(self):
        """Test that a token with tampered payload raises an exception."""
        from backend.auth.jwt import create_access_token, decode_token, InvalidTokenError
        import base64
        import json

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}
        token = create_access_token(data=user_data)

        # Tamper with payload
        parts = token.split(".")
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        payload["role"] = "admin"  # Attempt to elevate privileges
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            decode_token(tampered_token)

    def test_decode_wrong_secret_raises_error(self):
        """Test that a token signed with wrong secret raises an exception."""
        from jose import jwt
        from backend.auth.jwt import decode_token, InvalidTokenError

        # Create token with wrong secret
        payload = {
            "user_id": 1,
            "username": "testuser",
            "role": "user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        wrong_secret_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            decode_token(wrong_secret_token)


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_expired_token_raises_error(self):
        """Test that an expired token raises TokenExpiredError (Scenario 7)."""
        from backend.auth.jwt import create_access_token, decode_token, TokenExpiredError

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}
        # Create token that expires immediately
        expired_delta = timedelta(seconds=-10)  # Expired 10 seconds ago
        token = create_access_token(data=user_data, expires_delta=expired_delta)

        # Act & Assert
        with pytest.raises(TokenExpiredError) as exc_info:
            decode_token(token)

        assert "expired" in str(exc_info.value).lower()

    def test_token_just_before_expiry_is_valid(self):
        """Test that a token just before expiry is still valid."""
        from backend.auth.jwt import create_access_token, decode_token

        user_data = {"user_id": 1, "username": "testuser", "role": "user"}
        # Create token that expires in 5 seconds
        almost_expired_delta = timedelta(seconds=5)
        token = create_access_token(data=user_data, expires_delta=almost_expired_delta)

        # Act
        decoded = decode_token(token)

        # Assert
        assert decoded["user_id"] == 1


# ============================================================================
# Unit Tests: Password Hashing
# ============================================================================


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_different_value(self):
        """Test that hashing returns a different value than plain text."""
        from backend.auth.password import hash_password

        plain_password = "securepassword123"

        # Act
        hashed = hash_password(plain_password)

        # Assert
        assert hashed != plain_password
        assert len(hashed) > len(plain_password)

    def test_verify_password_with_correct_password(self):
        """Test that correct password verification succeeds."""
        from backend.auth.password import hash_password, verify_password

        plain_password = "securepassword123"
        hashed = hash_password(plain_password)

        # Act
        result = verify_password(plain_password, hashed)

        # Assert
        assert result is True

    def test_verify_password_with_incorrect_password(self):
        """Test that incorrect password verification fails."""
        from backend.auth.password import hash_password, verify_password

        plain_password = "securepassword123"
        wrong_password = "wrongpassword456"
        hashed = hash_password(plain_password)

        # Act
        result = verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    def test_hash_password_produces_unique_hashes(self):
        """Test that same password produces different hashes (salting)."""
        from backend.auth.password import hash_password

        plain_password = "securepassword123"

        # Act
        hash1 = hash_password(plain_password)
        hash2 = hash_password(plain_password)

        # Assert
        assert hash1 != hash2  # bcrypt adds salt, so hashes should differ

    def test_hash_password_uses_bcrypt(self):
        """Test that bcrypt algorithm is used."""
        from backend.auth.password import hash_password

        plain_password = "securepassword123"

        # Act
        hashed = hash_password(plain_password)

        # Assert - bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


# ============================================================================
# API Tests: Login Endpoint
# ============================================================================


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    @pytest.fixture
    def auth_client(self, db_session):
        """Create a test client with auth routes."""
        from backend.main import app
        from backend.database.connection import get_db

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user in the database."""
        from backend.models.user import User
        from backend.auth.password import hash_password

        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("validpassword123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_login_success_returns_token(self, auth_client, test_user):
        """Test successful login returns access token (Scenario 1)."""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": "validpassword123"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_login_success_token_is_valid_jwt(self, auth_client, test_user):
        """Test that returned token is a valid JWT."""
        from backend.auth.jwt import decode_token

        login_data = {
            "username": "testuser",
            "password": "validpassword123"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)
        token = response.json()["access_token"]

        # Assert
        decoded = decode_token(token)
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"

    def test_login_invalid_username_returns_401(self, auth_client, test_user):
        """Test login with invalid username returns 401 (Scenario 2)."""
        # Arrange
        login_data = {
            "username": "nonexistent",
            "password": "validpassword123"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid username or password"

    def test_login_invalid_password_returns_401(self, auth_client, test_user):
        """Test login with invalid password returns 401 (Scenario 2)."""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid username or password"

    def test_login_inactive_user_returns_401(self, auth_client, db_session):
        """Test login with inactive user returns 401."""
        from backend.models.user import User
        from backend.auth.password import hash_password

        # Create inactive user
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=hash_password("password123"),
            role="user",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        login_data = {
            "username": "inactive",
            "password": "password123"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "inactive" in data["detail"].lower() or "invalid" in data["detail"].lower()

    def test_login_missing_fields_returns_422(self, auth_client):
        """Test login with missing fields returns 422."""
        # Arrange - missing password
        login_data = {"username": "testuser"}

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422


class TestTokenRefresh:
    """Tests for token refresh mechanism."""

    @pytest.fixture
    def auth_client(self, db_session):
        """Create a test client with auth routes."""
        from backend.main import app
        from backend.database.connection import get_db

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def test_user_with_token(self, db_session):
        """Create a test user and return with valid token."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token

        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("validpassword123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        })

        return user, token

    def test_refresh_token_returns_new_token(self, auth_client, test_user_with_token):
        """Test that refresh endpoint returns a new token."""
        user, token = test_user_with_token

        # Act
        response = auth_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != token  # New token should be different

    def test_refresh_with_expired_token_returns_401(self, auth_client, db_session):
        """Test that refresh with expired token returns 401."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token

        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("validpassword123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        expired_token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            },
            expires_delta=timedelta(seconds=-10)  # Already expired
        )

        # Act
        response = auth_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401


# ============================================================================
# API Tests: Protected Endpoints
# ============================================================================


class TestProtectedEndpoints:
    """Tests for protected endpoint behavior."""

    @pytest.fixture
    def auth_client(self, db_session):
        """Create a test client with auth routes."""
        from backend.main import app
        from backend.database.connection import get_db

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def valid_user_token(self, db_session):
        """Create a valid user token."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token

        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("password123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        })

    def test_protected_endpoint_without_token_returns_401(self, auth_client):
        """Test protected endpoint without token returns 401 (Scenario 3)."""
        # Act
        response = auth_client.get("/api/v1/products")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_protected_endpoint_with_valid_token_succeeds(self, auth_client, valid_user_token):
        """Test protected endpoint with valid token succeeds (Scenario 4)."""
        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {valid_user_token}"}
        )

        # Assert
        assert response.status_code == 200

    def test_protected_endpoint_with_expired_token_returns_401(self, auth_client, db_session):
        """Test protected endpoint with expired token returns 401 (Scenario 7)."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token

        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("password123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        expired_token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            },
            expires_delta=timedelta(seconds=-10)  # Already expired
        )

        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Token has expired"

    def test_protected_endpoint_with_invalid_token_format_returns_401(self, auth_client):
        """Test protected endpoint with malformed token returns 401."""
        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": "Bearer invalid-token-format"}
        )

        # Assert
        assert response.status_code == 401

    def test_protected_endpoint_with_wrong_auth_scheme_returns_401(self, auth_client, valid_user_token):
        """Test protected endpoint with wrong auth scheme returns 401."""
        # Act - Using Basic instead of Bearer
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Basic {valid_user_token}"}
        )

        # Assert
        assert response.status_code == 401


# ============================================================================
# Configuration Tests
# ============================================================================


class TestJWTConfiguration:
    """Tests for JWT configuration from environment."""

    def test_jwt_secret_not_hardcoded(self):
        """Test that JWT secret is loaded from environment, not hardcoded."""
        import os
        from backend.config import settings

        # P0 Security Fix: Secret must come from file or environment variable
        # The attribute is now PCF_CALC_JWT_SECRET_KEY (not JWT_SECRET_KEY)
        assert hasattr(settings, 'PCF_CALC_JWT_SECRET_KEY')
        # Verify it's not the old hardcoded default
        assert settings.PCF_CALC_JWT_SECRET_KEY != "dev-secret-key-change-in-production-must-be-at-least-32-chars"

    def test_jwt_expiry_is_configurable(self):
        """Test that JWT expiry time is configurable."""
        from backend.config import settings

        # Should have configurable access token expiry
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES') or \
               hasattr(settings, 'JWT_EXPIRY_MINUTES')


# ============================================================================
# CORS with Auth Headers Tests
# ============================================================================


class TestCORSWithAuth:
    """Tests for CORS preflight with auth headers."""

    @pytest.fixture
    def client(self, db_session):
        """Create a test client."""
        from backend.main import app
        from backend.database.connection import get_db

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_cors_allows_authorization_header(self, client):
        """Test that CORS allows Authorization header in preflight."""
        # Act - Simulate preflight request
        response = client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization, content-type"
            }
        )

        # Assert
        assert response.status_code == 200
        # Authorization header should be in allowed headers
        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        assert "authorization" in allowed_headers

    def test_cors_includes_auth_headers_in_expose(self, client):
        """Test that CORS exposes WWW-Authenticate header if needed."""
        # This is a configuration test
        from backend.main import app

        # Check that ExtendedCORSMiddleware is configured
        middleware_configured = False
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and 'CORS' in str(middleware.cls):
                middleware_configured = True
                break

        assert middleware_configured
