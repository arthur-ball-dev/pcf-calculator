"""
Test suite for product BOM JSON file validation.

CRITICAL: These tests MUST be written BEFORE formalizing BOM files.
Tests validate structure, content, component references, and expected results
according to TASK-DATA-002 requirements.

Test Scenarios:
1. BOM file existence and JSON validity
2. BOM structure consistency across all files
3. Component references match emission factors
4. Realistic BOMs have expected results
5. Simple BOMs have zero energy/transport (not missing fields)
6. Quantities and units are valid
"""

import json
import pytest
import pandas as pd
from pathlib import Path


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EMISSION_FACTORS_CSV = DATA_DIR / "emission_factors_simple.csv"

# BOM file paths
BOM_FILES = {
    "tshirt_simple": DATA_DIR / "bom_tshirt_simple.json",
    "tshirt_realistic": DATA_DIR / "bom_tshirt_realistic.json",
    "water_bottle_simple": DATA_DIR / "bom_water_bottle_simple.json",
    "water_bottle_realistic": DATA_DIR / "bom_water_bottle_realistic.json",
    "phone_case_simple": DATA_DIR / "bom_phone_case_simple.json",
    "phone_case_realistic": DATA_DIR / "bom_phone_case_realistic.json",
}

REALISTIC_BOMS = ["tshirt_realistic", "water_bottle_realistic", "phone_case_realistic"]
SIMPLE_BOMS = ["tshirt_simple", "water_bottle_simple", "phone_case_simple"]


@pytest.fixture
def emission_factors_df():
    """Load emission factors CSV for component validation."""
    return pd.read_csv(EMISSION_FACTORS_CSV)


@pytest.fixture
def all_boms():
    """Load all BOM files into a dictionary."""
    boms = {}
    for name, path in BOM_FILES.items():
        with open(path, 'r') as f:
            boms[name] = json.load(f)
    return boms


class TestBOMFileExistence:
    """Test Scenario 1: BOM File Existence and JSON Validity"""

    def test_all_six_bom_files_exist(self):
        """All 6 BOM files must exist"""
        for name, path in BOM_FILES.items():
            assert path.exists(), f"BOM file not found: {name} at {path}"

    def test_tshirt_simple_is_valid_json(self):
        """T-shirt simple BOM must be valid JSON"""
        with open(BOM_FILES["tshirt_simple"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_tshirt_realistic_is_valid_json(self):
        """T-shirt realistic BOM must be valid JSON"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_water_bottle_simple_is_valid_json(self):
        """Water bottle simple BOM must be valid JSON"""
        with open(BOM_FILES["water_bottle_simple"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_water_bottle_realistic_is_valid_json(self):
        """Water bottle realistic BOM must be valid JSON"""
        with open(BOM_FILES["water_bottle_realistic"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_phone_case_simple_is_valid_json(self):
        """Phone case simple BOM must be valid JSON"""
        with open(BOM_FILES["phone_case_simple"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_phone_case_realistic_is_valid_json(self):
        """Phone case realistic BOM must be valid JSON"""
        with open(BOM_FILES["phone_case_realistic"], 'r') as f:
            bom = json.load(f)
        assert bom is not None

    def test_all_boms_load_without_errors(self, all_boms):
        """All BOM files must load without JSON errors"""
        assert len(all_boms) == 6


class TestBOMStructureConsistency:
    """Test Scenario 2: BOM Structure Consistent Across Files"""

    def test_all_boms_have_product_key(self, all_boms):
        """All BOMs must have 'product' key"""
        for name, bom in all_boms.items():
            assert 'product' in bom, f"{name} missing 'product' key"

    def test_all_boms_have_bill_of_materials_key(self, all_boms):
        """All BOMs must have 'bill_of_materials' key"""
        for name, bom in all_boms.items():
            assert 'bill_of_materials' in bom, f"{name} missing 'bill_of_materials' key"

    def test_all_products_have_code(self, all_boms):
        """All products must have 'code' field"""
        for name, bom in all_boms.items():
            assert 'code' in bom['product'], f"{name} product missing 'code'"

    def test_all_products_have_name(self, all_boms):
        """All products must have 'name' field"""
        for name, bom in all_boms.items():
            assert 'name' in bom['product'], f"{name} product missing 'name'"

    def test_all_products_have_unit(self, all_boms):
        """All products must have 'unit' field"""
        for name, bom in all_boms.items():
            assert 'unit' in bom['product'], f"{name} product missing 'unit'"

    def test_all_products_have_is_finished_product(self, all_boms):
        """All products must have 'is_finished_product' field"""
        for name, bom in all_boms.items():
            assert 'is_finished_product' in bom['product'], \
                f"{name} product missing 'is_finished_product'"

    def test_all_products_are_finished_products(self, all_boms):
        """All test products should be finished products"""
        for name, bom in all_boms.items():
            assert bom['product']['is_finished_product'] is True, \
                f"{name} should be a finished product"

    def test_simple_and_realistic_share_product_codes(self, all_boms):
        """Simple and realistic variants should share the same product code"""
        # T-shirt variants should share code
        assert all_boms['tshirt_simple']['product']['code'] == \
               all_boms['tshirt_realistic']['product']['code']

        # Water bottle variants should share code
        assert all_boms['water_bottle_simple']['product']['code'] == \
               all_boms['water_bottle_realistic']['product']['code']

        # Phone case variants should share code
        assert all_boms['phone_case_simple']['product']['code'] == \
               all_boms['phone_case_realistic']['product']['code']

    def test_three_unique_product_types(self, all_boms):
        """Should have 3 unique product types (T-shirt, Water Bottle, Phone Case)"""
        codes = set(bom['product']['code'] for bom in all_boms.values())
        assert len(codes) == 3, f"Expected 3 unique product codes, got {len(codes)}: {codes}"


class TestBOMComponents:
    """Test Scenario 3: BOM Components Structure and Validation"""

    def test_all_boms_have_at_least_one_component(self, all_boms):
        """All BOMs must have at least one component"""
        for name, bom in all_boms.items():
            components = bom['bill_of_materials']
            assert len(components) >= 1, f"{name} has no components"

    def test_all_components_have_component_name(self, all_boms):
        """All BOM components must have 'component_name' field"""
        for name, bom in all_boms.items():
            for i, comp in enumerate(bom['bill_of_materials']):
                assert 'component_name' in comp, \
                    f"{name} component {i} missing 'component_name'"

    def test_all_components_have_quantity(self, all_boms):
        """All BOM components must have 'quantity' field"""
        for name, bom in all_boms.items():
            for i, comp in enumerate(bom['bill_of_materials']):
                assert 'quantity' in comp, \
                    f"{name} component {i} missing 'quantity'"

    def test_all_components_have_unit(self, all_boms):
        """All BOM components must have 'unit' field"""
        for name, bom in all_boms.items():
            for i, comp in enumerate(bom['bill_of_materials']):
                assert 'unit' in comp, \
                    f"{name} component {i} missing 'unit'"

    def test_all_component_quantities_are_positive(self, all_boms):
        """All component quantities must be positive numbers"""
        for name, bom in all_boms.items():
            for comp in bom['bill_of_materials']:
                qty = comp['quantity']
                assert isinstance(qty, (int, float)), \
                    f"{name} component '{comp['component_name']}' quantity not numeric: {qty}"
                assert qty > 0, \
                    f"{name} component '{comp['component_name']}' quantity not positive: {qty}"

    def test_all_component_units_are_valid(self, all_boms):
        """All component units must be valid measurement units"""
        valid_units = ['kg', 'unit', 'L', 'kWh', 'MJ', 'tkm', 'm', 'm2', 'm3']
        for name, bom in all_boms.items():
            for comp in bom['bill_of_materials']:
                unit = comp['unit']
                assert unit in valid_units, \
                    f"{name} component '{comp['component_name']}' has invalid unit: {unit}"


class TestComponentReferencesMatchEmissionFactors:
    """Test Scenario 4: All Components Match Emission Factors"""

    def test_all_components_have_matching_emission_factors(self, all_boms, emission_factors_df):
        """All BOM components must have matching emission factors in CSV"""
        available_factors = set(emission_factors_df['activity_name'].values)

        for name, bom in all_boms.items():
            for comp in bom['bill_of_materials']:
                comp_name = comp['component_name']
                assert comp_name in available_factors, \
                    f"{name} component '{comp_name}' not found in emission factors CSV"

    def test_tshirt_realistic_components_match(self, emission_factors_df):
        """T-shirt realistic components must match emission factors"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)

        available_factors = set(emission_factors_df['activity_name'].values)
        for comp in bom['bill_of_materials']:
            assert comp['component_name'] in available_factors

    def test_water_bottle_realistic_components_match(self, emission_factors_df):
        """Water bottle realistic components must match emission factors"""
        with open(BOM_FILES["water_bottle_realistic"], 'r') as f:
            bom = json.load(f)

        available_factors = set(emission_factors_df['activity_name'].values)
        for comp in bom['bill_of_materials']:
            assert comp['component_name'] in available_factors

    def test_phone_case_realistic_components_match(self, emission_factors_df):
        """Phone case realistic components must match emission factors"""
        with open(BOM_FILES["phone_case_realistic"], 'r') as f:
            bom = json.load(f)

        available_factors = set(emission_factors_df['activity_name'].values)
        for comp in bom['bill_of_materials']:
            assert comp['component_name'] in available_factors


class TestRealisticBOMsHaveExpectedResults:
    """Test Scenario 5: Realistic BOMs Have Expected Results"""

    def test_all_realistic_boms_have_expected_result(self, all_boms):
        """All realistic BOMs must have 'expected_result' key"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            assert 'expected_result' in bom, f"{name} missing 'expected_result'"

    def test_expected_results_have_total_co2e_kg(self, all_boms):
        """All expected results must have 'total_co2e_kg' field"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            result = bom['expected_result']
            assert 'total_co2e_kg' in result, \
                f"{name} expected_result missing 'total_co2e_kg'"

    def test_expected_results_have_breakdown(self, all_boms):
        """All expected results must have 'breakdown' field"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            result = bom['expected_result']
            assert 'breakdown' in result, \
                f"{name} expected_result missing 'breakdown'"

    def test_breakdown_has_materials(self, all_boms):
        """All breakdowns must have 'materials' emissions"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            breakdown = bom['expected_result']['breakdown']
            assert 'materials' in breakdown, \
                f"{name} breakdown missing 'materials'"

    def test_tshirt_realistic_expected_total(self):
        """T-shirt realistic must have expected total of 2.05 kg CO2e"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)
        assert bom['expected_result']['total_co2e_kg'] == 2.05

    def test_tshirt_realistic_expected_breakdown(self):
        """T-shirt realistic must have correct emission breakdown"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)

        breakdown = bom['expected_result']['breakdown']
        assert breakdown['materials'] == 1.04
        assert breakdown['energy'] == 1.0
        assert breakdown['transport'] == 0.01

    def test_total_equals_breakdown_sum(self, all_boms):
        """Total CO2e should equal sum of breakdown components"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            total = bom['expected_result']['total_co2e_kg']
            breakdown = bom['expected_result']['breakdown']

            # Sum all breakdown values
            breakdown_sum = sum(breakdown.values())

            # Allow small floating point differences
            assert abs(total - breakdown_sum) < 0.01, \
                f"{name} total ({total}) doesn't match breakdown sum ({breakdown_sum})"


class TestSimpleBOMsHaveZeroEnergyTransport:
    """Test Scenario 6: Simple BOMs Have Zero Energy/Transport (Not Missing)"""

    def test_simple_boms_have_energy_data_field(self, all_boms):
        """Simple BOMs should have energy_data field (structure consistency)"""
        for name in SIMPLE_BOMS:
            bom = all_boms[name]
            assert 'energy_data' in bom, f"{name} missing 'energy_data' field"

    def test_simple_boms_have_zero_electricity(self, all_boms):
        """Simple BOMs should have electricity_kwh = 0"""
        for name in SIMPLE_BOMS:
            bom = all_boms[name]
            if 'energy_data' in bom and bom['energy_data']:
                assert bom['energy_data']['electricity_kwh'] == 0, \
                    f"{name} should have zero electricity consumption"

    def test_simple_boms_have_empty_transport_data(self, all_boms):
        """Simple BOMs should have empty transport_data list"""
        for name in SIMPLE_BOMS:
            bom = all_boms[name]
            assert 'transport_data' in bom, f"{name} missing 'transport_data' field"
            assert bom['transport_data'] == [], \
                f"{name} should have empty transport_data list"

    def test_simple_boms_have_at_least_two_components(self, all_boms):
        """Simple BOMs should have at least 2 components"""
        for name in SIMPLE_BOMS:
            bom = all_boms[name]
            assert len(bom['bill_of_materials']) >= 2, \
                f"{name} should have at least 2 components"

    def test_simple_boms_have_expected_result_with_zero_energy_transport(self, all_boms):
        """Simple BOMs should have expected_result with zero energy and transport"""
        for name in SIMPLE_BOMS:
            bom = all_boms[name]
            if 'expected_result' in bom:
                breakdown = bom['expected_result']['breakdown']
                assert breakdown.get('energy', 0) == 0, \
                    f"{name} should have zero energy emissions"
                assert breakdown.get('transport', 0) == 0, \
                    f"{name} should have zero transport emissions"


class TestRealisticBOMsHaveEnergyAndTransport:
    """Test that realistic BOMs include non-zero energy and transport data"""

    def test_realistic_boms_have_energy_data(self, all_boms):
        """Realistic BOMs should have energy_data"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            assert 'energy_data' in bom, f"{name} missing 'energy_data'"

    def test_realistic_boms_have_transport_data(self, all_boms):
        """Realistic BOMs should have transport_data"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            assert 'transport_data' in bom, f"{name} missing 'transport_data'"

    def test_energy_data_has_electricity_kwh(self, all_boms):
        """Energy data should specify electricity consumption in kWh"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            if bom.get('energy_data'):
                assert 'electricity_kwh' in bom['energy_data'], \
                    f"{name} energy_data missing 'electricity_kwh'"

    def test_realistic_boms_have_positive_electricity(self, all_boms):
        """Realistic BOMs should have positive electricity consumption"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            if bom.get('energy_data'):
                elec = bom['energy_data'].get('electricity_kwh', 0)
                assert elec > 0, f"{name} should have positive electricity consumption"

    def test_transport_data_is_list(self, all_boms):
        """Transport data should be a list of transport segments"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            if bom.get('transport_data'):
                assert isinstance(bom['transport_data'], list), \
                    f"{name} transport_data should be a list"

    def test_realistic_boms_have_transport_segments(self, all_boms):
        """Realistic BOMs should have at least one transport segment"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            assert len(bom.get('transport_data', [])) > 0, \
                f"{name} should have at least one transport segment"

    def test_transport_segments_have_mode(self, all_boms):
        """Each transport segment should have 'mode' field"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            if bom.get('transport_data') and len(bom['transport_data']) > 0:
                for segment in bom['transport_data']:
                    assert 'mode' in segment, \
                        f"{name} transport segment missing 'mode'"


class TestSpecificProductRequirements:
    """Test specific requirements for each product"""

    def test_tshirt_products_have_tshirt_code(self, all_boms):
        """T-shirt products should have TSHIRT code prefix"""
        tshirt_boms = {k: v for k, v in all_boms.items() if 'tshirt' in k}
        for name, bom in tshirt_boms.items():
            code = bom['product']['code']
            assert code.startswith('TSHIRT'), \
                f"{name} should have TSHIRT code prefix, got {code}"

    def test_water_bottle_products_have_bottle_code(self, all_boms):
        """Water bottle products should have BOTTLE code prefix"""
        bottle_boms = {k: v for k, v in all_boms.items() if 'water_bottle' in k}
        for name, bom in bottle_boms.items():
            code = bom['product']['code']
            assert code.startswith('BOTTLE'), \
                f"{name} should have BOTTLE code prefix, got {code}"

    def test_phone_case_products_have_case_code(self, all_boms):
        """Phone case products should have CASE code prefix"""
        case_boms = {k: v for k, v in all_boms.items() if 'phone_case' in k}
        for name, bom in case_boms.items():
            code = bom['product']['code']
            assert code.startswith('CASE'), \
                f"{name} should have CASE code prefix, got {code}"

    def test_tshirt_realistic_has_five_components(self):
        """T-shirt realistic should have 5 material components"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)
        assert len(bom['bill_of_materials']) == 5, \
            "T-shirt realistic should have 5 components (cotton, polyester, nylon, plastic_abs, paper)"

    def test_tshirt_realistic_has_cotton(self):
        """T-shirt realistic must include cotton as main material"""
        with open(BOM_FILES["tshirt_realistic"], 'r') as f:
            bom = json.load(f)

        component_names = [c['component_name'] for c in bom['bill_of_materials']]
        assert 'cotton' in component_names, "T-shirt realistic must include cotton"

    def test_water_bottle_has_plastic(self, all_boms):
        """Water bottle products must include plastic material"""
        bottle_boms = {k: v for k, v in all_boms.items() if 'water_bottle' in k}

        for name, bom in bottle_boms.items():
            component_names = [c['component_name'] for c in bom['bill_of_materials']]
            has_plastic = any('plastic' in comp for comp in component_names)
            assert has_plastic, f"{name} must include plastic material"

    def test_phone_case_has_plastic_abs(self, all_boms):
        """Phone case products should include plastic_abs material"""
        case_boms = {k: v for k, v in all_boms.items() if 'phone_case' in k}

        for name, bom in case_boms.items():
            component_names = [c['component_name'] for c in bom['bill_of_materials']]
            # May have plastic_abs or other plastic types
            has_plastic = any('plastic' in comp for comp in component_names)
            assert has_plastic, f"{name} must include plastic material"


class TestBOMDataTypes:
    """Test that BOM fields have correct data types"""

    def test_product_id_is_string(self, all_boms):
        """Product ID should be a string"""
        for name, bom in all_boms.items():
            if 'id' in bom['product']:
                assert isinstance(bom['product']['id'], str), \
                    f"{name} product id should be string"

    def test_product_code_is_string(self, all_boms):
        """Product code should be a string"""
        for name, bom in all_boms.items():
            assert isinstance(bom['product']['code'], str), \
                f"{name} product code should be string"

    def test_product_name_is_string(self, all_boms):
        """Product name should be a string"""
        for name, bom in all_boms.items():
            assert isinstance(bom['product']['name'], str), \
                f"{name} product name should be string"

    def test_is_finished_product_is_boolean(self, all_boms):
        """is_finished_product should be a boolean"""
        for name, bom in all_boms.items():
            assert isinstance(bom['product']['is_finished_product'], bool), \
                f"{name} is_finished_product should be boolean"

    def test_bill_of_materials_is_list(self, all_boms):
        """bill_of_materials should be a list"""
        for name, bom in all_boms.items():
            assert isinstance(bom['bill_of_materials'], list), \
                f"{name} bill_of_materials should be list"

    def test_total_co2e_is_numeric(self, all_boms):
        """total_co2e_kg should be a number in realistic BOMs"""
        for name in REALISTIC_BOMS:
            bom = all_boms[name]
            if 'expected_result' in bom:
                total = bom['expected_result']['total_co2e_kg']
                assert isinstance(total, (int, float)), \
                    f"{name} total_co2e_kg should be numeric"
