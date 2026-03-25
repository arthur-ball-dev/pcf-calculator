# Product Carbon Footprint (PCF) Calculator

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://pcf.glideslopeintelligence.ai/)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-blue)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Live Demo:** [pcf.glideslopeintelligence.ai](https://pcf.glideslopeintelligence.ai/)
>
> *Last synced: 2026-03-25 | Version: v2.0.0*

Professional carbon footprint calculator implementing ISO 14067 and GHG Protocol for cradle-to-gate emissions analysis.

---

## Features

**Core Workflow:**
- 3-step wizard: Product Selection -> BOM Editor -> Results
- 817 products (production) / 13 demo products (test mode) with complete BOMs (materials, energy, transport)
- Searchable product selector with BOM filter toggle
- Real-time BOM editor with validation

**Visualizations:**
- Interactive Sankey diagram with **click-to-drill-down** (expand categories to see individual items)
- Expandable breakdown table with item-level emissions
- Export to CSV/Excel
- Scenario comparison with delta visualization

**Tech Stack:**
- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Brightway2
- **Frontend**: React 19, TypeScript, Vite, shadcn/ui, Zustand, Nivo
- **Database**: PostgreSQL 16 (Railway)

> **Note:** The production deployment uses real emission factor data — 342 emission factors from EPA GHG Hub 2024 and DEFRA 2024. Test mode uses simplified emission factors for development.

---

## Quick Start

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload  # http://localhost:8000

# Frontend
cd frontend
npm install && npm run dev  # http://localhost:5173
```

---

## Architecture

```
+-------------+     REST API      +--------------+
|   React     | <---------------> |   FastAPI    |
|  Frontend   |                   |   Backend    |
+-------------+                   +--------------+
       |                                  |
   Zustand                          SQLAlchemy
   Nivo Sankey                      Brightway2
```

**API Endpoints:**
- `GET /api/v1/products?has_bom=true` - List products (filterable)
- `POST /api/v1/calculate` - Submit calculation
- `GET /api/v1/calculations/{id}` - Get results with breakdown

---

## Calculation Method

```
Total CO2e = Sum (Component Quantity x Emission Factor)
```

**Categories:** Materials, Energy, Transport
**Sources:** EPA, DEFRA
**Accuracy:** Validated to <2% error

---

## Recent Updates (v1.4.0)

- **3-Step Wizard**: Merged Calculate into BOM Editor for streamlined workflow
- **Scenario Comparison**: Create, clone, and compare calculations with delta visualization
- **CSV/Excel Export**: Multi-sheet workbook export with full calculation details
- **JWT Authentication**: Secure API access with token-based auth
- **Visual E2E Testing**: Playwright-based end-to-end test coverage
- **Ecoinvent Removed**: Cleaned out commercial-license dependency
- **Code Review Fixes**: 18 items resolved from comprehensive code review

**Previous (v1.3.0):**
- PostgreSQL Migration: Upgraded from SQLite to PostgreSQL 16 for production
- Railway PostgreSQL: Auto-configured database with connection pooling
- Database URL Normalization: Handles Railway's `postgres://` URL format
- Data Source Cleanup: Removed Exiobase (academic license)

**Previous (v1.2.0):**
- Expanded demo products from 3 to 13 with complete BOMs (electronics, apparel, accessories, home goods)
- Fixed NumPy 2.0 compatibility for Brightway2 LCA engine
- Added async database support with lazy initialization
- Streamlined Nixpacks deployment configuration

**Previous (v1.1.0):**
- Added BOM filter toggle in product selector
- Implemented in-chart Sankey drill-down
- Added expandable items in breakdown table
- Searchable product selector with Command palette

---

## Roadmap

**Completed in Phase 9:**
- Test stabilization and production readiness
- Connection pool optimization
- License compliance cleanup
- User authentication (JWT)
- Scenario comparison with delta visualization

**Future:**
- CSV/Excel import
- Multi-user collaboration
- API integrations
- Supply chain data connectors

---

## License

MIT License

---

**Contact:** [linkedin.com/in/arthur-ball](https://www.linkedin.com/in/arthur-ball/)

*Built with FastAPI, React, and Brightway2*
