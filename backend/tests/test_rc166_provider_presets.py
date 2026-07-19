from __future__ import annotations

import httpx
import pytest

from prompt_optimizer.providers import ModelRequest, ProviderConfig, ProviderRegistry, get_preset
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-166. Verify every listed OpenAI-compatible preset produces a request.

PRESET_NAMES = (
    "openrouter",
    "deepseek",
    "moonshot",
    "qwen",
    "doubao",
    "zhipu",
    "siliconflow",
    "groq",
    "together",
    "ollama",
    "lmstudio",
)


@pytest.mark.parametrize("provider_name", PRESET_NAMES)
def test_preset_has_default_endpoint_discovery_and_limitations(provider_name: str) -> None:
    preset = get_preset(provider_name)
    assert preset is not None
    assert preset.base_url.startswith(("http://", "https://"))
    assert preset.model_discovery_path == "/models"
    assert preset.compatibility in {"medium", "high"}
    assert preset.limitations


@pytest.mark.parametrize("provider_name", PRESET_NAMES)
def test_preset_generates_openai_compatible_chat_request(provider_name: str) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "目标：兼容请求。"}}]},
        )

    preset = get_preset(provider_name)
    assert preset is not None
    provider = OpenAICompatibleAdapter(
        ProviderConfig(
            name=provider_name,
            base_url=preset.base_url,
            api_key="preset-key",
            model="preset-model",
            custom_headers=(("X-Preset-Test", "enabled"),),
            max_retries=0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.optimize(ModelRequest(prompt=f"测试 {provider_name}"))

    assert result.analysis.optimized_prompt == "目标：兼容请求。"
    assert calls[0].headers["X-Preset-Test"] == "enabled"
    assert calls[0].url.path.endswith("/chat/completions")


def test_registry_uses_preset_base_url_and_custom_headers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RABBIT_CODE_OPENROUTER_API_KEY", "router-key")
    monkeypatch.setenv("RABBIT_CODE_OPENROUTER_MODEL", "router-model")
    monkeypatch.setenv(
        "RABBIT_CODE_OPENROUTER_HEADERS_JSON",
        '{"HTTP-Referer":"https://rabbit.example","X-Title":"Rabbit Code"}',
    )

    provider = ProviderRegistry().get("openrouter")

    assert isinstance(provider, OpenAICompatibleAdapter)
    assert provider.config.base_url == "https://openrouter.ai/api/v1"  # type: ignore[attr-defined]
    assert dict(provider.config.custom_headers) == {  # type: ignore[attr-defined]
        "HTTP-Referer": "https://rabbit.example",
        "X-Title": "Rabbit Code",
    }
