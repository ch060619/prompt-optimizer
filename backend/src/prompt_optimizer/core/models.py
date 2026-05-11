from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ExportFormat = Literal["md", "json", "txt", "csv"]


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
    original_prompt: str
    optimized_prompt: str
    analysis: PromptAnalysis
    created_at: datetime


class VersionSummary(BaseModel):
    id: int
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
