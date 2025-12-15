"""
Tests for admin data source sync endpoint with real connector integration.

TASK-BE-P7-002: Activate Data Connector Admin Endpoints

TDD Tests for:
- Connector registry functionality
- POST /admin/data-sources/{id}/sync with real connectors
- Background task execution
- Error handling for unknown data sources

Test scenarios from TASK-BE-P7-002_SPEC:
1. EPA sync trigger
2. DEFRA sync trigger
3. Exiobase sync trigger
4. Unknown connector error handling
5. Connector registry lookup
"""

import uuid
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models import Base, DataSource, DataSyncLog


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
def epa_data_source(db_session: Session) -> DataSource:
    """Create EPA data source matching seeded data."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="EPA GHG Emission Factors Hub",
        source_type="file",
        base_url="https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        sync_frequency="biweekly",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def defra_data_source(db_session: Session) -> DataSource:
    """Create DEFRA data source matching seeded data."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="DEFRA Conversion Factors",
        source_type="file",
        base_url="https://www.gov.uk/government/publications",
        sync_frequency="biweekly",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def exiobase_data_source(db_session: Session) -> DataSource:
    """Create Exiobase data source matching seeded data."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="Exiobase",
        source_type="database",
        base_url="https://zenodo.org/record/5589597",
        sync_frequency="monthly",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def unknown_data_source(db_session: Session) -> DataSource:
    """Create a data source with no registered connector."""
    data_source = DataSource(
        id=uuid.uuid4().hex,
        name="Unknown Custom Source",
        source_type="api",
        base_url="https://custom.example.com",
        sync_frequency="manual",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


@pytest.fixture
def app_with_db(db_session: Session) -> FastAPI:
    """Create FastAPI app with database dependency override."""
    from backend.main import app
    from backend.database.connection import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_with_db: FastAPI) -> TestClient:
    """Create test client with database override."""
    return TestClient(app_with_db)


# ============================================================================
# Test 5: Connector Registry Lookup
# ============================================================================


class TestConnectorRegistry:
    """Tests for connector registry functionality."""

    def test_connector_registry_returns_epa_class(self):
        """
        Test: get_connector_class returns EPAEmissionFactorsIngestion for EPA name.

        Input: "EPA GHG Emission Factors Hub"
        Expected: EPAEmissionFactorsIngestion class
        """
        from backend.services.data_ingestion.registry import get_connector_class
        from backend.services.data_ingestion.epa_ingestion import (
            EPAEmissionFactorsIngestion
        )

        connector_class = get_connector_class("EPA GHG Emission Factors Hub")
        assert connector_class == EPAEmissionFactorsIngestion

    def test_connector_registry_returns_defra_class(self):
        """
        Test: get_connector_class returns DEFRAEmissionFactorsIngestion for DEFRA name.

        Input: "DEFRA Conversion Factors"
        Expected: DEFRAEmissionFactorsIngestion class
        """
        from backend.services.data_ingestion.registry import get_connector_class
        from backend.services.data_ingestion.defra_ingestion import (
            DEFRAEmissionFactorsIngestion
        )

        connector_class = get_connector_class("DEFRA Conversion Factors")
        assert connector_class == DEFRAEmissionFactorsIngestion

    def test_connector_registry_returns_exiobase_class(self):
        """
        Test: get_connector_class returns ExiobaseEmissionFactorsIngestion for Exiobase name.

        Input: "Exiobase"
        Expected: ExiobaseEmissionFactorsIngestion class
        """
        from backend.services.data_ingestion.registry import get_connector_class
        from backend.services.data_ingestion.exiobase_ingestion import (
            ExiobaseEmissionFactorsIngestion
        )

        connector_class = get_connector_class("Exiobase")
        assert connector_class == ExiobaseEmissionFactorsIngestion

    def test_connector_registry_raises_for_unknown(self):
        """
        Test: get_connector_class raises ValueError for unknown data source.

        Input: "Unknown Source"
        Expected: ValueError with message containing "No connector registered"
        """
        from backend.services.data_ingestion.registry import get_connector_class

        with pytest.raises(ValueError, match="No connector registered"):
            get_connector_class("Unknown Source")

    def test_is_connector_available_returns_true_for_known(self):
        """
        Test: is_connector_available returns True for known data sources.
        """
        from backend.services.data_ingestion.registry import is_connector_available

        assert is_connector_available("EPA GHG Emission Factors Hub") is True
        assert is_connector_available("DEFRA Conversion Factors") is True
        assert is_connector_available("Exiobase") is True

    def test_is_connector_available_returns_false_for_unknown(self):
        """
        Test: is_connector_available returns False for unknown data sources.
        """
        from backend.services.data_ingestion.registry import is_connector_available

        assert is_connector_available("Unknown Source") is False
        assert is_connector_available("Custom API") is False


# ============================================================================
# Test 1: EPA Sync Trigger
# ============================================================================


class TestEPASyncTrigger:
    """Tests for EPA data source sync trigger."""

    def test_sync_trigger_epa_returns_202(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: POST /admin/data-sources/{epa_id}/sync returns 202 Accepted.

        Input:
            - data_sources table has EPA entry
            - POST /admin/data-sources/{epa_id}/sync
        Expected:
            - Returns 202 Accepted
            - Response contains task_id
            - Response contains sync_log_id
            - Response status is "queued"
        """
        # Mock the background task execution to avoid actual HTTP calls
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(f"/admin/data-sources/{epa_data_source.id}/sync")

            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
            assert "sync_log_id" in data
            assert data["status"] == "queued"
            assert data["data_source"]["name"] == "EPA GHG Emission Factors Hub"

    def test_sync_trigger_epa_creates_sync_log(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: EPA sync trigger creates DataSyncLog entry.

        Input: POST /admin/data-sources/{epa_id}/sync
        Expected: DataSyncLog entry created with status "queued"
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(f"/admin/data-sources/{epa_data_source.id}/sync")

            assert response.status_code == 202
            data = response.json()

            # Verify sync log was created
            sync_log = db_session.query(DataSyncLog).filter(
                DataSyncLog.id == data["sync_log_id"]
            ).first()

            assert sync_log is not None
            assert sync_log.data_source_id == epa_data_source.id
            assert sync_log.status == "queued"
            assert sync_log.sync_type == "manual"


# ============================================================================
# Test 2: DEFRA Sync Trigger
# ============================================================================


class TestDEFRASyncTrigger:
    """Tests for DEFRA data source sync trigger."""

    def test_sync_trigger_defra_returns_202(
        self,
        client: TestClient,
        defra_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: POST /admin/data-sources/{defra_id}/sync returns 202 Accepted.

        Input:
            - data_sources table has DEFRA entry
            - POST /admin/data-sources/{defra_id}/sync
        Expected:
            - Returns 202 Accepted
            - DEFRAEmissionFactorsIngestion connector will be invoked
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(f"/admin/data-sources/{defra_data_source.id}/sync")

            assert response.status_code == 202
            data = response.json()
            assert data["data_source"]["name"] == "DEFRA Conversion Factors"


# ============================================================================
# Test 3: Exiobase Sync Trigger
# ============================================================================


class TestExiobaseSyncTrigger:
    """Tests for Exiobase data source sync trigger."""

    def test_sync_trigger_exiobase_returns_202(
        self,
        client: TestClient,
        exiobase_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: POST /admin/data-sources/{exiobase_id}/sync returns 202 Accepted.

        Input:
            - data_sources table has Exiobase entry
            - POST /admin/data-sources/{exiobase_id}/sync
        Expected:
            - Returns 202 Accepted
            - ExiobaseEmissionFactorsIngestion connector will be invoked
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(f"/admin/data-sources/{exiobase_data_source.id}/sync")

            assert response.status_code == 202
            data = response.json()
            assert data["data_source"]["name"] == "Exiobase"


# ============================================================================
# Test 4: Unknown Connector Error
# ============================================================================


class TestUnknownConnectorError:
    """Tests for error handling with unknown data sources."""

    def test_sync_trigger_unknown_connector_returns_422(
        self,
        client: TestClient,
        unknown_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: POST /admin/data-sources/{id}/sync with unknown source returns 422.

        Input:
            - data_sources table has entry with name "Unknown Custom Source"
            - POST /admin/data-sources/{id}/sync
        Expected:
            - Returns 422 Unprocessable Entity
            - Error message indicates no connector registered
        """
        response = client.post(f"/admin/data-sources/{unknown_data_source.id}/sync")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check error message contains reference to no connector
        error_detail = data["detail"]
        if isinstance(error_detail, dict):
            message = error_detail.get("error", {}).get("message", "").lower()
        else:
            message = str(error_detail).lower()
        assert "connector" in message or "no connector" in message


# ============================================================================
# Test: Background Execution Verification
# ============================================================================


class TestBackgroundExecution:
    """Tests for verifying background execution behavior."""

    def test_sync_returns_immediately_without_blocking(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: Sync endpoint returns immediately (non-blocking).

        The endpoint should return 202 Accepted immediately,
        not wait for the actual sync to complete.
        """
        import time

        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            # Simulate slow connector
            mock_execute.return_value = None

            start_time = time.time()
            response = client.post(f"/admin/data-sources/{epa_data_source.id}/sync")
            elapsed_time = time.time() - start_time

            assert response.status_code == 202
            # Should return quickly (< 1 second) even though real sync would take minutes
            assert elapsed_time < 1.0

    def test_sync_calls_execute_sync_in_background(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: Sync trigger calls execute_sync_in_background with correct parameters.
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(f"/admin/data-sources/{epa_data_source.id}/sync")

            assert response.status_code == 202
            # Verify execute_sync_in_background was called
            assert mock_execute.called
            # Get the call arguments
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs["data_source_id"] == epa_data_source.id
            assert call_kwargs["data_source_name"] == "EPA GHG Emission Factors Hub"
            assert "sync_log_id" in call_kwargs


# ============================================================================
# Test: Force Refresh and Dry Run Options
# ============================================================================


class TestSyncOptions:
    """Tests for sync trigger options."""

    def test_sync_with_force_refresh(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: Sync trigger with force_refresh option.
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(
                f"/admin/data-sources/{epa_data_source.id}/sync",
                json={"force_refresh": True}
            )

            assert response.status_code == 202

            # Verify sync log metadata includes force_refresh
            data = response.json()
            sync_log = db_session.query(DataSyncLog).filter(
                DataSyncLog.id == data["sync_log_id"]
            ).first()
            assert sync_log.sync_metadata.get("force_refresh") is True

    def test_sync_with_dry_run(
        self,
        client: TestClient,
        epa_data_source: DataSource,
        db_session: Session
    ):
        """
        Test: Sync trigger with dry_run option.
        """
        with patch(
            'backend.api.routes.admin.data_sources.execute_sync_in_background'
        ) as mock_execute:
            mock_execute.return_value = None

            response = client.post(
                f"/admin/data-sources/{epa_data_source.id}/sync",
                json={"dry_run": True}
            )

            assert response.status_code == 202
            data = response.json()
            assert "dry run" in data["message"].lower()

            # Verify sync log metadata includes dry_run
            sync_log = db_session.query(DataSyncLog).filter(
                DataSyncLog.id == data["sync_log_id"]
            ).first()
            assert sync_log.sync_metadata.get("dry_run") is True
