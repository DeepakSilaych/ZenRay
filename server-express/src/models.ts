import { z } from 'zod'

// Enums
export const StepKind = z.enum([
  'RETRIEVE', 'FILTER', 'RANK', 'LLM_CALL', 
  'JUDGE', 'SELECT', 'TRANSFORM', 'TOOL_CALL'
])

export const RunStatus = z.enum(['RUNNING', 'SUCCESS', 'FAILURE', 'TIMEOUT'])

export const StepStatus = z.enum(['RUNNING', 'SUCCESS', 'FAILURE', 'SKIPPED'])

export const CaptureMode = z.enum(['SUMMARY', 'TOP_K', 'FULL'])

export const ArtifactType = z.enum([
  'prompt', 'response', 'config', 'input', 
  'output', 'judgments', 'metadata', 'error', 'debug'
])

// Schemas
export const CandidateSet = z.object({
  mode: CaptureMode.default('SUMMARY'),
  input_count: z.number().default(0),
  output_count: z.number().default(0),
  reason_histogram: z.record(z.number()).optional(),
  score_histogram: z.record(z.number()).optional(),
  top_kept: z.array(z.record(z.any())).optional(),
  top_dropped: z.array(z.record(z.any())).optional(),
  dropped_by_reason: z.record(z.array(z.record(z.any()))).optional(),
  full_candidates: z.array(z.record(z.any())).optional(),
})

export const Artifact = z.object({
  artifact_id: z.string(),
  step_id: z.string(),
  type: ArtifactType,
  content: z.any(),
})

export const Step = z.object({
  step_id: z.string(),
  run_id: z.string(),
  parent_step_id: z.string().optional(),
  kind: StepKind,
  name: z.string(),
  input_count: z.number().optional(),
  output_count: z.number().optional(),
  status: StepStatus.default('RUNNING'),
  duration_ms: z.number().optional(),
  started_at: z.string().optional(),
  ended_at: z.string().optional(),
  metrics: z.record(z.any()).optional(),
  candidate_set: CandidateSet.optional(),
  artifacts: z.array(Artifact).optional(),
})

export const Run = z.object({
  run_id: z.string(),
  pipeline_name: z.string(),
  version: z.string().optional(),
  status: RunStatus.default('RUNNING'),
  started_at: z.string(),
  ended_at: z.string().optional(),
  tags: z.record(z.string()).optional(),
  input_summary: z.record(z.any()).optional(),
  final_output: z.record(z.any()).optional(),
})

export const IngestPayload = z.object({
  schema_version: z.string().default('1.0'),
  runs: z.array(Run).optional(),
  steps: z.array(Step).optional(),
})

// Types
export type Run = z.infer<typeof Run>
export type Step = z.infer<typeof Step>
export type CandidateSet = z.infer<typeof CandidateSet>
export type Artifact = z.infer<typeof Artifact>
export type IngestPayload = z.infer<typeof IngestPayload>

// Response types
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
  run: Run
  steps: StepSummary[]
}

export interface StepDetail {
  step: Step
  candidate_set: CandidateSet | null
  artifacts: Record<string, unknown>[] | null
}

