import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchRunDetail, RunDetail, StepSummary, traceCandidate, CandidateTraceResult } from '../api'

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>()
  const [data, setData] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!runId) return
    setLoading(true)
    fetchRunDetail(runId)
      .then(setData)
      .finally(() => setLoading(false))
  }, [runId])

  if (loading) {
    return <div className="text-center py-12 text-xray-muted text-sm">Loading...</div>
  }

  if (!data) {
    return <div className="text-center py-12 text-xray-muted text-sm">Run not found</div>
  }

  const { run, steps } = data
  const duration = run.ended_at
    ? new Date(run.ended_at).getTime() - new Date(run.started_at).getTime()
    : null

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-xray-muted">
        <Link to="/" className="hover:text-xray-text">Runs</Link>
        <span className="mx-2 text-xray-dim">/</span>
        <span className="text-xray-text font-mono text-xs">{run.run_id}</span>
      </nav>

      {/* Run Summary */}
      <div className="bg-xray-surface border border-xray-border rounded-lg">
        <div className="px-5 py-4 border-b border-xray-border">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-lg font-semibold">{run.pipeline_name}</h1>
              <p className="text-xs text-xray-muted font-mono mt-0.5">{run.run_id}</p>
            </div>
            <StatusBadge status={run.status} />
          </div>
        </div>
        
        <div className="px-5 py-4">
          <dl className="grid grid-cols-5 gap-6 text-sm">
            <div>
              <dt className="text-xray-muted text-xs mb-1">Version</dt>
              <dd className="font-mono">{run.version || '—'}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Started</dt>
              <dd>{new Date(run.started_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Duration</dt>
              <dd className="font-mono">{duration !== null ? `${duration}ms` : '—'}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Steps</dt>
              <dd className="font-mono">{steps.length}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Tags</dt>
              <dd className="flex gap-1.5 flex-wrap">
                {run.tags && Object.entries(run.tags).map(([k, v]) => (
                  <span key={k} className="px-1.5 py-0.5 bg-xray-elevated rounded text-2xs text-xray-muted">
                    {k}={v}
                  </span>
                ))}
                {(!run.tags || Object.keys(run.tags).length === 0) && '—'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Candidate Trace */}
      <CandidateTrace runId={run.run_id} />

      {/* Steps Table */}
      <div>
        <h2 className="text-sm font-medium text-xray-muted mb-3">Step Timeline</h2>
        <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
          <table>
            <thead>
              <tr className="border-b border-xray-border">
                <th className="px-4 py-3 w-8">#</th>
                <th className="px-4 py-3">Step</th>
                <th className="px-4 py-3">Kind</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Input</th>
                <th className="px-4 py-3 text-right">Output</th>
                <th className="px-4 py-3 text-right">Drop %</th>
                <th className="px-4 py-3 text-right">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-xray-border">
              {steps.map((step, idx) => (
                <StepRow key={step.step_id} step={step} index={idx + 1} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Input/Output */}
      {(run.input_summary || run.final_output) && (
        <div className="grid grid-cols-2 gap-4">
          {run.input_summary && (
            <div>
              <h2 className="text-sm font-medium text-xray-muted mb-3">Input</h2>
              <pre className="bg-xray-surface border border-xray-border rounded-lg p-4 text-xs font-mono overflow-auto max-h-64">
                {JSON.stringify(run.input_summary, null, 2)}
              </pre>
            </div>
          )}
          {run.final_output && (
            <div>
              <h2 className="text-sm font-medium text-xray-muted mb-3">Output</h2>
              <pre className="bg-xray-surface border border-xray-border rounded-lg p-4 text-xs font-mono overflow-auto max-h-64">
                {JSON.stringify(run.final_output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CandidateTrace({ runId }: { runId: string }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<CandidateTraceResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await traceCandidate(runId, query.trim())
      setResult(res)
    } catch {
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg">
      <div className="px-4 py-3 border-b border-xray-border">
        <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Trace Candidate</h3>
      </div>
      <div className="p-4">
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search by ID, name, or title..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 h-9 px-3 bg-xray-bg border border-xray-border rounded text-sm
                       placeholder:text-xray-dim focus:outline-none focus:border-xray-accent
                       transition-colors"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="h-9 px-4 bg-xray-accent text-xray-bg rounded text-sm font-medium
                       hover:bg-xray-accentHover disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {loading ? 'Searching...' : 'Trace'}
          </button>
        </div>

        {searched && result && (
          <div className="mt-4">
            {!result.found ? (
              <div className="text-sm text-xray-muted py-4 text-center">
                No candidate matching "{result.query}" found in any step
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm text-xray-muted">
                  Found "{result.query}" in {result.journey.length} step(s)
                </div>
                <div className="border border-xray-border rounded overflow-hidden">
                  <table>
                    <thead>
                      <tr className="border-b border-xray-border bg-xray-bg">
                        <th className="px-4 py-2 w-8"></th>
                        <th className="px-4 py-2">Step</th>
                        <th className="px-4 py-2">Kind</th>
                        <th className="px-4 py-2">Result</th>
                        <th className="px-4 py-2">Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-xray-border">
                      {result.journey.map((j, idx) => (
                        <tr key={j.step_id} className="hover:bg-xray-elevated/30">
                          <td className="px-4 py-2 text-xray-dim font-mono text-xs">{idx + 1}</td>
                          <td className="px-4 py-2">
                            <Link 
                              to={`/steps/${j.step_id}`} 
                              className="text-xray-accent hover:underline"
                            >
                              {j.step_name}
                            </Link>
                          </td>
                          <td className="px-4 py-2">
                            <span className="px-2 py-0.5 bg-xray-elevated rounded text-2xs font-mono text-xray-muted">
                              {j.step_kind}
                            </span>
                          </td>
                          <td className="px-4 py-2">
                            {j.status === 'kept' ? (
                              <span className="inline-flex items-center gap-1.5 text-xray-success text-sm">
                                <span className="w-2 h-2 bg-xray-success rounded-full"></span>
                                Kept
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 text-xray-danger text-sm">
                                <span className="w-2 h-2 bg-xray-danger rounded-full"></span>
                                Dropped
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2 font-mono text-xs text-xray-muted">
                            {j.drop_reason || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Show candidate details */}
                {result.journey.length > 0 && result.journey[0].candidate && (
                  <div className="mt-3">
                    <div className="text-xs text-xray-muted mb-2">Candidate Data</div>
                    <pre className="bg-xray-bg border border-xray-border rounded p-3 text-xs font-mono overflow-auto max-h-48">
                      {JSON.stringify(result.journey[0].candidate, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {!searched && (
          <div className="text-xs text-xray-dim mt-3">
            Search for a candidate to see which steps it passed through and where it was dropped.
          </div>
        )}
      </div>
    </div>
  )
}

function StepRow({ step, index }: { step: StepSummary; index: number }) {
  const dropPct = step.drop_ratio !== null ? Math.round(step.drop_ratio * 100) : null

  return (
    <tr className="hover:bg-xray-elevated/50 transition-colors">
      <td className="px-4 py-3 text-xray-dim font-mono text-xs">{index}</td>
      <td className="px-4 py-3">
        <Link
          to={`/steps/${step.step_id}`}
          className="text-xray-accent hover:underline font-medium"
        >
          {step.name}
        </Link>
      </td>
      <td className="px-4 py-3">
        <span className="px-2 py-0.5 bg-xray-elevated rounded text-2xs font-mono text-xray-muted">
          {step.kind}
        </span>
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={step.status} />
      </td>
      <td className="px-4 py-3 text-right font-mono text-sm">
        {step.input_count ?? '—'}
      </td>
      <td className="px-4 py-3 text-right font-mono text-sm">
        {step.output_count ?? '—'}
      </td>
      <td className="px-4 py-3 text-right">
        {dropPct !== null && dropPct > 0 ? (
          <span className={`font-mono text-sm ${
            dropPct >= 80 ? 'text-xray-danger' : 
            dropPct >= 50 ? 'text-xray-warning' : 
            'text-xray-muted'
          }`}>
            {dropPct}%
          </span>
        ) : (
          <span className="text-xray-dim">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-right font-mono text-xs text-xray-muted">
        {step.duration_ms !== null ? `${step.duration_ms}ms` : '—'}
      </td>
    </tr>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    SUCCESS: 'bg-xray-success/10 text-xray-success border-xray-success/20',
    FAILURE: 'bg-xray-danger/10 text-xray-danger border-xray-danger/20',
    RUNNING: 'bg-xray-accent/10 text-xray-accent border-xray-accent/20',
    SKIPPED: 'bg-xray-elevated text-xray-dim border-xray-border',
  }
  
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-2xs font-medium border ${styles[status] || 'bg-xray-elevated text-xray-muted border-xray-border'}`}>
      {status}
    </span>
  )
}
