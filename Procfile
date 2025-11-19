# Procfile - Railway Startup Commands
# Place this file in the root of your repository
# Railway uses this to determine how to start your application

# Web service - runs the FastAPI backend
# Railway provides $PORT automatically
web: cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT

# Release phase - runs before web service starts
# Runs database migrations and seeds initial data
release: cd backend && python3 -m alembic upgrade head && python3 scripts/seed_data.py
