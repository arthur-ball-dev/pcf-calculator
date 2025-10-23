"""
Test suite for FastAPI initialization
Following TDD methodology - these tests are written BEFORE implementation

Test Scenarios (from TASK-BE-001 specification):
1. FastAPI App Initialization
2. Health Check Endpoint
3. Project Structure Created
4. Dependencies Installed
"""

import os
import sys
from pathlib import Path

import pytest


# Test Scenario 1: FastAPI App Initialization
def test_fastapi_app_exists():
    """Test that FastAPI app can be imported and is not None"""
    from backend.main import app

    assert app is not None, "FastAPI app should be initialized"


def test_fastapi_app_title():
    """Test that FastAPI app has correct title"""
    from backend.main import app

    assert app.title == "PCF Calculator API", f"Expected title 'PCF Calculator API', got '{app.title}'"


def test_fastapi_app_version():
    """Test that FastAPI app has correct version"""
    from backend.main import app

    assert app.version == "1.0.0", f"Expected version '1.0.0', got '{app.version}'"


def test_fastapi_app_description():
    """Test that FastAPI app has a description"""
    from backend.main import app

    assert hasattr(app, 'description'), "FastAPI app should have a description"
    assert len(app.description) > 0, "Description should not be empty"


# Test Scenario 2: Health Check Endpoint
def test_health_check_endpoint_exists():
    """Test that health check endpoint is accessible"""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"


def test_health_check_response_format():
    """Test that health check returns correct JSON structure"""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    data = response.json()
    assert "status" in data, "Response should contain 'status' field"
    assert "version" in data, "Response should contain 'version' field"


def test_health_check_response_values():
    """Test that health check returns correct values"""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")

    expected_response = {"status": "healthy", "version": "1.0.0"}
    assert response.json() == expected_response, f"Expected {expected_response}, got {response.json()}"


# Test Scenario 3: Project Structure Created
def test_backend_init_file_exists():
    """Test that backend/__init__.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    init_file = backend_path / "__init__.py"

    assert init_file.exists(), f"backend/__init__.py should exist at {init_file}"


def test_main_py_exists():
    """Test that backend/main.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    main_file = backend_path / "main.py"

    assert main_file.exists(), f"backend/main.py should exist at {main_file}"


def test_config_py_exists():
    """Test that backend/config.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    config_file = backend_path / "config.py"

    assert config_file.exists(), f"backend/config.py should exist at {config_file}"


def test_requirements_txt_exists():
    """Test that backend/requirements.txt exists"""
    backend_path = Path(__file__).parent.parent.parent
    requirements_file = backend_path / "requirements.txt"

    assert requirements_file.exists(), f"backend/requirements.txt should exist at {requirements_file}"


def test_api_directory_exists():
    """Test that backend/api/ directory exists"""
    backend_path = Path(__file__).parent.parent.parent
    api_dir = backend_path / "api"

    assert api_dir.exists(), f"backend/api/ should exist at {api_dir}"
    assert api_dir.is_dir(), "backend/api should be a directory"


def test_api_init_file_exists():
    """Test that backend/api/__init__.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    api_init = backend_path / "api" / "__init__.py"

    assert api_init.exists(), f"backend/api/__init__.py should exist at {api_init}"


def test_models_directory_exists():
    """Test that backend/models/ directory exists"""
    backend_path = Path(__file__).parent.parent.parent
    models_dir = backend_path / "models"

    assert models_dir.exists(), f"backend/models/ should exist at {models_dir}"
    assert models_dir.is_dir(), "backend/models should be a directory"


def test_models_init_file_exists():
    """Test that backend/models/__init__.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    models_init = backend_path / "models" / "__init__.py"

    assert models_init.exists(), f"backend/models/__init__.py should exist at {models_init}"


def test_services_directory_exists():
    """Test that backend/services/ directory exists"""
    backend_path = Path(__file__).parent.parent.parent
    services_dir = backend_path / "services"

    assert services_dir.exists(), f"backend/services/ should exist at {services_dir}"
    assert services_dir.is_dir(), "backend/services should be a directory"


def test_services_init_file_exists():
    """Test that backend/services/__init__.py exists"""
    backend_path = Path(__file__).parent.parent.parent
    services_init = backend_path / "services" / "__init__.py"

    assert services_init.exists(), f"backend/services/__init__.py should exist at {services_init}"


# Test Scenario 4: Dependencies Installed
def test_fastapi_import():
    """Test that fastapi can be imported"""
    try:
        import fastapi
        assert True
    except ImportError as e:
        pytest.fail(f"fastapi should be importable: {e}")


def test_uvicorn_import():
    """Test that uvicorn can be imported"""
    try:
        import uvicorn
        assert True
    except ImportError as e:
        pytest.fail(f"uvicorn should be importable: {e}")


def test_sqlalchemy_import():
    """Test that sqlalchemy can be imported"""
    try:
        import sqlalchemy
        assert True
    except ImportError as e:
        pytest.fail(f"sqlalchemy should be importable: {e}")


def test_pydantic_import():
    """Test that pydantic can be imported"""
    try:
        import pydantic
        assert True
    except ImportError as e:
        pytest.fail(f"pydantic should be importable: {e}")


def test_pandas_import():
    """Test that pandas can be imported"""
    try:
        import pandas
        assert True
    except ImportError as e:
        pytest.fail(f"pandas should be importable: {e}")


def test_pytest_import():
    """Test that pytest can be imported"""
    try:
        import pytest
        assert True
    except ImportError as e:
        pytest.fail(f"pytest should be importable: {e}")


def test_httpx_import():
    """Test that httpx can be imported (for TestClient)"""
    try:
        import httpx
        assert True
    except ImportError as e:
        pytest.fail(f"httpx should be importable: {e}")


def test_dotenv_import():
    """Test that python-dotenv can be imported"""
    try:
        import dotenv
        assert True
    except ImportError as e:
        pytest.fail(f"dotenv should be importable: {e}")


# Additional tests for robustness
def test_config_can_be_imported():
    """Test that config module can be imported"""
    try:
        from backend import config
        assert True
    except ImportError as e:
        pytest.fail(f"backend.config should be importable: {e}")


def test_openapi_docs_enabled():
    """Test that OpenAPI documentation is enabled"""
    from backend.main import app

    # FastAPI automatically enables /docs and /openapi.json
    # We just verify the app has the necessary attributes
    assert hasattr(app, 'openapi'), "FastAPI app should have openapi method"


def test_health_endpoint_is_async():
    """Test that health endpoint is defined as async (best practice for FastAPI)"""
    from backend.main import app
    import inspect

    # Find the health endpoint route
    health_route = None
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/health':
            health_route = route
            break

    assert health_route is not None, "Health route should be registered"
    assert hasattr(health_route, 'endpoint'), "Health route should have an endpoint"

    # Check if endpoint is async
    endpoint_func = health_route.endpoint
    assert inspect.iscoroutinefunction(endpoint_func), "Health endpoint should be async"


def test_requirements_contains_core_dependencies():
    """Test that requirements.txt contains all core dependencies"""
    backend_path = Path(__file__).parent.parent.parent
    requirements_file = backend_path / "requirements.txt"

    with open(requirements_file, 'r') as f:
        requirements_content = f.read()

    # Core dependencies that MUST be present
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pandas',
        'pytest',
        'httpx',
        'python-dotenv'
    ]

    for package in required_packages:
        assert package in requirements_content.lower(), f"requirements.txt should contain {package}"
