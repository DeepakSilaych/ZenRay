import aiosqlite
import json
from typing import Optional
from pathlib import Path

DB_PATH = Path("data/xray.db")
_db: Optional[aiosqlite.Connection] = None

async def init_db():
    global _db
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row
    
    await _db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            pipeline_name TEXT NOT NULL,
            version TEXT,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            tags TEXT,
            input_summary TEXT,
            final_output TEXT
        );
        
        CREATE TABLE IF NOT EXISTS steps (
            step_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL REFERENCES runs(run_id),
            parent_step_id TEXT,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            input_count INTEGER,
            output_count INTEGER,
            status TEXT NOT NULL,
            duration_ms INTEGER,
            started_at TEXT,
            ended_at TEXT,
            metrics TEXT,
            candidate_set_ref TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_runs_pipeline ON runs(pipeline_name);
        CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
        CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at);
        CREATE INDEX IF NOT EXISTS idx_steps_run ON steps(run_id);
        CREATE INDEX IF NOT EXISTS idx_steps_kind ON steps(kind);
    """)
    await _db.commit()

async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None

def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db

# --- Run operations ---

async def upsert_run(run: dict):
    db = get_db()
    await db.execute("""
        INSERT INTO runs (run_id, pipeline_name, version, status, started_at, ended_at, tags, input_summary, final_output)
        VALUES (:run_id, :pipeline_name, :version, :status, :started_at, :ended_at, :tags, :input_summary, :final_output)
        ON CONFLICT(run_id) DO UPDATE SET
            pipeline_name = excluded.pipeline_name,
            version = excluded.version,
            status = excluded.status,
            ended_at = COALESCE(excluded.ended_at, runs.ended_at),
            tags = excluded.tags,
            input_summary = excluded.input_summary,
            final_output = COALESCE(excluded.final_output, runs.final_output)
    """, {
        "run_id": run["run_id"],
        "pipeline_name": run["pipeline_name"],
        "version": run.get("version"),
        "status": run["status"],
        "started_at": run["started_at"],
        "ended_at": run.get("ended_at"),
        "tags": json.dumps(run.get("tags")) if run.get("tags") else None,
        "input_summary": json.dumps(run.get("input_summary")) if run.get("input_summary") else None,
        "final_output": json.dumps(run.get("final_output")) if run.get("final_output") else None,
    })
    await db.commit()

async def get_run(run_id: str) -> Optional[dict]:
    db = get_db()
    async with db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return _row_to_run(row)
    return None

async def search_runs(
    pipeline_name: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[dict] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    db = get_db()
    query = "SELECT * FROM runs WHERE 1=1"
    params = []
    
    if pipeline_name:
        query += " AND pipeline_name = ?"
        params.append(pipeline_name)
    if status:
        query += " AND status = ?"
        params.append(status)
    if start_time:
        query += " AND started_at >= ?"
        params.append(start_time)
    if end_time:
        query += " AND started_at <= ?"
        params.append(end_time)
    
    query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        runs = [_row_to_run(r) for r in rows]
    
    # Filter by tags in Python (JSON field)
    if tags:
        runs = [r for r in runs if _tags_match(r.get("tags"), tags)]
    
    return runs

def _row_to_run(row) -> dict:
    return {
        "run_id": row["run_id"],
        "pipeline_name": row["pipeline_name"],
        "version": row["version"],
        "status": row["status"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "tags": json.loads(row["tags"]) if row["tags"] else None,
        "input_summary": json.loads(row["input_summary"]) if row["input_summary"] else None,
        "final_output": json.loads(row["final_output"]) if row["final_output"] else None,
    }

def _tags_match(run_tags: Optional[dict], filter_tags: dict) -> bool:
    if not run_tags:
        return False
    return all(run_tags.get(k) == v for k, v in filter_tags.items())

# --- Step operations ---

async def upsert_step(step: dict):
    db = get_db()
    await db.execute("""
        INSERT INTO steps (step_id, run_id, parent_step_id, kind, name, input_count, output_count, status, duration_ms, started_at, ended_at, metrics, candidate_set_ref)
        VALUES (:step_id, :run_id, :parent_step_id, :kind, :name, :input_count, :output_count, :status, :duration_ms, :started_at, :ended_at, :metrics, :candidate_set_ref)
        ON CONFLICT(step_id) DO UPDATE SET
            kind = excluded.kind,
            name = excluded.name,
            input_count = COALESCE(excluded.input_count, steps.input_count),
            output_count = COALESCE(excluded.output_count, steps.output_count),
            status = excluded.status,
            duration_ms = COALESCE(excluded.duration_ms, steps.duration_ms),
            ended_at = COALESCE(excluded.ended_at, steps.ended_at),
            metrics = excluded.metrics,
            candidate_set_ref = COALESCE(excluded.candidate_set_ref, steps.candidate_set_ref)
    """, {
        "step_id": step["step_id"],
        "run_id": step["run_id"],
        "parent_step_id": step.get("parent_step_id"),
        "kind": step["kind"],
        "name": step["name"],
        "input_count": step.get("input_count"),
        "output_count": step.get("output_count"),
        "status": step["status"],
        "duration_ms": step.get("duration_ms"),
        "started_at": step.get("started_at"),
        "ended_at": step.get("ended_at"),
        "metrics": json.dumps(step.get("metrics")) if step.get("metrics") else None,
        "candidate_set_ref": step.get("candidate_set_ref"),
    })
    await db.commit()

async def get_step(step_id: str) -> Optional[dict]:
    db = get_db()
    async with db.execute("SELECT * FROM steps WHERE step_id = ?", (step_id,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return _row_to_step(row)
    return None

async def get_steps_for_run(run_id: str) -> list[dict]:
    db = get_db()
    async with db.execute(
        "SELECT * FROM steps WHERE run_id = ? ORDER BY started_at ASC",
        (run_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_step(r) for r in rows]

async def search_steps(
    kind: Optional[str] = None,
    run_id: Optional[str] = None,
    min_drop_ratio: Optional[float] = None,
    max_drop_ratio: Optional[float] = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    db = get_db()
    query = "SELECT * FROM steps WHERE 1=1"
    params = []
    
    if kind:
        query += " AND kind = ?"
        params.append(kind)
    if run_id:
        query += " AND run_id = ?"
        params.append(run_id)
    
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        steps = [_row_to_step(r) for r in rows]
    
    # Filter by drop ratio in Python
    if min_drop_ratio is not None or max_drop_ratio is not None:
        steps = [s for s in steps if _drop_ratio_match(s, min_drop_ratio, max_drop_ratio)]
    
    return steps

def _row_to_step(row) -> dict:
    return {
        "step_id": row["step_id"],
        "run_id": row["run_id"],
        "parent_step_id": row["parent_step_id"],
        "kind": row["kind"],
        "name": row["name"],
        "input_count": row["input_count"],
        "output_count": row["output_count"],
        "status": row["status"],
        "duration_ms": row["duration_ms"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "metrics": json.loads(row["metrics"]) if row["metrics"] else None,
        "candidate_set_ref": row["candidate_set_ref"],
    }

def _drop_ratio_match(step: dict, min_ratio: Optional[float], max_ratio: Optional[float]) -> bool:
    if step["input_count"] is None or step["output_count"] is None:
        return False
    if step["input_count"] == 0:
        return False
    ratio = 1 - (step["output_count"] / step["input_count"])
    if min_ratio is not None and ratio < min_ratio:
        return False
    if max_ratio is not None and ratio > max_ratio:
        return False
    return True

async def count_steps_for_run(run_id: str) -> int:
    db = get_db()
    async with db.execute("SELECT COUNT(*) FROM steps WHERE run_id = ?", (run_id,)) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0

