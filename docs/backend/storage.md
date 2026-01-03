# Storage & Data Flow

X-Ray splits data into:

- **Metadata** (runs, steps, indexes) stored in a database.
- **Blobs** (candidate sets, artifacts) stored in object storage (S3/MinIO).

## Why this split

- Candidate sets/artifacts can be large and are best handled via blob storage.
- Metadata needs indexing/filtering and benefits from DB query capabilities.

## Candidate sets

For each step, we store:

- counts: `input_count`, `output_count`
- histograms: `reason_histogram`, `score_histogram`
- examples: `top_kept`, `top_dropped`
- optional: `dropped_by_reason` mapping for drill-down in UI

Top-k capture is configurable in the SDK:

- SDK config: [`../sdk/configuration.md`](../sdk/configuration.md)

## Artifacts

Artifacts are stored as blobs and referenced from step records via a `blob_ref`/key.

## Related docs

- API endpoints returning blob-backed data: [`api.md`](./api.md)
- SDK capture behavior: [`../sdk/overview.md`](../sdk/overview.md)

## Where to make changes

- **Blob storage implementation (MinIO/S3)**: `server/app/blob_store.py`
- **Where blob refs are persisted**: `server/app/worker.py` (sets `candidate_set_ref`, indexes artifacts)
- **DB schema / queries**: `server/app/db.py`
- **SDK-side candidate capture format**: `sdk/xray/context.py` and `sdk/xray/models.py`

## Architecture context

Storage is split for scale: metadata in Postgres, large payloads in MinIO. Full details:

- [`../architecture.md`](../architecture.md)
