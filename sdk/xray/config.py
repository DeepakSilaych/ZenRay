"""
Environment-based configuration for X-Ray SDK.

Reads from environment variables:
- XRAY_ENDPOINT: Server endpoint (default: http://localhost:8000)
- XRAY_DISABLED: Set to "true" to disable all tracing
- XRAY_SAMPLE_RATE: Float 0-1 for sampling (default: 1.0 = 100%)
- XRAY_BATCH_SIZE: Batch size for flushing (default: 10)
- XRAY_FLUSH_INTERVAL: Seconds between flushes (default: 1.0)
- XRAY_TOP_K: Number of top candidates to capture (default: 10)
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class XRayConfig:
    endpoint: str = "http://localhost:8000"
    disabled: bool = False
    sample_rate: float = 1.0
    batch_size: int = 10
    flush_interval: float = 1.0
    fail_open: bool = True
    top_k: int = 10  # Number of top kept/dropped candidates to capture


_config: Optional[XRayConfig] = None


def get_config() -> XRayConfig:
    """Get current configuration."""
    global _config
    if _config is None:
        _config = XRayConfig()
    return _config


def init(
    endpoint: Optional[str] = None,
    disabled: Optional[bool] = None,
    sample_rate: Optional[float] = None,
    top_k: Optional[int] = None,
    **kwargs,
):
    """
    Initialize X-Ray SDK.
    
    Reads from environment variables if not explicitly provided:
    - XRAY_ENDPOINT
    - XRAY_DISABLED
    - XRAY_SAMPLE_RATE
    - XRAY_TOP_K
    
    Example:
        xray.init()  # reads from env
        xray.init(endpoint="http://myserver:8000")
        xray.init(top_k=20)  # capture more candidates
    """
    global _config
    
    # Read from env with fallbacks
    _endpoint = endpoint or os.getenv("XRAY_ENDPOINT", "http://localhost:8000")
    _disabled = disabled if disabled is not None else os.getenv("XRAY_DISABLED", "").lower() == "true"
    _sample_rate = sample_rate if sample_rate is not None else float(os.getenv("XRAY_SAMPLE_RATE", "1.0"))
    _batch_size = int(os.getenv("XRAY_BATCH_SIZE", "10"))
    _flush_interval = float(os.getenv("XRAY_FLUSH_INTERVAL", "1.0"))
    _top_k = top_k if top_k is not None else int(os.getenv("XRAY_TOP_K", "10"))
    
    _config = XRayConfig(
        endpoint=_endpoint,
        disabled=_disabled,
        sample_rate=_sample_rate,
        batch_size=kwargs.get("batch_size", _batch_size),
        flush_interval=kwargs.get("flush_interval", _flush_interval),
        fail_open=kwargs.get("fail_open", True),
        top_k=_top_k,
    )
    
    # Initialize the client with new config
    if not _disabled:
        from xray.client import configure
        configure(
            endpoint=_config.endpoint,
            batch_size=_config.batch_size,
            flush_interval=_config.flush_interval,
            fail_open=_config.fail_open,
        )
    
    return _config


def is_enabled() -> bool:
    """Check if tracing is enabled."""
    cfg = get_config()
    return not cfg.disabled


def should_sample() -> bool:
    """Check if this request should be sampled."""
    import random
    cfg = get_config()
    if cfg.disabled:
        return False
    if cfg.sample_rate >= 1.0:
        return True
    return random.random() < cfg.sample_rate

