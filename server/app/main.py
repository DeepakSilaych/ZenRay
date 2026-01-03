import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db import init_db, close_db
from app.blob_store import init_blob_store
from app.cache import init_cache, close_cache
from app.worker import start_worker, stop_worker
from app.ingest import router as ingest_router
from app.routes import router as query_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    logger.info("Starting X-Ray server...")
    
    init_blob_store()
    logger.info("✓ Blob store (MinIO) initialized")
    
    await init_db()
    logger.info("✓ Database (PostgreSQL) initialized")
    
    await init_cache()
    logger.info("✓ Cache (Redis) initialized")
    
    # Start background worker for async ingestion
    start_worker()
    logger.info("✓ Background flush worker started")
    
    logger.info("X-Ray server ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down X-Ray server...")
    
    # Stop worker and drain queue
    await stop_worker(drain=True)
    logger.info("✓ Worker stopped, queue drained")
    
    await close_cache()
    logger.info("✓ Cache closed")
    
    await close_db()
    logger.info("✓ Database closed")
    
    logger.info("X-Ray server stopped")


app = FastAPI(
    title="X-Ray Observability API",
    description="Debug multi-step ML/LLM pipelines by capturing decision context",
    version="2.1.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(query_router, tags=["query"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    from app import queue
    
    stats = await queue.get_queue_stats()
    
    return {
        "status": "ok",
        "version": "2.1.0",
        "queue_length": stats["queue_length"],
    }
