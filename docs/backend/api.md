# Backend API (Query + Ingest)

This is a human-oriented map of the API the UI/SDK uses. For the authoritative schema, use the FastAPI docs.

## Interactive docs

- Swagger UI: `<XRAY_ENDPOINT>/docs`

## Ingest

- `POST /ingest`: ingest run + step batches (queued)
- `GET /ingest/stats`: ingest queue stats

## Query

- `GET /runs`: list runs
- `GET /runs/{run_id}`: run details + step summaries
- `GET /steps/{step_id}`: step detail
- `GET /steps/{step_id}/candidates`: candidate set payload for a step
- `GET /trace/{run_id}/{candidate_id}`: trace candidate journey within a run
- `GET /compare`: compare two runs
- `GET /health`: health check

## Related docs

- Storage & blob refs: [`storage.md`](./storage.md)
- UI usage patterns: [`../frontend/overview.md`](../frontend/overview.md)

## Where to make changes

- **Endpoint implementations**: `server/app/routes.py`
- **Database access**: `server/app/db.py`
- **Blob reads** (candidate sets/artifacts): `server/app/blob_store.py`
- **Caching**: `server/app/cache.py`

## Architecture context

This file documents the **read path** (UI → Query API). For ingest/write path details, see:

- [`../architecture.md`](../architecture.md)


