import { getRedis } from './cache.js'

const INGEST_QUEUE = 'xray:ingest:queue'
const INGEST_STATS = 'xray:ingest:stats'

export async function enqueueIngest(payload: Record<string, unknown>): Promise<string> {
  const r = getRedis()

  const queueItem = {
    payload,
    queued_at: new Date().toISOString(),
  }

  await r.lpush(INGEST_QUEUE, JSON.stringify(queueItem))
  await r.hincrby(INGEST_STATS, 'total_queued', 1)

  return 'queued'
}

export async function dequeueBatch(batchSize: number = 100): Promise<Record<string, unknown>[]> {
  const r = getRedis()
  const items: Record<string, unknown>[] = []

  for (let i = 0; i < batchSize; i++) {
    const item = await r.rpop(INGEST_QUEUE)
    if (!item) break

    try {
      const parsed = JSON.parse(item)
      items.push(parsed)
    } catch {
      await r.hincrby(INGEST_STATS, 'parse_errors', 1)
    }
  }

  return items
}

export async function queueLength(): Promise<number> {
  const r = getRedis()
  return r.llen(INGEST_QUEUE)
}

export async function getQueueStats(): Promise<Record<string, unknown>> {
  const r = getRedis()
  const stats = await r.hgetall(INGEST_STATS)
  const len = await queueLength()

  return {
    queue_length: len,
    total_queued: parseInt(stats.total_queued || '0'),
    total_processed: parseInt(stats.total_processed || '0'),
    total_errors: parseInt(stats.total_errors || '0'),
    parse_errors: parseInt(stats.parse_errors || '0'),
    runs_processed: parseInt(stats.runs_processed || '0'),
    steps_processed: parseInt(stats.steps_processed || '0'),
  }
}

export async function recordProcessed(runs: number = 0, steps: number = 0): Promise<void> {
  const r = getRedis()
  await r.hincrby(INGEST_STATS, 'total_processed', 1)
  if (runs > 0) await r.hincrby(INGEST_STATS, 'runs_processed', runs)
  if (steps > 0) await r.hincrby(INGEST_STATS, 'steps_processed', steps)
}

export async function recordError(): Promise<void> {
  const r = getRedis()
  await r.hincrby(INGEST_STATS, 'total_errors', 1)
}

