from __future__ import annotations

from pathlib import Path

import pytest

from prompt_optimizer.core.analyzer import MAX_PROMPT_LENGTH
from prompt_optimizer.core.language import LanguageProfile
from prompt_optimizer.core.output_validation import OutputValidationError, OutputValidator
from prompt_optimizer.core.structure import StructuredPrompt
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-156. Cover control filtering, output limits, and safe non-adoption.


class InvalidOutputProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        analysis = AppServices().analyzer.analyze(request.prompt)
        analysis.optimized_prompt = "The model omitted the protected code block."
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest):
        yield from ()


def test_validator_filters_controls_and_keeps_valid_output() -> None:
    source = "Write a short release note."
    structure = StructuredPrompt.parse(source)

    validated = OutputValidator().validate(
        "Write a short" + chr(0) + " release note.",
        structure=structure,
        language_profile=LanguageProfile.detect(source),
        preserve_language=True,
    )

    assert chr(0) not in validated
    assert validated == "Write a short release note."


def test_validator_rejects_an_overlong_output() -> None:
    source = "Write a short release note."

    with pytest.raises(OutputValidationError, match="长度"):
        OutputValidator().validate(
            "a" * (MAX_PROMPT_LENGTH + 1),
            structure=StructuredPrompt.parse(source),
            language_profile=LanguageProfile.detect(source),
            preserve_language=True,
        )


def test_invalid_structured_output_is_not_saved(tmp_path: Path) -> None:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc156.sqlite3"))
    invalid_provider = InvalidOutputProvider()
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": invalid_provider},
    )
    source = "\u0060\u0060\u0060python\nprint('release')\n\u0060\u0060\u0060"

    with pytest.raises(OutputValidationError, match="结果未采用"):
        services.optimization.optimize(
            original_prompt=source,
            prompt=source,
            template=None,
            provider_name="openai",
        )

    assert services.versions.list(1) == []
