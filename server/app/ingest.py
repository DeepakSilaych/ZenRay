from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models import IngestPayload, Run, Step
from app import db
from app import blob_store

router = APIRouter()

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

class IngestResponse(BaseModel):
    accepted_runs: int = 0
    accepted_steps: int = 0
    errors: list[str] = []

@router.post("", response_model=IngestResponse)
async def ingest(payload: IngestPayload):
    """Batch ingest runs and steps."""
    
    # Validate schema version
    if payload.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported schema version: {payload.schema_version}. Supported: {SUPPORTED_SCHEMA_VERSIONS}"
        )
    
    response = IngestResponse()
    
    # Process runs
    if payload.runs:
        for run in payload.runs:
            try:
                await _process_run(run)
                response.accepted_runs += 1
            except Exception as e:
                response.errors.append(f"Run {run.run_id}: {str(e)}")
    
    # Process steps
    if payload.steps:
        for step in payload.steps:
            try:
                await _process_step(step)
                response.accepted_steps += 1
            except Exception as e:
                response.errors.append(f"Step {step.step_id}: {str(e)}")
    
    return response

async def _process_run(run: Run):
    """Process and store a run."""
    run_dict = {
        "run_id": run.run_id,
        "pipeline_name": run.pipeline_name,
        "version": run.version,
        "status": run.status.value,
        "started_at": run.started_at.isoformat(),
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "tags": run.tags,
        "input_summary": run.input_summary,
        "final_output": run.final_output,
    }
    await db.upsert_run(run_dict)

async def _process_step(step: Step):
    """Process and store a step with its candidate set and artifacts."""
    
    # Save candidate set to blob store if present
    candidate_set_ref = None
    if step.candidate_set:
        candidate_set_dict = step.candidate_set.model_dump()
        candidate_set_ref = blob_store.save_candidate_set(step.step_id, candidate_set_dict)
    
    # Save artifacts to blob store if present
    if step.artifacts:
        for artifact in step.artifacts:
            blob_store.save_artifact(artifact.artifact_id, {
                "step_id": artifact.step_id,
                "type": artifact.type.value,
                "content": artifact.content,
            })
    
    # Store step metadata in DB
    step_dict = {
        "step_id": step.step_id,
        "run_id": step.run_id,
        "parent_step_id": step.parent_step_id,
        "kind": step.kind.value,
        "name": step.name,
        "input_count": step.input_count,
        "output_count": step.output_count,
        "status": step.status.value,
        "duration_ms": step.duration_ms,
        "started_at": step.started_at.isoformat() if step.started_at else None,
        "ended_at": step.ended_at.isoformat() if step.ended_at else None,
        "metrics": step.metrics,
        "candidate_set_ref": candidate_set_ref,
    }
    await db.upsert_step(step_dict)

