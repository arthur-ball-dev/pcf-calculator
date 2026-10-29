"""
Validation Module - PCF Calculator Accuracy Testing

This module provides validation utilities for testing PCF calculator accuracy
against known expected results. It includes:
- Validation suite for all realistic BOMs
- Helper functions for normalizing test data
- Performance benchmarking

Expected Results (±5% tolerance):
- T-shirt: 2.05 kg CO2e (materials 1.04, energy 1.0, transport 0.01)
- Water Bottle: 0.157 kg CO2e (materials 0.095, energy 0.06, transport 0.002)
- Phone Case: 0.343 kg CO2e (materials 0.138, energy 0.2, transport 0.005)

TASK-CALC-004: Validate Calculations Against Expected Results
"""

import json
import os
import logging
from typing import Dict, Any, List

from backend.calculator.pcf_calculator import PCFCalculator


logger = logging.getLogger(__name__)


# Path to test data files
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def normalize_bom_format(bom: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize BOM format from JSON files to calculator format.

    The JSON files use "component_name" but the calculator expects "name".
    This function normalizes the field names and preserves other fields.

    Args:
        bom: BOM data from JSON file with "component_name" field

    Returns:
        Normalized BOM with "name" field for calculator

    Example:
        >>> json_bom = [{"component_name": "cotton", "quantity": 0.18, "unit": "kg"}]
        >>> normalized = normalize_bom_format(json_bom)
        >>> assert normalized[0]["name"] == "cotton"
    """
    normalized = []

    for item in bom:
        normalized_item = {
            "name": item.get("component_name", item.get("name")),
            "quantity": item["quantity"],
            "unit": item["unit"]
        }

        # Preserve optional fields
        if "category" in item:
            normalized_item["category"] = item["category"]
        if "description" in item:
            normalized_item["description"] = item["description"]
        if "data_source" in item:
            normalized_item["data_source"] = item["data_source"]

        normalized.append(normalized_item)

    return normalized


def infer_category_from_data(item: Dict[str, Any]) -> str:
    """
    Infer category (materials, energy, transport) from BOM item.

    The JSON test data doesn't include explicit "category" fields, so we
    infer them from component names and descriptions.

    Rules:
    - energy_data items → "energy"
    - transport_data items → "transport"
    - bill_of_materials items → "materials"

    Args:
        item: BOM item with component_name

    Returns:
        Category string: "materials", "energy", or "transport"

    Example:
        >>> item = {"component_name": "electricity_us", "quantity": 2.5}
        >>> assert infer_category_from_data(item) == "energy"
    """
    name = item.get("component_name", item.get("name", "")).lower()

    # Energy indicators
    if any(keyword in name for keyword in ["electricity", "energy", "kwh", "natural_gas"]):
        return "energy"

    # Transport indicators
    if any(keyword in name for keyword in ["transport", "truck", "ship", "freight", "tkm"]):
        return "transport"

    # Default to materials
    return "materials"


def convert_realistic_json_to_calculator_format(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert realistic JSON format to calculator BOM format.

    The realistic JSON files have structure:
    {
        "bill_of_materials": [...],
        "energy_data": {...},
        "transport_data": [...]
    }

    This function combines all three sections into a single flat BOM with
    inferred categories.

    Args:
        data: Full JSON data from realistic BOM file

    Returns:
        Flat BOM list ready for calculator with categories

    Example:
        >>> with open("data/bom_tshirt_realistic.json") as f:
        ...     data = json.load(f)
        >>> bom = convert_realistic_json_to_calculator_format(data)
        >>> assert all("category" in item for item in bom)
    """
    flat_bom = []

    # Add materials from bill_of_materials
    if "bill_of_materials" in data:
        for item in data["bill_of_materials"]:
            normalized = {
                "name": item["component_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "category": "materials"
            }
            if "description" in item:
                normalized["description"] = item["description"]
            flat_bom.append(normalized)

    # Add energy data
    if "energy_data" in data:
        energy = data["energy_data"]
        # Map location to emission factor name
        location = energy.get("location", "US")
        energy_name = f"electricity_{location.lower()}"

        flat_bom.append({
            "name": energy_name,
            "quantity": energy["electricity_kwh"],
            "unit": "kWh",
            "category": "energy"
        })

    # Add transport data
    if "transport_data" in data:
        for transport in data["transport_data"]:
            mode = transport["mode"]
            distance_km = transport["distance_km"]
            mass_kg = transport["mass_kg"]

            # Calculate tonne-kilometers (tkm)
            tkm = (mass_kg / 1000.0) * distance_km

            # Map mode to emission factor name
            transport_name = f"transport_{mode}"

            flat_bom.append({
                "name": transport_name,
                "quantity": tkm,
                "unit": "tkm",
                "category": "transport"
            })

    return flat_bom


def run_validation_suite() -> Dict[str, Any]:
    """
    Run validation suite against all realistic BOMs.

    Tests all 3 products (T-shirt, Water Bottle, Phone Case) against their
    expected results and returns a comprehensive validation report.

    Returns:
        Validation report with structure:
        {
            "total_tests": int,
            "passed": int,
            "failed": int,
            "results": {
                "product_name": {
                    "actual": float,
                    "expected": float,
                    "error_percentage": float,
                    "within_tolerance": bool,
                    "breakdown": {...}
                },
                ...
            }
        }

    Example:
        >>> report = run_validation_suite()
        >>> assert report["total_tests"] == 3
        >>> assert report["passed"] + report["failed"] == 3
    """
    calculator = PCFCalculator()
    results = {}

    test_files = [
        ("t-shirt", "bom_tshirt_realistic.json"),
        ("water_bottle", "bom_water_bottle_realistic.json"),
        ("phone_case", "bom_phone_case_realistic.json"),
    ]

    passed = 0
    failed = 0

    for product_name, filename in test_files:
        file_path = os.path.join(DATA_DIR, filename)

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Convert JSON format to calculator format
            bom = convert_realistic_json_to_calculator_format(data)

            # Calculate PCF
            result = calculator.calculate_with_categories(bom)

            # Get expected result
            expected = data["expected_result"]["total_co2e_kg"]

            # Calculate error
            actual = result["total_co2e_kg"]
            error = abs(actual - expected)
            error_pct = (error / expected) * 100

            # Check tolerance
            within_tolerance = error_pct <= 5.0

            if within_tolerance:
                passed += 1
                logger.info(
                    f"✓ {product_name}: {actual:.4f} kg CO2e "
                    f"(expected {expected}, error {error_pct:.2f}%)"
                )
            else:
                failed += 1
                logger.warning(
                    f"✗ {product_name}: {actual:.4f} kg CO2e "
                    f"(expected {expected}, error {error_pct:.2f}%)"
                )

            # Store detailed results
            results[product_name] = {
                "actual": actual,
                "expected": expected,
                "error_percentage": error_pct,
                "within_tolerance": within_tolerance,
                "breakdown": result["breakdown"],
                "breakdown_by_category": result["breakdown_by_category"]
            }

            # Compare breakdown if available
            if "breakdown" in data["expected_result"]:
                expected_breakdown = data["expected_result"]["breakdown"]
                actual_breakdown = result["breakdown_by_category"]

                breakdown_errors = {}
                for category, expected_value in expected_breakdown.items():
                    actual_value = actual_breakdown.get(category, 0.0)
                    category_error = abs(actual_value - expected_value)
                    category_error_pct = (category_error / expected_value) * 100
                    breakdown_errors[category] = {
                        "expected": expected_value,
                        "actual": actual_value,
                        "error_percentage": category_error_pct,
                        "within_tolerance": category_error_pct <= 5.0
                    }

                results[product_name]["breakdown_validation"] = breakdown_errors

        except Exception as e:
            logger.error(f"Error validating {product_name}: {str(e)}")
            failed += 1
            results[product_name] = {
                "error": str(e),
                "within_tolerance": False
            }

    return {
        "total_tests": len(test_files),
        "passed": passed,
        "failed": failed,
        "results": results
    }


def generate_validation_report(report: Dict[str, Any]) -> str:
    """
    Generate human-readable validation report.

    Args:
        report: Validation report from run_validation_suite()

    Returns:
        Formatted report string

    Example:
        >>> report = run_validation_suite()
        >>> print(generate_validation_report(report))
    """
    lines = []
    lines.append("=" * 80)
    lines.append("PCF CALCULATOR VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Tests: {report['total_tests']}")
    lines.append(f"Passed: {report['passed']}")
    lines.append(f"Failed: {report['failed']}")
    lines.append(f"Pass Rate: {report['passed'] / report['total_tests'] * 100:.1f}%")
    lines.append("")
    lines.append("=" * 80)
    lines.append("DETAILED RESULTS")
    lines.append("=" * 80)
    lines.append("")

    for product_name, result in report["results"].items():
        if "error" in result:
            lines.append(f"✗ {product_name.upper()}: ERROR")
            lines.append(f"  Error: {result['error']}")
            lines.append("")
            continue

        status = "✓ PASS" if result["within_tolerance"] else "✗ FAIL"
        lines.append(f"{status} - {product_name.upper()}")
        lines.append(f"  Expected: {result['expected']:.4f} kg CO2e")
        lines.append(f"  Actual:   {result['actual']:.4f} kg CO2e")
        lines.append(f"  Error:    {result['error_percentage']:.2f}%")
        lines.append("")

        if "breakdown_by_category" in result:
            lines.append("  Breakdown by Category:")
            for category, value in result["breakdown_by_category"].items():
                lines.append(f"    {category.capitalize()}: {value:.4f} kg CO2e")
            lines.append("")

        if "breakdown_validation" in result:
            lines.append("  Category Validation:")
            for category, validation in result["breakdown_validation"].items():
                cat_status = "✓" if validation["within_tolerance"] else "✗"
                lines.append(
                    f"    {cat_status} {category.capitalize()}: "
                    f"{validation['actual']:.4f} kg CO2e "
                    f"(expected {validation['expected']:.4f}, "
                    f"error {validation['error_percentage']:.2f}%)"
                )
            lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """
    Run validation suite from command line.

    Usage:
        python -m backend.calculator.validation
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("\nRunning PCF Calculator Validation Suite...\n")

    report = run_validation_suite()
    formatted_report = generate_validation_report(report)

    print(formatted_report)

    # Exit with error code if any tests failed
    if report["failed"] > 0:
        exit(1)
    else:
        print("\n✓ All validation tests passed!\n")
        exit(0)


if __name__ == "__main__":
    main()
