import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchStepDetail, StepDetail, CandidateSet } from '../api'

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

          {/* Reason Histogram with Expandable Rows */}
          {candidate_set.reason_histogram && Object.keys(candidate_set.reason_histogram).length > 0 && (
            <ReasonHistogramTable candidateSet={candidate_set} />
          )}

          {/* Score Histogram */}
          {candidate_set.score_histogram && Object.keys(candidate_set.score_histogram).length > 0 && (
            <ScoreHistogram histogram={candidate_set.score_histogram} />
          )}

          {/* Top Kept */}
          {candidate_set.top_kept && candidate_set.top_kept.length > 0 && (
            <CandidatesTable 
              title="Top Kept" 
              candidates={candidate_set.top_kept} 
              variant="success"
            />
          )}

          {/* Top Dropped */}
          {candidate_set.top_dropped && candidate_set.top_dropped.length > 0 && (
            <CandidatesTable 
              title="Top Dropped" 
              candidates={candidate_set.top_dropped} 
              variant="danger"
            />
          )}
        </div>
      )}

      {/* Artifacts */}
      {artifacts && artifacts.length > 0 && (
        <ArtifactsSection artifacts={artifacts} />
      )}
    </div>
  )
}

function ScoreHistogram({ histogram }: { histogram: Record<string, number> }) {
  const entries = Object.entries(histogram).sort(([a], [b]) => {
    // Sort by bucket range (extract first number)
    const aNum = parseFloat(a.split('-')[0]) || 0
    const bNum = parseFloat(b.split('-')[0]) || 0
    return aNum - bNum
  })
  
  const total = entries.reduce((sum, [, count]) => sum + count, 0)
  const max = Math.max(...entries.map(([, count]) => count))

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-xray-border flex items-center justify-between">
        <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Score Distribution</h3>
        <span className="text-2xs text-xray-dim">{total} total</span>
      </div>
      <div className="p-6">
        <div className="flex items-end justify-center gap-4" style={{ height: '140px' }}>
          {entries.map(([bucket, count]) => {
            const heightPct = max > 0 ? (count / max) * 100 : 0
            const pct = total > 0 ? Math.round((count / total) * 100) : 0
            
            return (
              <div key={bucket} className="flex-1 flex flex-col items-center max-w-24 group">
                {/* Count label on top of bar */}
                <div className="text-xs font-mono text-xray-muted mb-1">
                  {count}
                </div>
                {/* Bar container with fixed height */}
                <div className="w-full relative" style={{ height: '80px' }}>
                  <div
                    className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-xray-accent to-xray-accent/60 rounded-t 
                               hover:from-xray-accentHover hover:to-xray-accent transition-colors"
                    style={{ height: `${heightPct}%`, minHeight: count > 0 ? '4px' : '0' }}
                  />
                </div>
                {/* Percentage */}
                <div className="text-xs font-mono text-xray-text mt-2">{pct}%</div>
                {/* Range label */}
                <div className="text-2xs font-mono text-xray-dim mt-0.5 truncate w-full text-center" title={bucket}>
                  {bucket}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// Extract column headers from candidates
function getColumns(candidates: unknown[]): string[] {
  const allKeys = new Set<string>()
  candidates.forEach(c => {
    if (c && typeof c === 'object') {
      Object.keys(c as Record<string, unknown>).forEach(k => allKeys.add(k))
    }
  })
  // Prioritize common columns
  const priority = ['id', 'name', 'title', 'category', 'type', 'price', 'score', 'confidence']
  const sorted = [...allKeys].sort((a, b) => {
    const aIdx = priority.indexOf(a)
    const bIdx = priority.indexOf(b)
    if (aIdx >= 0 && bIdx >= 0) return aIdx - bIdx
    if (aIdx >= 0) return -1
    if (bIdx >= 0) return 1
    return a.localeCompare(b)
  })
  return sorted
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2)
  }
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function CandidatesTable({ 
  title, 
  candidates, 
  variant,
  maxRows = 10
}: { 
  title: string
  candidates: unknown[]
  variant: 'success' | 'danger' | 'default'
  maxRows?: number
}) {
  const columns = getColumns(candidates)
  const displayCandidates = candidates.slice(0, maxRows)
  
  const variantStyles = {
    success: 'text-xray-success',
    danger: 'text-xray-danger',
    default: 'text-xray-muted'
  }

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-xray-border flex items-center justify-between">
        <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">{title}</h3>
        <span className={`text-2xs ${variantStyles[variant]}`}>{candidates.length} items</span>
      </div>
      <div className="overflow-x-auto">
        <table>
          <thead>
            <tr className="border-b border-xray-border">
              {columns.map(col => (
                <th key={col} className="px-3 py-2 text-left whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-xray-border">
            {displayCandidates.map((c, i) => (
              <tr key={i} className="hover:bg-xray-elevated/30">
                {columns.map(col => (
                  <td key={col} className="px-3 py-2 font-mono text-xs whitespace-nowrap">
                    {formatValue((c as Record<string, unknown>)[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {candidates.length > maxRows && (
        <div className="px-4 py-2 border-t border-xray-border text-xs text-xray-dim">
          Showing {maxRows} of {candidates.length}
        </div>
      )}
    </div>
  )
}

function ReasonHistogramTable({ candidateSet }: { candidateSet: CandidateSet }) {
  const [expandedReason, setExpandedReason] = useState<string | null>(null)
  const histogram = candidateSet.reason_histogram!
  const droppedByReason = candidateSet.dropped_by_reason
  const total = Object.values(histogram).reduce((a, b) => a + b, 0)

  return (
    <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-xray-border flex items-center justify-between">
        <h3 className="text-xs font-medium text-xray-muted uppercase tracking-wider">Drop Reasons</h3>
        {droppedByReason && (
          <span className="text-2xs text-xray-dim">Click row to expand</span>
        )}
      </div>
      <table>
        <thead>
          <tr className="border-b border-xray-border">
            <th className="px-4 py-2 w-6"></th>
            <th className="px-4 py-2">Reason</th>
            <th className="px-4 py-2 text-right">Count</th>
            <th className="px-4 py-2 w-1/2">Distribution</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(histogram)
            .sort(([, a], [, b]) => b - a)
            .map(([reason, count]) => {
              const pct = Math.round((count / total) * 100)
              const isExpanded = expandedReason === reason
              const hasDetails = droppedByReason && droppedByReason[reason]
              const droppedCandidates = hasDetails ? droppedByReason[reason] : []
              
              return (
                <React.Fragment key={reason}>
                  <tr
                    className={`border-b border-xray-border ${hasDetails ? 'cursor-pointer hover:bg-xray-elevated/50' : ''} ${isExpanded ? 'bg-xray-elevated/30' : ''}`}
                    onClick={() => hasDetails && setExpandedReason(isExpanded ? null : reason)}
                  >
                    <td className="px-4 py-2 text-xray-dim">
                      {hasDetails && (
                        <span className="text-xs">{isExpanded ? '▼' : '▶'}</span>
                      )}
                    </td>
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
                  {isExpanded && hasDetails && (
                    <tr key={`${reason}-details`}>
                      <td colSpan={4} className="bg-xray-bg border-b border-xray-border p-0">
                        <div className="p-3">
                          <div className="text-xs text-xray-muted mb-2">
                            {droppedCandidates.length} candidates dropped for "{reason}"
                          </div>
                          <DroppedCandidatesTable candidates={droppedCandidates} />
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
        </tbody>
      </table>
    </div>
  )
}

function DroppedCandidatesTable({ candidates }: { candidates: unknown[] }) {
  const columns = getColumns(candidates)
  const maxRows = 10
  const displayCandidates = candidates.slice(0, maxRows)

  return (
    <div className="border border-xray-border rounded overflow-hidden">
      <div className="overflow-x-auto max-h-64">
        <table className="w-full">
          <thead className="bg-xray-surface sticky top-0">
            <tr className="border-b border-xray-border">
              {columns.map(col => (
                <th key={col} className="px-3 py-2 text-left whitespace-nowrap text-2xs">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-xray-border bg-xray-surface">
            {displayCandidates.map((c, i) => (
              <tr key={i} className="hover:bg-xray-elevated/30">
                {columns.map(col => (
                  <td key={col} className="px-3 py-1.5 font-mono text-xs whitespace-nowrap">
                    {formatValue((c as Record<string, unknown>)[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {candidates.length > maxRows && (
        <div className="px-3 py-1.5 border-t border-xray-border text-2xs text-xray-dim bg-xray-surface">
          Showing {maxRows} of {candidates.length}
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

// Artifact type icons and styling
const ARTIFACT_STYLES: Record<string, { icon: string; label: string; bgClass: string }> = {
  prompt: { icon: '💬', label: 'LLM Prompt', bgClass: 'bg-purple-500/10 border-purple-500/20' },
  response: { icon: '🤖', label: 'LLM Response', bgClass: 'bg-blue-500/10 border-blue-500/20' },
  config: { icon: '⚙️', label: 'Configuration', bgClass: 'bg-slate-500/10 border-slate-500/20' },
  judgments: { icon: '⚖️', label: 'Judgments', bgClass: 'bg-amber-500/10 border-amber-500/20' },
}

function ArtifactsSection({ artifacts }: { artifacts: unknown[] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)
  
  // Group artifacts by type
  const grouped = artifacts.reduce<Record<string, { art: Record<string, unknown>; idx: number }[]>>((acc, art, idx) => {
    const type = (art as Record<string, unknown>).type as string
    if (!acc[type]) acc[type] = []
    acc[type].push({ art: art as Record<string, unknown>, idx })
    return acc
  }, {})
  
  // Check if this is an LLM step (has prompt + response)
  const isLlmStep = 'prompt' in grouped && 'response' in grouped

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-xray-muted">Artifacts</h2>
        <span className="text-2xs text-xray-dim">{artifacts.length} items</span>
      </div>
      
      {isLlmStep ? (
        // LLM-specific layout: Prompt + Response side by side
        <div className="grid grid-cols-2 gap-4">
          {grouped.prompt?.map(({ art, idx }) => (
            <ArtifactCard 
              key={idx} 
              artifact={art} 
              isExpanded={expandedIdx === idx}
              onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
            />
          ))}
          {grouped.response?.map(({ art, idx }) => (
            <ArtifactCard 
              key={idx} 
              artifact={art}
              isExpanded={expandedIdx === idx}
              onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
            />
          ))}
        </div>
      ) : null}
      
      {/* Other artifacts in a grid */}
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(grouped)
          .filter(([type]) => !isLlmStep || !['prompt', 'response'].includes(type))
          .flatMap(([, items]) => items)
          .map(({ art, idx }) => (
            <ArtifactCard 
              key={idx} 
              artifact={art}
              isExpanded={expandedIdx === idx}
              onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
            />
          ))}
      </div>
    </div>
  )
}

function ArtifactCard({ 
  artifact, 
  isExpanded, 
  onToggle 
}: { 
  artifact: Record<string, unknown>
  isExpanded: boolean
  onToggle: () => void
}) {
  const type = artifact.type as string
  const content = artifact.content
  const style = ARTIFACT_STYLES[type] || { icon: '📄', label: type, bgClass: 'bg-xray-elevated border-xray-border' }
  
  const isTextContent = typeof content === 'string'
  const displayContent = isTextContent 
    ? content 
    : JSON.stringify(content, null, 2)
  
  // Truncate for preview
  const previewLength = 200
  const needsTruncation = displayContent.length > previewLength
  const preview = needsTruncation 
    ? displayContent.slice(0, previewLength) + '...' 
    : displayContent

  return (
    <div className={`bg-xray-surface border rounded-lg overflow-hidden ${style.bgClass}`}>
      <div 
        className="px-4 py-3 border-b border-xray-border flex items-center justify-between cursor-pointer hover:bg-xray-elevated/30"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{style.icon}</span>
          <span className="text-xs font-medium">{style.label}</span>
        </div>
        <span className="text-xs text-xray-dim">
          {isExpanded ? '▼ collapse' : '▶ expand'}
        </span>
      </div>
      
      <div className={`transition-all duration-200 ${isExpanded ? 'max-h-[500px] overflow-auto' : 'max-h-28 overflow-hidden'}`}>
        <pre className={`px-4 py-3 text-xs font-mono whitespace-pre-wrap break-words ${
          isTextContent ? 'text-xray-text leading-relaxed' : 'text-xray-muted'
        }`}>
          {isExpanded ? displayContent : preview}
        </pre>
      </div>
      
      {!isExpanded && needsTruncation && (
        <div 
          className="px-4 py-2 border-t border-xray-border text-2xs text-xray-accent cursor-pointer hover:bg-xray-elevated/30"
          onClick={onToggle}
        >
          Click to show full content ({displayContent.length} chars)
        </div>
      )}
    </div>
  )
}

