# ZenRay Infrastructure

Local development infrastructure for ZenRay.

## Services

| Service       | Port | Description                     |
| ------------- | ---- | ------------------------------- |
| PostgreSQL    | 5432 | Database for runs, steps, users |
| Redis         | 6379 | Cache and ingest queue          |
| MinIO         | 9000 | S3-compatible blob storage      |
| MinIO Console | 9001 | MinIO web UI                    |

## Quick Start

```bash
# Start all services
docker compose up -d

# Or start individually
docker compose -f postgres.yml up -d
docker compose -f redis.yml up -d
docker compose -f minio.yml up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove data
docker compose down -v
```

## Configuration

Copy `.env.example` to `.env` to customize:

```bash
cp ../.env.example .env
```

| Variable              | Default     | Description       |
| --------------------- | ----------- | ----------------- |
| `POSTGRES_USER`       | xray        | Database user     |
| `POSTGRES_PASSWORD`   | xray_secret | Database password |
| `POSTGRES_DB`         | xray        | Database name     |
| `POSTGRES_PORT`       | 5432        | Exposed port      |
| `REDIS_PORT`          | 6379        | Exposed port      |
| `MINIO_ROOT_USER`     | minioadmin  | MinIO access key  |
| `MINIO_ROOT_PASSWORD` | minioadmin  | MinIO secret key  |
| `MINIO_PORT`          | 9000        | S3 API port       |
| `MINIO_CONSOLE_PORT`  | 9001        | Web console port  |
| `S3_BUCKET`           | xray-blobs  | Default bucket    |

## Accessing Services

- **PostgreSQL**: `psql -h localhost -U xray -d xray`
- **Redis**: `redis-cli`
- **MinIO Console**: http://localhost:9001

## Data Persistence

Data is stored in Docker volumes:

- `postgres_data` - Database files
- `redis_data` - Redis snapshots
- `minio_data` - Object storage

To reset all data:

```bash
docker compose down -v
docker compose up -d
```
