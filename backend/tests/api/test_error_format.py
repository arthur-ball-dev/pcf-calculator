"""
Error response contract (#47).

Every error leaves the API in the single envelope defined in
knowledge/api/api-specifications.md:

    {"error": {"code": str, "message": str, "details": list},
     "request_id": "req_<12 hex>", "timestamp": <ISO-8601 with offset>}

No route, middleware or framework default may emit FastAPI's {"detail": ...}.
Producers covered here: HTTPException with a string detail (route level and the
auth dependencies), HTTPException carrying a pre-built envelope (admin routes),
request validation (pydantic), the domain exception handlers, the rate limiter
and the catch-all 500 handler.
"""

import re
from datetime import datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from backend.api.error_handlers import register_error_handlers
from backend.api.utils.error_responses import create_error_dict
from backend.middleware.rate_limiting import MemoryStorage, RateLimitMiddleware

REQUEST_ID = re.compile(r"^req_[0-9a-f]{12}$")


def assert_envelope(data: dict, *, code: str | None = None, message: str | None = None) -> None:
    """The body is exactly the envelope and nothing else."""
    assert set(data) == {"error", "request_id", "timestamp"}, f"unexpected keys: {sorted(data)}"
    assert set(data["error"]) == {"code", "message", "details"}, (
        f"unexpected error keys: {sorted(data['error'])}"
    )
    assert isinstance(data["error"]["code"], str) and data["error"]["code"]
    assert isinstance(data["error"]["message"], str) and data["error"]["message"]
    assert isinstance(data["error"]["details"], list)
    assert REQUEST_ID.match(data["request_id"]), data["request_id"]
    assert datetime.fromisoformat(data["timestamp"]).tzinfo is not None
    if code is not None:
        assert data["error"]["code"] == code
    if message is not None:
        assert data["error"]["message"] == message


# ============================================================================
# Handler behaviour on a minimal app (no database)
# ============================================================================


class _Body(BaseModel):
    quantity: float
    name: str


@pytest.fixture
def mini_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/status/{code}")
    async def raise_status(code: int):
        raise HTTPException(status_code=code, detail="something went wrong")

    @app.get("/challenge")
    async def challenge():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.get("/prebuilt")
    async def prebuilt():
        raise HTTPException(
            status_code=422,
            detail=create_error_dict(
                code="INVALID_DATA_SOURCE",
                message="Data source not found",
                details=[{"field": "data_source_id", "message": "No data source exists with ID x"}],
            ),
        )

    @app.post("/validated")
    async def validated(body: _Body):
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("secret internals")

    return TestClient(app, raise_server_exceptions=False)


class TestHTTPExceptionEnvelope:
    def test_string_detail_becomes_the_message(self, mini_client):
        response = mini_client.get("/status/404")

        assert response.status_code == 404
        assert_envelope(response.json(), code="NOT_FOUND", message="something went wrong")
        assert response.json()["error"]["details"] == []

    @pytest.mark.parametrize(
        "status_code, expected_code",
        [
            (400, "VALIDATION_ERROR"),
            (401, "UNAUTHORIZED"),
            (403, "FORBIDDEN"),
            (404, "NOT_FOUND"),
            (409, "CONFLICT"),
            (422, "VALIDATION_ERROR"),
            (429, "RATE_LIMITED"),
            (500, "INTERNAL_ERROR"),
            (503, "SERVICE_UNAVAILABLE"),
            (418, "HTTP_ERROR"),
        ],
    )
    def test_status_maps_to_a_default_code(self, mini_client, status_code, expected_code):
        response = mini_client.get(f"/status/{status_code}")

        assert response.status_code == status_code
        assert_envelope(response.json(), code=expected_code)

    def test_headers_are_preserved(self, mini_client):
        response = mini_client.get("/challenge")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert_envelope(response.json(), code="UNAUTHORIZED", message="Not authenticated")

    def test_prebuilt_envelope_is_the_body_not_nested_under_detail(self, mini_client):
        response = mini_client.get("/prebuilt")

        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, code="INVALID_DATA_SOURCE", message="Data source not found")
        assert data["error"]["details"] == [
            {"field": "data_source_id", "message": "No data source exists with ID x"}
        ]


class TestRequestValidationEnvelope:
    def test_missing_fields_are_listed_under_details(self, mini_client):
        response = mini_client.post("/validated", json={})

        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, code="VALIDATION_ERROR", message="Request validation failed")
        fields = {d["field"] for d in data["error"]["details"]}
        assert fields == {"body.quantity", "body.name"}
        for detail in data["error"]["details"]:
            assert set(detail) == {"field", "message", "type"}
            assert detail["type"] == "missing"
            assert detail["message"]

    def test_type_error_names_the_field(self, mini_client):
        response = mini_client.post("/validated", json={"quantity": "abc", "name": "x"})

        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, code="VALIDATION_ERROR")
        assert len(data["error"]["details"]) == 1
        assert data["error"]["details"][0]["field"] == "body.quantity"
        assert "float" in data["error"]["details"][0]["type"]


class TestUnhandledExceptionEnvelope:
    def test_500_is_generic_and_leaks_nothing(self, mini_client):
        response = mini_client.get("/boom")

        assert response.status_code == 500
        assert_envelope(response.json(), code="INTERNAL_ERROR", message="Internal server error")
        assert "secret internals" not in response.text


class TestRateLimitEnvelope:
    def test_429_uses_the_envelope_and_keeps_retry_after(self):
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/limited")
        async def limited():
            return {"ok": True}

        app.add_middleware(
            RateLimitMiddleware, storage=MemoryStorage(), default_limit=1, window_seconds=60
        )
        client = TestClient(app)

        assert client.get("/limited").status_code == 200
        response = client.get("/limited")

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        data = response.json()
        assert_envelope(data, code="RATE_LIMITED")
        assert "rate limit" in data["error"]["message"].lower()


# ============================================================================
# The real application: every producer, end to end
# ============================================================================


class TestApplicationErrorEnvelope:
    def test_unauthenticated_request(self, client):
        response = client.get("/admin/data-sources")

        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"
        assert_envelope(response.json(), code="UNAUTHORIZED", message="Not authenticated")

    def test_forbidden_request(self, authenticated_client):
        response = authenticated_client.get("/admin/data-sources")

        assert response.status_code == 403
        assert_envelope(response.json(), code="FORBIDDEN", message="Insufficient permissions")

    def test_failed_login(self, client):
        response = client.post(
            "/api/v1/auth/login", json={"username": "nobody", "password": "nothing"}
        )

        assert response.status_code == 401
        assert_envelope(response.json(), code="UNAUTHORIZED", message="Invalid username or password")

    def test_product_not_found(self, authenticated_client):
        response = authenticated_client.get("/api/v1/products/does-not-exist")

        assert response.status_code == 404
        data = response.json()
        assert_envelope(data, code="PRODUCT_NOT_FOUND")
        assert data["error"]["details"][0]["field"] == "product_id"

    def test_calculation_not_found(self, authenticated_client):
        response = authenticated_client.get("/api/v1/calculations/does-not-exist")

        assert response.status_code == 404
        data = response.json()
        assert_envelope(data, code="CALCULATION_NOT_FOUND")
        assert data["error"]["details"][0]["field"] == "calculation_id"
        assert set(data["error"]["details"][0]) == {"field", "message"}

    def test_request_validation(self, authenticated_client):
        response = authenticated_client.post("/api/v1/calculate", json={})

        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, code="VALIDATION_ERROR")
        assert "body.product_id" in {d["field"] for d in data["error"]["details"]}

    def test_emission_factor_not_found(self, admin_client):
        # There is no GET by id; DELETE is the route that raises the bare
        # HTTPException(404, "Emission factor not found")
        response = admin_client.delete("/api/v1/emission-factors/does-not-exist")

        assert response.status_code == 404
        assert_envelope(response.json(), code="NOT_FOUND", message="Emission factor not found")

    def test_unknown_route_is_405_or_404_in_the_envelope(self, authenticated_client):
        # A method the route does not implement: the framework's own
        # HTTPException goes through the same handler
        response = authenticated_client.get("/api/v1/emission-factors/does-not-exist")

        assert response.status_code in (404, 405)
        assert_envelope(response.json())
        assert response.json()["error"]["code"] in ("NOT_FOUND", "METHOD_NOT_ALLOWED")
