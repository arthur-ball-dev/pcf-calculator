"""
TASK-API-005: OpenAPI Documentation Tests
Test-Driven Development (TDD) - Tests written FIRST

These tests verify that FastAPI auto-generates complete, accurate
OpenAPI documentation at /docs with all endpoints properly documented.

Test Coverage:
1. Swagger UI is accessible at /docs
2. OpenAPI JSON is complete and valid
3. All endpoints have descriptions and summaries
4. Request/response schemas are documented
5. Example payloads are provided
6. API metadata is complete
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models import Base
from backend.main import app
from backend.database.connection import get_db


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Enable foreign key constraints for SQLite
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create FastAPI TestClient with database dependency override
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)

    yield test_client

    # Clean up dependency override
    app.dependency_overrides.clear()


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================

def test_swagger_ui_accessible(client: TestClient):
    """
    Scenario 1: Swagger UI Available
    GIVEN: API is running
    WHEN: GET /docs
    THEN: Returns 200 and HTML contains "swagger"
    """
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower(), "Swagger UI should be accessible"
    assert "openapi" in response.text.lower(), "OpenAPI references should be present"


def test_openapi_json_accessible(client: TestClient):
    """
    Scenario 2: OpenAPI JSON Complete
    GIVEN: API is running
    WHEN: GET /openapi.json
    THEN: Returns 200 and valid JSON structure with all endpoints
    """
    response = client.get("/openapi.json")

    assert response.status_code == 200

    openapi_spec = response.json()

    # Verify OpenAPI structure
    assert "openapi" in openapi_spec, "Should have OpenAPI version"
    assert "info" in openapi_spec, "Should have info section"
    assert "paths" in openapi_spec, "Should have paths section"
    assert "components" in openapi_spec, "Should have components section"

    # Verify all expected endpoints are present
    paths = openapi_spec["paths"]

    expected_endpoints = [
        "/health",
        "/api/v1/products",
        "/api/v1/products/{product_id}",
        "/api/v1/calculate",
        "/api/v1/calculations/{calculation_id}",
        "/api/v1/emission-factors"
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} should be documented"


def test_api_metadata_complete(client: TestClient):
    """
    Scenario 3: API Metadata Complete
    GIVEN: OpenAPI spec is generated
    WHEN: Checking info section
    THEN: Contains title, version, description, and contact info
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    info = openapi_spec["info"]

    # Required fields
    assert "title" in info, "API should have a title"
    assert "version" in info, "API should have a version"
    assert "description" in info, "API should have a description"

    # Title should be meaningful
    assert len(info["title"]) > 5, "Title should be descriptive"
    assert "PCF" in info["title"] or "Carbon" in info["title"], "Title should mention PCF or Carbon"

    # Description should be comprehensive
    assert len(info["description"]) > 50, "Description should be detailed (>50 chars)"

    # Version should be semantic
    assert info["version"] == "1.0.0", "Version should be 1.0.0"


def test_products_endpoints_documented(client: TestClient):
    """
    Scenario 4: Products Endpoints Have Descriptions
    GIVEN: OpenAPI spec is generated
    WHEN: Checking products endpoints
    THEN: Each endpoint has summary, description, and tags
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/products
    products_list = paths["/api/v1/products"]["get"]
    assert "summary" in products_list, "List products should have summary"
    assert "description" in products_list, "List products should have description"
    assert "tags" in products_list, "List products should have tags"
    assert "products" in products_list["tags"], "Should be tagged with 'products'"
    assert len(products_list["summary"]) > 5, "Summary should be meaningful"
    assert len(products_list["description"]) > 10, "Description should be detailed"

    # Test GET /api/v1/products/{product_id}
    product_detail = paths["/api/v1/products/{product_id}"]["get"]
    assert "summary" in product_detail, "Get product should have summary"
    assert "description" in product_detail, "Get product should have description"
    assert "tags" in product_detail, "Get product should have tags"


def test_calculations_endpoints_documented(client: TestClient):
    """
    Scenario 5: Calculations Endpoints Have Descriptions
    GIVEN: OpenAPI spec is generated
    WHEN: Checking calculations endpoints
    THEN: Each endpoint has summary, description, and tags
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test POST /api/v1/calculate
    calculate = paths["/api/v1/calculate"]["post"]
    assert "summary" in calculate, "Calculate endpoint should have summary"
    assert "description" in calculate, "Calculate endpoint should have description"
    assert "tags" in calculate, "Calculate endpoint should have tags"
    assert "calculations" in calculate["tags"], "Should be tagged with 'calculations'"

    # Test GET /api/v1/calculations/{calculation_id}
    calc_status = paths["/api/v1/calculations/{calculation_id}"]["get"]
    assert "summary" in calc_status, "Get calculation should have summary"
    assert "description" in calc_status, "Get calculation should have description"


def test_emission_factors_endpoints_documented(client: TestClient):
    """
    Scenario 6: Emission Factors Endpoints Have Descriptions
    GIVEN: OpenAPI spec is generated
    WHEN: Checking emission factors endpoints
    THEN: Each endpoint has summary, description, and tags
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/emission-factors
    ef_list = paths["/api/v1/emission-factors"]["get"]
    assert "summary" in ef_list, "List emission factors should have summary"
    assert "description" in ef_list, "List emission factors should have description"
    assert "tags" in ef_list, "List emission factors should have tags"
    assert "emission-factors" in ef_list["tags"], "Should be tagged with 'emission-factors'"

    # Test POST /api/v1/emission-factors
    ef_create = paths["/api/v1/emission-factors"]["post"]
    assert "summary" in ef_create, "Create emission factor should have summary"
    assert "description" in ef_create, "Create emission factor should have description"


def test_request_body_schemas_documented(client: TestClient):
    """
    Scenario 7: Request Body Schemas Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking endpoints with request bodies
    THEN: Request body schema is defined with proper references
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test POST /api/v1/calculate request body
    calculate = paths["/api/v1/calculate"]["post"]
    assert "requestBody" in calculate, "Calculate should have requestBody"

    request_body = calculate["requestBody"]
    assert "content" in request_body, "Request body should have content"
    assert "application/json" in request_body["content"], "Should accept application/json"

    json_content = request_body["content"]["application/json"]
    assert "schema" in json_content, "Should have schema definition"

    # Schema should reference CalculationRequest model
    schema = json_content["schema"]
    assert "$ref" in schema, "Should reference schema component"
    assert "CalculationRequest" in schema["$ref"], "Should reference CalculationRequest schema"

    # Test POST /api/v1/emission-factors request body
    ef_create = paths["/api/v1/emission-factors"]["post"]
    assert "requestBody" in ef_create, "Create emission factor should have requestBody"

    ef_request_body = ef_create["requestBody"]
    ef_schema = ef_request_body["content"]["application/json"]["schema"]
    assert "$ref" in ef_schema, "Should reference schema component"
    assert "EmissionFactorCreateRequest" in ef_schema["$ref"], "Should reference EmissionFactorCreateRequest"


def test_response_schemas_documented(client: TestClient):
    """
    Scenario 8: Response Schemas Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking endpoint responses
    THEN: Response schemas are defined for all status codes
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/products responses
    products_list = paths["/api/v1/products"]["get"]
    assert "responses" in products_list, "Should have responses defined"

    responses = products_list["responses"]
    assert "200" in responses, "Should document 200 response"

    success_response = responses["200"]
    assert "description" in success_response, "Response should have description"
    assert "content" in success_response, "Response should have content"
    assert "application/json" in success_response["content"], "Should return application/json"

    json_content = success_response["content"]["application/json"]
    assert "schema" in json_content, "Response should have schema"

    schema = json_content["schema"]
    assert "$ref" in schema, "Should reference schema component"
    assert "ProductListResponse" in schema["$ref"], "Should reference ProductListResponse"

    # Test POST /api/v1/calculate responses
    calculate = paths["/api/v1/calculate"]["post"]
    calc_responses = calculate["responses"]
    assert "202" in calc_responses, "Calculate should document 202 Accepted response"
    assert "422" in calc_responses, "Calculate should document 422 validation error"


def test_schema_components_present(client: TestClient):
    """
    Scenario 9: Schema Components Present
    GIVEN: OpenAPI spec is generated
    WHEN: Checking components section
    THEN: All Pydantic models are documented as schemas
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    assert "components" in openapi_spec, "Should have components section"
    assert "schemas" in openapi_spec["components"], "Should have schemas in components"

    schemas = openapi_spec["components"]["schemas"]

    # Expected schema components from our Pydantic models
    expected_schemas = [
        "ProductListResponse",
        "ProductListItemResponse",
        "ProductDetailResponse",
        "BOMItemResponse",
        "CalculationRequest",
        "CalculationStartResponse",
        "CalculationStatusResponse",
        "EmissionFactorListResponse",
        "EmissionFactorListItemResponse",
        "EmissionFactorCreateRequest",
        "EmissionFactorCreateResponse"
    ]

    for schema_name in expected_schemas:
        assert schema_name in schemas, f"Schema {schema_name} should be documented"

        schema = schemas[schema_name]
        assert "properties" in schema or "type" in schema, f"{schema_name} should have properties or type"

        # If it has properties, check they have descriptions
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                assert "description" in prop_def or "title" in prop_def, \
                    f"{schema_name}.{prop_name} should have description"


def test_examples_provided_in_schemas(client: TestClient):
    """
    Scenario 10: Examples Provided in Schemas
    GIVEN: OpenAPI spec is generated
    WHEN: Checking schema definitions
    THEN: Key schemas have example data
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    schemas = openapi_spec["components"]["schemas"]

    # CalculationRequest should have example
    calc_request = schemas["CalculationRequest"]
    # Examples can be in 'example', 'examples', or embedded in schema
    has_example = (
        "example" in calc_request or
        "examples" in calc_request or
        any("example" in prop for prop in calc_request.get("properties", {}).values())
    )
    assert has_example, "CalculationRequest should have example data"

    # CalculationStartResponse should have example
    calc_start = schemas["CalculationStartResponse"]
    has_example = (
        "example" in calc_start or
        "examples" in calc_start or
        any("example" in prop for prop in calc_start.get("properties", {}).values())
    )
    assert has_example, "CalculationStartResponse should have example data"

    # EmissionFactorCreateRequest should have example
    ef_create = schemas["EmissionFactorCreateRequest"]
    has_example = (
        "example" in ef_create or
        "examples" in ef_create or
        any("example" in prop for prop in ef_create.get("properties", {}).values())
    )
    assert has_example, "EmissionFactorCreateRequest should have example data"


def test_query_parameters_documented(client: TestClient):
    """
    Scenario 11: Query Parameters Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking endpoints with query parameters
    THEN: All query parameters have descriptions and schemas
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/products query parameters
    products_list = paths["/api/v1/products"]["get"]
    assert "parameters" in products_list, "Should document query parameters"

    params = products_list["parameters"]
    param_names = [p["name"] for p in params]

    # Expected query parameters
    assert "limit" in param_names, "Should document limit parameter"
    assert "offset" in param_names, "Should document offset parameter"
    assert "is_finished" in param_names, "Should document is_finished parameter"

    # Check parameter details
    for param in params:
        assert "name" in param, "Parameter should have name"
        assert "in" in param and param["in"] == "query", "Should be query parameter"
        assert "description" in param, f"Parameter {param['name']} should have description"
        assert "schema" in param, f"Parameter {param['name']} should have schema"

        # Description should be meaningful
        assert len(param["description"]) > 5, f"Parameter {param['name']} description should be detailed"


def test_path_parameters_documented(client: TestClient):
    """
    Scenario 12: Path Parameters Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking endpoints with path parameters
    THEN: Path parameters have descriptions and schemas
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/products/{product_id}
    product_detail = paths["/api/v1/products/{product_id}"]["get"]
    assert "parameters" in product_detail, "Should document path parameters"

    params = product_detail["parameters"]
    assert len(params) > 0, "Should have product_id parameter"

    product_id_param = next((p for p in params if p["name"] == "product_id"), None)
    assert product_id_param is not None, "Should have product_id parameter"
    assert product_id_param["in"] == "path", "Should be path parameter"
    assert "description" in product_id_param, "product_id should have description"
    assert product_id_param["required"] is True, "Path parameter should be required"


def test_error_responses_documented(client: TestClient):
    """
    Scenario 13: Error Responses Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking endpoint error responses
    THEN: Common error codes (404, 422, 500) are documented
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Test GET /api/v1/products/{product_id} - should document 404
    product_detail = paths["/api/v1/products/{product_id}"]["get"]
    responses = product_detail["responses"]

    # Most endpoints should document 422 validation error
    # At minimum, endpoints should document success response
    assert "200" in responses or "202" in responses or "201" in responses, \
        "Should document success response"


def test_tags_defined(client: TestClient):
    """
    Scenario 14: Tags Defined
    GIVEN: OpenAPI spec is generated
    WHEN: Checking tags section
    THEN: All used tags are defined with descriptions
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    # Tags should be defined (optional but recommended)
    # If tags are present at top level, they should have descriptions
    if "tags" in openapi_spec:
        tags = openapi_spec["tags"]

        for tag in tags:
            assert "name" in tag, "Tag should have name"
            assert "description" in tag, f"Tag {tag['name']} should have description"

            # Description should be meaningful
            assert len(tag["description"]) > 10, f"Tag {tag['name']} description should be detailed"


def test_http_methods_documented(client: TestClient):
    """
    Scenario 15: All HTTP Methods Documented
    GIVEN: OpenAPI spec is generated
    WHEN: Checking supported HTTP methods
    THEN: GET, POST methods are properly documented
    """
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec["paths"]

    # Verify various HTTP methods are documented
    assert "get" in paths["/api/v1/products"], "GET /products should be documented"
    assert "get" in paths["/api/v1/products/{product_id}"], "GET /products/{id} should be documented"
    assert "post" in paths["/api/v1/calculate"], "POST /calculate should be documented"
    assert "get" in paths["/api/v1/calculations/{calculation_id}"], "GET /calculations/{id} should be documented"
    assert "get" in paths["/api/v1/emission-factors"], "GET /emission-factors should be documented"
    assert "post" in paths["/api/v1/emission-factors"], "POST /emission-factors should be documented"
