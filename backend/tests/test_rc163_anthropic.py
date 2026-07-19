from __future__ import annotations

import httpx

from prompt_optimizer.providers import (
    AnthropicMessagesAdapter,
    ModelRequest,
    ProviderConfig,
    ProviderEventType,
    ProviderRegistry,
)

# RC ID: RC-163. Verify Anthropic Messages, content blocks, SSE, tools, and capability probes.


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="anthropic",
        base_url="https://api.anthropic.test/v1",
        api_key="anthropic-key",
        model="claude-test",
        api_protocol="anthropic",
        api_version="2023-06-01",
        beta_features=("prompt-caching-2024-07-31",),
        prompt_caching=True,
        max_retries=0,
    )


def _tool() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "lookup_release",
            "description": "Look up a release.",
            "parameters": {"type": "object", "properties": {"version": {"type": "string"}}},
        },
    }


def test_anthropic_messages_uses_native_blocks_headers_tools_and_cache() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/messages"
        assert request.headers["x-api-key"] == "anthropic-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert request.headers["anthropic-beta"] == "prompt-caching-2024-07-31"
        body = request.read()
        assert b"Bearer" not in body
        payload = httpx.Response(200, content=body).json()
        assert payload["system"][0]["cache_control"]["type"] == "ephemeral"
        assert payload["messages"][0]["content"][0]["type"] == "text"
        assert payload["messages"][0]["content"][1]["type"] == "tool_result"
        assert payload["tools"][0]["input_schema"]["type"] == "object"
        return httpx.Response(
            200,
            json={
                "content": [
                    {"type": "text", "text": "目标：整理版本。"},
                    {
                        "type": "tool_use",
                        "id": "toolu-1",
                        "name": "lookup_release",
                        "input": {"version": "3.0"},
                    },
                ],
                "usage": {"input_tokens": 12, "output_tokens": 8},
            },
        )

    provider = AnthropicMessagesAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = provider.optimize(
        ModelRequest(
            prompt="整理版本",
            system_prompt="Anthropic system",
            tools=(_tool(),),
            tool_results=({"tool_use_id": "old-tool", "content": "3.0"},),
            cache_prompt=True,
        )
    )

    assert response.analysis.optimized_prompt == "目标：整理版本。"
    assert response.tool_calls[0].id == "toolu-1"
    assert response.usage == {"input_tokens": 12, "output_tokens": 8}
    assert provider.probe_capabilities() == {
        "tool_use": True,
        "prompt_caching": True,
        "beta_extensions": True,
    }


def test_anthropic_messages_stream_parses_text_and_tool_use_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=(
                'event: content_block_delta\n'
                'data: {"type":"content_block_delta","delta":{"type":"text_delta",'
                '"text":"目标："}}\n\n'
                'event: content_block_start\n'
                'data: {"type":"content_block_start","content_block":{"type":"tool_use",'
                '"id":"toolu-2","name":"lookup_release","input":{}}}\n\n'
                'event: message_stop\n'
                'data: {"type":"message_stop"}\n\n'
            ),
        )

    provider = AnthropicMessagesAdapter(
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
    assert events[2].tool_calls[0].name == "lookup_release"


def test_registry_selects_anthropic_adapter_by_provider_name(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for suffix, value in {
        "BASE_URL": "https://api.anthropic.test/v1",
        "API_KEY": "anthropic-key",
        "MODEL": "claude-test",
        "AUTHORIZED": "true",
    }.items():
        monkeypatch.setenv(f"RABBIT_CODE_ANTHROPIC_{suffix}", value)

    provider = ProviderRegistry().get("anthropic")

    assert isinstance(provider, AnthropicMessagesAdapter)
