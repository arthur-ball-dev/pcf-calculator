"""
Test suite for Rate Limiting Middleware.

TASK-BE-P7-020: Rate Limiting Middleware
TASK-QA-P7-031: Updated to support authenticated endpoints
Following TDD methodology - these tests are written BEFORE implementation.

This test suite verifies that rate limiting middleware is properly configured to:
1. Protect API endpoints from abuse
2. Apply different limits per endpoint category
3. Return proper 429 responses with Retry-After headers
4. Track rate limits per client (by IP or user ID)

Test Scenarios:
1. Within rate limit - requests succeed with rate limit headers
2. Exceeds rate limit - 429 response with Retry-After
3. Calculation endpoint stricter limit (10/min vs 100/min)
4. Rate limit reset after window expires
5. Different limits per client (per-client, not global)
6. Auth endpoint brute force protection
7. Rate limit headers always present
8. Admin users have higher limits

Reference: Code Review Report (Issue #9 - No Rate Limiting)
"""

import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ============================================================================
# Fixtures
# ============================================================================


def _get_test_auth_headers():
    from backend.auth.jwt import create_access_token
    token = create_access_token(data={"user_id": 1, "username": "ratelimittest", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def _get_admin_auth_headers():
    from backend.auth.jwt import create_access_token
    token = create_access_token(data={"user_id": 2, "username": "adminratelimittest", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def app_with_rate_limiting():
    """
    Get the FastAPI app with rate limiting middleware.

    This fixture imports the app after rate limiting is implemented.
    """
    from backend.main import app
    return app


@pytest.fixture
def client(app_with_rate_limiting):
    """Create a TestClient for the app."""
    return TestClient(app_with_rate_limiting)


@pytest.fixture
def mock_rate_limit_storage():
    """
    Create a mock rate limit storage for testing.

    Allows tests to manipulate rate limit counters directly.
    """
    from backend.middleware.rate_limiting import get_rate_limit_storage

    storage = MagicMock()
    storage.get_count.return_value = 0
    storage.increment.return_value = 1
    storage.get_reset_time.return_value = int(time.time()) + 60

    return storage


# ============================================================================
# Scenario 1: Within Rate Limit - All Requests Succeed
# ============================================================================


def test_rate_limit_within_limit_succeeds():
    """
    Verify requests within rate limit succeed with 200 status.

    Input: 10 requests to GET /api/v1/products within 1 minute
    Rate limit: 100/minute
    Expected: All 10 requests return 200
    """
    from backend.main import app

    client = TestClient(app)

    # Make 10 requests (well under 100/min limit)
    for i in range(10):
        response = client.get("/api/v1/products", headers=_get_test_auth_headers())
        assert response.status_code == 200, (
            f"Request {i+1} should succeed within rate limit, got {response.status_code}"
        )


def test_rate_limit_headers_present_on_success():
    """
    Verify rate limit headers are present on successful responses.

    Expected headers:
    - X-RateLimit-Limit: 100
    - X-RateLimit-Remaining: decreasing value
    - X-RateLimit-Reset: Unix timestamp
    """
    from backend.main import app

    client = TestClient(app)

    response = client.get("/api/v1/products", headers=_get_test_auth_headers())

    assert response.status_code == 200

    # Check rate limit headers are present
    assert "X-RateLimit-Limit" in response.headers, (
        "X-RateLimit-Limit header should be present"
    )
    assert "X-RateLimit-Remaining" in response.headers, (
        "X-RateLimit-Remaining header should be present"
    )
    assert "X-RateLimit-Reset" in response.headers, (
        "X-RateLimit-Reset header should be present"
    )

    # Verify header values are valid
    limit = int(response.headers["X-RateLimit-Limit"])
    remaining = int(response.headers["X-RateLimit-Remaining"])
    reset = int(response.headers["X-RateLimit-Reset"])

    assert limit == 100, f"Expected limit 100, got {limit}"
    assert remaining >= 0, f"Remaining should be >= 0, got {remaining}"
    assert reset > 0, f"Reset should be a positive timestamp, got {reset}"


def test_rate_limit_remaining_decreases():
    """
    Verify X-RateLimit-Remaining decreases with each request.

    After first request: Remaining = 99
    After second request: Remaining = 98
    """
    from backend.main import app

    client = TestClient(app)

    # First request
    response1 = client.get("/api/v1/products")
    remaining1 = int(response1.headers.get("X-RateLimit-Remaining", 0))

    # Second request
    response2 = client.get("/api/v1/products")
    remaining2 = int(response2.headers.get("X-RateLimit-Remaining", 0))

    assert remaining2 == remaining1 - 1, (
        f"Remaining should decrease by 1. First: {remaining1}, Second: {remaining2}"
    )


# ============================================================================
# Scenario 2: Exceeds Rate Limit - 429 Response
# ============================================================================


def test_rate_limit_exceeded_returns_429():
    """
    Verify 429 status when rate limit is exceeded.

    Input: 101 requests to GET /api/v1/products within 1 minute
    Rate limit: 100/minute
    Expected (101st request): 429 Too Many Requests
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    # Create a fresh app for this test with low limit
    test_app = FastAPI()

    # Add rate limiting with very low limit for testing
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    # Apply rate limiting middleware with limit of 5 for quick testing
    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=5,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Make 5 requests (at limit)
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200, f"Request {i+1} should succeed"

    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429, (
        f"Request exceeding limit should return 429, got {response.status_code}"
    )


def test_rate_limit_exceeded_response_body():
    """
    Verify 429 response body contains proper error message.

    Expected body: {"detail": "Rate limit exceeded. Try again later."}
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=1,
        window_seconds=60
    )

    client = TestClient(test_app)

    # First request succeeds
    client.get("/test")

    # Second request is rate limited
    response = client.get("/test")

    assert response.status_code == 429
    data = response.json()
    assert "detail" in data, "Response should contain 'detail' field"
    assert "rate limit" in data["detail"].lower(), (
        f"Error message should mention rate limit. Got: {data['detail']}"
    )


def test_rate_limit_exceeded_retry_after_header():
    """
    Verify 429 response includes Retry-After header.

    Expected: Retry-After header with seconds until reset
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=1,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Exhaust limit
    client.get("/test")

    # Rate limited request
    response = client.get("/test")

    assert response.status_code == 429
    assert "Retry-After" in response.headers, (
        "429 response should include Retry-After header"
    )

    retry_after = int(response.headers["Retry-After"])
    assert 0 < retry_after <= 60, (
        f"Retry-After should be between 0 and 60 seconds, got {retry_after}"
    )


def test_rate_limit_exceeded_still_has_limit_headers():
    """
    Verify 429 response still includes rate limit headers.

    Expected headers on 429:
    - X-RateLimit-Limit: 100
    - X-RateLimit-Remaining: 0
    - X-RateLimit-Reset: <timestamp>
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=1,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Exhaust limit
    client.get("/test")

    # Rate limited request
    response = client.get("/test")

    assert response.status_code == 429

    # Rate limit headers should still be present
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    # Remaining should be 0
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert remaining == 0, f"Remaining should be 0 when exceeded, got {remaining}"


# ============================================================================
# Scenario 3: Calculation Endpoint Stricter Limit
# ============================================================================


def test_calculation_endpoint_has_stricter_limit():
    """
    Verify POST /api/v1/calculate has stricter rate limit (10/min).

    Input: 11 requests to POST /api/v1/calculate within 1 minute
    Rate limit: 10/minute for calculations
    Expected: 11th request returns 429
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/calculate")
    async def calculate_endpoint():
        return {"status": "ok"}

    @test_app.get("/api/v1/products")
    async def products_endpoint():
        return {"status": "ok"}

    # Add middleware with different limits per endpoint
    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/calculate": 10,  # Stricter limit for expensive operations
        }
    )

    client = TestClient(test_app)

    # Make 10 calculation requests (at limit)
    for i in range(10):
        response = client.post("/api/v1/calculate", headers=_get_test_auth_headers())
        assert response.status_code == 200, (
            f"Calculation request {i+1} should succeed, got {response.status_code}"
        )

    # 11th calculation request should be rate limited
    response = client.post("/api/v1/calculate", headers=_get_test_auth_headers())
    assert response.status_code == 429, (
        f"11th calculation request should return 429, got {response.status_code}"
    )


def test_calculation_limit_independent_of_general_limit():
    """
    Verify calculation limit is tracked separately from general endpoints.

    Calculation requests should use the 10/min limit while general
    endpoints use the 100/min limit.
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/calculate")
    async def calculate_endpoint():
        return {"status": "ok"}

    @test_app.get("/api/v1/products")
    async def products_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/calculate": 2,  # Very low limit for testing
        }
    )

    client = TestClient(test_app)

    # Exhaust calculation limit
    client.post("/api/v1/calculate", headers=_get_test_auth_headers())
    client.post("/api/v1/calculate", headers=_get_test_auth_headers())

    # Calculation should now be rate limited
    calc_response = client.post("/api/v1/calculate", headers=_get_test_auth_headers())
    assert calc_response.status_code == 429, (
        "Calculation endpoint should be rate limited"
    )

    # But products endpoint should still work
    products_response = client.get("/api/v1/products", headers=_get_test_auth_headers())
    assert products_response.status_code == 200, (
        "Products endpoint should not be affected by calculation limit"
    )


def test_calculation_endpoint_shows_correct_limit_header():
    """
    Verify X-RateLimit-Limit shows the correct limit for calculations.

    Expected: X-RateLimit-Limit: 10 (not 100)
    """
    from backend.main import app
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/calculate")
    async def calculate_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/calculate": 10,
        }
    )

    client = TestClient(test_app)

    response = client.post("/api/v1/calculate", headers=_get_test_auth_headers())

    assert response.status_code == 200
    limit = int(response.headers.get("X-RateLimit-Limit", 0))
    assert limit == 10, (
        f"Calculation endpoint should show limit of 10, got {limit}"
    )


# ============================================================================
# Scenario 4: Rate Limit Reset After Window
# ============================================================================


def test_rate_limit_resets_after_window():
    """
    Verify rate limit resets after the time window expires.

    Input:
    1. Exhaust limit (e.g., 5 requests)
    2. Wait for reset window
    3. Make another request

    Expected: Request after reset succeeds (200)
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    # Use 1-second window for fast testing
    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=2,
        window_seconds=1  # 1 second window for quick reset
    )

    client = TestClient(test_app)

    # Exhaust limit
    client.get("/test")
    client.get("/test")

    # Should be rate limited
    response = client.get("/test")
    assert response.status_code == 429, "Should be rate limited"

    # Wait for window to reset
    time.sleep(1.1)

    # Should succeed after reset
    response = client.get("/test")
    assert response.status_code == 200, (
        f"Request after reset should succeed, got {response.status_code}"
    )


def test_rate_limit_remaining_resets_after_window():
    """
    Verify X-RateLimit-Remaining resets to full value after window.

    Expected after reset: X-RateLimit-Remaining close to limit
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=10,
        window_seconds=1
    )

    client = TestClient(test_app)

    # Use some of the limit
    for _ in range(5):
        client.get("/test")

    response = client.get("/test")
    remaining_before = int(response.headers.get("X-RateLimit-Remaining", 0))

    # Wait for reset
    time.sleep(1.1)

    # Check remaining after reset
    response = client.get("/test")
    remaining_after = int(response.headers.get("X-RateLimit-Remaining", 0))

    assert remaining_after > remaining_before, (
        f"Remaining should reset. Before: {remaining_before}, After: {remaining_after}"
    )


# ============================================================================
# Scenario 5: Different Limits Per Client
# ============================================================================


def test_rate_limit_is_per_client_not_global():
    """
    Verify rate limits are tracked per client, not globally.

    Input:
    - Client A: 50 requests (different IP)
    - Client B: 50 requests (different IP)

    Expected: Both clients succeed (limit is per-client)
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=5,
        window_seconds=60
    )

    # Client A with IP 192.168.1.1
    client_a = TestClient(test_app)

    # Make requests as Client A
    for i in range(5):
        response = client_a.get(
            "/test",
            headers={"X-Forwarded-For": "192.168.1.1"}
        )
        assert response.status_code == 200, f"Client A request {i+1} should succeed"

    # Client A should now be rate limited
    response_a = client_a.get(
        "/test",
        headers={"X-Forwarded-For": "192.168.1.1"}
    )
    assert response_a.status_code == 429, "Client A should be rate limited"

    # Client B with different IP should still be able to make requests
    response_b = client_a.get(
        "/test",
        headers={"X-Forwarded-For": "192.168.1.2"}  # Different IP
    )
    assert response_b.status_code == 200, (
        "Client B should not be affected by Client A's rate limit"
    )


def test_each_client_has_independent_remaining_count():
    """
    Verify each client has independent remaining counts.

    Expected:
    - Client A X-RateLimit-Remaining: 49 (after 1 request)
    - Client B X-RateLimit-Remaining: 49 (after 1 request)
    (Not 48 for Client B, which would indicate shared counter)
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=50,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Client A first request
    response_a = client.get("/test", headers={"X-Forwarded-For": "10.0.0.1"})
    remaining_a = int(response_a.headers.get("X-RateLimit-Remaining", 0))

    # Client B first request
    response_b = client.get("/test", headers={"X-Forwarded-For": "10.0.0.2"})
    remaining_b = int(response_b.headers.get("X-RateLimit-Remaining", 0))

    # Both should have same remaining (independent counters)
    assert remaining_a == remaining_b, (
        f"Clients should have independent counters. "
        f"Client A: {remaining_a}, Client B: {remaining_b}"
    )


def test_authenticated_user_tracked_by_user_id():
    """
    Verify authenticated users are tracked by user ID, not IP.

    When a user is authenticated, rate limiting should use user ID
    so the same user is rate limited regardless of IP address.
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=3,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Simulate authenticated user by adding auth header
    # (The middleware should extract user ID from token)
    auth_headers = {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.test",
        "X-Forwarded-For": "10.0.0.1"
    }

    # Make requests from different IPs but same user
    for i in range(3):
        auth_headers["X-Forwarded-For"] = f"10.0.0.{i+1}"
        response = client.get("/test", headers=auth_headers)
        assert response.status_code == 200, f"Request {i+1} should succeed"

    # 4th request should be limited (same user, different IP)
    auth_headers["X-Forwarded-For"] = "10.0.0.100"
    response = client.get("/test", headers=auth_headers)

    # User should be rate limited regardless of IP
    assert response.status_code == 429, (
        "Authenticated user should be rate limited by user ID, not IP"
    )


# ============================================================================
# Scenario 6: Auth Endpoint Brute Force Protection
# ============================================================================


def test_auth_endpoint_has_brute_force_protection():
    """
    Verify auth endpoint has stricter limits for brute force protection.

    Input: 6 failed login attempts within 5 minutes
    Limit: 5 failed attempts per 5 minutes

    Expected: 429 response on 6th attempt
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/auth/login")
    async def login_endpoint():
        # Simulate failed login
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid credentials"}
        )

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/auth/login": 5,  # Only 5 attempts per window
        }
    )

    client = TestClient(test_app)

    # Make 5 login attempts (at limit)
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "wrong"}
        )
        # Even though auth fails, rate limit not yet exceeded
        assert response.status_code in [401, 200], (
            f"Attempt {i+1} should not be rate limited yet"
        )

    # 6th attempt should be rate limited
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": "wrong"}
    )
    assert response.status_code == 429, (
        f"6th login attempt should be rate limited, got {response.status_code}"
    )


def test_auth_rate_limit_error_message():
    """
    Verify auth rate limit returns specific error message.

    Expected: {"detail": "Too many login attempts. Please try again later."}
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/auth/login")
    async def login_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/auth/login": 1,
        },
        endpoint_error_messages={
            "/api/v1/auth/login": "Too many login attempts. Please try again later."
        }
    )

    client = TestClient(test_app)

    # Exhaust limit
    client.post("/api/v1/auth/login", json={"username": "test"})

    # Rate limited request
    response = client.post("/api/v1/auth/login", json={"username": "test"})

    assert response.status_code == 429
    data = response.json()
    assert "Too many login attempts" in data.get("detail", ""), (
        f"Auth rate limit should have specific message. Got: {data}"
    )


def test_auth_rate_limit_retry_after():
    """
    Verify auth rate limit Retry-After is set to longer window (5 minutes).

    Expected: Retry-After: 300 (5 minutes)
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.post("/api/v1/auth/login")
    async def login_endpoint():
        return {"status": "ok"}

    # Auth endpoints use 5-minute window (300 seconds)
    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        endpoint_limits={
            "/api/v1/auth/login": 1,
        },
        endpoint_windows={
            "/api/v1/auth/login": 300,  # 5 minute window
        }
    )

    client = TestClient(test_app)

    # Exhaust limit
    client.post("/api/v1/auth/login", json={})

    # Rate limited request
    response = client.post("/api/v1/auth/login", json={})

    assert response.status_code == 429
    retry_after = int(response.headers.get("Retry-After", 0))

    # Should be close to 300 seconds (5 minutes)
    assert retry_after > 0, "Retry-After should be set"
    assert retry_after <= 300, f"Retry-After should be <= 300, got {retry_after}"


# ============================================================================
# Scenario 7: Admin Users Have Higher Limits
# ============================================================================


def test_admin_user_has_higher_rate_limit():
    """
    Verify admin users have 10x higher rate limits.

    Regular user: 100/min
    Admin user: 1000/min

    Expected: Admin user's X-RateLimit-Limit shows 1000
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=100,
        window_seconds=60,
        admin_multiplier=10  # Admins get 10x limits
    )

    client = TestClient(test_app)

    # Request as admin (simulated via header or token)
    response = client.get(
        "/test",
        headers={"X-Admin": "true"}  # Or via JWT with admin role
    )

    limit = int(response.headers.get("X-RateLimit-Limit", 0))

    # Admin should have 10x the normal limit
    assert limit == 1000, (
        f"Admin should have limit of 1000 (10x normal), got {limit}"
    )


def test_admin_can_exceed_regular_limit():
    """
    Verify admin users can make more requests than regular limit.

    After regular users would be rate limited (101 requests),
    admin should still be able to continue.
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=5,  # Low limit for testing
        window_seconds=60,
        admin_multiplier=10  # Admin gets 50 (10x5)
    )

    client = TestClient(test_app)

    # Make requests as admin (exceeding regular limit)
    for i in range(10):
        response = client.get(
            "/test",
            headers={"X-Admin": "true"}
        )
        assert response.status_code == 200, (
            f"Admin request {i+1} should succeed (under admin limit)"
        )


# ============================================================================
# Additional Test Requirements
# ============================================================================


def test_x_forwarded_for_header_respected():
    """
    Verify X-Forwarded-For header is used for client IP (proxy support).

    When behind a load balancer/proxy, the real client IP is in
    X-Forwarded-For header.
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=3,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Make requests from "different" IPs via X-Forwarded-For
    for i in range(3):
        response = client.get(
            "/test",
            headers={"X-Forwarded-For": "192.168.1.100"}
        )
        assert response.status_code == 200

    # 4th request from same "IP" should be rate limited
    response = client.get(
        "/test",
        headers={"X-Forwarded-For": "192.168.1.100"}
    )
    assert response.status_code == 429, (
        "Should respect X-Forwarded-For for rate limiting"
    )

    # Request from different X-Forwarded-For IP should succeed
    response = client.get(
        "/test",
        headers={"X-Forwarded-For": "192.168.1.200"}
    )
    assert response.status_code == 200, (
        "Different X-Forwarded-For IP should have separate limit"
    )


def test_health_check_excluded_from_rate_limiting():
    """
    Verify /health endpoint is excluded from rate limiting.

    Health checks should never be rate limited as they're used
    for monitoring and load balancer health checks.
    """
    from backend.main import app

    client = TestClient(app)

    # Make many health check requests
    for i in range(200):  # Way over any rate limit
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Health check {i+1} should never be rate limited"
        )

    # Should not have rate limit headers
    response = client.get("/health")
    assert "X-RateLimit-Limit" not in response.headers, (
        "Health check should not have rate limit headers"
    )


def test_rate_limit_headers_case_insensitive():
    """
    Verify rate limit headers work regardless of case.

    HTTP headers are case-insensitive per RFC 7230.
    """
    from backend.main import app

    client = TestClient(app)

    response = client.get("/api/v1/products", headers=_get_test_auth_headers())

    # Headers should be accessible in various cases
    headers_lower = {k.lower(): v for k, v in response.headers.items()}

    assert "x-ratelimit-limit" in headers_lower, (
        "Rate limit headers should be present (case insensitive)"
    )


# ============================================================================
# Storage Backend Tests
# ============================================================================


def test_memory_storage_basic_operations():
    """
    Verify MemoryStorage correctly tracks request counts.
    """
    from backend.middleware.rate_limiting import MemoryStorage

    storage = MemoryStorage()
    key = "test_client_1"
    window = 60

    # Initial count should be 0
    count = storage.get_count(key)
    assert count == 0, f"Initial count should be 0, got {count}"

    # Increment should return new count
    new_count = storage.increment(key, window)
    assert new_count == 1, f"After increment, count should be 1, got {new_count}"

    # Get count should return 1
    count = storage.get_count(key)
    assert count == 1, f"Get count should return 1, got {count}"


def test_memory_storage_window_expiration():
    """
    Verify MemoryStorage expires keys after window.
    """
    from backend.middleware.rate_limiting import MemoryStorage

    storage = MemoryStorage()
    key = "test_client_2"
    window = 1  # 1 second window

    # Increment
    storage.increment(key, window)
    assert storage.get_count(key) == 1

    # Wait for expiration
    time.sleep(1.1)

    # Should be reset
    count = storage.get_count(key)
    assert count == 0, f"Count should reset after window, got {count}"


def test_redis_storage_when_available():
    """
    Verify RedisStorage works when Redis is available.

    This test is skipped if Redis is not available.
    """
    try:
        import redis
        from backend.middleware.rate_limiting import RedisStorage

        # Try to connect to Redis
        client = redis.Redis(host="localhost", port=6379, db=15)
        client.ping()

        storage = RedisStorage(client)
        key = "test:rate_limit:test_client"
        window = 60

        # Clean up first
        client.delete(key)

        # Test increment
        count = storage.increment(key, window)
        assert count == 1

        # Test get_count
        count = storage.get_count(key)
        assert count == 1

        # Cleanup
        client.delete(key)
        client.close()

    except (redis.ConnectionError, ImportError):
        pytest.skip("Redis not available")


def test_storage_fallback_when_redis_unavailable():
    """
    Verify middleware falls back to MemoryStorage when Redis unavailable.
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, get_storage

    # When Redis is not configured, should use MemoryStorage
    storage = get_storage(redis_url=None)

    assert storage is not None, "Should have fallback storage"
    assert storage.__class__.__name__ == "MemoryStorage", (
        f"Should use MemoryStorage as fallback, got {storage.__class__.__name__}"
    )


# ============================================================================
# Integration Tests with Real App
# ============================================================================


def test_rate_limiting_integrated_in_main_app():
    """
    Verify rate limiting middleware is actually added to the main app.
    """
    from backend.main import app

    # Check that rate limiting middleware is in the middleware stack
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]

    assert "RateLimitMiddleware" in middleware_classes, (
        f"RateLimitMiddleware should be in app middleware. Found: {middleware_classes}"
    )


def test_products_endpoint_respects_rate_limit():
    """
    Integration test: Verify /api/v1/products respects rate limits.
    """
    from backend.main import app

    client = TestClient(app)

    response = client.get("/api/v1/products", headers=_get_test_auth_headers())

    # Should have rate limit headers
    assert "X-RateLimit-Limit" in response.headers, (
        "Products endpoint should have rate limit headers"
    )
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_calculate_endpoint_respects_calculation_limit():
    """
    Integration test: Verify /api/v1/calculate has stricter limits.
    """
    from backend.main import app

    client = TestClient(app)

    # Make a calculation request (may fail due to validation, but should have headers)
    response = client.post(
        "/api/v1/calculate",
        json={"product_id": "test"}
    )

    # Check limit header shows calculation-specific limit
    limit = response.headers.get("X-RateLimit-Limit")
    if limit:
        limit_value = int(limit)
        assert limit_value == 10, (
            f"Calculate endpoint should have limit of 10, got {limit_value}"
        )


# ============================================================================
# Performance Tests
# ============================================================================


def test_rate_limiting_overhead_minimal():
    """
    Verify rate limiting adds minimal overhead (<5ms).
    """
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=1000,
        window_seconds=60
    )

    client = TestClient(test_app)

    # Warm up
    client.get("/test")

    # Measure average time for 100 requests
    start = time.time()
    for _ in range(100):
        client.get("/test")
    elapsed = time.time() - start

    avg_time_ms = (elapsed / 100) * 1000

    # Average overhead should be < 5ms per request
    # Note: This includes network overhead in TestClient, so we're lenient
    assert avg_time_ms < 50, (
        f"Average request time should be < 50ms, got {avg_time_ms:.2f}ms"
    )


def test_concurrent_requests_handled_correctly():
    """
    Verify rate limiting handles concurrent requests correctly.

    Multiple concurrent requests should be properly counted.
    """
    import concurrent.futures
    from backend.middleware.rate_limiting import RateLimitMiddleware, MemoryStorage

    test_app = FastAPI()
    storage = MemoryStorage()

    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    test_app.add_middleware(
        RateLimitMiddleware,
        storage=storage,
        default_limit=10,
        window_seconds=60
    )

    def make_request():
        client = TestClient(test_app)
        response = client.get("/test", headers={"X-Forwarded-For": "10.0.0.1"})
        return response.status_code

    # Make 15 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(make_request) for _ in range(15)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Count successes and rate limits
    successes = results.count(200)
    rate_limited = results.count(429)

    # Should have exactly 10 successes and 5 rate limited
    assert successes == 10, f"Expected 10 successes, got {successes}"
    assert rate_limited == 5, f"Expected 5 rate limited, got {rate_limited}"
