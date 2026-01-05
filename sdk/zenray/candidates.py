from typing import Any, Optional, Callable, TYPE_CHECKING
from collections import Counter

from zenray.models import CandidateSetData, CaptureMode

if TYPE_CHECKING:
    from zenray.step import Step

class CandidateSet:
    """Helper for recording candidate set transitions with automatic mode selection."""
    
    # Thresholds for automatic mode selection
    SUMMARY_THRESHOLD = 100  # Use SUMMARY mode if candidates > this
    
    def __init__(
        self,
        step: "Step",
        mode: Optional[CaptureMode] = None,
        top_k: Optional[int] = None,
    ):
        from zenray.config import get_config
        
        self._step = step
        self._mode = mode
        self._top_k = top_k if top_k is not None else get_config().top_k
        
        self._input_candidates: list[dict[str, Any]] = []
        self._output_candidates: list[dict[str, Any]] = []
        self._drop_reasons: dict[str, str] = {}  # candidate_id -> reason
        self._scores: dict[str, float] = {}  # candidate_id -> score
    
    def record_input(
        self,
        candidates: list[dict[str, Any]],
        id_field: str = "id",
    ):
        """Record input candidates."""
        self._input_candidates = candidates
        self._step.set_input_count(len(candidates))
    
    def record_output(
        self,
        candidates: list[dict[str, Any]],
        id_field: str = "id",
    ):
        """Record output candidates."""
        self._output_candidates = candidates
        self._step.set_output_count(len(candidates))
    
    def record_drop_reasons(self, reasons: dict[str, str]):
        """Record why candidates were dropped: {candidate_id: reason}."""
        self._drop_reasons.update(reasons)
    
    def record_scores(self, scores: dict[str, float]):
        """Record candidate scores: {candidate_id: score}."""
        self._scores.update(scores)
    
    def to_data(self) -> CandidateSetData:
        """Convert to wire format based on mode."""
        n_in = len(self._input_candidates)
        n_out = len(self._output_candidates)
        
        # Auto-select mode
        mode = self._mode
        if mode is None:
            if n_in > self.SUMMARY_THRESHOLD:
                mode = CaptureMode.SUMMARY
            else:
                mode = CaptureMode.TOP_K
        
        data = CandidateSetData(
            mode=mode,
            input_count=n_in,
            output_count=n_out,
        )
        
        # Reason histogram
        if self._drop_reasons:
            data.reason_histogram = dict(Counter(self._drop_reasons.values()))
        
        # Score histogram (buckets)
        if self._scores:
            data.score_histogram = self._build_score_histogram()
        
        if mode == CaptureMode.SUMMARY:
            # Just histograms + sample
            data.top_kept = self._output_candidates[:3] if self._output_candidates else None
            data.top_dropped = self._get_top_dropped(3)
        
        elif mode == CaptureMode.TOP_K:
            data.top_kept = self._output_candidates[:self._top_k]
            data.top_dropped = self._get_top_dropped(self._top_k)
            data.dropped_by_reason = self._get_dropped_by_reason()
        
        elif mode == CaptureMode.FULL:
            data.full_candidates = self._input_candidates
            data.top_kept = self._output_candidates
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
        
        # 5 buckets
        bucket_size = (max_s - min_s) / 5
        histogram: dict[str, int] = {}
        
        for s in scores:
            bucket_idx = min(4, int((s - min_s) / bucket_size))
            bucket_start = min_s + bucket_idx * bucket_size
            bucket_end = bucket_start + bucket_size
            bucket_key = f"{bucket_start:.2f}-{bucket_end:.2f}"
            histogram[bucket_key] = histogram.get(bucket_key, 0) + 1
        
        return histogram
    
    def _get_top_dropped(self, k: int) -> Optional[list[dict[str, Any]]]:
        """Get top-k dropped candidates (closest to threshold)."""
        output_ids = {c.get("id") for c in self._output_candidates}
        dropped = [c for c in self._input_candidates if c.get("id") not in output_ids]
        
        if not dropped:
            return None
        
        # Sort by score (highest first) if we have scores
        if self._scores:
            dropped.sort(key=lambda c: self._scores.get(c.get("id", ""), 0), reverse=True)
        
        return dropped[:k]
    
    def _get_dropped_by_reason(self) -> Optional[dict[str, list[dict[str, Any]]]]:
        """Group dropped candidates by their drop reason."""
        if not self._drop_reasons:
            return None
        
        output_ids = {c.get("id") for c in self._output_candidates}
        result: dict[str, list[dict[str, Any]]] = {}
        
        for c in self._input_candidates:
            cid = c.get("id")
            if cid not in output_ids and cid in self._drop_reasons:
                reason = self._drop_reasons[cid]
                result.setdefault(reason, []).append(c)
        
        return result if result else None

