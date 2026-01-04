import { Router, Request, Response } from 'express'
import * as db from '../db.js'
import * as cache from '../cache.js'
import * as blobStore from '../blob-store.js'
import type { StepSummary } from '../models.js'

const router = Router()

// List steps
router.get('/', async (req: Request, res: Response) => {
  try {
    const { kind, run_id, min_drop_ratio, max_drop_ratio, limit = '100', offset = '0' } = req.query

    const steps = await db.searchSteps({
      kind: kind as string | undefined,
      run_id: run_id as string | undefined,
      min_drop_ratio: min_drop_ratio ? parseFloat(min_drop_ratio as string) : undefined,
      max_drop_ratio: max_drop_ratio ? parseFloat(max_drop_ratio as string) : undefined,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    })

    res.json(steps.map(toStepSummary))
  } catch (err) {
    console.error('Error listing steps:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Get step detail
router.get('/:stepId', async (req: Request, res: Response) => {
  try {
    const { stepId } = req.params
    const cacheKey = cache.stepKey(stepId)

    const cached = await cache.cacheGet(cacheKey)
    if (cached) {
      return res.json(cached)
    }

    const step = await db.getStep(stepId)
    if (!step) {
      return res.status(404).json({ error: `Step ${stepId} not found` })
    }

    let candidateSet = null
    if (step.candidate_set_ref) {
      candidateSet = await blobStore.loadCandidateSet(stepId)
    }

    const artifactRecords = await db.getArtifactsForStep(stepId)
    const artifacts: Record<string, unknown>[] = []
    for (const art of artifactRecords) {
      const content = await blobStore.loadArtifact(art.artifact_id as string)
      if (content) artifacts.push(content as Record<string, unknown>)
    }

    const result = {
      step,
      candidate_set: candidateSet,
      artifacts: artifacts.length > 0 ? artifacts : null,
    }

    await cache.cacheSet(cacheKey, result, cache.CACHE_TTL_MEDIUM)

    res.json(result)
  } catch (err) {
    console.error('Error getting step:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Get step candidates
router.get('/:stepId/candidates', async (req: Request, res: Response) => {
  try {
    const { stepId } = req.params

    const step = await db.getStep(stepId)
    if (!step) {
      return res.status(404).json({ error: `Step ${stepId} not found` })
    }

    const candidateSet = await blobStore.loadCandidateSet(stepId)
    if (!candidateSet) {
      return res.json({ message: 'No candidate set recorded for this step' })
    }

    res.json(candidateSet)
  } catch (err) {
    console.error('Error getting candidates:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

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

