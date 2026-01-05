"""
ZenRay SDK - Observability for ML/LLM pipelines.

Debug candidate drop-off and track decision context with minimal code changes.

Quick Start:
    import zenray

    # Initialize with API key
    zenray.init(api_key="zenray_xxxxx")  # or set ZENRAY_API_KEY env var

    @zenray.pipeline("my-pipeline")
    def process(data):
        results = fetch(data)
        filtered = filter_items(results)
        return rank(filtered)

    @zenray.step("RETRIEVE")
    def fetch(query) -> list[dict]:
        return db.search(query)

    @zenray.step("FILTER")
    def filter_items(items: list[dict]) -> list[dict]:
        kept = []
        for item in items:
            if item["score"] < 0.5:
                zenray.drop(item, "low_score")
            else:
                kept.append(item)
        return kept

    @zenray.step("RANK")
    def rank(items: list[dict]) -> list[dict]:
        for item in items:
            zenray.score(item, item["relevance"])
        return sorted(items, key=lambda x: x["relevance"], reverse=True)[:10]

Main API:
    - init(api_key)      : Initialize SDK with API key
    - pipeline(name)     : Decorator for pipeline entry points
    - step(kind)         : Decorator for pipeline steps
    - drop(item, reason) : Record why an item was dropped
    - score(item, value) : Record a score for an item
    - metric(key, value) : Add custom metric to current step
    - artifact(type, content) : Attach artifact (prompt, response, etc.)
    - tag(key, value)    : Add tag to current run
    - flush()            : Force flush queued events

Step Kinds:
    RETRIEVE, FILTER, RANK, LLM_CALL, JUDGE, SELECT, TRANSFORM, TOOL_CALL

Environment Variables:
    ZENRAY_API_KEY      : API key for authentication (required)
    ZENRAY_ENDPOINT     : Server URL (default: http://localhost:8000)
    ZENRAY_DISABLED     : Set to "true" to disable tracing
    ZENRAY_SAMPLE_RATE  : Float 0-1 for sampling (default: 1.0)
"""

__version__ = "0.1.0"

# Exceptions
from zenray.client import ZenRayError, AuthenticationError, IngestError

# Configuration
from zenray.config import init, is_enabled, get_config

# Decorators (primary API)
from zenray.decorators import pipeline, step, async_pipeline, async_step

# Helper functions
from zenray.helpers import (
    drop,
    score,
    metric,
    artifact,
    tag,
    set_input_count,
    set_output_count,
)

# Context access (advanced)
from zenray.context import get_current_run, get_current_step

# Client access (advanced)
from zenray.client import XRayClient, configure, get_client

# Legacy
from zenray.run import Run, run as run_context
from zenray.step_legacy import Step
from zenray.candidates import CandidateSet, CaptureMode


def flush():
    """Force flush all queued events to the server."""
    if is_enabled():
        get_client().flush()


def shutdown():
    """Shutdown the SDK, flushing remaining events."""
    if is_enabled():
        get_client().shutdown()


def get_last_error():
    """Get the last error that occurred during ingestion."""
    if is_enabled():
        return get_client().last_error
    return None


def get_stats():
    """Get SDK statistics (success count, error count, queue size)."""
    if is_enabled():
        return get_client().stats
    return {"success_count": 0, "error_count": 0, "last_error": None, "queue_size": 0}


# Legacy aliases
run = run_context

__all__ = [
    # Version
    "__version__",
    # Main API
    "init",
    "pipeline",
    "step",
    "async_pipeline",
    "async_step",
    "drop",
    "score",
    "metric",
    "artifact",
    "tag",
    "set_input_count",
    "set_output_count",
    "flush",
    "shutdown",
    "get_last_error",
    "get_stats",
    # Exceptions
    "ZenRayError",
    "AuthenticationError",
    "IngestError",
    # Context
    "get_current_run",
    "get_current_step",
    "is_enabled",
    # Advanced
    "XRayClient",
    "configure",
    "get_client",
    "get_config",
    # Legacy
    "Run",
    "run",
    "Step",
    "CandidateSet",
    "CaptureMode",
]
