# ZenRay Python SDK

Instrument your ML pipelines with simple decorators.

---

## Overview

The ZenRay SDK provides:

- **`@xray.pipeline`** — Mark your pipeline entry point
- **`@xray.step`** — Track individual processing stages
- **`xray.drop()`** — Record why candidates were filtered
- **`xray.score()`** — Capture ranking scores
- **`xray.tag()`** — Add custom metadata

All data is sent asynchronously with <1ms overhead.

---

## Installation

### From Source (Development)

```bash
cd sdk
pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install zenray
```

---

## Quick Start

```python
import xray

@xray.pipeline("my-rag-pipeline")
def answer(question: str):
    docs = retrieve(question)
    filtered = filter_docs(docs)
    return generate(question, filtered)

@xray.step("RETRIEVE")
def retrieve(question: str):
    # Your retrieval logic
    return vector_db.search(question, k=100)

@xray.step("FILTER")
def filter_docs(docs):
    for doc in docs:
        if doc.score < 0.3:
            xray.drop(doc, "low_relevance")
            continue
        yield doc
```

---

## API Reference

### `@xray.pipeline(name)`

Marks the entry point of your pipeline. Creates a new run in the dashboard.

```python
@xray.pipeline("product-search")
def search(query: str, user_id: str):
    ...
```

### `@xray.step(name)`

Tracks a processing stage within a pipeline.

```python
@xray.step("RERANK")
def rerank(docs):
    ...
```

### `xray.drop(item, reason)`

Records why an item was filtered out.

```python
if doc.score < threshold:
    xray.drop(doc, "below_threshold")
```

### `xray.score(item, score)`

Captures a ranking score for an item.

```python
for doc in docs:
    score = model.predict(doc)
    xray.score(doc, score)
```

### `xray.tag(key, value)`

Adds custom metadata to the current run.

```python
xray.tag("user_id", user_id)
xray.tag("model_version", "v2.1")
```

---

## Configuration

Set via environment variables:

| Variable           | Default               | Description             |
| ------------------ | --------------------- | ----------------------- |
| `XRAY_ENDPOINT`    | http://localhost:8000 | ZenRay server URL       |
| `XRAY_DISABLED`    | false                 | Disable all tracing     |
| `XRAY_SAMPLE_RATE` | 1.0                   | Sampling rate (0.0-1.0) |
| `XRAY_TOP_K`       | 10                    | Max candidates per step |

---

## Examples

Run the example pipelines:

```bash
cd sdk

# Set the server endpoint
export XRAY_ENDPOINT="http://localhost:8000"

# Run examples
python examples/rag_document_retrieval.py
python examples/ecommerce_search.py
python examples/recommendation_system.py
python examples/content_moderation.py
```

### Available Examples

| Example                     | Description                   |
| --------------------------- | ----------------------------- |
| `minimal_api_demo.py`       | Basic SDK usage               |
| `rag_document_retrieval.py` | RAG pipeline with filtering   |
| `ecommerce_search.py`       | Product search with ranking   |
| `recommendation_system.py`  | User recommendations          |
| `content_moderation.py`     | Content filtering pipeline    |
| `job_screening_pipeline.py` | Resume screening example      |
| `competitor_selection.py`   | Competitive analysis pipeline |

---

## Project Structure

```
sdk/
├── xray/
│   ├── __init__.py      # Public API exports
│   ├── decorators.py    # @pipeline, @step decorators
│   ├── context.py       # Run/step context management
│   ├── client.py        # HTTP client for server
│   ├── models.py        # Data models
│   ├── candidates.py    # Candidate tracking
│   ├── config.py        # Configuration
│   └── helpers.py       # Utility functions
├── examples/            # Example pipelines
├── requirements.txt
└── pyproject.toml
```

---

## Development

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy xray/
```
