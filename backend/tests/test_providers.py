from __future__ import annotations

import httpx

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import ModelRequest, ProviderConfig, ProviderRateLimitError
from prompt_optimizer.providers.http import HttpChatProvider
from prompt_optimizer.providers.offline import OfflineRuleProvider


def test_offline_provider_uses_rule_optimizer() -> None:
    response = OfflineRuleProvider().optimize(ModelRequest(prompt="帮我写一封邮件"))

    assert response.provider_used == "offline"
    assert response.analysis.optimized_prompt is not None
    assert response.latency_ms >= 0


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

    provider = HttpChatProvider(
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

    provider = HttpChatProvider(
        ProviderConfig(
            name="openai",
            base_url="https://example.test/chat",
            api_key="test-key",
            model="demo",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert list(provider.stream(ModelRequest(prompt="写报告"))) == ["优化", "提示词"]
