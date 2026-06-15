from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ExportFormat = Literal["md", "json", "txt", "csv"]
ModelProviderName = Literal["offline", "openai", "tongyi", "zhipu"]
TaskStatus = Literal["queued", "running", "succeeded", "failed"]
TaskKind = Literal["optimize", "export", "evaluate"]


class ScoreDimension(BaseModel):
    name: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(gt=0)
    reason: str


class ScoreBreakdown(BaseModel):
    total_score: float = Field(ge=0, le=100)
    dimensions: list[ScoreDimension]


class OptimizationSuggestion(BaseModel):
    dimension: str
    title: str
    detail: str
    example: str
    priority: Literal["high", "medium", "low"]


class PromptAnalysis(BaseModel):
    prompt: str
    optimized_prompt: str | None = None
    score: ScoreBreakdown
    suggestions: list[OptimizationSuggestion]
    strengths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PromptTemplate(BaseModel):
    id: str
    name: str
    category: str
    description: str
    tags: list[str]
    template: str
    variables: list[str]
    best_practices: list[str]


class PromptVersion(BaseModel):
    id: int
    owner_id: int = 1
    project_id: int | None = None
    original_prompt: str
    optimized_prompt: str
    analysis: PromptAnalysis
    created_at: datetime


class VersionSummary(BaseModel):
    id: int
    owner_id: int = 1
    project_id: int | None = None
    original_preview: str
    optimized_preview: str
    score: float
    created_at: datetime


class DiffResult(BaseModel):
    old_id: int
    new_id: int
    old_score: float
    new_score: float
    score_delta: float
    diff_lines: list[str]


class ExportRequest(BaseModel):
    version_id: int
    format: ExportFormat
    output: str | None = None


class AnalyzeRequest(BaseModel):
    prompt: str


class OptimizeRequest(BaseModel):
    prompt: str
    template_id: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    provider: ModelProviderName = "offline"


class OptimizeMetadata(BaseModel):
    provider_requested: str
    provider_used: str
    fallback_used: bool = False
    latency_ms: int
    error_summary: str | None = None


class OptimizeResponse(BaseModel):
    version_id: int
    analysis: PromptAnalysis
    metadata: OptimizeMetadata


class UserPublic(BaseModel):
    id: int
    username: str
    created_at: datetime


class ProjectSpace(BaseModel):
    id: int
    owner_id: int
    name: str
    created_at: datetime


class AuthRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class TaskRecord(BaseModel):
    id: str
    owner_id: int
    kind: TaskKind
    status: TaskStatus
    input_json: dict[str, Any]
    result_json: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskCreateResponse(BaseModel):
    task_id: str
    status: TaskStatus


class EvaluateTaskRequest(BaseModel):
    prompts: list[str] = Field(min_length=1, max_length=100)
    provider: ModelProviderName = "offline"
