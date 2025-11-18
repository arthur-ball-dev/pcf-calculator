"""
Test Emission Factors API Endpoints
TASK-API-003: Comprehensive tests for emission factors REST endpoints

Test Scenarios (per specification):
1. GET /api/v1/emission-factors - List all emission factors
2. GET /api/v1/emission-factors - Pagination (limit, offset)
3. GET /api/v1/emission-factors - Filter by data_source
4. GET /api/v1/emission-factors - Filter by geography
5. GET /api/v1/emission-factors - Filter by unit
6. GET /api/v1/emission-factors - Filter by activity_name (search)
7. POST /api/v1/emission-factors - Create custom emission factor
8. POST /api/v1/emission-factors - Duplicate prevention (409 conflict)
9. POST /api/v1/emission-factors - Validation error (422)
10. Response format validation with Pydantic
11. HTTP status codes (200, 201, 400, 409, 422)
12. Response structure matches API specification
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from decimal import Decimal

# Import models and base
from backend.models import (
    Base,
    EmissionFactor
)
from backend.main import app
from backend.database.connection import get_db


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing with threading support"""
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

    This fixture overrides the get_db dependency to use the test database
    instead of the production database
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


@pytest.fixture(scope="function")
def seed_test_emission_factors(db_session):
    """
    Seed test database with known emission factors for endpoint testing

    Creates:
    - 10 emission factors from various sources (EPA, DEFRA, Ecoinvent)
    - Various geographies (GLO, US, EU)
    - Different units (kg, L, kWh)
    - Different activity types (materials, energy, transport)
    """
    emission_factors = [
        EmissionFactor(
            id="ef-cotton-001",
            activity_name="Cotton Fabric",
            co2e_factor=Decimal("5.5"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=Decimal("0.85")
        ),
        EmissionFactor(
            id="ef-polyester-001",
            activity_name="Polyester Thread",
            co2e_factor=Decimal("6.2"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=Decimal("0.80")
        ),
        EmissionFactor(
            id="ef-pet-001",
            activity_name="PET Plastic",
            co2e_factor=Decimal("3.5"),
            unit="kg",
            data_source="DEFRA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=Decimal("0.90")
        ),
        EmissionFactor(
            id="ef-abs-001",
            activity_name="ABS Plastic",
            co2e_factor=Decimal("3.8"),
            unit="kg",
            data_source="Ecoinvent",
            geography="EU",
            reference_year=2022,
            data_quality_rating=Decimal("0.92")
        ),
        EmissionFactor(
            id="ef-aluminum-001",
            activity_name="Aluminum",
            co2e_factor=Decimal("8.5"),
            unit="kg",
            data_source="EPA",
            geography="US",
            reference_year=2023,
            data_quality_rating=Decimal("0.88")
        ),
        EmissionFactor(
            id="ef-electricity-001",
            activity_name="Electricity Grid Mix",
            co2e_factor=Decimal("0.42"),
            unit="kWh",
            data_source="EPA",
            geography="US",
            reference_year=2023,
            data_quality_rating=Decimal("0.95")
        ),
        EmissionFactor(
            id="ef-diesel-001",
            activity_name="Diesel Fuel",
            co2e_factor=Decimal("2.68"),
            unit="L",
            data_source="DEFRA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=Decimal("0.93")
        ),
        EmissionFactor(
            id="ef-steel-001",
            activity_name="Steel",
            co2e_factor=Decimal("2.1"),
            unit="kg",
            data_source="Ecoinvent",
            geography="GLO",
            reference_year=2022,
            data_quality_rating=Decimal("0.89")
        ),
        EmissionFactor(
            id="ef-cardboard-001",
            activity_name="Cardboard Packaging",
            co2e_factor=Decimal("0.95"),
            unit="kg",
            data_source="DEFRA",
            geography="EU",
            reference_year=2023,
            data_quality_rating=Decimal("0.82")
        ),
        EmissionFactor(
            id="ef-glass-001",
            activity_name="Glass",
            co2e_factor=Decimal("0.85"),
            unit="kg",
            data_source="EPA",
            geography="GLO",
            reference_year=2023,
            data_quality_rating=Decimal("0.87")
        )
    ]

    db_session.add_all(emission_factors)
    db_session.commit()

    return {
        "total_count": 10,
        "epa_count": 5,
        "defra_count": 3,
        "ecoinvent_count": 2,
        "glo_count": 6,
        "us_count": 2,
        "eu_count": 2,
        "kg_unit_count": 8,
        "kwh_unit_count": 1,
        "l_unit_count": 1
    }


# ============================================================================
# Test Scenario 1: GET /api/v1/emission-factors - List all
# ============================================================================

class TestListEmissionFactors:
    """Test GET /api/v1/emission-factors endpoint"""

    def test_list_emission_factors_returns_200(self, client, seed_test_emission_factors):
        """Test that listing emission factors returns 200 OK"""
        response = client.get("/api/v1/emission-factors")

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

    def test_list_emission_factors_returns_items(self, client, seed_test_emission_factors):
        """Test that response includes items array"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert "items" in data, \
            "Response should include 'items' field"
        assert isinstance(data["items"], list), \
            "Items should be a list"

    def test_list_emission_factors_returns_total(self, client, seed_test_emission_factors):
        """Test that response includes total count"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert "total" in data, \
            "Response should include 'total' field"
        assert isinstance(data["total"], int), \
            "Total should be an integer"
        assert data["total"] == seed_test_emission_factors["total_count"], \
            f"Expected total={seed_test_emission_factors['total_count']}, got {data['total']}"

    def test_list_emission_factors_includes_expected_items(self, client, seed_test_emission_factors):
        """Test that response includes known test emission factors"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        # Extract activity names
        activity_names = [item["activity_name"] for item in data["items"]]

        assert "Cotton Fabric" in activity_names, \
            "Response should include Cotton Fabric"
        assert "PET Plastic" in activity_names, \
            "Response should include PET Plastic"
        assert "Electricity Grid Mix" in activity_names, \
            "Response should include Electricity Grid Mix"

    def test_list_emission_factors_item_structure(self, client, seed_test_emission_factors):
        """Test that each item has required fields"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert len(data["items"]) > 0, \
            "Should have at least one emission factor"

        first_item = data["items"][0]

        # Required fields per API specification
        assert "id" in first_item, "Item should have 'id'"
        assert "activity_name" in first_item, "Item should have 'activity_name'"
        assert "co2e_factor" in first_item, "Item should have 'co2e_factor'"
        assert "unit" in first_item, "Item should have 'unit'"
        assert "data_source" in first_item, "Item should have 'data_source'"
        assert "geography" in first_item, "Item should have 'geography'"
        assert "reference_year" in first_item, "Item should have 'reference_year'"


# ============================================================================
# Test Scenario 2: GET /api/v1/emission-factors - Pagination
# ============================================================================

class TestEmissionFactorsPagination:
    """Test pagination parameters (limit, offset)"""

    def test_pagination_with_limit(self, client, seed_test_emission_factors):
        """Test that limit parameter restricts results"""
        response = client.get("/api/v1/emission-factors?limit=3")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 3, \
            f"Expected 3 items with limit=3, got {len(data['items'])}"
        assert data["limit"] == 3, \
            f"Response should include limit=3, got {data.get('limit')}"

    def test_pagination_with_offset(self, client, seed_test_emission_factors):
        """Test that offset parameter skips results"""
        # Get first 3 factors
        response1 = client.get("/api/v1/emission-factors?limit=3&offset=0")
        data1 = response1.json()
        first_three_ids = [item["id"] for item in data1["items"]]

        # Get next 3 factors
        response2 = client.get("/api/v1/emission-factors?limit=3&offset=3")
        data2 = response2.json()
        next_three_ids = [item["id"] for item in data2["items"]]

        # IDs should be different (no overlap)
        assert len(set(first_three_ids) & set(next_three_ids)) == 0, \
            "Offset should skip previous results"
        assert data2["offset"] == 3, \
            f"Response should include offset=3, got {data2.get('offset')}"

    def test_pagination_default_values(self, client, seed_test_emission_factors):
        """Test default pagination values"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert "limit" in data, "Response should include limit"
        assert "offset" in data, "Response should include offset"
        assert data["offset"] == 0, \
            f"Default offset should be 0, got {data['offset']}"

    def test_pagination_limit_validation(self, client, seed_test_emission_factors):
        """Test that limit has minimum value of 1"""
        response = client.get("/api/v1/emission-factors?limit=0")

        # Should return 422 for invalid parameter
        assert response.status_code == 422, \
            f"Expected 422 for limit=0, got {response.status_code}"

    def test_pagination_offset_validation(self, client, seed_test_emission_factors):
        """Test that offset cannot be negative"""
        response = client.get("/api/v1/emission-factors?offset=-1")

        # Should return 422 for invalid parameter
        assert response.status_code == 422, \
            f"Expected 422 for offset=-1, got {response.status_code}"


# ============================================================================
# Test Scenario 3: GET /api/v1/emission-factors - Filter by data_source
# ============================================================================

class TestFilterByDataSource:
    """Test filtering by data_source parameter"""

    def test_filter_by_epa_source(self, client, seed_test_emission_factors):
        """Test filtering for EPA emission factors only"""
        response = client.get("/api/v1/emission-factors?data_source=EPA")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be from EPA
        for item in data["items"]:
            assert item["data_source"] == "EPA", \
                f"Factor {item['activity_name']} should be from EPA"

        # Should return exactly 4 EPA factors from seed
        assert len(data["items"]) == seed_test_emission_factors["epa_count"], \
            f"Expected {seed_test_emission_factors['epa_count']} EPA factors, got {len(data['items'])}"

    def test_filter_by_defra_source(self, client, seed_test_emission_factors):
        """Test filtering for DEFRA emission factors only"""
        response = client.get("/api/v1/emission-factors?data_source=DEFRA")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be from DEFRA
        for item in data["items"]:
            assert item["data_source"] == "DEFRA", \
                f"Factor {item['activity_name']} should be from DEFRA"

        # Should return exactly 3 DEFRA factors from seed
        assert len(data["items"]) == seed_test_emission_factors["defra_count"], \
            f"Expected {seed_test_emission_factors['defra_count']} DEFRA factors, got {len(data['items'])}"

    def test_filter_by_ecoinvent_source(self, client, seed_test_emission_factors):
        """Test filtering for Ecoinvent emission factors only"""
        response = client.get("/api/v1/emission-factors?data_source=Ecoinvent")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be from Ecoinvent
        for item in data["items"]:
            assert item["data_source"] == "Ecoinvent", \
                f"Factor {item['activity_name']} should be from Ecoinvent"

        # Should return exactly 3 Ecoinvent factors from seed
        assert len(data["items"]) == seed_test_emission_factors["ecoinvent_count"], \
            f"Expected {seed_test_emission_factors['ecoinvent_count']} Ecoinvent factors, got {len(data['items'])}"


# ============================================================================
# Test Scenario 4: GET /api/v1/emission-factors - Filter by geography
# ============================================================================

class TestFilterByGeography:
    """Test filtering by geography parameter"""

    def test_filter_by_global_geography(self, client, seed_test_emission_factors):
        """Test filtering for global (GLO) emission factors"""
        response = client.get("/api/v1/emission-factors?geography=GLO")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be GLO
        for item in data["items"]:
            assert item["geography"] == "GLO", \
                f"Factor {item['activity_name']} should be GLO"

        # Should return 6 GLO factors from seed
        assert len(data["items"]) == seed_test_emission_factors["glo_count"], \
            f"Expected {seed_test_emission_factors['glo_count']} GLO factors, got {len(data['items'])}"

    def test_filter_by_us_geography(self, client, seed_test_emission_factors):
        """Test filtering for US emission factors"""
        response = client.get("/api/v1/emission-factors?geography=US")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be US
        for item in data["items"]:
            assert item["geography"] == "US", \
                f"Factor {item['activity_name']} should be US"

        # Should return 2 US factors from seed
        assert len(data["items"]) == seed_test_emission_factors["us_count"], \
            f"Expected {seed_test_emission_factors['us_count']} US factors, got {len(data['items'])}"

    def test_filter_by_eu_geography(self, client, seed_test_emission_factors):
        """Test filtering for EU emission factors"""
        response = client.get("/api/v1/emission-factors?geography=EU")
        data = response.json()

        assert response.status_code == 200

        # All returned items should be EU
        for item in data["items"]:
            assert item["geography"] == "EU", \
                f"Factor {item['activity_name']} should be EU"

        # Should return 2 EU factors from seed
        assert len(data["items"]) == seed_test_emission_factors["eu_count"], \
            f"Expected {seed_test_emission_factors['eu_count']} EU factors, got {len(data['items'])}"


# ============================================================================
# Test Scenario 5: GET /api/v1/emission-factors - Filter by unit
# ============================================================================

class TestFilterByUnit:
    """Test filtering by unit parameter"""

    def test_filter_by_kg_unit(self, client, seed_test_emission_factors):
        """Test filtering for kg unit emission factors"""
        response = client.get("/api/v1/emission-factors?unit=kg")
        data = response.json()

        assert response.status_code == 200

        # All returned items should have kg unit
        for item in data["items"]:
            assert item["unit"] == "kg", \
                f"Factor {item['activity_name']} should have unit kg"

        # Should return 7 kg factors from seed
        assert len(data["items"]) == seed_test_emission_factors["kg_unit_count"], \
            f"Expected {seed_test_emission_factors['kg_unit_count']} kg factors, got {len(data['items'])}"

    def test_filter_by_kwh_unit(self, client, seed_test_emission_factors):
        """Test filtering for kWh unit emission factors"""
        response = client.get("/api/v1/emission-factors?unit=kWh")
        data = response.json()

        assert response.status_code == 200

        # All returned items should have kWh unit
        for item in data["items"]:
            assert item["unit"] == "kWh", \
                f"Factor {item['activity_name']} should have unit kWh"

        # Should return 1 kWh factor from seed
        assert len(data["items"]) == seed_test_emission_factors["kwh_unit_count"], \
            f"Expected {seed_test_emission_factors['kwh_unit_count']} kWh factors, got {len(data['items'])}"

    def test_filter_by_l_unit(self, client, seed_test_emission_factors):
        """Test filtering for L unit emission factors"""
        response = client.get("/api/v1/emission-factors?unit=L")
        data = response.json()

        assert response.status_code == 200

        # All returned items should have L unit
        for item in data["items"]:
            assert item["unit"] == "L", \
                f"Factor {item['activity_name']} should have unit L"

        # Should return 1 L factor from seed
        assert len(data["items"]) == seed_test_emission_factors["l_unit_count"], \
            f"Expected {seed_test_emission_factors['l_unit_count']} L factors, got {len(data['items'])}"


# ============================================================================
# Test Scenario 6: GET /api/v1/emission-factors - Filter by activity_name
# ============================================================================

class TestFilterByActivityName:
    """Test filtering by activity_name parameter (search)"""

    def test_filter_by_exact_activity_name(self, client, seed_test_emission_factors):
        """Test filtering by exact activity name"""
        response = client.get("/api/v1/emission-factors?activity_name=Cotton Fabric")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) >= 1, \
            "Should find at least one Cotton Fabric factor"

        # First item should match
        assert data["items"][0]["activity_name"] == "Cotton Fabric"

    def test_filter_by_partial_activity_name(self, client, seed_test_emission_factors):
        """Test filtering by partial activity name (case-insensitive search)"""
        response = client.get("/api/v1/emission-factors?activity_name=plastic")
        data = response.json()

        assert response.status_code == 200

        # Should find PET Plastic and ABS Plastic
        activity_names = [item["activity_name"] for item in data["items"]]
        assert any("Plastic" in name for name in activity_names), \
            "Should find factors with 'Plastic' in name"

    def test_filter_by_activity_name_no_results(self, client, seed_test_emission_factors):
        """Test filtering by activity name with no matches"""
        response = client.get("/api/v1/emission-factors?activity_name=NonexistentMaterial")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 0, \
            "Should return empty list for non-matching activity name"


# ============================================================================
# Test Scenario 7: GET /api/v1/emission-factors - Combined filters
# ============================================================================

class TestCombinedFilters:
    """Test combining multiple filter parameters"""

    def test_filter_by_source_and_geography(self, client, seed_test_emission_factors):
        """Test filtering by both data_source and geography"""
        response = client.get("/api/v1/emission-factors?data_source=EPA&geography=GLO")
        data = response.json()

        assert response.status_code == 200

        # All items should match both filters
        for item in data["items"]:
            assert item["data_source"] == "EPA", \
                f"Factor {item['activity_name']} should be from EPA"
            assert item["geography"] == "GLO", \
                f"Factor {item['activity_name']} should be GLO"

    def test_filter_by_unit_and_source(self, client, seed_test_emission_factors):
        """Test filtering by unit and data_source"""
        response = client.get("/api/v1/emission-factors?unit=kg&data_source=EPA")
        data = response.json()

        assert response.status_code == 200

        # All items should match both filters
        for item in data["items"]:
            assert item["unit"] == "kg", \
                f"Factor {item['activity_name']} should have unit kg"
            assert item["data_source"] == "EPA", \
                f"Factor {item['activity_name']} should be from EPA"


# ============================================================================
# Test Scenario 8: POST /api/v1/emission-factors - Create custom factor
# ============================================================================

class TestCreateEmissionFactor:
    """Test POST /api/v1/emission-factors endpoint"""

    def test_create_emission_factor_returns_201(self, client):
        """Test that creating emission factor returns 201 Created"""
        new_factor = {
            "activity_name": "Custom Material",
            "co2e_factor": 4.5,
            "unit": "kg",
            "data_source": "Custom",
            "geography": "GLO",
            "reference_year": 2024
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            f"Expected status 201, got {response.status_code}"

    def test_create_emission_factor_returns_id(self, client):
        """Test that created emission factor returns with ID"""
        new_factor = {
            "activity_name": "New Custom Material",
            "co2e_factor": 3.2,
            "unit": "kg",
            "data_source": "Custom",
            "geography": "GLO"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)
        data = response.json()

        assert "id" in data, \
            "Response should include 'id' field"
        assert isinstance(data["id"], str), \
            "ID should be a string"

    def test_create_emission_factor_with_all_fields(self, client):
        """Test creating emission factor with all optional fields"""
        new_factor = {
            "activity_name": "Advanced Material",
            "co2e_factor": 7.8,
            "unit": "kg",
            "data_source": "Research Paper",
            "geography": "US",
            "reference_year": 2024,
            "data_quality_rating": 0.75,
            "uncertainty_min": 6.5,
            "uncertainty_max": 9.1
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)
        data = response.json()

        assert response.status_code == 201
        assert data["activity_name"] == "Advanced Material"
        assert float(data["co2e_factor"]) == 7.8
        assert data["unit"] == "kg"
        assert data["data_source"] == "Research Paper"
        assert data["geography"] == "US"
        assert data["reference_year"] == 2024

    def test_create_emission_factor_with_minimal_fields(self, client):
        """Test creating emission factor with only required fields"""
        new_factor = {
            "activity_name": "Minimal Material",
            "co2e_factor": 2.1,
            "unit": "kg",
            "data_source": "Custom"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)
        data = response.json()

        assert response.status_code == 201
        assert data["activity_name"] == "Minimal Material"
        assert float(data["co2e_factor"]) == 2.1
        # Should have default geography
        assert data["geography"] == "GLO"

    def test_created_factor_appears_in_list(self, client):
        """Test that created emission factor appears in GET list"""
        new_factor = {
            "activity_name": "Unique Test Material",
            "co2e_factor": 5.5,
            "unit": "kg",
            "data_source": "Test"
        }

        # Create factor
        create_response = client.post("/api/v1/emission-factors", json=new_factor)
        assert create_response.status_code == 201

        # List factors
        list_response = client.get("/api/v1/emission-factors")
        list_data = list_response.json()

        # Should find our factor
        activity_names = [item["activity_name"] for item in list_data["items"]]
        assert "Unique Test Material" in activity_names, \
            "Created factor should appear in list"


# ============================================================================
# Test Scenario 9: POST /api/v1/emission-factors - Duplicate prevention
# ============================================================================

class TestDuplicatePrevention:
    """Test duplicate emission factor prevention (409 conflict)"""

    def test_create_duplicate_returns_409(self, client, seed_test_emission_factors):
        """Test that creating duplicate emission factor returns 409 Conflict"""
        # Try to create duplicate of existing Cotton Fabric (EPA, GLO, 2023)
        duplicate_factor = {
            "activity_name": "Cotton Fabric",
            "co2e_factor": 5.0,  # Different value, but same composite key
            "unit": "kg",
            "data_source": "EPA",
            "geography": "GLO",
            "reference_year": 2023
        }

        response = client.post("/api/v1/emission-factors", json=duplicate_factor)

        assert response.status_code == 409, \
            f"Expected status 409 for duplicate, got {response.status_code}"

    def test_duplicate_error_message(self, client, seed_test_emission_factors):
        """Test that 409 response includes helpful error message"""
        duplicate_factor = {
            "activity_name": "Cotton Fabric",
            "co2e_factor": 5.0,
            "unit": "kg",
            "data_source": "EPA",
            "geography": "GLO",
            "reference_year": 2023
        }

        response = client.post("/api/v1/emission-factors", json=duplicate_factor)
        data = response.json()

        assert "detail" in data, \
            "409 response should include 'detail' field"
        assert "already exists" in data["detail"].lower() or "duplicate" in data["detail"].lower(), \
            "Error message should indicate duplicate"

    def test_same_activity_different_source_allowed(self, client, seed_test_emission_factors):
        """Test that same activity with different data_source is allowed"""
        # Cotton Fabric exists with EPA, create with Custom source
        new_factor = {
            "activity_name": "Cotton Fabric",
            "co2e_factor": 5.2,
            "unit": "kg",
            "data_source": "Custom Research",
            "geography": "GLO",
            "reference_year": 2023
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Same activity with different source should be allowed"

    def test_same_activity_different_geography_allowed(self, client, seed_test_emission_factors):
        """Test that same activity with different geography is allowed"""
        # Cotton Fabric exists with GLO, create with US
        new_factor = {
            "activity_name": "Cotton Fabric",
            "co2e_factor": 5.3,
            "unit": "kg",
            "data_source": "EPA",
            "geography": "US",
            "reference_year": 2023
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Same activity with different geography should be allowed"

    def test_same_activity_different_year_allowed(self, client, seed_test_emission_factors):
        """Test that same activity with different reference_year is allowed"""
        # Cotton Fabric exists with 2023, create with 2024
        new_factor = {
            "activity_name": "Cotton Fabric",
            "co2e_factor": 5.1,
            "unit": "kg",
            "data_source": "EPA",
            "geography": "GLO",
            "reference_year": 2024
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Same activity with different reference_year should be allowed"


# ============================================================================
# Test Scenario 10: POST /api/v1/emission-factors - Validation errors
# ============================================================================

class TestValidationErrors:
    """Test validation error handling (422)"""

    def test_missing_required_activity_name(self, client):
        """Test that missing activity_name returns 422"""
        invalid_factor = {
            "co2e_factor": 3.5,
            "unit": "kg",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for missing activity_name, got {response.status_code}"

    def test_missing_required_co2e_factor(self, client):
        """Test that missing co2e_factor returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "unit": "kg",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for missing co2e_factor, got {response.status_code}"

    def test_missing_required_unit(self, client):
        """Test that missing unit returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "co2e_factor": 3.5,
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for missing unit, got {response.status_code}"

    def test_missing_required_data_source(self, client):
        """Test that missing data_source returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "co2e_factor": 3.5,
            "unit": "kg"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for missing data_source, got {response.status_code}"

    def test_negative_co2e_factor(self, client):
        """Test that negative co2e_factor returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "co2e_factor": -3.5,
            "unit": "kg",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for negative co2e_factor, got {response.status_code}"

    def test_invalid_data_type_co2e_factor(self, client):
        """Test that non-numeric co2e_factor returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "co2e_factor": "not-a-number",
            "unit": "kg",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for invalid co2e_factor type, got {response.status_code}"

    def test_empty_activity_name(self, client):
        """Test that empty activity_name returns 422"""
        invalid_factor = {
            "activity_name": "",
            "co2e_factor": 3.5,
            "unit": "kg",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for empty activity_name, got {response.status_code}"

    def test_empty_unit(self, client):
        """Test that empty unit returns 422"""
        invalid_factor = {
            "activity_name": "Test Material",
            "co2e_factor": 3.5,
            "unit": "",
            "data_source": "EPA"
        }

        response = client.post("/api/v1/emission-factors", json=invalid_factor)

        assert response.status_code == 422, \
            f"Expected 422 for empty unit, got {response.status_code}"


# ============================================================================
# Test Scenario 11: Response format validation
# ============================================================================

class TestResponseFormat:
    """Test that responses match API specification format"""

    def test_list_response_has_all_required_fields(self, client, seed_test_emission_factors):
        """Test list response structure"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        # Per API spec: items, total, limit, offset
        required_fields = ["items", "total", "limit", "offset"]
        for field in required_fields:
            assert field in data, \
                f"List response should include '{field}'"

    def test_emission_factor_item_has_all_required_fields(self, client, seed_test_emission_factors):
        """Test individual emission factor structure in list"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        item = data["items"][0]

        # Required fields
        required_fields = [
            "id", "activity_name", "co2e_factor", "unit",
            "data_source", "geography", "reference_year"
        ]
        for field in required_fields:
            assert field in item, \
                f"Emission factor item should include '{field}'"

    def test_created_emission_factor_response_structure(self, client):
        """Test created emission factor response structure"""
        new_factor = {
            "activity_name": "Response Test Material",
            "co2e_factor": 4.2,
            "unit": "kg",
            "data_source": "Test"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)
        data = response.json()

        # Should include all fields
        required_fields = [
            "id", "activity_name", "co2e_factor", "unit",
            "data_source", "geography"
        ]
        for field in required_fields:
            assert field in data, \
                f"Created emission factor should include '{field}'"


# ============================================================================
# Test Scenario 12: Data types validation
# ============================================================================

class TestDataTypes:
    """Test that response data types are correct"""

    def test_emission_factor_id_is_string(self, client, seed_test_emission_factors):
        """Test that emission factor ID is a string"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        item = data["items"][0]
        assert isinstance(item["id"], str), \
            f"Emission factor ID should be string, got {type(item['id'])}"

    def test_co2e_factor_is_numeric(self, client, seed_test_emission_factors):
        """Test that co2e_factor is numeric"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        item = data["items"][0]
        assert isinstance(item["co2e_factor"], (int, float)), \
            f"co2e_factor should be numeric, got {type(item['co2e_factor'])}"
        assert item["co2e_factor"] >= 0, \
            f"co2e_factor should be non-negative, got {item['co2e_factor']}"

    def test_total_is_integer(self, client, seed_test_emission_factors):
        """Test that total count is an integer"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert isinstance(data["total"], int), \
            f"Total should be integer, got {type(data['total'])}"

    def test_reference_year_is_integer_or_null(self, client, seed_test_emission_factors):
        """Test that reference_year is integer or null"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        item = data["items"][0]
        assert isinstance(item["reference_year"], (int, type(None))), \
            f"reference_year should be integer or null, got {type(item['reference_year'])}"


# ============================================================================
# Test Scenario 13: Edge cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_list_emission_factors_with_no_data(self, client):
        """Test listing emission factors when database is empty"""
        response = client.get("/api/v1/emission-factors")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 0, \
            "Empty database should return total=0"
        assert len(data["items"]) == 0, \
            "Empty database should return empty items list"

    def test_pagination_offset_beyond_total(self, client, seed_test_emission_factors):
        """Test offset beyond total count"""
        total_count = seed_test_emission_factors["total_count"]
        response = client.get(f"/api/v1/emission-factors?offset={total_count + 10}")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 0, \
            "Offset beyond total should return empty list"

    def test_filter_with_no_matches(self, client, seed_test_emission_factors):
        """Test filter that matches no records"""
        response = client.get("/api/v1/emission-factors?data_source=NonexistentSource")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 0, \
            "Non-matching filter should return empty list"
        assert data["total"] == 0, \
            "Non-matching filter should return total=0"

    def test_create_with_very_large_co2e_factor(self, client):
        """Test creating emission factor with very large co2e value"""
        new_factor = {
            "activity_name": "High Emission Material",
            "co2e_factor": 999999.99999999,
            "unit": "kg",
            "data_source": "Test"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Should accept large co2e_factor value"

    def test_create_with_very_small_co2e_factor(self, client):
        """Test creating emission factor with very small co2e value"""
        new_factor = {
            "activity_name": "Low Emission Material",
            "co2e_factor": 0.00000001,
            "unit": "kg",
            "data_source": "Test"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Should accept small co2e_factor value"

    def test_create_with_zero_co2e_factor(self, client):
        """Test creating emission factor with zero co2e value"""
        new_factor = {
            "activity_name": "Zero Emission Material",
            "co2e_factor": 0.0,
            "unit": "kg",
            "data_source": "Test"
        }

        response = client.post("/api/v1/emission-factors", json=new_factor)

        assert response.status_code == 201, \
            "Should accept zero co2e_factor value"
