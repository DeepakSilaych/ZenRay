import { Router, Request, Response } from 'express'
import { IngestPayload } from '../models.js'
import * as queue from '../queue.js'
import * as db from '../db.js'
import * as cache from '../cache.js'
import * as blobStore from '../blob-store.js'

const router = Router()

const SUPPORTED_SCHEMA_VERSIONS = new Set(['1.0'])

// Ingest endpoint
router.post('/', async (req: Request, res: Response) => {
  try {
    const payload = IngestPayload.parse(req.body)
    const sync = req.query.sync === 'true'

    if (!SUPPORTED_SCHEMA_VERSIONS.has(payload.schema_version)) {
      return res.status(400).json({
        error: `Unsupported schema version: ${payload.schema_version}. Supported: ${[...SUPPORTED_SCHEMA_VERSIONS].join(', ')}`,
      })
    }

    const runsCount = payload.runs?.length || 0
    const stepsCount = payload.steps?.length || 0

    if (sync) {
      const result = await processSync(payload)
      return res.json(result)
    }

    await queue.enqueueIngest(payload as unknown as Record<string, unknown>)

    res.json({
      accepted_runs: runsCount,
      accepted_steps: stepsCount,
      queued: true,
      errors: [],
    })
  } catch (err) {
    console.error('Error ingesting:', err)
    if (err instanceof Error && err.name === 'ZodError') {
      return res.status(400).json({ error: 'Invalid payload format', details: err })
    }
    res.status(503).json({ error: 'Failed to queue payload' })
  }
})

// Queue stats endpoint
router.get('/stats', async (_req: Request, res: Response) => {
  try {
    const stats = await queue.getQueueStats()
    res.json({
      queue: stats,
      mode: 'async',
      worker: 'running',
    })
  } catch (err) {
    console.error('Error getting stats:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

async function processSync(payload: typeof IngestPayload._type): Promise<Record<string, unknown>> {
  const response = {
    accepted_runs: 0,
    accepted_steps: 0,
    queued: false,
    errors: [] as string[],
  }

  // Process runs
  if (payload.runs) {
    for (const run of payload.runs) {
      try {
        const runDict = {
          run_id: run.run_id,
          pipeline_name: run.pipeline_name,
          version: run.version,
          status: run.status,
          started_at: run.started_at,
          ended_at: run.ended_at,
          tags: run.tags,
          input_summary: run.input_summary,
          final_output: run.final_output,
        }
        await db.upsertRun(runDict)
        await cache.invalidateRun(run.run_id)
        response.accepted_runs++
      } catch (err) {
        response.errors.push(`Run ${run.run_id}: ${err}`)
      }
    }
  }

  // Process steps
  if (payload.steps) {
    for (const step of payload.steps) {
      try {
        let candidateSetRef: string | null = null
        if (step.candidate_set) {
          candidateSetRef = await blobStore.saveCandidateSet(step.step_id, step.candidate_set)
        }

        if (step.artifacts) {
          for (const artifact of step.artifacts) {
            const blobRef = await blobStore.saveArtifact(artifact.artifact_id, {
              step_id: artifact.step_id,
              type: artifact.type,
              content: artifact.content,
            })
            await db.indexArtifact(
              artifact.artifact_id,
              step.step_id,
              step.run_id,
              artifact.type,
              blobRef
            )
          }
        }

        const stepDict = {
          step_id: step.step_id,
          run_id: step.run_id,
          parent_step_id: step.parent_step_id,
          kind: step.kind,
          name: step.name,
          input_count: step.input_count,
          output_count: step.output_count,
          status: step.status,
          duration_ms: step.duration_ms,
          started_at: step.started_at,
          ended_at: step.ended_at,
          metrics: step.metrics,
          candidate_set_ref: candidateSetRef,
        }
        await db.upsertStep(stepDict)
        await cache.invalidateStep(step.step_id, step.run_id)
        response.accepted_steps++
      } catch (err) {
        response.errors.push(`Step ${step.step_id}: ${err}`)
      }
    }
  }

  return response
}

export default router

