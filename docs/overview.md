# X-Ray Overview

X-Ray is an observability system for **multi-step ML/LLM pipelines**. It captures:

- **Runs**: an execution of a pipeline (start/end, status, tags, input/output summaries).
- **Steps**: units inside a run (kind/name, timing, metrics).
- **Candidate sets**: what went **in**, what was **kept**, what was **dropped** (and **why**), plus score distributions.
- **Artifacts**: prompts, responses, configs, debug payloads, errors, etc.

## What you can do in the UI

See [`frontend/features.md`](./frontend/features.md).

## What gets ingested

The SDK emits **run events** and **step events** to the backend ingest endpoint. The backend persists metadata and stores large payloads in object storage. See:

- Backend: [`backend/overview.md`](./backend/overview.md)
- Storage: [`backend/storage.md`](./backend/storage.md)
- SDK: [`sdk/overview.md`](./sdk/overview.md)

## Existing design docs

- [`problem_statement.md`](./problem_statement.md)
- [`PRD.md`](./PRD.md)
- [`solution.md`](./solution.md)

## Repository & architecture

- Repo structure: [`repo-structure.md`](./repo-structure.md)
- System architecture: [`architecture.md`](./architecture.md)
