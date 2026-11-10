"""
/health/ready is rate limited, while /health stays exempt.

/health/ready runs a database query and is public, so it must not sit inside the
blanket /health exemption. Railway's health check uses /health, which stays exempt.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware.rate_limiting import MemoryStorage, RateLimitMiddleware


def _client(**middleware):
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/health/ready")
    def ready():
        return {"status": "ready"}

    @app.get("/health/db")
    def db():
        return {"status": "healthy"}

    app.add_middleware(RateLimitMiddleware, storage=MemoryStorage(), **middleware)
    return TestClient(app)


def test_an_explicit_limit_overrides_an_excluded_prefix():
    client = _client(default_limit=100, endpoint_limits={"/health/ready": 2}, excluded_paths=["/health"])

    statuses = [client.get("/health/ready").status_code for _ in range(3)]

    assert statuses == [200, 200, 429]


def test_the_excluded_path_itself_stays_unlimited():
    client = _client(default_limit=1, endpoint_limits={"/health/ready": 2}, excluded_paths=["/health"])

    assert all(client.get("/health").status_code == 200 for _ in range(5))


def test_other_paths_under_the_prefix_stay_excluded():
    client = _client(default_limit=1, endpoint_limits={"/health/ready": 2}, excluded_paths=["/health"])

    assert all(client.get("/health/db").status_code == 200 for _ in range(5))


def test_the_app_limits_readiness_and_exempts_health():
    from backend.config import settings
    from backend.main import app, rate_limit_storage

    rate_limit_storage.clear()
    middleware = next(m for m in app.user_middleware if m.cls is RateLimitMiddleware)

    assert middleware.kwargs["endpoint_limits"]["/health/ready"] == settings.RATE_LIMIT_READINESS
    assert "/health" in middleware.kwargs["excluded_paths"]
