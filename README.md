<p align="center">
  <img src="./assets/logo.svg" alt="ZenRay Logo" width="100" height="100">
</p>

<h1 align="center">ZenRay</h1>

<p align="center">
  <strong>The observability layer for ML pipelines</strong>
</p>

<p align="center">
  <a href="#why-zenray">Why ZenRay</a> •
  <a href="#what-you-get">What You Get</a> •
  <a href="#use-cases">Use Cases</a> •
  <a href="#getting-started">Get Started</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab.svg?style=flat-square" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61dafb.svg?style=flat-square" alt="React 18">
  <img src="https://img.shields.io/badge/license-MIT-22c55e.svg?style=flat-square" alt="MIT License">
</p>

---

## Why ZenRay

Modern ML systems are pipelines. You retrieve 1000 documents, rerank them, filter by relevance, and pass 5 to your LLM. But when something goes wrong—bad answers, missing context, irrelevant results—**you have no idea where to look**.

Traditional logging doesn't help. You end up with gigabytes of unstructured text, no way to trace a single item through the system, and hours of manual investigation.

**ZenRay solves this.**

It gives you a complete audit trail of every decision in your pipeline. For every run, you can see:

- How many candidates entered each stage
- Which items were dropped and why
- What scores were assigned at each step
- The exact path any item took through your system

All with less than 1ms of overhead.

---

## What You Get

### Complete Visibility

Every pipeline run is captured as a trace. Each trace shows the flow of candidates through your stages—retrieval, ranking, filtering, generation. You see exactly what went in and what came out at every step.

### Drop Tracking

When you filter out a candidate, ZenRay records **why**. Low relevance score? Duplicate content? Failed safety check? Every drop reason is captured and aggregated, so you can identify systemic issues at a glance.

### Performance Insights

See how long each stage takes. Identify bottlenecks. Compare runs to understand why one query took 2 seconds and another took 200ms.

### Run Comparison

Select two runs and diff them. See which candidates appeared in one but not the other. Understand how a code change affected your pipeline's behavior.

### Zero Friction Integration

Two Python decorators. That's it. No config files, no YAML, no separate DSL to learn. Your existing code structure stays exactly the same.

---

## Use Cases

### RAG Pipelines

Your retrieval-augmented generation system pulls 100 documents but only 3 reach the LLM. ZenRay shows you exactly which 97 were dropped and why—low embedding similarity, filtered by metadata, or cut off by token limits.

### Search & Ranking

E-commerce search, job matching, content recommendations—any system with multiple ranking stages benefits. Track how a product moves from initial retrieval through L1 ranking, L2 reranking, business rule filters, and personalization.

### AI Agents

When your agent chooses tool A over tool B, you need to understand why. ZenRay captures the decision context: which tools were considered, their relevance scores, and the final selection reasoning.

### Content Moderation

Trace content through safety classifiers, policy filters, and human review queues. When something gets incorrectly flagged or incorrectly approved, you can reconstruct exactly what happened.

### Recommendation Systems

User requests generate hundreds of candidates. They pass through collaborative filtering, content-based ranking, diversity injection, and business constraints. ZenRay shows the full funnel.

---

## How It Works

**1. Instrument your pipeline**  
Add decorators to mark your pipeline entry point and each processing stage. Use helper functions to record drops and scores.

**2. Run normally**  
Execute your code as usual. ZenRay captures data asynchronously in the background. Your pipeline performance is unaffected.

**3. Explore in the dashboard**  
Browse runs by pipeline name, time, or status. Click into any run to see the step-by-step breakdown. Drill down to individual candidates.

**4. Debug faster**  
When something goes wrong, you have the complete picture. No more guessing, no more print statements, no more hours of log archaeology.

---

## Key Benefits

| Benefit                   | Description                                         |
| ------------------------- | --------------------------------------------------- |
| **Faster Debugging**      | Minutes instead of hours to find issues             |
| **Production Visibility** | Understand real-world behavior, not just test cases |
| **Team Alignment**        | Everyone can see what the pipeline is doing         |
| **Regression Detection**  | Compare runs before and after changes               |
| **Audit Trail**           | Every decision is recorded and queryable            |

---

## Architecture

ZenRay consists of four components:

**Python SDK** — Lightweight library that instruments your code and sends traces to the server asynchronously.

**FastAPI Server** — Receives traces, stores metadata in PostgreSQL, and saves candidate blobs to S3-compatible storage (MinIO).

**React Dashboard** — Web UI for browsing runs, inspecting steps, and comparing pipelines.

**Infrastructure** — PostgreSQL for metadata, MinIO for blob storage, Redis for caching and queue management.

---

## Getting Started

See the component READMEs for detailed setup:

| Component                            | Description                                      |
| ------------------------------------ | ------------------------------------------------ |
| [**SDK**](./sdk/README.md)           | Python SDK installation, API reference, examples |
| [**Server**](./server/README.md)     | Backend setup, API endpoints, configuration      |
| [**Dashboard**](./mainapp/README.md) | React app development and features               |
| [**Website**](./web/README.md)       | Landing page and documentation site              |

### Quick Setup

1. Start infrastructure: `docker compose up -d`
2. Start server: `cd server && uvicorn app.main:app --port 8000`
3. Start dashboard: `cd mainapp && npm run dev`
4. Install SDK: `cd sdk && pip install -e .`

---

## Configuration

### SDK Environment Variables

| Variable           | Default                 | Description                        |
| ------------------ | ----------------------- | ---------------------------------- |
| `XRAY_ENDPOINT`    | `http://localhost:8000` | Server URL                         |
| `XRAY_DISABLED`    | `false`                 | Disable all tracing                |
| `XRAY_SAMPLE_RATE` | `1.0`                   | Fraction of runs to trace          |
| `XRAY_TOP_K`       | `10`                    | Max candidates to capture per step |

### Server Environment Variables

| Variable             | Default                 | Description       |
| -------------------- | ----------------------- | ----------------- |
| `XRAY_POSTGRES_HOST` | `localhost`             | PostgreSQL host   |
| `XRAY_S3_ENDPOINT`   | `http://localhost:9000` | MinIO/S3 endpoint |
| `XRAY_REDIS_HOST`    | `localhost`             | Redis host        |

---

## License

MIT © 2024 ZenRay

---

<p align="center">
  <sub>Built with ⚡ for ML engineers who are tired of guessing</sub>
</p>
