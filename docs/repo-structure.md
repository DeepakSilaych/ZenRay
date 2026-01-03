# Repository Structure

This repo is organized as a **3-package system** plus shared docs and local infra config.

## Top-level layout

- `server/`: FastAPI backend API
- `sdk/`: Python SDK for instrumentation + runnable examples
- `client/`: React UI (Vite) for exploring traces
- `docker-compose.yml`: local infrastructure (Postgres, MinIO, Redis)
- `docs/`: project documentation (start at [`index.md`](./index.md))

## `server/` (backend)

Backend code lives under `server/app/`.

### Key files

- `server/app/main.py`
  - FastAPI app creation
  - CORS
  - startup/shutdown lifecycle: initializes DB/blob/cache and starts background worker
- `server/app/routes.py`
  - Query endpoints used by the UI (runs, run detail, step detail, compare, trace, candidates)
- `server/app/ingest.py`
  - Ingest endpoint used by SDK (`POST /ingest`)
  - Enqueues payloads to Redis for async processing
- `server/app/worker.py`
  - Background worker that drains the Redis ingest queue and persists data to DB + MinIO
- `server/app/db.py`
  - PostgreSQL access (runs/steps/artifacts indexes, search, upserts)
- `server/app/blob_store.py`
  - MinIO/S3 blob storage (candidate sets + artifacts)
- `server/app/cache.py`
  - Redis cache helpers (query caching + invalidation)
- `server/app/queue.py`
  - Redis queue helpers (enqueue, stats, record processed/errors)
- `server/app/models.py`
  - Pydantic models shared by ingest/query (Run/Step/CandidateSet/Artifact)

### Data directory

- `server/data/` contains local persistence used by the backend (for dev):
  - `server/data/xray.db` (if SQLite fallback/dev mode is used)
  - `server/data/blobs/` (legacy/local blob store artifacts/candidate sets)

## `sdk/` (Python SDK)

### Key files

- `sdk/xray/__init__.py`: public SDK surface (`xray.init`, decorators, helpers)
- `sdk/xray/config.py`: env + `xray.init(...)` configuration (includes `XRAY_TOP_K`)
- `sdk/xray/client.py`: background flush thread + batching to `POST /ingest`
- `sdk/xray/decorators.py`: `@xray.pipeline`, `@xray.step` wrappers (minimal-code API)
- `sdk/xray/context.py`: run/step context + candidate set building for decorator API
- `sdk/xray/helpers.py`: helper calls inside steps (`drop/score/metric/artifact/tag`)
- `sdk/xray/candidates.py`: candidate capture logic for legacy/explicit candidate sets
- `sdk/xray/models.py`: SDK-side models matching backend ingest schema

### Examples

- `sdk/examples/`: runnable, domain-style pipelines that generate realistic traces.
  - See [`sdk/examples.md`](./sdk/examples.md)

## `client/` (frontend UI)

### Key files

- `client/src/api.ts`: backend API client wrappers (runs, run detail, step detail, compare, trace)
- `client/src/main.tsx`: routes
- `client/src/App.tsx`: app shell + nav
- `client/src/pages/*`:
  - `RunsPage.tsx`: run list + overview chart + pagination + status buttons
  - `RunDetailPage.tsx`: run detail + step timeline + candidate trace
  - `StepDetailPage.tsx`: step detail view, candidate tables, artifacts
  - `ComparePage.tsx`: compare two runs
  - `DocsPage.tsx`: in-app docs tabs (SDK/API)

## Infra (`docker-compose.yml`)

- `postgres`: metadata
- `minio` + `minio-init`: blob storage bucket bootstrap
- `redis`: queue + cache (backend uses it for ingest buffering and query caching)

See also: [`deployment/docker.md`](./deployment/docker.md)

## Related docs

- Architecture: [`architecture.md`](./architecture.md)
- Docs index: [`index.md`](./index.md)
