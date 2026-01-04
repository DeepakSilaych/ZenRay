import { Router, Request, Response } from 'express'
import * as db from '../db.js'

const router = Router()

router.get('/', async (req: Request, res: Response) => {
  try {
    const { run_a, run_b } = req.query

    if (!run_a || !run_b) {
      return res.status(400).json({ error: 'Both run_a and run_b query parameters are required' })
    }

    const runAData = await db.getRun(run_a as string)
    const runBData = await db.getRun(run_b as string)

    if (!runAData) {
      return res.status(404).json({ error: `Run ${run_a} not found` })
    }
    if (!runBData) {
      return res.status(404).json({ error: `Run ${run_b} not found` })
    }

    const stepsA = await db.getStepsForRun(run_a as string)
    const stepsB = await db.getStepsForRun(run_b as string)

    const stepsAByName = new Map(stepsA.map(s => [s.name as string, s]))
    const stepsBByName = new Map(stepsB.map(s => [s.name as string, s]))

    const allStepNames = [...new Set([
      ...stepsA.map(s => s.name as string),
      ...stepsB.map(s => s.name as string),
    ])]

    const stepComparisons = allStepNames.map(name => {
      const sa = stepsAByName.get(name)
      const sb = stepsBByName.get(name)

      const comparison: Record<string, unknown> = {
        step_name: name,
        in_run_a: !!sa,
        in_run_b: !!sb,
        run_a: sa ? {
          step_id: sa.step_id,
          kind: sa.kind,
          input_count: sa.input_count,
          output_count: sa.output_count,
          drop_ratio: calcDropRatio(sa),
          duration_ms: sa.duration_ms,
          status: sa.status,
        } : null,
        run_b: sb ? {
          step_id: sb.step_id,
          kind: sb.kind,
          input_count: sb.input_count,
          output_count: sb.output_count,
          drop_ratio: calcDropRatio(sb),
          duration_ms: sb.duration_ms,
          status: sb.status,
        } : null,
        deltas: sa && sb ? {
          output_count: ((sb.output_count as number) || 0) - ((sa.output_count as number) || 0),
          drop_ratio: Math.round(((calcDropRatio(sb) || 0) - (calcDropRatio(sa) || 0)) * 10000) / 10000,
          duration_ms: ((sb.duration_ms as number) || 0) - ((sa.duration_ms as number) || 0),
        } : null,
      }

      return comparison
    })

    const totalDurationA = stepsA.reduce((sum, s) => sum + ((s.duration_ms as number) || 0), 0)
    const totalDurationB = stepsB.reduce((sum, s) => sum + ((s.duration_ms as number) || 0), 0)

    res.json({
      run_a: {
        run_id: run_a,
        pipeline_name: runAData.pipeline_name,
        version: runAData.version,
        status: runAData.status,
        total_steps: stepsA.length,
        total_duration_ms: totalDurationA,
        final_output: runAData.final_output,
      },
      run_b: {
        run_id: run_b,
        pipeline_name: runBData.pipeline_name,
        version: runBData.version,
        status: runBData.status,
        total_steps: stepsB.length,
        total_duration_ms: totalDurationB,
        final_output: runBData.final_output,
      },
      step_comparisons: stepComparisons,
      summary: {
        steps_only_in_a: stepComparisons.filter(c => c.in_run_a && !c.in_run_b).length,
        steps_only_in_b: stepComparisons.filter(c => c.in_run_b && !c.in_run_a).length,
        steps_in_both: stepComparisons.filter(c => c.in_run_a && c.in_run_b).length,
        duration_delta_ms: totalDurationB - totalDurationA,
        output_changed: JSON.stringify(runAData.final_output) !== JSON.stringify(runBData.final_output),
      },
    })
  } catch (err) {
    console.error('Error comparing runs:', err)
    res.status(500).json({ error: 'Internal server error' })
  }
})

function calcDropRatio(step: Record<string, unknown>): number | null {
  const inp = step.input_count as number | null
  const out = step.output_count as number | null
  if (inp && inp > 0 && out !== null && out <= inp) {
    return Math.round((1 - out / inp) * 10000) / 10000
  }
  return null
}

export default router

