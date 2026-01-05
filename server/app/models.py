"""
Pydantic models for ZenRay API.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class RunStatus(str, Enum):
    """Run status values."""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class StepStatus(str, Enum):
    """Step status values."""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class StepKind(str, Enum):
    """Step kind values."""
    RETRIEVE = "RETRIEVE"
    FILTER = "FILTER"
    RANK = "RANK"
    LLM_CALL = "LLM_CALL"
    JUDGE = "JUDGE"
    SELECT = "SELECT"
    TRANSFORM = "TRANSFORM"
    TOOL_CALL = "TOOL_CALL"


class ArtifactType(str, Enum):
    """Artifact type values."""
    PROMPT = "prompt"
    RESPONSE = "response"
    DEBUG = "debug"
    CONFIG = "config"
    METRICS = "metrics"


# =============================================================================
# Ingest Models
# =============================================================================

class CandidateSet(BaseModel):
    """Candidate set for a step."""
    mode: str = "summary"
    input_count: int = 0
    output_count: int = 0
    reason_histogram: Optional[dict[str, int]] = None
    score_histogram: Optional[dict[str, int]] = None
    top_kept: Optional[list[Any]] = None
    top_dropped: Optional[list[Any]] = None
    dropped_by_reason: Optional[dict[str, list[Any]]] = None
    full_candidates: Optional[list[Any]] = None


class Artifact(BaseModel):
    """Artifact attached to a step."""
    artifact_id: str
    step_id: str
    type: ArtifactType
    content: Any


class Run(BaseModel):
    """Run data for ingestion."""
    run_id: str
    pipeline_name: str
    version: Optional[str] = None
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime
    ended_at: Optional[datetime] = None
    tags: Optional[dict[str, str]] = None
    input_summary: Optional[dict[str, Any]] = None
    final_output: Optional[dict[str, Any]] = None


class Step(BaseModel):
    """Step data for ingestion."""
    step_id: str
    run_id: str
    parent_step_id: Optional[str] = None
    kind: StepKind
    name: str
    input_count: Optional[int] = None
    output_count: Optional[int] = None
    status: StepStatus = StepStatus.RUNNING
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metrics: Optional[dict[str, Any]] = None
    candidate_set: Optional[CandidateSet] = None
    artifacts: Optional[list[Artifact]] = None


class IngestPayload(BaseModel):
    """Batch ingest payload."""
    schema_version: str = "1.0"
    runs: Optional[list[Run]] = None
    steps: Optional[list[Step]] = None


# =============================================================================
# Query Response Models
# =============================================================================

class RunSummary(BaseModel):
    """Run summary for list views."""
    run_id: str
    pipeline_name: str
    version: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    tags: Optional[dict[str, str]] = None
    step_count: int = 0


class StepSummary(BaseModel):
    """Step summary for list views."""
    step_id: str
    run_id: str
    kind: str
    name: str
    input_count: Optional[int] = None
    output_count: Optional[int] = None
    drop_ratio: Optional[float] = None
    status: str
    duration_ms: Optional[int] = None


class RunDetail(BaseModel):
    """Detailed run with steps."""
    run: dict
    steps: list[StepSummary]


class StepDetail(BaseModel):
    """Detailed step with candidate set and artifacts."""
    step: dict
    candidate_set: Optional[dict] = None
    artifacts: Optional[list[dict]] = None
