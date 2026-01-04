/**
 * Background worker that processes the ingest queue.
 * Run separately: npm run worker
 */
import { initDb } from './db.js'
import { initCache } from './cache.js'
import { initBlobStore } from './blob-store.js'
import * as queue from './queue.js'
import * as db from './db.js'
import * as cache from './cache.js'
import * as blobStore from './blob-store.js'
import { IngestPayload } from './models.js'

const BATCH_SIZE = 100
const POLL_INTERVAL_MS = 100

async function processItem(item: Record<string, unknown>): Promise<void> {
  const payload = IngestPayload.parse(item.payload)

  let runsProcessed = 0
  let stepsProcessed = 0

  // Process runs
  if (payload.runs) {
    for (const run of payload.runs) {
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
      runsProcessed++
    }
  }

  // Process steps
  if (payload.steps) {
    for (const step of payload.steps) {
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
      stepsProcessed++
    }
  }

  await queue.recordProcessed(runsProcessed, stepsProcessed)
}

async function processBatch(): Promise<number> {
  const items = await queue.dequeueBatch(BATCH_SIZE)

  for (const item of items) {
    try {
      await processItem(item)
    } catch (err) {
      console.error('Error processing item:', err)
      await queue.recordError()
    }
  }

  return items.length
}

async function runWorker(): Promise<void> {
  console.log('Starting X-Ray ingest worker...')

  await initDb()
  console.log('✓ PostgreSQL connected')

  await initCache()
  console.log('✓ Redis connected')

  initBlobStore()
  console.log('✓ S3/MinIO configured')

  console.log('\n🔄 Worker running, polling for items...')

  while (true) {
    try {
      const processed = await processBatch()
      if (processed > 0) {
        console.log(`Processed ${processed} items`)
      }
    } catch (err) {
      console.error('Worker error:', err)
    }

    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS))
  }
}

runWorker().catch(console.error)

