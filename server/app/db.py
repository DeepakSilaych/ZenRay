"""
Database operations for ZenRay.

Uses asyncpg for async PostgreSQL access.
"""
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg

from app.config import get_settings

logger = logging.getLogger("zenray.db")

_pool: Optional[asyncpg.Pool] = None


# =============================================================================
# Connection Management
# =============================================================================

async def init_db():
    """Initialize PostgreSQL connection pool and create tables."""
    global _pool
    settings = get_settings()
    
    _pool = await asyncpg.create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
        min_size=5,
        max_size=20,
    )
    
    await _create_tables()
    logger.info("Database pool initialized")


async def _create_tables():
    """Create database tables if they don't exist."""
    async with _pool.acquire() as conn:
        await conn.execute("""
            -- Runs table
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                pipeline_name TEXT NOT NULL,
                version TEXT,
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                ended_at TIMESTAMPTZ,
                tags JSONB,
                input_summary JSONB,
                final_output JSONB
            );
            
            -- Steps table
            CREATE TABLE IF NOT EXISTS steps (
                step_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                parent_step_id TEXT,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                input_count INTEGER,
                output_count INTEGER,
                status TEXT NOT NULL,
                duration_ms INTEGER,
                started_at TIMESTAMPTZ,
                ended_at TIMESTAMPTZ,
                metrics JSONB,
                candidate_set_ref TEXT
            );
            
            -- Artifacts table
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                step_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                type TEXT NOT NULL,
                blob_ref TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                picture TEXT,
                google_id TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            -- API keys table
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                key_name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                last_used_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id);
            CREATE INDEX IF NOT EXISTS idx_runs_pipeline ON runs(pipeline_name);
            CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
            CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_steps_run ON steps(run_id);
            CREATE INDEX IF NOT EXISTS idx_steps_kind ON steps(kind);
            CREATE INDEX IF NOT EXISTS idx_artifacts_step ON artifacts(step_id);
            CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
        """)


async def close_db():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> asyncpg.Pool:
    """Get the database connection pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a connection from the pool."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


# =============================================================================
# Run Operations
# =============================================================================

async def upsert_run(run: dict):
    """Insert or update a run."""
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO runs (
                run_id, user_id, pipeline_name, version, status,
                started_at, ended_at, tags, input_summary, final_output
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT(run_id) DO UPDATE SET
                pipeline_name = EXCLUDED.pipeline_name,
                version = EXCLUDED.version,
                status = EXCLUDED.status,
                ended_at = COALESCE(EXCLUDED.ended_at, runs.ended_at),
                tags = EXCLUDED.tags,
                input_summary = EXCLUDED.input_summary,
                final_output = COALESCE(EXCLUDED.final_output, runs.final_output)
            """,
            run["run_id"],
            run["user_id"],
            run["pipeline_name"],
            run.get("version"),
            run["status"],
            run["started_at"],
            run.get("ended_at"),
            json.dumps(run.get("tags")) if run.get("tags") else None,
            json.dumps(run.get("input_summary")) if run.get("input_summary") else None,
            json.dumps(run.get("final_output")) if run.get("final_output") else None,
        )


async def get_run(run_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a run by ID, optionally filtered by user."""
    async with get_connection() as conn:
        if user_id:
            row = await conn.fetchrow(
                "SELECT * FROM runs WHERE run_id = $1 AND user_id = $2",
                run_id, user_id
            )
        else:
            row = await conn.fetchrow(
                "SELECT * FROM runs WHERE run_id = $1",
                run_id
            )
        return _row_to_run(row) if row else None


async def search_runs(
    user_id: str,
    pipeline_name: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[dict] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Search runs with filters."""
    async with get_connection() as conn:
        query = "SELECT * FROM runs WHERE user_id = $1"
        params: list = [user_id]
        idx = 2
        
        if pipeline_name:
            query += f" AND pipeline_name = ${idx}"
            params.append(pipeline_name)
            idx += 1
        if status:
            query += f" AND status = ${idx}"
            params.append(status)
            idx += 1
        if start_time:
            query += f" AND started_at >= ${idx}"
            params.append(start_time)
            idx += 1
        if end_time:
            query += f" AND started_at <= ${idx}"
            params.append(end_time)
            idx += 1
        if tags:
            query += f" AND tags @> ${idx}"
            params.append(json.dumps(tags))
            idx += 1
        
        query += f" ORDER BY started_at DESC LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        return [_row_to_run(r) for r in rows]


def _row_to_run(row) -> dict:
    """Convert database row to run dict."""
    return {
        "run_id": row["run_id"],
        "user_id": row["user_id"],
        "pipeline_name": row["pipeline_name"],
        "version": row["version"],
        "status": row["status"],
        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "tags": json.loads(row["tags"]) if row["tags"] else None,
        "input_summary": json.loads(row["input_summary"]) if row["input_summary"] else None,
        "final_output": json.loads(row["final_output"]) if row["final_output"] else None,
    }


# =============================================================================
# Step Operations
# =============================================================================

async def upsert_step(step: dict):
    """Insert or update a step."""
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO steps (
                step_id, run_id, parent_step_id, kind, name, input_count,
                output_count, status, duration_ms, started_at, ended_at,
                metrics, candidate_set_ref
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT(step_id) DO UPDATE SET
                kind = EXCLUDED.kind,
                name = EXCLUDED.name,
                input_count = COALESCE(EXCLUDED.input_count, steps.input_count),
                output_count = COALESCE(EXCLUDED.output_count, steps.output_count),
                status = EXCLUDED.status,
                duration_ms = COALESCE(EXCLUDED.duration_ms, steps.duration_ms),
                ended_at = COALESCE(EXCLUDED.ended_at, steps.ended_at),
                metrics = EXCLUDED.metrics,
                candidate_set_ref = COALESCE(EXCLUDED.candidate_set_ref, steps.candidate_set_ref)
            """,
            step["step_id"],
            step["run_id"],
            step.get("parent_step_id"),
            step["kind"],
            step["name"],
            step.get("input_count"),
            step.get("output_count"),
            step["status"],
            step.get("duration_ms"),
            step.get("started_at"),
            step.get("ended_at"),
            json.dumps(step.get("metrics")) if step.get("metrics") else None,
            step.get("candidate_set_ref"),
        )


async def get_step(step_id: str) -> Optional[dict]:
    """Get a step by ID."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM steps WHERE step_id = $1",
            step_id
        )
        return _row_to_step(row) if row else None


async def get_steps_for_run(run_id: str) -> list[dict]:
    """Get all steps for a run."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM steps WHERE run_id = $1 ORDER BY started_at ASC",
            run_id
        )
        return [_row_to_step(r) for r in rows]


async def search_steps(
    kind: Optional[str] = None,
    run_id: Optional[str] = None,
    user_id: Optional[str] = None,
    min_drop_ratio: Optional[float] = None,
    max_drop_ratio: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Search steps with filters."""
    async with get_connection() as conn:
        query = "SELECT s.* FROM steps s JOIN runs r ON s.run_id = r.run_id WHERE 1=1"
        params: list = []
        idx = 1
        
        if user_id:
            query += f" AND r.user_id = ${idx}"
            params.append(user_id)
            idx += 1
        if kind:
            query += f" AND s.kind = ${idx}"
            params.append(kind)
            idx += 1
        if run_id:
            query += f" AND s.run_id = ${idx}"
            params.append(run_id)
            idx += 1
        if min_drop_ratio is not None:
            query += f" AND s.input_count > 0 AND (1.0 - s.output_count::float / s.input_count::float) >= ${idx}"
            params.append(min_drop_ratio)
            idx += 1
        if max_drop_ratio is not None:
            query += f" AND s.input_count > 0 AND (1.0 - s.output_count::float / s.input_count::float) <= ${idx}"
            params.append(max_drop_ratio)
            idx += 1
        
        query += f" LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        return [_row_to_step(r) for r in rows]


async def count_steps_for_run(run_id: str) -> int:
    """Count steps in a run."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM steps WHERE run_id = $1",
            run_id
        )
        return row["count"] if row else 0


def _row_to_step(row) -> dict:
    """Convert database row to step dict."""
    return {
        "step_id": row["step_id"],
        "run_id": row["run_id"],
        "parent_step_id": row["parent_step_id"],
        "kind": row["kind"],
        "name": row["name"],
        "input_count": row["input_count"],
        "output_count": row["output_count"],
        "status": row["status"],
        "duration_ms": row["duration_ms"],
        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "metrics": json.loads(row["metrics"]) if row["metrics"] else None,
        "candidate_set_ref": row["candidate_set_ref"],
    }


# =============================================================================
# Artifact Operations
# =============================================================================

async def index_artifact(
    artifact_id: str,
    step_id: str,
    run_id: str,
    artifact_type: str,
    blob_ref: str,
):
    """Index an artifact in the database."""
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO artifacts (artifact_id, step_id, run_id, type, blob_ref)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT(artifact_id) DO UPDATE SET blob_ref = EXCLUDED.blob_ref
            """,
            artifact_id, step_id, run_id, artifact_type, blob_ref
        )


async def get_artifacts_for_step(step_id: str) -> list[dict]:
    """Get all artifacts for a step."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM artifacts WHERE step_id = $1 ORDER BY created_at",
            step_id
        )
        return [dict(r) for r in rows]
