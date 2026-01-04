import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchRuns, RunSummary } from '../api'

const STATUSES = ['ALL', 'SUCCESS', 'FAILURE', 'RUNNING'] as const
type StatusFilter = typeof STATUSES[number]

const PAGE_SIZE = 20

export default function RunsPage() {
  const [allRuns, setAllRuns] = useState<RunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    setLoading(true)
    fetchRuns({ limit: 500 })
      .then(setAllRuns)
      .finally(() => setLoading(false))
  }, [])

  // Filter runs by status (client-side)
  const filteredRuns = useMemo(() => {
    if (statusFilter === 'ALL') return allRuns
    return allRuns.filter(r => r.status === statusFilter)
  }, [allRuns, statusFilter])

  // Pagination
  const totalPages = Math.ceil(filteredRuns.length / PAGE_SIZE)
  const paginatedRuns = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE
    return filteredRuns.slice(start, start + PAGE_SIZE)
  }, [filteredRuns, currentPage])

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [statusFilter])

  // Status counts for filter buttons
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: allRuns.length }
    for (const run of allRuns) {
      counts[run.status] = (counts[run.status] || 0) + 1
    }
    return counts
  }, [allRuns])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Pipeline Runs</h1>
          <p className="text-sm text-xray-muted mt-0.5">
            {filteredRuns.length} runs {statusFilter !== 'ALL' ? `(${statusFilter.toLowerCase()})` : ''}
          </p>
        </div>
        
        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1">
          {STATUSES.map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                statusFilter === status
                  ? status === 'SUCCESS' ? 'bg-xray-success/20 text-xray-success border border-xray-success/30'
                  : status === 'FAILURE' ? 'bg-xray-danger/20 text-xray-danger border border-xray-danger/30'
                  : status === 'RUNNING' ? 'bg-xray-accent/20 text-xray-accent border border-xray-accent/30'
                  : 'bg-xray-elevated text-xray-text border border-xray-border'
                  : 'text-xray-muted hover:text-xray-text hover:bg-xray-elevated/50 border border-transparent'
              }`}
            >
              {status === 'ALL' ? 'All' : status.charAt(0) + status.slice(1).toLowerCase()}
              <span className="ml-1.5 text-xs opacity-70">
                {statusCounts[status] || 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Runs Overview Chart */}
      {!loading && allRuns.length > 0 && <RunsOverviewChart runs={allRuns} />}

      {/* Runs Table */}
      <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xray-muted text-sm">Loading...</div>
        ) : paginatedRuns.length === 0 ? (
          <div className="p-8 text-center text-xray-muted text-sm">
            No runs found
          </div>
        ) : (
          <>
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
                {paginatedRuns.map((run) => (
                  <RunRow key={run.run_id} run={run} />
                ))}
              </tbody>
            </table>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-xray-border flex items-center justify-between">
                <div className="text-xs text-xray-muted">
                  Showing {(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filteredRuns.length)} of {filteredRuns.length}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-2 py-1 rounded text-xs font-medium text-xray-muted 
                               hover:bg-xray-elevated disabled:opacity-40 disabled:cursor-not-allowed
                               transition-colors"
                  >
                    ← Prev
                  </button>
                  
                  {/* Page numbers */}
                  <div className="flex items-center gap-0.5">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum: number
                      if (totalPages <= 5) {
                        pageNum = i + 1
                      } else if (currentPage <= 3) {
                        pageNum = i + 1
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i
                      } else {
                        pageNum = currentPage - 2 + i
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`w-7 h-7 rounded text-xs font-medium transition-colors ${
                            currentPage === pageNum
                              ? 'bg-xray-accent text-xray-bg'
                              : 'text-xray-muted hover:bg-xray-elevated'
                          }`}
                        >
                          {pageNum}
                        </button>
                      )
                    })}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-2 py-1 rounded text-xs font-medium text-xray-muted 
                               hover:bg-xray-elevated disabled:opacity-40 disabled:cursor-not-allowed
                               transition-colors"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
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

// ============================================================
// Runs Overview Chart
// ============================================================

interface TimeSlot {
  time: string
  label: string
  success: number
  failure: number
  other: number
  total: number
}

function RunsOverviewChart({ runs }: { runs: RunSummary[] }) {
  const chartData = useMemo(() => {
    // Group runs by hour
    const slots: Record<string, TimeSlot> = {}
    
    // Create slots for last 24 hours
    const now = new Date()
    for (let i = 23; i >= 0; i--) {
      const slotTime = new Date(now.getTime() - i * 60 * 60 * 1000)
      const key = slotTime.toISOString().slice(0, 13) // YYYY-MM-DDTHH
      slots[key] = {
        time: key,
        label: slotTime.toLocaleTimeString('en-US', { hour: '2-digit', hour12: true }),
        success: 0,
        failure: 0,
        other: 0,
        total: 0,
      }
    }
    
    // Populate with actual data
    for (const run of runs) {
      const key = run.started_at.slice(0, 13)
      if (slots[key]) {
        if (run.status === 'SUCCESS') slots[key].success++
        else if (run.status === 'FAILURE') slots[key].failure++
        else slots[key].other++
        slots[key].total++
      }
    }
    
    return Object.values(slots)
  }, [runs])

  const maxTotal = Math.max(...chartData.map(d => d.total), 1)
  const successRate = runs.length > 0 
    ? (runs.filter(r => r.status === 'SUCCESS').length / runs.length * 100).toFixed(1)
    : '0'

  // Get unique pipelines
  const pipelines = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const run of runs) {
      counts[run.pipeline_name] = (counts[run.pipeline_name] || 0) + 1
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
  }, [runs])

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg">
      <div className="px-5 py-4 border-b border-xray-border">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium">Runs Overview (Last 24h)</h2>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-xray-success"></span>
              <span className="text-xray-muted">Success</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-xray-danger"></span>
              <span className="text-xray-muted">Failure</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-xray-accent"></span>
              <span className="text-xray-muted">Other</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="p-5">
        <div className="flex gap-6">
          {/* Area Chart */}
          <div className="flex-1">
            <div className="relative h-32">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 bottom-0 w-8 flex flex-col justify-between text-2xs text-xray-dim pr-2 text-right">
                <span>{maxTotal}</span>
                <span>{Math.round(maxTotal / 2)}</span>
                <span>0</span>
              </div>
              
              {/* Grid lines */}
              <div className="absolute left-10 right-0 top-0 bottom-0 flex flex-col justify-between pointer-events-none">
                <div className="border-t border-xray-border/50 border-dashed"></div>
                <div className="border-t border-xray-border/50 border-dashed"></div>
                <div className="border-t border-xray-border"></div>
              </div>
              
              {/* Y-axis line */}
              <div className="absolute left-10 top-0 bottom-0 w-px bg-xray-border"></div>
              
              {/* Chart area */}
              <div className="ml-10 h-full flex items-end gap-1 relative z-10">
                {chartData.map((slot, idx) => {
                  const successH = (slot.success / maxTotal) * 100
                  const failureH = (slot.failure / maxTotal) * 100
                  const otherH = (slot.other / maxTotal) * 100
                  
                  return (
                    <div key={idx} className="flex-1 flex flex-col-reverse h-full group relative max-w-2">
                      {/* Stacked bar */}
                      <div 
                        className="w-full bg-xray-success/80 rounded-t-sm transition-all duration-200 group-hover:bg-xray-success"
                        style={{ height: `${successH}%` }}
                      />
                      <div 
                        className="w-full bg-xray-danger/80 transition-all duration-200 group-hover:bg-xray-danger"
                        style={{ height: `${failureH}%` }}
                      />
                      <div 
                        className="w-full bg-xray-accent/80 transition-all duration-200 group-hover:bg-xray-accent"
                        style={{ height: `${otherH}%` }}
                      />
                      
                      {/* Tooltip */}
                      {slot.total > 0 && (
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 
                                        bg-xray-bg border border-xray-border rounded px-2 py-1 
                                        text-2xs whitespace-nowrap opacity-0 group-hover:opacity-100
                                        transition-opacity pointer-events-none z-10 shadow-lg">
                          <div className="font-medium">{slot.label}</div>
                          <div className="text-xray-success">{slot.success} success</div>
                          {slot.failure > 0 && <div className="text-xray-danger">{slot.failure} failure</div>}
                          {slot.other > 0 && <div className="text-xray-accent">{slot.other} other</div>}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
            
            {/* X-axis line */}
            <div className="ml-10 h-px bg-xray-border"></div>
            
            {/* X-axis labels with ticks */}
            <div className="ml-10 flex justify-between text-2xs text-xray-dim mt-1">
              {[0, 6, 12, 18, 23].map(i => (
                <div key={i} className="flex flex-col items-center">
                  <div className="w-px h-1 bg-xray-border mb-1"></div>
                  <span>{chartData[i]?.label}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Stats sidebar */}
          <div className="w-48 space-y-4 border-l border-xray-border pl-6">
            <div>
              <div className="text-2xs text-xray-muted uppercase tracking-wider mb-1">Success Rate</div>
              <div className="text-2xl font-semibold text-xray-success">{successRate}%</div>
            </div>
            
            <div>
              <div className="text-2xs text-xray-muted uppercase tracking-wider mb-2">Top Pipelines</div>
              <div className="space-y-1.5">
                {pipelines.map(([name, count]) => (
                  <div key={name} className="flex justify-between text-xs">
                    <span className="text-xray-text truncate max-w-[120px]">{name}</span>
                    <span className="text-xray-muted font-mono">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
