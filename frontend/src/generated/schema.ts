// AUTO-GENERATED FILE. DO NOT EDIT.
// RC IDs: RC-062, RC-154, RC-181, RC-184.
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

export interface CleanupRequest {
  confirm?: boolean;
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
  provider?: "offline" | "local" | "openai" | "tongyi" | "zhipu" | "anthropic" | "gemini" | "azure" | "vertex" | "bedrock" | "openrouter" | "deepseek" | "moonshot" | "qwen" | "doubao" | "siliconflow" | "groq" | "together" | "ollama" | "lmstudio";
}

export interface ExportRequest {
  version_id: number;
  format: "md" | "json" | "txt" | "csv";
  output?: string | null;
}

export interface HTTPValidationError {
  detail?: Array<ValidationError>;
}

export interface LocalModelEventRequest {
  event: "download_started" | "download_progress" | "download_paused" | "download_completed" | "verified" | "load_started" | "ready" | "busy" | "unload_started" | "unloaded" | "corrupt" | "update_available" | "update_started" | "failed" | "reset" | "disable" | "enable";
  message?: string;
  progress?: number | null;
  error?: string | null;
}

export interface ModelCleanupRequest {
  model_id?: string | null;
}

export interface ModelDirectoryCheckRequest {
  path: string;
  required_bytes?: number;
}

export interface ModelDirectoryMigrateRequest {
  destination: string;
}

export interface ModelRepairRequest {
  source?: string | null;
}

export interface ModelRollbackRequest {
  version: string;
}

export interface ModelVersionInstallRequest {
  source: string;
  version: string;
  checksum: string;
}

export interface OptimizationSuggestion {
  dimension: string;
  title: string;
  detail: string;
  example: string;
  priority: "high" | "medium" | "low";
}

export interface OptimizationTargets {
  clarity?: boolean;
  completeness?: boolean;
  constraints?: boolean;
  format?: boolean;
  role?: boolean;
  examples?: boolean;
  code_task?: boolean;
  conciseness?: boolean;
  language_preservation?: boolean;
}

export interface OptimizeMetadata {
  provider_requested: string;
  provider_used: string;
  provider_display_name: string;
  system_prompt_version: string;
  model?: string | null;
  execution_location?: "local" | "cloud";
  credential_ref?: string | null;
  fallback_used?: boolean;
  latency_ms: number;
  error_summary?: string | null;
  error_code?: string | null;
  error_category?: string | null;
  provider_request_id?: string | null;
  fallback_chain?: Array<string>;
  estimated_input_tokens?: number | null;
  estimated_output_tokens?: number | null;
  estimated_cost?: number | null;
  budget_limit_tokens?: number | null;
  budget_limit_cost?: number | null;
  budget_blocked?: boolean;
  fallback_reason?: "not_installed" | "not_ready" | "out_of_memory" | "timeout" | null;
  recovery_action?: "install" | "repair" | "free_memory" | "retry" | "configure_credentials" | "check_balance" | "wait_and_retry" | "change_region" | "choose_model" | "fix_parameters" | "review_content" | "check_network" | "cancel" | null;
  selection_scope?: "global" | "workspace" | "session" | "optimizer" | "default";
  provider_health?: "healthy" | "unavailable" | "fallback";
  quality_score_before: number;
  quality_score_after: number;
  quality_score_delta: number;
}

export interface OptimizeRequest {
  prompt: string;
  template_id?: string | null;
  variables?: Record<string, unknown>;
  provider?: "offline" | "local" | "openai" | "tongyi" | "zhipu" | "anthropic" | "gemini" | "azure" | "vertex" | "bedrock" | "openrouter" | "deepseek" | "moonshot" | "qwen" | "doubao" | "siliconflow" | "groq" | "together" | "ollama" | "lmstudio";
  model?: string | null;
  optimizer_provider?: "offline" | "local" | "openai" | "tongyi" | "zhipu" | "anthropic" | "gemini" | "azure" | "vertex" | "bedrock" | "openrouter" | "deepseek" | "moonshot" | "qwen" | "doubao" | "siliconflow" | "groq" | "together" | "ollama" | "lmstudio" | null;
  optimizer_model?: string | null;
  save_prompt_history?: boolean;
  targets?: OptimizationTargets | null;
  strategy?: "rules" | "model" | "combined";
  max_tokens?: number | null;
  max_cost?: number | null;
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
  accepted?: boolean;
  accepted_at?: string | null;
  provider_used?: string | null;
  model?: string | null;
  selection_scope?: "global" | "workspace" | "session" | "optimizer" | "default";
  provider_health?: "healthy" | "unavailable" | "fallback";
}

export interface RunnerGenerateRequest {
  prompt: string;
  model_id?: string | null;
  request_id?: string | null;
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
  accepted?: boolean;
  accepted_at?: string | null;
  provider_used?: string | null;
  model?: string | null;
  selection_scope?: "global" | "workspace" | "session" | "optimizer" | "default";
  provider_health?: "healthy" | "unavailable" | "fallback";
}
