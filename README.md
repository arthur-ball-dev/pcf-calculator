# Product Carbon Footprint Calculator

Calculate cradle-to-gate carbon emissions for products using Bill of Materials (BOM) data and emission factors from EPA, DEFRA, and Ecoinvent.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, SQLite, React (planned)

**Project Status:** ✅ Phase 2 Complete - Backend API Ready | ⏸️ Phase 3 Paused (Awaiting Authorization)

## Project Milestones

- ✅ **Phase 0 (Complete):** Project setup and architecture review
- ✅ **Phase 1 (Complete):** Database foundation and data pipeline (312/312 tests passing, 100% TDD)
- ✅ **Phase 2 (Complete):** Calculation engine and RESTful API (524/546 tests passing, 95.97% pass rate)
  - Brightway2 calculation engine with exceptional accuracy (0.17%-1.94% error)
  - 7 RESTful endpoints with full OpenAPI documentation
  - Async background task processing
  - 15 Pydantic validation models
- ⏸️ **Phase 3 (Pending):** Frontend development (React + TypeScript) - Awaiting user authorization
- ⏳ **Phase 4 (Pending):** Integration testing and MVP finalization

## Quick Start

### 1. Initial Setup

```bash
# Run setup script (installs dependencies + configures development automation)
./setup.sh
```

This will:
- Create virtual environment at project root (`.venv/`)
- Install Python dependencies from `backend/requirements.txt`
- Run database migrations
- Load seed data (products, BOMs, emission factors)
- Generate `settings.local.json` with absolute paths for your machine

### 2. Activate Virtual Environment

```bash
# From project root
source .venv/bin/activate
```

### 3. Run Tests (recommended)

```bash
# From backend directory
cd backend
pytest

# Expected: 550+ tests collected
```

### 4. Start API Server

```bash
# From backend directory
cd backend

# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or production mode
python main.py
```

**API Documentation:** http://localhost:8000/docs (Swagger UI)

## API Endpoints (Phase 2 Complete)

### Products
- `GET /api/v1/products` - List products with pagination
- `GET /api/v1/products/{id}` - Get product detail with BOM

### Calculations
- `POST /api/v1/calculate` - Submit async calculation (returns 202 + calculation_id)
- `GET /api/v1/calculations/{id}` - Get calculation status and results

### Emission Factors
- `GET /api/v1/emission-factors` - List emission factors with filtering
- `POST /api/v1/emission-factors` - Create custom emission factor

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /openapi.json` - OpenAPI 3.0 specification

## Calculation Accuracy

Phase 2 validation confirmed exceptional calculation accuracy:

| Product | Expected | Actual | Error |
|---------|----------|--------|-------|
| T-shirt | 2.05 kg CO2e | 2.0465 kg CO2e | **0.17%** ✅ |
| Water Bottle | 0.157 kg CO2e | 0.1566 kg CO2e | **0.25%** ✅ |
| Phone Case | 0.343 kg CO2e | 0.3497 kg CO2e | **1.94%** ✅ |

All within ±5% tolerance (target met with exceptional results).

## Claude Code Hooks

This project uses development automation for development workflow automation. The setup script automatically configures hooks with absolute paths.

**Why absolute paths?** Hooks with relative paths fail when you `cd backend` or work in subdirectories. Absolute paths ensure hooks work regardless of current working directory.

- **Template:** `settings.example.json` (tracked in git, uses `$PWD` placeholder)
- **Generated:** `settings.local.json` (gitignored, has your actual paths)

To regenerate settings after moving the project:
```bash
python3 scripts/init-claude.py
```

## Project Documentation

See `CLAUDE.md` for comprehensive development documentation including:
- Architecture and database schema
- API specifications
- Development commands
- Testing guidelines
- Project management workflow

## Testing Philosophy

This project follows **Test-Driven Development (TDD)**:
- 100% TDD compliance across all phases (22/22 tasks)
- Tests written before implementation
- No test modifications after implementation
- 550+ tests, >95% pass rate
- Zero critical or major bugs

## Quality Metrics (Phase 0-2)

- **Test Pass Rate:** >95% (550+ tests)
- **TDD Compliance:** 100% (22/22 tasks)
- **First-Pass Code Review Approval:** 91% (20/22 tasks)
- **Calculation Accuracy:** 0.17%-1.94% error (exceptional)
- **Technical Debt:** Zero (critical/high priority)
- **Open Bugs:** 0 (P0/P1/P2)

## Development Standards

- **TDD:** Tests written before implementation (enforced via git hooks)
- **Code Review:** Peer review required for all tasks
- **Code Coverage:** >80% target (currently: 95.97% backend)
- **Python Style:** PEP 8, type hints, docstrings
- **Commit Convention:** Conventional Commits format

## License

[Add license information here]

## Contributing

[Add contributing guidelines here]
