"""
Ingest API for ZenRay observability data.

Supports two modes:
- Async (default): Push to Redis queue for background processing
- Sync: Direct write to database (for testing or low-latency needs)

Authentication:
- Requires API key in Authorization header (Bearer token)
- All ingested data is associated with the API key's owner
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from app.models import IngestPayload
from app import queue
from app.auth import hash_api_key
from app.db import get_pool

router = APIRouter()
security = HTTPBearer()

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


class IngestResponse(BaseModel):
    accepted_runs: int = 0
    accepted_steps: int = 0
    queued: bool = False
    errors: list[str] = []


async def get_user_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate API key and return user info."""
    api_key = credentials.credentials
    key_hash = hash_api_key(api_key)
    
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.user_id, u.email
            FROM users u
            JOIN api_keys ak ON u.user_id = ak.user_id
            WHERE ak.key_hash = $1
            """,
            key_hash
        )
        
        if not row:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # Update last_used_at
        await conn.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE key_hash = $1",
            key_hash
        )
        
        return dict(row)


@router.post("", response_model=IngestResponse)
async def ingest(
    payload: IngestPayload,
    user: dict = Depends(get_user_from_api_key),
    sync: bool = Query(False, description="If true, write directly to DB instead of queuing"),
):
    """
    Batch ingest runs and steps.
    
    Requires API key authentication. All data is associated with the API key owner.
    
    By default, payloads are pushed to a Redis queue and processed
    asynchronously by a background worker. This provides:
    - Fast response times (~1ms)
    - Better throughput under load
    - Backpressure handling
    
    Set sync=true to write directly to the database (slower but immediate).
    """
    
    # Validate schema version
    if payload.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported schema version: {payload.schema_version}. Supported: {SUPPORTED_SCHEMA_VERSIONS}"
        )
    
    runs_count = len(payload.runs) if payload.runs else 0
    steps_count = len(payload.steps) if payload.steps else 0
    
    user_id = user["user_id"]
    
    if sync:
        # Synchronous mode: process immediately
        return await _process_sync(payload, user_id)
    
    # Async mode: push to queue with user_id
    try:
        # Convert to dict for queue
        payload_dict = payload.model_dump(mode='json')
        payload_dict["_user_id"] = user_id  # Add user_id for worker
        await queue.enqueue_ingest(payload_dict)
        
        return IngestResponse(
            accepted_runs=runs_count,
            accepted_steps=steps_count,
            queued=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to queue payload: {str(e)}"
        )


async def _process_sync(payload: IngestPayload, user_id: str) -> IngestResponse:
    """Process payload synchronously (direct DB write)."""
    from app import db, blob_store, cache
    
    response = IngestResponse()
    
    # Process runs
    if payload.runs:
        for run in payload.runs:
            try:
                run_dict = {
                    "run_id": run.run_id,
                    "user_id": user_id,
                    "pipeline_name": run.pipeline_name,
                    "version": run.version,
                    "status": run.status.value,
                    "started_at": run.started_at,
                    "ended_at": run.ended_at,
                    "tags": run.tags,
                    "input_summary": run.input_summary,
                    "final_output": run.final_output,
                }
                await db.upsert_run(run_dict)
                await cache.invalidate_run(run.run_id)
                response.accepted_runs += 1
            except Exception as e:
                response.errors.append(f"Run {run.run_id}: {str(e)}")
    
    # Process steps
    if payload.steps:
        for step in payload.steps:
            try:
                # Save candidate set
                candidate_set_ref = None
                if step.candidate_set:
                    candidate_set_dict = step.candidate_set.model_dump()
                    candidate_set_ref = await blob_store.save_candidate_set(step.step_id, candidate_set_dict)
                
                # Save artifacts
                if step.artifacts:
                    for artifact in step.artifacts:
                        blob_ref = await blob_store.save_artifact(artifact.artifact_id, {
                            "step_id": artifact.step_id,
                            "type": artifact.type.value,
                            "content": artifact.content,
                        })
                        await db.index_artifact(
                            artifact_id=artifact.artifact_id,
                            step_id=step.step_id,
                            run_id=step.run_id,
                            artifact_type=artifact.type.value,
                            blob_ref=blob_ref,
                        )
                
                # Store step
                step_dict = {
                    "step_id": step.step_id,
                    "run_id": step.run_id,
                    "parent_step_id": step.parent_step_id,
                    "kind": step.kind.value,
                    "name": step.name,
                    "input_count": step.input_count,
                    "output_count": step.output_count,
                    "status": step.status.value,
                    "duration_ms": step.duration_ms,
                    "started_at": step.started_at,
                    "ended_at": step.ended_at,
                    "metrics": step.metrics,
                    "candidate_set_ref": candidate_set_ref,
                }
                await db.upsert_step(step_dict)
                await cache.invalidate_step(step.step_id, step.run_id)
                response.accepted_steps += 1
            except Exception as e:
                response.errors.append(f"Step {step.step_id}: {str(e)}")
    
    return response


# --- Queue Stats Endpoint ---

@router.get("/stats")
async def get_ingest_stats():
    """Get ingest queue statistics."""
    stats = await queue.get_queue_stats()
    return {
        "queue": stats,
        "mode": "async",
        "worker": "running",
    }
