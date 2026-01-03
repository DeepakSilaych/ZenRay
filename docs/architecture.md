# Architecture

This document explains how X-Ray works end-to-end so new devs can quickly place code changes in the correct layer.

## High-level components

1. **Python SDK (`sdk/`)**

   - Instruments code using decorators/helpers.
   - Buffers events and ships them to the backend via `POST /ingest`.

2. **Backend API (`server/`)**

   - Accepts ingest payloads.
   - Pushes payloads into a Redis-backed ingest queue.
   - A background worker drains the queue and persists data.
   - Serves query endpoints to the UI (runs, steps, candidates, artifacts, compare, trace).

3. **UI (`client/`)**

   - Calls the backend query endpoints and renders run/step views.

4. **Infra**
   - **PostgreSQL**: durable metadata store (runs/steps/artifact index)
   - **MinIO (S3)**: blob store for large payloads (candidate sets + artifacts)
   - **Redis**: ingest queue + query cache (fast reads, buffers write spikes)

## Data model (conceptual)

- **Run**

  - Identity: `run_id`
  - Attributes: pipeline name, version, tags
  - Timing + status: started/ended + success/failure/running
  - Summaries: input + final output summary

- **Step**

  - Identity: `step_id`
  - Foreign key: `run_id`
  - Attributes: kind, name, parent_step_id
  - Metrics: key/value
  - Candidate set reference: `candidate_set_ref` (points to a blob)
  - Artifact index entries: artifact metadata points to blob refs

- **CandidateSet (blob)**
  - counts: input/output
  - histograms: reason + score histograms
  - samples: `top_kept`, `top_dropped`
  - drilldown: `dropped_by_reason` mapping (optional)

## Ingest flow (write path)

### 1) SDK creates events

During execution:

- `@xray.pipeline`: creates a run context and emits “run started” and “run ended/failed”.
- `@xray.step`: creates a step context, captures counts, emits “step ended/failed”.
- `xray.drop/xray.score`: enrich candidate set info for that step.
- `xray.artifact`: attaches artifacts to the step.

Relevant code:

- `sdk/xray/decorators.py`
- `sdk/xray/context.py`
- `sdk/xray/helpers.py`
- `sdk/xray/client.py`

### 2) SDK batches + sends to backend

`sdk/xray/client.py` buffers `RunData` and `StepData` in a bounded queue and periodically flushes:

- HTTP: `POST {XRAY_ENDPOINT}/ingest`
- payload: `IngestPayload { runs?: RunData[], steps?: StepData[] }`

Why batching:

- reduces per-step HTTP overhead
- fail-open behavior avoids blocking production pipelines

### 3) Backend enqueues ingest to Redis

`server/app/ingest.py` accepts ingest and enqueues the payload into Redis (write buffer).

Why:

- keeps ingest endpoint fast (returns quickly)
- smooths bursts (queue absorbs spikes)

### 4) Worker persists to Postgres + MinIO

`server/app/worker.py` drains the queue in batches:

- Upserts runs/steps into Postgres (`server/app/db.py`)
- Writes candidate sets to MinIO (`server/app/blob_store.py`)
- Writes artifacts to MinIO + indexes artifacts in Postgres
- Invalidates caches (`server/app/cache.py`)

## Query flow (read path)

The UI calls query endpoints in `server/app/routes.py`.

Typical path:

1. Request comes in (e.g. `GET /runs`)
2. Backend checks Redis cache (`server/app/cache.py`)
3. Cache miss → query Postgres
4. If response needs blob content:
   - backend loads from MinIO (candidate set, artifact payload)
5. Backend returns JSON models to UI

UI integration points:

- `client/src/api.ts`
- `client/src/pages/*`

## Where to change what (cheat sheet)

- **UI presentation** (tables/charts/UX): `client/src/pages/*`
- **UI data fetching / endpoint wiring**: `client/src/api.ts`
- **Add a new query endpoint**: `server/app/routes.py` + `server/app/db.py` (+ blob_store if needed)
- **Change ingest schema**: `sdk/xray/models.py` + `server/app/models.py` + ingest/worker/db
- **Change candidate capture logic** (top-k, histograms): `sdk/xray/context.py` and/or `sdk/xray/candidates.py`
- **Queue semantics / batching**: `server/app/queue.py`, `server/app/worker.py`
- **Blob storage format**: `server/app/blob_store.py` (+ migration/backward compat considerations)

## Related docs

- Repo structure: [`repo-structure.md`](./repo-structure.md)
- Backend API map: [`backend/api.md`](./backend/api.md)
- Storage specifics: [`backend/storage.md`](./backend/storage.md)
- SDK configuration: [`sdk/configuration.md`](./sdk/configuration.md)
