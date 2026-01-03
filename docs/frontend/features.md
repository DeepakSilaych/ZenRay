# Frontend Features

This page describes the current UX surfaced by the UI.

## Runs

- **Runs table**: status, duration, steps, started time.
- **Status filter buttons**: All / Success / Failure / Running.
- **Pagination**: page through runs (client-side in the UI).
- **Runs overview chart**: stacked “area-style” bar chart showing runs per hour for the last 24h.

## Run details

- **Step timeline table**: each step’s input/output counts, drop %, duration.
- **Candidate trace**: search for a candidate ID and see where it was kept/dropped.
- **Run input/output JSON**: bounded height with scroll.

## Step details

- **Candidate set**: histograms, top kept/dropped, dropped-by-reason expansion.
- **Artifacts**: prompts/responses/config/errors (expand/collapse).

## Related docs

- Backend endpoints powering the UI: [`../backend/api.md`](../backend/api.md)
- How candidate sets are captured in SDK: [`../sdk/overview.md`](../sdk/overview.md)

## Where to make changes

- **Runs page**: `client/src/pages/RunsPage.tsx`
- **Run detail page**: `client/src/pages/RunDetailPage.tsx`
- **Step detail page**: `client/src/pages/StepDetailPage.tsx`
- **Compare page**: `client/src/pages/ComparePage.tsx`
- **Docs page**: `client/src/pages/DocsPage.tsx`
- **API wiring**: `client/src/api.ts`

## Architecture context

Everything in the UI maps to backend endpoints and (sometimes) blob-backed payloads:

- Query endpoints: [`../backend/api.md`](../backend/api.md)
- Blob-backed candidate sets/artifacts: [`../backend/storage.md`](../backend/storage.md)
