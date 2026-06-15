export type Priority = "high" | "medium" | "low";

export interface ScoreDimension {
  name: string;
  label: string;
  score: number;
  weight: number;
  reason: string;
}

export interface ScoreBreakdown {
  total_score: number;
  dimensions: ScoreDimension[];
}

export interface Suggestion {
  dimension: string;
  title: string;
  detail: string;
  example: string;
  priority: Priority;
}

export interface PromptAnalysis {
  prompt: string;
  optimized_prompt?: string | null;
  score: ScoreBreakdown;
  suggestions: Suggestion[];
  strengths: string[];
  created_at: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  tags: string[];
  template: string;
  variables: string[];
  best_practices: string[];
}

export interface OptimizeResponse {
  version_id: number;
  analysis: PromptAnalysis;
  metadata: {
    provider_requested: string;
    provider_used: string;
    fallback_used: boolean;
    latency_ms: number;
    error_summary?: string | null;
  };
}

export type StreamEventName =
  | "started"
  | "analysis"
  | "chunk"
  | "fallback"
  | "saved"
  | "completed"
  | "error";

export interface StreamEvent {
  event: StreamEventName;
  data: unknown;
}

export interface VersionSummary {
  id: number;
  original_preview: string;
  optimized_preview: string;
  score: number;
  created_at: string;
}

export interface DiffResult {
  old_id: number;
  new_id: number;
  old_score: number;
  new_score: number;
  score_delta: number;
  diff_lines: string[];
}
