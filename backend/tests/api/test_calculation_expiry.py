"""
Calculation result rows expire after an hour (TASK-BE-P9-015, #196).

A pcf_calculations row is needed only while the browser polls GET /calculations/{id}, a few
seconds; nothing reads it afterwards. Each POST /calculate deletes rows older than an hour
(their calculation_details go with them, ON DELETE CASCADE), so with #195 the user's edited BOM
rows in the breakdown don't outlive the session. Ages are measured on the database clock.
"""

from datetime import timedelta

import pytest
from sqlalchemy import func

from backend.models import CalculationDetail, PCFCalculation, Product, generate_uuid


@pytest.fixture
def product(db_session):
    p = Product(id=generate_uuid(), code=f"EXP-{generate_uuid()[:10]}", name="Expiry Product",
                unit="unit", is_finished_product=True)
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture
def add_calculation(db_session, product):
    def _add(age: timedelta) -> PCFCalculation:
        calc = PCFCalculation(id=generate_uuid(), product_id=product.id, calculation_type="cradle_to_gate",
                              status="completed", total_co2e_kg=1, created_at=func.now() - age)
        db_session.add(calc)
        db_session.commit()
        return calc
    return _add


def _exists(db_session, calc_id) -> bool:
    db_session.expire_all()
    return db_session.get(PCFCalculation, calc_id) is not None


def test_a_new_calculation_deletes_rows_older_than_an_hour(client, db_session, product, add_calculation):
    old = add_calculation(timedelta(hours=2)).id
    recent = add_calculation(timedelta(minutes=10)).id

    response = client.post("/api/v1/calculate", json={"product_id": product.id})

    assert response.status_code == 202
    assert not _exists(db_session, old)
    assert _exists(db_session, recent)
    assert _exists(db_session, response.json()["calculation_id"])


def test_a_row_just_under_an_hour_old_is_kept(client, db_session, product, add_calculation):
    almost = add_calculation(timedelta(minutes=59)).id
    client.post("/api/v1/calculate", json={"product_id": product.id})
    assert _exists(db_session, almost)


def test_an_expired_rows_details_go_with_it(client, db_session, product, add_calculation):
    old = add_calculation(timedelta(hours=3))
    detail = CalculationDetail(id=generate_uuid(), calculation_id=old.id, component_name="Old Part")
    db_session.add(detail)
    db_session.commit()
    detail_id = detail.id

    client.post("/api/v1/calculate", json={"product_id": product.id})

    db_session.expire_all()
    assert db_session.get(CalculationDetail, detail_id) is None


def test_a_rejected_request_deletes_nothing(client, db_session, add_calculation):
    old = add_calculation(timedelta(hours=2)).id
    response = client.post("/api/v1/calculate", json={"product_id": generate_uuid()})
    assert response.status_code == 404
    assert _exists(db_session, old)


def test_an_expired_calculation_is_not_found(client, db_session, product, add_calculation):
    old = add_calculation(timedelta(hours=2)).id
    client.post("/api/v1/calculate", json={"product_id": product.id})
    assert client.get(f"/api/v1/calculations/{old}").status_code == 404
