import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchRuns, RunSummary } from '../api'

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ pipeline: '', status: '' })

  useEffect(() => {
    setLoading(true)
    fetchRuns({
      pipeline_name: filters.pipeline || undefined,
      status: filters.status || undefined,
      limit: 100,
    })
      .then(setRuns)
      .finally(() => setLoading(false))
  }, [filters])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Pipeline Runs</h1>
          <p className="text-sm text-xray-muted mt-0.5">
            {runs.length} runs found
          </p>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Filter pipeline..."
            value={filters.pipeline}
            onChange={(e) => setFilters((f) => ({ ...f, pipeline: e.target.value }))}
            className="h-8 px-3 bg-xray-surface border border-xray-border rounded text-sm
                       placeholder:text-xray-dim focus:outline-none focus:border-xray-accent
                       transition-colors w-48"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="h-8 px-3 bg-xray-surface border border-xray-border rounded text-sm
                       focus:outline-none focus:border-xray-accent transition-colors"
          >
            <option value="">All Status</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILURE">Failure</option>
            <option value="RUNNING">Running</option>
          </select>
        </div>
      </div>

      {/* Runs Table */}
      <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xray-muted text-sm">Loading...</div>
        ) : runs.length === 0 ? (
          <div className="p-8 text-center text-xray-muted text-sm">
            No runs found
          </div>
        ) : (
          <table>
            <thead>
              <tr className="border-b border-xray-border">
                <th className="px-4 py-3">Run ID</th>
                <th className="px-4 py-3">Pipeline</th>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Steps</th>
                <th className="px-4 py-3 text-right">Duration</th>
                <th className="px-4 py-3 text-right">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-xray-border">
              {runs.map((run) => (
                <RunRow key={run.run_id} run={run} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function RunRow({ run }: { run: RunSummary }) {
  const duration = run.ended_at
    ? new Date(run.ended_at).getTime() - new Date(run.started_at).getTime()
    : null

  return (
    <tr className="hover:bg-xray-elevated/50 transition-colors">
      <td className="px-4 py-3">
        <Link
          to={`/runs/${run.run_id}`}
          className="font-mono text-xs text-xray-accent hover:underline"
        >
          {run.run_id}
        </Link>
      </td>
      <td className="px-4 py-3 font-medium">{run.pipeline_name}</td>
      <td className="px-4 py-3 text-xray-muted font-mono text-xs">
        {run.version || '—'}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={run.status} />
      </td>
      <td className="px-4 py-3 text-right font-mono text-xray-muted">
        {run.step_count}
      </td>
      <td className="px-4 py-3 text-right font-mono text-xs text-xray-muted">
        {duration !== null ? formatDuration(duration) : '—'}
      </td>
      <td className="px-4 py-3 text-right text-xray-muted text-xs">
        {formatTime(run.started_at)}
      </td>
    </tr>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    SUCCESS: 'bg-xray-success/10 text-xray-success border-xray-success/20',
    FAILURE: 'bg-xray-danger/10 text-xray-danger border-xray-danger/20',
    RUNNING: 'bg-xray-accent/10 text-xray-accent border-xray-accent/20',
    TIMEOUT: 'bg-xray-warning/10 text-xray-warning border-xray-warning/20',
  }
  
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-2xs font-medium border ${styles[status] || 'bg-xray-elevated text-xray-muted border-xray-border'}`}>
      {status}
    </span>
  )
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
