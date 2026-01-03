# Navigation

- Back to docs index: [`index.md`](./index.md)
- Overview: [`overview.md`](./overview.md)
- Repo structure: [`repo-structure.md`](./repo-structure.md)
- Architecture: [`architecture.md`](./architecture.md)

Below is a solid **PRD** for an **X-Ray Observability SDK + Backend** that helps teams *pinpoint why* multi-step, non-deterministic pipelines produced bad outputs (LLM + retrieval + filters + ranking).

---

# PRD: X-Ray (Reasoning Observability for Decision Pipelines)

## 1) Problem

Modern pipelines (search/retrieval → filters → rankers → LLM judges → final selection) fail in ways that are **hard to debug**:

* Wrong output (e.g., “phone case matched to laptop stand”) but it’s unclear **which step introduced the error** vs **which step failed to stop it**.
* Existing observability (logs/traces) shows timings, not **decision context** (candidate sets, elimination reasons, model inputs/outputs).
* Teams need **cross-pipeline queryability** (“which filters are dropping >90%?”) without building custom dashboards per pipeline.
* Capturing full candidate details at scale can be **too expensive** (e.g., 5,000 candidates per step).

## 2) Goal

Provide an SDK + backend that captures **decision context** per pipeline step so engineers can:

1. **Pinpoint the divergence step** (where the output becomes “wrong”)
2. Identify **which rule/model/threshold** caused the divergence
3. Query suspicious patterns across all pipelines
4. Do this with minimal overhead and safe failure behavior

## 3) Non-goals (for V1)

* Automatically “fixing” pipelines or suggesting changes (we can add later).
* Full replay/execution of pipelines (future).
* Full UI as a must-have (V1 can ship with basic viewer/API; UI can come V1.5).

---

## 4) Users & Personas

### Primary

* **ML Engineer / Applied Scientist**: debugs ranking + LLM judge behavior
* **Backend Engineer**: owns retrieval/filtering infra; needs quick root-cause
* **Product Engineer**: integrates SDK into pipelines; wants minimal friction

### Secondary

* **PM / Analyst**: wants aggregate health metrics, regressions, drop spikes
* **Support / Ops**: uses run links to investigate customer reports

---

## 5) Key Use Cases

### UC1: Debug a single bad run (pinpoint cause)

Given a run with wrong final output:

* See step timeline + candidate-set transitions
* Identify first step where wrong candidates appear or correct ones disappear
* Inspect the step’s elimination reasons / score breakdown / LLM verdict

### UC2: Find systemic issues across runs/pipelines

Examples:

* “Filters dropping >90% candidates”
* “LLM judge acceptance rate spiked after model change”
* “Ranking feature causing category mismatch in top-10”

### UC3: Compare versions (regression)

* Same pipeline, new version → compare step-by-step deltas in:

  * drop ratio
  * top kept/dropped examples
  * score distribution
  * decision outcome

---

## 6) Product Requirements

### 6.1 Core Concepts

**Run**: one pipeline execution
**Step**: meaningful stage (retrieve/filter/rank/judge/select)
**CandidateSet**: before/after set of candidates with summary/top-k/full modes
**Artifacts**: prompt, model response, configs, intermediate payloads
**Decision**: final choice + reasoning/attribution

### 6.2 Instrumentation Levels

**Minimal (10 minutes)**

* Start run, create steps, record counts + status + timings, store final output

**Full (best debugging)**

* CandidateSet capture (summary/topK)
* Filter reasons per candidate (for sampled/topK)
* Rank score breakdown (topK)
* LLM prompt/response artifacts + structured verdict fields

### 6.3 Step Contract (mandatory for queryability)

Every step must emit:

* `kind` (enum: RETRIEVE, FILTER, RANK, LLM_CALL, JUDGE, SELECT, TRANSFORM, TOOL_CALL, etc.)
* `input_count`, `output_count` (or enough to compute)
* `status`, `duration`
* optional `metrics` map (custom)

### 6.4 Candidate Capture Modes (cost control)

* **SUMMARY (default for large N)**: counts, reason histogram, score histogram, sample + top kept/dropped examples
* **TOP_K**: full details for topK kept + topK dropped-near-threshold
* **FULL**: everything (explicit opt-in; typically staging)

### 6.5 Failure Behavior (must)

* SDK is **fail-open**: never blocks production traffic
* Async buffering + retries + backoff
* Optional disk spill with bounded size
* If buffer full: drop heavy payloads (FULL candidate dumps) first; keep the “query spine”

---

## 7) Functional Requirements (V1)

### SDK

* Start/end Run
* Create Step spans with parent-child nesting
* Attach artifacts (JSON/text/blob refs)
* CandidateSet helper:

  * `record_candidates_in(...)`
  * `record_candidates_out(...)`
  * `record_drop_reasons(...)`
  * `record_scores(...)`
* Automatic mode selection based on N and config
* Redaction hooks for PII

### Backend

* Ingest endpoint (batch)
* Event validation + schema versioning
* Storage:

  * Query store for runs/steps metadata
  * Blob store for heavy artifacts/candidate dumps
* Query API:

  * search runs (by time, pipeline, tags, status)
  * search steps (by kind, drop ratio, metrics thresholds)
  * fetch run detail (timeline + step summaries)
  * fetch candidate set detail (topK/full)

---

## 8) Non-Functional Requirements

### Performance

* SDK overhead: target **<1–2ms** per step instrumentation on hot path (excluding optional heavy serialization)
* Sampling supported (global + per-step)

### Scale

* Support large candidate sets (thousands)
* Sustain bursty ingestion via queue/log

### Reliability

* 99.9% ingest availability target (but SDK must not rely on it)
* Idempotency keys to avoid duplicates on retries

### Security/Privacy

* PII redaction + allowlist fields
* Tenant isolation (authZ on run/step access)
* Encryption at rest (blob store) and in transit
* Configurable retention periods

---

## 9) UX / Viewer (V1 “good enough”)

**Run Detail Page**

* Header: pipeline, version, input summary, final output
* Timeline list of steps:

  * kind, name, duration
  * in/out counts + drop ratio
  * expandable: candidate stats + topK examples
  * links to artifacts (prompt/response/config)

**Step Drilldown**

* Candidate diff view: kept vs dropped
* Reason histogram (filters)
* Score histogram + top contributors (rank)
* LLM verdict + rationale + selected evidence fields

If UI is out of scope for first sprint, expose via API and ship a lightweight CLI.

---

## 10) Metrics (Success Criteria)

### Adoption

* % pipelines instrumented (minimal vs full)
* # runs ingested/day, # active teams

### Debugging Impact

* Median time-to-root-cause (before vs after)
* % incidents where “divergence step” identified
* Reduction in “unknown cause” postmortems

### Data Quality

* % steps missing mandatory fields
* Event validation error rate
* Duplicate rate after retries

### Cost

* Avg bytes per run
* Blob-store utilization by capture mode
* % runs using FULL in prod (should be low)

