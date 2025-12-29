"""
Test suite for CORS middleware functionality.

TASK-BE-P7-033: Restrict CORS Configuration
Following TDD methodology - tests for CORS middleware behavior.

This test suite verifies that CORS middleware correctly handles:
1. Allowed HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
2. Allowed headers (Authorization, Content-Type, X-Request-ID, Accept)
3. CORS preflight requests (OPTIONS method)

Reference:
- Code Review Report 2025-12-18 (Issue #6)
- Security requirement: No wildcard methods or headers

Test Classes (27 tests total):
- TestAllowedHttpMethods: 7 tests for HTTP method validation
- TestAllowedHeaders: 7 tests for header validation
- TestCorsPreflightRequests: 7 tests for preflight behavior
- TestActualCorsRequests: 3 tests for non-preflight requests
- TestCorsSecurityValidation: 3 tests for security requirements
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Fixture for TestClient
# ============================================================================


@pytest.fixture
def cors_client():
    """
    Create a TestClient for CORS testing.

    This fixture provides a clean TestClient instance without database
    overrides, suitable for testing middleware behavior directly.
    """
    from backend.main import app
    return TestClient(app)


# ============================================================================
# Test Suite 1: Allowed HTTP Methods
# ============================================================================


class TestAllowedHttpMethods:
    """Test suite verifying allowed HTTP methods work with CORS."""

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
    def test_allowed_method_in_preflight_response(self, cors_client, method: str):
        """
        Verify allowed HTTP methods are returned in CORS preflight response.

        The Access-Control-Allow-Methods header should include the method
        when it is in the configured allow list.

        Args:
            cors_client: TestClient instance
            method: HTTP method to test
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": method,
            }
        )

        # Preflight should succeed
        assert response.status_code == 200, (
            f"Preflight for {method} should return 200, got {response.status_code}"
        )

        # Method should be in allowed methods
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert method in allowed_methods, (
            f"Method {method} should be in Access-Control-Allow-Methods. "
            f"Got: {allowed_methods}"
        )

    def test_options_method_works_for_preflight(self, cors_client):
        """
        Verify OPTIONS method works for CORS preflight requests.

        The OPTIONS method is essential for CORS preflight to function.
        Browsers send OPTIONS before actual requests to check CORS policy.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert response.status_code == 200, (
            f"OPTIONS preflight should return 200, got {response.status_code}"
        )

        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers

    def test_all_allowed_methods_present_in_response(self, cors_client):
        """
        Verify all allowed methods (GET, POST, PUT, DELETE, OPTIONS) are
        present in the CORS response header.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")

        # All standard methods should be allowed
        expected_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        for method in expected_methods:
            assert method in allowed_methods, (
                f"Expected {method} in allowed methods. Got: {allowed_methods}"
            )

    def test_no_wildcard_in_methods(self, cors_client):
        """
        Verify Access-Control-Allow-Methods does not contain wildcard.

        Security requirement: Methods should be explicitly listed, not '*'.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "*" not in allowed_methods, (
            f"Methods should not be wildcard. Got: {allowed_methods}"
        )


# ============================================================================
# Test Suite 2: Allowed Headers
# ============================================================================


class TestAllowedHeaders:
    """Test suite verifying allowed headers work with CORS."""

    @pytest.mark.parametrize("header", [
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "Accept"
    ])
    def test_allowed_header_in_preflight_response(self, cors_client, header: str):
        """
        Verify required headers are allowed in CORS preflight.

        These headers are needed by the frontend:
        - Authorization: For JWT auth tokens
        - Content-Type: For JSON request bodies
        - X-Request-ID: For request tracing
        - Accept: Standard content negotiation

        Args:
            cors_client: TestClient instance
            header: Header name to test
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": header,
            }
        )

        # Preflight should succeed
        assert response.status_code == 200, (
            f"Preflight with header {header} should return 200, "
            f"got {response.status_code}"
        )

        # Header should be in allowed headers (case-insensitive comparison)
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert header.lower() in allowed_headers, (
            f"Header '{header}' should be in Access-Control-Allow-Headers. "
            f"Got: {allowed_headers}"
        )

    def test_authorization_header_allowed(self, cors_client):
        """
        Verify Authorization header is explicitly allowed.

        The Authorization header is required for JWT authentication.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            }
        )

        assert response.status_code == 200
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "authorization" in allowed_headers

    def test_content_type_header_allowed(self, cors_client):
        """
        Verify Content-Type header is explicitly allowed.

        The Content-Type header is required for JSON request bodies.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )

        assert response.status_code == 200
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "content-type" in allowed_headers

    def test_multiple_headers_allowed_together(self, cors_client):
        """
        Verify multiple headers can be requested in single preflight.

        Browsers may request multiple headers in one preflight request.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type, Accept",
            }
        )

        assert response.status_code == 200
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()

        # All three headers should be allowed
        assert "authorization" in allowed_headers
        assert "content-type" in allowed_headers
        assert "accept" in allowed_headers


# ============================================================================
# Test Suite 3: CORS Preflight Requests
# ============================================================================


class TestCorsPreflightRequests:
    """Test suite verifying CORS preflight requests work correctly."""

    def test_preflight_returns_200(self, cors_client):
        """
        Verify preflight request returns 200 OK status.

        A successful preflight response should return HTTP 200.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert response.status_code == 200

    def test_preflight_includes_allow_origin(self, cors_client):
        """
        Verify preflight response includes Access-Control-Allow-Origin.

        This header tells the browser which origins are allowed.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert "Access-Control-Allow-Origin" in response.headers
        # With credentials, origin should be echoed back (not wildcard)
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"

    def test_preflight_includes_allow_methods(self, cors_client):
        """
        Verify preflight response includes Access-Control-Allow-Methods.

        This header lists the HTTP methods allowed for CORS requests.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            }
        )

        assert "Access-Control-Allow-Methods" in response.headers
        allowed_methods = response.headers["Access-Control-Allow-Methods"]
        assert len(allowed_methods) > 0

    def test_preflight_includes_allow_headers(self, cors_client):
        """
        Verify preflight response includes Access-Control-Allow-Headers.

        This header lists the request headers allowed for CORS requests.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )

        assert "Access-Control-Allow-Headers" in response.headers

    def test_preflight_includes_allow_credentials(self, cors_client):
        """
        Verify preflight response includes Access-Control-Allow-Credentials.

        This header allows cookies and authorization headers in CORS requests.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert "Access-Control-Allow-Credentials" in response.headers
        assert response.headers["Access-Control-Allow-Credentials"] == "true"

    def test_preflight_for_different_endpoints(self, cors_client):
        """
        Verify preflight works for various API endpoints.

        CORS preflight should work consistently across all API endpoints.
        """
        endpoints = [
            "/api/v1/products",
            "/api/v1/calculations",
            "/api/v1/emission-factors",
            "/health",
        ]

        for endpoint in endpoints:
            response = cors_client.options(
                endpoint,
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                }
            )

            assert response.status_code == 200, (
                f"Preflight for {endpoint} should return 200, "
                f"got {response.status_code}"
            )

    def test_preflight_with_post_method_and_json_headers(self, cors_client):
        """
        Verify preflight for typical POST request with JSON body.

        This simulates a browser preflight before sending a JSON POST request.
        """
        response = cors_client.options(
            "/api/v1/calculate",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            }
        )

        assert response.status_code == 200

        # POST should be allowed
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "POST" in allowed_methods

        # Both headers should be allowed
        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()
        assert "content-type" in allowed_headers
        assert "authorization" in allowed_headers


# ============================================================================
# Test Suite 4: Actual CORS Requests (Non-Preflight)
# ============================================================================


class TestActualCorsRequests:
    """Test suite verifying actual CORS requests (not preflight) work."""

    def test_get_request_includes_cors_headers(self, cors_client):
        """
        Verify GET request response includes CORS headers.

        After preflight, actual requests should also include CORS headers.
        """
        response = cors_client.get(
            "/api/v1/products",
            headers={"Origin": "http://localhost:5173"}
        )

        # Request should succeed (200 for list endpoint)
        assert response.status_code == 200

        # CORS headers should be present
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_headers_on_error_responses(self, cors_client):
        """
        Verify CORS headers are present on error responses.

        Even when API returns an error, CORS headers must be present
        so the browser allows the frontend to read the error message.
        """
        response = cors_client.get(
            "/api/v1/products/nonexistent-product-id-12345",
            headers={"Origin": "http://localhost:5173"}
        )

        # May return 404 (not found)
        # CORS headers should still be present
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"

    def test_post_request_includes_cors_headers(self, cors_client):
        """
        Verify POST request response includes CORS headers.
        """
        response = cors_client.post(
            "/api/v1/calculate",
            headers={
                "Origin": "http://localhost:5173",
                "Content-Type": "application/json",
            },
            json={"product_id": "test-product-id"}  # May be invalid
        )

        # CORS headers should be present regardless of validation status
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


# ============================================================================
# Test Suite 5: Security Validation
# ============================================================================


class TestCorsSecurityValidation:
    """Test suite for CORS security requirements."""

    def test_unknown_origin_not_allowed(self, cors_client):
        """
        Verify unknown origins are not echoed back in CORS response.

        Security: Only configured origins should receive CORS headers.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://malicious-site.com",
                "Access-Control-Request-Method": "GET",
            }
        )

        # Origin should NOT be echoed back for unknown origins
        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        assert allow_origin != "http://malicious-site.com", (
            f"Unknown origin should not be allowed. Got: {allow_origin}"
        )

    def test_arbitrary_headers_not_allowed(self, cors_client):
        """
        Verify arbitrary headers are not allowed.

        Security: Only configured headers should be in the allow list.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Dangerous-Custom-Header",
            }
        )

        allowed_headers = response.headers.get(
            "Access-Control-Allow-Headers", ""
        ).lower()

        # Arbitrary headers should NOT be included
        assert "x-dangerous-custom-header" not in allowed_headers, (
            f"Arbitrary headers should not be allowed. Got: {allowed_headers}"
        )

    def test_patch_method_not_in_allowed_methods(self, cors_client):
        """
        Verify PATCH method is not in allowed methods list.

        PATCH is not used by the frontend and should not be allowed.
        """
        response = cors_client.options(
            "/api/v1/products",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "PATCH" not in allowed_methods, (
            f"PATCH should not be in allowed methods. Got: {allowed_methods}"
        )
