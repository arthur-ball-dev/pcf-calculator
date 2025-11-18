# Test Data Documentation

This directory contains test data files for the PCF Calculator MVP, including emission factors and product Bill of Materials (BOMs).

## Emission Factors CSV

### File: `emission_factors_simple.csv`

**Purpose:** Provides CO2e emission factors for materials, energy, and transport used in PCF calculations.

**Format:** CSV with UTF-8 encoding

**Columns:**
- `activity_name`: Unique identifier for the emission activity (e.g., "cotton", "electricity_us")
- `co2e_factor`: CO2 equivalent emission factor (positive numeric value)
- `unit`: Unit of measurement (kg, kWh, tkm, L, MJ)
- `data_source`: Source of the emission factor (EPA, DEFRA, or Ecoinvent)
- `geography`: Geographic scope (GLO for global, US, EU, etc.)

**Content:** 20 emission factors covering:
- **Materials (16):** cotton, polyester, plastic_pet, plastic_abs, plastic_hdpe, aluminum, steel, glass, paper, rubber, copper, wood, leather, nylon, ceramic, foam
- **Energy (1):** electricity_us
- **Transport (2):** transport_truck, transport_ship
- **Other (1):** water

**Key Values:**
- Cotton: 5.0 kg CO2e/kg
- Electricity (US): 0.4 kg CO2e/kWh
- Transport truck: 0.1 kg CO2e/tkm
- Water: 0.001 kg CO2e/L

**Data Quality:**
- No null values
- All emission factors are positive
- All activity names are unique
- Data sources properly attributed
- Compatible with database schema constraints

**Usage:**
```python
import pandas as pd
df = pd.read_csv('data/emission_factors_simple.csv')
```

Loaded into database via: `backend/scripts/seed_data.py`

**Tests:** `backend/tests/test_data/test_emission_factors_csv.py` (32 tests)

---

## Product Bill of Materials (BOMs)

### Overview

Six JSON files representing three products with simple and realistic variants:
1. **T-Shirt** (`bom_tshirt_*.json`)
2. **Water Bottle** (`bom_water_bottle_*.json`)
3. **Phone Case** (`bom_phone_case_*.json`)

### Variants

**Simple BOMs:**
- Basic material composition only
- No energy or transport data (zero values, not missing fields)
- Used for quick validation testing

**Realistic BOMs:**
- Complete supply chain data
- Includes energy consumption
- Includes transport emissions
- Contains `expected_result` for validation

### JSON Structure

```json
{
  "product": {
    "id": "unique-id",
    "code": "PRODUCT-001",
    "name": "Product Name",
    "unit": "unit",
    "is_finished_product": true
  },
  "bill_of_materials": [
    {
      "component_name": "cotton",
      "quantity": 0.18,
      "unit": "kg",
      "description": "optional"
    }
  ],
  "energy_data": {
    "electricity_kwh": 2.5,
    "location": "US"
  },
  "transport_data": [
    {
      "mode": "truck",
      "distance_km": 500,
      "mass_kg": 0.203
    }
  ],
  "expected_result": {
    "total_co2e_kg": 2.05,
    "breakdown": {
      "materials": 1.04,
      "energy": 1.0,
      "transport": 0.01
    },
    "notes": "Calculation notes"
  }
}
```

### Product Details

#### T-Shirt (TSHIRT-001)
- **Simple:** 2 components (cotton, polyester)
- **Realistic:** 5 components + energy + transport
- **Expected PCF:** 2.05 kg CO2e
  - Materials: 1.04 kg CO2e
  - Energy: 1.0 kg CO2e (2.5 kWh)
  - Transport: 0.01 kg CO2e (500 km truck)

#### Water Bottle (BOTTLE-001)
- **Simple:** Basic plastic_hdpe composition
- **Realistic:** plastic_hdpe + aluminum cap + energy + transport
- **Contains:** Complete supply chain for beverage packaging

#### Phone Case (CASE-001)
- **Simple:** Basic plastic_abs composition
- **Realistic:** plastic_abs + foam padding + energy + transport
- **Contains:** Electronics accessory manufacturing data

### BOM Structure Validation

All BOMs have been validated for:
- **File Existence:** All 6 JSON files exist and are valid JSON
- **Structure Consistency:** All BOMs have consistent keys (product, bill_of_materials, energy_data, transport_data)
- **Product Codes:** Simple and realistic variants share product codes (3 unique products)
- **Component References:** All component_name values match emission_factors_simple.csv activity_name values
- **Data Types:** All fields have correct data types (strings, numbers, booleans, arrays)
- **Positive Quantities:** All component quantities are positive numbers
- **Valid Units:** All units are in approved list (kg, unit, L, kWh, MJ, tkm, m, m2, m3)
- **Expected Results:** Realistic BOMs include expected_result with total_co2e_kg and breakdown
- **Energy/Transport:** Simple BOMs have zero energy/transport; realistic BOMs have positive values

### Component Validation

All `component_name` values in BOMs must match `activity_name` values in `emission_factors_simple.csv`.

**Example:**
```bash
# Verify all BOM components have matching emission factors
python -c "
import json
import pandas as pd
ef = pd.read_csv('data/emission_factors_simple.csv')
for file in ['bom_tshirt_realistic.json', 'bom_water_bottle_realistic.json', 'bom_phone_case_realistic.json']:
    with open(f'data/{file}') as f:
        bom = json.load(f)
    for comp in bom['bill_of_materials']:
        assert comp['component_name'] in ef['activity_name'].values
print('All components validated!')
"
```

### Usage

**Load BOM:**
```python
import json
with open('data/bom_tshirt_realistic.json') as f:
    bom = json.load(f)
```

**Loaded into database via:** `backend/scripts/seed_data.py`

**Tests:** `backend/tests/test_data/test_product_boms.py` (59 tests)

---

## Data Quality Standards

### Validation Requirements

1. **Emission Factors CSV:**
   - Exactly 20 rows
   - 5 columns in correct order
   - No null values
   - Positive CO2e factors
   - Valid units (kg, kWh, tkm, L, MJ)
   - Valid data sources (EPA, DEFRA, Ecoinvent)
   - Unique activity names

2. **BOM JSON Files:**
   - Valid JSON structure
   - All components match emission factors
   - Realistic BOMs have expected_result
   - Quantities are positive numbers
   - Units are consistent
   - Simple BOMs have zero energy/transport (not missing)
   - Realistic BOMs have positive energy/transport

### Test Coverage

- **emission_factors_simple.csv:** 32 tests (100% pass)
- **BOM files:** 59 tests (100% pass) - TASK-DATA-002 complete

### Maintenance

When adding new emission factors or products:
1. Update CSV/JSON files
2. Run validation tests
3. Update seed_data.py script
4. Verify database loading works

---

## References

- **Database Schema:** `/knowledge/database-schema.md`
- **Seed Data Script:** `/backend/scripts/seed_data.py`
- **Test Specifications:**
  - TASK-DATA-001: Emission Factors CSV Validation (COMPLETE)
  - TASK-DATA-002: BOM File Validation (COMPLETE)
  - TASK-DATA-003: Seed Data Loading

---

**Last Updated:** 2025-10-24
**Data Engineer:** AI-assisted data engineering
