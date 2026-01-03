"""
X-Ray SDK - Minimal instrumentation for ML/LLM pipelines.

Quick Start:
    import xray
    
    xray.init()  # reads XRAY_ENDPOINT from env, or defaults to localhost:8000
    
    @xray.pipeline("my-pipeline")
    def process(data):
        results = fetch(data)
        filtered = filter_items(results)
        return rank(filtered)
    
    @xray.step("RETRIEVE")
    def fetch(query) -> list[dict]:
        return db.search(query)
    
    @xray.step("FILTER")
    def filter_items(items: list[dict]) -> list[dict]:
        kept = []
        for item in items:
            if item["score"] < 0.5:
                xray.drop(item, "low_score")
            else:
                kept.append(item)
        return kept
    
    @xray.step("RANK")
    def rank(items: list[dict]) -> list[dict]:
        for item in items:
            xray.score(item, item["relevance"])
        return sorted(items, key=lambda x: x["relevance"], reverse=True)[:10]

Available Functions:
    - init()          : Initialize SDK (reads from env vars)
    - pipeline(name)  : Decorator for pipeline entry points
    - step(kind)      : Decorator for pipeline steps
    - drop(item, reason) : Record why an item was dropped
    - score(item, value) : Record a score for an item
    - metric(key, value) : Add custom metric to current step
    - artifact(type, content) : Attach artifact (prompt, response, etc.)
    - tag(key, value) : Add tag to current run
    - flush()         : Force flush queued events

Step Kinds:
    RETRIEVE, FILTER, RANK, LLM_CALL, JUDGE, SELECT, TRANSFORM, TOOL_CALL

Environment Variables:
    XRAY_ENDPOINT     : Server URL (default: http://localhost:8000)
    XRAY_DISABLED     : Set to "true" to disable tracing
    XRAY_SAMPLE_RATE  : Float 0-1 for sampling (default: 1.0)
"""

# Legacy API (import first to avoid shadowing)
from xray.client import XRayClient, configure, get_client
from xray.run import Run, run as run_context
from xray.step_legacy import Step as LegacyStep
from xray.candidates import CandidateSet, CaptureMode

# Config and init
from xray.config import init, is_enabled, get_config

# Decorators (new minimal API) - these are the primary exports
from xray.decorators import pipeline, step, async_pipeline, async_step

# Helper functions
from xray.helpers import (
    drop,
    score,
    metric,
    artifact,
    tag,
    set_input_count,
    set_output_count,
)

# Context access (advanced usage)
from xray.context import get_current_run, get_current_step

# Legacy aliases
Step = LegacyStep
run = run_context


def flush():
    """Force flush all queued events to the server."""
    if is_enabled():
        get_client().flush()


def shutdown():
    """Shutdown the SDK, flushing remaining events."""
    if is_enabled():
        get_client().shutdown()


__all__ = [
    # New minimal API
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
    
    # Context access
    "get_current_run",
    "get_current_step",
    "is_enabled",
    
    # Legacy API
    "XRayClient",
    "configure",
    "get_client",
    "Run",
    "run",
    "Step",
    "CandidateSet",
    "CaptureMode",
]
