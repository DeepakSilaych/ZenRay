Repository layout

1. `server/` FastAPI backend
2. `client/` React UI (Vite)
3. `sdk/` Python SDK and examples
4. `docker-compose.yml` local Postgres, MinIO, Redis
5. `ARCHITECTURE.md` system architecture

## Prerequisites

1. Docker and Docker Compose
2. Python 3.11+
3. Node.js 18+ and pnpm

## 1. Start infrastructure

From repo root

```bash
docker compose up -d
```

Services

| Service       | Local port | Purpose                           |
| ------------- | ---------: | --------------------------------- |
| Postgres      |       5432 | Run and step metadata             |
| MinIO S3 API  |       9000 | Candidate sets and artifact blobs |
| MinIO Console |       9001 | Admin UI                          |
| Redis         |       6379 | Ingest queue and query cache      |

## 2. Run the backend

From repo root

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

Backend URLs

| URL                            | Purpose                |
| ------------------------------ | ---------------------- |
| `http://localhost:8000/health` | Health check           |
| `http://localhost:8000/docs`   | OpenAPI and Swagger UI |

## 3. Run the web UI

From repo root

```bash
cd client
pnpm install
pnpm dev --port 3000
```

UI URL

1. `http://localhost:3000`

UI configuration

Set the backend endpoint for the UI using Vite env

```bash
export VITE_XRAY_API_ENDPOINT="http://localhost:8000"
```

## 4. Generate data with the SDK

The UI will show no runs until the SDK sends events.

From repo root

```bash
cd sdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export XRAY_ENDPOINT="http://localhost:8000"
python examples/minimal_api_demo.py
```

Other examples

1. `python examples/ecommerce_search.py`
2. `python examples/rag_document_retrieval.py`
3. `python examples/recommendation_system.py`
4. `python examples/content_moderation.py`

SDK configuration

| Config                |                 Default | Use                                   |
| --------------------- | ----------------------: | ------------------------------------- |
| `XRAY_ENDPOINT`       | `http://localhost:8000` | Backend base URL                      |
| `XRAY_DISABLED`       |                 `false` | Disable tracing                       |
| `XRAY_SAMPLE_RATE`    |                   `1.0` | Sample runs to control cost           |
| `XRAY_BATCH_SIZE`     |                    `10` | Flush batch size                      |
| `XRAY_FLUSH_INTERVAL` |                   `1.0` | Flush cadence seconds                 |
| `XRAY_TOP_K`          |                    `10` | Top kept and top dropped capture size |

## Troubleshooting

1. Backend shows zero runs

   1. Confirm `XRAY_ENDPOINT` is set for the SDK
   2. Confirm the backend is running on port 8000
   3. Confirm Redis, Postgres, and MinIO are healthy via `docker ps`

2. MinIO bucket issues

   1. Open MinIO console at `http://localhost:9001`
   2. Confirm bucket `xray-blobs` exists

3. UI cannot reach backend
   1. Confirm `VITE_XRAY_API_ENDPOINT` is set correctly before starting `pnpm dev`
