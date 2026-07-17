// AUTO-GENERATED FILE. DO NOT EDIT.
// RC ID: RC-062.
// Source: docs/api/openapi-v1.json
// Generator: scripts/generate_api.py

export interface AnalyzeRequest {
  prompt: string;
}

export interface AuthRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user: UserPublic;
}

export interface DiffResult {
  old_id: number;
  new_id: number;
  old_score: number;
  new_score: number;
  score_delta: number;
  diff_lines: Array<string>;
}

export interface EvaluateTaskRequest {
  prompts: Array<string>;
  provider?: "offline" | "openai" | "tongyi" | "zhipu";
}

export interface ExportRequest {
  version_id: number;
  format: "md" | "json" | "txt" | "csv";
  output?: string | null;
}

export interface HTTPValidationError {
  detail?: Array<ValidationError>;
}

export interface OptimizationSuggestion {
  dimension: string;
  title: string;
  detail: string;
  example: string;
  priority: "high" | "medium" | "low";
}

export interface OptimizeMetadata {
  provider_requested: string;
  provider_used: string;
  fallback_used?: boolean;
  latency_ms: number;
  error_summary?: string | null;
}

export interface OptimizeRequest {
  prompt: string;
  template_id?: string | null;
  variables?: Record<string, unknown>;
  provider?: "offline" | "openai" | "tongyi" | "zhipu";
}

export interface OptimizeResponse {
  version_id?: number | null;
  analysis: PromptAnalysis;
  metadata: OptimizeMetadata;
}

export interface ProjectSpace {
  id: number;
  owner_id: number;
  name: string;
  created_at: string;
}

export interface PromptAnalysis {
  prompt: string;
  optimized_prompt?: string | null;
  score: ScoreBreakdown;
  suggestions: Array<OptimizationSuggestion>;
  strengths?: Array<string>;
  created_at?: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  tags: Array<string>;
  template: string;
  variables: Array<string>;
  best_practices: Array<string>;
}

export interface PromptVersion {
  id: number;
  owner_id?: number;
  project_id?: number | null;
  original_prompt: string;
  optimized_prompt: string;
  analysis: PromptAnalysis;
  created_at: string;
}

export interface ScoreBreakdown {
  total_score: number;
  dimensions: Array<ScoreDimension>;
}

export interface ScoreDimension {
  name: string;
  label: string;
  score: number;
  weight: number;
  reason: string;
}

export interface TaskCreateResponse {
  task_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
}

export interface TaskRecord {
  id: string;
  owner_id: number;
  kind: "optimize" | "export" | "evaluate";
  status: "queued" | "running" | "succeeded" | "failed";
  input_json: Record<string, unknown>;
  result_json?: Record<string, unknown> | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserPublic {
  id: number;
  username: string;
  created_at: string;
}

export interface ValidationError {
  loc: Array<string | number>;
  msg: string;
  type: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

export interface VersionSummary {
  id: number;
  owner_id?: number;
  project_id?: number | null;
  original_preview: string;
  optimized_preview: string;
  score: number;
  created_at: string;
}
