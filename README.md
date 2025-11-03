# Product Carbon Footprint Calculator

Calculate cradle-to-gate carbon emissions for products using Bill of Materials (BOM) data and emission factors from EPA, DEFRA, and Ecoinvent.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, SQLite, React (planned)

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
