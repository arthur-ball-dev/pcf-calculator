"""
TASK-QA-P7-031: Updated to use root conftest.py auth fixtures
Test Product Detail API Performance - N+1 Query Detection
TASK-BE-P7-014: Fix N+1 Query in Product Detail Endpoint - Phase A Tests

Test Scenarios:
1. Query count is constant regardless of BOM item count
2. Response time meets SLA (<100ms for product with 10+ BOM items)
3. Response format unchanged (backward compatible)
4. Edge case: Product with no BOM items

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (endpoint has N+1 query pattern)
- Implementation must make tests PASS without modifying tests

Target Performance:
- Query count: O(1) - constant, not O(n) where n = BOM items
- Response time: <100ms for products with 10+ BOM items
"""

import pytest
import time
import logging
from contextlib import contextmanager
from fastapi.testclient import TestClient
from sqlalchemy import text, event
from decimal import Decimal

from backend.models import Base, Product, BillOfMaterials
from backend.main import app
from backend.database.connection import get_db


class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        self.queries = []

    def _on_before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append(statement)

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._on_before_cursor_execute)
        return self

    def __exit__(self, *args):
        event.remove(self.engine, "before_cursor_execute", self._on_before_cursor_execute)

    @property
    def total(self):
        return self.count


@contextmanager
def count_queries(engine):
    counter = QueryCounter(engine)
    with counter:
        yield counter


    session.close()


def create_product(db_session, code, name, **kwargs):
    product = Product(
        code=code,
        name=name,
        unit=kwargs.get("unit", "unit"),
        description=kwargs.get("description"),
        is_finished_product=kwargs.get("is_finished_product", True),
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def create_bom_item(db_session, parent_id, child_id, quantity=1.0, unit="unit", notes=None):
    bom = BillOfMaterials(
        parent_product_id=parent_id,
        child_product_id=child_id,
        quantity=Decimal(str(quantity)),
        unit=unit,
        notes=notes,
    )
    db_session.add(bom)
    db_session.commit()
    db_session.refresh(bom)
    return bom


class TestProductDetailQueryCount:
    def test_query_count_with_5_bom_items(self, db_session, client, db_engine):
        parent = create_product(db_session, "PARENT-5", "Parent Product 5 Children")
        for i in range(5):
            child = create_product(db_session, f"CHILD-5-{i:03d}", f"Child Product {i}", is_finished_product=False)
            create_bom_item(db_session, parent.id, child.id, quantity=1.0)
        with count_queries(db_engine) as counter:
            response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bill_of_materials"]) == 5
        assert counter.total <= 3, f"Expected max 3 queries, got {counter.total}. N+1 query pattern detected!"

    def test_query_count_with_10_bom_items(self, db_session, client, db_engine):
        parent = create_product(db_session, "PARENT-10", "Parent Product 10 Children")
        for i in range(10):
            child = create_product(db_session, f"CHILD-10-{i:03d}", f"Child Product {i}", is_finished_product=False)
            create_bom_item(db_session, parent.id, child.id, quantity=float(i + 1))
        with count_queries(db_engine) as counter:
            response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bill_of_materials"]) == 10
        assert counter.total <= 3, f"Expected max 3 queries for 10 BOM items, got {counter.total}. N+1 detected!"

    def test_query_count_with_20_bom_items(self, db_session, client, db_engine):
        parent = create_product(db_session, "PARENT-20", "Parent Product 20 Children")
        for i in range(20):
            child = create_product(db_session, f"CHILD-20-{i:03d}", f"Child Product {i}", is_finished_product=False)
            create_bom_item(db_session, parent.id, child.id, quantity=1.5)
        with count_queries(db_engine) as counter:
            response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bill_of_materials"]) == 20
        assert counter.total <= 3, f"Expected max 3 queries for 20 BOM items, got {counter.total}. N+1 detected!"

    def test_query_count_does_not_scale_with_bom_size(self, db_session, client, db_engine):
        query_counts = []
        for bom_size in [1, 5, 10]:
            parent = create_product(db_session, f"SCALE-TEST-{bom_size}", f"Product with {bom_size} children")
            for i in range(bom_size):
                child = create_product(db_session, f"SCALE-CHILD-{bom_size}-{i}", f"Child {i}")
                create_bom_item(db_session, parent.id, child.id)
            with count_queries(db_engine) as counter:
                response = authenticated_client.get(f"/api/v1/products/{parent.id}")
            assert response.status_code == 200
            query_counts.append(counter.total)
        max_count = max(query_counts)
        min_count = min(query_counts)
        assert max_count - min_count <= 1, f"Query counts should be constant but vary: {query_counts}"
        assert max_count <= 4, f"Query count too high: {query_counts}"


class TestProductDetailResponseTime:
    @pytest.mark.parametrize("bom_count", [1, 5, 10, 20])
    def test_response_time_within_sla(self, db_session, client, bom_count):
        parent = create_product(db_session, f"PERF-{bom_count}", f"Performance Test {bom_count} Items")
        for i in range(bom_count):
            child = create_product(db_session, f"PERF-CHILD-{bom_count}-{i}", f"Child {i}")
            create_bom_item(db_session, parent.id, child.id, quantity=1.0)
        start_time = time.perf_counter()
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        assert response.status_code == 200
        data = response.json()
        assert len(data["bill_of_materials"]) == bom_count
        assert elapsed_ms < 100, f"Response time {elapsed_ms:.2f}ms exceeded 100ms SLA"

    def test_response_time_does_not_scale_linearly(self, db_session, authenticated_client):
        times = {}
        for bom_count in [5, 15]:
            parent = create_product(db_session, f"LINEAR-{bom_count}", f"Linear Test {bom_count}")
            for i in range(bom_count):
                child = create_product(db_session, f"LINEAR-CHILD-{bom_count}-{i}", f"Child {i}")
                create_bom_item(db_session, parent.id, child.id)
            authenticated_client.get(f"/api/v1/products/{parent.id}")
            start = time.perf_counter()
            response = authenticated_client.get(f"/api/v1/products/{parent.id}")
            elapsed = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            times[bom_count] = elapsed
        ratio = times[15] / times[5] if times[5] > 0 else float("inf")
        assert ratio < 2.0, f"Response time scaled too much: {times[5]:.2f}ms -> {times[15]:.2f}ms. Ratio: {ratio:.2f}"


class TestProductDetailBackwardCompatibility:
    def test_response_format_unchanged(self, db_session, authenticated_client):
        parent = create_product(db_session, "COMPAT-PARENT", "Compatibility Test Parent", description="Test description")
        child = create_product(db_session, "COMPAT-CHILD", "Compatibility Test Child", is_finished_product=False)
        create_bom_item(db_session, parent.id, child.id, quantity=2.5, unit="kg", notes="Test notes")
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "code" in data
        assert "name" in data
        assert "description" in data
        assert "bill_of_materials" in data
        assert data["code"] == "COMPAT-PARENT"
        assert data["name"] == "Compatibility Test Parent"

    def test_bom_item_format_unchanged(self, db_session, authenticated_client):
        parent = create_product(db_session, "BOM-FORMAT-PARENT", "Parent")
        child = create_product(db_session, "BOM-FORMAT-CHILD", "Child Product Name", is_finished_product=False)
        create_bom_item(db_session, parent.id, child.id, quantity=3.75, unit="kg", notes="BOM notes here")
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        assert len(data["bill_of_materials"]) == 1
        bom_item = data["bill_of_materials"][0]
        assert "id" in bom_item
        assert "child_product_id" in bom_item
        assert "child_product_name" in bom_item
        assert "quantity" in bom_item
        assert "unit" in bom_item
        assert "notes" in bom_item
        assert bom_item["child_product_id"] == child.id
        assert bom_item["child_product_name"] == "Child Product Name"
        assert bom_item["quantity"] == 3.75
        assert bom_item["unit"] == "kg"
        assert bom_item["notes"] == "BOM notes here"

    def test_child_product_name_correctly_loaded(self, db_session, authenticated_client):
        parent = create_product(db_session, "NAMES-PARENT", "Parent")
        child_names = ["Aluminum Frame", "Lithium Battery", "Copper Wiring", "Steel Bracket", "Plastic Cover"]
        for i, name in enumerate(child_names):
            child = create_product(db_session, f"NAMES-CHILD-{i}", name, is_finished_product=False)
            create_bom_item(db_session, parent.id, child.id)
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        assert len(data["bill_of_materials"]) == 5
        returned_names = {item["child_product_name"] for item in data["bill_of_materials"]}
        for expected_name in child_names:
            assert expected_name in returned_names, f"Child name {expected_name} not found in response"

    def test_multiple_bom_items_all_fields_populated(self, db_session, authenticated_client):
        parent = create_product(db_session, "MULTI-BOM-PARENT", "Parent")
        for i in range(3):
            child = create_product(db_session, f"MULTI-BOM-CHILD-{i}", f"Component {i}", is_finished_product=False)
            create_bom_item(db_session, parent.id, child.id, quantity=float(i + 1), unit="kg" if i % 2 == 0 else "unit")
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        assert len(data["bill_of_materials"]) == 3
        for item in data["bill_of_materials"]:
            assert item["id"]
            assert item["child_product_id"]
            assert item["child_product_name"]
            assert item["quantity"] > 0


class TestProductDetailEdgeCases:
    def test_product_with_no_bom_items(self, db_session, client, db_engine):
        product = create_product(db_session, "NO-BOM", "Product Without BOM")
        with count_queries(db_engine) as counter:
            response = authenticated_client.get(f"/api/v1/products/{product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["bill_of_materials"] == []
        assert counter.total <= 3

    def test_product_not_found_returns_404(self, authenticated_client):
        response = authenticated_client.get("/api/v1/products/nonexistent-id-12345")
        assert response.status_code == 404

    def test_product_with_single_bom_item(self, db_session, client, db_engine):
        parent = create_product(db_session, "SINGLE-BOM-PARENT", "Parent")
        child = create_product(db_session, "SINGLE-BOM-CHILD", "Only Child", is_finished_product=False)
        create_bom_item(db_session, parent.id, child.id, quantity=1.0)
        with count_queries(db_engine) as counter:
            response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bill_of_materials"]) == 1
        assert data["bill_of_materials"][0]["child_product_name"] == "Only Child"
        assert counter.total <= 3

    def test_bom_with_null_optional_fields(self, db_session, authenticated_client):
        parent = create_product(db_session, "NULL-FIELDS-PARENT", "Parent")
        child = create_product(db_session, "NULL-FIELDS-CHILD", "Child")
        bom = BillOfMaterials(
            parent_product_id=parent.id,
            child_product_id=child.id,
            quantity=Decimal("1.0"),
            unit=None,
            notes=None,
        )
        db_session.add(bom)
        db_session.commit()
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        assert response.status_code == 200
        assert len(data["bill_of_materials"]) == 1
        bom_item = data["bill_of_materials"][0]
        assert bom_item["unit"] is None or bom_item["unit"] == ""
        assert bom_item["notes"] is None


class TestProductDetailDataIntegrity:
    def test_bom_quantities_accurate(self, db_session, authenticated_client):
        parent = create_product(db_session, "QTY-PARENT", "Parent")
        quantities = [0.5, 1.25, 10.0, 100.0, 0.001]
        for i, qty in enumerate(quantities):
            child = create_product(db_session, f"QTY-CHILD-{i}", f"Child {i}")
            create_bom_item(db_session, parent.id, child.id, quantity=qty)
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        returned_quantities = sorted([item["quantity"] for item in data["bill_of_materials"]])
        expected_quantities = sorted(quantities)
        assert returned_quantities == expected_quantities

    def test_each_bom_item_has_correct_child_name(self, db_session, authenticated_client):
        parent = create_product(db_session, "MATCH-PARENT", "Parent")
        child_data = [("MATCH-C1", "Component Alpha"), ("MATCH-C2", "Component Beta"), ("MATCH-C3", "Component Gamma")]
        expected_mapping = {}
        for code, name in child_data:
            child = create_product(db_session, code, name)
            create_bom_item(db_session, parent.id, child.id)
            expected_mapping[child.id] = name
        response = authenticated_client.get(f"/api/v1/products/{parent.id}")
        data = response.json()
        for item in data["bill_of_materials"]:
            child_id = item["child_product_id"]
            expected_name = expected_mapping[child_id]
            assert item["child_product_name"] == expected_name
