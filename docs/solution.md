# Navigation

- Back to docs index: [`index.md`](./index.md)
- Overview: [`overview.md`](./overview.md)
- Repo structure: [`repo-structure.md`](./repo-structure.md)
- Architecture: [`architecture.md`](./architecture.md)

Below is an **ARCHITECTURE.md-style** architecture for an **X-Ray SDK + API** that explains *why* a multi-step, non-deterministic pipeline produced an output (not just what happened). This is tailored to the take-home brief: capture step inputs/candidates/filters/outcomes/reasoning  and support debugging cases like “phone case matched to laptop stand” , plus queryability (“filter eliminated >90%”)  and scale concerns (5,000 → 30) .

---

# X-Ray Architecture

## 1) Goals

**Primary goal:** make multi-step decision pipelines debuggable by capturing **business-level decision context** (candidates, filters, ranking, LLM reasoning), not just function timings. 

**Must support:**

* Heterogeneous pipelines (competitor selection, categorization, listing optimization) 
* Cross-pipeline queries like “filter step eliminated > 90% of candidates” 
* High fanout steps (5,000 candidates) without exploding cost 
* Dev-friendly instrumentation + safe failure when backend is down 

---

## 2) High-level System

```
Application code
   |
   |  (SDK emits Run/Step events + optional heavy payloads)
   v
X-Ray SDK  ---> local async buffer (in-mem + optional disk spill)
   |
   v
Ingest API (stateless)  ---> queue/log (Kafka/SQS/PubSub)
   |                          |
   |                          v
   |                      Indexer/Processor
   v                          |
Blob store (S3/GCS) <---------+-----> Query Store (ClickHouse/Postgres)
                                    |
                                    v
                                Query API (REST)
```

### Why this split?

* **Ingest API is thin** so instrumentation never blocks product flows.
* **Queue decouples spikes** (non-deterministic steps often bursty).
* **Two storage tiers**:

  * **Query Store**: cheap to filter/aggregate across runs/steps.
  * **Blob Store**: holds large candidate payloads when needed (5k candidates). 

---

## 3) Core Data Model (and why)

### 3.1 Entities

**Run**

* One end-to-end execution (e.g., “competitor selection” run). 
* Fields: `run_id`, `pipeline`, `pipeline_version`, `tenant`, `start_ts`, `end_ts`, `status`, `root_input_ref`, `final_output_ref`, `tags`

**Step**

* A logical decision unit (keyword generation, retrieval, filter, rank, LLM judge, select).
* Fields:

  * Identity/shape: `step_id`, `run_id`, `parent_step_id`, `name`
  * **Standardized kind**: `kind ∈ {INGEST, RETRIEVE, TRANSFORM, FILTER, RANK, JUDGE, SELECT, LLM_CALL, TOOL_CALL}`
  * Timing/outcome: `start_ts`, `end_ts`, `status`
  * **Required metrics for queryability**: `input_count`, `output_count`, `drop_ratio`
  * Optional: `model`, `prompt_ref`, `config_ref`, `error_ref`

**CandidateSet (optional heavy)**

* Represents a set before/after a step (especially retrieve/filter/rank).
* Fields:

  * `candidate_set_id`, `step_id`
  * `mode ∈ {SUMMARY, TOP_K, FULL}`
  * `stats`: `{n_in, n_out, reason_counts, score_histogram, topK_kept_refs, topK_dropped_refs}`
  * `blob_ref` (only if FULL or large TOP_K data)

**Decision**

* For steps that choose/commit output (select best competitor).
* Fields: `chosen_ids`, `decision_reasoning` (text + optional structured signals)

**Artifact**

* Any payload: input objects, prompts, LLM responses, configs, intermediate tables.
* Stored as refs (`artifact_ref`) pointing to blob store objects.

---

### 3.2 Why “Run → Steps → (CandidateSets/Artifacts)”?

Because the debugging questions are **step-local** (“which step went wrong?”) but also need **run context**. The brief explicitly wants to capture decision context per step (inputs, candidates, filters, outcomes, reasoning)  and debug wrong matches like phone case vs laptop stand by inspecting which step failed .

This model gives:

* **Fast cross-run analytics** on Step metadata (drop ratios, durations, statuses)
* **Deep drill-down** via CandidateSet/Artifacts only when needed

#### Alternatives considered (and what breaks)

1. **Store everything as unstructured logs**

   * Easy to emit, hard to query (“filter eliminated >90%”) across pipelines. 
2. **A rigid schema per pipeline**

   * Breaks general-purpose requirement (many pipelines, varying steps). 
3. **Only store full candidate dumps**

   * Too expensive at 5,000-candidate steps; kills adoption. 

So we enforce a **small required “query spine”** on every Step, and make everything else extensible via JSON + artifacts.

---

## 4) Queryability Across Pipelines

The key is a **contract**: every step must provide:

* `kind` (standard enum)
* `input_count`, `output_count`, `drop_ratio` (derived if not provided)
* `pipeline`, `pipeline_version`
* optional `tags` and `metrics.<custom_name>`

Then queries become pipeline-agnostic.

### Example query: “filter eliminated > 90%”

Filter steps are `kind=FILTER`, and drop ratio is indexed.

* Condition: `kind = "FILTER" AND drop_ratio > 0.90` 
* Works even if one pipeline calls it “PriceGate” and another calls it “HeuristicPrune”.

**Constraint on developers:** you can name steps anything, but you must assign the correct `kind` and counts.

---

## 5) Performance & Scale (5,000 → 30)

For CandidateSets, we support **capture modes**:

* **SUMMARY (default for large N)**
  Store: counts, reason_counts, score histograms, top-K examples (kept + dropped), and a stable sample.
* **TOP_K**
  Store: full details for top-K kept and top-K dropped (by score or “closest to threshold”).
* **FULL (explicit opt-in)**
  Store every candidate with accept/reject + reasons (goes to blob store).

This directly addresses the “capturing full details for all 5,000 might be expensive” constraint .

### Who decides what is captured?

Both:

* **System defaults**: if `input_count > N` auto-switch to SUMMARY and store only top-K + aggregates.
* **Developer override**: step-level config: `capture_mode`, `top_k`, `sampling_rate`, `redaction`.

This is important because some teams will happily pay cost for FULL in staging, but not in prod.

---

## 6) Debugging Walkthrough (phone case matched to laptop stand)

Given the competitor flow (keywords → retrieve → filter/rank → LLM judge → select) , a bad match happens (phone case ↔ laptop stand). 

### What you’d do in X-Ray

1. **Fetch the run summary**

* See ordered steps with:

  * step `kind`, name, duration
  * `input_count`, `output_count`, `drop_ratio`
  * outputs/chosen competitor ID

2. **Check “where the set drifted”**

* Inspect CandidateSet stats at each step:

  * After **keyword generation**: keywords + reasoning (artifact)
  * After **retrieval**: top retrieved candidates (are laptop stands showing up already?)
  * After **filters**: did filters remove legitimate laptop-stand competitors and keep nonsense?
  * After **LLM judge**: what did it say, and which candidates did it wrongly accept?

3. **Most common root causes you’ll spot quickly**

* **Bad keywords** (LLM step): keywords include “stand”, “laptop accessories” ⇒ retrieval polluted early.
* **Over-aggressive filters**: drop_ratio ~0.99 and reason_counts show “category_mismatch” incorrectly high.
* **Ranking bug**: top kept candidates have low category similarity; score distribution is off.
* **LLM judge hallucination**: LLM reasoning says “compatible accessory” despite category mismatch.

The point: you can localize failure to a specific step rather than guessing. 

---

## 7) Developer Experience (integration)

This is explicitly required: minimal vs full instrumentation + backend down behavior. 

### Minimal instrumentation (5–10 minutes)

* Wrap pipeline entrypoint:

  * `run = xray.start_run(pipeline="competitor_selection", input=...)`
* Wrap each major stage:

  * `step = run.step(kind="RETRIEVE", name="catalog_search")`
  * set `input_count/output_count`
* End run:

  * `run.finish(output=best_competitor)`

**You instantly get:** step timeline + drop ratios + outputs, enabling cross-run queries.

### Full instrumentation (best debugging)

* Attach artifacts:

  * LLM prompt/response refs
  * configs used (thresholds)
* Capture CandidateSets with SUMMARY/TOP_K
* Record Decision reasoning:

  * textual reasoning + key signals (scores, thresholds crossed)

### Backend unavailable

SDK is **fail-open**:

* Never blocks the pipeline (async buffer)
* Retries with backoff
* Optional disk spill for durability (bounded)
* If buffer full: drop low-priority payloads first (FULL candidate dumps), keep Step spine

This preserves product reliability while keeping as much X-Ray as possible.

---

## 8) API Spec (minimal but useful)

### Ingest

`POST /v1/ingest`

* Body: gzip JSON batch of events: `{runs:[...], steps:[...], candidate_sets:[...], artifacts:[...]}`
* Returns: `{accepted: n, dropped: m, errors:[...]}`
* Supports idempotency: `Idempotency-Key` header

### Query

`GET /v1/runs/{run_id}`

* Returns run summary + step list + lightweight CandidateSet stats

`GET /v1/runs/search?...`

* Filters: `pipeline`, `time_range`, `status`, tags
* Step predicates: `step.kind=FILTER`, `step.drop_ratio_gt=0.9` 

`GET /v1/steps/search?...`

* Directly find suspicious steps across all runs

`GET /v1/candidate_sets/{id}`

* Fetch TOP_K/FULL details (loads from blob store)

---

## 9) What Next (if shipping for real)

* **UI/Explorer**: run timeline + candidate diffs + “where did it go wrong?” suggestions
* **Compare runs**: same input across versions (A/B) to see which step changed
* **Anomaly detection**: alert when drop_ratio spikes or LLM judge flips often
* **Schema registry + linting**: enforce `kind`/counts, prevent “queryability rot”
* **RBAC + PII controls**: redaction policies at SDK and server

---

If you want, I can also convert this into an even tighter **1–2 page** ARCHITECTURE.md (more skimmable, less prose), but the design and reasoning above already hits the required points from the prompt. 
