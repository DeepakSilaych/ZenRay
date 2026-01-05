import { config } from './config'

const API_BASE = config.apiUrl

// Get auth token from localStorage
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token')
}

// Create fetch with auth headers
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getAuthToken()
  const headers: Record<string, string> = {}
  
  // Copy existing headers
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value
      })
    } else if (Array.isArray(options.headers)) {
      options.headers.forEach(([key, value]) => {
        headers[key] = value
      })
    } else {
      Object.assign(headers, options.headers)
    }
  }
  
  // Only set Content-Type if body is present and not FormData
  if (options.body && !(options.body instanceof FormData)) {
    if (!headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return fetch(url, { ...options, headers })
}

export interface RunSummary {
  run_id: string
  pipeline_name: string
  version: string | null
  status: string
  started_at: string
  ended_at: string | null
  tags: Record<string, string> | null
  step_count: number
}

export interface StepSummary {
  step_id: string
  run_id: string
  kind: string
  name: string
  input_count: number | null
  output_count: number | null
  drop_ratio: number | null
  status: string
  duration_ms: number | null
}

export interface RunDetail {
  run: {
    run_id: string
    pipeline_name: string
    version: string | null
    status: string
    started_at: string
    ended_at: string | null
    tags: Record<string, string> | null
    input_summary: Record<string, unknown> | null
    final_output: Record<string, unknown> | null
  }
  steps: StepSummary[]
}

export interface CandidateSet {
  mode: string
  input_count: number
  output_count: number
  reason_histogram: Record<string, number> | null
  score_histogram: Record<string, number> | null
  top_kept: unknown[] | null
  top_dropped: unknown[] | null
  dropped_by_reason: Record<string, unknown[]> | null
  full_candidates: unknown[] | null
}

export interface StepDetail {
  step: {
    step_id: string
    run_id: string
    parent_step_id: string | null
    kind: string
    name: string
    input_count: number | null
    output_count: number | null
    status: string
    duration_ms: number | null
    started_at: string | null
    ended_at: string | null
    metrics: Record<string, unknown> | null
  }
  candidate_set: CandidateSet | null
  artifacts: unknown[] | null
}

export async function fetchRuns(params?: {
  pipeline_name?: string
  status?: string
  limit?: number
}): Promise<RunSummary[]> {
  const query = new URLSearchParams()
  if (params?.pipeline_name) query.set('pipeline_name', params.pipeline_name)
  if (params?.status) query.set('status', params.status)
  if (params?.limit) query.set('limit', String(params.limit))
  
  const res = await fetchWithAuth(`${API_BASE}/runs?${query}`)
  if (!res.ok) throw new Error('Failed to fetch runs')
  return res.json()
}

export async function fetchRunDetail(runId: string): Promise<RunDetail> {
  const res = await fetchWithAuth(`${API_BASE}/runs/${runId}`)
  if (!res.ok) throw new Error('Failed to fetch run')
  return res.json()
}

export async function fetchStepDetail(stepId: string): Promise<StepDetail> {
  const res = await fetchWithAuth(`${API_BASE}/steps/${stepId}`)
  if (!res.ok) throw new Error('Failed to fetch step')
  return res.json()
}

export async function fetchStepCandidates(stepId: string): Promise<CandidateSet> {
  const res = await fetchWithAuth(`${API_BASE}/steps/${stepId}/candidates`)
  if (!res.ok) throw new Error('Failed to fetch candidates')
  return res.json()
}

export interface CandidateJourneyStep {
  step_id: string
  step_name: string
  step_kind: string
  status: 'kept' | 'dropped'
  drop_reason: string | null
  candidate: Record<string, unknown> | null
}

export interface CandidateTraceResult {
  query: string
  run_id: string
  found: boolean
  journey: CandidateJourneyStep[]
}

export async function traceCandidate(runId: string, query: string): Promise<CandidateTraceResult> {
  const res = await fetchWithAuth(`${API_BASE}/runs/${runId}/trace?q=${encodeURIComponent(query)}`)
  if (!res.ok) throw new Error('Failed to trace candidate')
  return res.json()
}

// --- Run Comparison ---

export interface StepComparisonData {
  step_id: string
  kind: string
  input_count: number | null
  output_count: number | null
  drop_ratio: number | null
  duration_ms: number | null
  status: string
}

export interface StepComparison {
  step_name: string
  in_run_a: boolean
  in_run_b: boolean
  run_a: StepComparisonData | null
  run_b: StepComparisonData | null
  deltas: {
    output_count: number
    drop_ratio: number
    duration_ms: number
  } | null
}

export interface RunComparisonResult {
  run_a: {
    run_id: string
    pipeline_name: string
    version: string | null
    status: string
    total_steps: number
    total_duration_ms: number
    final_output: unknown
  }
  run_b: {
    run_id: string
    pipeline_name: string
    version: string | null
    status: string
    total_steps: number
    total_duration_ms: number
    final_output: unknown
  }
  step_comparisons: StepComparison[]
  summary: {
    steps_only_in_a: number
    steps_only_in_b: number
    steps_in_both: number
    duration_delta_ms: number
    output_changed: boolean
  }
}

export async function compareRuns(runA: string, runB: string): Promise<RunComparisonResult> {
  const res = await fetchWithAuth(`${API_BASE}/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`)
  if (!res.ok) throw new Error('Failed to compare runs')
  return res.json()
}

// --- Auth API ---

export interface ApiKey {
  key_id: string
  key_name: string
  created_at: string
  last_used_at: string | null
}

export interface CreateApiKeyResponse {
  key_id: string
  key_name: string
  api_key: string
  created_at: string
  last_used_at: string | null
}

export async function getCurrentUser() {
  const res = await fetchWithAuth(`${API_BASE}/auth/me`)
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}

export async function createApiKey(name: string): Promise<CreateApiKeyResponse> {
  const res = await fetchWithAuth(`${API_BASE}/auth/api-keys`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to create API key')
  return res.json()
}

export async function listApiKeys(): Promise<ApiKey[]> {
  const res = await fetchWithAuth(`${API_BASE}/auth/api-keys`)
  if (!res.ok) throw new Error('Failed to fetch API keys')
  return res.json()
}

export async function deleteApiKey(keyId: string): Promise<void> {
  const res = await fetchWithAuth(`${API_BASE}/auth/api-keys/${keyId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Failed to delete API key')
}

