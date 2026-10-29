"""
Test suite for BOM Template System.

TASK-BE-P8-001: BOM Template System (5 Industry Templates)

This test suite validates:
- BOMTemplate generates correct number of components
- ComponentSpec generates quantities within range
- Variant modifiers apply correctly
- Optional components respect probability
- Transport calculation works correctly
- All industry templates are properly configured

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no BOM template classes exist yet)
- Implementation must make tests PASS without modifying tests

Exit Criteria:
- 12+ templates across 5 industries
- 30+ unique component types
- All tests passing
- >95% component mapping coverage
"""

import pytest
from decimal import Decimal
from typing import List, Dict, Any
from unittest.mock import patch


# ============================================================================
# ComponentSpec Unit Tests
# ============================================================================


class TestComponentSpec:
    """Test ComponentSpec dataclass functionality."""

    def test_component_spec_creation_basic(self):
        """Test basic ComponentSpec instantiation with required fields."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="aluminum",
            qty_range=(0.5, 1.5),
            unit="kg",
        )

        assert spec.name == "aluminum"
        assert spec.qty_range == (0.5, 1.5)
        assert spec.unit == "kg"
        assert spec.category == "material"  # default
        assert spec.optional is False  # default
        assert spec.probability == 1.0  # default

    def test_component_spec_creation_full(self):
        """Test ComponentSpec instantiation with all fields."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="lcd_panel",
            qty_range=(0.15, 0.3),
            unit="kg",
            description="LCD display panel",
            category="material",
            optional=True,
            probability=0.7,
        )

        assert spec.name == "lcd_panel"
        assert spec.qty_range == (0.15, 0.3)
        assert spec.unit == "kg"
        assert spec.description == "LCD display panel"
        assert spec.category == "material"
        assert spec.optional is True
        assert spec.probability == 0.7

    def test_generate_quantity_returns_decimal(self):
        """Test generate_quantity returns Decimal type."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="steel",
            qty_range=(1.0, 2.0),
            unit="kg",
        )

        qty = spec.generate_quantity()
        assert isinstance(qty, Decimal)

    def test_generate_quantity_within_range(self):
        """Test generate_quantity returns value within specified range."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="copper",
            qty_range=(0.5, 1.5),
            unit="kg",
        )

        # Test multiple times to ensure statistical validity
        for _ in range(100):
            qty = spec.generate_quantity()
            assert Decimal("0.5") <= qty <= Decimal("1.5"), \
                f"Quantity {qty} not in range [0.5, 1.5]"

    def test_generate_quantity_respects_precision(self):
        """Test generate_quantity rounds to 4 decimal places."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="glass",
            qty_range=(0.1, 0.2),
            unit="kg",
        )

        for _ in range(50):
            qty = spec.generate_quantity()
            # Check precision by converting to string
            str_qty = str(qty)
            if '.' in str_qty:
                decimal_places = len(str_qty.split('.')[1])
                assert decimal_places <= 4, \
                    f"Quantity {qty} has more than 4 decimal places"

    def test_generate_quantity_edge_case_same_min_max(self):
        """Test generate_quantity when min equals max."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        spec = ComponentSpec(
            name="fixed_qty",
            qty_range=(5.0, 5.0),
            unit="kg",
        )

        for _ in range(10):
            qty = spec.generate_quantity()
            assert qty == Decimal("5.0")


# ============================================================================
# BOMTemplate Unit Tests
# ============================================================================


class TestBOMTemplate:
    """Test BOMTemplate dataclass functionality."""

    @pytest.fixture
    def sample_components(self):
        """Create sample components for testing."""
        from backend.services.data_ingestion.bom_templates.base import ComponentSpec

        return [
            ComponentSpec("aluminum", (0.5, 1.0), "kg", "Chassis", "material"),
            ComponentSpec("steel", (0.1, 0.2), "kg", "Fasteners", "material"),
            ComponentSpec("copper", (0.05, 0.1), "kg", "Wiring", "material"),
            ComponentSpec(
                "lcd_panel", (0.15, 0.3), "kg", "Display",
                "material", optional=True, probability=0.7
            ),
            ComponentSpec(
                "electricity_manufacturing", (10, 20), "kWh", "Assembly",
                "energy"
            ),
        ]

    def test_bom_template_creation(self, sample_components):
        """Test basic BOMTemplate instantiation."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
        )

        assert template.name == "laptop"
        assert template.industry == "electronics"
        assert len(template.base_components) == 5
        assert template.typical_mass_kg == 1.0  # default

    def test_bom_template_with_variants(self, sample_components):
        """Test BOMTemplate with variant modifiers."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
            variants={
                "gaming": {"aluminum": 1.5, "electricity_manufacturing": 1.3},
                "ultrabook": {"aluminum": 0.7, "steel": 0.5},
            },
            typical_mass_kg=2.0,
        )

        assert "gaming" in template.variants
        assert "ultrabook" in template.variants
        assert template.variants["gaming"]["aluminum"] == 1.5
        assert template.typical_mass_kg == 2.0

    def test_get_components_no_variant(self, sample_components):
        """Test get_components returns all base components without variant."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
        )

        # Fix random seed for deterministic test
        with patch('random.random', return_value=0.5):  # Below 0.7, so optional included
            components = template.get_components()

        # Should return all non-optional + optional (since 0.5 < 0.7)
        assert len(components) >= 4  # At minimum, non-optional ones

    def test_get_components_with_variant_modifier(self, sample_components):
        """Test get_components applies variant modifiers to quantity ranges."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
            variants={
                "heavy": {"aluminum": 2.0},  # Double aluminum
            },
        )

        # Fix random for optional component
        with patch('random.random', return_value=0.5):
            components = template.get_components(variant="heavy")

        # Find aluminum component
        aluminum = next(c for c in components if c.name == "aluminum")

        # Original range was (0.5, 1.0), with 2.0 modifier should be (1.0, 2.0)
        assert aluminum.qty_range == (1.0, 2.0)

    def test_get_components_variant_removes_component(self, sample_components):
        """Test variant with 0 modifier removes component."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
            variants={
                "no_display": {"lcd_panel": 0},  # Remove LCD
            },
        )

        with patch('random.random', return_value=0.5):
            components = template.get_components(variant="no_display")

        # LCD should not be in components
        component_names = [c.name for c in components]
        assert "lcd_panel" not in component_names

    def test_get_components_optional_excluded_by_probability(self, sample_components):
        """Test optional components excluded when random > probability."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
        )

        # Fix random to 0.9, which is > 0.7 probability
        with patch('random.random', return_value=0.9):
            components = template.get_components()

        # lcd_panel should be excluded (probability 0.7, random 0.9)
        component_names = [c.name for c in components]
        assert "lcd_panel" not in component_names

    def test_get_components_optional_included_by_probability(self, sample_components):
        """Test optional components included when random <= probability."""
        from backend.services.data_ingestion.bom_templates.base import BOMTemplate

        template = BOMTemplate(
            name="laptop",
            industry="electronics",
            base_components=sample_components,
        )

        # Fix random to 0.5, which is < 0.7 probability
        with patch('random.random', return_value=0.5):
            components = template.get_components()

        # lcd_panel should be included (probability 0.7, random 0.5)
        component_names = [c.name for c in components]
        assert "lcd_panel" in component_names


class TestBOMTemplateTransport:
    """Test BOMTemplate transport calculation."""

    def test_calculate_transport_returns_transport_components(self):
        """Test calculate_transport returns transport component specs."""
        from backend.services.data_ingestion.bom_templates.base import (
            BOMTemplate,
            ComponentSpec,
        )

        template = BOMTemplate(
            name="test_product",
            industry="test",
            base_components=[
                ComponentSpec("material", (1.0, 2.0), "kg"),
            ],
            typical_mass_kg=10.0,
        )

        transport_components = template.calculate_transport(
            mass_kg=10.0,
            truck_distance_km=300,
            ship_distance_km=5000,
        )

        assert len(transport_components) == 2

        # Check transport_truck component
        truck = next(c for c in transport_components if c.name == "transport_truck")
        assert truck.unit == "tkm"
        assert truck.category == "transport"

        # Check transport_ship component
        ship = next(c for c in transport_components if c.name == "transport_ship")
        assert ship.unit == "tkm"
        assert ship.category == "transport"

    def test_calculate_transport_correct_tkm_values(self):
        """Test transport calculation produces correct tonne-km values."""
        from backend.services.data_ingestion.bom_templates.base import (
            BOMTemplate,
            ComponentSpec,
        )

        template = BOMTemplate(
            name="test_product",
            industry="test",
            base_components=[],
        )

        # 2kg product, 300km truck, 5000km ship
        # truck_tkm = 0.002 tonnes * 300 km = 0.6 tkm
        # ship_tkm = 0.002 tonnes * 5000 km = 10 tkm
        transport = template.calculate_transport(
            mass_kg=2.0,
            truck_distance_km=300,
            ship_distance_km=5000,
        )

        truck = next(c for c in transport if c.name == "transport_truck")
        ship = next(c for c in transport if c.name == "transport_ship")

        # With 10% variance: truck range should be around (0.54, 0.66)
        expected_truck_mid = 0.6
        assert truck.qty_range[0] == pytest.approx(expected_truck_mid * 0.9, rel=0.01)
        assert truck.qty_range[1] == pytest.approx(expected_truck_mid * 1.1, rel=0.01)

        # ship range should be around (9, 11)
        expected_ship_mid = 10.0
        assert ship.qty_range[0] == pytest.approx(expected_ship_mid * 0.9, rel=0.01)
        assert ship.qty_range[1] == pytest.approx(expected_ship_mid * 1.1, rel=0.01)


# ============================================================================
# Industry Template Integration Tests
# ============================================================================


class TestElectronicsTemplates:
    """Test electronics industry BOM templates."""

    def test_electronics_templates_exist(self):
        """Test electronics templates module exports templates."""
        from backend.services.data_ingestion.bom_templates.electronics_boms import (
            ELECTRONICS_TEMPLATES,
        )

        assert isinstance(ELECTRONICS_TEMPLATES, dict)
        assert len(ELECTRONICS_TEMPLATES) >= 3, \
            "Electronics should have at least 3 templates (laptop, smartphone, monitor)"

    def test_laptop_template_components(self):
        """Test laptop template has expected components."""
        from backend.services.data_ingestion.bom_templates.electronics_boms import (
            LAPTOP_TEMPLATE,
        )

        assert LAPTOP_TEMPLATE.name == "laptop"
        assert LAPTOP_TEMPLATE.industry == "electronics"
        assert len(LAPTOP_TEMPLATE.base_components) >= 10, \
            "Laptop should have at least 10 base components"

        component_names = [c.name for c in LAPTOP_TEMPLATE.base_components]

        # Check for key electronics components
        assert "aluminum" in component_names
        assert "copper" in component_names
        assert "pcb_board" in component_names or "semiconductor" in component_names

    def test_smartphone_template_components(self):
        """Test smartphone template has expected components."""
        from backend.services.data_ingestion.bom_templates.electronics_boms import (
            SMARTPHONE_TEMPLATE,
        )

        assert SMARTPHONE_TEMPLATE.name == "smartphone"
        assert SMARTPHONE_TEMPLATE.industry == "electronics"
        assert len(SMARTPHONE_TEMPLATE.base_components) >= 8

        # Smartphone should be lighter than laptop
        assert SMARTPHONE_TEMPLATE.typical_mass_kg < 1.0

    def test_monitor_template_components(self):
        """Test monitor template has expected components."""
        from backend.services.data_ingestion.bom_templates.electronics_boms import (
            MONITOR_TEMPLATE,
        )

        assert MONITOR_TEMPLATE.name == "monitor"
        assert MONITOR_TEMPLATE.industry == "electronics"
        assert len(MONITOR_TEMPLATE.base_components) >= 8


class TestApparelTemplates:
    """Test apparel industry BOM templates."""

    def test_apparel_templates_exist(self):
        """Test apparel templates module exports templates."""
        from backend.services.data_ingestion.bom_templates.apparel_boms import (
            APPAREL_TEMPLATES,
        )

        assert isinstance(APPAREL_TEMPLATES, dict)
        assert len(APPAREL_TEMPLATES) >= 3, \
            "Apparel should have at least 3 templates (tshirt, jeans, shoes)"

    def test_tshirt_template_components(self):
        """Test t-shirt template has expected components."""
        from backend.services.data_ingestion.bom_templates.apparel_boms import (
            TSHIRT_TEMPLATE,
        )

        assert TSHIRT_TEMPLATE.name == "tshirt"
        assert TSHIRT_TEMPLATE.industry == "apparel"
        assert len(TSHIRT_TEMPLATE.base_components) >= 5

        component_names = [c.name for c in TSHIRT_TEMPLATE.base_components]
        assert "textile_cotton" in component_names

    def test_jeans_template_components(self):
        """Test jeans template has expected components."""
        from backend.services.data_ingestion.bom_templates.apparel_boms import (
            JEANS_TEMPLATE,
        )

        assert JEANS_TEMPLATE.name == "jeans"
        assert JEANS_TEMPLATE.industry == "apparel"
        assert len(JEANS_TEMPLATE.base_components) >= 6

    def test_shoes_template_components(self):
        """Test shoes template has expected components."""
        from backend.services.data_ingestion.bom_templates.apparel_boms import (
            SHOES_TEMPLATE,
        )

        assert SHOES_TEMPLATE.name == "shoes"
        assert SHOES_TEMPLATE.industry == "apparel"
        assert len(SHOES_TEMPLATE.base_components) >= 6

        component_names = [c.name for c in SHOES_TEMPLATE.base_components]
        assert "rubber" in component_names


class TestAutomotiveTemplates:
    """Test automotive industry BOM templates."""

    def test_automotive_templates_exist(self):
        """Test automotive templates module exports templates."""
        from backend.services.data_ingestion.bom_templates.automotive_boms import (
            AUTOMOTIVE_TEMPLATES,
        )

        assert isinstance(AUTOMOTIVE_TEMPLATES, dict)
        assert len(AUTOMOTIVE_TEMPLATES) >= 2, \
            "Automotive should have at least 2 templates"

    def test_car_seat_template_components(self):
        """Test car seat template has expected components."""
        from backend.services.data_ingestion.bom_templates.automotive_boms import (
            CAR_SEAT_TEMPLATE,
        )

        assert CAR_SEAT_TEMPLATE.name == "car_seat"
        assert CAR_SEAT_TEMPLATE.industry == "automotive"
        assert len(CAR_SEAT_TEMPLATE.base_components) >= 6

        component_names = [c.name for c in CAR_SEAT_TEMPLATE.base_components]
        assert "steel" in component_names

    def test_wheel_assembly_template_components(self):
        """Test wheel assembly template has expected components."""
        from backend.services.data_ingestion.bom_templates.automotive_boms import (
            WHEEL_ASSEMBLY_TEMPLATE,
        )

        assert WHEEL_ASSEMBLY_TEMPLATE.name == "wheel_assembly"
        assert WHEEL_ASSEMBLY_TEMPLATE.industry == "automotive"
        assert len(WHEEL_ASSEMBLY_TEMPLATE.base_components) >= 4

        component_names = [c.name for c in WHEEL_ASSEMBLY_TEMPLATE.base_components]
        assert "rubber" in component_names
        assert "aluminum" in component_names


class TestConstructionTemplates:
    """Test construction industry BOM templates."""

    def test_construction_templates_exist(self):
        """Test construction templates module exports templates."""
        from backend.services.data_ingestion.bom_templates.construction_boms import (
            CONSTRUCTION_TEMPLATES,
        )

        assert isinstance(CONSTRUCTION_TEMPLATES, dict)
        assert len(CONSTRUCTION_TEMPLATES) >= 2, \
            "Construction should have at least 2 templates"

    def test_window_unit_template_components(self):
        """Test window unit template has expected components."""
        from backend.services.data_ingestion.bom_templates.construction_boms import (
            WINDOW_UNIT_TEMPLATE,
        )

        assert WINDOW_UNIT_TEMPLATE.name == "window_unit"
        assert WINDOW_UNIT_TEMPLATE.industry == "construction"
        assert len(WINDOW_UNIT_TEMPLATE.base_components) >= 5

        component_names = [c.name for c in WINDOW_UNIT_TEMPLATE.base_components]
        assert "glass" in component_names
        assert "aluminum" in component_names

    def test_door_assembly_template_components(self):
        """Test door assembly template has expected components."""
        from backend.services.data_ingestion.bom_templates.construction_boms import (
            DOOR_ASSEMBLY_TEMPLATE,
        )

        assert DOOR_ASSEMBLY_TEMPLATE.name == "door_assembly"
        assert DOOR_ASSEMBLY_TEMPLATE.industry == "construction"
        assert len(DOOR_ASSEMBLY_TEMPLATE.base_components) >= 5


class TestFoodBeverageTemplates:
    """Test food & beverage industry BOM templates."""

    def test_food_beverage_templates_exist(self):
        """Test food & beverage templates module exports templates."""
        from backend.services.data_ingestion.bom_templates.food_beverage_boms import (
            FOOD_BEVERAGE_TEMPLATES,
        )

        assert isinstance(FOOD_BEVERAGE_TEMPLATES, dict)
        assert len(FOOD_BEVERAGE_TEMPLATES) >= 2, \
            "Food & Beverage should have at least 2 templates"

    def test_beverage_bottle_template_components(self):
        """Test beverage bottle template has expected components."""
        from backend.services.data_ingestion.bom_templates.food_beverage_boms import (
            BEVERAGE_BOTTLE_TEMPLATE,
        )

        assert BEVERAGE_BOTTLE_TEMPLATE.name == "beverage_bottle"
        assert BEVERAGE_BOTTLE_TEMPLATE.industry == "food_beverage"
        assert len(BEVERAGE_BOTTLE_TEMPLATE.base_components) >= 4

        component_names = [c.name for c in BEVERAGE_BOTTLE_TEMPLATE.base_components]
        assert "plastic_pet" in component_names

    def test_canned_food_template_components(self):
        """Test canned food template has expected components."""
        from backend.services.data_ingestion.bom_templates.food_beverage_boms import (
            CANNED_FOOD_TEMPLATE,
        )

        assert CANNED_FOOD_TEMPLATE.name == "canned_food"
        assert CANNED_FOOD_TEMPLATE.industry == "food_beverage"
        assert len(CANNED_FOOD_TEMPLATE.base_components) >= 4


# ============================================================================
# ALL_TEMPLATES Aggregation Tests
# ============================================================================


class TestAllTemplates:
    """Test ALL_TEMPLATES aggregation and coverage."""

    def test_all_templates_structure(self):
        """Test ALL_TEMPLATES has correct structure."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        assert isinstance(ALL_TEMPLATES, dict)
        assert len(ALL_TEMPLATES) == 5, "Should have 5 industries"

        expected_industries = [
            "electronics",
            "apparel",
            "automotive",
            "construction",
            "food_beverage",
        ]
        for industry in expected_industries:
            assert industry in ALL_TEMPLATES, f"Missing industry: {industry}"

    def test_minimum_template_count(self):
        """Test total number of templates meets minimum."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        total_templates = sum(len(templates) for templates in ALL_TEMPLATES.values())
        assert total_templates >= 12, \
            f"Should have at least 12 templates, found {total_templates}"

    def test_unique_component_count(self):
        """Test total unique component types across all templates."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        all_component_names = set()
        for industry_templates in ALL_TEMPLATES.values():
            for template in industry_templates.values():
                for component in template.base_components:
                    all_component_names.add(component.name)

        assert len(all_component_names) >= 30, \
            f"Should have at least 30 unique components, found {len(all_component_names)}"

    def test_all_templates_generate_valid_components(self):
        """Test all templates can generate valid components."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        for industry, templates in ALL_TEMPLATES.items():
            for template_name, template in templates.items():
                components = template.get_components()

                assert len(components) > 0, \
                    f"Template {industry}/{template_name} has no components"

                for component in components:
                    qty = component.generate_quantity()
                    assert isinstance(qty, Decimal), \
                        f"Component {component.name} did not return Decimal"
                    assert qty > 0, \
                        f"Component {component.name} has non-positive quantity"


# ============================================================================
# Component Mapping Coverage Tests
# ============================================================================


class TestComponentMappingCoverage:
    """Test that all components can be mapped to emission factors."""

    def test_all_components_in_mapping_config(self):
        """Test all component names exist in mapping configuration."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES
        import json
        from pathlib import Path

        # Load mapping configuration
        mapping_path = Path(__file__).parent.parent.parent.parent / "data" / "emission_factor_mappings.json"

        if not mapping_path.exists():
            pytest.skip("Mapping config file not found")

        with open(mapping_path, 'r') as f:
            config = json.load(f)

        mappings = config.get("mappings", {})
        aliases = config.get("aliases", {})

        # Collect all component names
        all_component_names = set()
        for industry_templates in ALL_TEMPLATES.values():
            for template in industry_templates.values():
                for component in template.base_components:
                    all_component_names.add(component.name)

        # Check mapping coverage
        mapped_count = 0
        unmapped = []

        for name in all_component_names:
            # Check if name is in mappings or aliases
            if name in mappings or name in aliases:
                mapped_count += 1
            else:
                # Check if any mapping key is a substring
                found = False
                for mapping_key in mappings.keys():
                    if mapping_key in name or name in mapping_key:
                        found = True
                        break
                if found:
                    mapped_count += 1
                else:
                    unmapped.append(name)

        coverage_pct = (mapped_count / len(all_component_names)) * 100

        # Report unmapped for debugging
        if unmapped:
            print(f"\nUnmapped components: {unmapped}")

        assert coverage_pct >= 95, \
            f"Component mapping coverage {coverage_pct:.1f}% is below 95%"


# ============================================================================
# Template Variant Tests
# ============================================================================


class TestTemplateVariants:
    """Test template variant functionality across industries."""

    def test_electronics_variants(self):
        """Test electronics templates have variants."""
        from backend.services.data_ingestion.bom_templates.electronics_boms import (
            LAPTOP_TEMPLATE,
        )

        assert len(LAPTOP_TEMPLATE.variants) > 0, "Laptop should have variants"

    def test_apparel_variants(self):
        """Test apparel templates have variants."""
        from backend.services.data_ingestion.bom_templates.apparel_boms import (
            JEANS_TEMPLATE,
        )

        assert len(JEANS_TEMPLATE.variants) > 0, "Jeans should have variants"

    def test_automotive_variants(self):
        """Test automotive templates have variants."""
        from backend.services.data_ingestion.bom_templates.automotive_boms import (
            CAR_SEAT_TEMPLATE,
        )

        assert len(CAR_SEAT_TEMPLATE.variants) > 0, "Car seat should have variants"

    def test_variant_modifiers_are_numeric(self):
        """Test all variant modifiers are valid numbers."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        for industry, templates in ALL_TEMPLATES.items():
            for template_name, template in templates.items():
                for variant_name, modifiers in template.variants.items():
                    for component_name, modifier_value in modifiers.items():
                        assert isinstance(modifier_value, (int, float)), \
                            f"Modifier for {industry}/{template_name}/{variant_name}/{component_name} " \
                            f"is not numeric: {modifier_value}"
                        assert modifier_value >= 0, \
                            f"Negative modifier for {industry}/{template_name}/{variant_name}/{component_name}"


# ============================================================================
# Category Distribution Tests
# ============================================================================


class TestCategoryDistribution:
    """Test component category distribution across templates."""

    def test_templates_have_material_components(self):
        """Test all templates have at least one material component."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        for industry, templates in ALL_TEMPLATES.items():
            for template_name, template in templates.items():
                material_count = sum(
                    1 for c in template.base_components if c.category == "material"
                )
                assert material_count > 0, \
                    f"{industry}/{template_name} has no material components"

    def test_templates_have_energy_components(self):
        """Test templates have energy components (manufacturing)."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        templates_with_energy = 0
        total_templates = 0

        for industry, templates in ALL_TEMPLATES.items():
            for template_name, template in templates.items():
                total_templates += 1
                energy_count = sum(
                    1 for c in template.base_components if c.category == "energy"
                )
                if energy_count > 0:
                    templates_with_energy += 1

        # At least 80% of templates should have energy components
        energy_coverage = templates_with_energy / total_templates * 100
        assert energy_coverage >= 80, \
            f"Only {energy_coverage:.1f}% templates have energy components, expected >= 80%"

    def test_category_values_valid(self):
        """Test all category values are from allowed set."""
        from backend.services.data_ingestion.bom_templates import ALL_TEMPLATES

        allowed_categories = {"material", "energy", "transport", "other"}

        for industry, templates in ALL_TEMPLATES.items():
            for template_name, template in templates.items():
                for component in template.base_components:
                    assert component.category in allowed_categories, \
                        f"Invalid category '{component.category}' in " \
                        f"{industry}/{template_name}/{component.name}"
