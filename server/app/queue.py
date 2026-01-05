"""
Redis queue operations for async ingestion.
"""
import json
import logging
from typing import Any

from app.cache import get_redis

logger = logging.getLogger("zenray.queue")

INGEST_QUEUE_KEY = "zenray:ingest:queue"
STATS_KEY = "zenray:ingest:stats"


# =============================================================================
# Queue Operations
# =============================================================================

async def enqueue_ingest(payload: dict):
    """Add payload to ingest queue."""
    r = get_redis()
    await r.rpush(INGEST_QUEUE_KEY, json.dumps(payload))


async def dequeue_batch(batch_size: int = 50) -> list[dict]:
    """Dequeue a batch of payloads."""
    r = get_redis()
    batch = []
    
    for _ in range(batch_size):
        data = await r.lpop(INGEST_QUEUE_KEY)
        if not data:
            break
        batch.append(json.loads(data))
    
    return batch


async def queue_length() -> int:
    """Get current queue length."""
    r = get_redis()
    return await r.llen(INGEST_QUEUE_KEY)


# =============================================================================
# Statistics
# =============================================================================

async def record_processed(runs: int = 0, steps: int = 0):
    """Record processed items count."""
    r = get_redis()
    if runs:
        await r.hincrby(STATS_KEY, "runs_processed", runs)
    if steps:
        await r.hincrby(STATS_KEY, "steps_processed", steps)


async def record_error():
    """Record processing error."""
    r = get_redis()
    await r.hincrby(STATS_KEY, "errors", 1)


async def get_queue_stats() -> dict:
    """Get queue statistics."""
    r = get_redis()
    
    stats = await r.hgetall(STATS_KEY)
    length = await queue_length()
    
    return {
        "queue_length": length,
        "runs_processed": int(stats.get("runs_processed", 0)),
        "steps_processed": int(stats.get("steps_processed", 0)),
        "errors": int(stats.get("errors", 0)),
    }
