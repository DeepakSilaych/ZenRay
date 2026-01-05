"""
Decorator-based API for X-Ray tracing.

Provides @pipeline and @step decorators for minimal-code instrumentation.
"""
import functools
from typing import Optional, Callable, Any, TypeVar, ParamSpec

from zenray.context import (
    RunContext, StepContext,
    get_current_run, get_current_step,
    set_current_run, set_current_step,
    reset_current_run, reset_current_step,
)
from zenray.config import should_sample

P = ParamSpec("P")
R = TypeVar("R")


def pipeline(
    name: str,
    version: Optional[str] = None,
    tags: Optional[dict[str, str]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to mark a function as a pipeline entry point.
    
    Automatically:
    - Creates a run when the function is called
    - Captures input from arguments
    - Captures output from return value
    - Tracks timing and status
    
    Example:
        @xray.pipeline("my-pipeline", version="v1.0")
        def process(query: str):
            return do_stuff(query)
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Check sampling
            if not should_sample():
                return fn(*args, **kwargs)
            
            # Create run context
            run = RunContext(
                pipeline_name=name,
                version=version,
                tags=tags,
            )
            
            # Set as current run
            token = set_current_run(run)
            
            try:
                run._start(args, kwargs)
                result = fn(*args, **kwargs)
                run._end(result)
                return result
            except Exception as e:
                run._fail(e)
                raise
            finally:
                reset_current_run(token)
                # Flush to ensure data is sent
                from zenray.client import get_client
                from zenray.config import is_enabled
                if is_enabled():
                    get_client().flush()
        
        return wrapper
    return decorator


def step(
    kind: str,
    name: Optional[str] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to mark a function as a pipeline step.
    
    Automatically:
    - Links to the current run
    - Captures input count from list arguments
    - Captures output count from list return values
    - Tracks timing and status
    - Records drops and scores via helper functions
    
    Example:
        @xray.step("FILTER")
        def filter_items(items: list[dict]) -> list[dict]:
            return [i for i in items if i["score"] > 0.5]
    
    Args:
        kind: Step kind (RETRIEVE, FILTER, RANK, LLM_CALL, JUDGE, etc.)
        name: Optional step name (defaults to function name)
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Get current run - if none, just run the function
            run = get_current_run()
            if run is None:
                return fn(*args, **kwargs)
            
            # Get parent step (for nesting)
            parent_step = get_current_step()
            parent_step_id = parent_step.step_id if parent_step else None
            
            # Create step context
            step_ctx = StepContext(
                run_id=run.run_id,
                name=name or fn.__name__,
                kind=kind,
                parent_step_id=parent_step_id,
            )
            
            # Set as current step
            token = set_current_step(step_ctx)
            
            try:
                step_ctx._start(args)
                result = fn(*args, **kwargs)
                step_ctx._end(result)
                return result
            except Exception as e:
                step_ctx._fail(e)
                raise
            finally:
                reset_current_step(token)
        
        return wrapper
    return decorator


# --- Async Support ---

def async_pipeline(
    name: str,
    version: Optional[str] = None,
    tags: Optional[dict[str, str]] = None,
) -> Callable:
    """Async version of @pipeline decorator."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            if not should_sample():
                return await fn(*args, **kwargs)
            
            run = RunContext(
                pipeline_name=name,
                version=version,
                tags=tags,
            )
            
            token = set_current_run(run)
            
            try:
                run._start(args, kwargs)
                result = await fn(*args, **kwargs)
                run._end(result)
                return result
            except Exception as e:
                run._fail(e)
                raise
            finally:
                reset_current_run(token)
                from zenray.client import get_client
                from zenray.config import is_enabled
                if is_enabled():
                    get_client().flush()
        
        return wrapper
    return decorator


def async_step(
    kind: str,
    name: Optional[str] = None,
) -> Callable:
    """Async version of @step decorator."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            run = get_current_run()
            if run is None:
                return await fn(*args, **kwargs)
            
            parent_step = get_current_step()
            parent_step_id = parent_step.step_id if parent_step else None
            
            step_ctx = StepContext(
                run_id=run.run_id,
                name=name or fn.__name__,
                kind=kind,
                parent_step_id=parent_step_id,
            )
            
            token = set_current_step(step_ctx)
            
            try:
                step_ctx._start(args)
                result = await fn(*args, **kwargs)
                step_ctx._end(result)
                return result
            except Exception as e:
                step_ctx._fail(e)
                raise
            finally:
                reset_current_step(token)
        
        return wrapper
    return decorator

