"""
Validation Tests - Expected Results for Realistic BOMs

This module tests the PCF calculator against expected results for all 3
realistic BOMs (T-shirt, Water Bottle, Phone Case) from JSON test data.

Test data files are located in:
- /data/bom_tshirt_realistic.json
- /data/bom_water_bottle_realistic.json
- /data/bom_phone_case_realistic.json

Expected Results (±5% tolerance):
- T-shirt: 2.05 kg CO2e (1.9475 - 2.1525)
- Water Bottle: 0.157 kg CO2e (0.14915 - 0.16485)
- Phone Case: 0.343 kg CO2e (0.32585 - 0.36015)

TASK-CALC-004: Validate Calculations Against Expected Results
TDD Protocol: Tests written FIRST (before implementation)
"""

import json
import os
import pytest
from backend.calculator.pcf_calculator import PCFCalculator


# Path to test data files
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


class TestTshirtRealisticValidation:
    """Test T-shirt realistic BOM against expected results."""

    @pytest.fixture
    def tshirt_data(self):
        """Load t-shirt realistic BOM from JSON."""
        file_path = os.path.join(DATA_DIR, "bom_tshirt_realistic.json")
        with open(file_path) as f:
            return json.load(f)

    @pytest.fixture
    def calculator(self):
        """Initialize PCF calculator."""
        return PCFCalculator()

    def test_tshirt_total_pcf_within_tolerance(self, calculator, tshirt_data):
        """
        Test T-shirt total PCF is within ±5% of expected 2.05 kg CO2e.

        Expected: 2.05 kg CO2e
        Tolerance: ±5% (1.9475 - 2.1525 kg CO2e)
        """
        bom = tshirt_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = tshirt_data["expected_result"]["total_co2e_kg"]
        actual = result["total_co2e_kg"]

        # Check within tolerance range
        lower_bound = expected * 0.95
        upper_bound = expected * 1.05

        assert actual >= lower_bound, (
            f"T-shirt PCF {actual:.4f} below lower bound {lower_bound:.4f}"
        )
        assert actual <= upper_bound, (
            f"T-shirt PCF {actual:.4f} above upper bound {upper_bound:.4f}"
        )

        # Calculate error percentage
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"T-shirt PCF error {error_pct:.2f}% exceeds 5% tolerance"
        )

    def test_tshirt_materials_breakdown_within_tolerance(self, calculator, tshirt_data):
        """
        Test T-shirt materials breakdown is within ±5% of expected 1.04 kg CO2e.

        Expected: 1.04 kg CO2e
        Tolerance: ±5% (0.988 - 1.092 kg CO2e)
        """
        bom = tshirt_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = tshirt_data["expected_result"]["breakdown"]["materials"]
        actual = result["breakdown_by_category"].get("materials", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"T-shirt materials error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_tshirt_energy_breakdown_within_tolerance(self, calculator, tshirt_data):
        """
        Test T-shirt energy breakdown is within ±5% of expected 1.0 kg CO2e.

        Expected: 1.0 kg CO2e
        Tolerance: ±5% (0.95 - 1.05 kg CO2e)
        """
        bom = tshirt_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = tshirt_data["expected_result"]["breakdown"]["energy"]
        actual = result["breakdown_by_category"].get("energy", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"T-shirt energy error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_tshirt_transport_breakdown_within_tolerance(self, calculator, tshirt_data):
        """
        Test T-shirt transport breakdown is within ±5% of expected 0.01 kg CO2e.

        Expected: 0.01 kg CO2e
        Tolerance: ±5% (0.0095 - 0.0105 kg CO2e)
        """
        bom = tshirt_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = tshirt_data["expected_result"]["breakdown"]["transport"]
        actual = result["breakdown_by_category"].get("transport", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"T-shirt transport error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )


class TestWaterBottleRealisticValidation:
    """Test Water Bottle realistic BOM against expected results."""

    @pytest.fixture
    def bottle_data(self):
        """Load water bottle realistic BOM from JSON."""
        file_path = os.path.join(DATA_DIR, "bom_water_bottle_realistic.json")
        with open(file_path) as f:
            return json.load(f)

    @pytest.fixture
    def calculator(self):
        """Initialize PCF calculator."""
        return PCFCalculator()

    def test_bottle_total_pcf_within_tolerance(self, calculator, bottle_data):
        """
        Test Water Bottle total PCF is within ±5% of expected 0.157 kg CO2e.

        Expected: 0.157 kg CO2e
        Tolerance: ±5% (0.14915 - 0.16485 kg CO2e)
        """
        bom = bottle_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = bottle_data["expected_result"]["total_co2e_kg"]
        actual = result["total_co2e_kg"]

        # Check within tolerance range
        lower_bound = expected * 0.95
        upper_bound = expected * 1.05

        assert actual >= lower_bound, (
            f"Water Bottle PCF {actual:.4f} below lower bound {lower_bound:.4f}"
        )
        assert actual <= upper_bound, (
            f"Water Bottle PCF {actual:.4f} above upper bound {upper_bound:.4f}"
        )

        # Calculate error percentage
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Water Bottle PCF error {error_pct:.2f}% exceeds 5% tolerance"
        )

    def test_bottle_materials_breakdown_within_tolerance(self, calculator, bottle_data):
        """
        Test Water Bottle materials breakdown is within ±5% of expected 0.095 kg CO2e.

        Expected: 0.095 kg CO2e
        Tolerance: ±5%
        """
        bom = bottle_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = bottle_data["expected_result"]["breakdown"]["materials"]
        actual = result["breakdown_by_category"].get("materials", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Water Bottle materials error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_bottle_energy_breakdown_within_tolerance(self, calculator, bottle_data):
        """
        Test Water Bottle energy breakdown is within ±5% of expected 0.06 kg CO2e.

        Expected: 0.06 kg CO2e
        Tolerance: ±5%
        """
        bom = bottle_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = bottle_data["expected_result"]["breakdown"]["energy"]
        actual = result["breakdown_by_category"].get("energy", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Water Bottle energy error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_bottle_transport_breakdown_within_tolerance(self, calculator, bottle_data):
        """
        Test Water Bottle transport breakdown is within ±5% of expected 0.002 kg CO2e.

        Expected: 0.002 kg CO2e
        Tolerance: ±5%
        """
        bom = bottle_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = bottle_data["expected_result"]["breakdown"]["transport"]
        actual = result["breakdown_by_category"].get("transport", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Water Bottle transport error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )


class TestPhoneCaseRealisticValidation:
    """Test Phone Case realistic BOM against expected results."""

    @pytest.fixture
    def case_data(self):
        """Load phone case realistic BOM from JSON."""
        file_path = os.path.join(DATA_DIR, "bom_phone_case_realistic.json")
        with open(file_path) as f:
            return json.load(f)

    @pytest.fixture
    def calculator(self):
        """Initialize PCF calculator."""
        return PCFCalculator()

    def test_case_total_pcf_within_tolerance(self, calculator, case_data):
        """
        Test Phone Case total PCF is within ±5% of expected 0.343 kg CO2e.

        Expected: 0.343 kg CO2e
        Tolerance: ±5% (0.32585 - 0.36015 kg CO2e)
        """
        bom = case_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = case_data["expected_result"]["total_co2e_kg"]
        actual = result["total_co2e_kg"]

        # Check within tolerance range
        lower_bound = expected * 0.95
        upper_bound = expected * 1.05

        assert actual >= lower_bound, (
            f"Phone Case PCF {actual:.4f} below lower bound {lower_bound:.4f}"
        )
        assert actual <= upper_bound, (
            f"Phone Case PCF {actual:.4f} above upper bound {upper_bound:.4f}"
        )

        # Calculate error percentage
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Phone Case PCF error {error_pct:.2f}% exceeds 5% tolerance"
        )

    def test_case_materials_breakdown_within_tolerance(self, calculator, case_data):
        """
        Test Phone Case materials breakdown is within ±5% of expected 0.138 kg CO2e.

        Expected: 0.138 kg CO2e
        Tolerance: ±5%
        """
        bom = case_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = case_data["expected_result"]["breakdown"]["materials"]
        actual = result["breakdown_by_category"].get("materials", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Phone Case materials error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_case_energy_breakdown_within_tolerance(self, calculator, case_data):
        """
        Test Phone Case energy breakdown is within ±5% of expected 0.2 kg CO2e.

        Expected: 0.2 kg CO2e
        Tolerance: ±5%
        """
        bom = case_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = case_data["expected_result"]["breakdown"]["energy"]
        actual = result["breakdown_by_category"].get("energy", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Phone Case energy error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )

    def test_case_transport_breakdown_within_tolerance(self, calculator, case_data):
        """
        Test Phone Case transport breakdown is within ±5% of expected 0.005 kg CO2e.

        Expected: 0.005 kg CO2e
        Tolerance: ±5%
        """
        bom = case_data["bill_of_materials"]
        result = calculator.calculate_with_categories(bom)

        expected = case_data["expected_result"]["breakdown"]["transport"]
        actual = result["breakdown_by_category"].get("transport", 0.0)

        # Check within tolerance range
        error_pct = abs(actual - expected) / expected * 100
        assert error_pct <= 5.0, (
            f"Phone Case transport error {error_pct:.2f}% exceeds 5% tolerance "
            f"(expected {expected}, actual {actual})"
        )


class TestValidationSuite:
    """Test validation suite functionality."""

    def test_validation_suite_exists(self):
        """Test that validation module and run_validation_suite function exist."""
        from backend.calculator import validation
        assert hasattr(validation, "run_validation_suite")

    def test_validation_suite_runs_all_products(self):
        """Test that validation suite runs all 3 products."""
        from backend.calculator.validation import run_validation_suite

        report = run_validation_suite()

        assert report["total_tests"] == 3
        assert "results" in report
        assert "t-shirt" in report["results"]
        assert "water_bottle" in report["results"]
        assert "phone_case" in report["results"]

    def test_validation_suite_returns_pass_fail_counts(self):
        """Test that validation suite returns passed and failed counts."""
        from backend.calculator.validation import run_validation_suite

        report = run_validation_suite()

        assert "passed" in report
        assert "failed" in report
        assert isinstance(report["passed"], int)
        assert isinstance(report["failed"], int)
        assert report["passed"] + report["failed"] == report["total_tests"]

    def test_validation_suite_includes_error_percentage(self):
        """Test that validation suite includes error percentage for each product."""
        from backend.calculator.validation import run_validation_suite

        report = run_validation_suite()

        for product_name, result in report["results"].items():
            assert "error_percentage" in result
            assert "within_tolerance" in result
            assert isinstance(result["within_tolerance"], bool)
            assert "actual" in result
            assert "expected" in result

    def test_validation_suite_performance(self):
        """Test that validation suite completes in <5 seconds."""
        import time
        from backend.calculator.validation import run_validation_suite

        start_time = time.time()
        report = run_validation_suite()
        elapsed_time = time.time() - start_time

        assert elapsed_time < 5.0, (
            f"Validation suite took {elapsed_time:.2f}s, exceeds 5s requirement"
        )
