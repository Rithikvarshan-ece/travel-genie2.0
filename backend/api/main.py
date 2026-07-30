"""
TravelGenie Backend - FastAPI Application
Main entry point for the backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# from .routes import router as sync_router  # Old v1 routes - deprecated
from .async_routes import router as async_router
from .auth_routes import router as auth_router
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
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """Initialize the database and verify all connections on startup."""
    logger.info("Starting TravelGenie Backend...")

    # SQLite init
    try:
        init_db()
        logger.info("SQLite database initialized successfully")
    except Exception as e:
        logger.error(f"SQLite initialization failed: {e}")

    # MongoDB connectivity check
    from backend.config import get_settings
    settings = get_settings()
    if settings.mongodb_url:
        try:
            from pymongo import MongoClient
            client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
            )
            result = client.admin.command("ping")
            client.close()
            logger.info(f"MongoDB Atlas ping OK: {result}")
        except Exception as e:
            logger.warning(
                f"MongoDB Atlas unreachable: {e}. "
                "Check that IP 103.183.240.250 is whitelisted in Atlas Network Access. "
                "Cache will use SQLite fallback."
            )
    else:
        logger.info("MONGODB_URL not set — using SQLite cache fallback")

    logger.info("\u2728 TravelGenie API v2.0 is ready!")


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

