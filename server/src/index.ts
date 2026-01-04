import express from 'express'
import cors from 'cors'
import { config } from './config.js'
import { initDb, closeDb } from './db.js'
import { initCache, closeCache } from './cache.js'
import { initBlobStore } from './blob-store.js'

import runsRouter from './routes/runs.js'
import stepsRouter from './routes/steps.js'
import ingestRouter from './routes/ingest.js'
import compareRouter from './routes/compare.js'

const app = express()

app.use(cors())
app.use(express.json({ limit: '50mb' }))

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// API routes
app.use('/runs', runsRouter)
app.use('/steps', stepsRouter)
app.use('/ingest', ingestRouter)
app.use('/compare', compareRouter)

// Startup
async function start() {
  // Start server immediately
  app.listen(config.port, () => {
    console.log(`🚀 X-Ray server running on http://localhost:${config.port}`)
  })

  // Connect to services in background
  try {
    await initDb()
    console.log('✓ PostgreSQL connected')
  } catch (err) {
    console.warn('⚠ PostgreSQL not available:', (err as Error).message)
  }

  try {
    await initCache()
    console.log('✓ Redis connected')
  } catch (err) {
    console.warn('⚠ Redis not available:', (err as Error).message)
  }

  initBlobStore()
  console.log('✓ S3/MinIO configured')
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('\nShutting down...')
  await closeDb()
  await closeCache()
  process.exit(0)
})

process.on('SIGINT', async () => {
  console.log('\nShutting down...')
  await closeDb()
  await closeCache()
  process.exit(0)
})

start()

