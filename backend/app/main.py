"""
CodeGuard AI - FastAPI Application Entry Point
==============================================
Initializes the application, configures CORS, handles lifecycle events,
and mounts API routers.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import CORS_ORIGINS
from app.database.session import init_db

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codeguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Runs setup logic before application starts accepting requests,
    and cleanup logic when shutting down.
    """
    logger.info("Initializing CodeGuard AI Backend...")
    # Initialize SQLite database schema
    init_db()
    yield
    logger.info("CodeGuard AI Backend shutting down.")


app = FastAPI(
    title="CodeGuard AI API",
    description="AI-powered Python code review, bug detection, and security analysis engine.",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) Middleware
# Essential so the React frontend running on localhost:5173 can query the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root_status():
    """Root endpoint welcoming developers and linking to API documentation."""
    return {
        "name": "CodeGuard AI",
        "description": "Python Code Quality & Security Static Analysis Service",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
