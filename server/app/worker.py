"""
Background worker for flushing ingest queue to database.

Runs as an asyncio task, continuously polling the Redis queue
and writing batches to PostgreSQL/MinIO.
"""
import asyncio
import logging
from typing import Optional, Any
from datetime import datetime

from app import queue, db, blob_store, cache
from app.models import Run, Step, IngestPayload, RunStatus, StepStatus

logger = logging.getLogger(__name__)


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle ISO format strings
        try:
            # Remove 'Z' suffix if present and parse
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# Worker configuration
BATCH_SIZE = 50           # Max items per batch
POLL_INTERVAL = 0.1       # Seconds to wait when queue is empty
FLUSH_INTERVAL = 1.0      # Max seconds between flushes (even if batch not full)

_worker_task: Optional[asyncio.Task] = None
_shutdown = False


async def process_payload(payload_data: dict):
    """Process a single ingest payload."""
    try:
        # Reconstruct the payload
        payload = payload_data.get("payload", payload_data)
        
        runs_processed = 0
        steps_processed = 0
        
        # Process runs
        runs = payload.get("runs", [])
        if runs:
            for run_data in runs:
                await _process_run(run_data)
                runs_processed += 1
        
        # Process steps
        steps = payload.get("steps", [])
        if steps:
            for step_data in steps:
                await _process_step(step_data)
                steps_processed += 1
        
        # Record stats
        await queue.record_processed(runs=runs_processed, steps=steps_processed)
        
    except Exception as e:
        logger.error(f"Error processing payload: {e}")
        await queue.record_error()
        raise


async def _process_run(run_data: dict):
    """Process and store a run."""
    run_dict = {
        "run_id": run_data["run_id"],
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
    
    # Invalidate cache
    await cache.invalidate_run(run_data["run_id"])


async def _process_step(step_data: dict):
    """Process and store a step with its candidate set and artifacts."""
    step_id = step_data["step_id"]
    run_id = step_data["run_id"]
    
    # Save candidate set to blob store if present
    candidate_set_ref = None
    candidate_set = step_data.get("candidate_set")
    if candidate_set:
        candidate_set_ref = await blob_store.save_candidate_set(step_id, candidate_set)
    
    # Save artifacts to blob store and index them
    artifacts = step_data.get("artifacts", [])
    if artifacts:
        for artifact in artifacts:
            artifact_id = artifact.get("artifact_id")
            if artifact_id:
                blob_ref = await blob_store.save_artifact(artifact_id, {
                    "step_id": step_id,
                    "type": artifact.get("type", "unknown"),
                    "content": artifact.get("content"),
                })
                # Index artifact in database
                await db.index_artifact(
                    artifact_id=artifact_id,
                    step_id=step_id,
                    run_id=run_id,
                    artifact_type=artifact.get("type", "unknown"),
                    blob_ref=blob_ref,
                )
    
    # Store step metadata in DB
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
    
    # Invalidate cache
    await cache.invalidate_step(step_id, run_id)


async def flush_worker():
    """
    Background worker that continuously flushes the queue to database.
    Processes items in batches for efficiency.
    """
    global _shutdown
    logger.info("Flush worker started")
    
    while not _shutdown:
        try:
            # Get batch from queue
            batch = await queue.dequeue_batch(BATCH_SIZE)
            
            if not batch:
                # Queue is empty, wait before polling again
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            # Process batch
            for item in batch:
                try:
                    await process_payload(item)
                except Exception as e:
                    logger.error(f"Failed to process item: {e}")
                    # Continue with next item
            
            logger.debug(f"Flushed {len(batch)} payloads")
            
        except asyncio.CancelledError:
            logger.info("Flush worker cancelled")
            break
        except Exception as e:
            logger.error(f"Flush worker error: {e}")
            await asyncio.sleep(1.0)  # Back off on error
    
    logger.info("Flush worker stopped")


async def drain_queue():
    """
    Drain remaining items from queue (for graceful shutdown).
    """
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
    """Start the background flush worker."""
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

