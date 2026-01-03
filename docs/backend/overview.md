# Backend Overview

The backend is a FastAPI service that supports:

- **Ingest**: receives run/step events from the SDK.
- **Query API**: serves runs, steps, candidate sets, artifacts, comparisons, and traces to the UI.

## High-level flow

1. SDK sends run/step payloads to ingest.
2. Backend queues and persists metadata.
3. Large payloads (candidate sets, artifacts) are stored in object storage.
4. UI queries the backend for lists/details and renders visualizations.

## Where to look next

- API surface: [`api.md`](./api.md)
- Storage layout & blob refs: [`storage.md`](./storage.md)
- SDK emission model: [`../sdk/overview.md`](../sdk/overview.md)

## Where to make changes

- **FastAPI app lifecycle**: `server/app/main.py`
- **Query endpoints**: `server/app/routes.py`
- **Ingest endpoint**: `server/app/ingest.py`
- **Worker / write pipeline**: `server/app/worker.py`
- **DB queries/upserts**: `server/app/db.py`
- **Blob storage**: `server/app/blob_store.py`
- **Redis cache**: `server/app/cache.py`
- **Redis queue**: `server/app/queue.py`

## Architecture context

Backend sits between SDK and UI and owns persistence. Full flow:

- [`../architecture.md`](../architecture.md)
