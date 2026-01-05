# ZenRay

[![PyPI version](https://badge.fury.io/py/zenray.svg)](https://badge.fury.io/py/zenray)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Observability for ML/LLM pipelines.** Debug candidate drop-off and track decision context with minimal code changes.

---

## Installation

```bash
pip install zenray
```

---

## Quick Start

```python
import zenray

# Initialize with your API key
zenray.init(api_key="zenray_xxxxx")  # or set ZENRAY_API_KEY env var

@zenray.pipeline("my-rag-pipeline")
def answer(question: str):
    docs = retrieve(question)
    filtered = filter_docs(docs)
    return generate(question, filtered)

@zenray.step("RETRIEVE")
def retrieve(question: str):
    return vector_db.search(question, k=100)

@zenray.step("FILTER")
def filter_docs(docs):
    kept = []
    for doc in docs:
        if doc.score < 0.3:
            zenray.drop(doc, "low_relevance")  # Track why items are dropped
        else:
            kept.append(doc)
    return kept

@zenray.step("RANK")
def rank_docs(docs):
    for doc in docs:
        zenray.score(doc, doc.relevance)  # Track scores
    return sorted(docs, key=lambda d: d.relevance, reverse=True)[:10]
```

View traces at [zenray.live](https://zenray.live) or self-host.

---

## Features

| Feature                 | Description                         |
| ----------------------- | ----------------------------------- |
| **`@zenray.pipeline`**  | Mark pipeline entry points          |
| **`@zenray.step`**      | Track processing stages             |
| **`zenray.drop()`**     | Record why candidates were filtered |
| **`zenray.score()`**    | Capture ranking scores              |
| **`zenray.tag()`**      | Add custom metadata                 |
| **`zenray.artifact()`** | Attach prompts, responses, etc.     |

All data is sent asynchronously with **<1ms overhead**.

---

## API Reference

### Initialization

```python
zenray.init(
    api_key="zenray_xxxxx",     # Required (or ZENRAY_API_KEY env var)
    endpoint="http://localhost:8000",  # Server URL
    disabled=False,              # Disable tracing
    sample_rate=1.0,            # 0-1 sampling rate
)
```

### Decorators

```python
@zenray.pipeline("pipeline-name", version="v1.0")
def my_pipeline(input):
    ...

@zenray.step("RETRIEVE")  # or FILTER, RANK, LLM_CALL, etc.
def my_step(data):
    ...
```

### Tracking Functions

```python
# Record dropped candidates
zenray.drop(item, "reason")

# Record scores
zenray.score(item, 0.95)

# Custom metrics
zenray.metric("latency_ms", 150)

# Attach artifacts (prompts, responses)
zenray.artifact("prompt", "What is the capital of France?")
zenray.artifact("response", "Paris")

# Add tags to runs
zenray.tag("user_id", "u123")
zenray.tag("model", "gpt-4")
```

### Error Handling

```python
# Check for errors
if zenray.get_last_error():
    print(f"Error: {zenray.get_last_error()}")

# Get stats
stats = zenray.get_stats()
print(f"Success: {stats['success_count']}, Errors: {stats['error_count']}")
```

---

## Configuration

| Environment Variable | Default                 | Description             |
| -------------------- | ----------------------- | ----------------------- |
| `ZENRAY_API_KEY`     | -                       | API key (required)      |
| `ZENRAY_ENDPOINT`    | `http://localhost:8000` | Server URL              |
| `ZENRAY_DISABLED`    | `false`                 | Disable tracing         |
| `ZENRAY_SAMPLE_RATE` | `1.0`                   | Sampling rate (0-1)     |
| `ZENRAY_TOP_K`       | `10`                    | Max candidates per step |

---

## Step Kinds

| Kind        | Use Case                |
| ----------- | ----------------------- |
| `RETRIEVE`  | Database/vector search  |
| `FILTER`    | Candidate filtering     |
| `RANK`      | Scoring/reranking       |
| `LLM_CALL`  | LLM inference           |
| `JUDGE`     | LLM-as-judge evaluation |
| `SELECT`    | Final selection         |
| `TRANSFORM` | Data transformation     |
| `TOOL_CALL` | External tool calls     |

---

## Async Support

```python
@zenray.async_pipeline("async-pipeline")
async def my_async_pipeline(input):
    ...

@zenray.async_step("LLM_CALL")
async def call_llm(prompt):
    ...
```

---

## Self-Hosting

```bash
# Clone the repo
git clone https://github.com/DeepakSilaych/ZenRay
cd ZenRay

# Start services
docker compose up -d

# Access dashboard at http://localhost:5174
```

---

## Links

- **Dashboard**: [zenray.live](https://zenray.live)
- **Documentation**: [zenray.live/docs](https://zenray.live/docs)
- **GitHub**: [github.com/DeepakSilaych/ZenRay](https://github.com/DeepakSilaych/ZenRay)

---

## License

MIT License - see [LICENSE](LICENSE) for details.
