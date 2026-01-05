# ZenRay Server

Backend API server for ZenRay - the observability layer for ML/LLM pipelines.

## Features

- **Ingest API**: Receive telemetry from SDK via REST
- **Query API**: Search and explore runs, steps, and candidates
- **Authentication**: Google OAuth + API keys
- **Async Processing**: Redis queue for high-throughput ingestion
- **Blob Storage**: MinIO/S3 for candidate sets and artifacts

## Quick Start

### With Docker Compose (Recommended)

```bash
# From project root
docker compose up -d
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export XRAY_POSTGRES_HOST=localhost
export XRAY_REDIS_HOST=localhost
export XRAY_S3_ENDPOINT=http://localhost:9000

# Run server
uvicorn app.main:app --reload --port 8000
```

## Configuration

All settings via environment variables with `XRAY_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `XRAY_POSTGRES_HOST` | localhost | PostgreSQL host |
| `XRAY_POSTGRES_PORT` | 5432 | PostgreSQL port |
| `XRAY_POSTGRES_USER` | xray | Database user |
| `XRAY_POSTGRES_PASSWORD` | xray_secret | Database password |
| `XRAY_POSTGRES_DB` | xray | Database name |
| `XRAY_REDIS_HOST` | localhost | Redis host |
| `XRAY_REDIS_PORT` | 6379 | Redis port |
| `XRAY_S3_ENDPOINT` | http://localhost:9000 | MinIO/S3 endpoint |
| `XRAY_S3_ACCESS_KEY` | minioadmin | S3 access key |
| `XRAY_S3_SECRET_KEY` | minioadmin | S3 secret key |
| `XRAY_S3_BUCKET` | xray-blobs | S3 bucket name |
| `XRAY_JWT_SECRET` | (change me) | JWT signing secret |
| `XRAY_GOOGLE_CLIENT_ID` | - | Google OAuth client ID |
| `XRAY_GOOGLE_CLIENT_SECRET` | - | Google OAuth secret |
| `XRAY_FRONTEND_URL` | http://localhost:5174 | Frontend URL for OAuth |
| `XRAY_DEBUG` | false | Enable debug mode |

## API Endpoints

### Ingest (SDK)

```
POST /ingest          # Batch ingest runs and steps (requires API key)
GET  /ingest/stats    # Queue statistics
```

### Query (Dashboard)

```
GET  /runs            # List runs (requires auth)
GET  /runs/{id}       # Get run detail
GET  /runs/{id}/trace # Trace candidate through run
GET  /steps           # List steps
GET  /steps/{id}      # Get step detail
GET  /compare         # Compare two runs
```

### Auth

```
GET  /auth/google/url      # Get Google OAuth URL
POST /auth/google/callback # Google OAuth callback
GET  /auth/me              # Current user info
POST /auth/api-keys        # Create API key
GET  /auth/api-keys        # List API keys
DELETE /auth/api-keys/{id} # Delete API key
```

### System

```
GET  /health          # Health check
GET  /                # API info
```

## Project Structure

```
server/
├── app/
│   ├── __init__.py       # Package info
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings
│   ├── db.py             # PostgreSQL operations
│   ├── cache.py          # Redis operations
│   ├── queue.py          # Ingest queue
│   ├── worker.py         # Background processor
│   ├── blob_store.py     # S3/MinIO operations
│   ├── auth.py           # Auth utilities
│   ├── models.py         # Pydantic models
│   └── routers/
│       ├── auth.py       # Auth endpoints
│       ├── ingest.py     # Ingest endpoints
│       └── query.py      # Query endpoints
├── pyproject.toml        # Python project config
├── Dockerfile
└── README.md
```

## Development

```bash
# Run tests
pytest

# Format code
ruff format app/

# Lint
ruff check app/

# Type check
mypy app/
```

## License

MIT
