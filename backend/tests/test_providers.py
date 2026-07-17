from __future__ import annotations

import httpx

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelProvider,
    ModelRequest,
    ProviderConfig,
    ProviderEventType,
    ProviderRateLimitError,
)
from prompt_optimizer.providers.http import HttpChatProvider
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.providers.registry import ProviderRegistry

# RC ID: RC-049. Verify the shared Provider contract with deterministic Mock transports.


def test_offline_provider_uses_rule_optimizer() -> None:
    provider = OfflineRuleProvider()
    response = provider.optimize(ModelRequest(prompt="帮我写一封邮件"))

    assert response.provider_used == "offline"
    assert response.analysis.optimized_prompt is not None
    assert response.latency_ms >= 0
    assert isinstance(provider, ModelProvider)
    assert provider.capabilities.text is True
    assert provider.capabilities.streaming is True


def test_offline_provider_uses_unified_stream_events() -> None:
    events = list(OfflineRuleProvider().stream(ModelRequest(prompt="写一份报告")))

    assert events[0].type is ProviderEventType.STARTED
    assert events[-1].type is ProviderEventType.COMPLETED
    assert all(event.type is ProviderEventType.DELTA for event in events[1:-1])
    assert "".join(event.text or "" for event in events[1:-1])


def test_http_provider_parses_chat_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "你是一名资深工程师。目标：生成接口设计。"
                                "背景：用于面试项目。输出格式：Markdown 列表。"
                                "限制：说明假设，并给出测试步骤。"
                            )
                        }
                    }
                ]
            },
        )

    provider = OpenAICompatibleAdapter(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
        ),
        analyzer=Analyzer(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = provider.optimize(ModelRequest(prompt="设计一个 API"))

    assert response.provider_used == "openai"
    assert response.analysis.optimized_prompt is not None
    assert response.analysis.score.total_score > 0


def test_openai_compatible_adapter_does_not_guess_other_response_protocols() -> None:
    provider = OpenAICompatibleAdapter(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
        ),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"output": "other protocol"})
            )
        ),
    )

    try:
        provider.optimize(ModelRequest(prompt="写报告"))
    except RuntimeError as exc:
        assert "无法解析模型响应" in str(exc)
    else:
        raise AssertionError("non-OpenAI response should be rejected")


def test_http_provider_retries_timeout_then_succeeds() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.TimeoutException("timeout", request=request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "目标：写报告。输出格式：列表。限制：简洁。"}}
                ]
            },
        )

    provider = HttpChatProvider(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
            max_retries=1,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = provider.optimize(ModelRequest(prompt="写报告"))

    assert calls == 2
    assert response.provider_used == "openai"


def test_http_provider_rate_limit() -> None:
    provider = HttpChatProvider(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
            rate_limit_per_minute=1,
        ),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "目标：写报告。输出格式：列表。"}}]},
                )
            )
        ),
    )

    provider.optimize(ModelRequest(prompt="写报告"))

    try:
        provider.optimize(ModelRequest(prompt="再写一次"))
    except ProviderRateLimitError as exc:
        assert "限流" in str(exc)
    else:
        raise AssertionError("rate limit should fail")


def test_http_provider_streams_chat_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=(
                'data: {"choices":[{"delta":{"content":"优化"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"提示词"}}]}\n\n'
                "data: [DONE]\n\n"
            ),
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

    events = list(provider.stream(ModelRequest(prompt="写报告")))

    assert [event.type for event in events] == [
        ProviderEventType.STARTED,
        ProviderEventType.DELTA,
        ProviderEventType.DELTA,
        ProviderEventType.COMPLETED,
    ]
    assert [event.text for event in events[1:-1]] == ["优化", "提示词"]


def test_http_provider_compatibility_alias_points_to_explicit_adapter() -> None:
    assert HttpChatProvider is OpenAICompatibleAdapter


def test_registry_returns_explicit_openai_compatible_adapter() -> None:
    provider = ProviderRegistry().get("openai")

    assert isinstance(provider, OpenAICompatibleAdapter)
    assert provider.capabilities.streaming is True
    provider.client.close()
