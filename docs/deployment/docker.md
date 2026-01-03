# Docker Services

X-Ray commonly uses Docker for local infra:

- **PostgreSQL**: metadata storage
- **MinIO (S3-compatible)**: blob storage for artifacts/candidate sets
- **Redis**: queue/cache (depending on backend configuration)

## Related docs

- Local dev flow: [`local-dev.md`](./local-dev.md)
- Storage model: [`../backend/storage.md`](../backend/storage.md)

## Where to make changes

- Service definitions: `docker-compose.yml`
- Backend service config usage: `server/app/config.py` and related modules (`db.py`, `blob_store.py`, `cache.py`)
