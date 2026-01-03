from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum
from datetime import datetime

class StepKind(str, Enum):
    RETRIEVE = "RETRIEVE"
    FILTER = "FILTER"
    RANK = "RANK"
    LLM_CALL = "LLM_CALL"
    JUDGE = "JUDGE"
    SELECT = "SELECT"
    TRANSFORM = "TRANSFORM"
    TOOL_CALL = "TOOL_CALL"

class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"

class StepStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"

class CaptureMode(str, Enum):
    SUMMARY = "SUMMARY"
    TOP_K = "TOP_K"
    FULL = "FULL"

class ArtifactType(str, Enum):
    PROMPT = "prompt"
    RESPONSE = "response"
    CONFIG = "config"
    INPUT = "input"
    OUTPUT = "output"
    JUDGMENTS = "judgments"
    METADATA = "metadata"
    ERROR = "error"
    DEBUG = "debug"

class CandidateSetData(BaseModel):
    mode: CaptureMode = CaptureMode.SUMMARY
    input_count: int = 0
    output_count: int = 0
    reason_histogram: Optional[dict[str, int]] = None
    score_histogram: Optional[dict[str, int]] = None
    top_kept: Optional[list[dict[str, Any]]] = None
    top_dropped: Optional[list[dict[str, Any]]] = None
    dropped_by_reason: Optional[dict[str, list[dict[str, Any]]]] = None  # reason -> candidates
    full_candidates: Optional[list[dict[str, Any]]] = None

class ArtifactData(BaseModel):
    artifact_id: str
    step_id: str
    type: ArtifactType
    content: Any

class StepData(BaseModel):
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
    candidate_set: Optional[CandidateSetData] = None
    artifacts: Optional[list[ArtifactData]] = None

class RunData(BaseModel):
    run_id: str
    pipeline_name: str
    version: Optional[str] = None
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime
    ended_at: Optional[datetime] = None
    tags: Optional[dict[str, str]] = None
    input_summary: Optional[dict[str, Any]] = None
    final_output: Optional[dict[str, Any]] = None

class IngestPayload(BaseModel):
    schema_version: str = "1.0"
    runs: Optional[list[RunData]] = None
    steps: Optional[list[StepData]] = None

