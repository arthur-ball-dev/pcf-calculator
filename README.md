# Product Carbon Footprint (PCF) Calculator

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://pcf.glideslopeintelligence.ai/)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-blue)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Live Demo:** [pcf.glideslopeintelligence.ai](https://pcf.glideslopeintelligence.ai/)
>
> *Last synced: 2025-12-16 | Version: v1.2.0 (Phase 7)*

Professional carbon footprint calculator implementing ISO 14067 and GHG Protocol for cradle-to-gate emissions analysis.

---

## Features

**Core Workflow:**
- 4-step wizard: Product Selection → Edit Bill of Materials → Calculate → Results
- 13 demo products with complete BOMs (materials, energy, transport)
- Searchable product selector with BOM filter toggle
- Real-time BOM editor with validation

**Visualizations:**
- Interactive Sankey diagram with **click-to-drill-down** (expand categories to see individual items)
- Expandable breakdown table with item-level emissions
- Export to CSV/Excel

**Tech Stack:**
- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Brightway2
- **Frontend**: React 19, TypeScript, Vite, shadcn/ui, Zustand, Nivo
- **Database**: SQLite (MVP)

> **Note:** This demo uses sample test data (products, BOMs, and simplified emission factors) to demonstrate the calculation workflow. Production deployments would integrate real emission factor databases (EPA USEEIO, DEFRA, Ecoinvent).

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
┌─────────────┐     REST API      ┌──────────────┐
│   React     │ ←──────────────→  │   FastAPI    │
│  Frontend   │                   │   Backend    │
└─────────────┘                   └──────────────┘
       ↓                                  ↓
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
Total CO₂e = Σ (Component Quantity × Emission Factor)
```

**Categories:** Materials, Energy, Transport
**Sources:** EPA, DEFRA, Ecoinvent
**Accuracy:** Validated to <2% error

---

## Recent Updates (v1.2.0)

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

**Phase 8 (Next):**
- PostgreSQL Docker infrastructure
- Data migration tooling

**Future:**
- User authentication
- CSV/Excel import
- Scenario comparison
- API integrations

---

## License

MIT License

---

**Contact:** [linkedin.com/in/arthur-ball](https://www.linkedin.com/in/arthur-ball/)

*Built with FastAPI, React, and Brightway2*