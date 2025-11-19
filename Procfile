# Procfile - Railway Startup Commands
# Place this file in the root of your repository
# Railway uses this to determine how to start your application

# Web service - runs the FastAPI backend
# Railway provides $PORT automatically
web: cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT

# Release phase - runs before web service starts
# Seeds the database with initial data
release: cd backend && python3 seed_data.py
