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
import re
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
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
        "Access-Control-Request-Method": "POST"
    })

    # Preflight response
    assert "access-control-allow-methods" in response.headers, \
        "Preflight response should include access-control-allow-methods"


def test_cors_allows_headers():
    """Test that CORS includes allowed headers"""
    from backend.main import app

    client = TestClient(app)
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    })

    assert "access-control-allow-headers" in response.headers, \
        "Preflight response should include access-control-allow-headers"


# Test Scenario 2: CORS Rejection for Disallowed Origin
def test_cors_rejects_evil_com():
    """Test that CORS rejects origin http://evil.com"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://evil.com"})

    # For rejected origins, CORS should NOT include allow-origin header
    # OR should include "null" or omit the header entirely
    cors_header = response.headers.get("access-control-allow-origin")
    assert cors_header != "http://evil.com", \
        f"CORS should not allow origin 'http://evil.com', got '{cors_header}'"


def test_cors_rejects_random_origin():
    """Test that CORS rejects unspecified origin"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://random-site.com"})

    cors_header = response.headers.get("access-control-allow-origin")
    assert cors_header != "http://random-site.com", \
        f"CORS should not allow origin 'http://random-site.com', got '{cors_header}'"


def test_cors_works_without_origin_header():
    """Test that requests without Origin header still work (not CORS requests)"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200, \
        "Requests without Origin header should still work (same-origin requests)"


# Test Scenario 3: Security Headers Present
def test_security_header_x_content_type_options():
    """Test that X-Content-Type-Options header is set"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-content-type-options" in response.headers, \
        "Response should include X-Content-Type-Options header"
    assert response.headers["x-content-type-options"] == "nosniff", \
        f"Expected 'nosniff', got '{response.headers.get('x-content-type-options')}'"


def test_security_header_x_frame_options():
    """Test that X-Frame-Options header is set"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-frame-options" in response.headers, \
        "Response should include X-Frame-Options header"
    assert response.headers["x-frame-options"] == "DENY", \
        f"Expected 'DENY', got '{response.headers.get('x-frame-options')}'"


def test_security_header_strict_transport_security():
    """Test that Strict-Transport-Security header is set"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "strict-transport-security" in response.headers, \
        "Response should include Strict-Transport-Security header"

    hsts_header = response.headers["strict-transport-security"]
    assert "max-age=" in hsts_header, "HSTS header should include max-age"
    assert "includeSubDomains" in hsts_header, "HSTS header should include includeSubDomains"


def test_security_header_x_xss_protection():
    """Test that X-XSS-Protection header is set"""
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "x-xss-protection" in response.headers, \
        "Response should include X-XSS-Protection header"
    assert response.headers["x-xss-protection"] == "1; mode=block", \
        f"Expected '1; mode=block', got '{response.headers.get('x-xss-protection')}'"


def test_security_headers_with_cors_preflight():
    """Test that security headers are present even on CORS preflight requests"""
    from backend.main import app

    client = TestClient(app)
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })

    # Security headers should be present even on OPTIONS requests
    assert "x-content-type-options" in response.headers, \
        "Security headers should be present on preflight requests"


# Test Scenario 4: Request Logging Middleware
def test_request_logging_logs_successful_requests(caplog):
    """Test that successful requests are logged"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200

    # Check that request was logged
    assert len(caplog.records) > 0, "Request should be logged"
    assert any("GET /health" in record.message for record in caplog.records), \
        "Log should contain request method and path"
    assert any("status=200" in record.message for record in caplog.records), \
        "Log should contain status code"
    assert any("duration=" in record.message for record in caplog.records), \
        "Log should contain duration"


def test_request_logging_includes_duration(caplog):
    """Test that request logging includes duration in seconds"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        client.get("/health")

    # Find log record with duration
    log_messages = [record.message for record in caplog.records]
    duration_logs = [msg for msg in log_messages if "duration=" in msg]

    assert len(duration_logs) > 0, "Should have logs with duration"

    # Verify duration format (e.g., "duration=0.002s")
    duration_pattern = r"duration=\d+\.\d+s"
    assert any(re.search(duration_pattern, log) for log in duration_logs), \
        "Duration should be in format 'duration=X.XXXs'"


def test_request_logging_logs_error_requests(caplog):
    """Test that failed requests are logged with error information"""
    from backend.main import global_exception_handler
    from backend.middleware import SecurityHeadersMiddleware

    # Create test app with error endpoint
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/test-error")
    async def error_endpoint():
        raise ValueError("Test error")

    # Apply same middleware as main app
    @test_app.middleware("http")
    async def log_requests(request, call_next):
        import time
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger = logging.getLogger("backend.main")
            logger.info(
                f"{request.method} {request.url.path} "
                f"status={response.status_code} "
                f"duration={process_time:.3f}s"
            )
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger = logging.getLogger("backend.main")
            logger.error(
                f"{request.method} {request.url.path} "
                f"error={type(exc).__name__} "
                f"duration={process_time:.3f}s"
            )
            raise

    test_app.add_exception_handler(Exception, global_exception_handler)

    with caplog.at_level(logging.ERROR):
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test-error")

    # Check that error was logged
    assert any("error=" in record.message for record in caplog.records), \
        "Error requests should be logged with error information"
    assert any("ValueError" in record.message for record in caplog.records), \
        "Log should contain exception type"


def test_request_logging_different_methods(caplog):
    """Test that logging works for different HTTP methods"""
    from backend.main import app

    with caplog.at_level(logging.INFO):
        client = TestClient(app)
        client.get("/health")
        client.options("/health")

    log_messages = [record.message for record in caplog.records]

    # Should have logs for different methods
    assert any("GET /health" in msg for msg in log_messages), \
        "Should log GET requests"
    assert any("OPTIONS /health" in msg for msg in log_messages), \
        "Should log OPTIONS requests"


# Test Scenario 5: Global Exception Handler
@pytest.fixture
def test_app_with_errors():
    """Test app with pre-defined error endpoints for exception handler testing"""
    from backend.main import global_exception_handler
    from backend.middleware import SecurityHeadersMiddleware

    test_app = FastAPI()

    # Apply same middleware as main app
    test_app.add_middleware(SecurityHeadersMiddleware)

    # Add test routes BEFORE creating TestClient
    @test_app.get("/test-error")
    async def error_endpoint():
        raise ValueError("Test error message")

    @test_app.get("/test-error-sensitive")
    async def error_endpoint_sensitive():
        raise ValueError("Sensitive internal error: database password is 12345")

    @test_app.get("/test-error-runtime")
    async def error_endpoint_runtime():
        raise RuntimeError("Test runtime error")

    # Apply exception handler
    test_app.add_exception_handler(Exception, global_exception_handler)

    return test_app


def test_global_exception_handler_catches_exceptions(test_app_with_errors):
    """Test that global exception handler catches unhandled exceptions"""
    client = TestClient(test_app_with_errors, raise_server_exceptions=False)
    response = client.get("/test-error")

    assert response.status_code == 500, \
        f"Expected status code 500 for unhandled exception, got {response.status_code}"


def test_global_exception_handler_returns_correct_format(test_app_with_errors):
    """Test that global exception handler returns error in API specification format"""
    client = TestClient(test_app_with_errors, raise_server_exceptions=False)
    response = client.get("/test-error")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json", \
        "Error response should be JSON"

    data = response.json()

    # Verify error structure per api-specifications.md
    assert "error" in data, "Response should contain 'error' object"
    assert "request_id" in data, "Response should contain 'request_id'"
    assert "timestamp" in data, "Response should contain 'timestamp'"

    # Verify error object structure
    error_obj = data["error"]
    assert "code" in error_obj, "Error object should contain 'code'"
    assert "message" in error_obj, "Error object should contain 'message'"
    assert "details" in error_obj, "Error object should contain 'details'"

    # Verify error code is CALCULATION_FAILED for 500 errors
    assert error_obj["code"] == "CALCULATION_FAILED", \
        f"Expected error code 'CALCULATION_FAILED', got '{error_obj['code']}'"

    # Verify message is generic
    assert "Internal server error" in error_obj["message"], \
        "Error message should be generic"

    # Verify details is a list (empty for 500 errors)
    assert isinstance(error_obj["details"], list), \
        "Error details should be a list"

    # Verify request_id format (e.g., "req_abc123")
    assert data["request_id"].startswith("req_"), \
        f"Request ID should start with 'req_', got '{data['request_id']}'"

    # Verify timestamp is ISO 8601 format
    try:
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Timestamp should be valid ISO 8601 format, got '{data['timestamp']}'")


def test_global_exception_handler_does_not_leak_details(test_app_with_errors):
    """Test that global exception handler does not leak internal error details"""
    client = TestClient(test_app_with_errors, raise_server_exceptions=False)
    response = client.get("/test-error-sensitive")

    assert response.status_code == 500
    data = response.json()

    # Should contain generic error message
    assert "error" in data
    assert "Internal server error" in data["error"]["message"], \
        "Error should return generic message"

    # Should NOT contain sensitive details in any field
    response_str = str(data).lower()
    assert "password" not in response_str, \
        "Error response should not leak sensitive information (password)"
    assert "12345" not in response_str, \
        "Error response should not leak sensitive information (actual password)"


def test_global_exception_handler_logs_error(test_app_with_errors, caplog):
    """Test that global exception handler logs the full error server-side"""
    with caplog.at_level(logging.ERROR):
        client = TestClient(test_app_with_errors, raise_server_exceptions=False)
        response = client.get("/test-error")

    assert response.status_code == 500

    # Error should be logged server-side (but not exposed to client)
    assert len(caplog.records) > 0, "Exception should be logged"
    assert any("Unhandled exception" in record.message for record in caplog.records), \
        "Log should contain 'Unhandled exception'"

    # Full error details should be in logs
    log_messages = " ".join([record.message for record in caplog.records])
    assert "Test error message" in log_messages, \
        "Full error message should be logged server-side"


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

    # Response content should be preserved
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_middleware_applies_to_all_routes():
    """Test that middleware applies to all routes (not just /health)"""
    from backend.main import app

    client = TestClient(app)

    # Test with health endpoint
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert "x-content-type-options" in response.headers
    assert "access-control-allow-origin" in response.headers

    # Test with non-existent route (404 response should also have headers)
    response = client.get("/nonexistent")
    assert "x-content-type-options" in response.headers


# File Structure Tests
def test_backend_files_exist():
    """Test that required backend files exist"""
    backend_dir = Path(__file__).parent.parent

    assert (backend_dir / "main.py").exists(), "main.py should exist"
    assert (backend_dir / "config.py").exists(), "config.py should exist"
    assert (backend_dir / "middleware.py").exists(), "middleware.py should exist"
    assert (backend_dir / "__init__.py").exists(), "__init__.py should exist"


def test_backend_init_has_version():
    """Test that __init__.py exports version"""
    from backend import __version__

    assert __version__ == "1.0.0", \
        f"Expected version '1.0.0', got '{__version__}'"


def test_backend_config_has_settings():
    """Test that config module exports settings"""
    from backend.config import settings

    assert settings is not None, "settings should be exported from config module"
    assert hasattr(settings, "cors_origins"), "settings should have cors_origins attribute"


def test_backend_middleware_exports_security_class():
    """Test that middleware module exports SecurityHeadersMiddleware"""
    from backend.middleware import SecurityHeadersMiddleware

    assert SecurityHeadersMiddleware is not None, \
        "SecurityHeadersMiddleware should be exported from middleware module"
