import uuid
from datetime import datetime
from typing import Optional, Any
from contextlib import contextmanager

from zenray.models import RunData, RunStatus
from zenray.client import get_client
from zenray.step_legacy import Step

class Run:
    """Context manager for instrumenting a pipeline run."""
    
    def __init__(
        self,
        pipeline_name: str,
        run_id: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[dict[str, str]] = None,
        input_summary: Optional[dict[str, Any]] = None,
    ):
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.pipeline_name = pipeline_name
        self.version = version
        self.tags = tags
        self.input_summary = input_summary
        
        self._started_at = datetime.utcnow()
        self._status = RunStatus.RUNNING
        self._final_output: Optional[dict[str, Any]] = None
        self._steps: list[Step] = []
    
    def __enter__(self) -> "Run":
        # Send run start event
        run_data = RunData(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            version=self.version,
            status=RunStatus.RUNNING,
            started_at=self._started_at,
            tags=self.tags,
            input_summary=self.input_summary,
        )
        get_client().enqueue_run(run_data)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Determine final status
        if exc_type is not None:
            self._status = RunStatus.FAILURE
        elif self._status == RunStatus.RUNNING:
            self._status = RunStatus.SUCCESS
        
        # Send run end event
        run_data = RunData(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            version=self.version,
            status=self._status,
            started_at=self._started_at,
            ended_at=datetime.utcnow(),
            tags=self.tags,
            input_summary=self.input_summary,
            final_output=self._final_output,
        )
        get_client().enqueue_run(run_data)
        return False  # Don't suppress exceptions
    
    def set_output(self, output: dict[str, Any]):
        """Set the final output of the run."""
        self._final_output = output
    
    def set_status(self, status: RunStatus):
        """Manually set run status."""
        self._status = status
    
    def step(
        self,
        name: str,
        kind: str,
        parent: Optional["Step"] = None,
    ) -> Step:
        """Create a new step within this run."""
        step = Step(
            run_id=self.run_id,
            name=name,
            kind=kind,
            parent_step_id=parent.step_id if parent else None,
        )
        self._steps.append(step)
        return step


@contextmanager
def run(
    pipeline_name: str,
    run_id: Optional[str] = None,
    version: Optional[str] = None,
    tags: Optional[dict[str, str]] = None,
    input_summary: Optional[dict[str, Any]] = None,
):
    """Convenience function for creating a run context."""
    r = Run(
        pipeline_name=pipeline_name,
        run_id=run_id,
        version=version,
        tags=tags,
        input_summary=input_summary,
    )
    with r:
        yield r

