"""
Test suite for CORS and Security middleware
Following TDD methodology - these tests are written BEFORE implementation

Test Scenarios (from TASK-BE-003 specification):
1. CORS Headers for Allowed Origin
2. CORS Rejection for Disallowed Origin
3. Security Headers Present
4. Request Logging Middleware
5. Global Exception Handler
"""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Test Scenario 1: CORS Headers for Allowed Origin
def test_cors_allows_localhost_3000():
    """Test that CORS allows http://localhost:3000 origin"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000", \
        f"Expected CORS origin 'http://localhost:3000', got '{response.headers.get('access-control-allow-origin')}'"


def test_cors_allows_credentials():
    """Test that CORS allows credentials"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert "access-control-allow-credentials" in response.headers, \
        "CORS should include access-control-allow-credentials header"
    assert response.headers["access-control-allow-credentials"] == "true", \
        f"Expected credentials 'true', got '{response.headers.get('access-control-allow-credentials')}'"


def test_cors_allows_methods():
    """Test that CORS includes allowed methods header"""
    from backend.main import app

    client = TestClient(app)
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })

    assert "access-control-allow-methods" in response.headers, \
        "CORS should include access-control-allow-methods header"


def test_cors_allows_headers():
    """Test that CORS includes allowed headers"""
    from backend.main import app

    client = TestClient(app)
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type"
    })

    assert "access-control-allow-headers" in response.headers, \
        "CORS should include access-control-allow-headers header"


# Test Scenario 2: CORS Rejection for Disallowed Origin
def test_cors_rejects_disallowed_origin():
    """Test that CORS does not set access-control-allow-origin for disallowed origins"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://evil.com"})

    # FastAPI's CORS middleware will not set the header for disallowed origins
    assert response.headers.get("access-control-allow-origin") != "http://evil.com", \
        "CORS should not allow http://evil.com origin"


def test_cors_rejects_random_origin():
    """Test that CORS does not allow random origins"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://random-site.com"})

    # Should either not set the header or not match the origin
    cors_origin = response.headers.get("access-control-allow-origin")
    assert cors_origin != "http://random-site.com", \
        f"CORS should not allow random origins, got {cors_origin}"


def test_cors_allows_no_origin_header():
    """Test that requests without Origin header work normally"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    # Request should succeed even without Origin header
    assert response.status_code == 200


# Test Scenario 3: Security Headers Present
def test_security_header_x_content_type_options():
    """Test that X-Content-Type-Options header is present"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-content-type-options" in response.headers, \
        "Response should include X-Content-Type-Options header"
    assert response.headers["x-content-type-options"] == "nosniff", \
        f"Expected X-Content-Type-Options 'nosniff', got '{response.headers.get('x-content-type-options')}'"


def test_security_header_x_frame_options():
    """Test that X-Frame-Options header is present"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-frame-options" in response.headers, \
        "Response should include X-Frame-Options header"
    assert response.headers["x-frame-options"] == "DENY", \
        f"Expected X-Frame-Options 'DENY', got '{response.headers.get('x-frame-options')}'"


def test_security_header_x_xss_protection():
    """Test that X-XSS-Protection header is present"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-xss-protection" in response.headers, \
        "Response should include X-XSS-Protection header"
    assert response.headers["x-xss-protection"] == "1; mode=block", \
        f"Expected X-XSS-Protection '1; mode=block', got '{response.headers.get('x-xss-protection')}'"


def test_security_header_strict_transport_security():
    """Test that Strict-Transport-Security header is present"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "strict-transport-security" in response.headers, \
        "Response should include Strict-Transport-Security header"
    expected = "max-age=31536000; includeSubDomains"
    assert response.headers["strict-transport-security"] == expected, \
        f"Expected Strict-Transport-Security '{expected}', got '{response.headers.get('strict-transport-security')}'"


def test_security_headers_on_multiple_endpoints():
    """Test that security headers are present on all endpoints"""
    from backend.main import app

    client = TestClient(app)

    # Test health endpoint
    response_health = client.get("/health")
    assert "x-content-type-options" in response_health.headers
    assert "x-frame-options" in response_health.headers

    # Test docs endpoint (if it exists)
    response_docs = client.get("/docs")
    assert "x-content-type-options" in response_docs.headers
    assert "x-frame-options" in response_docs.headers


# Test Scenario 4: Request Logging Middleware
def test_request_logging_captures_method_and_path(caplog):
    """Test that request logging captures HTTP method and path"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    assert "GET" in caplog.text, "Log should contain HTTP method 'GET'"
    assert "/health" in caplog.text, "Log should contain path '/health'"


def test_request_logging_captures_status_code(caplog):
    """Test that request logging captures response status code"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    assert "200" in caplog.text, "Log should contain status code '200'"


def test_request_logging_captures_duration(caplog):
    """Test that request logging captures request duration"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    # Log should contain duration in format like "duration=0.001s"
    assert "duration=" in caplog.text, "Log should contain duration information"


def test_request_logging_for_different_methods(caplog):
    """Test that request logging works for different HTTP methods"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)

        # Test GET
        caplog.clear()
        client.get("/health")
        assert "GET" in caplog.text

        # Test OPTIONS (for CORS preflight)
        caplog.clear()
        client.options("/health")
        assert "OPTIONS" in caplog.text


# Test Scenario 5: Global Exception Handler
def test_global_exception_handler_catches_exceptions():
    """Test that global exception handler catches unhandled exceptions"""
    from backend.main import app

    # Add a test endpoint that raises an exception
    @app.get("/test-error")
    async def error_endpoint():
        raise ValueError("Test error message")

    client = TestClient(app)
    response = client.get("/test-error")

    assert response.status_code == 500, \
        f"Expected status code 500 for unhandled exception, got {response.status_code}"


def test_global_exception_handler_returns_json():
    """Test that global exception handler returns JSON response"""
    from backend.main import app

    # Add a test endpoint that raises an exception
    @app.get("/test-error-json")
    async def error_endpoint_json():
        raise RuntimeError("Test runtime error")

    client = TestClient(app)
    response = client.get("/test-error-json")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json", \
        "Error response should be JSON"

    data = response.json()
    assert "detail" in data, "Error response should contain 'detail' field"


def test_global_exception_handler_does_not_leak_details():
    """Test that global exception handler does not leak internal error details"""
    from backend.main import app

    # Add a test endpoint that raises an exception with sensitive info
    @app.get("/test-error-sensitive")
    async def error_endpoint_sensitive():
        raise ValueError("Sensitive internal error: database password is 12345")

    client = TestClient(app)
    response = client.get("/test-error-sensitive")

    assert response.status_code == 500
    data = response.json()

    # Should contain generic error message
    assert "detail" in data
    assert "Internal server error" in data["detail"], \
        "Error should return generic message"

    # Should NOT contain sensitive details
    assert "password" not in data["detail"].lower(), \
        "Error response should not leak sensitive information"
    assert "12345" not in data["detail"], \
        "Error response should not leak sensitive information"


def test_global_exception_handler_logs_error(caplog):
    """Test that global exception handler logs the full error"""
    from backend.main import app

    # Add a test endpoint that raises an exception
    @app.get("/test-error-logging")
    async def error_endpoint_logging():
        raise ValueError("This error should be logged")

    with caplog.at_level(logging.ERROR):
        client = TestClient(app)
        response = client.get("/test-error-logging")

    assert response.status_code == 500
    # Error should be logged (but not exposed to client)
    assert len(caplog.records) > 0, "Exception should be logged"
    assert any("Unhandled exception" in record.message for record in caplog.records), \
        "Log should contain 'Unhandled exception'"


# Additional Integration Tests
def test_middleware_order_cors_before_security():
    """Test that CORS headers work alongside security headers"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    # Both CORS and security headers should be present
    assert "access-control-allow-origin" in response.headers
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers


def test_middleware_preserves_response_content():
    """Test that middleware does not modify response content"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    expected = {"status": "healthy", "version": "1.0.0"}
    assert response.json() == expected, \
        "Middleware should not modify response content"


def test_security_headers_with_cors_preflight():
    """Test that security headers are present on CORS preflight requests"""
    from backend.main import app

    client = TestClient(app)
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })

    # Security headers should be present even on OPTIONS requests
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers


# File Structure Tests
def test_middleware_file_exists():
    """Test that middleware.py file exists in backend/"""
    backend_path = Path(__file__).parent.parent
    middleware_file = backend_path / "middleware.py"

    assert middleware_file.exists(), \
        f"backend/middleware.py should exist at {middleware_file}"


def test_middleware_can_be_imported():
    """Test that middleware module can be imported"""
    try:
        from backend import middleware
        assert True
    except ImportError as e:
        pytest.fail(f"backend.middleware should be importable: {e}")


def test_security_headers_middleware_exists():
    """Test that SecurityHeadersMiddleware class exists"""
    from backend.middleware import SecurityHeadersMiddleware

    assert SecurityHeadersMiddleware is not None, \
        "SecurityHeadersMiddleware class should be defined"


def test_security_headers_middleware_is_middleware():
    """Test that SecurityHeadersMiddleware extends BaseHTTPMiddleware"""
    from backend.middleware import SecurityHeadersMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware

    assert issubclass(SecurityHeadersMiddleware, BaseHTTPMiddleware), \
        "SecurityHeadersMiddleware should extend BaseHTTPMiddleware"
