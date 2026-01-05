"""
Redis cache operations for ZenRay.
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger("zenray.cache")

_redis: Optional[redis.Redis] = None

# Cache TTLs in seconds
CACHE_TTL_SHORT = 60       # 1 minute - for frequently changing data
CACHE_TTL_MEDIUM = 300     # 5 minutes - for run lists
CACHE_TTL_LONG = 3600      # 1 hour - for completed run details


# =============================================================================
# Connection Management
# =============================================================================

async def init_cache():
    """Initialize Redis connection."""
    global _redis
    settings = get_settings()
    _redis = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )
    await _redis.ping()
    logger.info("Redis connection initialized")


async def close_cache():
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed")


def get_redis() -> redis.Redis:
    """Get Redis client."""
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


# =============================================================================
# Cache Operations
# =============================================================================

async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = get_redis()
    value = await r.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_MEDIUM):
    """Set value in cache with TTL."""
    r = get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str):
    """Delete key from cache."""
    r = get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str):
    """Delete all keys matching pattern."""
    r = get_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break


# =============================================================================
# Cache Key Builders
# =============================================================================

def run_key(run_id: str) -> str:
    """Cache key for a run."""
    return f"run:{run_id}"


def run_detail_key(run_id: str) -> str:
    """Cache key for run detail."""
    return f"run_detail:{run_id}"


def step_key(step_id: str) -> str:
    """Cache key for a step."""
    return f"step:{step_id}"


def runs_list_key(
    pipeline_name: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Cache key for runs list."""
    return f"runs_list:{user_id or 'all'}:{pipeline_name or 'all'}:{status or 'all'}"


# =============================================================================
# Invalidation Helpers
# =============================================================================

async def invalidate_run(run_id: str):
    """Invalidate all caches related to a run."""
    await cache_delete(run_key(run_id))
    await cache_delete(run_detail_key(run_id))
    await cache_delete_pattern("runs_list:*")


async def invalidate_step(step_id: str, run_id: str):
    """Invalidate step and related caches."""
    await cache_delete(step_key(step_id))
    await cache_delete(run_detail_key(run_id))
