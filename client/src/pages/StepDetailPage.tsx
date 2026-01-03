import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchStepDetail, StepDetail } from '../api'

export default function StepDetailPage() {
  const { stepId } = useParams<{ stepId: string }>()
  const [data, setData] = useState<StepDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!stepId) return
    setLoading(true)
    fetchStepDetail(stepId)
      .then(setData)
      .finally(() => setLoading(false))
  }, [stepId])

  if (loading) {
    return <div className="text-center py-12 text-xray-muted text-sm">Loading...</div>
  }

  if (!data) {
    return <div className="text-center py-12 text-xray-muted text-sm">Step not found</div>
  }

  const { step, candidate_set, artifacts } = data
  const dropPct = step.input_count && step.output_count !== null
    ? Math.round((1 - step.output_count / step.input_count) * 100)
    : null

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-xray-muted">
        <Link to="/" className="hover:text-xray-text">Runs</Link>
        <span className="mx-2 text-xray-dim">/</span>
        <Link to={`/runs/${step.run_id}`} className="hover:text-xray-text font-mono text-xs">
          {step.run_id}
        </Link>
        <span className="mx-2 text-xray-dim">/</span>
        <span className="text-xray-text">{step.name}</span>
      </nav>

      {/* Step Summary */}
      <div className="bg-xray-surface border border-xray-border rounded-lg">
        <div className="px-5 py-4 border-b border-xray-border">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-lg font-semibold">{step.name}</h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2 py-0.5 bg-xray-elevated rounded text-2xs font-mono text-xray-muted">
                  {step.kind}
                </span>
                <span className="text-xs text-xray-dim font-mono">{step.step_id}</span>
              </div>
            </div>
            <StatusBadge status={step.status} />
          </div>
        </div>
        
        <div className="px-5 py-4">
          <dl className="grid grid-cols-5 gap-6 text-sm">
            <div>
              <dt className="text-xray-muted text-xs mb-1">Input Count</dt>
              <dd className="font-mono text-xl">{step.input_count ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Output Count</dt>
              <dd className="font-mono text-xl">{step.output_count ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Drop Ratio</dt>
              <dd className={`font-mono text-xl ${
                dropPct !== null && dropPct >= 80 ? 'text-xray-danger' :
                dropPct !== null && dropPct >= 50 ? 'text-xray-warning' : ''
              }`}>
                {dropPct !== null ? `${dropPct}%` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Duration</dt>
              <dd className="font-mono text-xl">{step.duration_ms !== null ? `${step.duration_ms}ms` : '—'}</dd>
            </div>
            <div>
              <dt className="text-xray-muted text-xs mb-1">Metrics</dt>
              <dd className="flex gap-1.5 flex-wrap">
                {step.metrics && Object.entries(step.metrics).map(([k, v]) => (
                  <span key={k} className="px-1.5 py-0.5 bg-xray-elevated rounded text-2xs text-xray-muted">
                    {k}={String(v)}
                  </span>
                ))}
                {(!step.metrics || Object.keys(step.metrics).length === 0) && '—'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Candidate Set */}
      {candidate_set && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-xray-muted">Candidate Set</h2>
            <span className="px-2 py-0.5 bg-xray-accent/10 text-xray-accent rounded text-2xs font-medium">
              {candidate_set.mode}
            </span>
          </div>

          {/* Reason Histogram */}
          {candidate_set.reason_histogram && Object.keys(candidate_set.reason_histogram).length > 0 && (
            <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-xray-border">
                <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Drop Reasons</h3>
              </div>
              <table>
                <thead>
                  <tr className="border-b border-xray-border">
                    <th className="px-4 py-2">Reason</th>
                    <th className="px-4 py-2 text-right">Count</th>
                    <th className="px-4 py-2 w-1/2">Distribution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-xray-border">
                  {Object.entries(candidate_set.reason_histogram)
                    .sort(([, a], [, b]) => b - a)
                    .map(([reason, count]) => {
                      const total = Object.values(candidate_set.reason_histogram!).reduce((a, b) => a + b, 0)
                      const pct = Math.round((count / total) * 100)
                      return (
                        <tr key={reason}>
                          <td className="px-4 py-2 font-mono text-sm">{reason}</td>
                          <td className="px-4 py-2 text-right font-mono text-sm text-xray-muted">{count}</td>
                          <td className="px-4 py-2">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 h-2 bg-xray-elevated rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-xray-danger/60 rounded-full"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                              <span className="text-xs text-xray-muted w-12 text-right">{pct}%</span>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
          )}

          {/* Score Histogram */}
          {candidate_set.score_histogram && Object.keys(candidate_set.score_histogram).length > 0 && (
            <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-xray-border">
                <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Score Distribution</h3>
              </div>
              <div className="p-4">
                <div className="flex items-end gap-1 h-20">
                  {Object.entries(candidate_set.score_histogram).map(([bucket, count]) => {
                    const max = Math.max(...Object.values(candidate_set.score_histogram!))
                    const height = (count / max) * 100
                    return (
                      <div key={bucket} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-2xs text-xray-muted font-mono">{count}</span>
                        <div
                          className="w-full bg-xray-accent/60 rounded-t"
                          style={{ height: `${height}%`, minHeight: '4px' }}
                        />
                        <span className="text-2xs text-xray-dim font-mono truncate w-full text-center">
                          {bucket}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Top Kept */}
          {candidate_set.top_kept && candidate_set.top_kept.length > 0 && (
            <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-xray-border flex items-center justify-between">
                <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Top Kept</h3>
                <span className="text-2xs text-xray-success">{candidate_set.top_kept.length} items</span>
              </div>
              <div className="divide-y divide-xray-border">
                {candidate_set.top_kept.slice(0, 5).map((c, i) => (
                  <pre key={i} className="px-4 py-3 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(c, null, 2)}
                  </pre>
                ))}
              </div>
            </div>
          )}

          {/* Top Dropped */}
          {candidate_set.top_dropped && candidate_set.top_dropped.length > 0 && (
            <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-xray-border flex items-center justify-between">
                <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Top Dropped</h3>
                <span className="text-2xs text-xray-danger">{candidate_set.top_dropped.length} items</span>
              </div>
              <div className="divide-y divide-xray-border">
                {candidate_set.top_dropped.slice(0, 5).map((c, i) => (
                  <pre key={i} className="px-4 py-3 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(c, null, 2)}
                  </pre>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Artifacts */}
      {artifacts && artifacts.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-xray-muted mb-3">Artifacts</h2>
          <div className="space-y-3">
            {artifacts.map((art, i) => (
              <div key={i} className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
                <div className="px-4 py-2 border-b border-xray-border">
                  <span className="text-xs text-xray-muted font-mono">
                    {(art as Record<string, unknown>).type as string}
                  </span>
                </div>
                <pre className="px-4 py-3 text-xs font-mono overflow-x-auto">
                  {JSON.stringify((art as Record<string, unknown>).content, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
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
