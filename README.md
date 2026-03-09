
# Product Carbon Footprint Calculator

Calculate cradle-to-gate carbon emissions for products using Bill of Materials (BOM) data and emission factors from EPA and DEFRA. Implements ISO 14067 and GHG Protocol standards.

## Tech Stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0, Brightway2 LCA, PostgreSQL

**Frontend:** React 19, TypeScript, Vite, Zustand, TanStack Query, shadcn/ui, Nivo charts, Playwright

**Project Status:** Phase 9 - Final MVP Validation

## Project Milestones

- **Phase 0 (Complete):** Project setup and architecture review
- **Phase 1 (Complete):** Database foundation and data pipeline
- **Phase 2 (Complete):** Calculation engine and RESTful API
- **Phase 3 (Complete):** Frontend development (React + TypeScript)
- **Phase 4 (Complete):** Integration testing and MVP core
- **Phase 5 (Complete):** MVP feature completion and polish
- **Phase 6 (Complete):** Deployment and CI/CD pipeline
- **Phase 7 (Complete):** Production hardening, data quality, and documentation
- **Phase 8 (Complete):** Performance optimization and caching
- **Phase 9 (In Progress):** Final MVP validation and documentation

## Quick Start

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
cd backend && alembic upgrade head

# Seed data
python scripts/seed_data.py

# Start API server (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:** http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run unit tests
npm test

# Run E2E tests (requires backend running)
npm run test:e2e
```

**Application:** http://localhost:5173

## Features

### Calculator Wizard
- **Product Selection:** Search and select products from the catalog
- **BOM Editor:** View and modify Bill of Materials with quantity adjustments
- **Results Display:** Interactive visualization of carbon footprint breakdown

### Visualizations
- **Sankey Diagram:** Material flow visualization showing emission sources
- **Category Breakdown:** Detailed emissions by material, energy, and transport
- **Export Options:** CSV and Excel data export

### Data Management
- **Emission Factors:** EPA and DEFRA databases
- **Product Catalog:** Pre-loaded products with complete BOMs
- **Scenario Comparison:** Create, clone, and compare calculations with delta visualization

## API Endpoints

### Products
- `GET /api/v1/products` - List products with pagination and filtering
- `GET /api/v1/products/{id}` - Get product detail with BOM

### Calculations
- `POST /api/v1/calculate` - Submit async calculation (returns 202)
- `GET /api/v1/calculations/{id}` - Get calculation status and results

### Emission Factors
- `GET /api/v1/emission-factors` - List emission factors with filtering
- `POST /api/v1/emission-factors` - Create custom emission factor

### Data Sources
- `GET /api/v1/data-sources` - List available data sources with license info

## Calculation Accuracy

Validated against reference data with exceptional accuracy:

| Product      | Expected       | Actual          | Error      |
|--------------|----------------|-----------------|------------|
| T-shirt      | 2.05 kg CO2e   | 2.0465 kg CO2e  | **0.17%**  |
| Water Bottle | 0.157 kg CO2e  | 0.1566 kg CO2e  | **0.25%**  |
| Phone Case   | 0.343 kg CO2e  | 0.3497 kg CO2e  | **1.94%**  |

All within ±5% tolerance target.

## Testing

```bash
# Backend tests (from project root)
cd backend && pytest

# Frontend unit tests
cd frontend && npm test

# Frontend E2E tests
cd frontend && npm run test:e2e

# With coverage
cd backend && pytest --cov=backend --cov-report=html
cd frontend && npm test -- --coverage
```

**Test Coverage:**
- Backend: 96 test files
- Frontend: 77 unit test files + 5 E2E test suites
- Coverage target: >80%

## Development

See `CLAUDE.md` for comprehensive development documentation including:
- Architecture and database schema
- API specifications
- Development commands
- Testing guidelines
- TDD methodology

### Development Standards

- **TDD:** Tests written before implementation (enforced via git hooks)
- **Code Review:** Peer review required for all tasks
- **Python Style:** PEP 8, type hints, docstrings
- **TypeScript:** Strict mode, no `any` types
- **Commit Convention:** Conventional Commits format

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator
CORS_ORIGINS=http://localhost:5173
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow TDD: Write tests first, then implementation
4. Ensure all tests pass (`pytest` for backend, `npm test` for frontend)
5. Commit with conventional format (`feat:`, `fix:`, `test:`, etc.)
6. Open a Pull Request

See `CLAUDE.md` for detailed development guidelines.
