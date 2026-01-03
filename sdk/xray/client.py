import httpx
from typing import Optional
from threading import Thread
from queue import Queue, Empty
import time
import atexit

from xray.models import IngestPayload, RunData, StepData

class XRayClient:
    """X-Ray SDK client for instrumenting pipelines."""
    
    def __init__(
        self,
        endpoint: str = "http://localhost:8000",
        batch_size: int = 10,
        flush_interval: float = 1.0,
        max_retries: int = 3,
        fail_open: bool = True,  # Never block production
    ):
        self.endpoint = endpoint.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.fail_open = fail_open
        
        self._queue: Queue = Queue(maxsize=10000)
        self._http = httpx.Client(timeout=10.0)
        self._running = True
        
        # Background flush thread
        self._flush_thread = Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
        
        atexit.register(self.shutdown)
    
    def _flush_loop(self):
        """Background thread that flushes queued events."""
        while self._running:
            time.sleep(self.flush_interval)
            self._flush()
    
    def _flush(self):
        """Flush queued events to backend."""
        runs, steps = [], []
        
        # Drain queue up to batch_size
        for _ in range(self.batch_size):
            try:
                event = self._queue.get_nowait()
                if isinstance(event, RunData):
                    runs.append(event)
                elif isinstance(event, StepData):
                    steps.append(event)
            except Empty:
                break
        
        if not runs and not steps:
            return
        
        payload = IngestPayload(runs=runs or None, steps=steps or None)
        self._send(payload)
    
    def _send(self, payload: IngestPayload):
        """Send payload to backend with retries."""
        for attempt in range(self.max_retries):
            try:
                resp = self._http.post(
                    f"{self.endpoint}/ingest",
                    json=payload.model_dump(mode="json", exclude_none=True),
                )
                if resp.status_code == 200:
                    return
            except Exception as e:
                if not self.fail_open:
                    raise
                # Log error but don't block
                pass
            
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
    
    def enqueue_run(self, run: RunData):
        """Queue a run event for sending."""
        try:
            self._queue.put_nowait(run)
        except:
            if not self.fail_open:
                raise
    
    def enqueue_step(self, step: StepData):
        """Queue a step event for sending."""
        try:
            self._queue.put_nowait(step)
        except:
            if not self.fail_open:
                raise
    
    def flush(self):
        """Force flush all queued events."""
        while not self._queue.empty():
            self._flush()
    
    def shutdown(self):
        """Shutdown client, flushing remaining events."""
        self._running = False
        self.flush()
        self._http.close()

# Global default client
_default_client: Optional[XRayClient] = None

def get_client() -> XRayClient:
    global _default_client
    if _default_client is None:
        _default_client = XRayClient()
    return _default_client

def configure(endpoint: str = "http://localhost:8000", **kwargs):
    global _default_client
    _default_client = XRayClient(endpoint=endpoint, **kwargs)

