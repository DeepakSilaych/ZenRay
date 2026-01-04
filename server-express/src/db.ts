import { Pool, PoolClient } from 'pg'
import { config } from './config.js'

let pool: Pool | null = null

export async function initDb(): Promise<void> {
  pool = new Pool({
    host: config.postgres.host,
    port: config.postgres.port,
    user: config.postgres.user,
    password: config.postgres.password,
    database: config.postgres.database,
    min: 5,
    max: 20,
  })

  const client = await pool.connect()
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        pipeline_name TEXT NOT NULL,
        version TEXT,
        status TEXT NOT NULL,
        started_at TIMESTAMPTZ NOT NULL,
        ended_at TIMESTAMPTZ,
        tags JSONB,
        input_summary JSONB,
        final_output JSONB
      );
      
      CREATE TABLE IF NOT EXISTS steps (
        step_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
        parent_step_id TEXT,
        kind TEXT NOT NULL,
        name TEXT NOT NULL,
        input_count INTEGER,
        output_count INTEGER,
        status TEXT NOT NULL,
        duration_ms INTEGER,
        started_at TIMESTAMPTZ,
        ended_at TIMESTAMPTZ,
        metrics JSONB,
        candidate_set_ref TEXT
      );
      
      CREATE TABLE IF NOT EXISTS artifacts (
        artifact_id TEXT PRIMARY KEY,
        step_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        type TEXT NOT NULL,
        blob_ref TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
      );
      
      CREATE INDEX IF NOT EXISTS idx_runs_pipeline ON runs(pipeline_name);
      CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
      CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at DESC);
      CREATE INDEX IF NOT EXISTS idx_steps_run ON steps(run_id);
      CREATE INDEX IF NOT EXISTS idx_steps_kind ON steps(kind);
      CREATE INDEX IF NOT EXISTS idx_artifacts_step ON artifacts(step_id);
    `)
  } finally {
    client.release()
  }
}

export async function closeDb(): Promise<void> {
  if (pool) {
    await pool.end()
    pool = null
  }
}

export function getPool(): Pool {
  if (!pool) throw new Error('Database pool not initialized')
  return pool
}

// Run operations
export async function upsertRun(run: Record<string, unknown>): Promise<void> {
  const client = await getPool().connect()
  try {
    await client.query(`
      INSERT INTO runs (run_id, pipeline_name, version, status, started_at, ended_at, tags, input_summary, final_output)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      ON CONFLICT(run_id) DO UPDATE SET
        pipeline_name = EXCLUDED.pipeline_name,
        version = EXCLUDED.version,
        status = EXCLUDED.status,
        ended_at = COALESCE(EXCLUDED.ended_at, runs.ended_at),
        tags = EXCLUDED.tags,
        input_summary = EXCLUDED.input_summary,
        final_output = COALESCE(EXCLUDED.final_output, runs.final_output)
    `, [
      run.run_id,
      run.pipeline_name,
      run.version || null,
      run.status,
      run.started_at,
      run.ended_at || null,
      run.tags ? JSON.stringify(run.tags) : null,
      run.input_summary ? JSON.stringify(run.input_summary) : null,
      run.final_output ? JSON.stringify(run.final_output) : null,
    ])
  } finally {
    client.release()
  }
}

export async function getRun(runId: string): Promise<Record<string, unknown> | null> {
  const client = await getPool().connect()
  try {
    const result = await client.query('SELECT * FROM runs WHERE run_id = $1', [runId])
    if (result.rows.length === 0) return null
    return rowToRun(result.rows[0])
  } finally {
    client.release()
  }
}

export async function searchRuns(params: {
  pipeline_name?: string
  status?: string
  start_time?: string
  end_time?: string
  limit?: number
  offset?: number
}): Promise<Record<string, unknown>[]> {
  const client = await getPool().connect()
  try {
    let query = 'SELECT * FROM runs WHERE 1=1'
    const values: unknown[] = []
    let idx = 1

    if (params.pipeline_name) {
      query += ` AND pipeline_name = $${idx++}`
      values.push(params.pipeline_name)
    }
    if (params.status) {
      query += ` AND status = $${idx++}`
      values.push(params.status)
    }
    if (params.start_time) {
      query += ` AND started_at >= $${idx++}`
      values.push(params.start_time)
    }
    if (params.end_time) {
      query += ` AND started_at <= $${idx++}`
      values.push(params.end_time)
    }

    query += ` ORDER BY started_at DESC LIMIT $${idx++} OFFSET $${idx++}`
    values.push(params.limit || 100, params.offset || 0)

    const result = await client.query(query, values)
    return result.rows.map(rowToRun)
  } finally {
    client.release()
  }
}

function rowToRun(row: Record<string, unknown>): Record<string, unknown> {
  return {
    run_id: row.run_id,
    pipeline_name: row.pipeline_name,
    version: row.version,
    status: row.status,
    started_at: row.started_at instanceof Date ? row.started_at.toISOString() : row.started_at,
    ended_at: row.ended_at instanceof Date ? row.ended_at.toISOString() : row.ended_at,
    tags: typeof row.tags === 'string' ? JSON.parse(row.tags) : row.tags,
    input_summary: typeof row.input_summary === 'string' ? JSON.parse(row.input_summary) : row.input_summary,
    final_output: typeof row.final_output === 'string' ? JSON.parse(row.final_output) : row.final_output,
  }
}

// Step operations
export async function upsertStep(step: Record<string, unknown>): Promise<void> {
  const client = await getPool().connect()
  try {
    await client.query(`
      INSERT INTO steps (step_id, run_id, parent_step_id, kind, name, input_count, output_count, status, duration_ms, started_at, ended_at, metrics, candidate_set_ref)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      ON CONFLICT(step_id) DO UPDATE SET
        kind = EXCLUDED.kind,
        name = EXCLUDED.name,
        input_count = COALESCE(EXCLUDED.input_count, steps.input_count),
        output_count = COALESCE(EXCLUDED.output_count, steps.output_count),
        status = EXCLUDED.status,
        duration_ms = COALESCE(EXCLUDED.duration_ms, steps.duration_ms),
        ended_at = COALESCE(EXCLUDED.ended_at, steps.ended_at),
        metrics = EXCLUDED.metrics,
        candidate_set_ref = COALESCE(EXCLUDED.candidate_set_ref, steps.candidate_set_ref)
    `, [
      step.step_id,
      step.run_id,
      step.parent_step_id || null,
      step.kind,
      step.name,
      step.input_count ?? null,
      step.output_count ?? null,
      step.status,
      step.duration_ms ?? null,
      step.started_at || null,
      step.ended_at || null,
      step.metrics ? JSON.stringify(step.metrics) : null,
      step.candidate_set_ref || null,
    ])
  } finally {
    client.release()
  }
}

export async function getStep(stepId: string): Promise<Record<string, unknown> | null> {
  const client = await getPool().connect()
  try {
    const result = await client.query('SELECT * FROM steps WHERE step_id = $1', [stepId])
    if (result.rows.length === 0) return null
    return rowToStep(result.rows[0])
  } finally {
    client.release()
  }
}

export async function getStepsForRun(runId: string): Promise<Record<string, unknown>[]> {
  const client = await getPool().connect()
  try {
    const result = await client.query(
      'SELECT * FROM steps WHERE run_id = $1 ORDER BY started_at ASC',
      [runId]
    )
    return result.rows.map(rowToStep)
  } finally {
    client.release()
  }
}

export async function searchSteps(params: {
  kind?: string
  run_id?: string
  min_drop_ratio?: number
  max_drop_ratio?: number
  limit?: number
  offset?: number
}): Promise<Record<string, unknown>[]> {
  const client = await getPool().connect()
  try {
    let query = 'SELECT * FROM steps WHERE 1=1'
    const values: unknown[] = []
    let idx = 1

    if (params.kind) {
      query += ` AND kind = $${idx++}`
      values.push(params.kind)
    }
    if (params.run_id) {
      query += ` AND run_id = $${idx++}`
      values.push(params.run_id)
    }
    if (params.min_drop_ratio !== undefined) {
      query += ` AND input_count > 0 AND (1.0 - output_count::float / input_count::float) >= $${idx++}`
      values.push(params.min_drop_ratio)
    }
    if (params.max_drop_ratio !== undefined) {
      query += ` AND input_count > 0 AND (1.0 - output_count::float / input_count::float) <= $${idx++}`
      values.push(params.max_drop_ratio)
    }

    query += ` LIMIT $${idx++} OFFSET $${idx++}`
    values.push(params.limit || 100, params.offset || 0)

    const result = await client.query(query, values)
    return result.rows.map(rowToStep)
  } finally {
    client.release()
  }
}

export async function countStepsForRun(runId: string): Promise<number> {
  const client = await getPool().connect()
  try {
    const result = await client.query('SELECT COUNT(*) as count FROM steps WHERE run_id = $1', [runId])
    return parseInt(result.rows[0].count)
  } finally {
    client.release()
  }
}

function rowToStep(row: Record<string, unknown>): Record<string, unknown> {
  return {
    step_id: row.step_id,
    run_id: row.run_id,
    parent_step_id: row.parent_step_id,
    kind: row.kind,
    name: row.name,
    input_count: row.input_count,
    output_count: row.output_count,
    status: row.status,
    duration_ms: row.duration_ms,
    started_at: row.started_at instanceof Date ? row.started_at.toISOString() : row.started_at,
    ended_at: row.ended_at instanceof Date ? row.ended_at.toISOString() : row.ended_at,
    metrics: typeof row.metrics === 'string' ? JSON.parse(row.metrics) : row.metrics,
    candidate_set_ref: row.candidate_set_ref,
  }
}

// Artifact operations
export async function indexArtifact(
  artifactId: string,
  stepId: string,
  runId: string,
  artifactType: string,
  blobRef: string
): Promise<void> {
  const client = await getPool().connect()
  try {
    await client.query(`
      INSERT INTO artifacts (artifact_id, step_id, run_id, type, blob_ref)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT(artifact_id) DO UPDATE SET blob_ref = EXCLUDED.blob_ref
    `, [artifactId, stepId, runId, artifactType, blobRef])
  } finally {
    client.release()
  }
}

export async function getArtifactsForStep(stepId: string): Promise<Record<string, unknown>[]> {
  const client = await getPool().connect()
  try {
    const result = await client.query(
      'SELECT * FROM artifacts WHERE step_id = $1 ORDER BY created_at',
      [stepId]
    )
    return result.rows
  } finally {
    client.release()
  }
}

