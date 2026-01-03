from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app import db
from app import blob_store
from app.models import RunSummary, StepSummary, RunDetail, StepDetail, RunStatus, StepStatus, StepKind

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
    return result

@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str):
    """Get run detail with step timeline."""
    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    steps = await db.get_steps_for_run(run_id)
    step_summaries = [_to_step_summary(s) for s in steps]
    
    return RunDetail(
        run=run,
        steps=step_summaries,
    )

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
    step = await db.get_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail=f"Step {step_id} not found")
    
    # Load candidate set from blob store
    candidate_set = None
    if step.get("candidate_set_ref"):
        candidate_set = blob_store.load_candidate_set(step_id)
    
    # Load artifacts
    artifacts = blob_store.list_artifacts_for_step(step_id)
    artifact_details = []
    for art in artifacts:
        content = blob_store.load_artifact(art["artifact_id"])
        if content:
            artifact_details.append(content)
    
    return StepDetail(
        step=step,
        candidate_set=candidate_set,
        artifacts=artifact_details if artifact_details else None,
    )

@router.get("/steps/{step_id}/candidates")
async def get_step_candidates(step_id: str):
    """Get full candidate set for a step."""
    step = await db.get_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail=f"Step {step_id} not found")
    
    candidate_set = blob_store.load_candidate_set(step_id)
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

