from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime

# --- Enums ---

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

# --- Core Models ---

class CandidateSet(BaseModel):
    mode: CaptureMode = CaptureMode.SUMMARY
    input_count: int = 0
    output_count: int = 0
    reason_histogram: Optional[dict[str, int]] = None  # reason -> count
    score_histogram: Optional[dict[str, int]] = None   # bucket -> count
    top_kept: Optional[list[dict[str, Any]]] = None
    top_dropped: Optional[list[dict[str, Any]]] = None
    full_candidates: Optional[list[dict[str, Any]]] = None  # only for FULL mode

class Artifact(BaseModel):
    artifact_id: str
    step_id: str
    type: ArtifactType
    content: Any  # JSON-serializable content

class Step(BaseModel):
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

class Run(BaseModel):
    run_id: str
    pipeline_name: str
    version: Optional[str] = None
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    tags: Optional[dict[str, str]] = None
    input_summary: Optional[dict[str, Any]] = None
    final_output: Optional[dict[str, Any]] = None

# --- Ingest Payload ---

class IngestPayload(BaseModel):
    schema_version: str = "1.0"
    runs: Optional[list[Run]] = None
    steps: Optional[list[Step]] = None

# --- Query Response Models ---

class RunSummary(BaseModel):
    run_id: str
    pipeline_name: str
    version: Optional[str]
    status: RunStatus
    started_at: datetime
    ended_at: Optional[datetime]
    tags: Optional[dict[str, str]]
    step_count: int = 0

class StepSummary(BaseModel):
    step_id: str
    run_id: str
    kind: StepKind
    name: str
    input_count: Optional[int]
    output_count: Optional[int]
    drop_ratio: Optional[float] = None
    status: StepStatus
    duration_ms: Optional[int]

class RunDetail(BaseModel):
    run: Run
    steps: list[StepSummary]

class StepDetail(BaseModel):
    step: Step
    candidate_set: Optional[CandidateSet] = None
    artifacts: Optional[list[dict[str, Any]]] = None

