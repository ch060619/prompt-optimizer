from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ExportFormat = Literal["md", "json", "txt", "csv"]
ModelProviderName = Literal[
    "offline",
    "local",
    "openai",
    "tongyi",
    "zhipu",
    "anthropic",
    "gemini",
    "azure",
    "vertex",
    "bedrock",
    "openrouter",
    "deepseek",
    "moonshot",
    "qwen",
    "doubao",
    "siliconflow",
    "groq",
    "together",
    "ollama",
    "lmstudio",
]
OptimizationStrategy = Literal["rules", "model", "combined"]
ProviderSelectionScope = Literal[
    "global",
    "workspace",
    "session",
    "optimizer",
    "default",
]
ProviderHealth = Literal["healthy", "unavailable", "fallback"]
FallbackReason = Literal["not_installed", "not_ready", "out_of_memory", "timeout"]
RecoveryAction = Literal[
    "install",
    "repair",
    "free_memory",
    "retry",
    "configure_credentials",
    "check_balance",
    "wait_and_retry",
    "change_region",
    "choose_model",
    "fix_parameters",
    "review_content",
    "check_network",
    "cancel",
]
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


# RC IDs: RC-154, RC-155. Keep optimization dimensions and composition strategy in the API contract.
class OptimizationTargets(BaseModel):
    clarity: bool = True
    completeness: bool = True
    constraints: bool = True
    format: bool = True
    role: bool = True
    examples: bool = True
    code_task: bool = True
    conciseness: bool = True
    language_preservation: bool = True

    def has_enabled_target(self) -> bool:
        return any(
            (
                self.clarity,
                self.completeness,
                self.constraints,
                self.format,
                self.role,
                self.examples,
                self.code_task,
                self.conciseness,
                self.language_preservation,
            )
        )


class PromptVersion(BaseModel):
    id: int
    owner_id: int = 1
    project_id: int | None = None
    original_prompt: str
    optimized_prompt: str
    analysis: PromptAnalysis
    created_at: datetime
    accepted: bool = False
    accepted_at: datetime | None = None
    provider_used: str | None = None
    model: str | None = None
    selection_scope: ProviderSelectionScope = "default"
    provider_health: ProviderHealth = "healthy"


class VersionSummary(BaseModel):
    id: int
    owner_id: int = 1
    project_id: int | None = None
    original_preview: str
    optimized_preview: str
    score: float
    created_at: datetime
    accepted: bool = False
    accepted_at: datetime | None = None
    provider_used: str | None = None
    model: str | None = None
    selection_scope: ProviderSelectionScope = "default"
    provider_health: ProviderHealth = "healthy"


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


# RC ID: RC-184. Require explicit confirmation before destructive local cleanup.
class CleanupRequest(BaseModel):
    confirm: bool = False


LocalModelEventName = Literal[
    "download_started",
    "download_progress",
    "download_paused",
    "download_completed",
    "verified",
    "load_started",
    "ready",
    "busy",
    "unload_started",
    "unloaded",
    "corrupt",
    "update_available",
    "update_started",
    "failed",
    "reset",
    "disable",
    "enable",
]


# RC ID: RC-194. Accept only lifecycle events consumed by the local model GUI.
class LocalModelEventRequest(BaseModel):
    event: LocalModelEventName
    message: str = ""
    progress: int | None = Field(default=None, ge=0, le=100)
    error: str | None = None


# RC ID: RC-197. Keep model directory lifecycle inputs explicit and path-scoped.
class ModelDirectoryCheckRequest(BaseModel):
    path: str = Field(min_length=1)
    required_bytes: int = Field(default=0, ge=0)


class ModelDirectoryMigrateRequest(BaseModel):
    destination: str = Field(min_length=1)


class ModelVersionInstallRequest(BaseModel):
    source: str = Field(min_length=1)
    version: str = Field(min_length=1)
    checksum: str = Field(min_length=64, max_length=71)


class ModelRollbackRequest(BaseModel):
    version: str = Field(min_length=1)


class ModelRepairRequest(BaseModel):
    source: str | None = None


class ModelCleanupRequest(BaseModel):
    model_id: str | None = None


# RC ID: RC-198. Keep local runner requests independent from runner commands.
class RunnerGenerateRequest(BaseModel):
    prompt: str
    model_id: str | None = None
    request_id: str | None = None


class AnalyzeRequest(BaseModel):
    prompt: str


class OptimizeRequest(BaseModel):
    prompt: str
    template_id: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    provider: ModelProviderName = "offline"
    model: str | None = None
    optimizer_provider: ModelProviderName | None = None
    optimizer_model: str | None = None
    save_prompt_history: bool = True
    targets: OptimizationTargets | None = None
    strategy: OptimizationStrategy = "combined"
    max_tokens: int | None = Field(default=None, gt=0)
    max_cost: float | None = Field(default=None, ge=0)


class OptimizeMetadata(BaseModel):
    # RC ID: RC-157. Record non-sensitive optimization quality metrics.
    provider_requested: str
    provider_used: str
    provider_display_name: str
    system_prompt_version: str
    model: str | None = None
    execution_location: Literal["local", "cloud"] = "local"
    credential_ref: str | None = None
    fallback_used: bool = False
    latency_ms: int
    error_summary: str | None = None
    error_code: str | None = None
    error_category: str | None = None
    provider_request_id: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    estimated_input_tokens: int | None = None
    estimated_output_tokens: int | None = None
    estimated_cost: float | None = None
    budget_limit_tokens: int | None = None
    budget_limit_cost: float | None = None
    budget_blocked: bool = False
    fallback_reason: FallbackReason | None = None
    recovery_action: RecoveryAction | None = None
    selection_scope: ProviderSelectionScope = "default"
    provider_health: ProviderHealth = "healthy"
    quality_score_before: float
    quality_score_after: float
    quality_score_delta: float


class OptimizeResponse(BaseModel):
    version_id: int | None = None
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
