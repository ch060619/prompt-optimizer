from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock
from time import perf_counter
from typing import Literal, cast
from uuid import uuid4

from prompt_optimizer.auth.service import AuthError, AuthService
from prompt_optimizer.cleanup import LocalDataCleanupService
from prompt_optimizer.config import ConfigService
from prompt_optimizer.contracts import PromptOptimizer, ProviderCatalog
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.language import LanguageProfile
from prompt_optimizer.core.models import (
    AuthResponse,
    ExecutionDestination,
    FallbackReason,
    OptimizationStrategy,
    OptimizationTargets,
    OptimizeMetadata,
    OptimizeResponse,
    PromptAnalysis,
    PromptTemplate,
    ProviderSelectionScope,
    RecoveryAction,
    UserPublic,
)
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.core.output_validation import OutputValidator
from prompt_optimizer.core.structure import StructuredPrompt
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.metrics import LocalMetricsAggregator
from prompt_optimizer.paths import app_data_dir
from prompt_optimizer.prompts.system import SYSTEM_PROMPT, SYSTEM_PROMPT_VERSION
from prompt_optimizer.providers import (
    LocalModelFailure,
    ModelProviderError,
    ModelRequest,
    ProviderCancelledError,
    ProviderEventType,
    ProviderRegistry,
    ProviderSelection,
)
from prompt_optimizer.providers.budget import BudgetEstimate, enforce_budget, estimate_request
from prompt_optimizer.public import (
    declared_execution_destination,
    error_category_for,
    error_code_for,
    execution_destination,
    fallback_details_for,
    provider_public_metadata,
    sanitize_error_message,
)
from prompt_optimizer.retention import RetentionService
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.tasks import TaskService
from prompt_optimizer.templates.manager import TemplateManager

OptimizationStreamEventName = Literal["analysis", "chunk", "fallback", "completed"]


# RC IDs: RC-154, RC-155, RC-156, RC-157, RC-181, RC-184. Preserve targets and composition
# strategy, validate output, and record non-sensitive quality metrics.
@dataclass(frozen=True)
class OptimizationStreamEvent:
    event: OptimizationStreamEventName
    data: object


def _fallback_allowed(provider_name: str, error: BaseException) -> bool:
    if isinstance(error, ProviderCancelledError):
        return False
    if provider_name == "local":
        return isinstance(error, LocalModelFailure)
    return True


class PromptOptimizationService:
    """Single routing and result-building service for every optimization entry point."""

    def __init__(
        self,
        *,
        analyzer: Analyzer,
        optimizer: PromptOptimizer,
        providers: ProviderCatalog,
        versions: VersionService,
        output_validator: OutputValidator | None = None,
        metrics: LocalMetricsAggregator | None = None,
    ) -> None:
        self.analyzer = analyzer
        self.optimizer = optimizer
        self.providers = providers
        self.versions = versions
        self.output_validator = output_validator or OutputValidator()
        self.metrics = metrics or LocalMetricsAggregator()
        self._cancellations: dict[str, Event] = {}
        self._cancellation_lock = Lock()

    def optimize(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        targets: OptimizationTargets | None = None,
        strategy: OptimizationStrategy = "combined",
        provider_name: str = "offline",
        model: str | None = None,
        optimizer_provider: str | None = None,
        optimizer_model: str | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
        max_tokens: int | None = None,
        max_cost: float | None = None,
        request_id: str | None = None,
    ) -> OptimizeResponse:
        optimization_id = request_id or uuid4().hex
        cancellation = Event()
        with self._cancellation_lock:
            self._cancellations[optimization_id] = cancellation
        try:
            return self._optimize(
                original_prompt=original_prompt,
                prompt=prompt,
                template=template,
                targets=targets,
                strategy=strategy,
                provider_name=provider_name,
                model=model,
                optimizer_provider=optimizer_provider,
                optimizer_model=optimizer_model,
                owner_id=owner_id,
                project_id=project_id,
                save_prompt_history=save_prompt_history,
                max_tokens=max_tokens,
                max_cost=max_cost,
                request_id=optimization_id,
                cancel_event=cancellation,
            )
        finally:
            with self._cancellation_lock:
                self._cancellations.pop(optimization_id, None)

    def _optimize(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        targets: OptimizationTargets | None = None,
        strategy: OptimizationStrategy = "combined",
        provider_name: str = "offline",
        model: str | None = None,
        optimizer_provider: str | None = None,
        optimizer_model: str | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
        max_tokens: int | None = None,
        max_cost: float | None = None,
        request_id: str,
        cancel_event: Event,
    ) -> OptimizeResponse:
        structure, language_profile, request = self._protected_request(
            prompt,
            template,
            targets=targets,
            strategy=strategy,
            request_id=request_id,
            cancel_event=cancel_event,
        )
        quality_score_before = self.analyzer.analyze(prompt).score.total_score
        fallback_used = False
        error_summary: str | None = None
        error_code: str | None = None
        error_category: str | None = None
        provider_request_id: str | None = None
        fallback_reason: FallbackReason | None = None
        recovery_action: RecoveryAction | None = None
        selection = self._resolve_selection(
            provider_name="offline" if strategy == "rules" else provider_name,
            model=model,
            optimizer_provider=optimizer_provider,
            optimizer_model=optimizer_model,
        )
        provider = selection.provider
        estimate = estimate_request(request, provider)
        enforce_budget(estimate, max_tokens=max_tokens, max_cost=max_cost)
        provider_started = perf_counter()
        try:
            provider_response = provider.optimize(request)
            if cancel_event.is_set():
                raise ProviderCancelledError("优化请求已取消。") from None
        except (ModelProviderError, RuntimeError, ValueError) as exc:
            self.metrics.record_request(
                provider=selection.name,
                latency_ms=int((perf_counter() - provider_started) * 1000),
                success=False,
            )
            if selection.name == "offline" or not _fallback_allowed(selection.name, exc):
                raise
            fallback_used = True
            error_summary = sanitize_error_message(exc)
            error_code = error_code_for(exc)
            error_category = error_category_for(exc)
            provider_request_id = getattr(exc, "request_id", None)
            fallback_reason, recovery_action = fallback_details_for(exc)
            provider = self.providers.get("offline")
            provider_response = provider.optimize(request)
            if cancel_event.is_set():
                raise ProviderCancelledError("优化请求已取消。") from None
        usage = provider_response.usage or {}
        self.metrics.record_request(
            provider=selection.name,
            latency_ms=provider_response.latency_ms,
            success=True,
            input_tokens=_usage_int(usage, "prompt_tokens", "input_tokens"),
            output_tokens=_usage_int(usage, "completion_tokens", "output_tokens"),
        )
        optimized_prompt = self._validate_output(
            provider_response.analysis.optimized_prompt or request.prompt,
            structure=structure,
            language_profile=language_profile,
            targets=targets,
        )
        analysis = self.analyzer.analyze(optimized_prompt)
        analysis.optimized_prompt = optimized_prompt
        return self._response(
            original_prompt=original_prompt,
            analysis=analysis,
            provider_name=selection.name,
            provider=provider,
            selected_model=None if fallback_used else selection.model,
            selection_scope=selection.scope,
            provider_health=(
                "fallback" if selection.health != "healthy" or fallback_used else "healthy"
            ),
            provider_used=provider_response.provider_used,
            fallback_used=fallback_used,
            latency_ms=provider_response.latency_ms,
            error_summary=error_summary,
            error_code=error_code,
            error_category=error_category,
            provider_request_id=provider_request_id,
            fallback_chain=selection.fallback_chain,
            estimate=estimate,
            max_tokens=max_tokens,
            max_cost=max_cost,
            fallback_reason=fallback_reason,
            recovery_action=recovery_action,
            owner_id=owner_id,
            project_id=project_id,
            save_prompt_history=save_prompt_history,
            quality_score_before=quality_score_before,
        )

    def execution_destination(
        self,
        *,
        provider_name: str,
        model: str | None = None,
        optimizer_provider: str | None = None,
        optimizer_model: str | None = None,
        strategy: OptimizationStrategy = "combined",
    ) -> ExecutionDestination:
        selection = self._resolve_selection(
            provider_name="offline" if strategy == "rules" else provider_name,
            model=model,
            optimizer_provider=optimizer_provider,
            optimizer_model=optimizer_model,
        )
        return execution_destination(selection.provider, selection.name, selection.model)

    def stream(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        targets: OptimizationTargets | None = None,
        strategy: OptimizationStrategy = "combined",
        provider_name: str = "offline",
        model: str | None = None,
        optimizer_provider: str | None = None,
        optimizer_model: str | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
        request_id: str | None = None,
        max_tokens: int | None = None,
        max_cost: float | None = None,
    ) -> Iterator[OptimizationStreamEvent]:
        stream_id = request_id or uuid4().hex
        cancellation = Event()
        with self._cancellation_lock:
            self._cancellations[stream_id] = cancellation
        try:
            structure, language_profile, request = self._protected_request(
                prompt,
                template,
                targets=targets,
                strategy=strategy,
                request_id=stream_id,
                cancel_event=cancellation,
            )
            yield OptimizationStreamEvent("analysis", self.analyzer.analyze(prompt))
            started = perf_counter()
            streamed_chunks: list[str] = []
            first_token_recorded = False
            selection = self._resolve_selection(
                provider_name="offline" if strategy == "rules" else provider_name,
                model=model,
                optimizer_provider=optimizer_provider,
                optimizer_model=optimizer_model,
            )
            provider_used = selection.name
            provider_display_name = selection.name
            selected_model = selection.model
            selected_scope = selection.scope
            selected_health = selection.health
            estimate = estimate_request(request, selection.provider)
            enforce_budget(estimate, max_tokens=max_tokens, max_cost=max_cost)
            execution_location: Literal["local", "cloud"] = "local"
            credential_ref: str | None = None
            try:
                provider = selection.provider
                provider_used = provider.name
                (
                    provider_display_name,
                    provider_model,
                    execution_location,
                    credential_ref,
                ) = provider_public_metadata(
                    provider,
                    provider_used,
                )
                selected_model = selected_model or provider_model
                for event in provider.stream(request):
                    if cancellation.is_set():
                        return
                    if event.type is ProviderEventType.DELTA and event.text:
                        if not first_token_recorded:
                            self.metrics.record_first_token(
                                int((perf_counter() - started) * 1000)
                            )
                            first_token_recorded = True
                        streamed_chunks.append(event.text)
            except (ModelProviderError, RuntimeError, ValueError) as exc:
                self.metrics.record_request(
                    provider=selection.name,
                    latency_ms=int((perf_counter() - started) * 1000),
                    success=False,
                )
                if selection.name == "offline" or not _fallback_allowed(selection.name, exc):
                    raise
                error_summary = sanitize_error_message(exc)
                error_code = error_code_for(exc)
                fallback_reason, recovery_action = fallback_details_for(exc)
                fallback_provider = self.providers.get("offline")
                fallback_response = fallback_provider.optimize(request)
                (
                    provider_display_name,
                    selected_model,
                    execution_location,
                    credential_ref,
                ) = provider_public_metadata(
                    fallback_provider,
                    fallback_response.provider_used,
                )
                fallback_prompt = self._validate_output(
                    fallback_response.analysis.optimized_prompt or request.prompt,
                    structure=structure,
                    language_profile=language_profile,
                    targets=targets,
                )
                self.metrics.record_request(
                    provider=fallback_response.provider_used,
                    latency_ms=fallback_response.latency_ms,
                    success=True,
                    input_tokens=_usage_int(
                        fallback_response.usage or {},
                        "prompt_tokens",
                        "input_tokens",
                    ),
                    output_tokens=_usage_int(
                        fallback_response.usage or {},
                        "completion_tokens",
                        "output_tokens",
                    ),
                )
                fallback = self.save_optimized_text(
                    original_prompt=original_prompt,
                    prompt=prompt,
                    optimized_prompt=fallback_prompt,
                    targets=targets,
                    provider_requested=selection.name,
                    provider_used=fallback_response.provider_used,
                    fallback_used=True,
                    latency_ms=fallback_response.latency_ms,
                    error_summary=error_summary,
                    provider_display_name=provider_display_name,
                    model=selected_model,
                    execution_location=execution_location,
                    credential_ref=credential_ref,
                    error_code=error_code,
                    error_category=error_category_for(exc),
                    provider_request_id=getattr(exc, "request_id", None),
                    fallback_chain=selection.fallback_chain,
                    estimate=estimate,
                    max_tokens=max_tokens,
                    max_cost=max_cost,
                    fallback_reason=fallback_reason,
                    recovery_action=recovery_action,
                    owner_id=owner_id,
                    project_id=project_id,
                    save_prompt_history=save_prompt_history,
                    selection_scope=selected_scope,
                    provider_health="fallback",
                )
                yield OptimizationStreamEvent("fallback", fallback.metadata)
                for chunk in _chunks(fallback.analysis.optimized_prompt or ""):
                    if cancellation.is_set():
                        return
                    yield OptimizationStreamEvent("chunk", chunk)
                yield OptimizationStreamEvent("completed", fallback)
                return
            if cancellation.is_set():
                return
            optimized_prompt = self._validate_output(
                "".join(streamed_chunks),
                structure=structure,
                language_profile=language_profile,
                targets=targets,
            )
            result = self.save_optimized_text(
                original_prompt=original_prompt,
                prompt=prompt,
                optimized_prompt=optimized_prompt,
                targets=targets,
                provider_requested=selection.name,
                provider_used=provider_used,
                fallback_used=False,
                latency_ms=int((perf_counter() - started) * 1000),
                error_summary=None,
                provider_display_name=provider_display_name,
                model=selected_model,
                execution_location=execution_location,
                credential_ref=credential_ref,
                owner_id=owner_id,
                project_id=project_id,
                save_prompt_history=save_prompt_history,
                selection_scope=selected_scope,
                provider_health=selected_health,
                fallback_chain=selection.fallback_chain,
                estimate=estimate,
                max_tokens=max_tokens,
                max_cost=max_cost,
            )
            self.metrics.record_request(
                provider=selection.name,
                latency_ms=int((perf_counter() - started) * 1000),
                success=True,
            )
            chunks = streamed_chunks if not structure.segments else list(_chunks(optimized_prompt))
            for chunk in chunks:
                if cancellation.is_set():
                    return
                yield OptimizationStreamEvent("chunk", chunk)
            yield OptimizationStreamEvent("completed", result)
        finally:
            with self._cancellation_lock:
                self._cancellations.pop(stream_id, None)

    def cancel(self, request_id: str) -> bool:
        with self._cancellation_lock:
            cancellation = self._cancellations.get(request_id)
        if cancellation is None:
            return False
        cancellation.set()
        return True

    def save_optimized_text(
        self,
        *,
        original_prompt: str,
        prompt: str,
        optimized_prompt: str,
        targets: OptimizationTargets | None = None,
        provider_requested: str,
        provider_used: str,
        fallback_used: bool,
        latency_ms: int,
        error_summary: str | None,
        provider_display_name: str | None = None,
        model: str | None = None,
        execution_location: Literal["local", "cloud"] = "local",
        credential_ref: str | None = None,
        error_code: str | None = None,
        error_category: str | None = None,
        provider_request_id: str | None = None,
        fallback_chain: tuple[str, ...] = (),
        estimate: BudgetEstimate | None = None,
        max_tokens: int | None = None,
        max_cost: float | None = None,
        fallback_reason: FallbackReason | None = None,
        recovery_action: RecoveryAction | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
        selection_scope: ProviderSelectionScope = "default",
        provider_health: Literal["healthy", "unavailable", "fallback"] = "healthy",
    ) -> OptimizeResponse:
        structure, language_profile, _request = self._protected_request(
            prompt,
            None,
            targets=targets,
        )
        optimized_prompt = self._validate_output(
            optimized_prompt,
            structure=structure,
            language_profile=language_profile,
            targets=targets,
        )
        analysis = self.analyzer.analyze(optimized_prompt)
        analysis.optimized_prompt = optimized_prompt
        quality_score_before = self.analyzer.analyze(prompt).score.total_score
        version_id = None
        if owner_id is not None and save_prompt_history:
            version_id = self.versions.create(
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt or prompt,
                analysis=analysis,
                owner_id=owner_id,
                project_id=project_id,
                provider_used=provider_used,
                model=model,
                selection_scope=selection_scope,
                provider_health=provider_health,
            )
        return OptimizeResponse(
            version_id=version_id,
            analysis=analysis,
            metadata=OptimizeMetadata(
                provider_requested=provider_requested,
                provider_used=provider_used,
                provider_display_name=provider_display_name or provider_used,
                system_prompt_version=SYSTEM_PROMPT_VERSION,
                model=model,
                execution_location=execution_location,
                destination=declared_execution_destination(
                    provider_used,
                    provider_display_name or provider_used,
                    model,
                    execution_location,
                ),
                credential_ref=credential_ref,
                fallback_used=fallback_used,
                latency_ms=latency_ms,
                error_summary=error_summary,
                error_code=error_code,
                error_category=error_category,
                provider_request_id=provider_request_id,
                fallback_chain=list(fallback_chain),
                estimated_input_tokens=estimate.input_tokens if estimate else None,
                estimated_output_tokens=estimate.output_tokens if estimate else None,
                estimated_cost=estimate.cost if estimate else None,
                budget_limit_tokens=max_tokens,
                budget_limit_cost=max_cost,
                fallback_reason=fallback_reason,
                recovery_action=recovery_action,
                selection_scope=selection_scope,
                provider_health=provider_health,
                quality_score_before=quality_score_before,
                quality_score_after=analysis.score.total_score,
                quality_score_delta=round(
                    analysis.score.total_score - quality_score_before,
                    2,
                ),
            ),
        )

    def _protected_request(
        self,
        prompt: str,
        template: PromptTemplate | None,
        targets: OptimizationTargets | None = None,
        strategy: OptimizationStrategy = "combined",
        request_id: str | None = None,
        cancel_event: Event | None = None,
    ) -> tuple[StructuredPrompt, LanguageProfile, ModelRequest]:
        if targets is not None and not targets.has_enabled_target():
            raise ValueError("至少选择一项优化目标。")
        rule_analysis = self.analyzer.analyze(prompt)
        structure = StructuredPrompt.parse(prompt)
        language_profile = LanguageProfile.detect(structure.language_text())
        protected_prompt = structure.protect()
        return (
            structure,
            language_profile,
            ModelRequest(
                prompt=protected_prompt,
                protected_structure=structure,
                template=template,
                targets=targets,
                strategy=strategy,
                rule_suggestions=(
                    tuple(rule_analysis.suggestions) if strategy == "combined" else ()
                ),
                language_profile=language_profile,
                language_instruction=language_profile.instruction,
                request_id=request_id,
                cancel_event=cancel_event,
                system_prompt=SYSTEM_PROMPT,
                system_prompt_version=SYSTEM_PROMPT_VERSION,
            ),
        )

    def _validate_output(
        self,
        output: str,
        *,
        structure: StructuredPrompt,
        language_profile: LanguageProfile,
        targets: OptimizationTargets | None,
    ) -> str:
        return self.output_validator.validate(
            output,
            structure=structure,
            language_profile=language_profile,
            preserve_language=targets is None or targets.language_preservation,
        )

    def _response(
        self,
        *,
        original_prompt: str,
        analysis: PromptAnalysis,
        provider_name: str,
        provider: object,
        provider_used: str,
        selected_model: str | None,
        selection_scope: ProviderSelectionScope,
        provider_health: Literal["healthy", "unavailable", "fallback"],
        fallback_used: bool,
        latency_ms: int,
        error_summary: str | None,
        error_code: str | None,
        error_category: str | None,
        provider_request_id: str | None,
        fallback_chain: tuple[str, ...],
        estimate: BudgetEstimate | None,
        max_tokens: int | None,
        max_cost: float | None,
        fallback_reason: FallbackReason | None,
        recovery_action: RecoveryAction | None,
        owner_id: int | None,
        project_id: int | None,
        save_prompt_history: bool,
        quality_score_before: float,
    ) -> OptimizeResponse:
        (
            provider_display_name,
            provider_model,
            execution_location,
            credential_ref,
        ) = provider_public_metadata(
            provider,
            provider_used,
        )
        model = selected_model or provider_model
        version_id = None
        if owner_id is not None and save_prompt_history:
            version_id = self.versions.create(
                original_prompt=original_prompt,
                optimized_prompt=analysis.optimized_prompt or "",
                analysis=analysis,
                owner_id=owner_id,
                project_id=project_id,
                provider_used=provider_used,
                model=model,
                selection_scope=selection_scope,
                provider_health=provider_health,
            )
        return OptimizeResponse(
            version_id=version_id,
            analysis=analysis,
            metadata=OptimizeMetadata(
                provider_requested=provider_name,
                provider_used=provider_used,
                provider_display_name=provider_display_name,
                system_prompt_version=SYSTEM_PROMPT_VERSION,
                model=model,
                execution_location=execution_location,
                destination=execution_destination(provider, provider_used, model),
                credential_ref=credential_ref,
                fallback_used=fallback_used,
                latency_ms=latency_ms,
                error_summary=error_summary,
                error_code=error_code,
                error_category=error_category,
                provider_request_id=provider_request_id,
                fallback_chain=list(fallback_chain),
                estimated_input_tokens=estimate.input_tokens if estimate else None,
                estimated_output_tokens=estimate.output_tokens if estimate else None,
                estimated_cost=estimate.cost if estimate else None,
                budget_limit_tokens=max_tokens,
                budget_limit_cost=max_cost,
                fallback_reason=fallback_reason,
                recovery_action=recovery_action,
                selection_scope=selection_scope,
                provider_health=provider_health,
                quality_score_before=quality_score_before,
                quality_score_after=analysis.score.total_score,
                quality_score_delta=round(
                    analysis.score.total_score - quality_score_before,
                    2,
                ),
            ),
        )

    def _resolve_selection(
        self,
        *,
        provider_name: str,
        model: str | None,
        optimizer_provider: str | None,
        optimizer_model: str | None,
    ) -> ProviderSelection:
        if isinstance(self.providers, ProviderRegistry):
            session_provider = (
                None if provider_name == "offline" and model is None else provider_name
            )
            return self.providers.resolve(
                session_provider=session_provider,
                session_model=model,
                optimizer_provider=optimizer_provider,
                optimizer_model=optimizer_model,
            )
        provider = self.providers.get(provider_name)
        return ProviderSelection(
            name=provider_name,
            model=model or getattr(provider, "model", None),
            scope="session" if provider_name != "offline" else "default",
            health="healthy",
            provider=provider,
        )


def _chunks(text: str, size: int = 120) -> Iterator[str]:
    if not text:
        return
    for start in range(0, len(text), size):
        yield text[start : start + size]


def _usage_int(usage: dict[str, int], *keys: str) -> int | None:
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    return None


class AppServices:
    def __init__(
        self,
        *,
        analyzer: Analyzer | None = None,
        optimizer: PromptOptimizer | None = None,
        templates: TemplateManager | None = None,
        versions: VersionService | None = None,
        export: ExportService | None = None,
        providers: ProviderCatalog | None = None,
        auth: AuthService | None = None,
        tasks: TaskService | None = None,
        config: ConfigService | None = None,
        cleanup: LocalDataCleanupService | None = None,
        retention: RetentionService | None = None,
        metrics: LocalMetricsAggregator | None = None,
    ) -> None:
        self.analyzer = analyzer or Analyzer()
        self.optimizer = optimizer or Optimizer(self.analyzer)
        self.templates = templates or TemplateManager()
        self.versions = versions or VersionService()
        self.export = export or ExportService()
        self.providers = providers or ProviderRegistry(self.optimizer)
        self.auth = auth or AuthService()
        self.tasks = tasks or TaskService(self.versions.storage)
        self.config = config or ConfigService()
        storage = self.versions.storage
        cleanup_paths = tuple(
            path
            for path in (
                getattr(storage, "db_path", None),
                getattr(storage, "backup_dir", None),
                getattr(getattr(storage, "file_store", None), "root", None),
                self.config.user_path,
            )
            if isinstance(path, Path)
        )
        self.cleanup = cleanup or LocalDataCleanupService(
            secret_store=self.config.secret_store,
            paths=cleanup_paths or (app_data_dir(),),
            config_paths=(self.config.user_path,),
        )
        self.retention = retention or RetentionService(cast(StorageService, storage))
        self.metrics = metrics or LocalMetricsAggregator()
        self._optimization = PromptOptimizationService(
            analyzer=self.analyzer,
            optimizer=self.optimizer,
            providers=self.providers,
            versions=self.versions,
            metrics=self.metrics,
        )

    @property
    def optimization(self) -> PromptOptimizationService:
        self._optimization.analyzer = self.analyzer
        self._optimization.optimizer = self.optimizer
        self._optimization.providers = self.providers
        self._optimization.versions = self.versions
        self._optimization.metrics = self.metrics
        return self._optimization

    def register_user(self, username: str, password: str) -> AuthResponse:
        user = self.versions.storage.create_user(username, self.auth.hash_password(password))
        return AuthResponse(access_token=self.auth.create_token(user), user=user)

    def login_user(self, username: str, password: str) -> AuthResponse:
        found = self.versions.storage.get_user_by_username(username)
        if found is None:
            raise AuthError("用户名或密码错误。")
        user, password_hash = found
        if not self.auth.verify_password(password, password_hash):
            raise AuthError("用户名或密码错误。")
        return AuthResponse(access_token=self.auth.create_token(user), user=user)

    def get_user_from_token(self, token: str | None) -> UserPublic:
        user = self.get_optional_user_from_token(token)
        if user is None:
            raise AuthError("需要登录。")
        return user

    def get_optional_user_from_token(self, token: str | None) -> UserPublic | None:
        if not token:
            return None
        if not token.startswith("Bearer "):
            raise AuthError("无效 token。")
        token_value = token.removeprefix("Bearer ").strip()
        try:
            return self.versions.storage.get_user(self.auth.read_token(token_value))
        except KeyError as exc:
            raise AuthError("用户不存在。") from exc

    def optimize_and_save(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        targets: OptimizationTargets | None = None,
        strategy: OptimizationStrategy = "combined",
        provider_name: str = "offline",
        model: str | None = None,
        optimizer_provider: str | None = None,
        optimizer_model: str | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
        max_tokens: int | None = None,
        max_cost: float | None = None,
    ) -> OptimizeResponse:
        return self.optimization.optimize(
            original_prompt=original_prompt,
            prompt=prompt,
            template=template,
            targets=targets,
            strategy=strategy,
            provider_name=provider_name,
            model=model,
            optimizer_provider=optimizer_provider,
            optimizer_model=optimizer_model,
            owner_id=owner_id,
            project_id=project_id,
            save_prompt_history=save_prompt_history,
            max_tokens=max_tokens,
            max_cost=max_cost,
        )

    def save_optimized_text(
        self,
        *,
        original_prompt: str,
        prompt: str,
        optimized_prompt: str,
        targets: OptimizationTargets | None = None,
        provider_requested: str,
        provider_used: str,
        fallback_used: bool,
        latency_ms: int,
        error_summary: str | None,
        provider_display_name: str | None = None,
        model: str | None = None,
        execution_location: Literal["local", "cloud"] = "local",
        credential_ref: str | None = None,
        error_code: str | None = None,
        fallback_reason: FallbackReason | None = None,
        recovery_action: RecoveryAction | None = None,
        owner_id: int | None = 1,
        project_id: int | None = None,
        save_prompt_history: bool = True,
    ) -> OptimizeResponse:
        return self.optimization.save_optimized_text(
            original_prompt=original_prompt,
            prompt=prompt,
            optimized_prompt=optimized_prompt,
            targets=targets,
            provider_requested=provider_requested,
            provider_used=provider_used,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            error_summary=error_summary,
            provider_display_name=provider_display_name,
            model=model,
            execution_location=execution_location,
            credential_ref=credential_ref,
            error_code=error_code,
            fallback_reason=fallback_reason,
            recovery_action=recovery_action,
            owner_id=owner_id,
            project_id=project_id,
            save_prompt_history=save_prompt_history,
        )
