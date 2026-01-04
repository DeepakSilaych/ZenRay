# X-Ray: ML Pipeline Observability

Repository layout

1. `server-express/` Express.js backend (Bun)
2. `web/` Landing page + docs (Astro)
3. `dashboard/` Dashboard UI (React + Vite)
4. `sdk/` Python SDK and examples
5. `docker-compose.yml` local Postgres, MinIO, Redis

## Prerequisites

1. Docker and Docker Compose
2. Bun 1.0+
3. Python 3.11+ (for SDK examples)

## 1. Start infrastructure

```bash
docker compose up -d
```

| Service       | Port | Purpose                           |
| ------------- | ---: | --------------------------------- |
| Postgres      | 5432 | Run and step metadata             |
| MinIO S3 API  | 9000 | Candidate sets and artifact blobs |
| MinIO Console | 9001 | Admin UI                          |
| Redis         | 6379 | Ingest queue and query cache      |

## 2. Run the backend

```bash
cd server-express
bun install
bun run dev
```

Server runs on `http://localhost:8000`

## 3. Run the landing page + docs

```bash
cd web
bun install
bun run dev
```

Landing page: `http://localhost:4000`
Docs: `http://localhost:4000/docs`

## 4. Run the dashboard

```bash
cd dashboard
bun install
bun run dev --port 3000
```

Dashboard: `http://localhost:3000`

## 5. Generate data with the SDK

```bash
cd sdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
export XRAY_ENDPOINT="http://localhost:8000"
python examples/minimal_api_demo.py
```

## URLs Summary

| Service   | URL                       |
| --------- | ------------------------- |
| Backend   | http://localhost:8000     |
| Landing   | http://localhost:4000     |
| Docs      | http://localhost:4000/docs|
| Dashboard | http://localhost:3000     |

## SDK Configuration

| Variable              | Default                   | Description                 |
| --------------------- | ------------------------- | --------------------------- |
| `XRAY_ENDPOINT`       | http://localhost:8000     | Backend URL                 |
| `XRAY_DISABLED`       | false                     | Disable tracing             |
| `XRAY_SAMPLE_RATE`    | 1.0                       | Sampling rate               |
| `XRAY_TOP_K`          | 10                        | Candidates to capture       |
