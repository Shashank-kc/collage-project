"""
CodeGuard AI - FastAPI Application Entry Point
==============================================
Initializes the application, configures CORS and security middlewares,
registers global exception handlers, and mounts API routers.
"""

from contextlib import asynccontextmanager
import logging
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth_routes import router as auth_router
from app.api.assistant_routes import router as assistant_router
from app.api.routes import router as api_router
from app.config import CORS_ORIGINS
from app.database.session import init_db
from app.middleware.security import RateLimitingMiddleware, SecurityHeadersMiddleware

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codeguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Runs schema migrations on startup, and cleanup on shutdown.
    """
    logger.info("Starting CodeGuard AI Backend v2.1...")
    init_db()
    yield
    logger.info("CodeGuard AI Backend shutdown complete.")


app = FastAPI(
    title="CodeGuard AI API",
    description="Production-grade Python static code analysis & security review engine with OpenAI Assistant.",
    version="2.1.0",
    lifespan=lifespan
)

# 1. In-memory Rate Limiting Middleware (prevents DoS/subprocess exhaustion)
app.add_middleware(RateLimitingMiddleware)

# 2. OWASP Security Headers Middleware (prevents clickjacking, MIME sniffing, XSS)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Cross-Origin Resource Sharing (CORS) Middleware with strict origins and cookie credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Cookie", "Accept"],
)

# Mount API routers
app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(api_router)


# Global Exception Handler to avoid leaking internal stack traces or filesystem paths
@app.exception_handler(Exception)
async def global_sanitized_exception_handler(request: Request, exc: Exception):
    error_id = uuid.uuid4().hex[:12]
    logger.error("Unhandled internal exception [ErrorID: %s]: %s", error_id, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing the request.",
            "error_id": error_id
        }
    )


@app.get("/", tags=["Root"])
def root_status():
    """Root endpoint welcoming developers and linking to API documentation."""
    return {
        "name": "CodeGuard AI",
        "description": "Python Code Quality & Security Static Analysis Service",
        "version": "1.1.0",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
