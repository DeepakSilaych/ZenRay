# Python SDK Overview

The Python SDK instruments your pipeline with minimal code and emits:

- **Run events** (start/end/failure)
- **Step events** (timing, metrics, candidate set summaries, artifacts)

## Primary usage style

Decorator-based instrumentation:

- `@xray.pipeline(...)`
- `@xray.step(...)`
- helpers like `xray.drop(...)`, `xray.score(...)`, `xray.metric(...)`, `xray.artifact(...)`, `xray.tag(...)`

## Candidate capture (top-k, histograms)

The SDK captures “top kept/dropped” candidates. The **top-k** is configurable via:

- env: `XRAY_TOP_K`
- code: `xray.init(top_k=...)`

See details: [`configuration.md`](./configuration.md)

## Examples

See: [`examples.md`](./examples.md)

## Where to make changes

- **Public SDK API**: `sdk/xray/__init__.py`
- **Config/env parsing**: `sdk/xray/config.py`
- **Batching + HTTP sending**: `sdk/xray/client.py`
- **Decorators**: `sdk/xray/decorators.py`
- **Run/step capture**: `sdk/xray/context.py`
- **Helpers inside steps**: `sdk/xray/helpers.py`
- **CandidateSet capture (legacy/explicit)**: `sdk/xray/candidates.py`
- **Wire models**: `sdk/xray/models.py`

## Architecture context

The SDK is the “producer” of run/step events. It should be **fail-open** and low-overhead, and it sends data to backend ingest.

- Full flow: [`../architecture.md`](../architecture.md)


