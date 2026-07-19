from __future__ import annotations

from prompt_optimizer.core.models import OptimizationSuggestion
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    OpenAICompatibleAdapter,
    ProviderCapabilities,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.templates.manager import TemplateManager

# RC ID: RC-155. Compare rules, model, and combined optimization without real API calls.

COMBINED_MIN_SCORE_DELTA = 0.0
SEMANTIC_PRESERVATION_MIN = 1.0


class CapturingModelProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        analysis = Optimizer().optimize(
            request.prompt,
            request.template,
            request.language_profile,
            request.targets,
        )
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest):
        yield from ()


def _services(provider: CapturingModelProvider) -> AppServices:
    services = AppServices()
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": provider},
    )
    return services


def test_combined_strategy_preserves_template_and_rule_gaps() -> None:
    provider = CapturingModelProvider()
    template = TemplateManager().get("tech-code-generation")

    _services(provider).optimization.optimize(
        original_prompt="Write a Python command-line parser",
        prompt="Write a Python command-line parser",
        template=template,
        provider_name="openai",
        strategy="combined",
        owner_id=None,
    )

    assert len(provider.requests) == 1
    request = provider.requests[0]
    assert request.template == template
    assert request.rule_suggestions
    assert request.strategy == "combined"
    assert "Write a Python command-line parser" not in request.system_prompt


def test_rules_strategy_uses_offline_rules_without_calling_the_model() -> None:
    provider = CapturingModelProvider()

    result = _services(provider).optimization.optimize(
        original_prompt="Draft a release note",
        prompt="Draft a release note",
        template=None,
        provider_name="openai",
        strategy="rules",
        owner_id=None,
    )

    assert not provider.requests
    assert result.metadata.provider_used == "offline"
    assert "Draft a release note" in (result.analysis.optimized_prompt or "")


def test_combined_ablation_meets_quality_and_semantic_thresholds() -> None:
    source = "Draft a release note for a fixed bug."
    provider = CapturingModelProvider()
    services = _services(provider)

    model = services.optimization.optimize(
        original_prompt=source,
        prompt=source,
        template=None,
        provider_name="openai",
        strategy="model",
        owner_id=None,
    )
    combined = services.optimization.optimize(
        original_prompt=source,
        prompt=source,
        template=None,
        provider_name="openai",
        strategy="combined",
        owner_id=None,
    )

    combined_prompt = combined.analysis.optimized_prompt or ""
    semantic_preservation = float(source in combined_prompt)
    assert (
        combined.analysis.score.total_score - model.analysis.score.total_score
        >= COMBINED_MIN_SCORE_DELTA
    )
    assert semantic_preservation >= SEMANTIC_PRESERVATION_MIN
    assert not provider.requests[0].rule_suggestions
    assert provider.requests[1].rule_suggestions


def test_cloud_adapter_places_rule_guidance_in_user_context() -> None:
    suggestion = OptimizationSuggestion(
        dimension="constraints",
        title="Add constraints",
        detail="State the limits already present in the prompt.",
        example="Do not add unsupported requirements.",
        priority="high",
    )
    request = ModelRequest(
        prompt="Write a changelog entry",
        strategy="combined",
        rule_suggestions=(suggestion,),
    )

    user_context = OpenAICompatibleAdapter._build_prompt(request)

    assert "Rule-derived optimization gaps" in user_context
    assert "do not invent facts" in user_context
    assert suggestion.detail in user_context
