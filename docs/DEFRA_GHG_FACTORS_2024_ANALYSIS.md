# DEFRA GHG Conversion Factors 2024 - Structure Analysis

**File:** `/data/defra/ghg-conversion-factors-2024.xlsx`
**Publication Date:** 2024
**Next Publication:** 2025-06-10
**Geography:** United Kingdom

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Sheets | 40 |
| Sheets with emission factors | 29 |
| Reference/metadata sheets | 11 |

---

## Sheet Directory

### Sheets WITH Emission Factor Data (29 sheets)

| Sheet Name | Data Rows | Key Categories |
|------------|-----------|----------------|
| Fuels | 117 | Gaseous fuels, Liquid fuels, Solid fuels |
| Bioenergy | 49 | Biofuels, Biomass |
| Passenger vehicles | 34 | Cars by segment, Motorcycles |
| Delivery vehicles | 40 | Vans by class |
| UK electricity | 1 | Grid electricity |
| UK electricity for EVs | 30 | EV charging factors |
| Heat and steam | 2 | District heating |
| WTT- fuels | 114 | Well-to-tank fuel emissions |
| WTT- bioenergy | 47 | Well-to-tank bioenergy |
| Transmission and distribution | 2 | Grid T&D losses |
| UK electricity T&D for EVs | 30 | EV T&D factors |
| WTT- UK electricity | 2 | Upstream electricity |
| WTT- heat and steam | 3 | Upstream heating |
| Water supply | 2 | Mains water supply |
| Water treatment | 2 | Wastewater treatment |
| **Material use** | 41 | **Materials/products** |
| **Waste disposal** | 42 | **End-of-life disposal** |
| Business travel- air | 14 | Air travel by haul |
| WTT- business travel- air | 14 | Upstream air travel |
| Business travel- sea | 3 | Ferry travel |
| WTT- business travel- sea | 3 | Upstream sea travel |
| Business travel- land | 46 | Rail, bus, taxi |
| WTT- pass vehs & travel- land | 46 | Upstream land travel |
| **Freighting goods** | 102+ | **Freight transport** |
| WTT- delivery vehs & freight | 49 | Upstream freight |
| Hotel stay | 39 | Hotel emissions by country |
| Managed assets- electricity | 1 | Leased assets |
| Managed assets- vehicles | 54 | Fleet vehicles |
| Homeworking | 3 | Remote work emissions |
| Outside of scopes | 56 | Biogenic emissions |

### Reference/Metadata Sheets (11 sheets)

- Introduction
- What's new
- Index
- Refrigerant & other (non-numeric factors)
- SECR kWh pass & delivery vehs
- Overseas electricity
- SECR kWh UK electricity for EVs
- Conversions
- Fuel properties
- Haul definition

---

## Key Sheets for PCF Calculator

### 1. Material Use Sheet

**Purpose:** Emission factors for procured materials (Scope 3 upstream)

**Structure:**
- Header row: 21
- Data rows: ~41
- Columns: Activity | Material | Unit | kg CO2e (by lifecycle stage)

**Lifecycle Stage Columns:**
1. Primary material production
2. Re-used
3. Open-loop source (recycled)
4. Closed-loop source (recycled)

**Material Categories:**

#### Construction Materials
| Material | Primary (kg CO2e/tonne) | Closed-loop |
|----------|------------------------|-------------|
| Aggregates | 7.75 | 3.19 |
| Asbestos | 27.00 | - |
| Asphalt | 39.21 | 28.65 |
| Bricks | 241.75 | - |
| Concrete | 118.75 | 3.19 |
| Insulation | 1,861.75 | 1,852.08 |
| Metals | 3,815.78 | 1,630.79 |
| Mineral oil | 1,401.00 | 676.00 |
| Plasterboard | 120.05 | 32.17 |
| Tyres | 3,335.57 | 731.22 (re-used) |
| Wood | 269.50 | 38.54 (re-used) |
| Glass | 1,402.77 | 823.19 |
| Clothing | 22,310.00 | 152.25 (re-used) |

#### Electrical Items & Batteries
| Material | Primary (kg CO2e/tonne) |
|----------|------------------------|
| Electrical items - fridges and freezers | 4,363.33 |
| Electrical items - large | 3,267.00 |
| Electrical items - IT | 24,865.48 |
| Electrical items - small | 5,647.95 |
| Batteries - Alkaline | 4,633.48 |
| Batteries - Li ion | 6,308.00 |
| Batteries - NiMh | 28,380.00 |

#### Metals
| Material | Primary (kg CO2e/tonne) | Closed-loop |
|----------|------------------------|-------------|
| Aluminium cans and foil | 9,106.92 | 990.48 |
| Mixed cans | 5,105.64 | 1,461.68 |
| Scrap metal | 3,464.56 | 1,620.28 |
| Steel cans | 2,854.92 | 1,726.73 |

#### Plastics
| Material | Primary (kg CO2e/tonne) | Closed-loop |
|----------|------------------------|-------------|
| Average plastics | 3,164.78 | 1,566.39 |
| Average plastic film | 2,910.47 | 1,094.58 |
| Average plastic rigid | 3,345.31 | 1,906.70 |
| HDPE | 3,086.39 | 1,761.81 |
| LDPE and LLDPE | 2,959.32 | 1,088.92 |
| PET | 3,854.92 | 2,204.92 |
| PP | 2,568.59 | 1,303.59 |
| PS | 4,367.44 | 2,660.40 |
| PVC | 2,935.77 | 1,838.84 |

#### Paper and Board
| Material | Primary (kg CO2e/tonne) | Closed-loop |
|----------|------------------------|-------------|
| Board | 1,193.97 | 1,092.35 |
| Mixed | 1,282.74 | 1,063.02 |
| Paper | 1,339.32 | 1,044.32 |

#### Organic
| Material | Primary (kg CO2e/tonne) |
|----------|------------------------|
| Compost from garden waste | 112.02 |
| Compost from food and garden waste | 114.83 |

---

### 2. Waste Disposal Sheet

**Purpose:** End-of-life emission factors (Scope 3 downstream)

**Structure:**
- Header row: 22-23
- Data rows: ~42
- Disposal method columns: Re-use | Open-loop | Closed-loop | Combustion | Composting | Landfill | Anaerobic digestion

**Disposal Method Emission Factors (kg CO2e/tonne):**

#### Construction Waste
| Waste Type | Open-loop | Closed-loop | Combustion | Landfill |
|------------|-----------|-------------|------------|----------|
| Aggregates | 0.98 | 0.98 | - | 1.23 |
| Asbestos | - | - | - | 5.91 |
| Asphalt | 0.98 | 0.98 | - | 1.23 |
| Bricks | 0.98 | - | - | 1.23 |
| Concrete | 0.98 | 0.98 | - | 1.23 |
| Insulation | - | 0.98 | - | 1.23 |
| Metals | - | 0.98 | - | 1.26 |
| Soils | - | 0.98 | - | 19.52 |
| Mineral oil | - | 6.41 | 6.41 | - |
| Plasterboard | - | 6.41 | - | 71.95 |
| Tyres | - | 6.41 | - | - |
| Wood | - | 6.41 | 6.41 | 925.24 |

#### Electrical Waste (WEEE)
| Waste Type | Open-loop | Combustion | Landfill |
|------------|-----------|------------|----------|
| WEEE - fridges and freezers | 6.41 | - | 8.88 |
| WEEE - large | 6.41 | 6.41 | 8.88 |
| WEEE - mixed | 6.41 | 6.41 | 8.88 |
| WEEE - small | 6.41 | 6.41 | 8.88 |
| Batteries | 6.41 | - | 8.88 |

#### Organic Waste
| Waste Type | Combustion | Composting | Landfill | AD |
|------------|------------|------------|----------|-----|
| Food and drink waste | 6.41 | 8.88 | 700.21 | 8.88 |
| Garden waste | 6.41 | 8.88 | 646.61 | 8.88 |
| Mixed food and garden | 6.41 | 8.88 | 655.99 | 8.88 |

#### Paper/Plastic/Metal Waste
| Waste Type | Closed-loop | Combustion | Landfill |
|------------|-------------|------------|----------|
| Books | 6.41 | 6.41 | 1,164.39 |
| Paper and board (all) | 6.41 | 6.41 | 1,164.39 |
| Plastics (all types) | 6.41 | 6.41 | 8.88 |
| Metal (all types) | 6.41 | 6.41 | 8.88 |
| Glass | 6.41 | 6.41 | 8.88 |
| Clothing | 6.41 | 6.41 | 496.68 |

---

### 3. Freighting Goods Sheet

**Purpose:** Freight transport emission factors

**Structure:**
- Multiple data tables for different transport modes
- Units: tonne.km, km, miles

**Transport Modes:**

#### Road Freight - Vans
| Vehicle Type | Unit | kg CO2e |
|--------------|------|---------|
| Class I (up to 1.305 tonnes) | tonne.km | 0.8535 |
| Class I (up to 1.305 tonnes) | km | 0.1536 |
| Class II (1.305 to 1.74 tonnes) | tonne.km | 0.6115 |
| Class II (1.305 to 1.74 tonnes) | km | 0.1883 |
| Class III (1.74 to 3.5 tonnes) | tonne.km | 0.6136 |
| Class III (1.74 to 3.5 tonnes) | km | 0.2737 |
| Average (up to 3.5 tonnes) | tonne.km | 0.6164 |
| Average (up to 3.5 tonnes) | km | 0.2502 |

#### Road Freight - HGV (Diesel)
| Vehicle Type | Unit | kg CO2e |
|--------------|------|---------|
| Rigid (>3.5 - 7.5 tonnes) | km | 0.4538 |
| Rigid (>7.5 - 17 tonnes) | km | 0.5443 |
| Rigid (>17 tonnes) | km | 0.7499 |
| All rigids | km | 0.6616 |
| Articulated (>3.5 - 33t) | km | 0.6156 |
| Articulated (>33t) | km | 0.6324 |
| All artics | km | 0.6316 |
| All HGVs | km | 0.6439 |

#### Road Freight - HGV Refrigerated
| Vehicle Type | Unit | kg CO2e |
|--------------|------|---------|
| Rigid (>3.5 - 7.5 tonnes) | km | 0.5403 |
| Rigid (>7.5 - 17 tonnes) | km | 0.6480 |
| Rigid (>17 tonnes) | km | 0.8925 |
| All rigids | km | 0.7876 |
| All artics | km | 0.7302 |
| All HGVs | km | 0.7535 |

#### Air Freight
| Route Type | Unit | kg CO2e |
|------------|------|---------|
| Domestic, to/from UK | tonne.km | 4.6734 |
| Short-haul, to/from UK | tonne.km | 1.6682 |
| Long-haul, to/from UK | tonne.km | 1.0990 |
| International, non-UK | tonne.km | 1.0990 |

#### Rail Freight
| Type | Unit | kg CO2e |
|------|------|---------|
| Freight train | tonne.km | 0.0278 |

#### Sea Freight - Tankers
| Vessel Type | Size | Unit | kg CO2e |
|-------------|------|------|---------|
| Crude tanker | 200,000+ dwt | tonne.km | 0.0029 |
| Products tanker | 60,000+ dwt | tonne.km | 0.0058 |
| Chemical tanker | 20,000+ dwt | tonne.km | 0.0085 |
| LNG tanker | 200,000+ m3 | tonne.km | 0.0094 |
| LPG tanker | 50,000+ m3 | tonne.km | 0.0091 |

#### Sea Freight - Cargo Ships
| Vessel Type | Size | Unit | kg CO2e |
|-------------|------|------|---------|
| Bulk carrier | 200,000+ dwt | tonne.km | 0.0025 |
| General cargo | 10,000+ dwt | tonne.km | 0.0120 |
| Refrigerated cargo | All dwt | tonne.km | 0.0131 |
| Container ship | Various | tonne.km | varies |

---

### 4. Water Supply Sheet

**Structure:**
- Header row: 17
- Data rows: 2

| Activity | Unit | kg CO2e |
|----------|------|---------|
| Water supply | cubic metres | 0.15311 |
| Water supply | million litres | 153.10865 |

---

### 5. Water Treatment Sheet

**Structure:**
- Header row: 16
- Data rows: 2

| Activity | Unit | kg CO2e |
|----------|------|---------|
| Water treatment | cubic metres | 0.18574 |
| Water treatment | million litres | 185.74120 |

---

### 6. UK Electricity Sheet

**Structure:**
- Header row: 24
- Data rows: 1

| Activity | Unit | Year | kg CO2e |
|----------|------|------|---------|
| Electricity: UK | kWh | 2024 | 0.20705 |

---

### 7. Fuels Sheet

**Purpose:** Stationary and mobile combustion emission factors

**Structure:**
- Header row: 22
- Data rows: 117
- Units: tonnes, litres, kWh (Net CV), kWh (Gross CV)

**Sample Fuel Factors:**

#### Gaseous Fuels
| Fuel | Unit | kg CO2e |
|------|------|---------|
| Natural gas | kWh (Gross CV) | 0.1829 |
| Natural gas | cubic metres | 2.0454 |
| LPG | kWh (Gross CV) | 0.2145 |
| LPG | litres | 1.5571 |
| CNG | kWh (Gross CV) | 0.1829 |
| LNG | kWh (Gross CV) | 0.1845 |
| Butane | kWh (Gross CV) | 0.2224 |

#### Liquid Fuels
| Fuel | Unit | kg CO2e |
|------|------|---------|
| Diesel (average biofuel blend) | litres | 2.5121 |
| Petrol (average biofuel blend) | litres | 2.1947 |
| Fuel oil | litres | 3.0880 |
| Gas oil | litres | 2.7563 |
| Aviation turbine fuel | litres | 2.5468 |

---

## Data Quality Notes

1. **Units**: All material/waste factors are in kg CO2e per tonne unless otherwise specified
2. **Geography**: UK-specific factors; use "Overseas electricity" sheet for international operations
3. **Lifecycle**: Material factors cover cradle-to-gate; waste factors cover end-of-life only
4. **WTT Factors**: "Well-to-Tank" sheets provide upstream supply chain emissions (Scope 3)
5. **SECR**: Streamlined Energy and Carbon Reporting factors for UK regulatory compliance

## Recommended Parsing Strategy

1. **Material Use**: Parse by Activity category, extract all lifecycle stage columns
2. **Waste Disposal**: Parse disposal method columns (4-10), track multiple factors per waste type
3. **Freighting Goods**: Handle multiple tables, track current Activity/Type context
4. **Water/Electricity**: Simple key-value extraction

## Integration Notes for PCF Calculator

- **Primary use**: Material use factors for BOM component emissions
- **Secondary use**: Transport factors for logistics emissions
- **Tertiary use**: Waste disposal for end-of-life modeling
- **Scope mapping**: Material use = Scope 3 upstream; Waste = Scope 3 downstream; Transport = varies
