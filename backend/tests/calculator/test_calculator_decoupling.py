"""
Test suite for calculator decoupling from ORM.

TASK-CALC-P7-022: Decouple Calculator from ORM + Add Emission Factor Cache

Tests that verify:
1. Calculator does NOT import SQLAlchemy directly
2. Emission factor provider interface exists
3. Calculator works with injected dependencies (mock providers)
4. Missing emission factors raise appropriate errors

Following TDD methodology - tests written BEFORE implementation.
These tests should FAIL initially until decoupling is implemented.
"""

import ast
import importlib
import inspect
import pytest
from dataclasses import dataclass
from typing import Dict, Optional
from abc import ABC, abstractmethod


# ==================== Test Data Classes ====================
# These represent the expected interface for the decoupled calculator


@dataclass(frozen=True)
class EmissionFactorDTO:
    """
    Data transfer object for emission factors - no ORM dependency.

    This is what the provider interface should return.
    """

    id: str
    category: str
    co2e_kg: float
    unit: str
    data_source: str
    uncertainty: Optional[float] = None


@dataclass
class BOMItem:
    """Bill of Materials item for calculation input."""

    material: str
    quantity: float
    unit: str


@dataclass
class ComponentBreakdown:
    """Breakdown of emissions by component."""

    material: str
    co2e: float
    quantity: float = 0.0
    unit: str = "kg"
    emission_factor: float = 0.0


@dataclass
class CalculationResult:
    """Result of PCF calculation."""

    total_co2e: float
    breakdown: list
    calculation_method: str = "attributional"


# ==================== Mock Providers ====================


class MockEmissionFactorProvider:
    """
    Mock implementation of EmissionFactorProvider for testing.

    Allows tests to inject specific emission factors without database.
    """

    def __init__(self, factors: Dict[str, EmissionFactorDTO]):
        """
        Initialize with dictionary of emission factors.

        Args:
            factors: Dict mapping category name to EmissionFactorDTO
        """
        self._factors = factors
        self.call_count = 0
        self.categories_requested: list[str] = []

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """Get emission factor by category."""
        self.call_count += 1
        self.categories_requested.append(category)
        return self._factors.get(category)

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """Get all emission factors."""
        self.call_count += 1
        return self._factors.copy()


class TrackingEmissionFactorProvider:
    """
    Provider wrapper that tracks call count for testing cache behavior.
    """

    def __init__(self, wrapped_provider):
        self._wrapped = wrapped_provider
        self.call_count = 0

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        """Get emission factor, tracking call count."""
        self.call_count += 1
        return await self._wrapped.get_by_category(category)

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        """Get all emission factors, tracking call count."""
        self.call_count += 1
        return await self._wrapped.get_all()


# ==================== Test Classes ====================


class TestCalculatorNoORMImports:
    """Test that calculator module has no direct SQLAlchemy imports."""

    def test_pcf_calculator_has_no_sqlalchemy_imports(self):
        """
        Scenario: Calculator module must not import SQLAlchemy directly

        Given: The pcf_calculator.py module
        When: We analyze its imports
        Then: No SQLAlchemy imports should be present at module level

        This ensures the calculator is decoupled from the ORM layer.
        """
        # Read the source code of pcf_calculator
        import backend.calculator.pcf_calculator as pcf_module

        source_file = inspect.getfile(pcf_module)
        with open(source_file, "r") as f:
            source_code = f.read()

        # Parse the AST to find imports
        tree = ast.parse(source_code)

        sqlalchemy_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "sqlalchemy" in alias.name.lower():
                        sqlalchemy_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and "sqlalchemy" in node.module.lower():
                    sqlalchemy_imports.append(node.module)

        assert len(sqlalchemy_imports) == 0, (
            f"Calculator module should not import SQLAlchemy directly. "
            f"Found imports: {sqlalchemy_imports}. "
            "Use dependency injection with EmissionFactorProvider instead."
        )

    def test_pcf_calculator_class_has_no_session_parameter(self):
        """
        Scenario: PCFCalculator class should not require db_session

        Given: The PCFCalculator class
        When: We inspect its __init__ method
        Then: It should not have a db_session or session parameter

        The calculator should receive an EmissionFactorProvider instead.
        """
        from backend.calculator.pcf_calculator import PCFCalculator

        init_sig = inspect.signature(PCFCalculator.__init__)
        params = list(init_sig.parameters.keys())

        # Remove 'self' from params
        params = [p for p in params if p != "self"]

        session_params = [
            p
            for p in params
            if "session" in p.lower() or p == "db" or p == "db_session"
        ]

        assert len(session_params) == 0, (
            f"PCFCalculator should not have session parameters. "
            f"Found: {session_params}. "
            "Use EmissionFactorProvider dependency injection instead."
        )


class TestEmissionFactorProviderInterface:
    """Test that EmissionFactorProvider interface exists and is correct."""

    def test_emission_factor_provider_interface_exists(self):
        """
        Scenario: EmissionFactorProvider interface must exist

        Given: The calculator module
        When: We import from providers module
        Then: EmissionFactorProvider abstract class should be available
        """
        try:
            from backend.calculator.providers import EmissionFactorProvider

            # Verify it's abstract
            assert inspect.isabstract(EmissionFactorProvider) or hasattr(
                EmissionFactorProvider, "get_by_category"
            ), "EmissionFactorProvider should be abstract or have abstract methods"
        except ImportError as e:
            pytest.fail(
                f"EmissionFactorProvider interface not found. "
                f"Create backend/calculator/providers.py with the interface. "
                f"Error: {e}"
            )

    def test_emission_factor_dto_exists(self):
        """
        Scenario: EmissionFactorDTO must exist for ORM-free data transfer

        Given: The calculator module
        When: We import from providers module
        Then: EmissionFactorDTO dataclass should be available
        """
        try:
            from backend.calculator.providers import EmissionFactorDTO

            # Verify it has required fields
            from dataclasses import fields

            field_names = [f.name for f in fields(EmissionFactorDTO)]
            required_fields = ["id", "category", "co2e_kg", "unit", "data_source"]

            for field in required_fields:
                assert field in field_names, (
                    f"EmissionFactorDTO missing required field: {field}"
                )
        except ImportError as e:
            pytest.fail(
                f"EmissionFactorDTO not found. "
                f"Create backend/calculator/providers.py with the DTO. "
                f"Error: {e}"
            )

    def test_provider_has_get_by_category_method(self):
        """
        Scenario: Provider interface must have get_by_category method

        Given: The EmissionFactorProvider interface
        When: We inspect its methods
        Then: get_by_category(category: str) should be defined
        """
        try:
            from backend.calculator.providers import EmissionFactorProvider

            assert hasattr(
                EmissionFactorProvider, "get_by_category"
            ), "EmissionFactorProvider must have get_by_category method"

            # Check method signature
            method = getattr(EmissionFactorProvider, "get_by_category")
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            assert "category" in params, (
                "get_by_category must accept 'category' parameter"
            )
        except ImportError:
            pytest.fail("EmissionFactorProvider not found")

    def test_provider_has_get_all_method(self):
        """
        Scenario: Provider interface must have get_all method

        Given: The EmissionFactorProvider interface
        When: We inspect its methods
        Then: get_all() should be defined
        """
        try:
            from backend.calculator.providers import EmissionFactorProvider

            assert hasattr(
                EmissionFactorProvider, "get_all"
            ), "EmissionFactorProvider must have get_all method"
        except ImportError:
            pytest.fail("EmissionFactorProvider not found")


class TestCalculatorWithInjectedDependencies:
    """Test that calculator works with injected mock providers."""

    @pytest.mark.asyncio
    async def test_calculator_with_mock_provider_simple_calculation(self):
        """
        Scenario 1: Calculator with Injected EF Provider

        Given: A mock emission factor provider with known values
        When: calculate() is called with BOM items
        Then: Correct total_co2e is returned (quantity * emission_factor)

        Input:
            - steel: 10kg, emission factor 2.5 kg CO2e/kg
            - aluminum: 5kg, emission factor 8.1 kg CO2e/kg

        Expected:
            - total_co2e = (10 * 2.5) + (5 * 8.1) = 25.0 + 40.5 = 65.5
        """
        # This test will fail until the decoupled calculator is implemented
        try:
            from backend.calculator.pcf_calculator import PCFCalculator
            from backend.calculator.providers import EmissionFactorProvider, EmissionFactorDTO
        except ImportError:
            pytest.fail(
                "Decoupled calculator imports not available. "
                "Implement backend/calculator/providers.py first."
            )

        # Arrange: Create mock provider with known emission factors
        mock_ef_provider = MockEmissionFactorProvider(
            {
                "steel": EmissionFactorDTO(
                    id="ef-1",
                    category="steel",
                    co2e_kg=2.5,
                    unit="kg",
                    data_source="EPA",
                ),
                "aluminum": EmissionFactorDTO(
                    id="ef-2",
                    category="aluminum",
                    co2e_kg=8.1,
                    unit="kg",
                    data_source="EPA",
                ),
            }
        )

        # Act: Create calculator with injected provider
        calculator = PCFCalculator(ef_provider=mock_ef_provider)

        bom_items = [
            BOMItem(material="steel", quantity=10, unit="kg"),
            BOMItem(material="aluminum", quantity=5, unit="kg"),
        ]

        result = await calculator.calculate(
            product_id="prod-1", bom_items=bom_items
        )

        # Assert
        assert result.total_co2e == pytest.approx(65.5, rel=0.01), (
            f"Expected 65.5 kg CO2e, got {result.total_co2e}"
        )

        # Verify breakdown
        assert len(result.breakdown) == 2
        steel_breakdown = next(
            (b for b in result.breakdown if b.material == "steel"), None
        )
        aluminum_breakdown = next(
            (b for b in result.breakdown if b.material == "aluminum"), None
        )

        assert steel_breakdown is not None
        assert steel_breakdown.co2e == pytest.approx(25.0, rel=0.01)

        assert aluminum_breakdown is not None
        assert aluminum_breakdown.co2e == pytest.approx(40.5, rel=0.01)

    @pytest.mark.asyncio
    async def test_calculator_missing_emission_factor_raises_error(self):
        """
        Scenario 2: Missing Emission Factor

        Given: A mock provider with empty emission factors
        When: calculate() is called with unknown material
        Then: EmissionFactorNotFoundError is raised with clear message
        """
        try:
            from backend.calculator.pcf_calculator import PCFCalculator
            from backend.calculator.exceptions import EmissionFactorNotFoundError
        except ImportError:
            pytest.fail(
                "Decoupled calculator imports not available. "
                "Implement backend/calculator/exceptions.py with EmissionFactorNotFoundError."
            )

        # Arrange: Create mock provider with no emission factors
        mock_ef_provider = MockEmissionFactorProvider({})

        # Act & Assert
        calculator = PCFCalculator(ef_provider=mock_ef_provider)

        bom_items = [BOMItem(material="unknown", quantity=10, unit="kg")]

        with pytest.raises(EmissionFactorNotFoundError) as exc_info:
            await calculator.calculate(product_id="prod-1", bom_items=bom_items)

        assert "unknown" in str(exc_info.value).lower(), (
            f"Error message should mention the missing category 'unknown'. "
            f"Got: {exc_info.value}"
        )

    @pytest.mark.asyncio
    async def test_calculator_provider_called_for_each_material(self):
        """
        Scenario: Provider is called once per unique material

        Given: A tracking mock provider
        When: calculate() is called with 3 different materials
        Then: Provider's get_by_category is called 3 times
        """
        try:
            from backend.calculator.pcf_calculator import PCFCalculator
            from backend.calculator.providers import EmissionFactorDTO
        except ImportError:
            pytest.fail("Decoupled calculator imports not available.")

        # Arrange
        base_provider = MockEmissionFactorProvider(
            {
                "steel": EmissionFactorDTO(
                    id="ef-1",
                    category="steel",
                    co2e_kg=2.5,
                    unit="kg",
                    data_source="EPA",
                ),
                "plastic": EmissionFactorDTO(
                    id="ef-2",
                    category="plastic",
                    co2e_kg=3.0,
                    unit="kg",
                    data_source="EPA",
                ),
                "glass": EmissionFactorDTO(
                    id="ef-3",
                    category="glass",
                    co2e_kg=1.2,
                    unit="kg",
                    data_source="EPA",
                ),
            }
        )

        tracking_provider = TrackingEmissionFactorProvider(base_provider)

        # Act
        calculator = PCFCalculator(ef_provider=tracking_provider)

        bom_items = [
            BOMItem(material="steel", quantity=5, unit="kg"),
            BOMItem(material="plastic", quantity=3, unit="kg"),
            BOMItem(material="glass", quantity=2, unit="kg"),
        ]

        await calculator.calculate(product_id="prod-1", bom_items=bom_items)

        # Assert: Provider called 3 times (once per material)
        assert tracking_provider.call_count == 3, (
            f"Expected 3 provider calls, got {tracking_provider.call_count}"
        )

    @pytest.mark.asyncio
    async def test_calculator_zero_quantity_item(self):
        """
        Scenario: Zero quantity BOM item

        Given: A BOM with zero quantity item
        When: calculate() is called
        Then: Result includes zero emissions for that item
        """
        try:
            from backend.calculator.pcf_calculator import PCFCalculator
            from backend.calculator.providers import EmissionFactorDTO
        except ImportError:
            pytest.fail("Decoupled calculator imports not available.")

        mock_ef_provider = MockEmissionFactorProvider(
            {
                "steel": EmissionFactorDTO(
                    id="ef-1",
                    category="steel",
                    co2e_kg=2.5,
                    unit="kg",
                    data_source="EPA",
                ),
            }
        )

        calculator = PCFCalculator(ef_provider=mock_ef_provider)

        bom_items = [BOMItem(material="steel", quantity=0, unit="kg")]

        result = await calculator.calculate(
            product_id="prod-1", bom_items=bom_items
        )

        assert result.total_co2e == pytest.approx(0.0, abs=0.001)

    @pytest.mark.asyncio
    async def test_calculator_accepts_provider_via_constructor(self):
        """
        Scenario: Calculator must accept ef_provider via constructor

        Given: A PCFCalculator class
        When: Instantiated with ef_provider parameter
        Then: Calculator uses the provided provider
        """
        try:
            from backend.calculator.pcf_calculator import PCFCalculator
        except ImportError:
            pytest.fail("PCFCalculator not available")

        # Check __init__ signature accepts ef_provider
        init_sig = inspect.signature(PCFCalculator.__init__)
        params = list(init_sig.parameters.keys())

        assert "ef_provider" in params, (
            "PCFCalculator.__init__ must accept 'ef_provider' parameter. "
            f"Current parameters: {params}"
        )


class TestSQLAlchemyProviderExists:
    """Test that SQLAlchemy provider implementation exists for integration."""

    def test_sqlalchemy_provider_exists(self):
        """
        Scenario: SQLAlchemy implementation of provider exists

        Given: The providers module
        When: We import SQLAlchemyEmissionFactorProvider
        Then: Class should be available

        This is needed for actual database integration.
        """
        try:
            from backend.calculator.sqlalchemy_provider import (
                SQLAlchemyEmissionFactorProvider,
            )

            # Verify it accepts session in constructor
            init_sig = inspect.signature(SQLAlchemyEmissionFactorProvider.__init__)
            params = list(init_sig.parameters.keys())

            assert "session" in params or any("session" in p.lower() for p in params), (
                "SQLAlchemyEmissionFactorProvider must accept session parameter"
            )
        except ImportError as e:
            pytest.fail(
                f"SQLAlchemyEmissionFactorProvider not found. "
                f"Create backend/calculator/sqlalchemy_provider.py. "
                f"Error: {e}"
            )

    def test_sqlalchemy_provider_implements_interface(self):
        """
        Scenario: SQLAlchemy provider implements EmissionFactorProvider

        Given: The SQLAlchemyEmissionFactorProvider class
        When: We check its methods
        Then: It should have get_by_category and get_all methods
        """
        try:
            from backend.calculator.sqlalchemy_provider import (
                SQLAlchemyEmissionFactorProvider,
            )

            assert hasattr(SQLAlchemyEmissionFactorProvider, "get_by_category"), (
                "SQLAlchemyEmissionFactorProvider must have get_by_category method"
            )
            assert hasattr(SQLAlchemyEmissionFactorProvider, "get_all"), (
                "SQLAlchemyEmissionFactorProvider must have get_all method"
            )
        except ImportError:
            pytest.fail("SQLAlchemyEmissionFactorProvider not found")


class TestFastAPIDependencyInjection:
    """Test that FastAPI dependency injection is properly configured."""

    def test_get_ef_provider_dependency_exists(self):
        """
        Scenario: FastAPI dependency for EF provider exists

        Given: The API dependencies module
        When: We import get_ef_provider
        Then: Function should be available
        """
        try:
            from backend.api.dependencies import get_ef_provider

            assert callable(get_ef_provider), "get_ef_provider should be callable"
        except ImportError as e:
            pytest.fail(
                f"get_ef_provider dependency not found. "
                f"Add to backend/api/dependencies.py. "
                f"Error: {e}"
            )

    def test_get_calculator_dependency_exists(self):
        """
        Scenario: FastAPI dependency for calculator exists

        Given: The API dependencies module
        When: We import get_calculator
        Then: Function should be available
        """
        try:
            from backend.api.dependencies import get_calculator

            assert callable(get_calculator), "get_calculator should be callable"
        except ImportError as e:
            pytest.fail(
                f"get_calculator dependency not found. "
                f"Add to backend/api/dependencies.py. "
                f"Error: {e}"
            )
