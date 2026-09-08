<p align="center">
  <img src="./assets/logo.svg" alt="ZenRay Logo" width="100" height="100">
</p>

<h1 align="center">ZenRay</h1>

<p align="center">
  <strong>Trace every stage of an ML or RAG pipeline and see which candidates got dropped, where, and why.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab.svg?style=flat-square" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61dafb.svg?style=flat-square" alt="React 18">
  <img src="https://img.shields.io/badge/license-MIT-22c55e.svg?style=flat-square" alt="MIT License">
</p>

## Why

A RAG or ranking pipeline retrieves 200 documents, filters them, reranks them, and hands 5 to the LLM. When the answer is wrong, plain logs tell you nothing about the other 195.

ZenRay records each pipeline call as a **run** made of **steps**. Every step keeps its input and output counts, a histogram of drop reasons, a score histogram, the top kept and dropped items, and any prompts or responses you attach. You can then ask the server "where did document X go in run Y" and get its journey step by step.

Instrumentation is two decorators and a few helper calls. Your function signatures and return values stay the same.

## Demo

<!-- TODO: screenshot of the Run detail page with the step timeline and candidate trace -->

<!-- TODO: screenshot of the Step detail page showing reason_histogram and top_dropped -->

Runnable pipelines live under [`sdk/examples/`](./sdk/examples): RAG retrieval, e-commerce search, content moderation, recommendations, job screening. `minimal_api_demo.py` is the smallest.

## Quickstart

Ports used by the defaults in this repo: website `4001`, dashboard `4002`, server `4003`.

**1. Start Postgres, Redis and MinIO**

```bash
cd infra
docker compose -f postgres.yml -f redis.yml -f minio.yml up -d
```

**2. Start the server** (Python 3.11+)

```bash
cd server
cp .env.example .env            # fill XRAY_GOOGLE_CLIENT_ID / _SECRET for dashboard login
pip install -e ".[dev]"
uvicorn app.main:app --port 4003
curl localhost:4003/health      # {"status":"healthy","version":"2.1.0","queue_length":0}
```

Tables are created on startup (`server/app/db.py`), so no migration step.

**3. Start the dashboard and create an API key**

```bash
cd mainapp
npm install
npm run dev                     # http://localhost:4002, proxies /api/* to :4003
```

Log in with Google, open **API Keys**, create one. The full key (`zenray_...`) is shown once.

If you do not want to configure Google OAuth, insert a user and a key directly. The server stores the SHA-256 of the key (`server/app/auth.py`):

```bash
docker exec -i zenray-postgres psql -U xray -d xray <<'SQL'
INSERT INTO users (user_id, email) VALUES ('user_dev', 'dev@example.com');
INSERT INTO api_keys (key_id, user_id, key_name, key_hash)
VALUES ('key_dev', 'user_dev', 'dev', encode(sha256('zenray_dev-key'::bytea), 'hex'));
SQL
```

This key works for `/ingest` and for the query API over curl, but the dashboard UI still needs a Google login.

**4. Install the SDK and run an example**

```bash
cd sdk
pip install -e .
export ZENRAY_API_KEY=zenray_...              # from step 3
export ZENRAY_ENDPOINT=http://localhost:4003  # SDK default is :8000, server default is :4003
python examples/minimal_api_demo.py
```

**5. Verify**

```bash
curl -H "Authorization: Bearer $ZENRAY_API_KEY" localhost:4003/runs
```

or open http://localhost:4002 and click into the `product-search` run.

### Docker

`server/`, `mainapp/` and `web/` each have a Dockerfile (ports 4003, 4002, 4001). Put the server on the compose network from step 1 so service names resolve:

```bash
docker build -t zenray-server server/
docker run --rm -p 4003:4003 --network infra_default \
  -e XRAY_POSTGRES_HOST=postgres -e XRAY_REDIS_HOST=redis \
  -e XRAY_S3_ENDPOINT=http://minio:9000 zenray-server
```

## How it works

```
 your code                 sdk/zenray                    server/app                  storage
 ---------                 ----------                    ----------                  -------
 @zenray.pipeline -> RunContext  --+
 @zenray.step ----> StepContext  --+-> Queue -> flush --> POST /ingest -> Redis list -> worker.py
 zenray.drop/score -> step._drops --+  (10k)   thread     Bearer key     (queue.py)    (50 / poll)
                                       10 / 1s                                            |
                                                                    +---------------------+---------+
                                                                    v                               v
                                                              Postgres (db.py)             MinIO (blob_store.py)
                                                              runs, steps, artifacts,      candidates/{step_id}.json
                                                              users, api_keys              artifacts/{artifact_id}.json
                                                                    ^                               ^
 mainapp :4002 -> /api/* -> vite proxy -> routers/query.py ---------+----- Redis cache (cache.py) ---+
```

1. `@zenray.pipeline` (`sdk/zenray/decorators.py`) creates a `RunContext`, stores it in a `contextvar`, and enqueues a `RunData` with status `RUNNING`. When the function returns it enqueues the same run as `SUCCESS` (or `FAILURE` with the exception) and then calls a blocking `flush()`.
2. `@zenray.step` creates a `StepContext` (`sdk/zenray/context.py`). The first `list` positional argument sets `input_count`; a `list` return value sets `output_count`. `parent_step_id` comes from the enclosing step, so nested steps form a tree.
3. `zenray.drop(item, reason)` and `zenray.score(item, value)` (`sdk/zenray/helpers.py`) write into the current step keyed by the item's `id`. At step end, `_build_candidate_set` turns that into a `reason_histogram`, a 5-bucket `score_histogram`, `top_kept`, `top_dropped` (sorted by score) and `dropped_by_reason`, capped at `ZENRAY_TOP_K` items each.
4. `XRayClient` (`sdk/zenray/client.py`) holds a bounded `Queue(maxsize=10000)`. A daemon thread posts batches of `batch_size` every `flush_interval` seconds to `POST {endpoint}/ingest` with `Authorization: Bearer <api key>`. 5xx and connection errors retry 3 times with backoff; 400 and 401 do not retry.
5. `POST /ingest` (`server/app/routers/ingest.py`) validates the API key hash against `api_keys`, tags the payload with the owner's `user_id`, and `RPUSH`es it to the Redis list `zenray:ingest:queue`. Pass `?sync=true` to write straight to the database instead.
6. `server/app/worker.py` runs as an asyncio task inside the server process. It pops up to 50 payloads every 100 ms, upserts runs and steps into Postgres, writes each candidate set to `candidates/{step_id}.json` and each artifact to `artifacts/{artifact_id}.json` in the S3 bucket, and invalidates the Redis cache for that run.
7. The dashboard (`mainapp/src/api.ts`) calls the query API (`server/app/routers/query.py`). Every query is scoped to the caller's `user_id`. Run lists and details are cached in Redis for 60 s to 1 h depending on run status.

### Data model

Names in code are `Run` and `Step` (the trace and span). Wire format is `sdk/zenray/models.py`; the server mirrors it in `server/app/models.py`.

```
Run                                             Postgres: runs
  run_id, pipeline_name, version
  status: RUNNING | SUCCESS | FAILURE
  started_at, ended_at, tags {k: v}
  input_summary, final_output
  Step[]  (parent_step_id links nesting)        Postgres: steps
    step_id, kind, name
    kind: RETRIEVE | FILTER | RANK | LLM_CALL | JUDGE | SELECT | TRANSFORM | TOOL_CALL
    status: RUNNING | SUCCESS | FAILURE | SKIPPED
    input_count, output_count, duration_ms
    metrics {k: v}                              (zenray.metric)
    candidate_set                               S3: candidates/{step_id}.json
      mode: SUMMARY | TOP_K | FULL
      reason_histogram {reason: n}              (zenray.drop)
      score_histogram {"lo-hi": n}              (zenray.score)
      top_kept[], top_dropped[]
      dropped_by_reason {reason: [items]}
    artifacts[]                                 S3: artifacts/{id}.json, indexed in Postgres
      type: prompt | response | config | ...    (zenray.artifact)
      content
```

### Minimal SDK usage

From [`sdk/examples/minimal_api_demo.py`](./sdk/examples/minimal_api_demo.py), comments and docstrings removed:

```python
import zenray

# Initialize - reads ZENRAY_API_KEY and ZENRAY_ENDPOINT from env
zenray.init()

@zenray.pipeline("product-search", version="v2.0")
def search_products(query: str, max_results: int = 5) -> list[dict]:
    zenray.tag("query", query)
    candidates = retrieve_candidates(query)
    filtered = filter_candidates(candidates)
    ranked = rank_by_relevance(filtered, query)
    return ranked[:max_results]

@zenray.step("RETRIEVE")
def retrieve_candidates(query: str) -> list[dict]:
    zenray.metric("source", "mock_db")
    query_lower = query.lower()
    matches = [
        p for p in PRODUCTS
        if query_lower in p["name"].lower() or query_lower in p["category"].lower()
    ]
    if not matches:
        return PRODUCTS.copy()
    return matches

@zenray.step("FILTER")
def filter_candidates(candidates: list[dict]) -> list[dict]:
    kept = []
    for product in candidates:
        if not product["active"]:
            zenray.drop(product, "inactive")
        elif product["rating"] < 4.0:
            zenray.drop(product, "low_rating")
        else:
            kept.append(product)
    return kept

@zenray.step("RANK")
def rank_by_relevance(candidates: list[dict], query: str) -> list[dict]:
    query_lower = query.lower()
    for product in candidates:
        name_match = 1.0 if query_lower in product["name"].lower() else 0.5
        rating_score = product["rating"] / 5.0
        relevance = (name_match * 0.6) + (rating_score * 0.4)
        zenray.score(product, relevance)
        product["relevance"] = relevance
    return sorted(candidates, key=lambda x: x["relevance"], reverse=True)
```

Items passed to `drop` and `score` need an `id` (dict key `id` or `_id`, or an `.id` attribute). Async code uses `@zenray.async_pipeline` and `@zenray.async_step`.

## Features

| Area | What it does | Where |
| --- | --- | --- |
| Decorators | `@pipeline`, `@step`, `@async_pipeline`, `@async_step`; nested steps via contextvars | `sdk/zenray/decorators.py` |
| Helpers | `drop`, `score`, `metric`, `artifact`, `tag`, `set_input_count`, `set_output_count` | `sdk/zenray/helpers.py` |
| Auto counts | Input count from the first `list` argument, output count from a `list` return | `sdk/zenray/context.py` |
| Candidate sets | Reason histogram, 5-bucket score histogram, top-k kept and dropped, dropped-by-reason | `sdk/zenray/context.py` |
| Sampling | `ZENRAY_SAMPLE_RATE` skips whole runs at the pipeline boundary | `sdk/zenray/config.py` |
| Fail-open client | Bounded queue, background flush, retries with backoff, `get_stats()` and `get_last_error()` | `sdk/zenray/client.py` |
| Async ingest | Redis list plus in-process worker; `?sync=true` bypasses the queue | `server/app/routers/ingest.py`, `worker.py` |
| Query API | `GET /runs`, `/runs/{id}`, `/steps`, `/steps/{id}`, `/steps/{id}/candidates` | `server/app/routers/query.py` |
| Candidate trace | `GET /runs/{id}/trace?q=` matches `id`, `name` or `title` across every step's candidate set | `server/app/routers/query.py` |
| Run compare | `GET /compare?run_a&run_b` diffs steps by name: counts, drop ratio, duration, final output | `server/app/routers/query.py` |
| Drop-ratio search | `GET /steps?min_drop_ratio=&max_drop_ratio=` finds the stages that cut the most | `server/app/db.py` |
| Auth | Google OAuth to JWT for the UI; SHA-256 hashed API keys for the SDK; all data scoped per user | `server/app/auth.py`, `routers/auth.py` |
| Read cache | Redis cache for run lists and details, invalidated on ingest | `server/app/cache.py` |
| Dashboard | Runs, Run detail with timeline and trace search, Step detail, Compare, API keys | `mainapp/src/pages/` |
| Legacy API | `Run` and `Step` context managers, `CandidateSet` with auto `SUMMARY` mode above 100 items | `sdk/zenray/run.py`, `candidates.py` |

## Configuration

### SDK

Read by `zenray.init()` (`sdk/zenray/config.py`). Each variable also accepts the older `XRAY_` prefix. Keyword arguments to `init()` win over the environment.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ZENRAY_API_KEY` | none | Required. Sent as `Authorization: Bearer`. A warning is logged if missing. |
| `ZENRAY_ENDPOINT` | `http://localhost:8000` | Server base URL. Set to `http://localhost:4003` for the server defaults in this repo. |
| `ZENRAY_DISABLED` | `false` | `true` turns off all tracing. |
| `ZENRAY_SAMPLE_RATE` | `1.0` | Fraction of pipeline calls to trace. |
| `ZENRAY_TOP_K` | `10` | Max kept and dropped items stored per step. |
| `ZENRAY_BATCH_SIZE` | `10` | Events per `POST /ingest`. |
| `ZENRAY_FLUSH_INTERVAL` | `1.0` | Seconds between background flushes. |

`init(fail_open=False)` makes ingest errors raise instead of being recorded.

### Server

`pydantic-settings` with prefix `XRAY_`, also read from `server/.env` (`server/app/config.py`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `XRAY_PORT` | `4003` | Used by the Dockerfile `CMD`. `uvicorn --port` wins when run by hand. |
| `XRAY_DEBUG` | `false` | Enables `/docs` and `/redoc`. |
| `XRAY_LOG_LEVEL` | `INFO` | Python logging level. |
| `XRAY_POSTGRES_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_DB` | `localhost` / `5432` / `xray` / `xray_secret` / `xray` | asyncpg pool, 5 to 20 connections. |
| `XRAY_REDIS_HOST` / `_PORT` / `_DB` / `_PASSWORD` | `localhost` / `6379` / `0` / none | Queue and cache. |
| `XRAY_S3_ENDPOINT` / `_ACCESS_KEY` / `_SECRET_KEY` / `_BUCKET` / `_REGION` | `http://localhost:9000` / `minioadmin` / `minioadmin` / `xray-blobs` / `us-east-1` | Bucket is created on startup if missing. |
| `XRAY_JWT_SECRET` / `_ALGORITHM` / `_EXPIRATION_HOURS` | `change-this-in-production` / `HS256` / `168` | Dashboard session tokens. |
| `XRAY_GOOGLE_CLIENT_ID` / `_SECRET` | none | Required for dashboard login. |
| `XRAY_FRONTEND_URL` | `http://localhost:4002` | OAuth redirect target (`{url}/auth`). |

### Dashboard (`mainapp/`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `DASHBOARD_PORT` | `4002` | Vite dev and preview port. |
| `SERVER_HOST` / `SERVER_PORT` | `localhost` / `4003` | Target of the `/api/*` dev proxy. |
| `VITE_SERVER_URL` | unset (uses `/api`) | Set to call the server directly without the proxy. |
| `VITE_SITE_URL` / `VITE_DOCS_URL` / `VITE_GITHUB_URL` | zenray.live links | Sidebar links. |
| `VITE_ALLOWED_HOSTS` | `zenray.live,...,localhost,127.0.0.1` | Vite host allowlist. |

### Website and infra

`web/.env.example`: `WEB_PORT` (`4001`), `PUBLIC_SITE_URL`, `PUBLIC_DASHBOARD_URL`, `PUBLIC_API_URL`, `PUBLIC_GITHUB_URL`, `ALLOWED_HOSTS`.
`infra/.env.example`: `POSTGRES_USER` / `_PASSWORD` / `_DB` / `_PORT`, `REDIS_PORT`, `MINIO_ROOT_USER` / `_PASSWORD` / `MINIO_PORT` / `MINIO_CONSOLE_PORT` (`9001`), `S3_BUCKET`. Defaults match the server defaults above.

## Design decisions

- **Metadata in Postgres, candidates in S3.** A `steps` row holds counts and a `candidate_set_ref`; the item lists live in MinIO. Rows stay small, but `/runs/{id}/trace` and `/steps/{id}` do one S3 read per step.
- **Queue first, one worker.** `POST /ingest` only pushes to Redis. A single asyncio task per server process drains it in batches of 50. There is no ack: a payload that fails to process is logged and dropped (`server/app/worker.py`).
- **Fail-open SDK.** Ingest errors never raise by default. They are counted in `zenray.get_stats()`; the queue is capped at 10,000 events and drops beyond that. Flip `fail_open=False` in tests.
- **Blocking flush at the end of each run.** `@pipeline` calls `flush()` in its `finally`, so the run's events have reached the server (or its Redis queue) before the decorated function returns. That adds one HTTP round trip per run.
- **Top-k, not full capture.** The decorator API always emits `mode=TOP_K` with `ZENRAY_TOP_K` items per list. `FULL` exists in the model but only the legacy `CandidateSet` class can produce it.
- **Item identity is your `id`.** Drops and scores are keyed by `item["id"]`, `item["_id"]` or `item.id`, falling back to Python's `id()`. Without a stable id, items cannot be traced.
- **Schema by `CREATE TABLE IF NOT EXISTS` at startup.** No migration tool. Changing a table means editing `server/app/db.py` and altering existing databases by hand.

## Project layout

```
sdk/        Python package `zenray` (decorators, context, client, models) and runnable examples
server/     FastAPI app: ingest queue, worker, query API, auth, Postgres/Redis/S3 adapters
mainapp/    React 18 + Vite dashboard (runs, steps, compare, API keys)
web/        Astro landing page and docs, served by nginx in Docker
infra/      Compose files for Postgres 16, Redis 7, MinIO, plus an init job that creates the bucket
assets/     Logo
```

## Development

```bash
# SDK (Python 3.9+)
cd sdk && pip install -e ".[dev]"
ruff check zenray/ && mypy zenray/

# Server (Python 3.11+)
cd server && pip install -e ".[dev]"
ruff check app/ && ruff format app/ && mypy app/

# Dashboard
cd mainapp && npm install && npm run build      # tsc + vite build

# Website
cd web && npm install && npm run build
```

`pytest` is configured in both `pyproject.toml` files with `testpaths = ["tests"]`, but no `tests/` directory exists yet. There is no CI workflow in the repo.

## Limitations

- **Login is Google OAuth only.** No local user or password flow (`server/app/routers/auth.py`). Use the SQL insert in Quickstart for API-only setups.
- **Artifact types disagree between SDK and server.** The SDK allows `input`, `output`, `judgments`, `metadata`, `error`; the server enum only accepts `prompt`, `response`, `debug`, `config`, `metrics`. A step carrying one of the extra types is rejected with a 422 and dropped by the fail-open client. `sdk/examples/rag_document_retrieval.py` hits this with `zenray.artifact("input", ...)`.
- **SDK default endpoint is `:8000`, server default is `:4003`.** Always set `ZENRAY_ENDPOINT`.
- **No tests, no CI.**
- **Dead code.** `sdk/xray/client.py` imports a module that does not exist, and `sdk/examples/competitor_selection.py` imports `from xray import configure, Run`, which has no package. Both are leftovers from the pre-rename `xray` API.
- `pyproject.toml` links a `CHANGELOG.md` that is not in the repo.

## Contributing

Open an issue or PR at [github.com/DeepakSilaych/ZenRay](https://github.com/DeepakSilaych/ZenRay). Component READMEs: [SDK](./sdk/README.md), [Server](./server/README.md), [Dashboard](./mainapp/README.md), [Website](./web/README.md), [Infra](./infra/README.md).

## License

MIT. The license text ships at [`sdk/LICENSE`](./sdk/LICENSE); the server and web manifests declare MIT as well. There is no root `LICENSE` file yet.
