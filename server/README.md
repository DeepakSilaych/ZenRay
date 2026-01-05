# ZenRay Server

FastAPI backend for the ZenRay observability platform.

---

## Overview

The server handles:

- **Ingestion** — Receives pipeline traces from the Python SDK
- **Storage** — Persists metadata to PostgreSQL, blobs to MinIO
- **Caching** — Uses Redis for query caching and ingest queuing
- **Query API** — Serves the dashboard with run and step data

### Architecture

```
┌──────────────┐
│  Ingest API  │──▶ Redis Queue ──▶ Background Worker
└──────────────┘                           │
                                           ▼
┌──────────────┐                    ┌─────────────┐
│  Query API   │◀───────────────────│  PostgreSQL │
└──────────────┘                    │    MinIO    │
                                    └─────────────┘
```

---

## Prerequisites

- Python 3.11+
- Docker (for PostgreSQL, MinIO, Redis)

---

## Setup

### 1. Start Infrastructure

From the project root:

```bash
docker compose up -d
```

### 2. Create Virtual Environment

```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Server will be available at `http://localhost:8000`

---

## API Endpoints

### Health Check

```
GET /health
```

Returns server status and queue length.

### Ingest

```
POST /ingest/run       # Create a new run
POST /ingest/step      # Add a step to a run
POST /ingest/candidates # Add candidates to a step
```

### Query

```
GET /runs              # List all runs
GET /runs/{run_id}     # Get run details
GET /runs/{run_id}/steps           # List steps in a run
GET /runs/{run_id}/steps/{step_id} # Get step details with candidates
```

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Configuration

All settings use the `XRAY_` prefix:

| Variable                 | Default               | Description         |
| ------------------------ | --------------------- | ------------------- |
| `XRAY_POSTGRES_HOST`     | localhost             | PostgreSQL host     |
| `XRAY_POSTGRES_PORT`     | 5432                  | PostgreSQL port     |
| `XRAY_POSTGRES_USER`     | xray                  | PostgreSQL user     |
| `XRAY_POSTGRES_PASSWORD` | xray_secret           | PostgreSQL password |
| `XRAY_POSTGRES_DB`       | xray                  | PostgreSQL database |
| `XRAY_S3_ENDPOINT`       | http://localhost:9000 | MinIO endpoint      |
| `XRAY_S3_ACCESS_KEY`     | minioadmin            | MinIO access key    |
| `XRAY_S3_SECRET_KEY`     | minioadmin            | MinIO secret key    |
| `XRAY_S3_BUCKET`         | xray-blobs            | MinIO bucket name   |
| `XRAY_REDIS_HOST`        | localhost             | Redis host          |
| `XRAY_REDIS_PORT`        | 6379                  | Redis port          |

---

## Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app & lifespan
│   ├── config.py      # Settings management
│   ├── db.py          # PostgreSQL connection
│   ├── blob_store.py  # MinIO/S3 client
│   ├── cache.py       # Redis client
│   ├── queue.py       # Async ingest queue
│   ├── worker.py      # Background flush worker
│   ├── models.py      # Pydantic models
│   ├── ingest.py      # Ingest routes
│   └── routes.py      # Query routes
└── requirements.txt
```

---

## Development

### Run with Auto-reload

```bash
uvicorn app.main:app --reload --port 8000
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
black app/
isort app/
```
