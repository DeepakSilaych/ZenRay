"""
Helper functions for recording data within steps.

These functions access the current step context and record data.
They are designed to be called within @step decorated functions.
"""
from typing import Any, Optional

from zenray.context import get_current_step


def _get_item_id(item: Any) -> str:
    """Extract ID from an item."""
    if isinstance(item, dict):
        return item.get("id", item.get("_id", str(id(item))))
    if hasattr(item, "id"):
        return str(item.id)
    return str(id(item))


def drop(item: Any, reason: str) -> None:
    """
    Record that an item was dropped and why.
    
    Call this within a @step function when filtering out candidates.
    
    Example:
        @xray.step("FILTER")
        def filter_items(items):
            kept = []
            for item in items:
                if item["score"] < 0.5:
                    xray.drop(item, "low_score")
                else:
                    kept.append(item)
            return kept
    
    Args:
        item: The item being dropped (dict or object with .id)
        reason: Why the item was dropped (e.g., "low_score", "inactive")
    """
    step = get_current_step()
    if step is None:
        return  # No active step, silently ignore
    
    item_id = _get_item_id(item)
    step._drops[item_id] = reason


def score(item: Any, value: float) -> None:
    """
    Record a score for an item.
    
    Call this within a @step function when assigning scores to candidates.
    The SDK will build a score histogram from recorded scores.
    
    Example:
        @xray.step("RANK")
        def rank_items(items):
            for item in items:
                s = compute_similarity(item)
                xray.score(item, s)
                item["score"] = s
            return sorted(items, key=lambda x: x["score"], reverse=True)
    
    Args:
        item: The item being scored (dict or object with .id)
        value: The score value (typically 0-1)
    """
    step = get_current_step()
    if step is None:
        return
    
    item_id = _get_item_id(item)
    step._scores[item_id] = value


def metric(key: str, value: Any) -> None:
    """
    Record a custom metric for the current step.
    
    Example:
        @xray.step("LLM_CALL")
        def generate(prompt):
            xray.metric("model", "gpt-4")
            xray.metric("temperature", 0.7)
            xray.metric("tokens_used", 150)
            return call_llm(prompt)
    
    Args:
        key: Metric name
        value: Metric value (should be JSON-serializable)
    """
    step = get_current_step()
    if step is None:
        return
    
    step._metrics[key] = value


def artifact(artifact_type: str, content: Any) -> None:
    """
    Attach an artifact to the current step.
    
    Artifacts are stored as blobs and can be viewed in the UI.
    Common types: "prompt", "response", "config", "input", "output"
    
    Example:
        @xray.step("LLM_CALL")
        def generate(prompt):
            xray.artifact("prompt", prompt)
            response = call_llm(prompt)
            xray.artifact("response", response)
            return response
    
    Args:
        artifact_type: Type of artifact (prompt, response, config, etc.)
        content: The artifact content (will be JSON-serialized)
    """
    step = get_current_step()
    if step is None:
        return
    
    step._artifacts.append({
        "type": artifact_type,
        "content": content,
    })


def set_input_count(count: int) -> None:
    """
    Manually set the input count for the current step.
    
    Usually auto-detected from list arguments, but can be set manually
    if input is not a list or comes from multiple sources.
    
    Example:
        @xray.step("RETRIEVE")
        def fetch_data(query):
            xray.set_input_count(1)  # single query input
            results = db.search(query)
            return results  # output count auto-detected
    """
    step = get_current_step()
    if step is None:
        return
    
    step._input_count = count


def set_output_count(count: int) -> None:
    """
    Manually set the output count for the current step.
    
    Usually auto-detected from list return values, but can be set manually
    if output is not a list.
    """
    step = get_current_step()
    if step is None:
        return
    
    step._output_count = count


def tag(key: str, value: str) -> None:
    """
    Add a tag to the current run.
    
    Tags can be used for filtering runs in the UI.
    
    Example:
        @xray.pipeline("search")
        def search(query):
            xray.tag("query_type", classify_query(query))
            return do_search(query)
    """
    from zenray.context import get_current_run
    run = get_current_run()
    if run is None:
        return
    
    if run.tags is None:
        run.tags = {}
    run.tags[key] = value

