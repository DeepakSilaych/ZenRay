import { Router, Request, Response } from 'express'
import * as db from '../db.js'
import * as cache from '../cache.js'
import * as blobStore from '../blob-store.js'
import type { RunSummary, StepSummary } from '../models.js'

const router = Router()

// List runs
router.get('/', async (req: Request, res: Response) => {
  try {
    const { pipeline_name, status, start_time, end_time, limit = '100', offset = '0' } = req.query

    const cacheKey = cache.runsListKey(
      pipeline_name as string | undefined,
      status as string | undefined
    )

    if (parseInt(offset as string) === 0) {
      const cached = await cache.cacheGet<RunSummary[]>(cacheKey)
      if (cached) {
        return res.json(cached.slice(0, parseInt(limit as string)))
      }
    }

    const runs = await db.searchRuns({
      pipeline_name: pipeline_name as string | undefined,
      status: status as string | undefined,
      start_time: start_time as string | undefined,
      end_time: end_time as string | undefined,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    })

    const result: RunSummary[] = []
    for (const run of runs) {
      const stepCount = await db.countStepsForRun(run.run_id as string)
      result.push({
        run_id: run.run_id as string,
        pipeline_name: run.pipeline_name as string,
        version: run.version as string | null,
        status: run.status as string,
        started_at: run.started_at as string,
        ended_at: run.ended_at as string | null,
        tags: run.tags as Record<string, string> | null,
        step_count: stepCount,
      })
    }

    if (parseInt(offset as string) === 0) {
      await cache.cacheSet(cacheKey, result, cache.CACHE_TTL_SHORT)
    }

    res.json(result)
  } catch (err) {
    console.error('Error listing runs:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Get run detail
router.get('/:runId', async (req: Request, res: Response) => {
  try {
    const { runId } = req.params
    const cacheKey = cache.runDetailKey(runId)

    const cached = await cache.cacheGet(cacheKey)
    if (cached) {
      return res.json(cached)
    }

    const run = await db.getRun(runId)
    if (!run) {
      return res.status(404).json({ error: `Run ${runId} not found` })
    }

    const steps = await db.getStepsForRun(runId)
    const stepSummaries = steps.map(toStepSummary)

    const result = { run, steps: stepSummaries }

    const ttl = ['SUCCESS', 'FAILURE'].includes(run.status as string)
      ? cache.CACHE_TTL_LONG
      : cache.CACHE_TTL_SHORT

    await cache.cacheSet(cacheKey, result, ttl)

    res.json(result)
  } catch (err) {
    console.error('Error getting run:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Trace candidate through run
router.get('/:runId/trace', async (req: Request, res: Response) => {
  try {
    const { runId } = req.params
    const { q } = req.query

    if (!q) {
      return res.status(400).json({ error: 'Query parameter q is required' })
    }

    const run = await db.getRun(runId)
    if (!run) {
      return res.status(404).json({ error: `Run ${runId} not found` })
    }

    const steps = await db.getStepsForRun(runId)
    const qLower = (q as string).toLowerCase()
    const journey: Record<string, unknown>[] = []

    for (const step of steps) {
      const stepId = step.step_id as string
      const candidateSet = await blobStore.loadCandidateSet(stepId)
      if (!candidateSet) continue

      const foundInKept = searchCandidates(
        (candidateSet.top_kept as Record<string, unknown>[]) || [],
        qLower
      )
      const foundInDropped = searchCandidates(
        (candidateSet.top_dropped as Record<string, unknown>[]) || [],
        qLower
      )

      let dropReason: string | null = null
      const droppedByReason = (candidateSet.dropped_by_reason as Record<string, Record<string, unknown>[]>) || {}
      for (const [reason, candidates] of Object.entries(droppedByReason)) {
        const matches = searchCandidates(candidates || [], qLower)
        if (matches.length > 0) {
          foundInDropped.push(...matches)
          dropReason = reason
          break
        }
      }

      if (foundInKept.length > 0 || foundInDropped.length > 0) {
        journey.push({
          step_id: stepId,
          step_name: step.name,
          step_kind: step.kind,
          status: foundInKept.length > 0 ? 'kept' : 'dropped',
          drop_reason: foundInDropped.length > 0 ? dropReason : null,
          candidate: foundInKept[0] || foundInDropped[0] || null,
        })
      }
    }

    res.json({
      query: q,
      run_id: runId,
      found: journey.length > 0,
      journey,
    })
  } catch (err) {
    console.error('Error tracing candidate:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

function searchCandidates(
  candidates: Record<string, unknown>[],
  query: string
): Record<string, unknown>[] {
  const matches: Record<string, unknown>[] = []
  for (const c of candidates) {
    if (typeof c !== 'object' || c === null) continue
    const searchable = [
      String(c.id || ''),
      String(c.name || ''),
      String(c.title || ''),
    ]
    if (searchable.some(s => s.toLowerCase().includes(query))) {
      matches.push(c)
    }
  }
  return matches
}

function toStepSummary(step: Record<string, unknown>): StepSummary {
  const inp = step.input_count as number | null
  const out = step.output_count as number | null
  let dropRatio: number | null = null

  if (inp && inp > 0 && out !== null && out <= inp) {
    dropRatio = Math.round((1 - out / inp) * 10000) / 10000
  }

  return {
    step_id: step.step_id as string,
    run_id: step.run_id as string,
    kind: step.kind as string,
    name: step.name as string,
    input_count: inp,
    output_count: out,
    drop_ratio: dropRatio,
    status: step.status as string,
    duration_ms: step.duration_ms as number | null,
  }
}

export default router

