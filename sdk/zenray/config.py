"""
Environment-based configuration for ZenRay SDK.

Reads from environment variables:
- ZENRAY_API_KEY: API key for authentication (required)
- ZENRAY_ENDPOINT: Server endpoint (default: http://localhost:8000)
- ZENRAY_DISABLED: Set to "true" to disable all tracing
- ZENRAY_SAMPLE_RATE: Float 0-1 for sampling (default: 1.0 = 100%)
- ZENRAY_BATCH_SIZE: Batch size for flushing (default: 10)
- ZENRAY_FLUSH_INTERVAL: Seconds between flushes (default: 1.0)
- ZENRAY_TOP_K: Number of top candidates to capture (default: 10)

Legacy XRAY_* prefixes are also supported for backwards compatibility.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class XRayConfig:
    endpoint: str = "http://localhost:8000"
    api_key: Optional[str] = None
    disabled: bool = False
    sample_rate: float = 1.0
    batch_size: int = 10
    flush_interval: float = 1.0
    fail_open: bool = True
    top_k: int = 10  # Number of top kept/dropped candidates to capture


_config: Optional[XRayConfig] = None


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get env var with ZENRAY_ or XRAY_ prefix."""
    return os.getenv(f"ZENRAY_{name}") or os.getenv(f"XRAY_{name}") or default


def get_config() -> XRayConfig:
    """Get current configuration."""
    global _config
    if _config is None:
        _config = XRayConfig()
    return _config


def init(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    disabled: Optional[bool] = None,
    sample_rate: Optional[float] = None,
    top_k: Optional[int] = None,
    **kwargs,
):
    """
    Initialize ZenRay SDK.
    
    Args:
        api_key: API key for authentication. Required for ingestion.
                 Can also be set via ZENRAY_API_KEY env var.
        endpoint: Server endpoint URL.
        disabled: Set to True to disable tracing.
        sample_rate: Float 0-1 for request sampling.
        top_k: Number of top candidates to capture.
    
    Reads from environment variables if not explicitly provided:
    - ZENRAY_API_KEY (required)
    - ZENRAY_ENDPOINT
    - ZENRAY_DISABLED
    - ZENRAY_SAMPLE_RATE
    - ZENRAY_TOP_K
    
    Example:
        import xray
        
        xray.init(api_key="zenray_xxxxx")  # explicit key
        xray.init()  # reads from ZENRAY_API_KEY env var
    """
    global _config
    
    # Read from env with fallbacks
    _api_key = api_key or _get_env("API_KEY")
    _endpoint = endpoint or _get_env("ENDPOINT", "http://localhost:8000")
    _disabled = disabled if disabled is not None else _get_env("DISABLED", "").lower() == "true"
    _sample_rate = sample_rate if sample_rate is not None else float(_get_env("SAMPLE_RATE", "1.0"))
    _batch_size = int(_get_env("BATCH_SIZE", "10"))
    _flush_interval = float(_get_env("FLUSH_INTERVAL", "1.0"))
    _top_k = top_k if top_k is not None else int(_get_env("TOP_K", "10"))
    
    # Warn if no API key
    if not _api_key and not _disabled:
        import warnings
        warnings.warn(
            "ZenRay SDK initialized without API key. "
            "Set ZENRAY_API_KEY env var or pass api_key to init(). "
            "Ingestion will fail without authentication.",
            UserWarning
        )
    
    _config = XRayConfig(
        endpoint=_endpoint,
        api_key=_api_key,
        disabled=_disabled,
        sample_rate=_sample_rate,
        batch_size=kwargs.get("batch_size", _batch_size),
        flush_interval=kwargs.get("flush_interval", _flush_interval),
        fail_open=kwargs.get("fail_open", True),
        top_k=_top_k,
    )
    
    # Initialize the client with new config
    if not _disabled:
        from zenray.client import configure
        configure(
            endpoint=_config.endpoint,
            api_key=_config.api_key,
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
