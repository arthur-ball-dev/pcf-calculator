"""
Tests for GET /health/ready.

/health answers without touching the database, so it stayed healthy through a
production outage where every connection failed authentication. /health/ready runs
a real query and reports failure with a 503.
"""

import asyncio
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes import health


class FakeSession:
    def __init__(self, error: Exception | None = None, delay: float = 0) -> None:
        self.error = error
        self.delay = delay
        self.statements: list[str] = []

    async def execute(self, statement: object) -> None:
        self.statements.append(str(statement))
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(health.router)
    return TestClient(app)


def use_session(monkeypatch: pytest.MonkeyPatch, session: FakeSession) -> None:
    @asynccontextmanager
    async def fake_get_async_session():
        yield session

    monkeypatch.setattr(health, "get_async_session", fake_get_async_session)


def test_ready_when_query_succeeds(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    use_session(monkeypatch, session)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert session.statements == ["SELECT 1"]


def test_unavailable_when_query_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    use_session(monkeypatch, FakeSession(error=RuntimeError("password authentication failed")))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_failure_detail_is_not_exposed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    detail = 'connection to server at "10.0.0.1" failed for user "postgres"'
    use_session(monkeypatch, FakeSession(error=RuntimeError(detail)))

    response = client.get("/health/ready")

    assert "postgres" not in response.text
    assert "10.0.0.1" not in response.text


def test_unavailable_when_session_cannot_be_opened(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    @asynccontextmanager
    async def broken_get_async_session():
        raise RuntimeError("pool exhausted")
        yield

    monkeypatch.setattr(health, "get_async_session", broken_get_async_session)

    assert client.get("/health/ready").status_code == 503


def test_unavailable_when_query_hangs(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "READINESS_TIMEOUT_SECONDS", 0.01)
    use_session(monkeypatch, FakeSession(delay=5))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
