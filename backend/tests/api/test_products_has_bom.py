"""
TASK-FE-P8-001: Tests for has_bom Query Parameter on Product Search API

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (has_bom parameter not implemented)
- Implementation must make tests PASS without modifying tests

Test Scenarios:
1. Filter products with BOM (has_bom=true returns only products with BOM entries)
2. Filter products without BOM (has_bom=false returns only products without BOM entries)
3. No filter returns all products (has_bom not specified)
4. Combined filters work correctly (has_bom + is_finished_product + query)
5. Edge cases (empty results, invalid values)

API Contract:
- Endpoint: GET /api/v1/products/search
- New Parameter: has_bom (optional boolean)
  - true: Products that ARE a parent in bill_of_materials
  - false: Products that are NOT a parent in bill_of_materials
  - undefined/omitted: Return all products regardless of BOM status

Expected Response Format:
{
    "items": [{"id": "...", "name": "...", "has_bom": true/false, ...}],
    "total": 22,
    "limit": 50,
    "offset": 0,
    "has_more": false
}
"""

import pytest
from decimal import Decimal

from backend.models import Product, BillOfMaterials


def create_product(db_session, code, name, **kwargs):
    """Helper function to create a product in the database."""
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


def create_bom_entry(db_session, parent_id, child_id, quantity=1.0):
    """Helper function to create a BOM entry in the database."""
    bom = BillOfMaterials(
        parent_product_id=parent_id,
        child_product_id=child_id,
        quantity=Decimal(str(quantity)),
        unit="unit",
    )
    db_session.add(bom)
    db_session.commit()
    db_session.refresh(bom)
    return bom


class TestHasBomFilterHappyPath:
    """Test Scenario 1: Filter products with BOM (has_bom=true)"""

    def test_search_has_bom_true_returns_products_with_bom(
        self, db_session, authenticated_client
    ):
        """
        Given: Products exist, some with BOM entries and some without
        When: GET /api/v1/products/search?has_bom=true
        Then: Only products that are parents in bill_of_materials are returned
        """
        # Arrange: Create products with and without BOM
        parent_product = create_product(
            db_session, "PARENT-001", "Electric Motor Assembly"
        )
        child_product = create_product(
            db_session, "CHILD-001", "Copper Wiring", is_finished_product=False
        )
        standalone_product = create_product(
            db_session, "STANDALONE-001", "Simple Widget"
        )

        # Create BOM entry: parent_product -> child_product
        create_bom_entry(db_session, parent_product.id, child_product.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

        # Only parent_product should be returned (it has BOM)
        returned_ids = [item["id"] for item in data["items"]]
        assert parent_product.id in returned_ids
        assert standalone_product.id not in returned_ids
        assert child_product.id not in returned_ids

    def test_search_has_bom_true_returns_all_required_fields(
        self, db_session, authenticated_client
    ):
        """
        Given: Products with BOM exist
        When: GET /api/v1/products/search?has_bom=true
        Then: Response contains all required fields per API contract
        """
        # Arrange
        parent = create_product(db_session, "FIELD-PARENT", "Parent Product")
        child = create_product(
            db_session, "FIELD-CHILD", "Child Product", is_finished_product=False
        )
        create_bom_entry(db_session, parent.id, child.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        # Check item fields
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "id" in item
            assert "name" in item
            assert "code" in item


class TestHasBomFalseFilter:
    """Test Scenario 4: has_bom=false returns products without BOM"""

    def test_search_has_bom_false_returns_products_without_bom(
        self, db_session, authenticated_client
    ):
        """
        Given: Products exist, some with BOM entries and some without
        When: GET /api/v1/products/search?has_bom=false
        Then: Only products that are NOT parents in bill_of_materials are returned
        """
        # Arrange
        parent_product = create_product(db_session, "PARENT-002", "Assembly Product")
        child_product = create_product(
            db_session, "CHILD-002", "Raw Material", is_finished_product=False
        )
        standalone_product = create_product(
            db_session, "STANDALONE-002", "No BOM Product"
        )

        # Create BOM entry: parent_product -> child_product
        create_bom_entry(db_session, parent_product.id, child_product.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": False, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # parent_product should NOT be returned (it has BOM)
        assert parent_product.id not in returned_ids
        # standalone_product should be returned (no BOM)
        assert standalone_product.id in returned_ids
        # child_product should be returned (not a parent in any BOM)
        assert child_product.id in returned_ids

    def test_search_has_bom_false_excludes_all_bom_parents(
        self, db_session, authenticated_client
    ):
        """
        Given: Multiple products with BOMs exist
        When: GET /api/v1/products/search?has_bom=false
        Then: None of the products that have BOM entries are returned
        """
        # Arrange: Create multiple products with BOMs
        products_with_bom = []
        for i in range(3):
            parent = create_product(db_session, f"BOM-PARENT-{i}", f"BOM Parent {i}")
            child = create_product(
                db_session, f"BOM-CHILD-{i}", f"BOM Child {i}", is_finished_product=False
            )
            create_bom_entry(db_session, parent.id, child.id)
            products_with_bom.append(parent.id)

        # Create standalone product
        standalone = create_product(db_session, "STANDALONE-003", "Standalone")

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": False, "limit": 100}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        returned_ids = [item["id"] for item in data["items"]]

        # None of the BOM parents should be in results
        for parent_id in products_with_bom:
            assert parent_id not in returned_ids

        # Standalone should be in results
        assert standalone.id in returned_ids


class TestNoHasBomFilter:
    """Test Scenario 2: Unfiltered returns all products"""

    def test_search_no_has_bom_returns_all_products(
        self, db_session, authenticated_client
    ):
        """
        Given: Products exist, some with BOM entries and some without
        When: GET /api/v1/products/search (no has_bom parameter)
        Then: All products are returned regardless of BOM status
        """
        # Arrange
        parent = create_product(db_session, "ALL-PARENT", "Parent Product")
        child = create_product(
            db_session, "ALL-CHILD", "Child Product", is_finished_product=False
        )
        standalone = create_product(db_session, "ALL-STANDALONE", "Standalone Product")
        create_bom_entry(db_session, parent.id, child.id)

        # Act: No has_bom parameter
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"limit": 100}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # All three products should be returned
        assert parent.id in returned_ids
        assert child.id in returned_ids
        assert standalone.id in returned_ids


class TestCombinedFilters:
    """Test Scenario 3: Combined filters work correctly"""

    def test_search_has_bom_with_is_finished_product(
        self, db_session, authenticated_client
    ):
        """
        Given: Mix of finished and non-finished products with/without BOM
        When: GET /api/v1/products/search?has_bom=true&is_finished_product=true
        Then: Only finished products with BOM are returned
        """
        # Arrange
        finished_with_bom = create_product(
            db_session, "COMBO-FIN-BOM", "Finished With BOM", is_finished_product=True
        )
        finished_no_bom = create_product(
            db_session, "COMBO-FIN-NOBOM", "Finished No BOM", is_finished_product=True
        )
        raw_material = create_product(
            db_session, "COMBO-RAW", "Raw Material", is_finished_product=False
        )

        create_bom_entry(db_session, finished_with_bom.id, raw_material.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "is_finished_product": True, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # Only finished_with_bom should be returned
        assert finished_with_bom.id in returned_ids
        assert finished_no_bom.id not in returned_ids
        assert raw_material.id not in returned_ids

    def test_search_has_bom_with_query(
        self, db_session, authenticated_client
    ):
        """
        Given: Multiple products with BOM
        When: GET /api/v1/products/search?has_bom=true&query=motor
        Then: Only products with BOM matching the query are returned
        """
        # Arrange
        motor_with_bom = create_product(
            db_session, "MOTOR-BOM", "Electric Motor Assembly"
        )
        widget_with_bom = create_product(
            db_session, "WIDGET-BOM", "Widget Assembly"
        )
        motor_no_bom = create_product(
            db_session, "MOTOR-NOBOM", "Motor Component"
        )
        raw = create_product(
            db_session, "RAW-MATERIAL", "Raw Material", is_finished_product=False
        )

        create_bom_entry(db_session, motor_with_bom.id, raw.id)
        create_bom_entry(db_session, widget_with_bom.id, raw.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "query": "motor", "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # Only motor_with_bom should be returned (has BOM AND matches "motor")
        assert motor_with_bom.id in returned_ids
        assert widget_with_bom.id not in returned_ids
        assert motor_no_bom.id not in returned_ids

    def test_search_all_three_filters_combined(
        self, db_session, authenticated_client
    ):
        """
        Given: Products with various combinations of filters
        When: GET /api/v1/products/search?has_bom=true&is_finished_product=true&query=assembly
        Then: Only products matching ALL criteria are returned
        """
        # Arrange
        target_product = create_product(
            db_session, "TARGET", "Motor Assembly"
        )  # Finished, has BOM, matches query
        partial_match_1 = create_product(
            db_session, "PARTIAL-1", "Motor Assembly No BOM"
        )  # Finished, no BOM, matches query
        partial_match_2 = create_product(
            db_session, "PARTIAL-2", "Widget Assembly",
        )  # Finished, has BOM, doesn't match
        raw = create_product(
            db_session, "RAW", "Raw Material", is_finished_product=False
        )

        create_bom_entry(db_session, target_product.id, raw.id)
        create_bom_entry(db_session, partial_match_2.id, raw.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={
                "has_bom": True,
                "is_finished_product": True,
                "query": "motor",
                "limit": 50
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # Only target_product matches all three criteria
        assert target_product.id in returned_ids
        assert partial_match_1.id not in returned_ids
        assert partial_match_2.id not in returned_ids


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_search_has_bom_true_with_no_matching_products(
        self, db_session, authenticated_client
    ):
        """
        Given: No products with BOM exist
        When: GET /api/v1/products/search?has_bom=true
        Then: Empty result set is returned
        """
        # Arrange: Create only standalone products
        create_product(db_session, "EDGE-001", "Standalone 1")
        create_product(db_session, "EDGE-002", "Standalone 2")

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_search_has_bom_false_with_no_matching_products(
        self, db_session, authenticated_client
    ):
        """
        Given: All products have BOM entries
        When: GET /api/v1/products/search?has_bom=false
        Then: Empty result set is returned (or only non-parent products)
        """
        # Arrange: Create products where all are BOM parents
        parent1 = create_product(db_session, "EDGE-PARENT-1", "Parent 1")
        parent2 = create_product(db_session, "EDGE-PARENT-2", "Parent 2")
        child = create_product(
            db_session, "EDGE-CHILD", "Shared Child", is_finished_product=False
        )

        create_bom_entry(db_session, parent1.id, child.id)
        create_bom_entry(db_session, parent2.id, child.id)

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": False, "limit": 50}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data["items"]]

        # Only the child (which is not a parent) should be returned
        assert parent1.id not in returned_ids
        assert parent2.id not in returned_ids
        assert child.id in returned_ids

    def test_search_has_bom_pagination_works(
        self, db_session, authenticated_client
    ):
        """
        Given: Many products with BOM exist
        When: GET /api/v1/products/search?has_bom=true&limit=5
        Then: Pagination works correctly with has_bom filter
        """
        # Arrange: Create 10 products with BOM
        shared_child = create_product(
            db_session, "SHARED-CHILD", "Shared Child", is_finished_product=False
        )
        for i in range(10):
            parent = create_product(db_session, f"PAGE-PARENT-{i}", f"Parent {i}")
            create_bom_entry(db_session, parent.id, shared_child.id)

        # Act: Get first page
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 5, "offset": 0}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 5
        assert data["total"] == 10
        assert data["has_more"] is True

        # Act: Get second page
        response2 = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 5, "offset": 5}
        )

        data2 = response2.json()
        assert len(data2["items"]) == 5
        assert data2["offset"] == 5


class TestProductWithMultipleBomEntries:
    """Test products with multiple BOM entries"""

    def test_product_with_multiple_children_appears_once(
        self, db_session, authenticated_client
    ):
        """
        Given: A product has multiple BOM entries (children)
        When: GET /api/v1/products/search?has_bom=true
        Then: The parent product appears only once in results
        """
        # Arrange
        parent = create_product(db_session, "MULTI-PARENT", "Multi-Child Parent")
        for i in range(5):
            child = create_product(
                db_session, f"MULTI-CHILD-{i}", f"Child {i}", is_finished_product=False
            )
            create_bom_entry(db_session, parent.id, child.id, quantity=float(i + 1))

        # Act
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 100}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Count occurrences of parent product
        parent_count = sum(1 for item in data["items"] if item["id"] == parent.id)
        assert parent_count == 1, "Parent product should appear exactly once"


class TestIntegration:
    """Integration tests for has_bom filter"""

    @pytest.mark.integration
    def test_has_bom_filter_performance(
        self, db_session, authenticated_client
    ):
        """
        Given: Large number of products
        When: GET /api/v1/products/search?has_bom=true
        Then: Response time is acceptable (<500ms)
        """
        import time

        # Arrange: Create many products
        shared_child = create_product(
            db_session, "PERF-CHILD", "Shared Child", is_finished_product=False
        )
        for i in range(50):
            parent = create_product(db_session, f"PERF-PARENT-{i}", f"Parent {i}")
            if i % 2 == 0:  # Half have BOM
                create_bom_entry(db_session, parent.id, shared_child.id)

        # Act
        start_time = time.perf_counter()
        response = authenticated_client.get(
            "/api/v1/products/search",
            params={"has_bom": True, "limit": 50}
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assert
        assert response.status_code == 200
        assert elapsed_ms < 500, f"Response time {elapsed_ms:.2f}ms exceeded 500ms SLA"
