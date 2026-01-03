import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { compareRuns, fetchRuns, RunComparisonResult, RunSummary } from '../api'

export default function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [comparison, setComparison] = useState<RunComparisonResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const runA = searchParams.get('run_a') || ''
  const runB = searchParams.get('run_b') || ''

  // Load available runs for selection
  useEffect(() => {
    fetchRuns({ limit: 50 }).then(setRuns).catch(console.error)
  }, [])

  // Load comparison when both runs are selected
  useEffect(() => {
    if (!runA || !runB) {
      setComparison(null)
      return
    }
    
    setLoading(true)
    setError(null)
    
    compareRuns(runA, runB)
      .then(setComparison)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [runA, runB])

  const selectRun = (key: 'run_a' | 'run_b', value: string) => {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    setSearchParams(params)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Compare Runs</h1>
        <p className="text-sm text-xray-muted mt-1">
          A/B test pipeline versions or debug regressions
        </p>
      </div>

      {/* Run Selection */}
      <div className="grid grid-cols-2 gap-4">
        <RunSelector
          label="Run A (Baseline)"
          runs={runs}
          selected={runA}
          onSelect={(v) => selectRun('run_a', v)}
          exclude={runB}
        />
        <RunSelector
          label="Run B (Comparison)"
          runs={runs}
          selected={runB}
          onSelect={(v) => selectRun('run_b', v)}
          exclude={runA}
        />
      </div>

      {/* Loading / Error */}
      {loading && (
        <div className="text-center py-12 text-xray-muted">Loading comparison...</div>
      )}
      {error && (
        <div className="text-center py-8 text-xray-danger">{error}</div>
      )}

      {/* Comparison Results */}
      {comparison && !loading && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 gap-4">
            <RunSummaryCard run={comparison.run_a} label="Run A" variant="a" />
            <RunSummaryCard run={comparison.run_b} label="Run B" variant="b" />
          </div>

          {/* Overall Summary - Table */}
          <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-xray-border">
              <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">
                Summary
              </h3>
            </div>
            <table>
              <tbody className="divide-y divide-xray-border">
                <tr>
                  <td className="px-4 py-3 text-sm text-xray-muted w-48">Shared Steps</td>
                  <td className="px-4 py-3 font-mono text-sm">{comparison.summary.steps_in_both}</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm text-xray-muted">Only in Run A</td>
                  <td className="px-4 py-3 font-mono text-sm">{comparison.summary.steps_only_in_a}</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm text-xray-muted">Only in Run B</td>
                  <td className="px-4 py-3 font-mono text-sm">{comparison.summary.steps_only_in_b}</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm text-xray-muted">Duration Δ</td>
                  <td className="px-4 py-3 font-mono text-sm">
                    {comparison.summary.duration_delta_ms > 0 ? '+' : ''}
                    {comparison.summary.duration_delta_ms}ms
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm text-xray-muted">Output Match</td>
                  <td className="px-4 py-3 font-mono text-sm">
                    {comparison.summary.output_changed ? 'Different' : 'Identical'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Step-by-Step Comparison */}
          <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-xray-border">
              <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">
                Step-by-Step Comparison
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table>
                <thead>
                  <tr className="border-b border-xray-border">
                    <th className="px-4 py-2"></th>
                    <th className="px-4 py-2 text-center border-l border-xray-border" colSpan={4}>
                      Run A
                    </th>
                    <th className="px-4 py-2 text-center border-l-2 border-xray-border" colSpan={4}>
                      Run B
                    </th>
                    <th className="px-4 py-2 text-center border-l border-xray-border" colSpan={3}>
                      Delta
                    </th>
                  </tr>
                  <tr className="border-b border-xray-border text-2xs text-xray-dim">
                    <th className="px-4 py-1 text-left font-normal">Step</th>
                    <th className="px-2 py-1 font-normal border-l border-xray-border">Input</th>
                    <th className="px-2 py-1 font-normal">Output</th>
                    <th className="px-2 py-1 font-normal">Drop %</th>
                    <th className="px-2 py-1 font-normal">Duration</th>
                    <th className="px-2 py-1 font-normal border-l-2 border-xray-border">Input</th>
                    <th className="px-2 py-1 font-normal">Output</th>
                    <th className="px-2 py-1 font-normal">Drop %</th>
                    <th className="px-2 py-1 font-normal">Duration</th>
                    <th className="px-2 py-1 font-normal border-l border-xray-border">Input Δ</th>
                    <th className="px-2 py-1 font-normal">Output Δ</th>
                    <th className="px-2 py-1 font-normal">Drop Δ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-xray-border">
                  {comparison.step_comparisons.map((sc) => (
                    <tr key={sc.step_name} className="hover:bg-xray-elevated/30">
                      <td className="px-4 py-2">
                        <div className="font-medium text-sm">{sc.step_name}</div>
                        <div className="text-2xs text-xray-dim">
                          {sc.run_a?.kind || sc.run_b?.kind}
                        </div>
                      </td>
                      {/* Run A columns */}
                      <td className="px-2 py-2 text-center font-mono text-xs border-l border-xray-border">
                        {sc.run_a ? sc.run_a.input_count ?? '—' : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.run_a ? sc.run_a.output_count ?? '—' : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.run_a && sc.run_a.drop_ratio !== null 
                          ? `${Math.round(sc.run_a.drop_ratio * 100)}%` 
                          : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs text-xray-muted">
                        {sc.run_a?.duration_ms ?? '—'}ms
                      </td>
                      {/* Run B columns */}
                      <td className="px-2 py-2 text-center font-mono text-xs border-l-2 border-xray-border">
                        {sc.run_b ? sc.run_b.input_count ?? '—' : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.run_b ? sc.run_b.output_count ?? '—' : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.run_b && sc.run_b.drop_ratio !== null 
                          ? `${Math.round(sc.run_b.drop_ratio * 100)}%` 
                          : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs text-xray-muted">
                        {sc.run_b?.duration_ms ?? '—'}ms
                      </td>
                      {/* Delta columns */}
                      <td className="px-2 py-2 text-center font-mono text-xs border-l border-xray-border">
                        <InputDelta a={sc.run_a?.input_count} b={sc.run_b?.input_count} />
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.deltas ? (
                          <span>
                            {sc.deltas.output_count > 0 ? '+' : ''}{sc.deltas.output_count}
                          </span>
                        ) : <span className="text-xray-dim">—</span>}
                      </td>
                      <td className="px-2 py-2 text-center font-mono text-xs">
                        {sc.deltas ? (
                          <span>
                            {sc.deltas.drop_ratio > 0 ? '+' : ''}
                            {Math.round(sc.deltas.drop_ratio * 100)}%
                          </span>
                        ) : <span className="text-xray-dim">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Final Output Comparison */}
          {(comparison.run_a.final_output || comparison.run_b.final_output) && (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
                <div className="px-4 py-2 border-b border-xray-border">
                  <span className="text-xs text-xray-muted">Run A Final Output</span>
                </div>
                <pre className="px-4 py-3 text-xs font-mono overflow-auto max-h-48">
                  {JSON.stringify(comparison.run_a.final_output, null, 2) || '—'}
                </pre>
              </div>
              <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
                <div className="px-4 py-2 border-b border-xray-border">
                  <span className="text-xs text-xray-muted">Run B Final Output</span>
                </div>
                <pre className="px-4 py-3 text-xs font-mono overflow-auto max-h-48">
                  {JSON.stringify(comparison.run_b.final_output, null, 2) || '—'}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!runA && !runB && !loading && (
        <div className="text-center py-16 text-xray-muted">
          <p className="text-lg mb-2">Select two runs to compare</p>
          <p className="text-sm text-xray-dim">
            Compare pipeline versions, debug regressions, or A/B test changes
          </p>
        </div>
      )}
    </div>
  )
}

function RunSelector({ 
  label, 
  runs, 
  selected, 
  onSelect, 
  exclude 
}: { 
  label: string
  runs: RunSummary[]
  selected: string
  onSelect: (v: string) => void
  exclude?: string
}) {
  const filtered = runs.filter(r => r.run_id !== exclude)

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg p-4">
      <label className="block text-xs font-medium text-xray-muted mb-2">
        {label}
      </label>
      <select
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
        className="w-full bg-xray-elevated border border-xray-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-xray-accent"
      >
        <option value="">Select a run...</option>
        {filtered.map(r => (
          <option key={r.run_id} value={r.run_id}>
            {r.pipeline_name} ({r.run_id.slice(-8)}) — {r.version || 'no version'} — {r.status}
          </option>
        ))}
      </select>
    </div>
  )
}

function RunSummaryCard({ 
  run, 
  label,
  variant
}: { 
  run: RunComparisonResult['run_a']
  label: string
  variant: 'a' | 'b'
}) {
  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-xray-border flex items-center justify-between">
        <span className="text-xs font-medium text-xray-muted uppercase tracking-wider">
          {label} {variant === 'a' ? '(Baseline)' : '(Compare)'}
        </span>
        <Link 
          to={`/runs/${run.run_id}`} 
          className="text-xs text-xray-accent hover:underline"
        >
          View →
        </Link>
      </div>
      <table>
        <tbody className="divide-y divide-xray-border">
          <tr>
            <td className="px-4 py-2 text-xs text-xray-dim w-32">Pipeline</td>
            <td className="px-4 py-2 text-sm font-medium">{run.pipeline_name}</td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-xs text-xray-dim">Version</td>
            <td className="px-4 py-2 text-sm font-mono">{run.version || '—'}</td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-xs text-xray-dim">Status</td>
            <td className="px-4 py-2 text-sm font-mono">{run.status}</td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-xs text-xray-dim">Steps</td>
            <td className="px-4 py-2 text-sm font-mono">{run.total_steps}</td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-xs text-xray-dim">Duration</td>
            <td className="px-4 py-2 text-sm font-mono">{run.total_duration_ms}ms</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function InputDelta({ a, b }: { a: number | null | undefined; b: number | null | undefined }) {
  if (a === null || a === undefined || b === null || b === undefined) {
    return <span className="text-xray-dim">—</span>
  }
  const delta = b - a
  if (delta === 0) {
    return <span className="text-xray-dim">0</span>
  }
  return <span>{delta > 0 ? '+' : ''}{delta}</span>
}

