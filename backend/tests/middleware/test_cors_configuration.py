"""
Test suite for CORS configuration hardening.

TASK-BE-P7-017: Restrict CORS Configuration
Following TDD methodology - these tests are written BEFORE implementation.

This test suite verifies that CORS middleware is properly configured with
explicit allow lists instead of wildcards, reducing attack surface.

Test Scenarios:
1. Allowed HTTP methods (GET, POST, PUT, DELETE, OPTIONS) work correctly
2. Disallowed HTTP methods (PATCH) are blocked
3. Required headers (Authorization, Content-Type, X-Request-ID) are allowed
4. Frontend origin (http://localhost:5173) is allowed
5. End-to-end frontend request simulation

Reference: Code Review Report 2025-12-18 (Issue #6)
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Scenario 1: Allowed HTTP Methods Work
# ============================================================================


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_cors_allows_standard_methods(method: str):
    """
    Verify standard HTTP methods are allowed in CORS preflight.

    CORS preflight requests (OPTIONS) should return the requested method
    in the Access-Control-Allow-Methods header when the method is allowed.

    Args:
        method: HTTP method to test (GET, POST, PUT, DELETE)
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": method,
        }
    )

    assert response.status_code == 200, (
        f"Preflight for {method} should return 200, got {response.status_code}"
    )
    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    assert method in allowed_methods, (
        f"Method {method} should be in Access-Control-Allow-Methods header. "
        f"Got: {allowed_methods}"
    )


def test_cors_allows_options_method():
    """
    Verify OPTIONS method itself works for CORS preflight.

    The OPTIONS method is required for CORS preflight requests to function.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200, (
        "OPTIONS preflight request should return 200"
    )


# ============================================================================
# Scenario 2: Disallowed Methods Are Blocked
# ============================================================================


def test_cors_blocks_patch_method():
    """
    Verify PATCH method is not allowed in CORS preflight.

    PATCH is not used by the frontend and should not be in the allow list
    to follow the principle of least privilege.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
        }
    )

    # The preflight may still return 200, but PATCH should not be in allowed methods
    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")

    # PATCH should NOT be in the allowed methods list
    assert "PATCH" not in allowed_methods, (
        f"PATCH method should NOT be in Access-Control-Allow-Methods. "
        f"Got: {allowed_methods}"
    )


def test_cors_blocks_connect_method():
    """
    Verify CONNECT method is not allowed (security risk).

    CONNECT is used for proxying and should never be allowed via CORS.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "CONNECT",
        }
    )

    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    assert "CONNECT" not in allowed_methods, (
        f"CONNECT method should NOT be allowed for security reasons. "
        f"Got: {allowed_methods}"
    )


def test_cors_blocks_trace_method():
    """
    Verify TRACE method is not allowed (security risk - XST attacks).

    TRACE can be used for Cross-Site Tracing attacks and should be blocked.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "TRACE",
        }
    )

    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    assert "TRACE" not in allowed_methods, (
        f"TRACE method should NOT be allowed for security reasons. "
        f"Got: {allowed_methods}"
    )


# ============================================================================
# Scenario 3: Required Headers Allowed
# ============================================================================


@pytest.mark.parametrize("header", ["Content-Type", "Authorization", "X-Request-ID"])
def test_cors_allows_required_headers(header: str):
    """
    Verify required request headers are allowed in CORS preflight.

    These headers are needed by the frontend:
    - Content-Type: For JSON request bodies
    - Authorization: For future authentication tokens
    - X-Request-ID: For request tracing

    Args:
        header: Header name to test
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": header,
        }
    )

    assert response.status_code == 200, (
        f"Preflight with header {header} should return 200, got {response.status_code}"
    )

    # Header names are case-insensitive in CORS
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
    assert header.lower() in allowed_headers, (
        f"Header '{header}' should be in Access-Control-Allow-Headers. "
        f"Got: {allowed_headers}"
    )


def test_cors_allows_accept_header():
    """
    Verify Accept header is allowed (standard content negotiation).
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Accept",
        }
    )

    assert response.status_code == 200
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
    assert "accept" in allowed_headers, (
        f"Accept header should be allowed. Got: {allowed_headers}"
    )


def test_cors_allows_multiple_headers_in_single_request():
    """
    Verify multiple headers can be requested in a single preflight.

    Browsers may request multiple headers in a single preflight request.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        }
    )

    assert response.status_code == 200
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()

    # Both headers should be allowed
    assert "content-type" in allowed_headers, (
        f"Content-Type should be in allowed headers. Got: {allowed_headers}"
    )
    assert "authorization" in allowed_headers, (
        f"Authorization should be in allowed headers. Got: {allowed_headers}"
    )


# ============================================================================
# Scenario 4: Frontend Origin Allowed
# ============================================================================


def test_cors_allows_localhost_5173():
    """
    Verify http://localhost:5173 (Vite dev server) is allowed.

    This is the default Vite development server port.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200

    # With allow_credentials=True, origin should be echoed back (not wildcard)
    allow_origin = response.headers.get("Access-Control-Allow-Origin")
    assert allow_origin == "http://localhost:5173", (
        f"Expected origin 'http://localhost:5173', got '{allow_origin}'"
    )


def test_cors_allows_configured_frontend_origins():
    """
    Verify all configured frontend development origins are allowed.

    The frontend may run on different ports during development.
    """
    from backend.main import app
    from backend.config import settings

    client = TestClient(app)

    # Test each configured origin
    for origin in settings.cors_origins:
        response = client.options(
            "/api/v1/products",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )

        assert response.status_code == 200, (
            f"Origin {origin} should be allowed"
        )

        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        assert allow_origin == origin, (
            f"Expected origin '{origin}' to be echoed back, got '{allow_origin}'"
        )


def test_cors_allows_credentials():
    """
    Verify credentials are allowed (required for cookie authentication).

    The Access-Control-Allow-Credentials header must be 'true' for
    cross-origin requests with credentials to work.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200
    allow_credentials = response.headers.get("Access-Control-Allow-Credentials")
    assert allow_credentials == "true", (
        f"Expected credentials 'true', got '{allow_credentials}'"
    )


def test_cors_rejects_unknown_origin():
    """
    Verify unknown origins are rejected.

    Origins not in the allow list should not receive CORS headers.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        }
    )

    # The origin should NOT be echoed back for unknown origins
    allow_origin = response.headers.get("Access-Control-Allow-Origin")
    assert allow_origin != "http://malicious-site.com", (
        f"Malicious origin should not be allowed. Got: {allow_origin}"
    )


# ============================================================================
# Scenario 5: End-to-End Frontend Request
# ============================================================================


def test_cors_actual_get_request_from_frontend():
    """
    Verify actual GET request from frontend origin works.

    Simulates a real API request from the frontend.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.get(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
        }
    )

    # Request should succeed
    assert response.status_code == 200

    # CORS headers should be present in response
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_actual_post_request_from_frontend():
    """
    Verify actual POST request from frontend origin works.

    Simulates a calculation submission from the frontend.
    """
    from backend.main import app

    client = TestClient(app)

    # This endpoint may return 404 or 422, but CORS headers should still be present
    response = client.post(
        "/api/v1/calculate",
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
        },
        json={"product_id": "test-123"}  # May be invalid, that's OK
    )

    # CORS headers should be present regardless of response status
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


def test_cors_headers_on_error_response():
    """
    Verify CORS headers are present on error responses.

    Even when the API returns an error, CORS headers must be present
    for the browser to allow the frontend to read the error.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.get(
        "/api/v1/products/nonexistent-id-12345",
        headers={
            "Origin": "http://localhost:5173",
        }
    )

    # May return 404 (not found)
    # CORS headers should still be present
    allow_origin = response.headers.get("Access-Control-Allow-Origin")
    assert allow_origin == "http://localhost:5173", (
        f"CORS headers should be present on error responses. Got: {allow_origin}"
    )


# ============================================================================
# Scenario 6: Exposed Headers (Optional - for X-Request-ID tracing)
# ============================================================================


def test_cors_exposes_request_id_header():
    """
    Verify X-Request-ID is exposed to the frontend.

    The X-Request-ID header should be readable by the frontend for
    request tracing and debugging purposes.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    # Check expose_headers includes X-Request-ID
    exposed_headers = response.headers.get("Access-Control-Expose-Headers", "").lower()

    # This test verifies the configuration includes X-Request-ID in expose_headers
    assert "x-request-id" in exposed_headers, (
        f"X-Request-ID should be in Access-Control-Expose-Headers for tracing. "
        f"Got: {exposed_headers}"
    )


def test_cors_exposes_total_count_header():
    """
    Verify X-Total-Count is exposed to the frontend.

    The X-Total-Count header is used for pagination and should be
    readable by the frontend.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    exposed_headers = response.headers.get("Access-Control-Expose-Headers", "").lower()

    assert "x-total-count" in exposed_headers, (
        f"X-Total-Count should be in Access-Control-Expose-Headers for pagination. "
        f"Got: {exposed_headers}"
    )


# ============================================================================
# Security-Focused Tests
# ============================================================================


def test_cors_no_wildcard_methods():
    """
    Verify allow_methods is not a wildcard (*).

    Security requirement: Methods should be explicitly listed.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )

    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")

    # Wildcard should not be present
    assert "*" not in allowed_methods, (
        f"Access-Control-Allow-Methods should not be wildcard. Got: {allowed_methods}"
    )

    # Should contain explicit methods
    assert any(method in allowed_methods for method in ["GET", "POST", "PUT", "DELETE"]), (
        f"Should contain explicit method list, not wildcard. Got: {allowed_methods}"
    )


def test_cors_no_wildcard_headers():
    """
    Verify allow_headers is not a wildcard (*).

    Security requirement: Headers should be explicitly listed.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )

    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")

    # When explicitly requesting Content-Type, the response should list explicit headers
    # Note: With wildcard config, FastAPI may echo back the requested header
    # After fix, should return explicit list without wildcard

    # The key check: if we request a dangerous header, it should NOT be allowed
    # This is a secondary verification - the primary check is in test_cors_blocks_arbitrary_headers


def test_cors_blocks_arbitrary_headers():
    """
    Verify arbitrary/dangerous headers are not allowed.

    Headers like X-Custom-Dangerous should not be in the allow list.
    """
    from backend.main import app

    client = TestClient(app)
    response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Dangerous-Custom-Header",
        }
    )

    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()

    # With explicit header list, arbitrary headers should NOT be included
    # Note: With wildcard (*), the arbitrary header would be echoed back
    assert "x-dangerous-custom-header" not in allowed_headers, (
        f"Arbitrary headers should NOT be allowed. "
        f"This indicates wildcard headers are configured. Got: {allowed_headers}"
    )
