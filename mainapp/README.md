# ZenRay Dashboard

React dashboard for viewing and debugging pipeline runs.

---

## Overview

The dashboard provides:

- **Runs List** — Browse all pipeline executions
- **Run Details** — View steps and timing for a specific run
- **Step Inspector** — Examine candidates, drops, and scores
- **Compare View** — Side-by-side pipeline comparison

Built with:

- [React 18](https://react.dev) — UI framework
- [Vite](https://vitejs.dev) — Build tool
- [React Router](https://reactrouter.com) — Client-side routing
- [Tailwind CSS](https://tailwindcss.com) — Styling
- [TypeScript](https://typescriptlang.org) — Type safety

---

## Prerequisites

- Node.js 18+ or Bun
- ZenRay server running on port 8000

---

## Setup

### Install Dependencies

```bash
cd mainapp
npm install
# or
bun install
```

### Run Development Server

```bash
npm run dev
# or
bun run dev
```

Dashboard will be available at `http://localhost:5173`

---

## Build for Production

```bash
npm run build
```

Output is in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

---

## Project Structure

```
mainapp/
├── src/
│   ├── main.tsx           # App entry point
│   ├── App.tsx            # Router setup
│   ├── api.ts             # Server API client
│   ├── index.css          # Global styles
│   └── pages/
│       ├── RunsPage.tsx       # List all runs
│       ├── RunDetailPage.tsx  # Single run view
│       ├── StepDetailPage.tsx # Step inspector
│       ├── ComparePage.tsx    # Compare runs
│       └── DocsPage.tsx       # Embedded docs
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

---

## Configuration

### API Endpoint

The dashboard connects to the server at `http://localhost:8000` by default.

To change this, update `src/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

Or set the environment variable:

```bash
VITE_API_URL=https://api.zenray.dev npm run dev
```

---

## Pages

### Runs List (`/`)

Displays all pipeline runs with:

- Pipeline name
- Status (running, completed, failed)
- Duration
- Step count
- Timestamp

### Run Details (`/runs/:id`)

Shows a single run with:

- Step timeline visualization
- Step-by-step breakdown
- Candidate counts per step
- Drop summary

### Step Details (`/runs/:runId/steps/:stepId`)

Deep dive into a step:

- All candidates entering the step
- Dropped candidates with reasons
- Scores and rankings
- Raw metadata

### Compare (`/compare`)

Side-by-side comparison of two runs:

- Diff view of steps
- Candidate overlap analysis
- Performance comparison

---

## Development

### Type Check

```bash
npm run build
```

(TypeScript checking is part of the build process)

### Format Code

```bash
npx prettier --write src/
```

### Lint

```bash
npx eslint src/
```

