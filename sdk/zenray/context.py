"""
Context management for X-Ray tracing.

Uses Python's contextvars for thread-safe and async-safe
tracking of the current run and step.
"""
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from zenray.models import RunData, StepData

# Context variables for tracking active run/step
_current_run: ContextVar[Optional["RunContext"]] = ContextVar("xray_run", default=None)
_current_step: ContextVar[Optional["StepContext"]] = ContextVar("xray_step", default=None)


class RunContext:
    """Lightweight run context for decorator-based tracing."""
    
    def __init__(
        self,
        pipeline_name: str,
        run_id: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[dict[str, str]] = None,
    ):
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.pipeline_name = pipeline_name
        self.version = version
        self.tags = tags
        self.started_at = datetime.utcnow()
        self.input_summary: Optional[dict] = None
        self.final_output: Any = None
        self._steps: list["StepContext"] = []
        self._token = None
    
    def _start(self, input_args: tuple = (), input_kwargs: dict = None):
        """Start the run and send start event."""
        from zenray.models import RunData, RunStatus
        from zenray.client import get_client
        from zenray.config import is_enabled
        
        # Capture input summary from first positional arg if dict-like
        if input_args and hasattr(input_args[0], "__dict__"):
            self.input_summary = {"type": type(input_args[0]).__name__}
        elif input_args and isinstance(input_args[0], dict):
            self.input_summary = input_args[0]
        
        if not is_enabled():
            return
        
        run_data = RunData(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            version=self.version,
            status=RunStatus.RUNNING,
            started_at=self.started_at,
            tags=self.tags,
            input_summary=self.input_summary,
        )
        get_client().enqueue_run(run_data)
    
    def _end(self, result: Any = None):
        """End the run successfully."""
        from zenray.models import RunData, RunStatus
        from zenray.client import get_client
        from zenray.config import is_enabled
        
        self.final_output = self._summarize_output(result)
        
        if not is_enabled():
            return
        
        run_data = RunData(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            version=self.version,
            status=RunStatus.SUCCESS,
            started_at=self.started_at,
            ended_at=datetime.utcnow(),
            tags=self.tags,
            input_summary=self.input_summary,
            final_output=self.final_output,
        )
        get_client().enqueue_run(run_data)
    
    def _fail(self, error: Exception):
        """End the run with failure."""
        from zenray.models import RunData, RunStatus
        from zenray.client import get_client
        from zenray.config import is_enabled
        
        if not is_enabled():
            return
        
        run_data = RunData(
            run_id=self.run_id,
            pipeline_name=self.pipeline_name,
            version=self.version,
            status=RunStatus.FAILURE,
            started_at=self.started_at,
            ended_at=datetime.utcnow(),
            tags=self.tags,
            input_summary=self.input_summary,
            final_output={"error": str(error), "type": type(error).__name__},
        )
        get_client().enqueue_run(run_data)
    
    def _summarize_output(self, result: Any) -> Optional[dict]:
        """Create a summary of the output."""
        if result is None:
            return None
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"count": len(result), "type": "list"}
        if hasattr(result, "__dict__"):
            return {"type": type(result).__name__}
        return {"value": str(result)[:100]}


class StepContext:
    """Lightweight step context for decorator-based tracing."""
    
    def __init__(
        self,
        run_id: str,
        name: str,
        kind: str,
        parent_step_id: Optional[str] = None,
    ):
        self.step_id = f"step-{uuid.uuid4().hex[:12]}"
        self.run_id = run_id
        self.name = name
        self.kind = kind
        self.parent_step_id = parent_step_id
        self.started_at = datetime.utcnow()
        
        self._input_count: Optional[int] = None
        self._output_count: Optional[int] = None
        self._metrics: dict[str, Any] = {}
        self._drops: dict[str, str] = {}  # id -> reason
        self._scores: dict[str, float] = {}  # id -> score
        self._artifacts: list[dict] = []
        self._input_items: list[dict] = []
        self._output_items: list[dict] = []
        self._token = None
    
    def _start(self, input_args: tuple = ()):
        """Start the step, capture input."""
        # Auto-detect input from first list argument
        for arg in input_args:
            if isinstance(arg, list):
                self._input_items = arg
                self._input_count = len(arg)
                break
    
    def _end(self, result: Any = None):
        """End the step, capture output."""
        from zenray.models import StepData, StepStatus, StepKind, CandidateSetData, CaptureMode, ArtifactData, ArtifactType
        from zenray.client import get_client
        from zenray.config import is_enabled
        
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)
        
        # Auto-detect output from return value
        if isinstance(result, list):
            self._output_items = result
            self._output_count = len(result)
        
        if not is_enabled():
            return
        
        # Build candidate set if we have data
        candidate_set = None
        if self._input_count is not None or self._output_count is not None:
            candidate_set = self._build_candidate_set()
        
        # Build artifacts
        artifacts = None
        if self._artifacts:
            artifacts = [
                ArtifactData(
                    artifact_id=f"{self.step_id}_{a['type']}_{uuid.uuid4().hex[:8]}",
                    step_id=self.step_id,
                    type=ArtifactType(a["type"]),
                    content=a["content"],
                )
                for a in self._artifacts
            ]
        
        step_data = StepData(
            step_id=self.step_id,
            run_id=self.run_id,
            parent_step_id=self.parent_step_id,
            kind=StepKind(self.kind),
            name=self.name,
            input_count=self._input_count,
            output_count=self._output_count,
            status=StepStatus.SUCCESS,
            duration_ms=duration_ms,
            started_at=self.started_at,
            ended_at=ended_at,
            metrics=self._metrics if self._metrics else None,
            candidate_set=candidate_set,
            artifacts=artifacts,
        )
        get_client().enqueue_step(step_data)
    
    def _fail(self, error: Exception):
        """End the step with failure."""
        from zenray.models import StepData, StepStatus, StepKind
        from zenray.client import get_client
        from zenray.config import is_enabled
        
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)
        
        if not is_enabled():
            return
        
        step_data = StepData(
            step_id=self.step_id,
            run_id=self.run_id,
            parent_step_id=self.parent_step_id,
            kind=StepKind(self.kind),
            name=self.name,
            input_count=self._input_count,
            output_count=self._output_count,
            status=StepStatus.FAILURE,
            duration_ms=duration_ms,
            started_at=self.started_at,
            ended_at=ended_at,
            metrics={"error": str(error), "error_type": type(error).__name__},
        )
        get_client().enqueue_step(step_data)
    
    def _build_candidate_set(self):
        """Build candidate set data from recorded information."""
        from zenray.models import CandidateSetData, CaptureMode
        from zenray.config import get_config
        from collections import Counter
        import json
        
        mode = CaptureMode.TOP_K
        top_k = get_config().top_k
        
        data = CandidateSetData(
            mode=mode,
            input_count=self._input_count or 0,
            output_count=self._output_count or 0,
        )
        
        # Reason histogram
        if self._drops:
            data.reason_histogram = dict(Counter(self._drops.values()))
        
        # Score histogram
        if self._scores:
            data.score_histogram = self._build_score_histogram()
        
        # Top kept (from output) - serialize to ensure clean dicts
        if self._output_items:
            data.top_kept = [self._serialize_item(c) for c in self._output_items[:top_k]]
        
        # Top dropped
        if self._input_items and self._output_items:
            output_ids = {self._get_id(c) for c in self._output_items}
            dropped = [c for c in self._input_items if self._get_id(c) not in output_ids]
            if dropped:
                # Sort by score if available
                if self._scores:
                    dropped.sort(key=lambda c: self._scores.get(self._get_id(c), 0), reverse=True)
                data.top_dropped = [self._serialize_item(c) for c in dropped[:top_k]]
        
        # Dropped by reason
        if self._drops and self._input_items:
            data.dropped_by_reason = self._get_dropped_by_reason()
        
        return data
    
    def _build_score_histogram(self) -> dict[str, int]:
        """Build score distribution histogram."""
        if not self._scores:
            return {}
        
        scores = list(self._scores.values())
        min_s, max_s = min(scores), max(scores)
        
        if min_s == max_s:
            return {f"{min_s:.2f}": len(scores)}
        
        bucket_size = (max_s - min_s) / 5
        histogram: dict[str, int] = {}
        
        for s in scores:
            bucket_idx = min(4, int((s - min_s) / bucket_size))
            bucket_start = min_s + bucket_idx * bucket_size
            bucket_end = bucket_start + bucket_size
            bucket_key = f"{bucket_start:.2f}-{bucket_end:.2f}"
            histogram[bucket_key] = histogram.get(bucket_key, 0) + 1
        
        return histogram
    
    def _get_dropped_by_reason(self) -> Optional[dict[str, list[dict]]]:
        """Group dropped candidates by reason."""
        if not self._drops or not self._input_items:
            return None
        
        output_ids = {self._get_id(c) for c in self._output_items}
        result: dict[str, list[dict]] = {}
        
        for c in self._input_items:
            cid = self._get_id(c)
            if cid not in output_ids and cid in self._drops:
                reason = self._drops[cid]
                result.setdefault(reason, []).append(self._serialize_item(c))
        
        return result if result else None
    
    def _serialize_item(self, item: Any) -> dict:
        """Serialize an item to a clean dict for Pydantic."""
        import json
        if isinstance(item, dict):
            # Round-trip through JSON to ensure clean serialization
            try:
                return json.loads(json.dumps(item, default=str))
            except (TypeError, ValueError):
                return {"id": self._get_id(item), "_serialization_error": True}
        if hasattr(item, "__dict__"):
            try:
                return json.loads(json.dumps(item.__dict__, default=str))
            except (TypeError, ValueError):
                return {"id": self._get_id(item), "_serialization_error": True}
        return {"value": str(item)}
    
    def _get_id(self, item: Any) -> str:
        """Extract ID from an item."""
        if isinstance(item, dict):
            return item.get("id", item.get("_id", str(id(item))))
        if hasattr(item, "id"):
            return str(item.id)
        return str(id(item))


# --- Context Access Functions ---

def get_current_run() -> Optional[RunContext]:
    """Get the current active run context."""
    return _current_run.get()


def get_current_step() -> Optional[StepContext]:
    """Get the current active step context."""
    return _current_step.get()


def set_current_run(run: Optional[RunContext]) -> Any:
    """Set the current run context, returns token for reset."""
    return _current_run.set(run)


def set_current_step(step: Optional[StepContext]) -> Any:
    """Set the current step context, returns token for reset."""
    return _current_step.set(step)


def reset_current_run(token: Any):
    """Reset run context to previous value."""
    _current_run.reset(token)


def reset_current_step(token: Any):
    """Reset step context to previous value."""
    _current_step.reset(token)

