# Local Development

This repo is structured into:

- `server/`: FastAPI backend
- `sdk/`: Python SDK + examples
- `client/`: React UI

## Typical local dev flow

1. Start infra services (DB, object storage, Redis)
2. Start backend (`server/`)
3. Start UI (`client/`)
4. Run SDK examples (`sdk/examples/`) to generate data

## Related docs

- Docker services: [`docker.md`](./docker.md)
- Backend API: [`../backend/api.md`](../backend/api.md)
- SDK examples: [`../sdk/examples.md`](../sdk/examples.md)

## Where to make changes

- Docker infra: `docker-compose.yml`
- Backend startup lifecycle: `server/app/main.py`
- SDK endpoint/config: `sdk/xray/config.py`
- UI endpoint/config (Vite env): `client/vite.config.ts` + `client/src/api.ts`
