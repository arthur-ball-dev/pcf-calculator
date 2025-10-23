"""
FastAPI application entry point
PCF Calculator MVP - Product Carbon Footprint Calculator
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# Initialize FastAPI application
app = FastAPI(
    title="PCF Calculator API",
    version="1.0.0",
    description="Product Carbon Footprint Calculator MVP"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        dict: Status and version information
    """
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
