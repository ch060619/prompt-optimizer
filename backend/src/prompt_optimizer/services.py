from __future__ import annotations

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.models import OptimizeMetadata, OptimizeResponse, PromptTemplate
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.providers import ModelProviderError, ModelRequest, ProviderRegistry
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.templates.manager import TemplateManager


class AppServices:
    def __init__(self) -> None:
        self.analyzer = Analyzer()
        self.optimizer = Optimizer(self.analyzer)
        self.templates = TemplateManager()
        self.versions = VersionService()
        self.export = ExportService()
        self.providers = ProviderRegistry(self.optimizer)

    def optimize_and_save(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        provider_name: str = "offline",
    ) -> OptimizeResponse:
        request = ModelRequest(prompt=prompt, template=template)
        fallback_used = False
        error_summary: str | None = None
        try:
            provider_response = self.providers.get(provider_name).optimize(request)
        except (ModelProviderError, RuntimeError, ValueError) as exc:
            if provider_name == "offline":
                raise
            fallback_used = True
            error_summary = str(exc)
            provider_response = self.providers.get("offline").optimize(request)
        analysis = provider_response.analysis
        version_id = self.versions.create(
            original_prompt=original_prompt,
            optimized_prompt=analysis.optimized_prompt or prompt,
            analysis=analysis,
        )
        metadata = OptimizeMetadata(
            provider_requested=provider_name,
            provider_used=provider_response.provider_used,
            fallback_used=fallback_used,
            latency_ms=provider_response.latency_ms,
            error_summary=error_summary,
        )
        return OptimizeResponse(version_id=version_id, analysis=analysis, metadata=metadata)
