"""
Redis-backed write queue for async ingestion.

The queue buffers ingest payloads and allows background workers
to flush them to PostgreSQL/MinIO in batches, reducing write latency
for the SDK and improving throughput under load.
"""
import json
from typing import Any, Optional
from datetime import datetime

from app.cache import get_redis

# Queue keys
INGEST_QUEUE = "xray:ingest:queue"
INGEST_PROCESSING = "xray:ingest:processing"
INGEST_STATS = "xray:ingest:stats"


async def enqueue_ingest(payload: dict) -> str:
    """
    Push ingest payload to Redis queue.
    Returns a queue ID for tracking.
    """
    r = get_redis()
    
    # Add metadata
    queue_item = {
        "payload": payload,
        "queued_at": datetime.utcnow().isoformat(),
    }
    
    # Push to queue (left side - FIFO with rpop)
    await r.lpush(INGEST_QUEUE, json.dumps(queue_item, default=str))
    
    # Update stats
    await r.hincrby(INGEST_STATS, "total_queued", 1)
    
    return "queued"


async def dequeue_batch(batch_size: int = 100) -> list[dict]:
    """
    Pop a batch of payloads from the queue.
    Uses RPOP for FIFO ordering (oldest first).
    """
    r = get_redis()
    items = []
    
    for _ in range(batch_size):
        # Pop from right side (oldest items)
        item = await r.rpop(INGEST_QUEUE)
        if item is None:
            break
        
        try:
            parsed = json.loads(item)
            items.append(parsed)
        except json.JSONDecodeError:
            # Log and skip malformed items
            await r.hincrby(INGEST_STATS, "parse_errors", 1)
            continue
    
    return items


async def queue_length() -> int:
    """Get current queue length."""
    r = get_redis()
    return await r.llen(INGEST_QUEUE)


async def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics."""
    r = get_redis()
    
    stats = await r.hgetall(INGEST_STATS)
    queue_len = await queue_length()
    
    return {
        "queue_length": queue_len,
        "total_queued": int(stats.get("total_queued", 0)),
        "total_processed": int(stats.get("total_processed", 0)),
        "total_errors": int(stats.get("total_errors", 0)),
        "parse_errors": int(stats.get("parse_errors", 0)),
        "runs_processed": int(stats.get("runs_processed", 0)),
        "steps_processed": int(stats.get("steps_processed", 0)),
    }


async def record_processed(runs: int = 0, steps: int = 0):
    """Record successful processing stats."""
    r = get_redis()
    await r.hincrby(INGEST_STATS, "total_processed", 1)
    if runs > 0:
        await r.hincrby(INGEST_STATS, "runs_processed", runs)
    if steps > 0:
        await r.hincrby(INGEST_STATS, "steps_processed", steps)


async def record_error():
    """Record processing error."""
    r = get_redis()
    await r.hincrby(INGEST_STATS, "total_errors", 1)


async def reset_stats():
    """Reset queue statistics (for testing)."""
    r = get_redis()
    await r.delete(INGEST_STATS)

