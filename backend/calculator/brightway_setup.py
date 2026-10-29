"""
Brightway2 Project Initialization Module

This module provides functionality to initialize a Brightway2 project for PCF calculations.
It creates the project, installs the biosphere3 database, configures IPCC 2021 impact methods,
and sets up a custom database for emission factors.

Usage:
    from backend.calculator.brightway_setup import initialize_brightway

    initialize_brightway()  # Idempotent - safe to run multiple times

Brightway2 Documentation: https://docs.brightway.dev/
"""

import brightway2 as bw
import logging
from typing import Literal

logger = logging.getLogger(__name__)


def _create_ipcc_2021_methods():
    """
    Create IPCC 2021 GWP100 impact assessment method.

    Since Brightway2 2.4.3 only includes methods up to IPCC 2013,
    we manually create IPCC 2021 GWP100 using the key GWP values
    from the IPCC AR6 report (2021).

    Reference: IPCC AR6 Working Group I, Table 7.15
    https://www.ipcc.ch/report/ar6/wg1/
    """
    method_name = ('IPCC 2021', 'climate change', 'GWP100')

    # Check if method already exists
    if method_name in bw.methods:
        logger.info("IPCC 2021 GWP100 method already exists")
        return

    # Get biosphere database to link flows
    biosphere = bw.Database('biosphere3')

    # Key GHG characterization factors from IPCC AR6 (100-year GWP)
    # Format: (flow_name, categories, GWP value)
    # Note: biosphere3 uses nested tuple categories like ('air', 'urban air close to ground')
    gwp_factors = [
        # CO2 - baseline
        ('Carbon dioxide', ('air',), 1.0),
        ('Carbon dioxide, fossil', ('air',), 1.0),
        ('Carbon dioxide, non-fossil', ('air',), 1.0),

        # Methane - AR6 values
        ('Methane', ('air',), 27.0),
        ('Methane, fossil', ('air',), 29.8),
        ('Methane, non-fossil', ('air',), 27.2),
        ('Methane, tetrafluoro-, CFC-14', ('air',), 7380.0),

        # N2O
        ('Dinitrogen monoxide', ('air',), 273.0),

        # Fluorinated gases
        ('Sulfur hexafluoride', ('air',), 25200.0),
        ('Nitrogen trifluoride', ('air',), 17400.0),
    ]

    # Build characterization factors list
    cfs = []
    biosphere_list = list(biosphere)

    for flow_name, target_categories, gwp_value in gwp_factors:
        # Find matching biosphere flows - try exact match first
        matches = [
            act for act in biosphere_list
            if act['name'] == flow_name and act.get('categories', ()) == target_categories
        ]

        # If no exact match, try finding flows with this name and any subcategory of target
        if not matches:
            matches = [
                act for act in biosphere_list
                if act['name'] == flow_name
                and len(act.get('categories', ())) >= len(target_categories)
                and act.get('categories', ())[:len(target_categories)] == target_categories
            ]

        if matches:
            for match in matches:
                cfs.append((match.key, gwp_value))
                logger.debug(f"Added CF for {flow_name} {match.get('categories', ())}: {gwp_value} kg CO2-eq")
        else:
            logger.warning(f"No biosphere flow found for {flow_name} {target_categories}")

    # Create and write the method
    if cfs:
        method = bw.Method(method_name)
        method.register(unit='kg CO2-eq', description='IPCC 2021 AR6 GWP100')
        method.write(cfs)
        logger.info(f"Created IPCC 2021 GWP100 method with {len(cfs)} characterization factors")
    else:
        logger.error("No characterization factors could be created for IPCC 2021 method")


def initialize_brightway() -> Literal[True]:
    """
    Initialize Brightway2 project for PCF calculations.

    This function:
    1. Creates or sets the "pcf_calculator" project
    2. Installs biosphere3 database and IPCC methods via bw2setup()
    3. Creates IPCC 2021 GWP100 method (not included in bw2setup)
    4. Creates an empty "pcf_emission_factors" database for custom data

    The function is idempotent - it's safe to run multiple times.
    On subsequent runs, it will reuse existing resources.

    Returns:
        True: Always returns True upon successful initialization

    Raises:
        Exception: If Brightway2 setup fails (e.g., network issues, disk full)

    Example:
        >>> initialize_brightway()
        True
        >>> import brightway2 as bw
        >>> "pcf_calculator" in bw.projects
        True
        >>> "biosphere3" in bw.databases
        True
    """
    # Set or create project
    if "pcf_calculator" not in bw.projects:
        bw.projects.set_current("pcf_calculator")
        logger.info("Created new Brightway2 project: pcf_calculator")

        # Install default biosphere and methods
        # bw2setup() installs:
        # - biosphere3 database (elementary flows like CO2, CH4, etc.)
        # - LCIA methods (IPCC 2013, ReCiPe, etc.)
        bw.bw2setup()
        logger.info("Installed biosphere3 database and IPCC impact methods")

        # Create IPCC 2021 method (not included in default setup)
        _create_ipcc_2021_methods()
    else:
        bw.projects.set_current("pcf_calculator")
        logger.info("Using existing Brightway2 project: pcf_calculator")

        # Ensure IPCC 2021 method exists even in existing projects
        _create_ipcc_2021_methods()

    # Create custom emission factors database if not exists
    # This database will be populated with emission factors from our SQLite database
    if "pcf_emission_factors" not in bw.databases:
        db = bw.Database("pcf_emission_factors")
        db.write({})  # Create empty database (will be populated later)
        logger.info("Created empty pcf_emission_factors database")
    else:
        logger.info("Using existing pcf_emission_factors database")

    return True
