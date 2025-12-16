"""
Exiobase test fixtures for data ingestion tests.

TASK-DATA-P5-004: Exiobase Data Connector - Phase A Tests

This module provides functions to create Exiobase-style test data files
programmatically. Exiobase uses ZIP archives containing CSV/TSV matrices.

The F matrix (satellite account) contains emission intensities per product
per region in the format: stressor x (region_product).

Usage:
    from backend.tests.fixtures.exiobase_fixtures import create_exiobase_sample_zip

    zip_bytes = create_exiobase_sample_zip()
"""

import io
import zipfile
from io import BytesIO
from typing import List, Dict, Any, Optional
import csv


# Exiobase regions (49 total: 44 countries + 5 rest-of-world)
EXIOBASE_REGIONS = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK", "GB", "US", "JP",
    "CN", "CA", "KR", "BR", "IN", "MX", "RU", "AU", "CH", "TR",
    "TW", "NO", "ID", "ZA",
    "WA", "WL", "WE", "WF", "WM",  # Rest-of-world regions
]

# Sample product categories matching Exiobase structure
SAMPLE_PRODUCTS = [
    "Electricity by coal",
    "Electricity by gas",
    "Electricity by nuclear",
    "Motor Gasoline",
    "Gas/Diesel Oil",
    "Natural Gas and services",
    "Coal and lignite",
    "Iron and steel",
    "Aluminium and aluminium products",
    "Cement",
    "Plastics, basic",
    "Paper and paper products",
    "Textiles",
    "Chemicals nec",
    "Motor vehicles",
    "Electronic equipment nec",
    "Machinery and equipment nec",
]

# GHG stressors in Exiobase F matrix
GHG_STRESSORS = [
    "CO2 - combustion - air",
    "CH4 - combustion - air",
    "N2O - combustion - air",
    "CO2 - non combustion - Cement production",
    "CO2 - non combustion - Chemicals",
]


def create_exiobase_sample_zip(
    num_regions: int = 5,
    num_products: int = 5,
    include_f_matrix: bool = True,
    f_matrix_filename: str = "satellite/F.txt"
) -> bytes:
    """
    Create a minimal Exiobase-style ZIP archive for testing.

    Creates a ZIP containing a sample F matrix (emission intensity matrix)
    with the structure matching real Exiobase 3.8.2 data.

    Args:
        num_regions: Number of regions to include (default 5)
        num_products: Number of products per region (default 5)
        include_f_matrix: Whether to include F matrix file
        f_matrix_filename: Path within ZIP for F matrix

    Returns:
        bytes: ZIP archive content
    """
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        if include_f_matrix:
            f_matrix_content = _create_f_matrix_tsv(num_regions, num_products)
            zf.writestr(f_matrix_filename, f_matrix_content)

        # Add a metadata file (common in Exiobase)
        metadata = "Exiobase 3.8.2 Test Sample\nCreated for unit testing\n"
        zf.writestr("readme.txt", metadata)

    buffer.seek(0)
    return buffer.getvalue()


def _create_f_matrix_tsv(num_regions: int, num_products: int) -> str:
    """
    Create the F matrix content in TSV format.

    The F matrix has:
    - Rows: Environmental stressors (emissions)
    - Columns: Region_Product combinations

    Args:
        num_regions: Number of regions to include
        num_products: Number of products per region

    Returns:
        str: TSV content for F matrix
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')

    # Select subset of regions and products
    regions = EXIOBASE_REGIONS[:num_regions]
    products = SAMPLE_PRODUCTS[:num_products]

    # Header row: stressor name column + all region_product combinations
    header = ["stressor"]
    for region in regions:
        for product in products:
            header.append(f"{region}_{product}")
    writer.writerow(header)

    # Data rows: one per stressor
    for stressor in GHG_STRESSORS:
        row = [stressor]
        for region in regions:
            for product in products:
                # Generate realistic emission values based on stressor type
                base_value = _get_base_emission_value(stressor, product)
                # Add some regional variation
                region_factor = _get_region_factor(region)
                value = base_value * region_factor
                row.append(f"{value:.6f}")
        writer.writerow(row)

    return output.getvalue()


def _get_base_emission_value(stressor: str, product: str) -> float:
    """
    Get base emission value based on stressor and product.

    CO2 emissions are much higher than CH4 and N2O.
    Energy-intensive products have higher emissions.

    Args:
        stressor: Stressor name
        product: Product name

    Returns:
        float: Base emission value
    """
    # Base values by stressor type (kg per EUR output)
    stressor_base = {
        "CO2 - combustion - air": 0.5,
        "CH4 - combustion - air": 0.001,  # Much lower than CO2
        "N2O - combustion - air": 0.0001,  # Even lower
        "CO2 - non combustion - Cement production": 0.3,
        "CO2 - non combustion - Chemicals": 0.2,
    }

    # Product multipliers (energy-intensive = higher)
    product_multiplier = {
        "Electricity by coal": 3.0,
        "Electricity by gas": 1.5,
        "Electricity by nuclear": 0.1,
        "Motor Gasoline": 2.5,
        "Gas/Diesel Oil": 2.2,
        "Natural Gas and services": 1.8,
        "Coal and lignite": 4.0,
        "Iron and steel": 2.0,
        "Aluminium and aluminium products": 3.5,
        "Cement": 2.8,
        "Plastics, basic": 1.5,
        "Paper and paper products": 0.8,
        "Textiles": 0.6,
        "Chemicals nec": 1.2,
        "Motor vehicles": 0.5,
        "Electronic equipment nec": 0.3,
        "Machinery and equipment nec": 0.4,
    }

    base = stressor_base.get(stressor, 0.1)
    multiplier = product_multiplier.get(product, 1.0)

    return base * multiplier


def _get_region_factor(region: str) -> float:
    """
    Get regional emission factor multiplier.

    Different regions have different emission intensities
    based on their energy mix and industrial efficiency.

    Args:
        region: Region code

    Returns:
        float: Regional multiplier
    """
    # High-carbon regions (coal-heavy energy mix)
    high_carbon = ["CN", "IN", "AU", "ZA", "PL"]
    # Low-carbon regions (renewable/nuclear heavy)
    low_carbon = ["FR", "SE", "NO", "CH", "AT"]

    if region in high_carbon:
        return 1.5
    elif region in low_carbon:
        return 0.6
    else:
        return 1.0


def create_exiobase_zip_without_f_matrix() -> bytes:
    """
    Create an Exiobase ZIP without F matrix for error testing.

    Returns:
        bytes: ZIP archive without F matrix file
    """
    return create_exiobase_sample_zip(include_f_matrix=False)


def create_exiobase_zip_with_alternate_f_path(path: str = "IOT/F.txt") -> bytes:
    """
    Create an Exiobase ZIP with F matrix in alternate location.

    Different Exiobase versions may have F matrix in different paths.

    Args:
        path: Path within ZIP for F matrix

    Returns:
        bytes: ZIP archive content
    """
    return create_exiobase_sample_zip(f_matrix_filename=path)


def create_exiobase_zip_full_regions() -> bytes:
    """
    Create an Exiobase ZIP with all 49 regions.

    Useful for testing multi-region coverage requirements.

    Returns:
        bytes: ZIP archive with all regions
    """
    return create_exiobase_sample_zip(
        num_regions=49,
        num_products=5
    )


def create_large_exiobase_zip(
    num_regions: int = 49,
    num_products: int = 200
) -> bytes:
    """
    Create a large Exiobase ZIP for performance/memory testing.

    Warning: This creates a large file (~MB range depending on parameters).

    Args:
        num_regions: Number of regions (max 49)
        num_products: Number of products (max 200)

    Returns:
        bytes: ZIP archive content
    """
    # Cap at actual Exiobase limits
    num_regions = min(num_regions, len(EXIOBASE_REGIONS))

    # Generate more products for large test
    extended_products = SAMPLE_PRODUCTS.copy()
    while len(extended_products) < num_products:
        idx = len(extended_products)
        extended_products.append(f"Product_{idx}")

    return create_exiobase_sample_zip(
        num_regions=num_regions,
        num_products=min(num_products, len(extended_products))
    )


def create_exiobase_zip_with_zero_values() -> bytes:
    """
    Create an Exiobase ZIP where some emission values are zero.

    Useful for testing filtering of zero/null values.

    Returns:
        bytes: ZIP archive content
    """
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')

        regions = ["DE", "FR", "US"]
        products = ["Electricity by coal", "Iron and steel"]

        # Header
        header = ["stressor"]
        for region in regions:
            for product in products:
                header.append(f"{region}_{product}")
        writer.writerow(header)

        # Data with some zeros
        for stressor in GHG_STRESSORS[:3]:
            row = [stressor]
            for i, region in enumerate(regions):
                for j, product in enumerate(products):
                    # Some values are zero
                    if (i + j) % 3 == 0:
                        row.append("0")
                    else:
                        row.append(f"{0.5:.6f}")
            writer.writerow(row)

        zf.writestr("satellite/F.txt", output.getvalue())

    buffer.seek(0)
    return buffer.getvalue()


def create_exiobase_zip_with_malformed_data() -> bytes:
    """
    Create an Exiobase ZIP with malformed data.

    Useful for testing error handling.

    Returns:
        bytes: ZIP archive content
    """
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Invalid TSV content
        malformed_content = "this\tis\tnot\tvalid\texiobase\tdata\n"
        zf.writestr("satellite/F.txt", malformed_content)

    buffer.seek(0)
    return buffer.getvalue()


def get_expected_regions() -> List[str]:
    """
    Get the full list of Exiobase regions.

    Returns:
        List[str]: All 49 Exiobase region codes
    """
    return EXIOBASE_REGIONS.copy()


def get_expected_stressors() -> List[str]:
    """
    Get the list of GHG stressors used in fixtures.

    Returns:
        List[str]: GHG stressor names
    """
    return GHG_STRESSORS.copy()


__all__ = [
    'create_exiobase_sample_zip',
    'create_exiobase_zip_without_f_matrix',
    'create_exiobase_zip_with_alternate_f_path',
    'create_exiobase_zip_full_regions',
    'create_large_exiobase_zip',
    'create_exiobase_zip_with_zero_values',
    'create_exiobase_zip_with_malformed_data',
    'get_expected_regions',
    'get_expected_stressors',
    'EXIOBASE_REGIONS',
    'GHG_STRESSORS',
    'SAMPLE_PRODUCTS',
]
