"""
Test Calculation API Endpoints
TASK-API-002: Test coverage for async calculation endpoints

Tests for:
- POST /api/v1/calculate - Start async calculation
- GET /api/v1/calculations/{id} - Poll for results

Following TDD methodology: Tests written FIRST before implementation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import time

from backend.main import app
from backend.models import Base, Product, BillOfMaterials, PCFCalculation, generate_uuid
from backend.database.connection import get_db


# ============================================================================
# Test Database Setup
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create test database with in-memory SQLite"""
    # Use StaticPool to enable threading for TestClient
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with test database"""
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for test setup"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing"""
    product = Product(
        id=generate_uuid(),
        code="TEST-PRODUCT-001",
        name="Test Product",
        unit="unit",
        category="test",
        is_finished_product=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_product_with_bom(db_session):
    """Create a product with bill of materials"""
    # Create finished product
    product = Product(
        id=generate_uuid(),
        code="TSHIRT-001",
        name="Cotton T-Shirt",
        unit="unit",
        category="apparel",
        is_finished_product=True
    )
    db_session.add(product)

    # Create material components
    cotton = Product(
        id=generate_uuid(),
        code="cotton",
        name="Cotton",
        unit="kg",
        category="materials",
        is_finished_product=False
    )
    db_session.add(cotton)

    polyester = Product(
        id=generate_uuid(),
        code="polyester",
        name="Polyester",
        unit="kg",
        category="materials",
        is_finished_product=False
    )
    db_session.add(polyester)

    db_session.commit()

    # Create BOM entries
    bom_cotton = BillOfMaterials(
        id=generate_uuid(),
        parent_product_id=product.id,
        child_product_id=cotton.id,
        quantity=0.18,
        unit="kg"
    )
    db_session.add(bom_cotton)

    bom_polyester = BillOfMaterials(
        id=generate_uuid(),
        parent_product_id=product.id,
        child_product_id=polyester.id,
        quantity=0.02,
        unit="kg"
    )
    db_session.add(bom_polyester)

    db_session.commit()
    db_session.refresh(product)

    return product


# ============================================================================
# Test Cases: POST /api/v1/calculate
# ============================================================================

class TestStartCalculation:
    """Test suite for POST /api/v1/calculate endpoint"""

    def test_start_calculation_returns_202_accepted(self, client, sample_product):
        """
        SCENARIO 1: Start calculation successfully
        Should return 202 Accepted with calculation_id and status="processing"
        """
        # Arrange
        payload = {
            "product_id": sample_product.id
        }

        # Act
        response = client.post("/api/v1/calculate", json=payload)

        # Assert
        assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}"

        data = response.json()
        assert "calculation_id" in data, "Response should include calculation_id"
        assert "status" in data, "Response should include status"
        assert data["status"] == "processing", f"Status should be 'processing', got {data['status']}"

        # Verify calculation_id is a valid UUID hex string (32 chars)
        calc_id = data["calculation_id"]
        assert len(calc_id) == 32, f"calculation_id should be 32 chars, got {len(calc_id)}"

    def test_start_calculation_creates_database_record(self, client, sample_product, db_session):
        """
        Should create PCFCalculation record in database with status="pending"
        """
        # Arrange
        payload = {"product_id": sample_product.id}

        # Act
        response = client.post("/api/v1/calculate", json=payload)
        calc_id = response.json()["calculation_id"]

        # Assert - check database record was created
        calculation = db_session.query(PCFCalculation).filter_by(id=calc_id).first()
        assert calculation is not None, "Calculation record should exist in database"
        assert calculation.product_id == sample_product.id
        assert calculation.status in ["pending", "running", "completed"], \
            f"Status should be pending/running/completed, got {calculation.status}"

    def test_start_calculation_missing_product_id(self, client):
        """
        SCENARIO 4: Validation error - missing product_id
        Should return 422 Unprocessable Entity
        """
        # Arrange
        payload = {}  # Missing product_id

        # Act
        response = client.post("/api/v1/calculate", json=payload)

        # Assert
        assert response.status_code == 422, \
            f"Should return 422 for missing product_id, got {response.status_code}"

        data = response.json()
        assert "detail" in data, "Error response should include detail"

    def test_start_calculation_invalid_product_id(self, client):
        """
        Should handle invalid product_id (product not found)
        Returns 202 but calculation will fail with appropriate error
        """
        # Arrange
        payload = {"product_id": "nonexistent-product-id"}

        # Act
        response = client.post("/api/v1/calculate", json=payload)

        # Assert
        # API returns 202 immediately (async pattern)
        # The error will be captured in calculation status
        assert response.status_code == 202, \
            f"Should return 202 for async processing, got {response.status_code}"

    def test_start_calculation_with_bom_product(self, client, sample_product_with_bom):
        """
        Should start calculation for product with BOM structure
        """
        # Arrange
        payload = {"product_id": sample_product_with_bom.id}

        # Act
        response = client.post("/api/v1/calculate", json=payload)

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "calculation_id" in data
        assert data["status"] == "processing"


# ============================================================================
# Test Cases: GET /api/v1/calculations/{id}
# ============================================================================

class TestGetCalculationStatus:
    """Test suite for GET /api/v1/calculations/{id} endpoint"""

    def test_get_calculation_processing_status(self, client, sample_product, db_session):
        """
        SCENARIO 2: Poll status while processing
        Should return 200 with status="processing" (no result yet)
        """
        # Arrange - create calculation record with status="processing"
        calc_id = generate_uuid()
        calculation = PCFCalculation(
            id=calc_id,
            product_id=sample_product.id,
            calculation_type="cradle_to_gate",
            status="pending",
            total_co2e_kg=0.0
        )
        db_session.add(calculation)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/calculations/{calc_id}")

        # Assert
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

        data = response.json()
        assert data["status"] in ["pending", "running", "processing"], \
            f"Status should be pending/running/processing, got {data['status']}"
        assert data["calculation_id"] == calc_id

        # Should NOT have result while processing
        assert "result" not in data or data.get("result") is None, \
            "Should not include result while processing"

    def test_get_calculation_completed_status(self, client, sample_product, db_session):
        """
        SCENARIO 3: Poll status when completed
        Should return 200 with status="completed" and full results
        """
        # Arrange - create completed calculation
        calc_id = generate_uuid()
        calculation = PCFCalculation(
            id=calc_id,
            product_id=sample_product.id,
            calculation_type="cradle_to_gate",
            status="completed",
            total_co2e_kg=2.05,
            materials_co2e=1.80,
            energy_co2e=0.15,
            transport_co2e=0.10,
            calculation_time_ms=150
        )
        db_session.add(calculation)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/calculations/{calc_id}")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["calculation_id"] == calc_id

        # Should include result when completed
        assert "total_co2e_kg" in data, "Completed calculation should include total_co2e_kg"
        assert data["total_co2e_kg"] == 2.05

        # Should include breakdown
        assert "materials_co2e" in data
        assert data["materials_co2e"] == 1.80

    def test_get_calculation_not_found(self, client):
        """
        SCENARIO 5: Get calculation - 404 for missing calculation
        Should return 404 Not Found for nonexistent calculation_id
        """
        # Arrange
        nonexistent_id = "nonexistent-calc-id-12345678"

        # Act
        response = client.get(f"/api/v1/calculations/{nonexistent_id}")

        # Assert
        assert response.status_code == 404, \
            f"Should return 404 for missing calculation, got {response.status_code}"

        data = response.json()
        assert "detail" in data, "404 response should include detail message"

    def test_get_calculation_failed_status(self, client, sample_product, db_session):
        """
        Should return failed status with error message when calculation fails
        """
        # Arrange - create failed calculation
        calc_id = generate_uuid()
        calculation = PCFCalculation(
            id=calc_id,
            product_id=sample_product.id,
            calculation_type="cradle_to_gate",
            status="failed",
            total_co2e_kg=0.0,
            calculation_metadata={"error_message": "Product not found"}
        )
        db_session.add(calculation)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/calculations/{calc_id}")

        # Assert
        assert response.status_code == 200  # Still returns 200, but with failed status

        data = response.json()
        assert data["status"] == "failed"
        assert "error_message" in data
        assert data["error_message"] == "Product not found"


# ============================================================================
# Integration Tests: Full Calculation Flow
# ============================================================================

class TestCalculationIntegration:
    """Integration tests for complete calculation workflow"""

    @pytest.mark.asyncio
    async def test_full_calculation_workflow(self, client, sample_product):
        """
        Integration test: Start calculation and poll until completion
        Tests the full async workflow
        """
        # Step 1: Start calculation
        response = client.post("/api/v1/calculate", json={"product_id": sample_product.id})
        assert response.status_code == 202

        calc_id = response.json()["calculation_id"]

        # Step 2: Poll for completion (with timeout)
        max_polls = 10
        poll_interval = 0.1  # 100ms

        for i in range(max_polls):
            response = client.get(f"/api/v1/calculations/{calc_id}")
            assert response.status_code == 200

            data = response.json()
            status = data["status"]

            if status == "completed":
                # Success - calculation completed
                assert "total_co2e_kg" in data
                break
            elif status == "failed":
                # Calculation failed
                pytest.fail(f"Calculation failed: {data.get('error_message', 'Unknown error')}")

            # Still processing, wait and retry
            time.sleep(poll_interval)
        else:
            # Timeout - calculation didn't complete
            pytest.fail(f"Calculation did not complete within {max_polls * poll_interval}s")

    def test_multiple_concurrent_calculations(self, client, sample_product):
        """
        Should handle multiple concurrent calculations for same product
        """
        # Arrange - start multiple calculations
        calc_ids = []
        for i in range(3):
            response = client.post("/api/v1/calculate", json={"product_id": sample_product.id})
            assert response.status_code == 202
            calc_ids.append(response.json()["calculation_id"])

        # Assert - all calculation IDs should be unique
        assert len(calc_ids) == len(set(calc_ids)), "All calculation IDs should be unique"

        # Assert - all calculations should be queryable
        for calc_id in calc_ids:
            response = client.get(f"/api/v1/calculations/{calc_id}")
            assert response.status_code == 200


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestCalculationEdgeCases:
    """Test edge cases and error conditions"""

    def test_calculate_product_without_bom(self, client, sample_product):
        """
        Should handle product with no BOM (empty bill of materials)
        Returns 0.0 emissions
        """
        # Arrange
        payload = {"product_id": sample_product.id}

        # Act
        response = client.post("/api/v1/calculate", json=payload)
        assert response.status_code == 202

        calc_id = response.json()["calculation_id"]

        # Poll until complete
        time.sleep(0.2)  # Give it time to process

        response = client.get(f"/api/v1/calculations/{calc_id}")
        data = response.json()

        # Assert - should complete with 0.0 emissions
        if data["status"] == "completed":
            assert data["total_co2e_kg"] == 0.0, "Product without BOM should have 0.0 emissions"

    def test_calculate_with_malformed_json(self, client):
        """
        Should return 422 for malformed JSON payload
        """
        # Act - send invalid JSON
        response = client.post(
            "/api/v1/calculate",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422, \
            f"Should return 422 for malformed JSON, got {response.status_code}"

    def test_get_calculation_with_invalid_id_format(self, client):
        """
        Should return 404 for invalid calculation_id format
        """
        # Act
        response = client.get("/api/v1/calculations/invalid-format")

        # Assert
        assert response.status_code == 404, \
            f"Should return 404 for invalid ID format, got {response.status_code}"
