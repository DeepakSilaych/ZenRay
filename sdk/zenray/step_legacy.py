import uuid
from datetime import datetime
from typing import Optional, Any

from zenray.models import StepData, StepStatus, StepKind, ArtifactData, ArtifactType
from zenray.client import get_client
from zenray.candidates import CandidateSet

class Step:
    """Context manager for instrumenting a pipeline step."""
    
    def __init__(
        self,
        run_id: str,
        name: str,
        kind: str,
        step_id: Optional[str] = None,
        parent_step_id: Optional[str] = None,
    ):
        self.step_id = step_id or f"step-{uuid.uuid4().hex[:12]}"
        self.run_id = run_id
        self.name = name
        self.kind = StepKind(kind)
        self.parent_step_id = parent_step_id
        
        self._started_at = datetime.utcnow()
        self._status = StepStatus.RUNNING
        self._input_count: Optional[int] = None
        self._output_count: Optional[int] = None
        self._metrics: dict[str, Any] = {}
        self._candidate_set: Optional[CandidateSet] = None
        self._artifacts: list[ArtifactData] = []
    
    def __enter__(self) -> "Step":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - self._started_at).total_seconds() * 1000)
        
        if exc_type is not None:
            self._status = StepStatus.FAILURE
        elif self._status == StepStatus.RUNNING:
            self._status = StepStatus.SUCCESS
        
        # Build step data
        step_data = StepData(
            step_id=self.step_id,
            run_id=self.run_id,
            parent_step_id=self.parent_step_id,
            kind=self.kind,
            name=self.name,
            input_count=self._input_count,
            output_count=self._output_count,
            status=self._status,
            duration_ms=duration_ms,
            started_at=self._started_at,
            ended_at=ended_at,
            metrics=self._metrics if self._metrics else None,
            candidate_set=self._candidate_set.to_data() if self._candidate_set else None,
            artifacts=self._artifacts if self._artifacts else None,
        )
        get_client().enqueue_step(step_data)
        return False
    
    def set_counts(self, input_count: int, output_count: int):
        """Set input/output candidate counts."""
        self._input_count = input_count
        self._output_count = output_count
    
    def set_input_count(self, count: int):
        self._input_count = count
    
    def set_output_count(self, count: int):
        self._output_count = count
    
    def add_metric(self, key: str, value: Any):
        """Add a custom metric."""
        self._metrics[key] = value
    
    def set_status(self, status: StepStatus):
        """Manually set step status."""
        self._status = status
    
    def record_candidates(self) -> CandidateSet:
        """Get a CandidateSet helper for recording candidates."""
        self._candidate_set = CandidateSet(step=self)
        return self._candidate_set
    
    def add_artifact(
        self,
        artifact_type: str,
        content: Any,
        artifact_id: Optional[str] = None,
    ):
        """Attach an artifact (prompt, response, config, etc.)."""
        art_id = artifact_id or f"{self.step_id}_{artifact_type}_{uuid.uuid4().hex[:8]}"
        self._artifacts.append(ArtifactData(
            artifact_id=art_id,
            step_id=self.step_id,
            type=ArtifactType(artifact_type),
            content=content,
        ))

