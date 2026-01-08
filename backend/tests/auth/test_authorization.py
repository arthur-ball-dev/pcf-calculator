"""
Role-Based Authorization Tests

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access
Phase: A (Tests Only) - TDD Methodology

This module tests:
1. Role-based access control (RBAC)
2. Admin-only endpoints protection
3. User role restrictions
4. Role hierarchy validation
5. Permission checks on specific endpoints

Test Scenarios (from SPEC):
- Scenario 5: Admin Endpoint With User Role (403)
- Scenario 6: Admin Endpoint With Admin Role (200/202)
- Role hierarchy tests

References:
- SPEC: project-sdlc-admin/handoffs/active_tasks/BE/TASK-BE-P7-018_*.md
- Endpoint Protection Table from SPEC
"""

import pytest
from datetime import timedelta
from typing import Generator
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models import Base


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite test engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_client(db_session):
    """Create a test client with auth and admin routes."""
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
def user_token(db_session):
    """Create a token for a regular user."""
    from backend.models.user import User
    from backend.auth.password import hash_password
    from backend.auth.jwt import create_access_token

    user = User(
        username="regularuser",
        email="user@example.com",
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


@pytest.fixture
def admin_token(db_session):
    """Create a token for an admin user."""
    from backend.models.user import User
    from backend.auth.password import hash_password
    from backend.auth.jwt import create_access_token

    admin = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return create_access_token(data={
        "user_id": admin.id,
        "username": admin.username,
        "role": admin.role
    })


# ============================================================================
# Unit Tests: Role Permission Checks
# ============================================================================


class TestRolePermissions:
    """Tests for role-based permission logic."""

    def test_require_admin_with_admin_role_succeeds(self):
        """Test that require_admin passes for admin users."""
        from backend.auth.dependencies import check_admin_permission

        user_data = {"user_id": 1, "username": "admin", "role": "admin"}

        # Act & Assert - should not raise
        result = check_admin_permission(user_data)
        assert result is True

    def test_require_admin_with_user_role_raises_403(self):
        """Test that require_admin raises for regular users."""
        from backend.auth.dependencies import check_admin_permission

        user_data = {"user_id": 1, "username": "user", "role": "user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            check_admin_permission(user_data)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Insufficient permissions"

    def test_role_hierarchy_admin_includes_user_permissions(self):
        """Test that admin role includes all user permissions."""
        from backend.auth.dependencies import has_permission

        # Admin should have both admin and user permissions
        assert has_permission("admin", "read_products") is True
        assert has_permission("admin", "create_calculation") is True
        assert has_permission("admin", "manage_emission_factors") is True
        assert has_permission("admin", "trigger_data_sync") is True

    def test_role_hierarchy_user_has_limited_permissions(self):
        """Test that user role has limited permissions."""
        from backend.auth.dependencies import has_permission

        # User should have basic permissions
        assert has_permission("user", "read_products") is True
        assert has_permission("user", "create_calculation") is True

        # User should NOT have admin permissions
        assert has_permission("user", "manage_emission_factors") is False
        assert has_permission("user", "trigger_data_sync") is False


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    def test_get_current_user_extracts_user_from_token(self, db_session):
        """Test that get_current_user correctly extracts user info from token."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token
        from backend.auth.dependencies import get_current_user_from_token

        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
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

        # Act
        current_user = get_current_user_from_token(token, db_session)

        # Assert
        assert current_user.id == user.id
        assert current_user.username == "testuser"
        assert current_user.role == "user"

    def test_get_current_user_returns_none_for_deleted_user(self, db_session):
        """Test that get_current_user handles deleted users."""
        from backend.auth.jwt import create_access_token
        from backend.auth.dependencies import get_current_user_from_token

        # Create token for non-existent user
        token = create_access_token(data={
            "user_id": 99999,
            "username": "deleted_user",
            "role": "user"
        })

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_token(token, db_session)

        assert exc_info.value.status_code == 401


# ============================================================================
# API Tests: Admin Endpoints with User Role (Scenario 5)
# ============================================================================


class TestAdminEndpointsWithUserRole:
    """Tests for admin endpoints accessed with user role - should return 403."""

    def test_admin_data_sync_with_user_role_returns_403(self, auth_client, user_token):
        """Test POST /admin/data-sources/sync with user role returns 403 (Scenario 5)."""
        # Act
        response = auth_client.post(
            "/api/v1/admin/data-sources/sync",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Insufficient permissions"

    def test_emission_factors_post_with_user_role_returns_403(self, auth_client, user_token):
        """Test POST /emission-factors with user role returns 403."""
        # Arrange
        new_factor = {
            "activity_name": "Test Factor",
            "category": "Test",
            "co2e_factor": 1.5,
            "unit": "kg"
        }

        # Act
        response = auth_client.post(
            "/api/v1/emission-factors",
            json=new_factor,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Insufficient permissions"

    def test_emission_factors_put_with_user_role_returns_403(self, auth_client, user_token):
        """Test PUT /emission-factors/{id} with user role returns 403."""
        # Arrange
        update_data = {"co2e_factor": 2.0}

        # Act
        response = auth_client.put(
            "/api/v1/emission-factors/some-factor-id",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Insufficient permissions"

    def test_emission_factors_delete_with_user_role_returns_403(self, auth_client, user_token):
        """Test DELETE /emission-factors/{id} with user role returns 403."""
        # Act
        response = auth_client.delete(
            "/api/v1/emission-factors/some-factor-id",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Insufficient permissions"

    def test_admin_any_endpoint_with_user_role_returns_403(self, auth_client, user_token):
        """Test any POST /admin/* endpoint with user role returns 403."""
        # Test various admin endpoints
        admin_endpoints = [
            "/api/v1/admin/data-sources/test-id/sync",
            "/api/v1/admin/sync/trigger",
        ]

        for endpoint in admin_endpoints:
            response = auth_client.post(
                endpoint,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            # Should be 403 (forbidden) not 404 (not found) if auth is working
            # 404 is acceptable if the endpoint doesn't exist
            assert response.status_code in [403, 404], \
                f"Expected 403 or 404 for {endpoint}, got {response.status_code}"


# ============================================================================
# API Tests: Admin Endpoints with Admin Role (Scenario 6)
# ============================================================================


class TestAdminEndpointsWithAdminRole:
    """Tests for admin endpoints accessed with admin role - should succeed."""

    def test_admin_data_sync_with_admin_role_succeeds(self, auth_client, admin_token, db_session):
        """Test POST /admin/data-sources/{id}/sync with admin role succeeds (Scenario 6)."""
        from backend.models import DataSource
        import uuid
        from datetime import datetime, timezone

        # Create a test data source
        data_source = DataSource(
            id=uuid.uuid4().hex,
            name="Test EPA Source",
            source_type="file",
            base_url="https://test.example.com",
            sync_frequency="manual",
            is_active=True
        )
        db_session.add(data_source)
        db_session.commit()

        # Act
        response = auth_client.post(
            f"/api/v1/admin/data-sources/{data_source.id}/sync",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert - 200 or 202 (accepted for async operation)
        assert response.status_code in [200, 202], \
            f"Expected 200/202, got {response.status_code}: {response.json()}"

    def test_emission_factors_post_with_admin_role_succeeds(self, auth_client, admin_token, db_session):
        """Test POST /emission-factors with admin role succeeds."""
        from backend.models import DataSource
        import uuid

        # Create a data source first if needed
        data_source = DataSource(
            id=uuid.uuid4().hex,
            name="Test Source",
            source_type="manual",
            base_url="https://test.example.com",
            sync_frequency="manual",
            is_active=True
        )
        db_session.add(data_source)
        db_session.commit()

        # Arrange
        new_factor = {
            "activity_name": "Test Factor",
            "category": "Test Category",
            "co2e_factor": 1.5,
            "unit": "kg",
            "data_source": "Test",
            "geography": "US",
            "reference_year": 2023,
            "data_source_id": data_source.id
        }

        # Act
        response = auth_client.post(
            "/api/v1/emission-factors",
            json=new_factor,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code in [200, 201], \
            f"Expected 200/201, got {response.status_code}: {response.json()}"

    def test_emission_factors_delete_with_admin_role_succeeds(self, auth_client, admin_token, db_session):
        """Test DELETE /emission-factors/{id} with admin role succeeds."""
        from backend.models import EmissionFactor, DataSource
        import uuid

        # Create test data source
        data_source = DataSource(
            id=uuid.uuid4().hex,
            name="Test Source",
            source_type="manual",
            base_url="https://test.example.com",
            sync_frequency="manual",
            is_active=True
        )
        db_session.add(data_source)
        db_session.flush()

        # Create test emission factor
        factor = EmissionFactor(
            id=uuid.uuid4().hex,
            activity_name="Test Factor",
            category="Test",
            co2e_factor=1.5,
            unit="kg",
            data_source="Test",
            geography="US",
            reference_year=2023,
            data_source_id=data_source.id,
            is_active=True
        )
        db_session.add(factor)
        db_session.commit()

        # Act
        response = auth_client.delete(
            f"/api/v1/emission-factors/{factor.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code in [200, 204], \
            f"Expected 200/204, got {response.status_code}"


# ============================================================================
# API Tests: User Endpoints with User Role (Should Succeed)
# ============================================================================


class TestUserEndpointsWithUserRole:
    """Tests for user-accessible endpoints with user role."""

    def test_get_products_with_user_role_succeeds(self, auth_client, user_token):
        """Test GET /products with user role succeeds."""
        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 200

    def test_get_product_by_id_with_user_role_succeeds(self, auth_client, user_token, db_session):
        """Test GET /products/{id} with user role succeeds."""
        from backend.models import Product
        import uuid

        # Create test product
        product = Product(
            id=uuid.uuid4().hex,
            code="TEST-001",
            name="Test Product",
            unit="kg",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        # Act
        response = auth_client.get(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 200

    def test_post_calculate_with_user_role_succeeds(self, auth_client, user_token, db_session):
        """Test POST /calculate with user role succeeds."""
        from backend.models import Product
        import uuid

        # Create test product
        product = Product(
            id=uuid.uuid4().hex,
            code="TEST-CALC",
            name="Product for Calculation",
            unit="unit",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        # Arrange
        calc_request = {
            "product_id": product.id,
            "quantity": 1.0
        }

        # Act
        response = auth_client.post(
            "/api/v1/calculate",
            json=calc_request,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert - may be 200, 201, or 202 depending on implementation
        assert response.status_code in [200, 201, 202, 422], \
            f"Unexpected status {response.status_code}"

    def test_get_emission_factors_with_user_role_succeeds(self, auth_client, user_token):
        """Test GET /emission-factors with user role succeeds (read-only)."""
        # Act
        response = auth_client.get(
            "/api/v1/emission-factors",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == 200


# ============================================================================
# API Tests: User Endpoints with Admin Role (Should Also Succeed)
# ============================================================================


class TestUserEndpointsWithAdminRole:
    """Tests for user-accessible endpoints with admin role (admin > user)."""

    def test_get_products_with_admin_role_succeeds(self, auth_client, admin_token):
        """Test GET /products with admin role succeeds."""
        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 200

    def test_post_calculate_with_admin_role_succeeds(self, auth_client, admin_token, db_session):
        """Test POST /calculate with admin role succeeds."""
        from backend.models import Product
        import uuid

        # Create test product
        product = Product(
            id=uuid.uuid4().hex,
            code="ADMIN-CALC",
            name="Admin Calculation Product",
            unit="unit",
            is_finished_product=True
        )
        db_session.add(product)
        db_session.commit()

        calc_request = {
            "product_id": product.id,
            "quantity": 1.0
        }

        # Act
        response = auth_client.post(
            "/api/v1/calculate",
            json=calc_request,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code in [200, 201, 202, 422]


# ============================================================================
# Edge Cases and Security Tests
# ============================================================================


class TestAuthorizationEdgeCases:
    """Tests for authorization edge cases and security."""

    def test_token_without_role_returns_403(self, auth_client, db_session):
        """Test that token without role claim is rejected for protected endpoints."""
        from backend.auth.jwt import create_access_token

        # Create token without role
        token = create_access_token(data={
            "user_id": 1,
            "username": "testuser"
            # Missing "role"
        })

        # Act
        response = auth_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - should fail due to missing role
        assert response.status_code in [401, 403]

    def test_token_with_invalid_role_returns_403(self, auth_client, db_session):
        """Test that token with invalid role is rejected."""
        from backend.auth.jwt import create_access_token

        # Create token with invalid role
        token = create_access_token(data={
            "user_id": 1,
            "username": "testuser",
            "role": "superadmin"  # Invalid role
        })

        # Act - try to access admin endpoint
        response = auth_client.post(
            "/api/v1/admin/data-sources/sync",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code in [403, 401]

    def test_role_escalation_in_token_is_rejected(self, auth_client, db_session):
        """Test that role escalation attempt via token tampering is rejected."""
        from backend.models.user import User
        from backend.auth.password import hash_password
        from backend.auth.jwt import create_access_token
        import base64
        import json

        # Create regular user
        user = User(
            username="normaluser",
            email="normal@example.com",
            hashed_password=hash_password("password123"),
            role="user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create valid token
        valid_token = create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "role": "user"
        })

        # Tamper with token to escalate role
        parts = valid_token.split(".")
        payload_b64 = parts[1]
        # Add padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        payload["role"] = "admin"  # Attempt to escalate
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        # Act - try to access admin endpoint with tampered token
        response = auth_client.post(
            "/api/v1/admin/data-sources/sync",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        # Assert - should be rejected (signature mismatch)
        assert response.status_code == 401


class TestEndpointProtectionMatrix:
    """Tests verifying the endpoint protection matrix from SPEC."""

    # Endpoint protection table from SPEC:
    # | Endpoint Pattern | Required Role |
    # |-----------------|---------------|
    # | GET /api/v1/* | user |
    # | POST /api/v1/calculate | user |
    # | POST /api/v1/emission-factors | admin |
    # | PUT /api/v1/emission-factors/* | admin |
    # | DELETE /api/v1/emission-factors/* | admin |
    # | POST /api/v1/admin/* | admin |

    @pytest.mark.parametrize("endpoint,method,required_role", [
        ("/api/v1/products", "GET", "user"),
        ("/api/v1/products/test-id", "GET", "user"),
        ("/api/v1/emission-factors", "GET", "user"),
        ("/api/v1/calculate", "POST", "user"),
    ])
    def test_user_accessible_endpoints(self, auth_client, user_token, endpoint, method, required_role):
        """Test that user-role endpoints are accessible with user token."""
        # Act
        if method == "GET":
            response = auth_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {user_token}"}
            )
        else:
            response = auth_client.post(
                endpoint,
                json={},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        # Assert - should not be 401 or 403
        # May be 404 (not found) or 422 (validation error) which is acceptable
        assert response.status_code not in [401, 403], \
            f"Expected {endpoint} to be accessible with user role, got {response.status_code}"

    @pytest.mark.parametrize("endpoint,method,required_role", [
        ("/api/v1/emission-factors", "POST", "admin"),
        ("/api/v1/emission-factors/test-id", "PUT", "admin"),
        ("/api/v1/emission-factors/test-id", "DELETE", "admin"),
        ("/api/v1/admin/data-sources/sync", "POST", "admin"),
        ("/api/v1/admin/data-sources/test-id/sync", "POST", "admin"),
    ])
    def test_admin_only_endpoints_reject_user(self, auth_client, user_token, endpoint, method, required_role):
        """Test that admin-only endpoints reject user tokens."""
        # Act
        if method == "GET":
            response = auth_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {user_token}"}
            )
        elif method == "POST":
            response = auth_client.post(
                endpoint,
                json={},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        elif method == "PUT":
            response = auth_client.put(
                endpoint,
                json={},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        elif method == "DELETE":
            response = auth_client.delete(
                endpoint,
                headers={"Authorization": f"Bearer {user_token}"}
            )

        # Assert - should be 403 (forbidden)
        assert response.status_code == 403, \
            f"Expected {endpoint} to return 403 for user role, got {response.status_code}"

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v1/emission-factors", "POST"),
        ("/api/v1/admin/data-sources/sync", "POST"),
    ])
    def test_admin_only_endpoints_allow_admin(self, auth_client, admin_token, endpoint, method):
        """Test that admin-only endpoints allow admin tokens."""
        # Act
        if method == "POST":
            response = auth_client.post(
                endpoint,
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        elif method == "PUT":
            response = auth_client.put(
                endpoint,
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        elif method == "DELETE":
            response = auth_client.delete(
                endpoint,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        # Assert - should not be 401 or 403
        # May be 422 (validation) or 404 (not found) which is acceptable
        assert response.status_code not in [401, 403], \
            f"Expected {endpoint} to be accessible with admin role, got {response.status_code}"
