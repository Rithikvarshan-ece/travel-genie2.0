"""
TravelGenie Backend - FastAPI Application
Main entry point for the backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# from .routes import router as sync_router  # Old v1 routes - deprecated
from .async_routes import router as async_router
from ..database.database import init_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TravelGenie API",
    description="Agentic AI Budget Travel Planner - Multi-Agent System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (v2 only - new async agent system)
app.include_router(async_router)


@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    logger.info("Starting TravelGenie Backend...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error Database initialization failed: {e}")
    
    logger.info("✨ TravelGenie API v2.0 is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 TravelGenie Backend shutting down...")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

