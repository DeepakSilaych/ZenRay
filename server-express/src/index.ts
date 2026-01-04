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
  console.log('Initializing services...')

  try {
    await initDb()
    console.log('✓ PostgreSQL connected')

    await initCache()
    console.log('✓ Redis connected')

    initBlobStore()
    console.log('✓ S3/MinIO configured')

    app.listen(config.port, () => {
      console.log(`\n🚀 X-Ray server running on http://localhost:${config.port}`)
      console.log('\nEndpoints:')
      console.log('  GET  /health')
      console.log('  GET  /runs')
      console.log('  GET  /runs/:id')
      console.log('  GET  /runs/:id/trace?q=...')
      console.log('  GET  /steps')
      console.log('  GET  /steps/:id')
      console.log('  GET  /steps/:id/candidates')
      console.log('  POST /ingest')
      console.log('  GET  /ingest/stats')
      console.log('  GET  /compare?run_a=...&run_b=...')
    })
  } catch (err) {
    console.error('Failed to start server:', err)
    process.exit(1)
  }
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

