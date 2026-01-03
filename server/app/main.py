from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db import init_db, close_db
from app.blob_store import init_blob_store
from app.ingest import router as ingest_router
from app.routes import router as query_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_blob_store()
    await init_db()
    yield
    await close_db()

app = FastAPI(
    title="X-Ray Observability API",
    description="Debug multi-step ML/LLM pipelines by capturing decision context",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(query_router, tags=["query"])

@app.get("/health")
async def health():
    return {"status": "ok"}

