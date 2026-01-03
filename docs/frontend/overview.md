# Frontend Overview

The frontend is a React UI for exploring pipeline traces.

## Main pages

- **Runs list**: browse runs, filter by status, paginate, and view an overview chart.
- **Run detail**: step timeline + run input/output JSON.
- **Step detail**: candidate set charts, “top kept/dropped” tables, reasons, artifacts.
- **Compare**: compare two runs side-by-side.
- **Docs**: in-app docs for SDK and API.

## How it talks to the backend

The UI calls the backend Query API using the configured API endpoint (via Vite env).

See:

- Features: [`features.md`](./features.md)
- Backend endpoints: [`../backend/api.md`](../backend/api.md)

## Where to make changes

- **Pages / UX**: `client/src/pages/*`
- **API calls**: `client/src/api.ts`
- **Routing**: `client/src/main.tsx`
- **Layout/nav**: `client/src/App.tsx`

## Architecture context

Frontend is read-only against the backend’s Query API. For the full flow (SDK → ingest queue → persistence → query), see:

- [`../architecture.md`](../architecture.md)
