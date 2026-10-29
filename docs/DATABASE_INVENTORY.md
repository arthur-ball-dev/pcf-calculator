# Database Inventory Report

This document provides a breakdown of emission factors and products in the PCF Calculator database.

**Last Updated:** 2026-02-10
**Database:** PostgreSQL (all environments)
**Data Sources:** EPA (US Public Domain), DEFRA (UK OGL v3.0)

---

## Emission Factors

### By Data Provider

| Provider | Count |
|----------|-------|
| EPA | 268 |
| DEFRA | 74 |
| **Total** | **342** |

**Note:** Only EPA and DEFRA emission factors are used. Previously evaluated data sources (Exiobase, Ecoinvent) were removed due to licensing requirements (academic and commercial licenses, respectively).

### By Category

| Category | Count |
|----------|-------|
| Combustion | ~93 |
| Material | ~59 |
| Electricity | ~28 |
| Other | ~25 |
| Energy | ~3 |
| Waste | ~3 |
| Additional EPA/DEFRA categories | ~131 |

---

## Products Summary

| Metric | Count |
|--------|-------|
| **Total Products** | **817** |
| Finished Products (with BOMs) | 725 |
| Components (without BOMs) | 92 |
| BOM Relationships | 7,025+ |

**Product Naming:** Products use fictional brand naming (e.g., "Dellware ProEdge 200 Titan 17") to avoid trademark issues while maintaining realistic catalog structure.

---

## Products by Industry

### Quick Reference Table

| Industry | Finished Products | Components | Total |
|----------|-------------------|------------|-------|
| Electronics | ~145 | ~18 | ~163 |
| Apparel | ~145 | ~18 | ~163 |
| Automotive | ~145 | ~18 | ~163 |
| Construction | ~145 | ~18 | ~163 |
| Food & Beverage | ~145 | ~18 | ~163 |
| **Total** | **725** | **92** | **817** |

**Note:** Product distribution is approximately equal across 5 industries, generated via BOM templates (17 templates, 32 component types).

---

## Product Catalog Structure

### BOM Templates (5 Industries)

Each industry has multiple product templates with standardized BOM structures:

**Electronics:** Laptops (Gaming, Business, Ultrabook, Standard), Monitors (24", 27", 32"), Smartphones (Flagship, Budget, Standard), Tablets

**Apparel:** T-Shirts (Basic, Organic, Premium), Jeans (Regular, Raw, Distressed), Jackets (Light, Outdoor, Winter), Shoes (Running, Casual, Boots)

**Automotive:** Car Seats (Manual, Power, Heated), Dashboards (Basic, Digital, Premium), Wheel Assemblies (Economy, Performance, Standard)

**Construction:** Door Assemblies (Interior, Exterior, Fire Rated), HVAC Units (Residential, Commercial, Industrial), Window Units (Single, Double, Triple Pane)

**Food & Beverage:** Beverage Bottles (Small, Standard, Large), Canned Food (Small, Standard, Large), Packaged Snacks (Single, Multi, Family)

### Example Products (Fictional Brand Names)

| Industry | Example Product Name | Code Pattern |
|----------|---------------------|--------------|
| Electronics | Dellware ProEdge 200 Titan 17 | ELE-LAPT-GAM-XXXX |
| Apparel | Threadmark Essential Crew Standard | APP-TSHI-BAS-XXXX |
| Automotive | AutoCraft PowerGlide 500 Heated | AUT-CAR_-HEA-XXXX |
| Construction | BuildPro SecureSeal 3000 Exterior | CON-DOOR-EXT-XXXX |
| Food & Beverage | FreshPack Premium Brew 1L | FOD-BEVE-LAR-XXXX |

---

## Original Seed Products (12 products)

These are the original development seed data products from JSON files, included in both test and production modes:

| Code | Name |
|------|------|
| HELMET-001 | Bicycle Helmet - Sport |
| MUG-001 | Ceramic Coffee Mug |
| TSHIRT-001 | Cotton T-Shirt - Realistic |
| LAMP-001 | LED Desk Lamp |
| CASE-001 | Phone Case - Realistic |
| SUNGLASSES-001 | Polarized Sunglasses |
| SHOES-001 | Running Shoes - Performance |
| PHONE-001 | Smartphone Pro |
| BACKPACK-001 | Travel Backpack 30L |
| BOTTLE-001 | Water Bottle - Realistic |
| EARBUDS-001 | Wireless Earbuds Pro |
| YOGAMAT-001 | Yoga Mat - Premium |

---

## Product Selector Behavior

### "With BOMs" Filter Selected

Shows only finished products that have Bill of Materials entries (725 total):
- Distributed across 5 industries
- Each product has a complete BOM with material, energy, and transport components
- Products use fictional brand naming for realism

### "All Products" Filter Selected

Shows all 817 products including:
- 725 finished products with BOMs
- 92 component/material products without BOMs

### Industry Filter

When combined with "With BOMs":
- Selecting a specific industry shows only finished products in that industry
- Selecting "All Industries" shows all 725 finished products across all industries

---

## Data Modes

The database supports two mutually exclusive data modes. Switching modes clears all data and loads fresh datasets.

### Test Mode
- 23 emission factors from `data/emission_factors_simple.csv`
- ~34 products (13 finished + 21 components) from `data/bom_*.json`
- ~144 BOM relationships
- **Use for:** Running pytest, development, debugging

### Production Mode
- 342 emission factors from EPA/DEFRA (downloaded to `data/epa/` and `data/defra/`)
- 817 products (725 finished + 92 components)
- 7,025+ BOM relationships
- **Use for:** Demo, UI testing, realistic data scenarios

### Mode Switching Commands

```bash
# Check current mode
python backend/scripts/check_data_mode.py

# Switch to test mode
python backend/scripts/load_test_data.py

# Switch to production mode
python backend/scripts/load_production_data.py
```

---

## Database Environments

| Environment | Database | Connection |
|-------------|----------|------------|
| Development | PostgreSQL (Docker) | `postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator` |
| Production | PostgreSQL (Railway) | Auto-configured via `DATABASE_URL` |
| Testing | PostgreSQL | `postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test` |

**Note:** SQLite is no longer used. All environments run PostgreSQL (as of Phase 9, 2026-01-14).

---

*Generated from production database inventory on 2026-02-10*
*Document Owner: Technical-Lead*
