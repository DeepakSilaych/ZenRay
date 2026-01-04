import Redis from 'ioredis'
import { config } from './config.js'

let redis: Redis | null = null

export const CACHE_TTL_SHORT = 60       // 1 minute
export const CACHE_TTL_MEDIUM = 300     // 5 minutes
export const CACHE_TTL_LONG = 3600      // 1 hour

export async function initCache(): Promise<void> {
  redis = new Redis({
    host: config.redis.host,
    port: config.redis.port,
    db: config.redis.db,
    maxRetriesPerRequest: 1,
    retryStrategy: () => null,
    lazyConnect: true,
  })
  redis.on('error', () => {}) // Suppress connection errors
  await redis.connect()
  await redis.ping()
}

export async function closeCache(): Promise<void> {
  if (redis) {
    await redis.quit()
    redis = null
  }
}

export function getRedis(): Redis {
  if (!redis) throw new Error('Redis not initialized')
  return redis
}

// Cache operations
export async function cacheGet<T>(key: string): Promise<T | null> {
  const r = getRedis()
  const value = await r.get(key)
  if (value) return JSON.parse(value) as T
  return null
}

export async function cacheSet(key: string, value: unknown, ttl: number = CACHE_TTL_MEDIUM): Promise<void> {
  const r = getRedis()
  await r.setex(key, ttl, JSON.stringify(value))
}

export async function cacheDelete(key: string): Promise<void> {
  const r = getRedis()
  await r.del(key)
}

export async function cacheDeletePattern(pattern: string): Promise<void> {
  const r = getRedis()
  let cursor = '0'
  do {
    const [newCursor, keys] = await r.scan(cursor, 'MATCH', pattern, 'COUNT', 100)
    cursor = newCursor
    if (keys.length > 0) {
      await r.del(...keys)
    }
  } while (cursor !== '0')
}

// Cache key builders
export function runKey(runId: string): string {
  return `run:${runId}`
}

export function runDetailKey(runId: string): string {
  return `run_detail:${runId}`
}

export function stepKey(stepId: string): string {
  return `step:${stepId}`
}

export function runsListKey(pipelineName?: string, status?: string): string {
  return `runs_list:${pipelineName || 'all'}:${status || 'all'}`
}

// Invalidation helpers
export async function invalidateRun(runId: string): Promise<void> {
  await cacheDelete(runKey(runId))
  await cacheDelete(runDetailKey(runId))
  await cacheDeletePattern('runs_list:*')
}

export async function invalidateStep(stepId: string, runId: string): Promise<void> {
  await cacheDelete(stepKey(stepId))
  await cacheDelete(runDetailKey(runId))
}

