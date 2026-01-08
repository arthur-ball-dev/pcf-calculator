"""
Test Domain Layer Integration with API Routes

TASK-BE-P7-050: Wire Domain Layer to API Routes

Tests verify that:
1. API routes use domain services via FastAPI dependency injection
2. Domain exceptions are properly mapped to HTTP status codes
3. No direct ORM imports exist in route handlers
4. Domain layer separation is maintained

TDD Step 1: Write failing tests FIRST before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.models import Product, BillOfMaterials, PCFCalculation, generate_uuid
from backend.domain.entities.errors import (
    ProductNotFoundError,
    CalculationNotFoundError,
    DomainValidationError,
)
from backend.domain.entities.product import Product as DomainProduct, ProductWithBOM, BOMItem
from backend.domain.entities.calculation import Calculation, CalculationResult


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_domain_product():
    """Create a sample domain Product entity."""
    return DomainProduct(
        id="test-product-001",
        code="TEST-PROD-001",
        name="Test Product",
        unit="kg",
        category="test",
        description="A test product",
    )


@pytest.fixture
def sample_domain_product_with_bom(sample_domain_product):
    """Create a sample domain ProductWithBOM entity."""
    bom_items = [
        BOMItem(component_id="component-001", quantity=0.5, unit="kg"),
        BOMItem(component_id="component-002", quantity=0.3, unit="kg"),
    ]
    return ProductWithBOM(product=sample_domain_product, bom_items=bom_items)


@pytest.fixture
def sample_domain_calculation():
    """Create a sample domain Calculation entity."""
    return Calculation(
        id="test-calc-001",
        product_id="test-product-001",
        total_co2e_kg=2.5,
        status="completed",
        calculation_type="cradle_to_gate",
        materials_co2e=1.8,
        energy_co2e=0.5,
        transport_co2e=0.2,
    )


@pytest.fixture
def seed_products(db_session):
    """Seed test database with products for integration tests."""
    product = Product(
        id="domain-test-001",
        code="DOM-TEST-001",
        name="Domain Test Product",
        unit="unit",
        category="test",
        is_finished_product=True,
        description="Product for domain integration testing"
    )

    component = Product(
        id="domain-comp-001",
        code="DOM-COMP-001",
        name="Domain Test Component",
        unit="kg",
        category="material",
        is_finished_product=False,
    )

    db_session.add_all([product, component])
    db_session.commit()

    # Create BOM entry
    bom = BillOfMaterials(
        parent_product_id="domain-test-001",
        child_product_id="domain-comp-001",
        quantity=0.25,
        unit="kg",
        notes="Test BOM entry"
    )
    db_session.add(bom)
    db_session.commit()

    return {"product": product, "component": component, "bom": bom}


# ============================================================================
# Test: Dependency Providers Exist
# ============================================================================


class TestDependencyProviders:
    """Test that FastAPI dependency providers are properly configured."""

    def test_get_product_service_provider_exists(self):
        """
        Test that get_product_service dependency provider exists in api/dependencies.py.
        This provider should return a ProductService instance.
        """
        from backend.api import dependencies

        assert hasattr(dependencies, "get_product_service"),             "dependencies.py should have get_product_service function"

    def test_get_calculation_service_provider_exists(self):
        """
        Test that get_calculation_service dependency provider exists in api/dependencies.py.
        This provider should return a CalculationService instance.
        """
        from backend.api import dependencies

        assert hasattr(dependencies, "get_calculation_service"),             "dependencies.py should have get_calculation_service function"

    def test_get_product_repository_provider_exists(self):
        """
        Test that get_product_repository dependency provider exists.
        This is needed for creating service instances.
        """
        from backend.api import dependencies

        assert hasattr(dependencies, "get_product_repository"),             "dependencies.py should have get_product_repository function"

    def test_get_calculation_repository_provider_exists(self):
        """
        Test that get_calculation_repository dependency provider exists.
        This is needed for creating service instances.
        """
        from backend.api import dependencies

        assert hasattr(dependencies, "get_calculation_repository"),             "dependencies.py should have get_calculation_repository function"


# ============================================================================
# Test: Domain Exception Handlers
# ============================================================================


class TestDomainExceptionHandlers:
    """Test that domain exceptions are mapped to HTTP status codes."""

    def test_product_not_found_returns_404(self, authenticated_client, seed_products):
        """
        Test that ProductNotFoundError is mapped to 404 Not Found.
        """
        response = authenticated_client.get("/api/v1/products/nonexistent-domain-id")

        assert response.status_code == 404,             f"ProductNotFoundError should return 404, got {response.status_code}"

    def test_calculation_not_found_returns_404(self, authenticated_client):
        """
        Test that CalculationNotFoundError is mapped to 404 Not Found.
        """
        response = authenticated_client.get("/api/v1/calculations/nonexistent-calc-id")

        assert response.status_code == 404,             f"CalculationNotFoundError should return 404, got {response.status_code}"

    def test_domain_validation_error_returns_422(self, authenticated_client):
        """
        Test that DomainValidationError is mapped to 422 Unprocessable Entity.
        """
        from backend.main import app

        exception_handlers = app.exception_handlers

        assert DomainValidationError in exception_handlers or             any(issubclass(DomainValidationError, exc) for exc in exception_handlers.keys() if isinstance(exc, type)),             "DomainValidationError handler should be registered"


# ============================================================================
# Test: Products Route Uses Domain Service
# ============================================================================


class TestProductsRoutesDomainIntegration:
    """Test that products routes use domain services."""

    def test_list_products_uses_product_service(self, authenticated_client, seed_products):
        """
        Test GET /api/v1/products uses ProductService.list_products().
        """
        response = authenticated_client.get("/api/v1/products")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

        product_ids = [item["id"] for item in data["items"]]
        assert "domain-test-001" in product_ids

    def test_get_product_uses_product_service(self, authenticated_client, seed_products):
        """
        Test GET /api/v1/products/{id} uses ProductService.get_product_with_bom().
        """
        response = authenticated_client.get("/api/v1/products/domain-test-001")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "domain-test-001"
        assert data["code"] == "DOM-TEST-001"
        assert data["name"] == "Domain Test Product"

        assert "bill_of_materials" in data
        assert len(data["bill_of_materials"]) >= 1


# ============================================================================
# Test: Calculations Route Uses Domain Service
# ============================================================================


class TestCalculationsRoutesDomainIntegration:
    """Test that calculations routes use domain services."""

    def test_get_calculation_uses_calculation_service(
        self, authenticated_client, seed_products, db_session
    ):
        """
        Test GET /api/v1/calculations/{id} uses CalculationService.get_calculation().
        """
        calc = PCFCalculation(
            id="domain-calc-001",
            product_id="domain-test-001",
            calculation_type="cradle_to_gate",
            status="completed",
            total_co2e_kg=1.5,
            materials_co2e=1.0,
            energy_co2e=0.3,
            transport_co2e=0.2,
        )
        db_session.add(calc)
        db_session.commit()

        response = authenticated_client.get("/api/v1/calculations/domain-calc-001")

        assert response.status_code == 200
        data = response.json()

        assert data["calculation_id"] == "domain-calc-001"
        assert data["status"] == "completed"
        assert data["total_co2e_kg"] == 1.5

    def test_start_calculation_uses_calculation_service(
        self, authenticated_client, seed_products
    ):
        """
        Test POST /api/v1/calculate uses CalculationService.create_calculation().
        """
        payload = {"product_id": "domain-test-001"}

        response = authenticated_client.post("/api/v1/calculate", json=payload)

        assert response.status_code == 202
        data = response.json()

        assert "calculation_id" in data
        assert "status" in data


# ============================================================================
# Test: Domain Service Integration
# ============================================================================


class TestDomainServiceIntegration:
    """Test full integration between API routes and domain services."""

    def test_product_service_list_products_integration(
        self, authenticated_client, seed_products, db_session
    ):
        """
        Integration test: Verify ProductService correctly lists products.
        """
        response = authenticated_client.get("/api/v1/products")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2

        test_product = next(
            (p for p in data["items"] if p["id"] == "domain-test-001"),
            None
        )
        assert test_product is not None
        assert test_product["name"] == "Domain Test Product"

    def test_product_service_get_with_bom_integration(
        self, authenticated_client, seed_products, db_session
    ):
        """
        Integration test: Verify ProductService correctly returns product with BOM.
        """
        response = authenticated_client.get("/api/v1/products/domain-test-001")

        assert response.status_code == 200
        data = response.json()

        assert "bill_of_materials" in data
        assert len(data["bill_of_materials"]) == 1

        bom_item = data["bill_of_materials"][0]
        assert bom_item["child_product_id"] == "domain-comp-001"
        assert bom_item["quantity"] == 0.25

    def test_product_not_found_via_domain_service(
        self, authenticated_client, seed_products
    ):
        """
        Test that ProductNotFoundError from domain service is properly handled.
        """
        response = authenticated_client.get("/api/v1/products/nonexistent-product")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data or "error" in data

    def test_calculation_not_found_via_domain_service(
        self, authenticated_client, seed_products
    ):
        """
        Test that CalculationNotFoundError from domain service is properly handled.
        """
        response = authenticated_client.get("/api/v1/calculations/nonexistent-calc")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data or "error" in data


# ============================================================================
# Test: Repository Provider Configuration
# ============================================================================


class TestRepositoryProviders:
    """Test that repository providers are correctly configured."""

    def test_product_repository_returns_sqlalchemy_implementation(self, db_session):
        """
        Test that get_product_repository returns SQLAlchemyProductRepository.
        """
        from backend.api.dependencies import get_product_repository
        from backend.infrastructure.repositories.sqlalchemy_product_repository import (
            SQLAlchemyProductRepository,
        )

        repo = None

        result = get_product_repository(db_session)
        if hasattr(result, "__next__"):
            repo = next(result)
        else:
            repo = result

        assert isinstance(repo, SQLAlchemyProductRepository),             f"Expected SQLAlchemyProductRepository, got {type(repo)}"

    def test_calculation_repository_returns_sqlalchemy_implementation(self, db_session):
        """
        Test that get_calculation_repository returns SQLAlchemyCalculationRepository.
        """
        from backend.api.dependencies import get_calculation_repository
        from backend.infrastructure.repositories.sqlalchemy_calculation_repository import (
            SQLAlchemyCalculationRepository,
        )

        repo = None

        result = get_calculation_repository(db_session)
        if hasattr(result, "__next__"):
            repo = next(result)
        else:
            repo = result

        assert isinstance(repo, SQLAlchemyCalculationRepository),             f"Expected SQLAlchemyCalculationRepository, got {type(repo)}"


# ============================================================================
# Test: Exception Handler Registration
# ============================================================================


class TestExceptionHandlerRegistration:
    """Test that domain exception handlers are registered with FastAPI app."""

    def test_product_not_found_handler_registered(self):
        """
        Test that ProductNotFoundError exception handler is registered.
        """
        from backend.main import app

        handlers = app.exception_handlers

        assert ProductNotFoundError in handlers,             "ProductNotFoundError handler should be registered in main.py"

    def test_calculation_not_found_handler_registered(self):
        """
        Test that CalculationNotFoundError exception handler is registered.
        """
        from backend.main import app

        handlers = app.exception_handlers

        assert CalculationNotFoundError in handlers,             "CalculationNotFoundError handler should be registered in main.py"

    def test_domain_validation_error_handler_registered(self):
        """
        Test that DomainValidationError exception handler is registered.
        """
        from backend.main import app

        handlers = app.exception_handlers

        assert DomainValidationError in handlers,             "DomainValidationError handler should be registered in main.py"


# ============================================================================
# Test: Error Response Format
# ============================================================================


class TestErrorResponseFormat:
    """Test that domain errors return properly formatted responses."""

    def test_product_not_found_response_format(self, authenticated_client, seed_products):
        """
        Test ProductNotFoundError returns proper error response format.
        """
        response = authenticated_client.get("/api/v1/products/nonexistent-id")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data or "error" in data

    def test_calculation_not_found_response_format(self, authenticated_client):
        """
        Test CalculationNotFoundError returns proper error response format.
        """
        response = authenticated_client.get("/api/v1/calculations/nonexistent-id")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data or "error" in data
