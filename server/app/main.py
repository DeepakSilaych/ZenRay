"""
ZenRay Server - Main FastAPI application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.db import init_db, close_db
from app.blob_store import init_blob_store
from app.cache import init_cache, close_cache
from app.worker import start_worker, stop_worker
from app.routers import ingest, query, auth

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zenray")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting ZenRay server...")
    
    # Initialize services
    init_blob_store()
    logger.info("✓ Blob store initialized")
    
    await init_db()
    logger.info("✓ Database initialized")
    
    await init_cache()
    logger.info("✓ Cache initialized")
    
    start_worker()
    logger.info("✓ Background worker started")
    
    logger.info(f"ZenRay server v{__version__} ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZenRay server...")
    
    await stop_worker(drain=True)
    logger.info("✓ Worker stopped")
    
    await close_cache()
    logger.info("✓ Cache closed")
    
    await close_db()
    logger.info("✓ Database closed")
    
    logger.info("ZenRay server stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ZenRay API",
        description="Observability layer for ML/LLM pipelines",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
    app.include_router(query.router, tags=["query"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    
    @app.get("/health", tags=["system"])
    async def health():
        """Health check endpoint."""
        from app import queue
        stats = await queue.get_queue_stats()
        return {
            "status": "healthy",
            "version": __version__,
            "queue_length": stats["queue_length"],
        }
    
    @app.get("/", tags=["system"])
    async def root():
        """Root endpoint."""
        return {
            "name": "ZenRay API",
            "version": __version__,
            "docs": "/docs" if settings.debug else "Disabled in production",
        }
    
    return app


# Create app instance
app = create_app()
