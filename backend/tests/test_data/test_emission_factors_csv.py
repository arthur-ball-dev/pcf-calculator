"""
Test suite for emission factors CSV validation.

CRITICAL: These tests MUST be written BEFORE creating the CSV file.
Tests validate structure, completeness, data quality, and schema compliance.

Test Scenarios:
1. CSV structure validation (columns, row count, format)
2. Required materials presence (all 20 emission factors)
3. Data quality validation (no nulls, positive values)
4. Unit validation (valid units only)
5. Data source attribution (EPA, DEFRA, Ecoinvent)
"""

import os
import pytest
import pandas as pd
from pathlib import Path


# Path to the CSV file (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "emission_factors_simple.csv"


class TestEmissionFactorsCSVStructure:
    """Test Scenario 1: CSV Structure Validation"""

    def test_csv_file_exists(self):
        """CSV file must exist at the expected location"""
        assert CSV_PATH.exists(), f"CSV file not found at {CSV_PATH}"

    def test_csv_readable_with_pandas(self):
        """CSV must be readable by pandas without errors"""
        df = pd.read_csv(CSV_PATH)
        assert df is not None
        assert isinstance(df, pd.DataFrame)

    def test_csv_has_correct_columns(self):
        """CSV must have exactly these columns in order"""
        df = pd.read_csv(CSV_PATH)
        expected_columns = ['activity_name', 'co2e_factor', 'unit', 'data_source', 'geography']
        assert list(df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {list(df.columns)}"

    def test_csv_has_exactly_20_rows(self):
        """CSV must contain exactly 20 emission factors"""
        df = pd.read_csv(CSV_PATH)
        assert df.shape[0] == 20, f"Expected 20 rows, got {df.shape[0]}"

    def test_activity_names_are_unique(self):
        """Each activity name must be unique (no duplicates)"""
        df = pd.read_csv(CSV_PATH)
        assert df['activity_name'].is_unique, \
            f"Duplicate activity names found: {df['activity_name'][df['activity_name'].duplicated()].tolist()}"


class TestEmissionFactorsRequiredMaterials:
    """Test Scenario 2: Required Materials Presence"""

    def test_all_required_materials_present(self):
        """All 20 required materials must be present in the CSV"""
        df = pd.read_csv(CSV_PATH)

        required_materials = [
            'cotton', 'polyester', 'plastic_pet', 'plastic_abs',
            'aluminum', 'steel', 'glass', 'paper',
            'rubber', 'copper', 'wood', 'leather',
            'nylon', 'ceramic', 'foam',
            'electricity_us', 'transport_truck', 'transport_ship',
            'natural_gas', 'water'
        ]

        activity_names = df['activity_name'].tolist()

        for material in required_materials:
            assert material in activity_names, \
                f"Required material '{material}' not found in CSV"

    def test_material_categories_coverage(self):
        """CSV must cover all material categories: materials, energy, transport"""
        df = pd.read_csv(CSV_PATH)
        activity_names = df['activity_name'].tolist()

        # Materials category (at least 10)
        materials = ['cotton', 'polyester', 'plastic_pet', 'plastic_abs',
                     'aluminum', 'steel', 'glass', 'paper', 'rubber', 'copper',
                     'wood', 'leather', 'nylon', 'ceramic', 'foam']
        materials_count = sum(1 for m in materials if m in activity_names)
        assert materials_count >= 10, f"Expected at least 10 materials, found {materials_count}"

        # Energy category (at least 1)
        energy_items = ['electricity_us', 'natural_gas']
        energy_count = sum(1 for e in energy_items if e in activity_names)
        assert energy_count >= 1, f"Expected at least 1 energy item, found {energy_count}"

        # Transport category (at least 1)
        transport_items = ['transport_truck', 'transport_ship']
        transport_count = sum(1 for t in transport_items if t in activity_names)
        assert transport_count >= 1, f"Expected at least 1 transport item, found {transport_count}"


class TestEmissionFactorsDataQuality:
    """Test Scenario 3: Data Quality - No Nulls"""

    def test_no_null_values_in_any_column(self):
        """No null values allowed in any column"""
        df = pd.read_csv(CSV_PATH)
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()

        assert total_nulls == 0, \
            f"Found {total_nulls} null values. Details: {null_counts[null_counts > 0].to_dict()}"

    def test_no_empty_strings_in_activity_name(self):
        """Activity names must not be empty strings"""
        df = pd.read_csv(CSV_PATH)
        empty_names = df[df['activity_name'].str.strip() == '']
        assert len(empty_names) == 0, \
            f"Found {len(empty_names)} empty activity names"

    def test_all_co2e_factors_are_positive(self):
        """All CO2e factors must be positive numbers (> 0)"""
        df = pd.read_csv(CSV_PATH)
        assert df['co2e_factor'].min() > 0, \
            f"Found non-positive CO2e factor: {df['co2e_factor'].min()}"

    def test_co2e_factors_are_numeric(self):
        """All CO2e factors must be numeric (float or int)"""
        df = pd.read_csv(CSV_PATH)
        assert pd.api.types.is_numeric_dtype(df['co2e_factor']), \
            f"co2e_factor column is not numeric: {df['co2e_factor'].dtype}"

    def test_co2e_factors_reasonable_range(self):
        """CO2e factors should be within a reasonable range (0.001 to 100 kg CO2e)"""
        df = pd.read_csv(CSV_PATH)
        min_factor = df['co2e_factor'].min()
        max_factor = df['co2e_factor'].max()

        assert min_factor >= 0.001, \
            f"Minimum CO2e factor {min_factor} seems unreasonably low"
        assert max_factor <= 100, \
            f"Maximum CO2e factor {max_factor} seems unreasonably high"


class TestEmissionFactorsUnits:
    """Test Scenario 4: Units Validation"""

    def test_all_units_are_valid(self):
        """All units must be from the allowed list"""
        df = pd.read_csv(CSV_PATH)
        valid_units = ['kg', 'kWh', 'tkm', 'L', 'MJ']

        for unit in df['unit']:
            assert unit in valid_units, \
                f"Invalid unit '{unit}' found. Valid units: {valid_units}"

    def test_no_empty_units(self):
        """Unit column must not contain empty strings"""
        df = pd.read_csv(CSV_PATH)
        empty_units = df[df['unit'].str.strip() == '']
        assert len(empty_units) == 0, \
            f"Found {len(empty_units)} empty units"

    def test_material_units_are_kg(self):
        """Material emission factors should use 'kg' as unit"""
        df = pd.read_csv(CSV_PATH)

        materials = ['cotton', 'polyester', 'plastic_pet', 'plastic_abs',
                     'aluminum', 'steel', 'glass', 'paper', 'rubber', 'copper',
                     'wood', 'leather', 'nylon', 'ceramic', 'foam']

        for material in materials:
            material_row = df[df['activity_name'] == material]
            if not material_row.empty:
                assert material_row.iloc[0]['unit'] == 'kg', \
                    f"Material '{material}' should have unit 'kg', got '{material_row.iloc[0]['unit']}'"

    def test_electricity_unit_is_kwh(self):
        """Electricity emission factor should use 'kWh' as unit"""
        df = pd.read_csv(CSV_PATH)
        electricity_row = df[df['activity_name'] == 'electricity_us']

        if not electricity_row.empty:
            assert electricity_row.iloc[0]['unit'] == 'kWh', \
                f"Electricity should have unit 'kWh', got '{electricity_row.iloc[0]['unit']}'"

    def test_transport_unit_is_tkm(self):
        """Transport emission factors should use 'tkm' (tonne-kilometer) as unit"""
        df = pd.read_csv(CSV_PATH)

        transport_items = ['transport_truck', 'transport_ship']
        for transport in transport_items:
            transport_row = df[df['activity_name'] == transport]
            if not transport_row.empty:
                assert transport_row.iloc[0]['unit'] == 'tkm', \
                    f"Transport '{transport}' should have unit 'tkm', got '{transport_row.iloc[0]['unit']}'"


class TestEmissionFactorsDataSources:
    """Test Scenario 5: Data Sources Attribution"""

    def test_all_data_sources_are_valid(self):
        """All data sources must be from the allowed list"""
        df = pd.read_csv(CSV_PATH)
        valid_sources = ['EPA', 'DEFRA', 'Ecoinvent']

        for source in df['data_source']:
            assert source in valid_sources, \
                f"Invalid data source '{source}' found. Valid sources: {valid_sources}"

    def test_no_empty_data_sources(self):
        """Data source column must not contain empty strings"""
        df = pd.read_csv(CSV_PATH)
        empty_sources = df[df['data_source'].str.strip() == '']
        assert len(empty_sources) == 0, \
            f"Found {len(empty_sources)} empty data sources"

    def test_data_source_distribution(self):
        """Data sources should be distributed (not all from one source)"""
        df = pd.read_csv(CSV_PATH)
        source_counts = df['data_source'].value_counts()

        # At least 2 different sources should be used
        assert len(source_counts) >= 2, \
            f"Expected at least 2 different data sources, found {len(source_counts)}"


class TestEmissionFactorsGeography:
    """Additional validation for geography column"""

    def test_geography_column_exists(self):
        """Geography column must exist and not be null"""
        df = pd.read_csv(CSV_PATH)
        assert 'geography' in df.columns
        assert df['geography'].isnull().sum() == 0

    def test_geography_values_valid(self):
        """Geography values should be valid codes (GLO, US, EU, etc.)"""
        df = pd.read_csv(CSV_PATH)
        valid_geographies = ['GLO', 'US', 'EU', 'CN', 'GLOBAL']

        for geo in df['geography']:
            assert geo in valid_geographies, \
                f"Invalid geography '{geo}' found. Valid geographies: {valid_geographies}"

    def test_default_geography_is_GLO(self):
        """Most entries should use 'GLO' (global) as default geography"""
        df = pd.read_csv(CSV_PATH)
        glo_count = (df['geography'] == 'GLO').sum()

        # At least 50% should be GLO
        assert glo_count >= len(df) * 0.5, \
            f"Expected at least 50% entries with 'GLO' geography, got {glo_count}/{len(df)}"


class TestEmissionFactorsSpecificValues:
    """Test specific known values from the specification"""

    def test_cotton_emission_factor(self):
        """Cotton emission factor should be 5.0 kg CO2e/kg"""
        df = pd.read_csv(CSV_PATH)
        cotton_row = df[df['activity_name'] == 'cotton']
        assert not cotton_row.empty, "Cotton not found in CSV"
        assert cotton_row.iloc[0]['co2e_factor'] == 5.0, \
            f"Expected cotton factor 5.0, got {cotton_row.iloc[0]['co2e_factor']}"

    def test_electricity_us_emission_factor(self):
        """Electricity (US) emission factor should be 0.4 kg CO2e/kWh"""
        df = pd.read_csv(CSV_PATH)
        elec_row = df[df['activity_name'] == 'electricity_us']
        assert not elec_row.empty, "electricity_us not found in CSV"
        assert elec_row.iloc[0]['co2e_factor'] == 0.4, \
            f"Expected electricity_us factor 0.4, got {elec_row.iloc[0]['co2e_factor']}"

    def test_transport_truck_emission_factor(self):
        """Transport truck emission factor should be 0.1 kg CO2e/tkm"""
        df = pd.read_csv(CSV_PATH)
        truck_row = df[df['activity_name'] == 'transport_truck']
        assert not truck_row.empty, "transport_truck not found in CSV"
        assert truck_row.iloc[0]['co2e_factor'] == 0.1, \
            f"Expected transport_truck factor 0.1, got {truck_row.iloc[0]['co2e_factor']}"

    def test_water_emission_factor(self):
        """Water emission factor should be 0.001 kg CO2e/L"""
        df = pd.read_csv(CSV_PATH)
        water_row = df[df['activity_name'] == 'water']
        assert not water_row.empty, "water not found in CSV"
        assert water_row.iloc[0]['co2e_factor'] == 0.001, \
            f"Expected water factor 0.001, got {water_row.iloc[0]['co2e_factor']}"


class TestEmissionFactorsDatabaseCompatibility:
    """Test CSV compatibility with database schema"""

    def test_csv_columns_match_database_schema(self):
        """CSV columns must match emission_factors table columns"""
        df = pd.read_csv(CSV_PATH)

        # Required columns from database schema
        required_columns = ['activity_name', 'co2e_factor', 'unit', 'data_source', 'geography']

        for col in required_columns:
            assert col in df.columns, \
                f"Required column '{col}' missing from CSV"

    def test_activity_name_length_under_255(self):
        """Activity names must be under 255 characters (VARCHAR(255) in schema)"""
        df = pd.read_csv(CSV_PATH)
        max_length = df['activity_name'].str.len().max()

        assert max_length <= 255, \
            f"Activity name too long: {max_length} characters (max 255)"

    def test_data_source_length_under_100(self):
        """Data sources must be under 100 characters (VARCHAR(100) in schema)"""
        df = pd.read_csv(CSV_PATH)
        max_length = df['data_source'].str.len().max()

        assert max_length <= 100, \
            f"Data source too long: {max_length} characters (max 100)"

    def test_geography_length_under_50(self):
        """Geography codes must be under 50 characters (VARCHAR(50) in schema)"""
        df = pd.read_csv(CSV_PATH)
        max_length = df['geography'].str.len().max()

        assert max_length <= 50, \
            f"Geography code too long: {max_length} characters (max 50)"

    def test_unit_length_under_20(self):
        """Units must be under 20 characters (VARCHAR(20) in schema)"""
        df = pd.read_csv(CSV_PATH)
        max_length = df['unit'].str.len().max()

        assert max_length <= 20, \
            f"Unit too long: {max_length} characters (max 20)"
