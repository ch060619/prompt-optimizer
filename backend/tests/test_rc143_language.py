from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.language import LanguagePreservationError, LanguageProfile
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.core.structure import StructuredPrompt
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    OpenAICompatibleAdapter,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


class EchoProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self, output: str | None = None) -> None:
        self.output = output
        self.request: ModelRequest | None = None

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self.request = request
        output = self.output or request.prompt
        analysis = Analyzer().analyze(output)
        analysis.optimized_prompt = output
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest):
        response = self.optimize(request)
        yield from ()
        return response


def _services(tmp_path: Path, provider: EchoProvider) -> AppServices:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc143.sqlite3"))
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": provider},
    )
    return services


def test_language_profile_detects_chinese_english_and_mixed_ratio() -> None:
    chinese = LanguageProfile.detect("请优化这段中文提示词")
    english = LanguageProfile.detect("Write a concise API summary")
    mixed = LanguageProfile.detect("请总结这段 API response")

    assert chinese.primary == "zh"
    assert english.primary == "en"
    assert mixed.primary == "mixed"
    assert mixed.chinese_share > 0
    assert mixed.latin_share > 0


def test_translation_intent_overrides_language_preservation() -> None:
    profile = LanguageProfile.detect("Translate this prompt into Chinese")

    profile.validate("请把这段内容翻译成中文")

    assert profile.translation_requested is True


def test_negated_translation_does_not_override_language_preservation() -> None:
    profile = LanguageProfile.detect("Please do not translate this English prompt")

    with pytest.raises(LanguagePreservationError):
        profile.validate("请把这段内容翻译成中文")


def test_offline_optimizer_uses_english_scaffolding_for_english_input() -> None:
    result = Optimizer().optimize("Write a concise API summary")
    optimized = result.optimized_prompt or ""

    assert "Goal:" in optimized
    assert "输出要求" not in optimized


def test_language_profile_ignores_code_when_validating_content_language() -> None:
    structure = StructuredPrompt.parse("请说明这个接口\n```python\nprint('English only code')\n```")
    profile = LanguageProfile.detect(structure.language_text())

    profile.validate(
        StructuredPrompt.parse(
            "请说明这个接口的作用。\n```python\nprint('English only code')\n```",
        ).language_text()
    )


def test_service_sends_language_instruction_with_request(tmp_path: Path) -> None:
    provider = EchoProvider()
    result = _services(tmp_path, provider).optimize_and_save(
        original_prompt="Write a concise API summary",
        prompt="Write a concise API summary",
        template=None,
        provider_name="openai",
        owner_id=None,
    )

    assert result.analysis.optimized_prompt == "Write a concise API summary"
    assert provider.request is not None
    assert provider.request.language_profile is not None
    assert provider.request.language_profile.primary == "en"
    assert "Preserve the user's English" in (provider.request.language_instruction or "")


def test_service_rejects_language_changed_output(tmp_path: Path) -> None:
    with pytest.raises(LanguagePreservationError, match="结果未采用"):
        _services(tmp_path, EchoProvider("请写一封邮件")).optimize_and_save(
            original_prompt="Write a concise API summary",
            prompt="Write a concise API summary",
            template=None,
            provider_name="openai",
            owner_id=None,
        )


def test_openai_request_includes_language_instruction() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read().decode("utf-8")
        assert "Preserve the user's English" in payload
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Write a concise API summary"}}]},
        )

    provider = OpenAICompatibleAdapter(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    provider.optimize(
        ModelRequest(
            prompt="Write a concise API summary",
            language_instruction="Preserve the user's English.",
        )
    )
