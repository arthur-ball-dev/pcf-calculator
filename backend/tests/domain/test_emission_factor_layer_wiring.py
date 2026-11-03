"""
Emission factor routes on the domain layer (issue #19).

The repository runs on a real session, the service on a stub repository, and the
routes against a replaced service.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from backend.api.dependencies import get_emission_factor_service
from backend.auth.dependencies import require_admin
from backend.domain.entities.emission_factor import (
    DataSourceLicense,
    EmissionFactor,
    EmissionFactorFilters,
    EmissionFactorPage,
    NewEmissionFactor,
)
from backend.domain.entities.errors import (
    DuplicateEmissionFactorError,
    EmissionFactorNotFoundError,
)
from backend.domain.repositories.interfaces import EmissionFactorRepository
from backend.domain.services.emission_factor_service import EmissionFactorService
from backend.infrastructure.repositories.sqlalchemy_emission_factor_repository import (
    SQLAlchemyEmissionFactorRepository,
)
from backend.models import DataSource
from backend.models import EmissionFactor as EmissionFactorModel

FACTORS = "/api/v1/emission-factors"
CREATED = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _new(**fields):
    defaults = dict(
        activity_name="Wire activity", co2e_factor=1.25, unit="kg", data_source="WIRE",
        geography="GLO", reference_year=2025, data_quality_rating=0.5,
    )
    return NewEmissionFactor(**{**defaults, **fields})


def _stored(**fields):
    defaults = dict(
        id="only-in-fake", activity_name="Fake", co2e_factor=2.5, unit="kg",
        data_source="WIRE", geography="GLO", created_at=CREATED,
    )
    return EmissionFactor(**{**defaults, **fields})


@pytest.fixture
def repo(db_session):
    return SQLAlchemyEmissionFactorRepository(db_session)


class TestRepository:
    def test_create_and_list(self, repo):
        created = repo.create(_new())

        assert created.id
        assert created.co2e_factor == 1.25
        assert created.data_quality_rating == 0.5
        assert created.created_at is not None
        page = repo.list_all(EmissionFactorFilters(data_source="WIRE"))
        assert [f.id for f in page.items] == [created.id]
        assert page.total == 1

    def test_list_filters(self, repo):
        repo.create(_new(activity_name="Wire steel", unit="kg", geography="US"))
        repo.create(_new(activity_name="Wire oil", unit="L", geography="GLO"))

        def names(**filters):
            found = repo.list_all(EmissionFactorFilters(data_source="WIRE", **filters)).items
            return {f.activity_name for f in found}

        assert names(unit="L") == {"Wire oil"}
        assert names(geography="US") == {"Wire steel"}
        assert names(activity_name="STEEL") == {"Wire steel"}

    def test_total_ignores_the_page(self, repo):
        repo.create(_new(activity_name="Wire one"))
        repo.create(_new(activity_name="Wire two"))

        page = repo.list_all(EmissionFactorFilters(data_source="WIRE"), limit=1)

        assert len(page.items) == 1
        assert page.total == 2

    def test_exists(self, repo):
        repo.create(_new())

        assert repo.exists("Wire activity", "WIRE", "GLO", 2025) is True
        assert repo.exists("Wire activity", "WIRE", "GLO", 2024) is False

    def test_update_skips_none_values(self, repo):
        created = repo.create(_new())

        updated = repo.update(created.id, {"co2e_factor": 3.5, "unit": "L", "geography": None})

        assert (updated.co2e_factor, updated.unit, updated.geography) == (3.5, "L", "GLO")

    def test_update_with_no_changes(self, repo):
        created = repo.create(_new())

        assert repo.update(created.id, {}).co2e_factor == 1.25

    def test_update_missing(self, repo):
        assert repo.update("wire-none", {"unit": "L"}) is None

    def test_delete(self, repo, db_session):
        created = repo.create(_new())

        assert repo.delete(created.id) is True
        assert db_session.get(EmissionFactorModel, created.id) is None
        assert repo.delete(created.id) is False

    def test_licenses_only_active_with_defaults(self, repo, db_session):
        db_session.add_all(
            [
                DataSource(name="Wire active", source_type="file", is_active=True, allows_commercial_use=None),
                DataSource(name="Wire inactive", source_type="file", is_active=False),
            ]
        )
        db_session.commit()

        licenses = {item.name: item for item in repo.list_active_licenses()}

        assert "Wire inactive" not in licenses
        assert licenses["Wire active"].allows_commercial_use is True
        assert licenses["Wire active"].requires_attribution in (True, False)


class TestService:
    @pytest.fixture
    def stub(self):
        return MagicMock(spec=EmissionFactorRepository)

    def test_duplicate_is_rejected_before_create(self, stub):
        stub.exists.return_value = True

        with pytest.raises(DuplicateEmissionFactorError) as exc_info:
            EmissionFactorService(stub).create_factor(_new())

        stub.exists.assert_called_once_with("Wire activity", "WIRE", "GLO", 2025)
        stub.create.assert_not_called()
        assert "already exists" in str(exc_info.value)

    def test_create(self, stub):
        stub.exists.return_value = False
        stub.create.return_value = _stored()

        assert EmissionFactorService(stub).create_factor(_new()) == _stored()

    def test_update_missing_raises(self, stub):
        stub.update.return_value = None

        with pytest.raises(EmissionFactorNotFoundError):
            EmissionFactorService(stub).update_factor("x", {})

    def test_delete_missing_raises(self, stub):
        stub.delete.return_value = False

        with pytest.raises(EmissionFactorNotFoundError):
            EmissionFactorService(stub).delete_factor("x")


class TestRoutesUseTheService:
    @pytest.fixture
    def service(self, client):
        from backend.main import app

        fake = MagicMock(spec=EmissionFactorService)
        app.dependency_overrides[get_emission_factor_service] = lambda: fake
        app.dependency_overrides[require_admin] = lambda: MagicMock()
        return fake

    def test_list(self, client, service):
        service.list_factors.return_value = EmissionFactorPage(items=[_stored()], total=42)

        body = client.get(f"{FACTORS}?limit=7&offset=2&unit=kg&activity_name=st").json()

        assert body["total"] == 42
        assert body["items"][0]["id"] == "only-in-fake"
        assert body["items"][0]["created_at"] == CREATED.isoformat()
        service.list_factors.assert_called_once_with(
            EmissionFactorFilters(unit="kg", activity_name="st"), limit=7, offset=2
        )

    def test_create(self, client, service):
        service.create_factor.return_value = _stored()

        response = client.post(
            FACTORS,
            json={"activity_name": "A", "co2e_factor": 1.5, "unit": "kg", "data_source": "S"},
        )

        assert response.status_code == 201
        assert response.json()["id"] == "only-in-fake"
        assert service.create_factor.call_args.args[0].activity_name == "A"

    def test_duplicate_is_409(self, client, service):
        service.create_factor.side_effect = DuplicateEmissionFactorError("A", "S", "GLO", None)

        response = client.post(
            FACTORS,
            json={"activity_name": "A", "co2e_factor": 1.5, "unit": "kg", "data_source": "S"},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["error"]["message"]

    def test_update_sends_only_the_fields_given(self, client, service):
        service.update_factor.return_value = _stored()

        response = client.put(f"{FACTORS}/x", json={"unit": "L"})

        assert response.status_code == 200
        service.update_factor.assert_called_once_with("x", {"unit": "L"})

    def test_update_missing_is_404(self, client, service):
        service.update_factor.side_effect = EmissionFactorNotFoundError(factor_id="x")

        response = client.put(f"{FACTORS}/x", json={"unit": "L"})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
        assert response.json()["error"]["message"] == "Emission factor not found"

    def test_delete(self, client, service):
        assert client.delete(f"{FACTORS}/x").status_code == 204
        service.delete_factor.assert_called_once_with("x")

    def test_delete_missing_is_404(self, client, service):
        service.delete_factor.side_effect = EmissionFactorNotFoundError(factor_id="x")

        assert client.delete(f"{FACTORS}/x").status_code == 404

    def test_attributions(self, client, service):
        service.list_licenses.return_value = [DataSourceLicense(id="d", name="Only in fake")]

        body = client.get("/api/v1/attributions").json()

        assert body["attributions"][0]["name"] == "Only in fake"
