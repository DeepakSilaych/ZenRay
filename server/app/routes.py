from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app import db
from app import blob_store
from app import cache
from app.models import RunSummary, StepSummary, RunDetail, StepDetail, RunStatus, StepKind

router = APIRouter()

# --- Run endpoints ---

@router.get("/runs", response_model=list[RunSummary])
async def list_runs(
    pipeline_name: Optional[str] = None,
    status: Optional[RunStatus] = None,
    start_time: Optional[str] = Query(None, description="ISO format datetime"),
    end_time: Optional[str] = Query(None, description="ISO format datetime"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Search runs by pipeline, status, time range."""
    # Check cache first
    cache_key = cache.runs_list_key(pipeline_name, status.value if status else None)
    cached = await cache.cache_get(cache_key)
    if cached and offset == 0:
        return cached[:limit]
    
    runs = await db.search_runs(
        pipeline_name=pipeline_name,
        status=status.value if status else None,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    
    # Enrich with step count
    result = []
    for run in runs:
        step_count = await db.count_steps_for_run(run["run_id"])
        result.append(RunSummary(
            run_id=run["run_id"],
            pipeline_name=run["pipeline_name"],
            version=run["version"],
            status=run["status"],
            started_at=run["started_at"],
            ended_at=run["ended_at"],
            tags=run["tags"],
            step_count=step_count,
        ))
    
    # Cache the result
    if offset == 0:
        await cache.cache_set(cache_key, [r.model_dump() for r in result], cache.CACHE_TTL_SHORT)
    
    return result


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str):
    """Get run detail with step timeline."""
    # Check cache
    cache_key = cache.run_detail_key(run_id)
    cached = await cache.cache_get(cache_key)
    if cached:
        return RunDetail(**cached)
    
    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    steps = await db.get_steps_for_run(run_id)
    step_summaries = [_to_step_summary(s) for s in steps]
    
    result = RunDetail(
        run=run,
        steps=step_summaries,
    )
    
    # Cache completed runs longer
    ttl = cache.CACHE_TTL_LONG if run["status"] in ("SUCCESS", "FAILURE") else cache.CACHE_TTL_SHORT
    await cache.cache_set(cache_key, result.model_dump(), ttl)
    
    return result


# --- Candidate Trace ---

@router.get("/runs/{run_id}/trace")
async def trace_candidate(
    run_id: str,
    q: str = Query(..., description="Search term (matches id, name, or title)"),
):
    """Trace a candidate through all steps of a run."""
    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    steps = await db.get_steps_for_run(run_id)
    q_lower = q.lower()
    
    # Track candidate journey
    journey = []
    
    for step in steps:
        step_id = step["step_id"]
        candidate_set = await blob_store.load_candidate_set(step_id)
        
        if not candidate_set:
            continue
        
        # Search in top_kept, top_dropped, and dropped_by_reason
        found_in_kept = _search_candidates(candidate_set.get("top_kept", []) or [], q_lower)
        found_in_dropped = _search_candidates(candidate_set.get("top_dropped", []) or [], q_lower)
        
        # Also search in dropped_by_reason
        drop_reason = None
        dropped_by_reason = candidate_set.get("dropped_by_reason", {}) or {}
        for reason, candidates in dropped_by_reason.items():
            matches = _search_candidates(candidates or [], q_lower)
            if matches:
                found_in_dropped.extend(matches)
                drop_reason = reason
                break
        
        if found_in_kept or found_in_dropped:
            journey.append({
                "step_id": step_id,
                "step_name": step["name"],
                "step_kind": step["kind"],
                "status": "kept" if found_in_kept else "dropped",
                "drop_reason": drop_reason if found_in_dropped else None,
                "candidate": found_in_kept[0] if found_in_kept else (found_in_dropped[0] if found_in_dropped else None),
            })
    
    return {
        "query": q,
        "run_id": run_id,
        "found": len(journey) > 0,
        "journey": journey,
    }


def _search_candidates(candidates: list, query: str) -> list:
    """Search candidates by id, name, or title."""
    matches = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        # Search in common fields
        searchable = [
            str(c.get("id", "")),
            str(c.get("name", "")),
            str(c.get("title", "")),
        ]
        if any(query in s.lower() for s in searchable):
            matches.append(c)
    return matches


# --- Step endpoints ---

@router.get("/steps", response_model=list[StepSummary])
async def list_steps(
    kind: Optional[StepKind] = None,
    run_id: Optional[str] = None,
    min_drop_ratio: Optional[float] = Query(None, ge=0, le=1, description="Min drop ratio (0-1)"),
    max_drop_ratio: Optional[float] = Query(None, ge=0, le=1, description="Max drop ratio (0-1)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Search steps by kind, drop ratio."""
    steps = await db.search_steps(
        kind=kind.value if kind else None,
        run_id=run_id,
        min_drop_ratio=min_drop_ratio,
        max_drop_ratio=max_drop_ratio,
        limit=limit,
        offset=offset,
    )
    return [_to_step_summary(s) for s in steps]


@router.get("/steps/{step_id}", response_model=StepDetail)
async def get_step(step_id: str):
    """Get step detail with candidate set and artifacts."""
    # Check cache
    cache_key = cache.step_key(step_id)
    cached = await cache.cache_get(cache_key)
    if cached:
        return StepDetail(**cached)
    
    step = await db.get_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail=f"Step {step_id} not found")
    
    # Load candidate set from blob store
    candidate_set = None
    if step.get("candidate_set_ref"):
        candidate_set = await blob_store.load_candidate_set(step_id)
    
    # Load artifacts from database index
    artifact_records = await db.get_artifacts_for_step(step_id)
    artifact_details = []
    for art in artifact_records:
        content = await blob_store.load_artifact(art["artifact_id"])
        if content:
            artifact_details.append(content)
    
    result = StepDetail(
        step=step,
        candidate_set=candidate_set,
        artifacts=artifact_details if artifact_details else None,
    )
    
    # Cache the result
    await cache.cache_set(cache_key, result.model_dump(), cache.CACHE_TTL_MEDIUM)
    
    return result


@router.get("/steps/{step_id}/candidates")
async def get_step_candidates(step_id: str):
    """Get full candidate set for a step."""
    step = await db.get_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail=f"Step {step_id} not found")
    
    candidate_set = await blob_store.load_candidate_set(step_id)
    if not candidate_set:
        return {"message": "No candidate set recorded for this step"}
    
    return candidate_set


# --- Helpers ---

def _to_step_summary(step: dict) -> StepSummary:
    drop_ratio = None
    inp, out = step.get("input_count"), step.get("output_count")
    if inp and inp > 0 and out is not None and out <= inp:
        drop_ratio = round(1 - (out / inp), 4)
    
    return StepSummary(
        step_id=step["step_id"],
        run_id=step["run_id"],
        kind=step["kind"],
        name=step["name"],
        input_count=step.get("input_count"),
        output_count=step.get("output_count"),
        drop_ratio=drop_ratio,
        status=step["status"],
        duration_ms=step.get("duration_ms"),
    )


# --- Run Comparison ---

@router.get("/compare")
async def compare_runs(
    run_a: str = Query(..., description="First run ID"),
    run_b: str = Query(..., description="Second run ID"),
):
    """
    Compare two runs side-by-side.
    Useful for A/B testing pipeline versions or debugging regressions.
    """
    # Fetch both runs
    run_a_data = await db.get_run(run_a)
    run_b_data = await db.get_run(run_b)
    
    if not run_a_data:
        raise HTTPException(status_code=404, detail=f"Run {run_a} not found")
    if not run_b_data:
        raise HTTPException(status_code=404, detail=f"Run {run_b} not found")
    
    # Fetch steps for both
    steps_a = await db.get_steps_for_run(run_a)
    steps_b = await db.get_steps_for_run(run_b)
    
    # Build step maps by name for comparison
    steps_a_by_name = {s["name"]: s for s in steps_a}
    steps_b_by_name = {s["name"]: s for s in steps_b}
    
    # Get all unique step names
    all_step_names = list(dict.fromkeys(
        [s["name"] for s in steps_a] + [s["name"] for s in steps_b]
    ))
    
    # Compare each step
    step_comparisons = []
    for name in all_step_names:
        sa = steps_a_by_name.get(name)
        sb = steps_b_by_name.get(name)
        
        comparison = {
            "step_name": name,
            "in_run_a": sa is not None,
            "in_run_b": sb is not None,
        }
        
        if sa:
            comparison["run_a"] = {
                "step_id": sa["step_id"],
                "kind": sa["kind"],
                "input_count": sa.get("input_count"),
                "output_count": sa.get("output_count"),
                "drop_ratio": _calc_drop_ratio(sa),
                "duration_ms": sa.get("duration_ms"),
                "status": sa["status"],
            }
        else:
            comparison["run_a"] = None
            
        if sb:
            comparison["run_b"] = {
                "step_id": sb["step_id"],
                "kind": sb["kind"],
                "input_count": sb.get("input_count"),
                "output_count": sb.get("output_count"),
                "drop_ratio": _calc_drop_ratio(sb),
                "duration_ms": sb.get("duration_ms"),
                "status": sb["status"],
            }
        else:
            comparison["run_b"] = None
        
        # Calculate deltas
        if sa and sb:
            comparison["deltas"] = {
                "output_count": (sb.get("output_count") or 0) - (sa.get("output_count") or 0),
                "drop_ratio": round((_calc_drop_ratio(sb) or 0) - (_calc_drop_ratio(sa) or 0), 4),
                "duration_ms": (sb.get("duration_ms") or 0) - (sa.get("duration_ms") or 0),
            }
        else:
            comparison["deltas"] = None
        
        step_comparisons.append(comparison)
    
    # Overall summary
    total_duration_a = sum(s.get("duration_ms") or 0 for s in steps_a)
    total_duration_b = sum(s.get("duration_ms") or 0 for s in steps_b)
    
    # Final output comparison
    final_a = run_a_data.get("final_output")
    final_b = run_b_data.get("final_output")
    
    return {
        "run_a": {
            "run_id": run_a,
            "pipeline_name": run_a_data["pipeline_name"],
            "version": run_a_data.get("version"),
            "status": run_a_data["status"],
            "total_steps": len(steps_a),
            "total_duration_ms": total_duration_a,
            "final_output": final_a,
        },
        "run_b": {
            "run_id": run_b,
            "pipeline_name": run_b_data["pipeline_name"],
            "version": run_b_data.get("version"),
            "status": run_b_data["status"],
            "total_steps": len(steps_b),
            "total_duration_ms": total_duration_b,
            "final_output": final_b,
        },
        "step_comparisons": step_comparisons,
        "summary": {
            "steps_only_in_a": sum(1 for c in step_comparisons if c["in_run_a"] and not c["in_run_b"]),
            "steps_only_in_b": sum(1 for c in step_comparisons if c["in_run_b"] and not c["in_run_a"]),
            "steps_in_both": sum(1 for c in step_comparisons if c["in_run_a"] and c["in_run_b"]),
            "duration_delta_ms": total_duration_b - total_duration_a,
            "output_changed": final_a != final_b,
        },
    }


def _calc_drop_ratio(step: dict) -> Optional[float]:
    inp, out = step.get("input_count"), step.get("output_count")
    if inp and inp > 0 and out is not None and out <= inp:
        return round(1 - (out / inp), 4)
    return None
