import httpx
import logging
from typing import Optional
from threading import Thread, Lock
from queue import Queue, Empty
import time
import atexit

from zenray.models import IngestPayload, RunData, StepData

logger = logging.getLogger("zenray")


class ZenRayError(Exception):
    """Base exception for ZenRay SDK errors."""
    pass


class AuthenticationError(ZenRayError):
    """Raised when API key authentication fails."""
    pass


class IngestError(ZenRayError):
    """Raised when data ingestion fails."""
    pass


class XRayClient:
    """ZenRay SDK client for instrumenting pipelines."""
    
    def __init__(
        self,
        endpoint: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 1.0,
        max_retries: int = 3,
        fail_open: bool = True,  # Never block production by default
        on_error: Optional[callable] = None,  # Error callback
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.fail_open = fail_open
        self.on_error = on_error
        
        self._queue: Queue = Queue(maxsize=10000)
        self._error_lock = Lock()
        self._last_error: Optional[Exception] = None
        self._error_count = 0
        self._success_count = 0
        
        # Build headers with API key
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._http = httpx.Client(timeout=10.0, headers=headers)
        self._running = True
        
        # Background flush thread
        self._flush_thread = Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
        
        atexit.register(self.shutdown)
    
    def _record_error(self, error: Exception):
        """Record an error for later inspection."""
        with self._error_lock:
            self._last_error = error
            self._error_count += 1
        
        logger.warning(f"ZenRay SDK error: {error}")
        
        if self.on_error:
            try:
                self.on_error(error)
            except:
                pass
    
    def _record_success(self, runs: int = 0, steps: int = 0):
        """Record successful ingestion."""
        with self._error_lock:
            self._success_count += runs + steps
    
    @property
    def last_error(self) -> Optional[Exception]:
        """Get the last error that occurred."""
        with self._error_lock:
            return self._last_error
    
    @property
    def stats(self) -> dict:
        """Get client statistics."""
        with self._error_lock:
            return {
                "success_count": self._success_count,
                "error_count": self._error_count,
                "last_error": str(self._last_error) if self._last_error else None,
                "queue_size": self._queue.qsize(),
            }
    
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
        self._send(payload, len(runs), len(steps))
    
    def _send(self, payload: IngestPayload, runs_count: int = 0, steps_count: int = 0):
        """Send payload to backend with retries."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                resp = self._http.post(
                    f"{self.endpoint}/ingest",
                    json=payload.model_dump(mode="json", exclude_none=True),
                )
                
                if resp.status_code == 200:
                    self._record_success(runs_count, steps_count)
                    return
                
                elif resp.status_code == 401:
                    # Authentication failed - don't retry
                    error = AuthenticationError(
                        "Invalid API key. Check your ZENRAY_API_KEY or pass api_key to init()."
                    )
                    self._record_error(error)
                    if not self.fail_open:
                        raise error
                    return
                
                elif resp.status_code == 400:
                    # Bad request - don't retry
                    try:
                        detail = resp.json().get("detail", "Bad request")
                    except:
                        detail = resp.text
                    error = IngestError(f"Bad request: {detail}")
                    self._record_error(error)
                    if not self.fail_open:
                        raise error
                    return
                
                elif resp.status_code >= 500:
                    # Server error - retry
                    last_error = IngestError(f"Server error: {resp.status_code}")
                
                else:
                    last_error = IngestError(f"Unexpected status: {resp.status_code}")
                    
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = IngestError(f"Connection error: {e}")
            except AuthenticationError:
                raise
            except Exception as e:
                last_error = IngestError(f"Request failed: {e}")
            
            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
        
        # All retries exhausted
        if last_error:
            self._record_error(last_error)
            if not self.fail_open:
                raise last_error
    
    def enqueue_run(self, run: RunData):
        """Queue a run event for sending."""
        try:
            self._queue.put_nowait(run)
        except Exception as e:
            error = IngestError(f"Queue full, dropping run: {e}")
            self._record_error(error)
            if not self.fail_open:
                raise error
    
    def enqueue_step(self, step: StepData):
        """Queue a step event for sending."""
        try:
            self._queue.put_nowait(step)
        except Exception as e:
            error = IngestError(f"Queue full, dropping step: {e}")
            self._record_error(error)
            if not self.fail_open:
                raise error
    
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


def configure(
    endpoint: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    **kwargs
):
    global _default_client
    _default_client = XRayClient(endpoint=endpoint, api_key=api_key, **kwargs)
