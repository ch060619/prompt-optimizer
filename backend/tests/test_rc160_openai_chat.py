from __future__ import annotations

import httpx
import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ProviderConfig,
    ProviderEventType,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnauthorizedError,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-160. Verify OpenAI Chat Completions request, stream, tools, and error contracts.


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="openai",
        base_url="https://api.openai.test/v1",
        api_key="test-key",
        model="gpt-test",
        organization="org-test",
        project="proj-test",
        max_retries=0,
    )


def _tool() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "lookup_release",
            "description": "Look up a release by version.",
            "parameters": {
                "type": "object",
                "properties": {"version": {"type": "string"}},
                "required": ["version"],
            },
        },
    }


def test_chat_completions_builds_standard_endpoint_headers_and_tools() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.openai.test/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["OpenAI-Organization"] == "org-test"
        assert request.headers["OpenAI-Project"] == "proj-test"
        payload = request.read()
        assert b"test-key" not in payload
        body = httpx.Response(200, content=payload).json()
        assert body["model"] == "gpt-test"
        assert body["messages"][0]["role"] == "system"
        assert body["tools"] == [_tool()]
        assert body["tool_choice"] == "auto"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "目标：输出版本信息。格式：列表。",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "lookup_release",
                                        "arguments": '{"version":"3.0"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = provider.optimize(
        ModelRequest(
            prompt="整理版本信息",
            tools=(_tool(),),
            tool_choice="auto",
        )
    )

    assert response.tool_calls[0].name == "lookup_release"
    assert response.tool_calls[0].arguments == '{"version":"3.0"}'
    assert provider.capabilities.tools is True


def test_chat_completions_stream_exposes_text_and_tool_call_deltas() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.read()
        return httpx.Response(
            200,
            content=(
                'data: {"choices":[{"delta":{"content":"目标："}}]}\n\n'
                'data: {"choices":[{"delta":{"tool_calls":[{"id":"call-2",'
                '"type":"function","function":{"name":"lookup_release",'
                '"arguments":"{\\"version\\":\\"3.0\\"}"}}]}}]}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    events = list(provider.stream(ModelRequest(prompt="流式整理")))

    assert [event.type for event in events] == [
        ProviderEventType.STARTED,
        ProviderEventType.DELTA,
        ProviderEventType.DELTA,
        ProviderEventType.COMPLETED,
    ]
    assert events[1].text == "目标："
    assert events[2].tool_calls[0].id == "call-2"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, "unauthorized"),
        (429, "rate_limit"),
        (504, "timeout"),
    ],
)
def test_chat_completions_maps_common_http_errors(
    status: int,
    error_type: str,
) -> None:
    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(status))
        ),
    )
    error_class = {
        "unauthorized": ProviderUnauthorizedError,
        "rate_limit": ProviderRateLimitError,
        "timeout": ProviderTimeoutError,
    }[error_type]

    with pytest.raises(error_class):
        provider.optimize(ModelRequest(prompt="错误映射"))
