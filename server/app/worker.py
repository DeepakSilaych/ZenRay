"""
Background worker for processing ingest queue.

Runs as an asyncio task, continuously polling the Redis queue
and writing batches to PostgreSQL/MinIO.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from app import queue, db, blob_store, cache

logger = logging.getLogger("zenray.worker")

# Configuration
BATCH_SIZE = 50
POLL_INTERVAL = 0.1  # seconds

_worker_task: Optional[asyncio.Task] = None
_shutdown = False


# =============================================================================
# Payload Processing
# =============================================================================

def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


async def process_payload(payload_data: dict):
    """Process a single ingest payload."""
    try:
        payload = payload_data.get("payload", payload_data)
        user_id = payload.get("_user_id")
        
        if not user_id:
            logger.error("Payload missing user_id, skipping")
            return
        
        runs_processed = 0
        steps_processed = 0
        
        # Process runs
        for run_data in payload.get("runs", []):
            await _process_run(run_data, user_id)
            runs_processed += 1
        
        # Process steps
        for step_data in payload.get("steps", []):
            await _process_step(step_data)
            steps_processed += 1
        
        await queue.record_processed(runs=runs_processed, steps=steps_processed)
        
    except Exception as e:
        logger.error(f"Error processing payload: {e}")
        await queue.record_error()
        raise


async def _process_run(run_data: dict, user_id: str):
    """Process and store a run."""
    run_dict = {
        "run_id": run_data["run_id"],
        "user_id": user_id,
        "pipeline_name": run_data["pipeline_name"],
        "version": run_data.get("version"),
        "status": run_data.get("status", "RUNNING"),
        "started_at": parse_datetime(run_data.get("started_at")),
        "ended_at": parse_datetime(run_data.get("ended_at")),
        "tags": run_data.get("tags"),
        "input_summary": run_data.get("input_summary"),
        "final_output": run_data.get("final_output"),
    }
    await db.upsert_run(run_dict)
    await cache.invalidate_run(run_data["run_id"])


async def _process_step(step_data: dict):
    """Process and store a step with candidate set and artifacts."""
    step_id = step_data["step_id"]
    run_id = step_data["run_id"]
    
    # Save candidate set
    candidate_set_ref = None
    candidate_set = step_data.get("candidate_set")
    if candidate_set:
        candidate_set_ref = await blob_store.save_candidate_set(step_id, candidate_set)
    
    # Save artifacts
    for artifact in step_data.get("artifacts", []):
        artifact_id = artifact.get("artifact_id")
        if artifact_id:
            blob_ref = await blob_store.save_artifact(artifact_id, {
                "step_id": step_id,
                "type": artifact.get("type", "unknown"),
                "content": artifact.get("content"),
            })
            await db.index_artifact(
                artifact_id=artifact_id,
                step_id=step_id,
                run_id=run_id,
                artifact_type=artifact.get("type", "unknown"),
                blob_ref=blob_ref,
            )
    
    # Store step
    step_dict = {
        "step_id": step_id,
        "run_id": run_id,
        "parent_step_id": step_data.get("parent_step_id"),
        "kind": step_data.get("kind", "TRANSFORM"),
        "name": step_data.get("name", "unknown"),
        "input_count": step_data.get("input_count"),
        "output_count": step_data.get("output_count"),
        "status": step_data.get("status", "RUNNING"),
        "duration_ms": step_data.get("duration_ms"),
        "started_at": parse_datetime(step_data.get("started_at")),
        "ended_at": parse_datetime(step_data.get("ended_at")),
        "metrics": step_data.get("metrics"),
        "candidate_set_ref": candidate_set_ref,
    }
    await db.upsert_step(step_dict)
    await cache.invalidate_step(step_id, run_id)


# =============================================================================
# Worker Lifecycle
# =============================================================================

async def flush_worker():
    """Background worker that processes the queue."""
    global _shutdown
    logger.info("Flush worker started")
    
    while not _shutdown:
        try:
            batch = await queue.dequeue_batch(BATCH_SIZE)
            
            if not batch:
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            for item in batch:
                try:
                    await process_payload(item)
                except Exception as e:
                    logger.error(f"Failed to process item: {e}")
            
            logger.debug(f"Flushed {len(batch)} payloads")
            
        except asyncio.CancelledError:
            logger.info("Flush worker cancelled")
            break
        except Exception as e:
            logger.error(f"Flush worker error: {e}")
            await asyncio.sleep(1.0)
    
    logger.info("Flush worker stopped")


async def drain_queue():
    """Drain remaining items from queue."""
    logger.info("Draining queue...")
    remaining = await queue.queue_length()
    
    while remaining > 0:
        batch = await queue.dequeue_batch(BATCH_SIZE)
        if not batch:
            break
        
        for item in batch:
            try:
                await process_payload(item)
            except Exception as e:
                logger.error(f"Failed to process during drain: {e}")
        
        remaining = await queue.queue_length()
        logger.info(f"Drained batch, {remaining} remaining")
    
    logger.info("Queue drained")


def start_worker() -> asyncio.Task:
    """Start the background worker."""
    global _worker_task, _shutdown
    _shutdown = False
    _worker_task = asyncio.create_task(flush_worker())
    return _worker_task


async def stop_worker(drain: bool = True):
    """Stop the background worker."""
    global _worker_task, _shutdown
    _shutdown = True
    
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
    
    if drain:
        await drain_queue()
