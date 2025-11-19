# Procfile - Railway Startup Commands
# Place this file in the root of your repository
# Railway uses this to determine how to start your application

# Web service - runs the FastAPI backend
# Railway provides $PORT automatically
web: PYTHONPATH=/app python3 -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT

# Release phase - runs before web service starts
# Runs database migrations, seeds initial data, and initializes Brightway2
# All commands run from /app root for consistent database location
release: PYTHONPATH=/app python3 -m alembic -c backend/alembic.ini upgrade head && PYTHONPATH=/app python3 backend/scripts/seed_data.py && PYTHONPATH=/app python3 backend/scripts/init_brightway.py
